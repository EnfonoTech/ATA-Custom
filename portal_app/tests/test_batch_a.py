"""Customer list of 27 Oct 2026, batch A: phase IFC, office = team, browser time zone.

Run with (on a development site, never production):
    bench --site <site> run-tests --app portal_app --module portal_app.tests.test_batch_a
"""

import frappe

from portal_app.api import profile, projects, teams
from portal_app.patches import rename_phase_fc_to_ifc
from portal_app.tests.test_portal_roles import PortalRoleTestBase


class TestOfficeFollowsTeam(PortalRoleTestBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.db.set_value("Department", cls.d2, "portal_office", "CAIRO")

	def _office(self, project):
		return frappe.db.get_value("Project", project, "portal_office")

	def test_office_is_the_teams_office_and_clears_with_it(self):
		doc = frappe.get_doc("Project", self.pc)
		doc.portal_team = self.d2
		doc.portal_office = "LISBON"  # a typed office no longer sticks
		doc.save(ignore_permissions=True)
		self.assertEqual(self._office(self.pc), "CAIRO")

		doc.reload()
		doc.portal_team = None
		doc.save(ignore_permissions=True)
		self.assertIsNone(self._office(self.pc))

	def test_update_project_sets_office_from_team(self):
		frappe.set_user(self.super_admin)
		projects.update_project(self.pb, portal_team=self.d1)
		self.assertEqual(self._office(self.pb), "RIYADH")

	def test_dept_admin_creates_under_own_team_only(self):
		frappe.set_user(self.admin)
		res = projects.create_project("Batch A own team", portal_team=self.d1)
		self.addCleanup(frappe.delete_doc, "Project", res["name"], force=1, ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Project", res["name"], "portal_team"), self.d1)
		self.assertEqual(self._office(res["name"]), "RIYADH")

		with self.assertRaises(frappe.PermissionError):
			projects.create_project("Batch A other team", portal_team=self.d2)
		self.assertFalse(frappe.db.exists("Project", {"project_name": "Batch A other team"}))

	def test_team_options_follow_the_department_rule(self):
		frappe.set_user(self.super_admin)
		self.assertTrue({self.d1, self.d2} <= {t["name"] for t in teams.get_team_options()})

		frappe.set_user(self.admin)
		options = teams.get_team_options()
		self.assertEqual({t["name"] for t in options}, {self.d1})
		self.assertEqual(options[0]["office"], "RIYADH")

		frappe.set_user(self.client)
		with self.assertRaises(frappe.PermissionError):
			teams.get_team_options()


class TestPhaseRename(PortalRoleTestBase):
	def test_ifc_is_an_option_and_fc_is_moved(self):
		options = frappe.get_meta("Project").get_field("portal_phase").options.split("\n")
		self.assertIn("IFC", options)
		self.assertNotIn("FC", options)

		frappe.db.set_value("Project", self.pa, "portal_phase", "FC", update_modified=False)
		rename_phase_fc_to_ifc.execute()
		rename_phase_fc_to_ifc.execute()  # safe to run twice
		self.assertEqual(frappe.db.get_value("Project", self.pa, "portal_phase"), "IFC")


class TestBrowserTimeZone(PortalRoleTestBase):
	def _set_tz(self, user, tz):
		frappe.db.set_value("User", user, "time_zone", tz, update_modified=False)

	def test_rule(self):
		follow = profile._should_follow_browser_time_zone
		self.assertTrue(follow(None, "Europe/Lisbon", "Asia/Riyadh"))
		self.assertTrue(follow("", "Europe/Lisbon", "Asia/Riyadh"))
		self.assertTrue(follow("Asia/Riyadh", "Asia/Manila", "Asia/Riyadh"))
		self.assertFalse(follow("Africa/Cairo", "Asia/Manila", "Asia/Riyadh"))

	def test_empty_zone_follows_the_browser(self):
		self._set_tz(self.m1, None)
		frappe.set_user(self.m1)
		res = profile.sync_browser_time_zone("Europe/Lisbon")
		self.assertTrue(res["changed"])
		self.assertEqual(frappe.db.get_value("User", self.m1, "time_zone"), "Europe/Lisbon")

	def test_a_chosen_zone_is_kept(self):
		self._set_tz(self.m2, "Africa/Cairo")
		frappe.set_user(self.m2)
		res = profile.sync_browser_time_zone("Asia/Manila")
		self.assertFalse(res["changed"])
		self.assertEqual(frappe.db.get_value("User", self.m2, "time_zone"), "Africa/Cairo")

	def test_unknown_zone_is_ignored(self):
		self._set_tz(self.m3, None)
		frappe.set_user(self.m3)
		res = profile.sync_browser_time_zone("Mars/Olympus")
		self.assertFalse(res["changed"])
		self.assertFalse(frappe.db.get_value("User", self.m3, "time_zone"))
