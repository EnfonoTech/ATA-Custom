"""The five portal roles: Super Admin, Department Admin, Team Lead, Team Member, Client Customer.

Run with (on a development site, never production):
    bench --site <site> run-tests --app portal_app --module portal_app.tests.test_portal_roles
"""

import json

import frappe
from erpnext import get_default_company
from frappe.tests.utils import FrappeTestCase

from portal_app.api import auth, files, helper, portal_admin, projects, teams

TEST_PASSWORD = "Prt-" + "4c1e9b7a2d6f" + "#Aa1"
SUFFIX = "@roles.test"


def _user(name, roles=("Projects User",), user_type="System User"):
	email = name + SUFFIX
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=1, ignore_permissions=True)
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": name.title(),
			"enabled": 1,
			"send_welcome_email": 0,
			"new_password": TEST_PASSWORD,
			"user_type": user_type,
		}
	)
	for r in roles:
		doc.append("roles", {"role": r})
	doc.flags.ignore_permissions = True
	doc.insert()
	return doc.name


def _department(label):
	existing = frappe.db.get_value("Department", {"department_name": label})
	if existing:
		frappe.delete_doc("Department", existing, force=1, ignore_permissions=True)
	return (
		frappe.get_doc(
			{
				"doctype": "Department",
				"department_name": label,
				"company": get_default_company() or frappe.get_all("Company", pluck="name")[0],
				"parent_department": "All Departments",
				"is_group": 0,
				"portal_office": "RIYADH",
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _project(label, users=(), lead=None, customer=None, team=None):
	existing = frappe.db.get_value("Project", {"project_name": label})
	if existing:
		frappe.delete_doc("Project", existing, force=1, ignore_permissions=True)
	doc = frappe.get_doc({"doctype": "Project", "project_name": label})
	if lead:
		doc.portal_project_manager = lead
	if customer:
		doc.customer = customer
	if team:
		doc.portal_team = team
	doc.insert(ignore_permissions=True)
	for u in users:
		doc.append("users", {"user": u})
	if users:
		doc.save(ignore_permissions=True)
	return doc.name


def _customer(name):
	if not frappe.db.exists("Customer", name):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name", order_by="lft asc"),
				"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name", order_by="lft asc"),
			}
		).insert(ignore_permissions=True)
	return name


