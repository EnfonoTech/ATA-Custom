import re
import frappe
from frappe import _

from portal_app.api import helper


def _team_sort_key(dept):
	m = re.search(r"(\d+)", dept["department_name"])
	return int(m.group(1)) if m else 999


def _assigned_users_by_department(dept_names):
	"""Team membership = Frappe's standard "Assign To" (ToDo) on the Department doc, not Employee.department."""
	if not dept_names:
		return {}
	assignments = frappe.get_all(
		"ToDo",
		filters={
			"reference_type": "Department",
			"reference_name": ["in", dept_names],
			"status": ["not in", ("Cancelled", "Closed")],
		},
		fields=["reference_name", "allocated_to"],
	)
	user_names = {a.allocated_to for a in assignments}
	user_info = {}
	if user_names:
		rows = frappe.get_all(
			"User", filters={"name": ["in", list(user_names)]}, fields=["name", "full_name"]
		)
		user_info = {r.name: r.full_name for r in rows}

	by_dept = {}
	for a in assignments:
		by_dept.setdefault(a.reference_name, []).append(
			{
				"name": a.allocated_to,
				"employee_name": user_info.get(a.allocated_to) or a.allocated_to,
				"designation": None,
				"company_email": a.allocated_to,
			}
		)
	for members in by_dept.values():
		members.sort(key=lambda m: m["employee_name"])
	return by_dept


@frappe.whitelist()
def get_teams():
	# Returns every member's login email — staff-only. Non-staff portal users get an
	# empty list rather than an error so the shared Dashboard widget still renders.
	helper.assert_portal_user()
	if not helper.can_manage_teams():
		return []
	departments = frappe.get_all(
		"Department",
		filters={"parent_department": "All Departments", "portal_office": ["!=", ""]},
		fields=["name", "department_name", "portal_office"],
	)
	departments = sorted(departments, key=_team_sort_key)
	members_by_dept = _assigned_users_by_department([d.name for d in departments])

	result = []
	for dept in departments:
		members = members_by_dept.get(dept.name, [])

		project_count = 0
		active_project_count = 0
		if frappe.get_meta("Project").has_field("portal_team"):
			project_count = frappe.db.count("Project", {"portal_team": dept.name})
			active_project_count = frappe.db.count("Project", {"portal_team": dept.name, "status": "Open"})

		result.append(
			{
				"name": dept.name,
				"department_name": dept.department_name,
				"office": dept.portal_office or "",
				"member_count": len(members),
				"members": members,
				"project_count": project_count,
				"active_project_count": active_project_count,
			}
		)

	return result


@frappe.whitelist()
def get_team_summary():
	# Headcount is staff-only; the sidebar widget degrades to zeros for everyone else.
	helper.assert_portal_user()
	if not helper.can_manage_teams():
		return {"total": 0, "departments": []}
	total = frappe.db.count("Employee", {"status": "Active"})

	departments = frappe.get_all(
		"Department",
		filters={"parent_department": "All Departments", "portal_office": ["!=", ""]},
		fields=["name", "department_name", "portal_office"],
	)
	departments = sorted(departments, key=_team_sort_key)

	dept_counts = []
	for dept in departments:
		count = frappe.db.count("Employee", {"department": dept.name, "status": "Active"})
		if count > 0:
			dept_counts.append(
				{
					"name": dept.name,
					"label": dept.department_name,
					"office": dept.portal_office or "",
					"count": count,
				}
			)

	return {"total": total, "departments": dept_counts}


@frappe.whitelist()
def get_offices():
	# Office labels only (no PII) — every portal user needs them for filter dropdowns.
	helper.assert_portal_user()
	rows = frappe.get_all(
		"Department",
		filters={"portal_office": ["!=", ""]},
		fields=["portal_office"],
		distinct=True,
	)
	return sorted({r.portal_office for r in rows if r.portal_office})


