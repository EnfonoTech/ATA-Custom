"""Batch C: R2 six-level roles with departments over teams, R3 per-project links with
per-user access and payload stripping, R4 change_user_role with last-Super-Admin
protection, R6 logo. Plus the generic patches and the ATA one-shot script.

Written before the implementation (TDD). Spec: .pipeline/spec.md, section 9.

Run with (on a development site, never production):
    bench --site <site> run-tests --module portal_app.tests.test_batch_c
"""

import contextlib
import glob
import importlib
import io
import json
import os
import re
import time
import unittest
from unittest import mock

import frappe
from erpnext import get_default_company
from erpnext.projects.doctype.project.project import Project
from frappe.tests.utils import FrappeTestCase
from frappe.utils.file_manager import save_file

from portal_app import install
from portal_app.api import files, gantt, helper, portal_admin, projects, search, teams
from portal_app.tests.test_portal_roles import PortalRoleTestBase, _project, _user

DEPT_DT = "Department"
COORD_DT = "Portal Department Coordinator"
LINK_DT = "Portal Project Link"
LINK_USER_DT = "Portal Project Link User"
TEAM_MANAGER = "Team Manager"
DEPT_COORDINATOR = "Department Coordinator"
LINK_TYPES = ("T Server", "Autodesk Server", "ERP")

# ERPNext 15.121 revokes a removed Project User's DocShare as that user, which fails
# ("User not allowed to delete DocShare"); live (15.101) has no such method. The revoke
# is a function nested in Project.control_access_for_project_users, so test for that.
ERPNEXT_REVOKES_SHARES = hasattr(Project, "control_access_for_project_users")
SKIP_REVOKE = "ERPNext 15.121-only DocShare revoke path"

SECRET_PATH = "T:\\My Drive\\BC-SECRET-PATH-7f3a91"
SECRET_URL = "https://drive.google.com/drive/folders/BC-SECRET-URL-c4e2b8"

APP_DIR = os.path.dirname(os.path.abspath(frappe.get_app_path("portal_app")))
FRONTEND_SRC = os.path.join(APP_DIR, "frontend", "src")


# ---------------------------------------------------------------------------------------
# lazily-imported modules (so a missing module fails each test, not the whole file)
# ---------------------------------------------------------------------------------------
def _links():
	return importlib.import_module("portal_app.api.links")


def _patch(name):
	return importlib.import_module("portal_app.patches." + name)


def _script():
	return importlib.import_module("portal_app.scripts.apply_ata_role_hierarchy")


def _company():
	return get_default_company() or frappe.get_all("Company", pluck="name")[0]


def _abbr():
	return frappe.db.get_value("Company", _company(), "abbr")


def _dept_has(field):
	return frappe.get_meta(DEPT_DT).has_field(field)


def _purge_departments(prefix):
	"""Delete leftover fixture departments (children before parents)."""
	rows = frappe.get_all(
		DEPT_DT, filters={"department_name": ["like", prefix + "%"]}, fields=["name"], order_by="lft desc"
	)
	for r in rows:
		if frappe.db.exists(DEPT_DT, r.name):
			frappe.delete_doc(DEPT_DT, r.name, force=1, ignore_permissions=True)


def _purge_links(project_prefix):
	if not frappe.db.table_exists(LINK_DT):
		return
	projects_ = frappe.get_all("Project", filters={"project_name": ["like", project_prefix + "%"]}, pluck="name")
	if projects_:
		for name in frappe.get_all(LINK_DT, filters={"project": ["in", projects_]}, pluck="name"):
			frappe.delete_doc(LINK_DT, name, force=1, ignore_permissions=True)


def _purge_fresh_projects():
	"""Delete leftover "BC fresh" projects. files.share_file_with_user commits mid-test,
	so they outlive the class rollback and make their Project Lead a project_lead (V9)."""
	names = frappe.get_all("Project", filters={"project_name": ["like", "BC fresh %"]}, pluck="name")
	if not names:
		return
	if frappe.db.table_exists(LINK_DT):
		for name in frappe.get_all(LINK_DT, filters={"project": ["in", names]}, pluck="name"):
			frappe.delete_doc(LINK_DT, name, force=1, ignore_permissions=True)
	frappe.db.delete("Project User", {"parenttype": "Project", "parent": ["in", names]})
	frappe.db.delete("ToDo", {"reference_type": "Project", "reference_name": ["in", names]})
	for name in names:
		frappe.delete_doc("Project", name, force=1, ignore_permissions=True)


def _unit(label, unit, parent="All Departments", office="", pending=0, is_group=0):
	"""A Department row; `unit` is "Department" or "Team". Tolerant before the custom fields exist."""
	existing = frappe.db.get_value(DEPT_DT, {"department_name": label})
	if existing:
		frappe.delete_doc(DEPT_DT, existing, force=1, ignore_permissions=True)
	doc = frappe.get_doc(
		{
			"doctype": DEPT_DT,
			"department_name": label,
			"company": _company(),
			"parent_department": parent,
			"is_group": is_group,
			"portal_office": office,
		}
	)
	if _dept_has("portal_unit"):
		doc.portal_unit = unit
	if _dept_has("portal_pending"):
		doc.portal_pending = pending
	return doc.insert(ignore_permissions=True).name


def _add_rows(dept, admins=(), coordinators=(), lead=None):
	"""Set designations the way the script does: append + save (the hook syncs markers)."""
	doc = frappe.get_doc(DEPT_DT, dept)
	for u in admins:
		if u not in {r.user for r in doc.get("portal_department_admins") or []}:
			doc.append("portal_department_admins", {"user": u})
	if coordinators and _dept_has("portal_department_coordinators"):
		for u in coordinators:
			if u not in {r.user for r in doc.get("portal_department_coordinators") or []}:
				doc.append("portal_department_coordinators", {"user": u})
	if lead:
		doc.portal_team_lead = lead
	doc.save(ignore_permissions=True)


def _remove_rows(dept, field, user):
	doc = frappe.get_doc(DEPT_DT, dept)
	for row in list(doc.get(field) or []):
		if row.user == user:
			doc.remove(row)
	doc.save(ignore_permissions=True)


def _rows(dept, field):
	if not _dept_has(field):
		return set()
	return {r.user for r in frappe.get_doc(DEPT_DT, dept).get(field) or []}


def _in_team(team, user):
	return bool(
		frappe.db.exists(
			"ToDo",
			{"reference_type": DEPT_DT, "reference_name": team, "allocated_to": user, "status": "Open"},
		)
	)


def _project_users(project):
	return {r.user for r in frappe.get_doc("Project", project).users}


def _dump(obj):
	return json.dumps(obj, default=str)


def _methods(fn):
	return list(frappe.allowed_http_methods_for_whitelisted_func.get(fn, []))


def _entries(resp):
	"""get_project_links may return the entry list itself or {"links": [...], ...}."""
	if isinstance(resp, dict):
		return resp.get("links") or resp.get("portal_links") or []
	return resp or []


def _by_type(entries):
	return {e["link_type"]: e for e in entries}


def _portal_links_of(resp):
	"""portal_links of a get_project / project_dashboard response (top level or on "project")."""
	if "portal_links" in resp:
		return resp["portal_links"]
	return (resp.get("project") or {}).get("portal_links")


class BatchCBase(PortalRoleTestBase):
	"""Section 9.1 fixture: departments over teams, every role, five projects."""

	_counter = 0

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		_purge_fresh_projects()
		frappe.db.commit()  # only the purge: FrappeTestCase.setUpClass has just committed
		_purge_links("BC ")
		_purge_departments("BC ")
		for name in ("ensure_department_portal_custom_fields",):
			fn = getattr(install, name, None)
			if fn:
				fn()
		helper.ensure_portal_roles()

		# units
		cls.dc = _unit("BC Concept", "Department", is_group=1)
		cls.tc1 = _unit("BC Team One", "Team", parent=cls.dc, office="LISBON")
		cls.tc2 = _unit("BC Team Two", "Team", parent=cls.dc, office="MANILA")
		cls.dt = _unit("BC Technical", "Department", is_group=1)
		cls.tt1 = _unit("BC Tech Team", "Team", parent=cls.dt, office="CAIRO")
		cls.dhr = _unit("BC HR", "Department")
		cls.dp = _unit("BC Pending", "Department", is_group=1, pending=1)
		cls.tp1 = _unit("BC Pending Team", "Team", parent=cls.dp)

		# users
		cls.coord = _user("bccoord")
		cls.dadmin = _user("bcdadmin")
		cls.hradmin = _user("bchradmin")
		cls.tm1 = _user("bctm1")
		cls.arch1 = _user("bcarch1")
		cls.arch2 = _user("bcarch2")
		cls.tarch = _user("bctarch")
		cls.pend = _user("bcpend")
		cls.dual = _user("bcdual")
		cls.sup = _user("bcsup")

		# team membership (open ToDo on the team)
		teams._assign_users_to_team(cls.tc1, [cls.tm1, cls.arch1])
		teams._assign_users_to_team(cls.tc2, [cls.arch2])
		teams._assign_users_to_team(cls.tt1, [cls.dual, cls.tarch, cls.sup])
		teams._assign_users_to_team(cls.tp1, [cls.pend])

		# designations, the way the script sets them
		_add_rows(cls.dc, admins=[cls.dadmin], coordinators=[cls.coord])
		_add_rows(cls.dhr, admins=[cls.hradmin])
		_add_rows(cls.dt, admins=[cls.dual])
		_add_rows(cls.dp, admins=[cls.pend])
		_add_rows(cls.tc1, lead=cls.tm1)
		_add_rows(cls.tt1, lead=cls.dual)
		_add_rows(cls.tp1, lead=cls.pend)

		# projects
		cls.p1 = _project("BC P1", [cls.arch1], lead=cls.arch1, team=cls.tc1)
		cls.p2 = _project("BC P2", [cls.arch2], team=cls.tc2)
		cls.p3 = _project("BC P3", [cls.tarch], team=cls.tt1)
		cls.p4 = _project("BC P4 orphan")
		cls.p5 = _project("BC P5", [cls.pend], lead=cls.pend)

	@classmethod
	def tearDownClass(cls):
		# Undo the class first, then drop whatever a mid-test commit kept, for the next run.
		frappe.set_user("Administrator")
		frappe.db.rollback()
		_purge_fresh_projects()
		frappe.db.commit()
		super().tearDownClass()

	# -- helpers ----------------------------------------------------------------------
	def bc(self, user):
		"""Fixture projects this user may see, by key."""
		allowed = set(helper.get_allowed_project_names(user))
		return {
			k
			for k, p in {"p1": self.p1, "p2": self.p2, "p3": self.p3, "p4": self.p4, "p5": self.p5}.items()
			if p in allowed
		}

	@classmethod
	def _unique(cls, prefix):
		cls._counter += 1
		return f"{prefix}{cls._counter}{frappe.generate_hash(length=5)}".lower()

	def fresh_user(self, team=None, roles=("Projects User",)):
		frappe.set_user("Administrator")
		u = _user(self._unique("bcx"), roles)
		if team:
			teams._assign_users_to_team(team, [u])
		return u

	def fresh_project(self, users=(), lead=None, team=None):
		frappe.set_user("Administrator")
		return _project("BC fresh " + self._unique("p"), list(users), lead=lead, team=team)