class PortalRoleTestBase(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		helper.ensure_portal_customer_role()
		helper.ensure_portal_roles()
		cls.d1 = _department("Roles Test Team One")
		cls.d2 = _department("Roles Test Team Two")
		cls.super_admin = _user("super", ("System Manager", "Projects User"))
		cls.admin = _user("deptadmin")
		cls.lead = _user("lead")
		cls.m1 = _user("member1")
		cls.m2 = _user("member2")
		cls.m3 = _user("member3")
		cls.outsider = _user("outsider")
		cls.consultant = _user("consultant")  # on a project, but on no department's team
		cls.cust = _customer("Roles Test Customer")
		cls.client = _user("client", (helper.PORTAL_CUSTOMER_ROLE,), "Website User")
		frappe.get_doc({"doctype": helper.PORTAL_USER_CUSTOMER, "user": cls.client, "customer": cls.cust}).insert(
			ignore_permissions=True
		)
		teams._assign_users_to_team(cls.d1, [cls.admin, cls.lead, cls.m1, cls.m2])
		teams._assign_users_to_team(cls.d2, [cls.m3])
		# The roles are set the way the Org Chart sets them.
		frappe.set_user(cls.super_admin)
		teams.set_member_role(cls.d1, cls.admin, "department_admin")
		teams.set_member_role(cls.d1, cls.lead, "team_lead")
		frappe.set_user("Administrator")
		cls.pa = _project("Roles Test PA", [cls.m1], lead=cls.m1, customer=cls.cust)
		cls.pb = _project("Roles Test PB", [cls.m3], lead=cls.m3)
		cls.pc = _project("Roles Test PC orphan")
		cls.pd = _project("Roles Test PD team", team=cls.d1)
		# staffed by somebody outside every department and under no team: it belongs to nobody yet
		cls.pe = _project("Roles Test PE staffed outside", [cls.consultant])

	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")

	def names(self, user):
		return {
			k
			for k, p in {"pa": self.pa, "pb": self.pb, "pc": self.pc, "pd": self.pd, "pe": self.pe}.items()
			if p in helper.get_allowed_project_names(user)
		}


class TestRoleVisibility(PortalRoleTestBase):
	def test_roles_are_detected(self):
		self.assertEqual(helper.get_portal_role(self.super_admin), "super_admin")
		self.assertEqual(helper.get_portal_role(self.admin), "department_admin")
		self.assertEqual(helper.get_portal_role(self.lead), "team_lead")
		self.assertEqual(helper.get_portal_role(self.m1), "team_member")
		self.assertEqual(helper.get_portal_role(self.client), "client_customer")

	def test_marker_roles_follow_the_department_data(self):
		self.assertIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.admin))
		self.assertIn(helper.TEAM_LEAD_ROLE, frappe.get_roles(self.lead))
		self.assertNotIn(helper.TEAM_LEAD_ROLE, frappe.get_roles(self.m1))

	def test_super_admin_sees_everything(self):
		self.assertEqual(self.names(self.super_admin), {"pa", "pb", "pc", "pd", "pe"})

	def test_team_member_sees_only_their_projects(self):
		self.assertEqual(self.names(self.m1), {"pa"})
		self.assertEqual(self.names(self.m3), {"pb"})
		self.assertEqual(self.names(self.m2), set())
		self.assertEqual(self.names(self.outsider), set())
		self.assertEqual(self.names(self.consultant), {"pe"})

	def test_team_lead_sees_the_projects_of_their_team(self):
		# PA: their member m1 is on it. PD: it belongs to their team. Not PB (other team), not the orphan.
		self.assertEqual(self.names(self.lead), {"pa", "pd"})

	def test_department_admin_sees_their_department_and_the_projects_nobody_owns(self):
		# PA, PD: theirs. PC and PE belong to no department (PE has a consultant on it, but no
		# department's team and no team), so a Department Admin can triage them. Not PB: that is
		# another department's.
		self.assertEqual(self.names(self.admin), {"pa", "pc", "pd", "pe"})
		# a Team Lead looks after their own team only, never the projects nobody owns
		self.assertTrue({"pc", "pe"}.isdisjoint(self.names(self.lead)))

	def test_client_sees_only_their_customers_projects(self):
		self.assertEqual(self.names(self.client), {"pa"})

	def test_manageable_projects(self):
		mine = {self.pa, self.pb, self.pc, self.pd, self.pe}  # ignore any other projects on the site

		def manageable(user):
			return set(helper.get_manageable_project_names(user)) & mine

		self.assertEqual(manageable(self.m1), {self.pa})
		self.assertEqual(manageable(self.lead), {self.pa, self.pd})
		self.assertEqual(manageable(self.admin), {self.pa, self.pc, self.pd, self.pe})
		self.assertEqual(helper.get_manageable_project_names(self.client), [])

	def test_value_is_seen_only_by_super_admin_and_the_project_lead_of_an_admin(self):
		self.assertTrue(helper.can_view_project_value(self.pa, self.super_admin))
		self.assertFalse(helper.can_view_project_value(self.pa, self.m1))
		self.assertFalse(helper.can_view_project_value(self.pa, self.admin))