@frappe.whitelist()
def update_team(team, department_name=None, office=None):
	"""Update editable team (Department) fields from the portal Teams edit modal."""
	helper.assert_manage_teams()
	doc = frappe.get_doc("Department", team)
	if department_name is not None and department_name.strip():
		doc.department_name = department_name.strip()
	if office is not None:
		doc.portal_office = office or None
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "department_name": doc.department_name, "office": doc.portal_office}


@frappe.whitelist()
def get_assignable_users(team=None):
	"""Enabled portal users not already assigned to `team`, plus available User Groups,
	for the Add Member picker — mirrors Frappe's "Assign To" / "Assign To User Group" pair."""
	helper.assert_manage_teams()
	assigned = set()
	if team:
		assigned = {
			r.allocated_to
			for r in frappe.get_all(
				"ToDo",
				filters={
					"reference_type": "Department",
					"reference_name": team,
					"status": ["not in", ("Cancelled", "Closed")],
				},
				fields=["allocated_to"],
			)
		}
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "name": ["not in", ["Guest", "Administrator"]]},
		fields=["name", "full_name"],
		order_by="full_name asc",
		limit_page_length=500,
	)
	return [u for u in users if u.name not in assigned]


@frappe.whitelist()
def get_user_groups():
	"""User Groups available for the "assign the whole group at once" picker, with member counts.

	Staff-only: the picker is a team-management control, and group names/sizes describe
	internal org structure. Non-staff portal users get an empty list so the ProjectDetail
	modal still renders. Callers that mutate assignments (add_team_member,
	sync_project_team, ...) enforce their own permission check on top of this.
	"""
	helper.assert_portal_user()
	if not helper.can_manage_teams():
		return []
	groups = frappe.get_all("User Group", fields=["name"], order_by="name asc")
	if not groups:
		return []
	counts = frappe.get_all(
		"User Group Member",
		filters={"parent": ["in", [g.name for g in groups]]},
		fields=["parent", "count(name) as count"],
		group_by="parent",
	)
	count_by_group = {c.parent: c.count for c in counts}
	return [{"name": g.name, "member_count": count_by_group.get(g.name, 0)} for g in groups]


@frappe.whitelist()
def get_user_group_members(user_group):
	"""Member user IDs of a User Group, for pickers that add a whole group at once."""
	# Returns login emails; only callers who may actually assign members should see them.
	helper.assert_manage_teams()
	return frappe.get_all("User Group Member", filters={"parent": user_group}, pluck="user")


@frappe.whitelist()
def add_team_member(team, user=None, user_group=None):
	"""Team membership = assigning the Department doc to Users via Frappe's standard Assign To.

	`user_group` resolves to its member users and assigns all of them at once — same
	behaviour as picking "Assign To User Group" in Frappe's native assign dialog."""
	helper.assert_manage_teams()
	if not frappe.db.exists("Department", team):
		frappe.throw(_("Team not found"))

	if user_group:
		users = frappe.get_all("User Group Member", filters={"parent": user_group}, pluck="user")
		if not users:
			frappe.throw(_("This User Group has no members"))
	else:
		if not user:
			frappe.throw(_("user or user_group is required"))
		if not frappe.db.exists("User", user):
			frappe.throw(_("User not found"))
		users = [user]

	import frappe.share as _share
	from frappe.desk.form.assign_to import add as assign_add

	# assign_add() auto-shares the doc with an assignee who lacks read access to it,
	# and that auto-share checks the CALLING user's own "share" DocPerm on Department
	# — ignore_permissions=True does not bypass this separate, lower-level RBAC check.
	# Pre-share it via frappe.share's own ignore_share_permission flag instead (same
	# fix already applied to _sync_project_assignment for the equivalent Project case).
	for u in users:
		_share.add_docshare("Department", team, user=u, read=1, flags={"ignore_share_permission": True})

	assign_add({"doctype": "Department", "name": team, "assign_to": users}, ignore_permissions=True)
	return {"team": team, "users": users}


@frappe.whitelist()
def remove_team_member(team, user):
	helper.assert_manage_teams()
	from frappe.desk.form.assign_to import remove as assign_remove

	assign_remove("Department", team, user, ignore_permissions=True)
	return {"team": team, "user": user}