# =====================================================================================
# Model / markers (M1-M4) + DocType / custom field shape
# =====================================================================================
class TestUnitModel(BatchCBase):
	def test_constants_and_labels(self):
		self.assertEqual(helper.TEAM_MANAGER_ROLE, TEAM_MANAGER)
		self.assertEqual(helper.TEAM_LEAD_ROLE, helper.TEAM_MANAGER_ROLE)  # alias kept for old callers
		self.assertEqual(helper.LEGACY_TEAM_LEAD_ROLE, "Team Lead")
		self.assertEqual(helper.DEPT_COORDINATOR_ROLE, DEPT_COORDINATOR)
		self.assertEqual(helper.DEPARTMENT_COORDINATOR_DOCTYPE, COORD_DT)
		self.assertEqual(helper.PROJECT_LINK_DOCTYPE, LINK_DT)
		self.assertEqual(tuple(helper.LINK_TYPES), LINK_TYPES)
		self.assertIn(DEPT_COORDINATOR, helper.PORTAL_ROLES)
		self.assertEqual(
			helper.ROLE_LABELS,
			{
				"super_admin": "Super Admin",
				"department_admin": "Department Admin",
				"department_coordinator": "Department Coordinator",
				"team_lead": "Team Manager",
				"project_lead": "Project Lead",
				"team_member": "Project Architect",
				"client_customer": "Client Customer",
			},
		)
		self.assertEqual(helper.ROLE_KEY_ALIASES, {"team_manager": "team_lead", "project_architect": "team_member"})

	def test_new_doctypes_shape(self):
		coord = frappe.get_meta(COORD_DT)
		self.assertTrue(coord.istable)
		f = coord.get_field("user")
		self.assertEqual((f.fieldtype, f.options, f.reqd), ("Link", "User", 1))

		link_user = frappe.get_meta(LINK_USER_DT)
		self.assertTrue(link_user.istable)
		self.assertEqual(link_user.get_field("user").options, "User")

		link = frappe.get_meta(LINK_DT)
		self.assertFalse(link.istable)
		self.assertEqual(link.autoname, "hash")
		self.assertTrue(link.track_changes)
		self.assertEqual(link.get_field("project").options, "Project")
		self.assertTrue(link.get_field("project").reqd)
		self.assertEqual(link.get_field("link_type").fieldtype, "Select")
		self.assertEqual(link.get_field("link_type").options.split("\n"), list(LINK_TYPES))
		self.assertEqual(link.get_field("copy_path").fieldtype, "Small Text")
		self.assertEqual(link.get_field("open_url").fieldtype, "Small Text")
		self.assertEqual(link.get_field("allowed_users").fieldtype, "Table")
		self.assertEqual(link.get_field("allowed_users").options, LINK_USER_DT)
		# System Manager only: no other role may read it through Desk / REST
		self.assertEqual({p.role for p in link.permissions}, {"System Manager"})

	def test_custom_fields(self):
		dept = frappe.get_meta(DEPT_DT)
		unit = dept.get_field("portal_unit")
		self.assertEqual(unit.fieldtype, "Select")
		self.assertEqual(set(filter(None, unit.options.split("\n"))), {"Department", "Team"})
		self.assertEqual(dept.get_field("portal_pending").fieldtype, "Check")
		coords = dept.get_field("portal_department_coordinators")
		self.assertEqual((coords.fieldtype, coords.options), ("Table", COORD_DT))
		self.assertEqual(dept.get_field("portal_team_lead").label, "Portal Team Manager")
		proj = frappe.get_meta("Project")
		self.assertEqual(proj.get_field("portal_project_manager").label, "Project Lead")
		for f in ("portal_server_t", "portal_server_a", "portal_server_c"):
			df = proj.get_field(f)
			self.assertIsNotNone(df, f)  # the column is kept
			self.assertTrue(df.hidden and df.read_only, f)

	def test_patches_registered(self):
		with open(frappe.get_app_path("portal_app", "patches.txt")) as fh:
			text = fh.read()
		pre, _, post = text.partition("[post_model_sync]")
		self.assertIn("portal_app.patches.rename_team_lead_role", pre)
		lines = [ln.strip() for ln in post.splitlines() if ln.strip() and not ln.strip().startswith("#")]
		self.assertEqual(
			lines[-2:],
			["portal_app.patches.mark_portal_teams", "portal_app.patches.migrate_project_server_links"],
		)

	def test_m1_team_lead_role_is_renamed(self):
		if not frappe.db.exists("Role", "Team Lead"):
			frappe.get_doc({"doctype": "Role", "role_name": "Team Lead", "desk_access": 1}).insert(ignore_permissions=True)
		patch = _patch("rename_team_lead_role")
		patch.execute()
		patch.execute()  # idempotent
		self.assertTrue(frappe.db.exists("Role", TEAM_MANAGER))
		self.assertFalse(frappe.db.exists("Role", "Team Lead"))
		helper.ensure_portal_roles()  # never recreates the old role
		self.assertFalse(frappe.db.exists("Role", "Team Lead"))
		self.assertTrue(frappe.db.exists("Role", TEAM_MANAGER))
		self.assertTrue(frappe.db.exists("Role", DEPT_COORDINATOR))

	def test_m2_mark_portal_teams(self):
		legacy = _unit("BC Legacy Blank", "", office="RIYADH")
		frappe.db.set_value(DEPT_DT, legacy, "portal_unit", "", update_modified=False)
		patch = _patch("mark_portal_teams")
		patch.execute()
		self.assertEqual(frappe.db.get_value(DEPT_DT, legacy, "portal_unit"), "Team")
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.dhr, "portal_unit"), "Department")  # untouched
		patch.execute()
		self.assertEqual(frappe.db.get_value(DEPT_DT, legacy, "portal_unit"), "Team")

	def test_m3_team_names(self):
		names = set(helper.portal_team_names())
		self.assertTrue({self.tc1, self.tc2, self.tt1, self.d1, self.d2} <= names)
		self.assertTrue({self.dc, self.dt, self.dhr, self.dp, self.tp1}.isdisjoint(names))
		self.assertIn(self.tp1, set(helper.portal_team_names(include_pending=True)))
		self.assertEqual(sorted(helper.portal_department_names()), sorted(helper.portal_team_names()))
		units = set(helper.portal_unit_department_names())
		self.assertTrue({self.dc, self.dt, self.dhr} <= units)
		self.assertNotIn(self.dp, units)
		self.assertIn(self.dp, set(helper.portal_unit_department_names(include_pending=True)))
		self.assertTrue({self.dp, self.tp1} <= set(helper.pending_unit_names()))
		self.assertEqual(sorted(helper.teams_of_unit(self.dc)), sorted([self.tc1, self.tc2]))
		self.assertEqual(helper.teams_of_unit(self.tc1), [self.tc1])
		self.assertEqual(helper.teams_of_unit(self.dhr), [])
		self.assertEqual(helper.team_department(self.tc1), self.dc)
		self.assertEqual(helper.team_department(self.tt1), self.dt)
		self.assertIsNone(helper.team_department(self.d1))

	def test_m4_marker_roles(self):
		self.assertIn(DEPT_COORDINATOR, frappe.get_roles(self.coord))
		self.assertIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.dadmin))
		self.assertIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.hradmin))
		self.assertIn(TEAM_MANAGER, frappe.get_roles(self.tm1))
		self.assertNotIn("Team Lead", frappe.get_roles(self.tm1))
		self.assertNotIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.pend))
		self.assertNotIn(TEAM_MANAGER, frappe.get_roles(self.pend))

		frappe.set_user(self.super_admin)
		teams.set_department_pending(self.dp, 0)
		try:
			self.assertIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.pend))
			self.assertIn(TEAM_MANAGER, frappe.get_roles(self.pend))
		finally:
			frappe.set_user(self.super_admin)
			teams.set_department_pending(self.dp, 1)
		self.assertNotIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.pend))
		self.assertNotIn(TEAM_MANAGER, frappe.get_roles(self.pend))

	def test_designation_readers_ignore_pending(self):
		self.assertEqual(helper.admin_department_names(self.pend), [])
		self.assertEqual(helper.led_department_names(self.pend), [])
		self.assertEqual(helper.coordinator_department_names(self.coord), [self.dc])
		self.assertEqual(helper.admin_department_names(self.dadmin), [self.dc])
		self.assertEqual(sorted(helper.scope_department_names(self.coord)), sorted([self.tc1, self.tc2]))  # teams
		self.assertEqual(sorted(helper.scope_department_names(self.dadmin)), sorted([self.tc1, self.tc2]))
		self.assertEqual(helper.scope_department_names(self.hradmin), [])
		self.assertEqual(helper.managed_team_names(self.tm1), [self.tc1])