class TestOrgChart(PortalRoleTestBase):
	def chart(self, user):
		frappe.set_user(user)
		return teams.get_org_chart()

	def test_nobody_below_team_lead_can_open_the_chart(self):
		for user in (self.m1, self.outsider, self.client):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				teams.get_org_chart()

	def test_chart_shows_roles_and_flags_per_caller(self):
		chart = self.chart(self.super_admin)
		by_team = {t["name"]: t for t in chart["teams"]}
		people = {m["user"]: m for m in by_team[self.d1]["members"]}
		self.assertEqual(people[self.admin]["team_role"], "department_admin")
		self.assertEqual(people[self.lead]["team_role"], "team_lead")
		self.assertEqual(people[self.m1]["team_role"], "team_member")
		self.assertTrue(people[self.super_admin]["is_super_admin"] if self.super_admin in people else True)
		self.assertTrue(by_team[self.d1]["can_edit"] and by_team[self.d2]["can_edit"])
		self.assertTrue(people[self.m1]["can_change_role"] and people[self.m1]["can_reset_password"])

		chart = self.chart(self.admin)
		by_team = {t["name"]: t for t in chart["teams"]}
		self.assertTrue(by_team[self.d1]["can_edit"])
		self.assertFalse(by_team[self.d2]["can_edit"])
		people = {m["user"]: m for m in by_team[self.d1]["members"]}
		self.assertTrue(people[self.m1]["can_change_role"])
		self.assertTrue(people[self.m1]["can_reset_password"])
		self.assertFalse(people[self.admin]["can_reset_password"])  # themselves

		chart = self.chart(self.lead)
		self.assertTrue(chart["me"]["can_assign_to_projects"])
		self.assertFalse(any(t["can_edit"] for t in chart["teams"]))
		self.assertFalse(any(m["can_change_role"] for t in chart["teams"] for m in t["members"]))
		self.assertEqual(chart["unassigned"], [])

	def test_a_client_is_never_in_the_chart_or_assignable(self):
		frappe.set_user(self.super_admin)
		with self.assertRaises(frappe.PermissionError):
			teams.add_team_member(self.d1, self.client)
		names = {u["name"] for u in teams.get_assignable_users(self.d1)}
		self.assertNotIn(self.client, names)


class TestRoleChanges(PortalRoleTestBase):
	def test_super_admin_makes_a_member_the_team_lead_and_the_old_lead_steps_down(self):
		frappe.set_user(self.super_admin)
		teams.set_member_role(self.d1, self.m2, "team_lead")
		self.assertEqual(frappe.db.get_value("Department", self.d1, "portal_team_lead"), self.m2)
		self.assertIn(helper.TEAM_LEAD_ROLE, frappe.get_roles(self.m2))
		self.assertNotIn(helper.TEAM_LEAD_ROLE, frappe.get_roles(self.lead))
		self.assertEqual(helper.get_portal_role(self.lead), "team_member")
		# put it back
		teams.set_member_role(self.d1, self.lead, "team_lead")
		self.assertEqual(frappe.db.get_value("Department", self.d1, "portal_team_lead"), self.lead)
		self.assertNotIn(helper.TEAM_LEAD_ROLE, frappe.get_roles(self.m2))

	def test_department_admin_manages_own_team_but_not_admins_or_other_teams(self):
		frappe.set_user(self.admin)
		teams.set_member_role(self.d1, self.m1, "team_lead")
		self.assertEqual(frappe.db.get_value("Department", self.d1, "portal_team_lead"), self.m1)
		teams.set_member_role(self.d1, self.lead, "team_lead")  # restore
		with self.assertRaises(frappe.PermissionError):
			teams.set_member_role(self.d1, self.m1, "department_admin")
		with self.assertRaises(frappe.PermissionError):
			teams.set_member_role(self.d2, self.m3, "team_lead")
		with self.assertRaises(frappe.PermissionError):
			teams.set_member_role(self.d1, self.admin, "team_member")  # an admin is changed by a Super Admin

	def test_team_lead_and_member_cannot_change_roles(self):
		for user in (self.lead, self.m1):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				teams.set_member_role(self.d1, self.m2, "team_lead")

	def test_super_admin_makes_and_removes_a_department_admin(self):
		frappe.set_user(self.super_admin)
		teams.set_member_role(self.d2, self.m3, "department_admin")
		self.assertIn(self.d2, helper.admin_department_names(self.m3))
		self.assertIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.m3))
		self.assertEqual(helper.get_portal_role(self.m3), "department_admin")
		teams.set_member_role(self.d2, self.m3, "team_member")
		self.assertNotIn(self.d2, helper.admin_department_names(self.m3))
		self.assertNotIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.m3))
		self.assertEqual(helper.get_portal_role(self.m3), "team_member")

	def test_setting_a_role_adds_the_person_to_the_team_first(self):
		frappe.set_user(self.super_admin)
		teams.set_member_role(self.d2, self.outsider, "team_member")
		chart = teams.get_org_chart()
		d2 = next(t for t in chart["teams"] if t["name"] == self.d2)
		self.assertIn(self.outsider, [m["user"] for m in d2["members"]])
		teams.remove_team_member(self.d2, self.outsider)

	def test_removing_people_is_for_super_and_department_admins(self):
		frappe.set_user(self.admin)
		teams.remove_team_member(self.d1, self.m2)
		self.assertNotIn(self.m2, [m["user"] for m in next(t for t in teams.get_org_chart()["teams"] if t["name"] == self.d1)["members"]])
		teams.add_team_member(self.d1, self.m2)
		with self.assertRaises(frappe.PermissionError):
			teams.remove_team_member(self.d2, self.m3)  # not their department
		for user in (self.lead, self.m1):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				teams.remove_team_member(self.d1, self.m2)
			with self.assertRaises(frappe.PermissionError):
				teams.remove_team_lead(self.d1)
		frappe.set_user(self.admin)
		with self.assertRaises(frappe.PermissionError):
			teams.remove_team_member(self.d1, self.admin)  # only a Super Admin removes an admin

	def test_removing_the_team_lead_keeps_them_on_the_team(self):
		frappe.set_user(self.admin)
		teams.remove_team_lead(self.d1)
		self.assertFalse(frappe.db.get_value("Department", self.d1, "portal_team_lead"))
		self.assertNotIn(helper.TEAM_LEAD_ROLE, frappe.get_roles(self.lead))
		self.assertEqual(helper.get_portal_role(self.lead), "team_member")
		teams.set_member_role(self.d1, self.lead, "team_lead")

	def test_super_admin_can_be_granted_but_not_self_changed_or_orphaned(self):
		frappe.set_user(self.super_admin)
		with self.assertRaises(frappe.PermissionError):
			portal_admin.set_super_admin(self.super_admin, 0)
		portal_admin.set_super_admin(self.m3, 1)
		self.assertTrue(helper.is_super_admin(self.m3))
		portal_admin.set_super_admin(self.m3, 0)
		self.assertFalse(helper.is_super_admin(self.m3))
		frappe.set_user(self.admin)
		with self.assertRaises(frappe.PermissionError):
			portal_admin.set_super_admin(self.m3, 1)


