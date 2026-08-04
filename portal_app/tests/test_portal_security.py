"""Regression tests for the security fixes in the production-readiness pass.

Every test here maps to a defect that shipped in `main`. They are deliberately
about *authorization and storage*, not UI behaviour — those are the failures that
are silent in production and expensive to discover late.

Run with:
    bench --site <site> run-tests --app portal_app
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from portal_app.api import files as files_api
from portal_app.api import helper

TEST_PASSWORD = "Prt-" + "9f3a2c7d1e5b" + "#Aa1"


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
			"user_type": "System User",
			"new_password": TEST_PASSWORD,
		}
	)
	for r in roles:
		doc.append("roles", {"role": r})
	if customer and frappe.get_meta("User").has_field("portal_linked_customer"):
		doc.portal_linked_customer = customer
	doc.insert(ignore_permissions=True)
	return doc.name


class TestUploadSafety(FrappeTestCase):
	"""_safe_upload_filename is the only thing standing between a multipart
	filename and the File records / folder tree it feeds."""

	def test_strips_directory_components(self):
		self.assertEqual(files_api._safe_upload_filename("report.pdf"), "report.pdf")
		self.assertEqual(files_api._safe_upload_filename("../../etc/passwd"), "passwd")
		self.assertEqual(files_api._safe_upload_filename("C:\\Users\\x\\plan.dwg"), "plan.dwg")
		self.assertEqual(files_api._safe_upload_filename("a/b/c/drawing.dwg"), "drawing.dwg")

	def test_rejects_traversal_only_names(self):
		for bad in ("..", ".", "", "   "):
			with self.assertRaises(frappe.ValidationError):
				files_api._safe_upload_filename(bad)

	def test_rejects_extensions_that_execute_in_the_site_origin(self):
		# A stored .html/.svg served from the site origin is same-origin script
		# against the portal session.
		for bad in ("payload.html", "logo.svg", "x.PHTML", "run.sh", "a.js"):
			with self.assertRaises(frappe.ValidationError):
				files_api._safe_upload_filename(bad)

	def test_allows_the_document_types_the_portal_exists_for(self):
		for good in ("plan.dwg", "contract.pdf", "sheet.xlsx", "model.skp", "photo.JPG"):
			self.assertEqual(files_api._safe_upload_filename(good), good)


class TestShareTokenFailsClosed(FrappeTestCase):
	def test_tampered_signature_is_rejected(self):
		token = files_api._sign_share_payload({"p": "PROJ-TEST", "f": "Home/Attachments/PROJ-TEST", "exp": 0})
		payload_part, _sig = token.rsplit(".", 1)
		forged = payload_part + "." + ("0" * 64)
		with self.assertRaises(frappe.PermissionError):
			files_api._verify_share_token(forged)

	def test_expired_token_is_rejected(self):
		token = files_api._sign_share_payload({"p": "PROJ-TEST", "f": "Home/Attachments/PROJ-TEST", "exp": 1})
		with self.assertRaises(frappe.PermissionError):
			files_api._verify_share_token(token)

	def test_valid_token_round_trips(self):
		payload = {"p": "PROJ-TEST", "f": "Home/Attachments/PROJ-TEST", "exp": 0}
		out = files_api._verify_share_token(files_api._sign_share_payload(payload))
		self.assertEqual(out["p"], "PROJ-TEST")

	def test_missing_share_record_is_not_treated_as_a_valid_legacy_token(self):
		# _share_record_active(None) must be False: a token whose share row has been
		# deleted used to be honoured forever instead of being revoked.
		self.assertFalse(files_api._share_record_active(None))
		self.assertFalse(files_api._share_record_active({"revoked": 1}))


class TestEndpointAuthorization(FrappeTestCase):
	"""Every whitelisted endpoint is a public HTTP endpoint. These are the ones
	that shipped with no check at all."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.outsider = _make_user("portal.test.outsider@example.com", ["Blogger"])

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_non_portal_user_cannot_read_the_staff_directory(self):
		from portal_app.api import teams

		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			teams.get_teams()
		with self.assertRaises(frappe.PermissionError):
			teams.get_team_summary()
		with self.assertRaises(frappe.PermissionError):
			teams.get_offices()

	def test_non_portal_user_cannot_enumerate_users(self):
		from portal_app.api import projects

		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			projects.get_portal_users()

	def test_non_portal_user_cannot_read_portal_config(self):
		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			files_api.list_portal_file_types()
		with self.assertRaises(frappe.PermissionError):
			files_api.list_folder_route_rules()

	def test_ai_chat_requires_a_portal_user(self):
		from portal_app.api import ai_chat

		frappe.set_user(self.outsider)
		with self.assertRaises(frappe.PermissionError):
			ai_chat.ask("how many projects")

	def test_assert_portal_user_rejects_guest(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			helper.assert_portal_user()


class TestSortAllowlist(FrappeTestCase):
	def test_unknown_sort_field_falls_back_instead_of_reaching_the_query(self):
		from portal_app.api.projects import _safe_order_by

		self.assertEqual(_safe_order_by("(select 1)", "desc"), "modified desc")
		self.assertEqual(_safe_order_by("name; drop table", "asc"), "modified asc")
		self.assertEqual(_safe_order_by("project_name", "asc"), "project_name asc")
		self.assertEqual(_safe_order_by("modified", "sideways"), "modified desc")


class TestDemoSeedHasNoStaticCredential(FrappeTestCase):
	def test_password_is_random_per_run(self):
		from portal_app.project_portal.doctype.portal_demo_seed_run.portal_demo_seed_run import (
			_new_demo_password,
		)

		first, second = _new_demo_password(), _new_demo_password()
		self.assertNotEqual(first, second)
		self.assertNotIn("ChangeMe", first)
		self.assertGreaterEqual(len(first), 16)
