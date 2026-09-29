"""Customer portal invite / password-reset rules.

Run with:
    bench --site <site> run-tests --app portal_app --module portal_app.tests.test_customer_portal_access
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from portal_app.api import helper
from portal_app.api import portal_admin
from portal_app.api import projects

TEST_PASSWORD = "Prt-" + "4c1e9b7a2d6f" + "#Aa1"


def _make_customer(name: str) -> str:
	if not frappe.db.exists("Customer", name):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_group": frappe.db.get_value("Customer Group", {}, "name", order_by="lft asc"),
				"territory": frappe.db.get_value("Territory", {}, "name", order_by="lft asc"),
			}
		).insert(ignore_permissions=True)
	return name


def _make_user(email: str, roles: list[str], customer: str | None = None) -> str:
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=1, ignore_permissions=True)
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"enabled": 1,
			"send_welcome_email": 0,
			"new_password": TEST_PASSWORD,
		}
	)
	for r in roles:
		doc.append("roles", {"role": r})
	if customer:
		doc.portal_linked_customer = customer
	doc.insert(ignore_permissions=True)
	return doc.name


class TestCustomerPortalAccess(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		helper.ensure_portal_customer_role()
		helper.ensure_user_portal_linked_customer_field()
		cls.cust_a = _make_customer("Portal Test Customer A")
		cls.cust_b = _make_customer("Portal Test Customer B")
		cls.contact_a = _make_user("portal.test.contact.a@example.com", ["Portal Customer"], cls.cust_a)
		cls.contact_b = _make_user("portal.test.contact.b@example.com", ["Portal Customer"], cls.cust_b)
		cls.staff = _make_user("portal.test.staff@example.com", ["Projects Manager"])
		cls.staff_with_link = _make_user(
			"portal.test.staff.linked@example.com", ["Projects Manager", "Portal Customer"], cls.cust_a
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_customer_contact_lands_on_the_portal(self):
		self.assertEqual(helper.get_website_user_home_page(self.contact_a), "portal-app")

	def test_staff_and_guest_fall_through_to_frappe_home_page(self):
		self.assertIsNone(helper.get_website_user_home_page(self.staff))
		self.assertIsNone(helper.get_website_user_home_page(self.staff_with_link))
		self.assertIsNone(helper.get_website_user_home_page("Administrator"))
		self.assertIsNone(helper.get_website_user_home_page("Guest"))

	def test_reset_allows_only_a_contact_of_the_same_customer(self):
		projects._assert_resettable_customer_contact(self.contact_a, self.cust_a)
		with self.assertRaises(frappe.PermissionError):
			projects._assert_resettable_customer_contact(self.contact_b, self.cust_a)

	def test_reset_never_reaches_staff_or_administrator(self):
		with self.assertRaises(frappe.PermissionError):
			projects._assert_resettable_customer_contact(self.staff, self.cust_a)
		with self.assertRaises(frappe.PermissionError):
			projects._assert_resettable_customer_contact(self.staff_with_link, self.cust_a)
		with self.assertRaises(frappe.DoesNotExistError):
			projects._assert_resettable_customer_contact("Administrator", self.cust_a)

	def test_only_system_manager_may_reset(self):
		self.assertTrue(projects._can_reset_customer_portal_passwords("Administrator"))
		self.assertFalse(projects._can_reset_customer_portal_passwords(self.staff))

	def test_admin_page_refuses_customer_with_staff_role(self):
		with self.assertRaises(frappe.ValidationError):
			portal_admin.create_portal_user(
				email="portal.test.mixed@example.com",
				full_name="Mixed Role",
				password=TEST_PASSWORD,
				roles_json='["Portal Customer", "Projects User"]',
				portal_linked_customer=self.cust_a,
			)
		self.assertFalse(frappe.db.exists("User", "portal.test.mixed@example.com"))

	def test_admin_page_refuses_a_login_nobody_can_sign_in_to(self):
		with self.assertRaises(frappe.ValidationError):
			portal_admin.create_portal_user(
				email="portal.test.nopass@example.com",
				full_name="No Password",
				password="",
				roles_json='["Portal Customer"]',
				send_welcome_email=0,
				portal_linked_customer=self.cust_a,
			)
		self.assertFalse(frappe.db.exists("User", "portal.test.nopass@example.com"))

	def test_admin_page_customer_gets_portal_redirect(self):
		email = "portal.test.new.contact@example.com"
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=1, ignore_permissions=True)
		portal_admin.create_portal_user(
			email=email,
			full_name="New Contact",
			password=TEST_PASSWORD,
			roles_json='["Portal Customer"]',
			send_welcome_email=0,
			portal_linked_customer=self.cust_a,
		)
		user = frappe.get_doc("User", email)
		self.assertEqual(user.redirect_url, helper.PORTAL_HOME)
		self.assertEqual(user.portal_linked_customer, self.cust_a)
		self.assertEqual({r.role for r in user.roles}, {"Portal Customer"})