class TestProjectTeams(PortalRoleTestBase):
	def team(self, project):
		return {r.user for r in frappe.get_doc("Project", project).users}

	def test_team_lead_adds_people_from_the_chart_but_cannot_remove(self):
		frappe.set_user(self.lead)
		projects.add_project_members(self.pa, [self.m2])
		self.assertEqual(self.team(self.pa), {self.m1, self.m2})
		with self.assertRaises(frappe.PermissionError):
			projects.sync_project_team(self.pa, [self.m1])  # would remove m2
		self.assertEqual(self.team(self.pa), {self.m1, self.m2})
		frappe.set_user(self.admin)
		projects.sync_project_team(self.pa, [self.m1])  # a Department Admin may
		self.assertEqual(self.team(self.pa), {self.m1})

	def test_remove_project_members_is_admin_only_and_survives_disabled_users(self):
		frappe.set_user(self.lead)
		projects.add_project_members(self.pa, [self.m2])
		with self.assertRaises(frappe.PermissionError):
			projects.remove_project_members(self.pa, [self.m2])
		frappe.set_user(self.m1)
		with self.assertRaises(frappe.PermissionError):
			projects.remove_project_members(self.pa, [self.m2])
		self.assertIn(self.m2, self.team(self.pa))
		# someone whose login was disabled since can still be taken off the team
		frappe.db.set_value("User", self.m2, "enabled", 0)
		try:
			frappe.set_user(self.admin)
			res = projects.remove_project_members(self.pa, json.dumps([self.m2]))
			self.assertEqual(res["removed"], [self.m2])
			self.assertEqual(self.team(self.pa), {self.m1})
		finally:
			frappe.db.set_value("User", self.m2, "enabled", 1)

	def test_team_lead_cannot_assign_to_a_project_outside_their_scope(self):
		frappe.set_user(self.lead)
		with self.assertRaises(frappe.PermissionError):
			projects.add_project_members(self.pb, [self.m2])

	def test_member_cannot_add_but_the_lead_architect_can(self):
		frappe.set_user(self.m2)
		with self.assertRaises(frappe.PermissionError):
			projects.add_project_members(self.pa, [self.m2])
		frappe.set_user(self.m1)  # m1 is on PA and its Lead Architect
		projects.add_project_members(self.pa, [self.m2])
		self.assertIn(self.m2, self.team(self.pa))
		with self.assertRaises(frappe.PermissionError):
			projects.sync_project_team(self.pa, [self.m1])
		frappe.set_user(self.super_admin)
		projects.sync_project_team(self.pa, [self.m1])

	def test_clients_are_never_added_to_a_project_team(self):
		frappe.set_user(self.super_admin)
		with self.assertRaises(frappe.PermissionError):
			projects.add_project_members(self.pa, [self.client])

	def test_assignable_projects_list(self):
		frappe.set_user(self.lead)
		names = {p["name"] for p in projects.get_assignable_projects(self.m1)}
		self.assertEqual(names, {self.pa, self.pd})
		frappe.set_user(self.m1)
		self.assertEqual({p["name"] for p in projects.get_assignable_projects()}, {self.pa})  # only as Lead Architect

	def test_lead_architect_rules(self):
		frappe.set_user(self.admin)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(self.pa, portal_project_manager=self.admin)  # cannot take it over
		projects.update_project(self.pa, portal_project_manager=self.m2)
		self.assertEqual(frappe.db.get_value("Project", self.pa, "portal_project_manager"), self.m2)
		frappe.set_user(self.super_admin)
		projects.update_project(self.pa, portal_project_manager=self.m1)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(self.pa, portal_project_manager=self.client)

	def test_capabilities(self):
		frappe.set_user(self.lead)
		caps = projects.get_capabilities()
		self.assertEqual(caps["portal_role"], "team_lead")
		self.assertTrue(caps["can_view_org_chart"])
		self.assertFalse(caps["is_manager"])
		self.assertFalse(caps["can_edit_org_roles"])
		frappe.set_user(self.admin)
		caps = projects.get_capabilities()
		self.assertEqual(caps["portal_role"], "department_admin")
		self.assertTrue(caps["is_manager"] and caps["can_edit_org_roles"] and caps["can_reset_passwords"])
		self.assertEqual(caps["admin_team_names"], [self.d1])
		frappe.set_user(self.m1)
		caps = projects.get_capabilities()
		self.assertFalse(caps["can_view_org_chart"])
		self.assertEqual(caps["portal_role"], "team_member")
		frappe.set_user(self.client)
		self.assertEqual(projects.get_capabilities()["portal_role"], "client_customer")