# =====================================================================================
# Visibility (V1-V10)
# =====================================================================================
class TestVisibility(BatchCBase):
	def test_v1_coordinator_sees_department_and_unassigned(self):
		seen = self.bc(self.coord)
		self.assertTrue({"p1", "p2", "p4"} <= seen)
		self.assertNotIn("p3", seen)
		self.assertTrue(helper.sees_unassigned_projects(self.coord))

	def test_v2_department_level_admin_does_not_see_unassigned(self):
		self.assertEqual(self.bc(self.dadmin), {"p1", "p2"})
		self.assertFalse(helper.sees_unassigned_projects(self.dadmin))

	def test_v3_legacy_team_row_admin_unchanged(self):
		self.assertTrue({"pa", "pc", "pd", "pe"} <= self.names(self.admin))
		self.assertIn("p4", self.bc(self.admin))
		self.assertTrue(helper.sees_unassigned_projects(self.admin))

	def test_v4_hr_admin_sees_only_own(self):
		self.assertEqual(self.bc(self.hradmin), set())

	def test_v5_team_manager(self):
		self.assertEqual(self.bc(self.tm1), {"p1"})

	def test_v6_architects(self):
		self.assertEqual(self.bc(self.arch1), {"p1"})
		self.assertEqual(self.bc(self.arch2), {"p2"})
		self.assertEqual(self.bc(self.sup), set())

	def test_v7_pending_designations_change_nothing(self):
		self.assertEqual(self.bc(self.pend), {"p5"})

	def test_v8_two_designations_union(self):
		self.assertEqual(self.bc(self.dual), {"p3"})

	def test_v9_portal_role(self):
		self.assertEqual(helper.get_portal_role(self.coord), "department_coordinator")
		self.assertEqual(helper.get_portal_role(self.tm1), "team_lead")
		self.assertEqual(helper.get_portal_role(self.arch1), "project_lead")
		self.assertEqual(helper.get_portal_role(self.arch2), "team_member")
		self.assertEqual(helper.get_portal_role(self.dadmin), "department_admin")
		self.assertEqual(helper.get_portal_role("Administrator"), "super_admin")
		self.assertEqual(helper.get_portal_role(self.client), "client_customer")
		self.assertEqual(helper.ROLE_LABELS["team_lead"], "Team Manager")
		self.assertEqual(helper.ROLE_LABELS["team_member"], "Project Architect")

	def test_v10_designations(self):
		dual = {(d["role"], d.get("unit")): d for d in helper.get_portal_designations(self.dual)}
		self.assertIn(("team_lead", self.tt1), dual)
		self.assertIn(("department_admin", self.dt), dual)
		self.assertFalse(dual[("team_lead", self.tt1)]["pending"])
		for d in dual.values():
			self.assertTrue({"role", "label", "unit", "unit_label", "pending"} <= set(d))
		pend = {(d["role"], d.get("unit")): d for d in helper.get_portal_designations(self.pend)}
		self.assertTrue(pend[("department_admin", self.dp)]["pending"])
		self.assertTrue(pend[("team_lead", self.tp1)]["pending"])
		lead = [d for d in helper.get_portal_designations(self.arch1) if d["role"] == "project_lead"]
		self.assertEqual(len(lead), 1)
		self.assertGreaterEqual(lead[0]["count"], 1)
		admin = helper.get_portal_designations("Administrator")
		self.assertEqual([d["role"] for d in admin], ["super_admin"])

	def test_rights(self):
		self.assertTrue(helper.can_manage_project(self.p1, self.coord))
		self.assertTrue(helper.can_manage_project(self.p4, self.coord))
		self.assertFalse(helper.can_manage_project(self.p3, self.coord))
		self.assertTrue(helper.can_add_project_members(self.p1, self.coord))
		self.assertTrue(helper.can_remove_project_members(self.p1, self.coord))
		self.assertTrue(helper.can_add_project_members(self.p1, self.tm1))
		self.assertFalse(helper.can_remove_project_members(self.p1, self.tm1))
		self.assertTrue(helper.can_view_org_chart(self.coord))
		# coordinators manage no people and see no money; not in the admin tier
		self.assertFalse(helper.can_manage_team(self.tc1, self.coord))
		self.assertFalse(helper.can_reset_password_for(self.arch1, self.coord))
		self.assertFalse(helper.can_view_project_value(self.p1, self.coord))
		self.assertFalse(helper.has_portal_staff_project_access(self.coord))
		# a department-level DA manages the teams of their department only
		self.assertTrue(helper.can_manage_team(self.tc1, self.dadmin))
		self.assertFalse(helper.can_manage_team(self.tt1, self.dadmin))
		self.assertTrue(helper.can_reset_password_for(self.arch1, self.dadmin))
		self.assertFalse(helper.can_reset_password_for(self.tarch, self.dadmin))
		self.assertFalse(helper.can_reset_password_for(self.coord, self.coord))

	def test_department_member_users(self):
		people = helper.department_member_users([self.dc])
		self.assertTrue({self.tm1, self.arch1, self.arch2, self.dadmin, self.coord} <= people)
		self.assertNotIn(self.tarch, people)
		self.assertNotIn(self.client, people)

	def test_project_permission_hook_covers_coordinator(self):
		self.assertIsNone(helper.project_has_permission(frappe.get_doc("Project", self.p1), "read", self.coord))
		self.assertIs(helper.project_has_permission(frappe.get_doc("Project", self.p3), "read", self.coord), False)


# =====================================================================================
# Org chart / teams (O1-O5)
# =====================================================================================
class TestOrgChartC(BatchCBase):
	def chart(self, user):
		frappe.set_user(user)
		return teams.get_org_chart()

	@staticmethod
	def dept_names(chart):
		return {d["name"] for d in chart["departments"] if d["name"]}

	@staticmethod
	def all_team_names(chart):
		out = {t["name"] for t in chart["teams"]}
		for d in chart["departments"]:
			out |= {t["name"] for t in d["teams"]}
		return out

	def test_o1_coordinator_chart_read_only(self):
		chart = self.chart(self.coord)
		self.assertEqual(self.dept_names(chart), {self.dc})
		dc = next(d for d in chart["departments"] if d["name"] == self.dc)
		self.assertEqual({t["name"] for t in dc["teams"]}, {self.tc1, self.tc2})
		self.assertFalse(dc["can_edit"])
		self.assertFalse(any(t["can_edit"] for t in dc["teams"]))
		self.assertFalse(any(t["can_edit"] for t in chart["teams"]))
		frappe.set_user(self.coord)
		got = teams.get_teams()
		self.assertEqual({t["name"] for t in got}, {self.tc1, self.tc2})
		self.assertFalse(any(t["can_edit"] for t in got))

	def test_o2_department_admin_sees_only_own_department(self):
		chart = self.chart(self.dadmin)
		self.assertEqual(self.dept_names(chart), {self.dc})
		self.assertEqual(self.all_team_names(chart), {self.tc1, self.tc2})
		frappe.set_user(self.dadmin)
		self.assertEqual({t["name"] for t in teams.get_teams()}, {self.tc1, self.tc2})
		chart = self.chart(self.hradmin)
		self.assertEqual(self.dept_names(chart), {self.dhr})
		self.assertEqual(self.all_team_names(chart), set())
		frappe.set_user(self.hradmin)
		self.assertEqual(teams.get_teams(), [])

	def test_o3_pending_departments_super_admin_only(self):
		chart = self.chart(self.super_admin)
		depts = {d["name"]: d for d in chart["departments"]}
		self.assertTrue(depts[self.dp]["pending"])
		self.assertFalse(depts[self.dc]["pending"])
		self.assertIn(self.tp1, {t["name"] for t in depts[self.dp]["teams"]})
		self.assertTrue({self.dc, self.dt, self.dhr} <= set(depts))
		# legacy teams with no department under the "Other teams" pseudo group
		other = depts.get("")
		self.assertIsNotNone(other)
		self.assertIn(self.d1, {t["name"] for t in other["teams"]})
		self.assertIn("can_change_roles", chart["me"])
		for user in (self.coord, self.dadmin, self.tm1, self.hradmin):
			chart = self.chart(user)
			self.assertNotIn(self.dp, self.dept_names(chart), user)
			self.assertNotIn(self.tp1, self.all_team_names(chart), user)

	def test_o4_team_manager_sees_their_team(self):
		chart = self.chart(self.tm1)
		self.assertEqual(self.all_team_names(chart), {self.tc1})
		frappe.set_user(self.tm1)
		self.assertEqual({t["name"] for t in teams.get_teams()}, {self.tc1})

	def test_o5_department_endpoints_super_admin_and_post_only(self):
		for name in ("create_portal_department", "set_department_pending", "set_team_department"):
			fn = getattr(teams, name)
			self.assertEqual(_methods(fn), ["POST"], name)
		for user in (self.dadmin, self.coord, self.tm1, self.arch1):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				teams.create_portal_department("BC Refused Dept")
			with self.assertRaises(frappe.PermissionError):
				teams.set_department_pending(self.dc, 1)
			with self.assertRaises(frappe.PermissionError):
				teams.set_team_department(self.tc1, self.dt)
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.tc1, "parent_department"), self.dc)

	def test_super_admin_department_endpoints(self):
		frappe.set_user(self.super_admin)
		res = teams.create_portal_department("BC Created Dept", pending=1)
		name = res["name"] if isinstance(res, dict) else res
		row = frappe.db.get_value(DEPT_DT, name, ["portal_unit", "portal_pending", "is_group", "parent_department"], as_dict=True)
		self.assertEqual((row.portal_unit, row.portal_pending, row.is_group), ("Department", 1, 1))
		self.assertEqual(row.parent_department, "All Departments")
		again = teams.create_portal_department("BC Created Dept")
		self.assertEqual(again["name"] if isinstance(again, dict) else again, name)  # exact name -> existing
		team = _unit("BC Movable Team", "Team", office="RIYADH")
		frappe.set_user(self.super_admin)
		teams.set_team_department(team, self.dhr)  # leaf department becomes a group first
		self.assertEqual(frappe.db.get_value(DEPT_DT, team, "parent_department"), self.dhr)
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.dhr, "is_group"), 1)
		with self.assertRaises(frappe.ValidationError):
			teams.set_team_department(team, self.tc1)  # not a Department unit

	def test_create_or_get_team_under_department(self):
		frappe.set_user(self.super_admin)
		res = teams.create_or_get_team("BC Created Team", office="RIYADH", department=self.dt)
		name = res["name"] if isinstance(res, dict) else res
		self.assertEqual(frappe.db.get_value(DEPT_DT, name, "portal_unit"), "Team")
		self.assertEqual(frappe.db.get_value(DEPT_DT, name, "parent_department"), self.dt)

	def test_set_member_role_accepts_new_keys(self):
		u = self.fresh_user(team=self.tc2)
		frappe.set_user(self.super_admin)
		self.addCleanup(frappe.db.set_value, DEPT_DT, self.tc2, "portal_team_lead", None)
		teams.set_member_role(self.tc2, u, "team_manager")
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.tc2, "portal_team_lead"), u)
		teams.set_member_role(self.tc2, u, "project_architect")
		self.assertFalse(frappe.db.get_value(DEPT_DT, self.tc2, "portal_team_lead"))


