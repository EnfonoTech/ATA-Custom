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
	if customer:
		# Rows are the only access source; mirror the backfilled state.
		frappe.get_doc({"doctype": helper.PORTAL_USER_CUSTOMER, "user": doc.name, "customer": customer}).insert(
			ignore_permissions=True
		)
	return doc.name


def _make_project(name: str, customer: str) -> str:
	existing = frappe.db.get_value("Project", {"project_name": name})
	if existing:
		frappe.db.set_value("Project", existing, "customer", customer)
		return existing
	return (
		frappe.get_doc({"doctype": "Project", "project_name": name, "customer": customer})
		.insert(ignore_permissions=True)
		.name
	)


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


class TestMultiCustomerLogin(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		helper.ensure_portal_customer_role()
		helper.ensure_user_portal_linked_customer_field()
		cls.cust_a = _make_customer("Portal Test Customer A")
		cls.cust_b = _make_customer("Portal Test Customer B")
		cls.contact = _make_user("portal.test.multi@example.com", ["Portal Customer"], cls.cust_a)
		cls.project_a = _make_project("Portal Test Project A", cls.cust_a)
		cls.project_b = _make_project("Portal Test Project B", cls.cust_b)

	def setUp(self):
		# Tests must not depend on order: rebuild the contact as "customer A only".
		frappe.set_user("Administrator")
		frappe.db.delete(helper.PORTAL_USER_CUSTOMER, {"user": self.contact})
		user = frappe.get_doc("User", self.contact)
		if not any(r.role == "Portal Customer" for r in user.roles):
			user.append("roles", {"role": "Portal Customer"})
			user.save(ignore_permissions=True)
		frappe.db.set_value("User", self.contact, "portal_linked_customer", self.cust_a)
		frappe.get_doc({"doctype": helper.PORTAL_USER_CUSTOMER, "user": self.contact, "customer": self.cust_a}).insert(
			ignore_permissions=True
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_sync_adds_a_contact_already_linked_to_another_customer(self):
		# The reported bug: "already linked to another customer".
		projects.sync_customer_portal_users(self.project_b, [self.contact])
		self.assertEqual(set(helper.get_portal_linked_customers(self.contact)), {self.cust_a, self.cust_b})
		allowed = set(helper.get_allowed_project_names(self.contact))
		self.assertTrue({self.project_a, self.project_b} <= allowed)

	def test_editing_own_user_field_grants_nothing(self):
		# Every user can write their own User doc (share_with_self); the field is
		# permlevel 1 and is not an access source anyway.
		frappe.set_user(self.contact)
		user = frappe.get_doc("User", self.contact)
		user.portal_linked_customer = self.cust_b
		user.save()
		frappe.set_user("Administrator")
		self.assertNotEqual(frappe.db.get_value("User", self.contact, "portal_linked_customer"), self.cust_b)
		frappe.db.set_value("User", self.contact, "portal_linked_customer", self.cust_b)
		self.assertNotIn(self.project_b, helper.get_allowed_project_names(self.contact))

	def test_removing_the_role_in_desk_drops_every_customer(self):
		user = frappe.get_doc("User", self.contact)
		for row in list(user.roles):
			if row.role == "Portal Customer":
				user.remove(row)
		user.save(ignore_permissions=True)
		self.assertEqual(frappe.get_all(helper.PORTAL_USER_CUSTOMER, filters={"user": self.contact}), [])

	def test_deleting_the_primary_row_repoints_the_primary(self):
		projects._attach_portal_customer_user(self.contact, self.cust_b)
		name = frappe.db.get_value(helper.PORTAL_USER_CUSTOMER, {"user": self.contact, "customer": self.cust_a})
		frappe.delete_doc(helper.PORTAL_USER_CUSTOMER, name, ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("User", self.contact, "portal_linked_customer"), self.cust_b)
		self.assertNotIn(self.project_a, helper.get_allowed_project_names(self.contact))

	def test_team_member_cannot_attach_contacts(self):
		staff = _make_user("portal.test.teammember@example.com", ["Projects User"])
		project = frappe.get_doc("Project", self.project_b)
		project.append("users", {"user": staff})
		project.save(ignore_permissions=True)
		# The old gate: always True through the self-share.
		frappe.set_user(staff)
		self.assertFalse(projects._can_link_customer_logins())
		with self.assertRaises(frappe.PermissionError):
			projects.sync_customer_portal_users(self.project_b, [self.contact])

	def test_share_recipient_check_is_role_based(self):
		from portal_app.api import files

		files._assert_valid_share_recipient(self.contact, self.project_a)
		with self.assertRaises(frappe.PermissionError):
			files._assert_valid_share_recipient(self.contact, self.project_b)
		# A Portal Customer with no customers passes for nothing.
		frappe.db.delete(helper.PORTAL_USER_CUSTOMER, {"user": self.contact})
		with self.assertRaises(frappe.PermissionError):
			files._assert_valid_share_recipient(self.contact, self.project_a)

	def test_customer_cannot_share_or_upload_outside_client_submittal(self):
		from portal_app.api import files

		frappe.set_user(self.contact)
		with self.assertRaises(frappe.PermissionError):
			files._assert_not_customer_sharer()
		root = files.get_project_folders(self.project_a)["project_root"]
		with self.assertRaises(frappe.PermissionError):
			files._assert_upload_allowed(self.project_a, root)
		files._assert_upload_allowed(self.project_a, files._customer_folder_roots(self.project_a)[0])

	def test_one_login_can_hold_several_customers(self):
		projects._attach_portal_customer_user(self.contact, self.cust_b)
		self.assertEqual(set(helper.get_portal_linked_customers(self.contact)), {self.cust_a, self.cust_b})
		self.assertIn(self.contact, helper.get_customer_contact_users(self.cust_b))
		projects._assert_resettable_customer_contact(self.contact, self.cust_b)

	def test_removing_one_customer_keeps_the_others_and_the_role(self):
		projects._attach_portal_customer_user(self.contact, self.cust_b)
		projects._detach_portal_customer_user(self.contact, self.cust_a)
		self.assertEqual(helper.get_portal_linked_customers(self.contact), [self.cust_b])
		self.assertEqual(frappe.db.get_value("User", self.contact, "portal_linked_customer"), self.cust_b)
		self.assertIn("Portal Customer", frappe.get_roles(self.contact))

	def test_removing_the_last_customer_drops_the_role(self):
		for cust in list(helper.get_portal_linked_customers(self.contact)):
			projects._detach_portal_customer_user(self.contact, cust)
		self.assertEqual(helper.get_portal_linked_customers(self.contact), [])
		self.assertNotIn("Portal Customer", frappe.get_roles(self.contact))