class TestResetPassword(PortalRoleTestBase):
	def test_who_may_reset_whom(self):
		self.assertTrue(helper.can_reset_password_for(self.m1, self.super_admin))
		self.assertTrue(helper.can_reset_password_for(self.client, self.super_admin))
		self.assertFalse(helper.can_reset_password_for("Administrator", self.super_admin))
		self.assertFalse(helper.can_reset_password_for(self.super_admin, self.super_admin))
		# a Department Admin: people of their department only
		self.assertTrue(helper.can_reset_password_for(self.m1, self.admin))
		self.assertTrue(helper.can_reset_password_for(self.lead, self.admin))
		self.assertFalse(helper.can_reset_password_for(self.m3, self.admin))  # other department
		self.assertFalse(helper.can_reset_password_for(self.super_admin, self.admin))
		self.assertFalse(helper.can_reset_password_for(self.client, self.admin))
		# nobody else
		for caller in (self.lead, self.m1, self.client):
			self.assertFalse(helper.can_reset_password_for(self.m2, caller))

	def test_the_endpoint_enforces_it(self):
		frappe.set_user(self.lead)
		with self.assertRaises(frappe.PermissionError):
			portal_admin.reset_user_password(self.m1, "email")
		frappe.set_user(self.admin)
		with self.assertRaises(frappe.PermissionError):
			portal_admin.reset_user_password(self.m3, "email")
		with self.assertRaises(frappe.PermissionError):
			portal_admin.reset_user_password(self.m1, "set", TEST_PASSWORD)  # direct set is for Super Admins
		frappe.set_user(self.super_admin)
		portal_admin.reset_user_password(self.m1, "set", "Prt-" + "9f3b1c7d2a5e" + "#Zz9")
		self.assertTrue(frappe.utils.password.check_password(self.m1, "Prt-" + "9f3b1c7d2a5e" + "#Zz9"))

	def test_forgot_password_answers_the_same_for_unknown_addresses(self):
		frappe.set_user("Guest")
		fn = getattr(auth.request_password_reset, "__wrapped__", auth.request_password_reset)
		known = fn(self.m1)
		unknown = fn("nobody-here@roles.test")
		blank = fn("")
		self.assertEqual(known, unknown)
		self.assertEqual(known, blank)