# =====================================================================================
# Project rules (P1-P5)
# =====================================================================================
class TestProjectRulesC(BatchCBase):
	def test_lead_picker_for_coordinator_and_team_manager_is_staff_only(self):
		for user in (self.coord, self.tm1):
			frappe.set_user(user)
			names = {u.name for u in projects.get_portal_users()}
			self.assertIn(self.arch1, names)
			self.assertNotIn(self.client, names)
		frappe.set_user(self.arch2)
		self.assertEqual(projects.get_portal_users(), [])

	def test_p1_coordinator_allocates_projects(self):
		orphan = self.fresh_project()
		frappe.set_user(self.coord)
		projects.update_project(orphan, portal_team=self.tc1)
		self.assertEqual(frappe.db.get_value("Project", orphan, "portal_team"), self.tc1)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(orphan, portal_team=self.tt1)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(self.p3, portal_team="")
		self.assertEqual(frappe.db.get_value("Project", self.p3, "portal_team"), self.tt1)
		# a project of their own department may be cleared
		projects.update_project(orphan, portal_team="")
		self.assertFalse(frappe.db.get_value("Project", orphan, "portal_team"))

	def test_coordinator_cannot_take_a_project_from_another_department(self):
		other = self.fresh_project(users=[self.coord], team=self.tt1)  # visible (own), team not theirs
		frappe.set_user(self.coord)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(other, portal_team="")
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(other, portal_team=self.tc1)
		self.assertEqual(frappe.db.get_value("Project", other, "portal_team"), self.tt1)

	def test_p2_department_admin_sets_team_within_department(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		frappe.set_user(self.dadmin)
		projects.update_project(p, portal_team=self.tc2)
		self.assertEqual(frappe.db.get_value("Project", p, "portal_team"), self.tc2)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(p, portal_team=self.tt1)

	def test_p3_team_manager_project_lead_and_members(self):
		p = self.fresh_project(users=[self.arch1, self.arch2], lead=self.arch1, team=self.tc1)
		frappe.set_user(self.arch1)  # the Project Lead adds Project Architects
		projects.add_project_members(p, [self.tm1])
		self.assertIn(self.tm1, _project_users(p))
		frappe.set_user(self.tm1)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(p, portal_project_manager=self.tm1)  # not over someone else
		projects.update_project(p, portal_project_manager=self.arch2)
		self.assertEqual(frappe.db.get_value("Project", p, "portal_project_manager"), self.arch2)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(p, portal_project_manager=self.client)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(p, portal_team=self.tc2)  # a team manager does not re-allocate
		frappe.set_user(self.tm1)
		projects.add_project_members(p, [self.sup])
		self.assertIn(self.sup, _project_users(p))
		with self.assertRaises(frappe.PermissionError):
			projects.remove_project_members(p, [self.sup])
		self.assertIn(self.sup, _project_users(p))

	def test_coordinator_sets_project_lead(self):
		p = self.fresh_project(users=[self.arch1, self.arch2], lead=self.arch1, team=self.tc1)
		frappe.set_user(self.coord)
		projects.update_project(p, portal_project_manager=self.arch2)
		self.assertEqual(frappe.db.get_value("Project", p, "portal_project_manager"), self.arch2)
		with self.assertRaises(frappe.PermissionError):
			projects.update_project(p, portal_project_manager=self.coord)

	def test_p4_coordinator_adds_members(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		frappe.set_user(self.coord)
		projects.add_project_members(p, [self.arch2])
		self.assertEqual(_project_users(p), {self.arch1, self.arch2})

	@unittest.skipIf(ERPNEXT_REVOKES_SHARES, SKIP_REVOKE)
	def test_p4_coordinator_removes_members(self):
		p = self.fresh_project(users=[self.arch1, self.arch2], team=self.tc1)
		frappe.set_user(self.coord)
		projects.remove_project_members(p, [self.arch2])
		self.assertEqual(_project_users(p), {self.arch1})

	def test_coordinator_has_no_contracts_or_delete_on_projects_not_their_own(self):
		"""Spec Q7: a Coordinator gets explicit rights only. p4 is unassigned: visible and
		manageable for them, but no Contracts and no delete."""
		from portal_app.api import contracts

		frappe.set_user(self.coord)
		self.assertTrue(helper.can_manage_project(self.p4))
		self.assertFalse(helper.can_manage_project_records(self.p4))
		with self.assertRaises(frappe.PermissionError):
			contracts.list_contract_files(self.p4)
		with self.assertRaises(frappe.PermissionError):
			contracts.upload_contract_file(self.p4)
		with self.assertRaises(frappe.PermissionError):
			contracts.delete_contract_file(self.p4, "nothing")
		with self.assertRaises(frappe.PermissionError):
			projects.delete_project(self.p4)
		self.assertTrue(frappe.db.exists("Project", self.p4))
		# their own project: unchanged
		own = self.fresh_project(users=[self.coord], team=self.tc1)
		frappe.set_user(self.coord)
		self.assertTrue(helper.can_manage_project_records(own))
		self.assertEqual(contracts.list_contract_files(own), [])
		projects.delete_project(own)
		self.assertFalse(frappe.db.exists("Project", own))

	def test_admin_and_team_manager_keep_contracts(self):
		from portal_app.api import contracts

		frappe.set_user(self.dadmin)
		self.assertEqual(contracts.list_contract_files(self.p1), [])
		frappe.set_user(self.tm1)
		self.assertTrue(helper.can_manage_project_records(self.p1))
		self.assertEqual(contracts.list_contract_files(self.p1), [])
		frappe.set_user(self.arch2)
		self.assertFalse(helper.can_manage_project_records(self.p1))

	def test_coordinator_and_team_manager_see_and_clear_the_project_lead(self):
		p = self.fresh_project(users=[self.arch1, self.arch2], lead=self.arch1, team=self.tc1)
		for caller in (self.coord, self.tm1):
			frappe.set_user("Administrator")
			frappe.db.set_value("Project", p, "portal_project_manager", self.arch1)
			frappe.set_user(caller)
			self.assertEqual(projects.get_project(p)["project"].get("portal_project_manager"), self.arch1, caller)
			self.assertEqual(projects.project_dashboard(p)["project"].get("portal_project_manager"), self.arch1, caller)
			row = next(x for x in projects.list_projects()["projects"] if x["name"] == p)
			self.assertEqual(row.get("portal_project_manager"), self.arch1, caller)
			self.assertNotIn("estimated_costing", row)  # money stays hidden
			projects.update_project(p, portal_project_manager="")
			self.assertFalse(frappe.db.get_value("Project", p, "portal_project_manager"), caller)
		# a Project Architect still is not shown it, and their blank changes nothing
		frappe.set_user("Administrator")
		frappe.db.set_value("Project", p, "portal_project_manager", self.arch1)
		frappe.set_user(self.arch2)
		self.assertNotIn("portal_project_manager", projects.get_project(p)["project"])
		row = next(x for x in projects.list_projects()["projects"] if x["name"] == p)
		self.assertNotIn("portal_project_manager", row)
		projects.update_project(p, portal_project_manager="")
		self.assertEqual(frappe.db.get_value("Project", p, "portal_project_manager"), self.arch1)

	def test_p5_capabilities(self):
		frappe.set_user(self.coord)
		caps = projects.get_capabilities()
		self.assertEqual(caps["portal_role"], "department_coordinator")
		self.assertTrue(caps["can_view_org_chart"])
		self.assertFalse(caps["is_manager"])
		self.assertTrue(caps["is_department_coordinator"])
		self.assertEqual(caps["coordinator_department_names"], [self.dc])
		self.assertTrue(caps["can_assign_project_lead"])
		self.assertIn("portal_role_designations", caps)
		frappe.set_user(self.tm1)
		caps = projects.get_capabilities()
		self.assertTrue(caps["is_team_manager"] and caps["is_team_lead"])

	def test_assignable_projects_for_coordinator(self):
		frappe.set_user(self.coord)
		names = {p["name"] for p in projects.get_assignable_projects(self.arch1)}
		self.assertTrue({self.p1, self.p2, self.p4} <= names)
		self.assertNotIn(self.p3, names)

	def test_supervision_sharing_keeps_working(self):
		"""S-share: a file on p1 shared with a Projects User who is not on p1."""
		frappe.set_user("Administrator")
		root = files.ensure_project_folders(self.p1)["project_root"]
		f = save_file("bc-share-" + frappe.generate_hash(length=6) + ".txt", b"bc share", "Project", self.p1, folder=root, is_private=1)
		frappe.set_user(self.arch1)
		files.share_file_with_user(self.p1, f.name, self.sup)


# =====================================================================================
# R4 role changes (R1-R10)
# =====================================================================================
class TestChangeUserRole(BatchCBase):
	def change(self, caller, *args, **kw):
		frappe.set_user(caller)
		return portal_admin.change_user_role(*args, **kw)

	def test_r1_super_admin_makes_a_team_manager(self):
		u = self.fresh_user(team=self.tc2)
		p = self.fresh_project(users=[u], team=self.tc2)
		before = helper.own_project_names(u)
		self.addCleanup(frappe.db.set_value, DEPT_DT, self.tc2, "portal_team_lead", None)
		res = self.change(self.super_admin, u, "team_manager", unit=self.tc2)
		self.assertTrue(res["ok"])
		self.assertEqual(res["user"], u)
		self.assertIn(("team_lead", self.tc2), {(d["role"], d.get("unit")) for d in res["designations"]})
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.tc2, "portal_team_lead"), u)
		self.assertIn(TEAM_MANAGER, frappe.get_roles(u))
		self.assertEqual(helper.own_project_names(u), before)
		self.assertIn(p, before)

	def test_new_team_manager_replaces_the_previous_one(self):
		u = self.fresh_user()  # not on the team yet: is added
		frappe.set_user("Administrator")

		def restore():
			frappe.set_user("Administrator")
			_add_rows(self.tc1, lead=self.tm1)

		self.addCleanup(restore)
		self.change(self.super_admin, u, "team_manager", unit=self.tc1)
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.tc1, "portal_team_lead"), u)
		self.assertTrue(_in_team(self.tc1, u))
		self.assertTrue(_in_team(self.tc1, self.tm1))  # previous manager stays a member
		self.assertNotIn(TEAM_MANAGER, frappe.get_roles(self.tm1))

	def test_r2_back_to_project_architect_keeps_team_and_projects(self):
		u = self.fresh_user(team=self.tc2)
		p = self.fresh_project(users=[u], team=self.tc2)
		self.addCleanup(frappe.db.set_value, DEPT_DT, self.tc2, "portal_team_lead", None)
		self.change(self.super_admin, u, "team_manager", unit=self.tc2)
		self.change(self.super_admin, u, "project_architect")
		self.assertFalse(frappe.db.get_value(DEPT_DT, self.tc2, "portal_team_lead"))
		self.assertNotIn(TEAM_MANAGER, frappe.get_roles(u))
		self.assertTrue(_in_team(self.tc2, u))
		self.assertIn(u, _project_users(p))

	def test_r3_department_admin_may_set_coordinator_only_below(self):
		u = self.fresh_user(team=self.tc1)
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dc, "portal_department_coordinators", u)))
		self.change(self.dadmin, u, "department_coordinator", unit=self.dc)
		self.assertIn(u, _rows(self.dc, "portal_department_coordinators"))
		self.assertIn(DEPT_COORDINATOR, frappe.get_roles(u))
		with self.assertRaises(frappe.PermissionError):
			self.change(self.dadmin, u, "department_admin", unit=self.dc)
		with self.assertRaises(frappe.PermissionError):
			self.change(self.dadmin, u, "super_admin")
		self.assertNotIn(u, _rows(self.dc, "portal_department_admins"))
		self.assertNotIn("System Manager", frappe.get_roles(u))

	def test_department_admin_cannot_make_themselves_coordinator(self):
		"""Self-change goes downwards only (spec 7): Coordinator would add unassigned projects."""
		frappe.set_user(self.dadmin)
		self.assertNotIn("department_coordinator", helper.assignable_roles_for(self.dadmin, self.dadmin))
		with self.assertRaises(frappe.PermissionError):
			self.change(self.dadmin, self.dadmin, "department_coordinator", unit=self.dc, keep_other_roles=1)
		self.assertNotIn(self.dadmin, _rows(self.dc, "portal_department_coordinators"))
		self.assertFalse(helper.sees_unassigned_projects(self.dadmin))

	def test_r4_department_admin_cannot_reach_other_departments(self):
		with self.assertRaises(frappe.PermissionError):
			self.change(self.dadmin, self.tarch, "project_architect")
		with self.assertRaises(frappe.PermissionError):
			self.change(self.dadmin, self.tarch, "team_manager", unit=self.tt1)
		u = self.fresh_user(team=self.tc1)
		with self.assertRaises(frappe.PermissionError):
			self.change(self.dadmin, u, "department_coordinator", unit=self.dt)  # foreign unit
		with self.assertRaises(frappe.PermissionError):
			self.change(self.dadmin, u, "team_manager", unit=self.tt1)
		self.assertNotIn(u, _rows(self.dt, "portal_department_coordinators"))
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.tt1, "portal_team_lead"), self.dual)

	def test_r5_department_admin_targets(self):
		c = self.fresh_user(team=self.tc1)
		frappe.set_user("Administrator")
		_add_rows(self.dc, coordinators=[c])
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dc, "portal_department_coordinators", c)))
		self.change(self.dadmin, c, "project_architect")  # a coordinator is below a DA
		self.assertNotIn(c, _rows(self.dc, "portal_department_coordinators"))
		other_da = self.fresh_user(team=self.tc1)
		frappe.set_user("Administrator")
		_add_rows(self.dc, admins=[other_da])
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dc, "portal_department_admins", other_da)))
		for target in (other_da, self.admin, self.super_admin):
			with self.assertRaises(frappe.PermissionError, msg=target):
				self.change(self.dadmin, target, "project_architect")
		self.assertIn(other_da, _rows(self.dc, "portal_department_admins"))

	def test_r6_self_demotion(self):
		da2 = self.fresh_user(team=self.tc1)
		frappe.set_user("Administrator")
		_add_rows(self.dc, admins=[da2])
		self.change(da2, da2, "project_architect")
		self.assertNotIn(da2, _rows(self.dc, "portal_department_admins"))
		self.assertNotIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(da2))
		self.assertIn(self.dadmin, _rows(self.dc, "portal_department_admins"))  # others untouched

	def test_r6_last_super_admin_is_protected(self):
		sa1 = self.fresh_user(roles=("System Manager", "Projects User"))
		with mock.patch.object(portal_admin, "_super_admin_names", return_value=[sa1]):
			with self.assertRaisesRegex((frappe.ValidationError, frappe.PermissionError), "last Super Admin"):
				self.change(sa1, sa1, "project_architect")
			frappe.set_user(sa1)
			with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
				portal_admin.remove_user_designation(sa1, "super_admin")
		self.assertIn("System Manager", frappe.get_roles(sa1))
		# with another Super Admin left it goes through
		self.change(sa1, sa1, "project_architect")
		self.assertNotIn("System Manager", frappe.get_roles(sa1))
		self.assertTrue(helper.is_super_admin(self.super_admin))

	def test_super_admin_grant(self):
		u = self.fresh_user(team=self.tc2)
		self.change(self.super_admin, u, "super_admin")
		self.assertTrue(helper.is_super_admin(u))
		self.assertIn("Projects User", frappe.get_roles(u))

	def test_r7_keep_other_roles(self):
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dt, "portal_department_coordinators", self.dual)))
		self.change(self.super_admin, self.dual, "department_coordinator", unit=self.dt, keep_other_roles=1)
		got = {(d["role"], d.get("unit")) for d in helper.get_portal_designations(self.dual)}
		self.assertTrue(
			{("department_coordinator", self.dt), ("department_admin", self.dt), ("team_lead", self.tt1)} <= got
		)
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.tt1, "portal_team_lead"), self.dual)

	def test_change_replaces_by_default(self):
		u = self.fresh_user(team=self.tc2)
		self.addCleanup(frappe.db.set_value, DEPT_DT, self.tc2, "portal_team_lead", None)
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dc, "portal_department_coordinators", u)))
		self.change(self.super_admin, u, "team_manager", unit=self.tc2)
		self.change(self.super_admin, u, "department_coordinator", unit=self.dc)
		self.assertFalse(frappe.db.get_value(DEPT_DT, self.tc2, "portal_team_lead"))
		self.assertIn(u, _rows(self.dc, "portal_department_coordinators"))
		self.assertTrue(_in_team(self.tc2, u))  # team membership is never removed

	def test_pending_units_super_admin_only(self):
		u = self.fresh_user(team=self.tc1)
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			self.change(self.dadmin, u, "department_coordinator", unit=self.dp)
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dp, "portal_department_coordinators", u)))
		self.change(self.super_admin, u, "department_coordinator", unit=self.dp, keep_other_roles=1)
		self.assertIn(u, _rows(self.dp, "portal_department_coordinators"))
		self.assertNotIn(DEPT_COORDINATOR, frappe.get_roles(u))  # pending: recorded, no marker

	def test_unit_must_have_the_right_kind(self):
		u = self.fresh_user(team=self.tc2)
		with self.assertRaises(frappe.ValidationError):
			self.change(self.super_admin, u, "team_manager", unit=self.dc)  # a department, not a team
		with self.assertRaises(frappe.ValidationError):
			self.change(self.super_admin, u, "department_admin", unit=self.tc2)  # a team, not a department
		with self.assertRaises(frappe.ValidationError):
			self.change(self.super_admin, u, "department_admin", unit="BC no such unit")

	def test_r8_refused_roles_and_targets(self):
		u = self.fresh_user(team=self.tc2)
		with self.assertRaisesRegex(frappe.ValidationError, "Project Lead is set on each project"):
			self.change(self.super_admin, u, "project_lead")
		with self.assertRaises(frappe.ValidationError):
			self.change(self.super_admin, u, "bogus_role")
		disabled = self.fresh_user(team=self.tc2)
		frappe.db.set_value("User", disabled, "enabled", 0)
		for target in ("Administrator", "Guest", self.client, disabled, "nobody-bc@roles.test"):
			with self.assertRaises((frappe.ValidationError, frappe.PermissionError), msg=target):
				self.change(self.super_admin, target, "project_architect")
		self.assertTrue(helper.is_super_admin("Administrator"))

	def test_r9_nobody_else_changes_roles(self):
		for caller in (self.coord, self.tm1, self.arch1, self.client, self.hradmin):
			with self.assertRaises(frappe.PermissionError, msg=caller):
				self.change(caller, self.arch2, "project_architect")
			frappe.set_user(caller)
			with self.assertRaises(frappe.PermissionError, msg=caller):
				portal_admin.remove_user_designation(self.tm1, "team_manager", unit=self.tc1)
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.tc1, "portal_team_lead"), self.tm1)

	def test_r10_methods_and_read_only_get(self):
		self.assertEqual(_methods(portal_admin.change_user_role), ["POST"])
		self.assertEqual(_methods(portal_admin.remove_user_designation), ["POST"])
		self.assertIn("GET", _methods(portal_admin.get_user_designations))
		self.assertIn("GET", _methods(portal_admin.search_role_changeable_users))
		todo, has_role = frappe.db.count("ToDo"), frappe.db.count("Has Role")
		frappe.set_user(self.super_admin)
		res = portal_admin.get_user_designations(self.arch1)
		self.assertIn("designations", res)
		self.assertIn("assignable", res)
		frappe.set_user(self.dadmin)
		res = portal_admin.get_user_designations(self.arch1)
		self.assertTrue(set(res["assignable"]) <= {"department_coordinator", "team_lead", "team_manager", "team_member", "project_architect"})
		self.assertNotIn("department_admin", res["assignable"])
		self.assertNotIn("super_admin", res["assignable"])
		portal_admin.search_role_changeable_users("bc")
		self.assertEqual((frappe.db.count("ToDo"), frappe.db.count("Has Role")), (todo, has_role))

	def test_get_user_designations_gate(self):
		frappe.set_user(self.dadmin)
		with self.assertRaises(frappe.PermissionError):
			portal_admin.get_user_designations(self.tarch)
		frappe.set_user(self.arch1)
		self.assertIn("designations", portal_admin.get_user_designations(self.arch1))  # own
		with self.assertRaises(frappe.PermissionError):
			portal_admin.get_user_designations(self.arch2)

	def test_search_role_changeable_users(self):
		frappe.set_user(self.dadmin)
		found = {r["name"] for r in portal_admin.search_role_changeable_users("bc")}
		self.assertIn(self.arch1, found)
		self.assertNotIn(self.tarch, found)
		self.assertNotIn(self.super_admin, found)
		self.assertNotIn(self.client, found)
		frappe.set_user(self.tm1)
		with self.assertRaises(frappe.PermissionError):
			portal_admin.search_role_changeable_users("bc")

	def test_remove_user_designation(self):
		u = self.fresh_user(team=self.tc2)
		self.addCleanup(frappe.db.set_value, DEPT_DT, self.tc2, "portal_team_lead", None)
		self.change(self.super_admin, u, "team_manager", unit=self.tc2)
		frappe.set_user(self.dadmin)
		portal_admin.remove_user_designation(u, "team_manager", unit=self.tc2)
		self.assertFalse(frappe.db.get_value(DEPT_DT, self.tc2, "portal_team_lead"))
		self.assertTrue(_in_team(self.tc2, u))

	def test_role_change_never_touches_project_participation(self):
		u = self.fresh_user(team=self.tc1)
		p = self.fresh_project(users=[u], lead=u, team=self.tc1)
		before = (helper.own_project_names(u), _project_users(p), frappe.db.get_value("Project", p, "portal_project_manager"))
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dc, "portal_department_coordinators", u)))
		self.change(self.dadmin, u, "department_coordinator", unit=self.dc)
		self.change(self.dadmin, u, "project_architect")
		after = (helper.own_project_names(u), _project_users(p), frappe.db.get_value("Project", p, "portal_project_manager"))
		self.assertEqual(before, after)

	def test_create_portal_user_as_coordinator(self):
		email = "bccreated-coord@roles.test"
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=1, ignore_permissions=True)
		frappe.set_user(self.super_admin)
		self.addCleanup(lambda: (frappe.set_user("Administrator"), _remove_rows(self.dc, "portal_department_coordinators", email)))
		portal_admin.create_portal_user(
			email=email, full_name="BC Coord", password="Prt-" + "8d2c6e1f4a7b" + "#Bb2",
			role="department_coordinator", teams_json=json.dumps([self.dc]),
		)
		self.assertIn(email, _rows(self.dc, "portal_department_coordinators"))
		self.assertEqual(helper.get_portal_role(email), "department_coordinator")

	def test_admin_capability_flag(self):
		for user, expected in ((self.super_admin, True), (self.dadmin, True), (self.coord, False), (self.tm1, False)):
			frappe.set_user(user)
			self.assertIs(bool(portal_admin.get_portal_admin_capabilities()["can_change_roles"]), expected, user)