class TestClientFolders(PortalRoleTestBase):
	def setUp(self):
		super().setUp()
		files._forget_client_folders()

	def test_every_project_gets_incoming_and_outgoing(self):
		folders = files._ensure_client_folders(self.pa)
		root = files._client_folder_path(self.pa)
		self.assertEqual(folders["incoming"], root + "/Incoming")
		self.assertEqual(folders["outgoing"], root + "/Outgoing")
		self.assertTrue(frappe.db.exists("File", folders["incoming"]) and frappe.db.exists("File", folders["outgoing"]))
		self.assertEqual(files._ensure_client_folders(self.pa), folders)  # idempotent
		template = files._folder_template()
		self.assertIn("06-CLIENT SUBMITTAL/Incoming", template)
		self.assertIn("06-CLIENT SUBMITTAL/Outgoing", template)

	def test_a_client_uploads_to_outgoing_only(self):
		folders = files._ensure_client_folders(self.pa)
		frappe.set_user(self.client)
		self.assertEqual(files._resolve_client_upload_target(self.pa, files.CLIENT_OUTGOING_TARGET), folders["outgoing"])
		self.assertEqual(files._resolve_client_upload_target(self.pa, ""), folders["outgoing"])
		files._assert_upload_allowed(self.pa, folders["outgoing"])
		files._assert_upload_allowed(self.pa, folders["outgoing"] + "/sub")
		for refused in (folders["incoming"], folders["root"], files._attachments_root() + "/" + self.pa):
			with self.assertRaises(frappe.PermissionError):
				files._assert_upload_allowed(self.pa, refused)

	def test_a_client_sees_both_folders_but_nothing_else(self):
		files._ensure_client_folders(self.pa)
		frappe.set_user(self.client)
		names = set(files._customer_folder_names([self.pa]))
		root = files._client_folder_path(self.pa)
		self.assertTrue({root, root + "/Incoming", root + "/Outgoing"} <= names)
		listed = files.list_project_folders(self.pa)["subfolders"]
		self.assertTrue(all(files._in_customer_roots(self.pa, f["name"]) for f in listed))

	def test_submit_to_client_lands_in_incoming_and_is_tagged_incoming(self):
		frappe.set_user(self.super_admin)
		from frappe.utils.file_manager import save_file

		ctx = files.ensure_project_folders(self.pa)
		src = save_file("roles-test-src.txt", b"roles test content one", "Project", self.pa, folder=ctx["project_root"], is_private=1)
		result = files.submit_to_client_submittal(src.name, self.pa)
		copy = frappe.get_doc("File", frappe.db.get_value("File", {"file_name": result["file_name"], "attached_to_name": self.pa}))
		self.assertEqual(copy.folder, files._client_folder_path(self.pa) + "/Incoming")
		listing = files.list_project_files(self.pa)["files"]
		row = next(f for f in listing if f["name"] == copy.name)
		self.assertEqual(row["client_direction"], "incoming")

	def test_the_client_folders_cannot_be_renamed_away(self):
		frappe.set_user(self.super_admin)
		files._ensure_client_folders(self.pa)
		root = files._client_folder_path(self.pa)
		for path in (root, root + "/Incoming", root + "/Outgoing"):
			with self.assertRaises(frappe.PermissionError):
				files.rename_project_subfolder(self.pa, path, "Renamed")

	def test_a_lookalike_client_folder_name_is_found(self):
		project = _project("Roles Test lookalike")
		files.ensure_project_folders(project)
		canonical = files._attachments_root() + "/" + project + "/06-CLIENT SUBMITTAL"
		lookalike = files._attachments_root() + "/" + project + "/06 - CLIENT SUBMITTAL"
		frappe.rename_doc("File", canonical, lookalike, force=True)
		frappe.db.set_value("File", lookalike, "file_name", "06 - CLIENT SUBMITTAL")
		files._forget_client_folders()
		self.assertEqual(files._client_folder_path(project), lookalike)
		folders = files._ensure_client_folders(project)
		self.assertEqual(folders["root"], lookalike)
		self.assertEqual(folders["outgoing"], lookalike + "/Outgoing")