# =====================================================================================
# R3 project links (L1-L14)
# =====================================================================================
class TestProjectLinks(BatchCBase):
	def save_link(self, caller, project, link_type="T Server", **kw):
		frappe.set_user(caller)
		if "allowed_users" in kw and isinstance(kw["allowed_users"], list):
			kw["allowed_users"] = json.dumps(kw["allowed_users"])
		return _links().save_project_link(project, link_type, **kw)

	def seed(self):
		"""L5: the Super Admin sets the T Server link of p1 for arch1."""
		return self.save_link(
			self.super_admin, self.p1, "T Server", copy_path=SECRET_PATH, open_url=SECRET_URL, allowed_users=[self.arch1]
		)

	def new_link(self, project, link_type="T Server", **fields):
		doc = frappe.get_doc({"doctype": LINK_DT, "project": project, "link_type": link_type, **fields})
		return doc.insert(ignore_permissions=True)

	def test_l1_doctype_is_system_manager_only(self):
		self.seed()
		self.assertFalse(frappe.has_permission(LINK_DT, "read", user=self.arch1))
		self.assertFalse(frappe.has_permission(LINK_DT, "read", user=self.dadmin))
		self.assertFalse(frappe.has_permission(LINK_DT, "read", user=self.coord))
		self.assertTrue(frappe.has_permission(LINK_DT, "read", user=self.super_admin))
		for user in (self.arch1, self.coord):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				frappe.get_list(LINK_DT, fields=["name", "open_url"])

	def test_l2_controller_validation(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		self.new_link(p, "Autodesk Server", open_url="  https://x.example/a  ")
		self.assertEqual(frappe.db.get_value(LINK_DT, {"project": p, "link_type": "Autodesk Server"}, "open_url"), "https://x.example/a")
		with self.assertRaises(frappe.ValidationError):
			self.new_link(p, "Autodesk Server", open_url="https://y.example")  # duplicate (project, type)
		for bad in ("javascript:alert(1)", "data:text/html,x", "JAVASCRIPT:alert(1)", "https://a b", "ftp://x", "https://x\n"):
			with self.assertRaises(frappe.ValidationError, msg=bad):
				self.new_link(p, "ERP", open_url=bad)
		self.new_link(p, "ERP", open_url="HTTP://Upper.example/x")  # case-insensitive scheme
		with self.assertRaises(frappe.ValidationError):
			self.new_link(p, "T Server", copy_path="T:\\x\x07y")  # control characters
		with self.assertRaises(frappe.ValidationError):
			self.new_link(p, "T Server", copy_path="T:\\" + "x" * 1001)
		with self.assertRaises(frappe.ValidationError):
			self.new_link(p, "T Server", open_url="https://x.example/" + "a" * 2000)

	def test_allowed_users_are_deduped_and_vetted(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		doc = self.new_link(p, "T Server", copy_path="T:\\x", allowed_users=[{"user": self.arch1}, {"user": self.arch1}])
		self.assertEqual([r.user for r in doc.allowed_users], [self.arch1])
		for bad in ("Administrator", "Guest"):
			with self.assertRaises(frappe.ValidationError, msg=bad):
				self.new_link(p, "ERP", copy_path="x", allowed_users=[{"user": bad}])
		disabled = self.fresh_user()
		frappe.db.set_value("User", disabled, "enabled", 0)
		with self.assertRaises(frappe.ValidationError):
			self.new_link(p, "ERP", copy_path="x", allowed_users=[{"user": disabled}])

	def test_l3_client_never_allowed(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Client contacts cannot be given access"):
			self.new_link(self.pa, "ERP", open_url="https://erp.example", allowed_users=[{"user": self.client}])
		with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
			self.save_link(self.super_admin, self.pa, "ERP", open_url="https://erp.example", allowed_users=[self.client])

	def test_l4_allowed_user_must_see_the_project(self):
		with self.assertRaisesRegex(frappe.ValidationError, "cannot see this project"):
			self.save_link(self.super_admin, self.p1, "ERP", open_url="https://erp.example", allowed_users=[self.sup])
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(LINK_DT, {"project": self.p1, "link_type": "ERP"}))

	def test_l5_save_and_upsert(self):
		self.seed()
		rows = frappe.get_all(LINK_DT, filters={"project": self.p1, "link_type": "T Server"}, fields=["name", "copy_path", "open_url"])
		self.assertEqual(len(rows), 1)
		self.assertEqual((rows[0].copy_path, rows[0].open_url), (SECRET_PATH, SECRET_URL))
		self.assertEqual({r.user for r in frappe.get_doc(LINK_DT, rows[0].name).allowed_users}, {self.arch1})
		# None leaves a field unchanged; a second save never makes a second row
		res = self.save_link(self.super_admin, self.p1, "T Server", copy_path=None, open_url=None)
		self.assertEqual(frappe.db.count(LINK_DT, {"project": self.p1, "link_type": "T Server"}), 1)
		self.assertEqual(frappe.db.get_value(LINK_DT, rows[0].name, "open_url"), SECRET_URL)
		self.assertEqual(len(_entries(res)), 3)
		with self.assertRaises(frappe.ValidationError):
			self.save_link(self.super_admin, self.p1, "Dropbox", open_url="https://x.example")
		self.assertEqual(_methods(_links().save_project_link), ["POST"])

	def test_l6_allowed_user_gets_the_values(self):
		self.seed()
		frappe.set_user(self.arch1)
		row = next(p for p in projects.list_projects()["projects"] if p["name"] == self.p1)
		entries = row["portal_links"]
		self.assertEqual([e["link_type"] for e in entries], list(LINK_TYPES))
		t = _by_type(entries)["T Server"]
		self.assertEqual((t["can_open"], t["has_path"], t["has_url"]), (1, 1, 1))
		self.assertEqual((t["copy_path"], t["open_url"]), (SECRET_PATH, SECRET_URL))
		self.assertEqual(_by_type(entries)["ERP"]["has_url"], 0)
		for resp in (projects.get_project(self.p1), projects.project_dashboard(self.p1)):
			t = _by_type(_portal_links_of(resp))["T Server"]
			self.assertEqual((t["can_open"], t["copy_path"], t["open_url"]), (1, SECRET_PATH, SECRET_URL))
		t = _by_type(_entries(_links().get_project_links(self.p1)))["T Server"]
		self.assertEqual((t["can_open"], t["copy_path"], t["open_url"]), (1, SECRET_PATH, SECRET_URL))
		self.assertNotIn("allowed_users", t)  # only managers see the list

	def test_l7_no_leak_to_a_user_who_may_not_open(self):
		self.seed()
		frappe.set_user(self.tm1)
		self.assertIn(self.p1, helper.get_allowed_project_names(self.tm1))
		responses = {
			"list_projects": projects.list_projects(),
			"kanban_board": projects.kanban_board(),
			"get_project": projects.get_project(self.p1),
			"project_dashboard": projects.project_dashboard(self.p1),
			"get_project_links": _links().get_project_links(self.p1),
			"global_search": search.global_search("BC"),
			"gantt": gantt.get_gantt_data(),
			"get_capabilities": projects.get_capabilities(),
			"links_for_projects": _links().links_for_projects([self.p1], user=self.tm1),
		}
		for name, resp in responses.items():
			text = _dump(resp)
			self.assertNotIn("BC-SECRET-PATH", text, name)
			self.assertNotIn("BC-SECRET-URL", text, name)
		t = _by_type(_entries(responses["get_project_links"]))["T Server"]
		self.assertEqual((t["has_path"], t["has_url"], t["can_open"]), (1, 1, 0))
		self.assertNotIn("copy_path", t)
		self.assertNotIn("open_url", t)
		row = next(p for p in responses["list_projects"]["projects"] if p["name"] == self.p1)
		self.assertEqual(_by_type(row["portal_links"])["T Server"]["can_open"], 0)

	def test_l8_clients_get_nothing(self):
		self.save_link(self.super_admin, self.pa, "ERP", open_url=SECRET_URL, allowed_users=[self.m1])
		frappe.set_user(self.client)
		listed = projects.list_projects()["projects"]
		self.assertTrue(listed)
		for p in listed:
			self.assertNotIn("portal_links", p)
		self.assertNotIn("BC-SECRET", _dump(listed))
		self.assertNotIn("BC-SECRET", _dump(projects.get_project(self.pa)))
		self.assertIsNone(_portal_links_of(projects.get_project(self.pa)))
		self.assertEqual(_links().links_for_projects([self.pa], user=self.client), {})
		with self.assertRaises(frappe.PermissionError):
			_links().get_project_links(self.pa)

	def test_l9_who_manages_links(self):
		self.seed()
		# Coordinator of p1's department
		self.save_link(self.coord, self.p1, "Autodesk Server", open_url="https://autodesk.example/a")
		res = _links().get_project_links(self.p1)
		t = _by_type(_entries(res))["T Server"]
		self.assertEqual([u["user"] for u in t["allowed_users"]], [self.arch1])
		self.assertEqual((t["copy_path"], t["open_url"]), (SECRET_PATH, SECRET_URL))
		self.assertTrue(res.get("can_manage") if isinstance(res, dict) else t.get("can_manage"))
		self.assertTrue(helper.can_manage_project_links(self.p1, self.coord))
		self.assertFalse(helper.can_manage_project_links(self.p1, self.tm1))
		self.assertFalse(helper.can_manage_project_links(self.p4, self.coord))
		with self.assertRaises(frappe.PermissionError):
			self.save_link(self.coord, self.p3, "ERP", open_url="https://erp.example")
		# Department Admin of p1's department
		self.save_link(self.dadmin, self.p1, "ERP", open_url="https://erp.example/p1")
		# not a Team Manager, not a Project Lead, not an architect
		for user in (self.tm1, self.arch1, self.hradmin):
			with self.assertRaises(frappe.PermissionError, msg=user):
				self.save_link(user, self.p1, "ERP", open_url="https://erp.example/x")
		# a project with no team: Super Admin only
		with self.assertRaises(frappe.PermissionError):
			self.save_link(self.coord, self.p4, "ERP", open_url="https://erp.example/p4")
		self.save_link(self.super_admin, self.p4, "ERP", open_url="https://erp.example/p4")
		# the legacy team-level admin row on the team itself also manages
		legacy_p = self.fresh_project(team=self.d1)
		self.save_link(self.admin, legacy_p, "ERP", open_url="https://erp.example/legacy")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(LINK_DT, {"project": self.p1, "link_type": "ERP"}, "open_url"), "https://erp.example/p1")

	def test_l10_allowed_users_rechecked_at_read(self):
		p = self.fresh_project(users=[self.arch1, self.arch2], team=self.tc1)
		self.save_link(self.super_admin, p, "T Server", copy_path=SECRET_PATH, allowed_users=[self.arch2])
		frappe.set_user(self.arch2)
		self.assertEqual(_by_type(_entries(_links().get_project_links(p)))["T Server"]["copy_path"], SECRET_PATH)
		frappe.set_user("Administrator")
		frappe.db.delete("Project User", {"parent": p, "user": self.arch2})
		self.assertNotIn(p, helper.get_allowed_project_names(self.arch2))
		frappe.set_user(self.arch2)
		self.assertNotIn("BC-SECRET", _dump(_links().links_for_projects([p], user=self.arch2)))
		with self.assertRaises(frappe.PermissionError):
			_links().get_project_links(p)

	def test_l11_update_project_ignores_legacy_fields(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		frappe.set_user(self.super_admin)
		projects.update_project(p, portal_server_t="https://leak.example", portal_server_a="x", portal_server_c="y")
		for f in ("portal_server_t", "portal_server_a", "portal_server_c"):
			self.assertFalse(frappe.db.get_value("Project", p, f), f)

	def test_legacy_fields_are_stripped_everywhere(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		frappe.db.set_value("Project", p, "portal_server_t", "https://bc-legacy-leak.example", update_modified=False)
		frappe.set_user(self.super_admin)
		row = next(x for x in projects.list_projects()["projects"] if x["name"] == p)
		for resp in (row, projects.get_project(p), projects.project_dashboard(p), projects.kanban_board()):
			text = _dump(resp)
			self.assertNotIn("portal_server_t", text)
			self.assertNotIn("bc-legacy-leak", text)

	def test_l12_migration_patch(self):
		patch = _patch("migrate_project_server_links")
		p = self.fresh_project(users=[self.arch1], lead=self.arch1, team=self.tc1)
		q = self.fresh_project(users=[self.arch2], team=self.tc2)
		frappe.db.set_value(
			"Project", p,
			{"portal_server_t": "T:\\My Drive\\X", "portal_server_a": "https://autodesk.example/x", "portal_server_c": "client box"},
			update_modified=False,
		)
		existing = self.new_link(q, "T Server", open_url="https://keep.example/q")
		frappe.db.set_value("Project", q, {"portal_server_t": "https://other.example/q", "portal_server_a": "https://bad url/x"}, update_modified=False)
		started = time.time()

		count = frappe.db.count(LINK_DT)
		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			patch.run(dry_run=1)
		self.assertEqual(frappe.db.count(LINK_DT), count)
		self.assertEqual(frappe.db.get_value("Project", p, "portal_server_t"), "T:\\My Drive\\X")
		self.assertIn(p, out.getvalue())

		patch.run(dry_run=0)
		links = {r.link_type: r for r in frappe.get_all(LINK_DT, filters={"project": p}, fields=["name", "link_type", "copy_path", "open_url"])}
		self.assertEqual(set(links), set(LINK_TYPES))
		self.assertEqual((links["T Server"].copy_path, links["T Server"].open_url or ""), ("T:\\My Drive\\X", ""))
		self.assertEqual((links["Autodesk Server"].open_url, links["Autodesk Server"].copy_path or ""), ("https://autodesk.example/x", ""))
		self.assertEqual((links["ERP"].copy_path, links["ERP"].open_url or ""), ("client box", ""))
		for r in links.values():
			self.assertEqual({u.user for u in frappe.get_doc(LINK_DT, r.name).allowed_users}, {self.arch1})
		for f in ("portal_server_t", "portal_server_a", "portal_server_c"):
			self.assertFalse(frappe.db.get_value("Project", p, f), f)
		# an existing link is never overwritten; a URL with whitespace stays a path
		self.assertEqual(frappe.db.get_value(LINK_DT, existing.name, "open_url"), "https://keep.example/q")
		self.assertEqual(frappe.db.get_value(LINK_DT, {"project": q, "link_type": "Autodesk Server"}, "copy_path"), "https://bad url/x")
		# a backup of the original values was written first
		backups = [
			f for f in glob.glob(frappe.get_site_path("private", "backups", "portal_server_links_*.json"))
			if os.path.getmtime(f) >= started - 1
		]
		self.assertTrue(backups)
		with open(max(backups, key=os.path.getmtime)) as fh:
			data = json.load(fh)
		self.assertEqual(data[p]["portal_server_c"], "client box")
		# rerun is a no-op
		before = sorted(frappe.get_all(LINK_DT, filters={"project": ["in", [p, q]]}, fields=["name", "modified"]), key=lambda r: r.name)
		patch.execute()
		after = sorted(frappe.get_all(LINK_DT, filters={"project": ["in", [p, q]]}, fields=["name", "modified"]), key=lambda r: r.name)
		self.assertEqual(before, after)

	def test_project_with_links_can_be_deleted(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		self.save_link(self.super_admin, p, "T Server", copy_path=SECRET_PATH, allowed_users=[self.arch1])
		self.save_link(self.super_admin, p, "ERP", open_url=SECRET_URL)
		link_names = frappe.get_all(LINK_DT, filters={"project": p}, pluck="name")
		self.assertEqual(len(link_names), 2)
		frappe.set_user(self.super_admin)
		projects.delete_project(p)
		self.assertFalse(frappe.db.exists("Project", p))
		self.assertFalse(frappe.get_all(LINK_DT, filters={"project": p}))
		self.assertFalse(frappe.get_all(LINK_USER_DT, filters={"parent": ["in", link_names]}))

	def test_project_and_type_are_unique_in_the_database(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		self.new_link(p, "ERP", open_url="https://erp.example/a")
		frappe.db.savepoint("bc_unique")
		with self.assertRaises(frappe.UniqueValidationError):
			# what a concurrent insert sees: the controller check bypassed
			doc = frappe.get_doc({"doctype": LINK_DT, "project": p, "link_type": "ERP", "open_url": "https://erp.example/b"})
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)
		frappe.db.rollback(save_point="bc_unique")

	def test_migration_dry_run_reports_values_that_would_fail(self):
		patch = _patch("migrate_project_server_links")
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		frappe.db.set_value(
			"Project", p, {"portal_server_t": "T:\\x\x07y", "portal_server_c": "https://ok.example/c"}, update_modified=False
		)
		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			patch.run(dry_run=1)
		text = out.getvalue()
		self.assertIn(f"! WOULD FAIL {p} portal_server_t", text)
		self.assertNotIn(f"! WOULD FAIL {p} portal_server_c", text)
		out = io.StringIO()
		with contextlib.redirect_stdout(out):
			patch.run(dry_run=0)
		text = out.getvalue()
		self.assertRegex(text, r"[1-9]\d* failed")
		self.assertIn(p, text)
		# rolled back: the value is still on the project, no link was made
		self.assertTrue(frappe.db.get_value("Project", p, "portal_server_t"))
		self.assertFalse(frappe.get_all(LINK_DT, filters={"project": p}))

	def test_l13_blank_save_deletes_the_row(self):
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		self.save_link(self.super_admin, p, "ERP", open_url="https://erp.example", allowed_users=[self.arch1])
		self.assertTrue(frappe.db.exists(LINK_DT, {"project": p, "link_type": "ERP"}))
		self.save_link(self.super_admin, p, "ERP", copy_path="", open_url="", allowed_users=[])
		self.assertFalse(frappe.db.exists(LINK_DT, {"project": p, "link_type": "ERP"}))

	def test_l14_get_is_read_only(self):
		self.assertIn("GET", _methods(_links().get_project_links))
		p = self.fresh_project(users=[self.arch1], team=self.tc1)
		counts = (frappe.db.count(LINK_DT), frappe.db.count("ToDo"), frappe.db.count(LINK_USER_DT))
		for user in (self.super_admin, self.coord, self.arch1):
			frappe.set_user(user)
			res = _links().get_project_links(p)
			self.assertEqual([e["link_type"] for e in _entries(res)], list(LINK_TYPES))
			self.assertTrue(all(e["has_path"] == 0 and e["has_url"] == 0 for e in _entries(res)))
		self.assertEqual((frappe.db.count(LINK_DT), frappe.db.count("ToDo"), frappe.db.count(LINK_USER_DT)), counts)

	def test_project_endpoints_report_can_manage_links(self):
		self.seed()
		frappe.set_user(self.coord)
		self.assertTrue(_can_manage(projects.get_project(self.p1)))
		frappe.set_user(self.arch1)
		self.assertFalse(_can_manage(projects.get_project(self.p1)))
		self.assertFalse(_can_manage(projects.project_dashboard(self.p1)))

	def test_links_for_projects_has_no_n_plus_one(self):
		self.seed()
		names = [self.p1, self.p2, self.p3, self.p4, self.p5]
		frappe.set_user(self.super_admin)
		with mock.patch.object(frappe.db, "sql", wraps=frappe.db.sql) as spy:
			out = _links().links_for_projects(names, user=self.super_admin)
		self.assertEqual(set(out), set(names))
		few = spy.call_count
		more = names + [self.fresh_project(team=self.tc1) for _ in range(5)]
		frappe.set_user(self.super_admin)
		with mock.patch.object(frappe.db, "sql", wraps=frappe.db.sql) as spy:
			_links().links_for_projects(more, user=self.super_admin)
		self.assertLessEqual(spy.call_count, few + 2)


def _can_manage(resp):
	if "can_manage_links" in resp:
		return bool(resp["can_manage_links"])
	return bool((resp.get("project") or {}).get("can_manage_links"))


# =====================================================================================
# One-shot script (S1-S3)
# =====================================================================================
class TestRoleScript(BatchCBase):
	"""The script runs against a fixture plan of the same shape as its constants:

	plan = {
	    "departments":          [{"label": str, "pending": 0|1}],          # ensured, is_group 1, portal_unit Department
	    "existing_departments": [label, ...],                              # must exist; only portal_unit set
	    "new_teams":            [{"label": str, "department": label}],     # created under the department, portal_unit Team
	    "team_parents":         {team_name: department_label},             # reparent (exact name, then fuzzy)
	    "super_admins":         [user, ...],                               # ensure System Manager + Projects User
	    "keep_super_admins":    [user, ...],                               # verify only, never removed
	    "designations":         [{"user", "role": "admin"|"coordinator", "department": label}],
	    "team_managers":        [{"user", "team": team_name}],             # conflict -> ! SKIP
	    "members":              [{"user", "team": team_name}],             # report only
	    "protected":            [user, ...],                               # added to PROTECTED, never written
	}
	Department labels resolve to `<label> - <company abbr>`.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		_purge_departments("BCS ")
		abbr = _abbr()
		cls.hr = _unit("BCS HR", "")  # existing leaf, blank unit
		cls.team_a = _unit("BCS Team A", "Team", office="RIYADH")
		cls.team_b = _unit("BCS Team B", "Team", office="RIYADH")
		cls.s_coordadmin = _user("bcscoordadmin")
		cls.s_hra = _user("bcshra")
		cls.s_pendadmin = _user("bcspendadmin")
		cls.s_mgr = _user("bcsmgr")
		cls.s_other = _user("bcsother")
		cls.s_newsa = _user("bcsnewsa")
		cls.s_keepsa = _user("bcskeepsa", ("System Manager", "Projects User"))
		cls.s_member = _user("bcsmember")
		cls.s_prot = _user("bcsprot")
		teams._assign_users_to_team(cls.team_a, [cls.s_member])
		teams._assign_users_to_team(cls.team_b, [cls.s_other])
		_add_rows(cls.team_b, lead=cls.s_other)  # conflict for the plan below
		cls.sp = _project("BC S project", [cls.s_member, cls.s_mgr], lead=cls.s_member, team=cls.team_a)
		cls.concept = "BCS Concept - " + abbr
		cls.pending = "BCS Pending - " + abbr
		cls.coord_team = "BCS COORD TEAM - " + abbr
		cls.plan = {
			"departments": [{"label": "BCS Concept", "pending": 0}, {"label": "BCS Pending", "pending": 1}],
			"existing_departments": ["BCS HR", "BCS Missing Existing"],
			"new_teams": [{"label": "BCS COORD TEAM", "department": "BCS Pending"}],
			"team_parents": {
				cls.team_a: "BCS Concept",
				"bcs  team b - " + abbr.lower(): "BCS Concept",  # fuzzy: case + doubled space
				"BCS Missing Team - " + abbr: "BCS Concept",
			},
			"super_admins": [cls.s_newsa],
			"keep_super_admins": [cls.s_keepsa],
			"designations": [
				{"user": cls.s_coordadmin, "role": "coordinator", "department": "BCS Concept"},
				{"user": cls.s_coordadmin, "role": "admin", "department": "BCS Concept"},
				{"user": cls.s_hra, "role": "admin", "department": "BCS HR"},
				{"user": cls.s_pendadmin, "role": "admin", "department": "BCS Pending"},
				{"user": "bcs-missing@roles.test", "role": "admin", "department": "BCS Concept"},
			],
			"team_managers": [
				{"user": cls.s_mgr, "team": cls.team_a},
				{"user": cls.s_mgr, "team": cls.team_b},  # already led by s_other -> skip
				{"user": cls.s_pendadmin, "team": cls.coord_team},
			],
			"members": [{"user": cls.s_member.upper(), "team": cls.team_a}, {"user": "bcs-gone@roles.test", "team": cls.team_a}],
			"protected": [cls.s_prot],
		}

	def counts(self):
		out = {
			"Department": frappe.db.count(DEPT_DT),
			"Portal Department Admin": frappe.db.count("Portal Department Admin"),
			"Has Role": frappe.db.count("Has Role"),
			"ToDo": frappe.db.count("ToDo"),
			"Project User": frappe.db.count("Project User"),
		}
		if frappe.db.table_exists(COORD_DT):
			out[COORD_DT] = frappe.db.count(COORD_DT)
		return out

	def run_script(self, plan, dry_run):
		frappe.set_user("Administrator")
		buf = io.StringIO()
		with contextlib.redirect_stdout(buf):
			_script().execute(dry_run=dry_run, plan=plan)
		return buf.getvalue()

	def snapshot(self):
		users = [self.s_coordadmin, self.s_hra, self.s_pendadmin, self.s_mgr, self.s_other, self.s_newsa, self.s_keepsa, self.s_member, self.s_prot]
		depts = frappe.get_all(DEPT_DT, filters={"department_name": ["like", "BCS %"]}, fields=["name", "modified", "parent_department", "lft", "rgt"], order_by="name")
		roles = {u: sorted(frappe.get_roles(u)) for u in users}
		pu = sorted(frappe.get_all("Project User", filters={"user": ["in", users]}, fields=["parent", "user"], order_by="parent, user"), key=lambda r: (r.parent, r.user))
		return depts, roles, pu

	def test_protected_constant(self):
		self.assertTrue({"khaled@ata.com.sa", "uat.pm@ata-test.local"} <= set(_script().PROTECTED))

	def test_s1_dry_run_writes_nothing(self):
		before = self.counts()
		out = self.run_script(self.plan, dry_run=1)
		self.assertEqual(self.counts(), before)
		self.assertFalse(frappe.db.exists(DEPT_DT, self.concept))
		self.assertRegex(out, r"(?m)^\s*\+")  # it prints the plan

	def test_s2_apply_and_rerun(self):
		project_users_before = _project_users(self.sp)
		out = self.run_script(self.plan, dry_run=0)
		# A. departments
		c = frappe.db.get_value(DEPT_DT, self.concept, ["portal_unit", "is_group", "portal_pending", "parent_department"], as_dict=True)
		self.assertEqual((c.portal_unit, c.is_group, c.portal_pending, c.parent_department), ("Department", 1, 0, "All Departments"))
		pnd = frappe.db.get_value(DEPT_DT, self.pending, ["portal_unit", "is_group", "portal_pending"], as_dict=True)
		self.assertEqual((pnd.portal_unit, pnd.is_group, pnd.portal_pending), ("Department", 1, 1))
		hr = frappe.db.get_value(DEPT_DT, self.hr, ["portal_unit", "is_group", "parent_department"], as_dict=True)
		self.assertEqual((hr.portal_unit, hr.is_group, hr.parent_department), ("Department", 0, "All Departments"))
		ct = frappe.db.get_value(DEPT_DT, self.coord_team, ["portal_unit", "parent_department"], as_dict=True)
		self.assertEqual((ct.portal_unit, ct.parent_department), ("Team", self.pending))
		# B. reparent (exact + fuzzy)
		for team in (self.team_a, self.team_b):
			row = frappe.db.get_value(DEPT_DT, team, ["parent_department", "portal_unit", "portal_office"], as_dict=True)
			self.assertEqual((row.parent_department, row.portal_unit, row.portal_office), (self.concept, "Team", "RIYADH"))
		# C. super admins
		self.assertTrue({"System Manager", "Projects User"} <= set(frappe.get_roles(self.s_newsa)))
		self.assertIn("System Manager", frappe.get_roles(self.s_keepsa))
		# D. designations + markers (none for pending)
		self.assertIn(self.s_coordadmin, _rows(self.concept, "portal_department_admins"))
		self.assertIn(self.s_coordadmin, _rows(self.concept, "portal_department_coordinators"))
		self.assertTrue({helper.DEPT_ADMIN_ROLE, DEPT_COORDINATOR} <= set(frappe.get_roles(self.s_coordadmin)))
		self.assertTrue(_in_team(self.concept, self.s_coordadmin))
		self.assertIn(self.s_hra, _rows(self.hr, "portal_department_admins"))
		self.assertIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.s_hra))
		self.assertIn(self.s_pendadmin, _rows(self.pending, "portal_department_admins"))
		self.assertNotIn(helper.DEPT_ADMIN_ROLE, frappe.get_roles(self.s_pendadmin))
		self.assertNotIn(TEAM_MANAGER, frappe.get_roles(self.s_pendadmin))
		# E. team managers; a conflict is skipped, never overwritten
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.team_a, "portal_team_lead"), self.s_mgr)
		self.assertTrue(_in_team(self.team_a, self.s_mgr))
		self.assertIn(TEAM_MANAGER, frappe.get_roles(self.s_mgr))
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.team_b, "portal_team_lead"), self.s_other)
		self.assertEqual(frappe.db.get_value(DEPT_DT, self.coord_team, "portal_team_lead"), self.s_pendadmin)
		self.assertRegex(out, r"(?mi)^\s*!.*skip.*conflict")
		self.assertRegex(out, r"(?m)^\s*!.*bcs-missing@roles\.test")
		self.assertRegex(out, r"(?m)^\s*!.*BCS Missing Team")
		# F. members: report only (case-insensitive lookup)
		self.assertIn(self.s_member, out.lower())
		# never touches projects
		self.assertEqual(_project_users(self.sp), project_users_before)

		snap = self.snapshot()
		counts = self.counts()
		out2 = self.run_script(self.plan, dry_run=0)
		self.assertNotRegex(out2, r"(?m)^\s*[+~]")
		self.assertRegex(out2, r"(?m)^\s*=")
		self.assertEqual(self.snapshot(), snap)
		self.assertEqual(self.counts(), counts)

	def test_s3_protected_and_missing(self):
		frappe.set_user("Administrator")
		prot_roles = sorted(frappe.get_roles(self.s_prot))
		plan = {
			"departments": [{"label": "BCS Concept", "pending": 0}],
			"designations": [{"user": self.s_prot, "role": "admin", "department": "BCS Concept"}],
			"team_managers": [{"user": self.s_prot, "team": self.team_a}],
			"super_admins": [self.s_prot],
			"protected": [self.s_prot],
		}
		try:
			self.run_script(plan, dry_run=0)
		except Exception:  # refusing outright is acceptable too
			frappe.db.rollback()
		self.assertNotIn(self.s_prot, _rows(self.concept, "portal_department_admins") if frappe.db.exists(DEPT_DT, self.concept) else set())
		self.assertNotEqual(frappe.db.get_value(DEPT_DT, self.team_a, "portal_team_lead"), self.s_prot)
		self.assertEqual(sorted(frappe.get_roles(self.s_prot)), prot_roles)
		# missing users / teams are skipped, not fatal
		out = self.run_script(
			{
				"team_parents": {"BCS Nowhere - X": "BCS Concept"},
				"team_managers": [{"user": "bcs-nobody@roles.test", "team": self.team_a}],
				"designations": [{"user": "bcs-nobody@roles.test", "role": "admin", "department": "BCS HR"}],
			},
			dry_run=0,
		)
		self.assertRegex(out, r"(?m)^\s*!")
		self.assertFalse(frappe.db.exists("User", "bcs-nobody@roles.test"))

	def test_logo_report_and_clear(self):
		frappe.set_user("Administrator")
		settings = "Portal Project Settings"
		if not frappe.get_meta(settings).has_field("company_logo"):
			self.skipTest("no company_logo field")
		old = frappe.db.get_single_value(settings, "company_logo")
		frappe.db.set_single_value(settings, "company_logo", "/files/bc-old-logo.png")
		self.addCleanup(frappe.db.set_single_value, settings, "company_logo", old)
		out = self.run_script({}, dry_run=0)
		self.assertIn("bc-old-logo.png", out)
		self.assertEqual(frappe.db.get_single_value(settings, "company_logo"), "/files/bc-old-logo.png")
		buf = io.StringIO()
		with contextlib.redirect_stdout(buf):
			_script().execute(dry_run=0, clear_old_logo=1, plan={})
		self.assertFalse(frappe.db.get_single_value(settings, "company_logo"))


# =====================================================================================
# Frontend / logo static checks (F1-F3)
# =====================================================================================
class TestFrontendContractC(FrappeTestCase):
	def _read(self, rel, base=FRONTEND_SRC):
		path = os.path.join(base, rel)
		self.assertTrue(os.path.exists(path), path)
		with open(path, encoding="utf-8") as fh:
			return fh.read()

	@staticmethod
	def _strip_comments(text):
		text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
		text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
		return re.sub(r"(?m)(^|[^:])//.*$", r"\1", text)

	def test_f1_no_old_labels(self):
		bad = []
		for root, _dirs, names in os.walk(FRONTEND_SRC):
			for n in names:
				if not n.endswith((".vue", ".js")):
					continue
				with open(os.path.join(root, n), encoding="utf-8") as fh:
					text = self._strip_comments(fh.read())
				for phrase in ("Lead Architect", "Team Lead", "Team Member"):
					if re.search(r"\b" + phrase + r"\b", text):
						bad.append((os.path.relpath(os.path.join(root, n), FRONTEND_SRC), phrase))
		self.assertEqual(bad, [])

	def test_roles_config(self):
		js = self._read("config/roles.js")
		for token in ("ROLE_LABELS", "LINK_LABELS", "LOGOS", "Project Architect", "Team Manager", "Project Lead", "Department Coordinator"):
			self.assertIn(token, js)
		for f in ("ata-logo-horizontal.png", "ata-logo-horizontal-white.png", "ata-logo-stacked.png", "ata-logo-stacked-white.png"):
			self.assertIn("/assets/portal_app/images/" + f, js)

	def test_f2_pages(self):
		projects_vue = self._read("pages/Projects.vue")
		self.assertNotIn("portal_server_", projects_vue)
		self.assertIn("portal_links", projects_vue)
		detail = self._read("pages/ProjectDetail.vue")
		self.assertIn("portal_app.api.links.save_project_link", detail)
		self.assertIn("portal_app.api.links.get_project_links", detail)
		self.assertRegex(detail, r"save_project_link[\s\S]{0,400}type:\s*[\"']POST[\"']")
		self.assertIn("navigator.clipboard", detail)
		self.assertIn("noopener", detail)
		self.assertIn("aria-disabled", detail)
		chart = self._read("pages/OrgChartPage.vue")
		self.assertRegex(chart, r"change_user_role[\s\S]{0,400}type:\s*[\"']POST[\"']")
		self.assertIn("remove_user_designation", chart)
		self.assertIn("set_department_pending", chart)
		admin = self._read("pages/Admin.vue")
		self.assertIn("search_role_changeable_users", admin)
		self.assertIn("department_coordinator", admin)
		self.assertIn("designations", self._read("pages/Profile.vue"))

	def test_f3_logo_files_and_references(self):
		images = frappe.get_app_path("portal_app", "public", "images")
		for f in ("ata-logo-horizontal.png", "ata-logo-horizontal-white.png", "ata-logo-stacked.png", "ata-logo-stacked-white.png", "ata-logo-stacked-800.png"):
			path = os.path.join(images, f)
			self.assertTrue(os.path.exists(path), f)
			self.assertLessEqual(os.path.getsize(path), 300 * 1024, f)
			with open(path, "rb") as fh:
				self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n", f)
		for rel in ("pages/Login.vue", "component/Sidebar.vue", "pages/ClientTransmittals.vue"):
			self.assertIn("ata-logo-", self._read(rel), rel)
		self.assertIn("ata-logo-", self._read(frappe.get_app_path("portal_app", "www", "handbook.html"), base=""))
		from portal_app import hooks

		self.assertEqual(hooks.add_to_apps_screen[0]["logo"], "/assets/portal_app/images/ata-logo-stacked-800.png")