class TestMigrationPatches(PortalRoleTestBase):
	def test_role_model_patch_is_idempotent_and_keeps_super_admins_out(self):
		from portal_app.patches import setup_portal_role_model

		legacy = _user("legacypm", ("Projects Manager", "Projects User"))
		setup_portal_role_model.execute()
		first = set(helper.admin_department_names(legacy))
		self.assertTrue(first)
		self.assertIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(legacy))
		setup_portal_role_model.execute()
		self.assertEqual(set(helper.admin_department_names(legacy)), first)
		self.assertFalse(helper.admin_department_names(self.super_admin))
		self.assertTrue(helper.has_portal_staff_project_access(legacy))
		# the legacy manager sees the whole portfolio as before: every department's projects plus the
		# ones that belong to no department (a manager of every department has nothing hidden)
		self.assertEqual(set(helper.get_allowed_project_names(legacy)), set(frappe.get_all("Project", pluck="name")))

	def test_folder_patch_sorts_loose_files_and_is_idempotent(self):
		from frappe.utils.file_manager import save_file

		from portal_app.patches import create_client_incoming_outgoing_folders

		project = _project("Roles Test patch folders", [self.m1])
		files.ensure_project_folders(project)
		root = files._client_folder_path(project)
		for sub in ("Incoming", "Outgoing"):
			frappe.delete_doc("File", root + "/" + sub, force=1, ignore_permissions=True)
		files._forget_client_folders()
		frappe.set_user("Administrator")
		ata_file = save_file("patch-from-ata.txt", b"patch ata content", "Project", project, folder=root, is_private=1)
		frappe.set_user(self.client)
		client_file = save_file("patch-from-client.txt", b"patch client content", "Project", project, folder=root, is_private=1)
		frappe.set_user("Administrator")
		create_client_incoming_outgoing_folders.execute()
		self.assertEqual(frappe.db.get_value("File", ata_file.name, "folder"), root + "/Incoming")
		self.assertEqual(frappe.db.get_value("File", client_file.name, "folder"), root + "/Outgoing")
		create_client_incoming_outgoing_folders.execute()
		self.assertEqual(frappe.db.get_value("File", client_file.name, "folder"), root + "/Outgoing")


class TestCreateUserRoles(PortalRoleTestBase):
	def make(self, **kw):
		args = dict(email="created%d@roles.test" % kw.pop("n", 1), full_name="Created User", password=TEST_PASSWORD)
		args.update(kw)
		email = args["email"]
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=1, ignore_permissions=True)
		return portal_admin.create_portal_user(**args)

	def test_each_role_can_be_created(self):
		frappe.set_user(self.super_admin)
		r = self.make(n=1, role="team_member", team=self.d1)
		self.assertEqual(helper.get_portal_role(r["name"]), "team_member")
		self.assertIn(r["name"], [m["user"] for m in next(t for t in teams.get_org_chart()["teams"] if t["name"] == self.d1)["members"]])
		r = self.make(n=2, role="team_lead", team=self.d2)
		self.assertEqual(helper.get_portal_role(r["name"]), "team_lead")
		self.assertEqual(frappe.db.get_value("Department", self.d2, "portal_team_lead"), r["name"])
		teams.remove_team_lead(self.d2)
		r = self.make(n=3, role="department_admin", teams_json='["%s"]' % self.d2)
		self.assertEqual(helper.get_portal_role(r["name"]), "department_admin")
		self.assertIn(self.d2, helper.admin_department_names(r["name"]))
		r = self.make(n=4, role="super_admin")
		self.assertTrue(helper.is_super_admin(r["name"]))
		r = self.make(n=5, role="client_customer", portal_linked_customer=self.cust)
		self.assertEqual(helper.get_portal_role(r["name"]), "client_customer")
		self.assertEqual(frappe.db.get_value("User", r["name"], "user_type"), "Website User")

	def test_only_a_super_admin_creates_admins(self):
		frappe.set_user(self.admin)
		with self.assertRaises(frappe.PermissionError):
			self.make(n=6, role="team_member", team=self.d1)  # a Department Admin cannot create logins at all
