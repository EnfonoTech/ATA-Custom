import re

import frappe
from frappe import _
from frappe.utils import cstr

from portal_app.api import helper

# Team roles, highest first. A person's ROLE in the chart is the highest portal role they
# hold (a Super Admin shows as Super Admin); their TEAM ROLE is what they are in one team.
_TEAM_ROLE_RANK = {"department_admin": 0, "team_lead": 1, "team_member": 2}
_SETTABLE_TEAM_ROLES = ("department_admin", "team_lead", "team_member")


def _team_sort_key(dept):
	m = re.search(r"(\d+)", dept["department_name"])
	return int(m.group(1)) if m else 999


def _portal_departments(only=None):
	"""The departments the portal calls teams: direct children of "All Departments" that
	carry an office tag. `only` narrows to a list of names."""
	has_lead = frappe.get_meta("Department").has_field("portal_team_lead")
	fields = ["name", "department_name", "portal_office"]
	if has_lead:
		fields.append("portal_team_lead")
	filters = {"parent_department": "All Departments", "portal_office": ["!=", ""]}
	if only is not None:
		filters["name"] = ["in", list(only) or [""]]
	departments = frappe.get_all("Department", filters=filters, fields=fields)
	for d in departments:
		d.setdefault("portal_team_lead", None)
	return sorted(departments, key=_team_sort_key)


def _super_admin_users() -> set:
	"""Enabled logins that hold the Super Admin (System Manager) role."""
	holders = set(
		frappe.get_all("Has Role", filters={"parenttype": "User", "role": helper.SUPER_ADMIN_ROLE}, pluck="parent")
	)
	holders.discard("Administrator")
	holders.discard("Guest")
	if not holders:
		return set()
	return set(frappe.get_all("User", filters={"name": ["in", list(holders)], "enabled": 1}, pluck="name"))


def _admins_by_department(dept_names) -> dict:
	out: dict[str, list] = {}
	if not dept_names or not frappe.db.table_exists(helper.DEPARTMENT_ADMIN_DOCTYPE):
		return out
	rows = frappe.get_all(
		helper.DEPARTMENT_ADMIN_DOCTYPE,
		filters={"parent": ["in", list(dept_names)], "parenttype": "Department"},
		fields=["parent", "user"],
		order_by="idx asc",
	)
	for r in rows:
		if r.user and r.user not in out.setdefault(r.parent, []):
			out[r.parent].append(r.user)
	return out


def _assigned_by_department(dept_names) -> dict:
	"""Team membership = Frappe's standard "Assign To" (ToDo) on the Department doc."""
	out: dict[str, list] = {}
	if not dept_names:
		return out
	rows = frappe.get_all(
		"ToDo",
		filters={
			"reference_type": "Department",
			"reference_name": ["in", list(dept_names)],
			"status": ["not in", ("Cancelled", "Closed")],
		},
		fields=["reference_name", "allocated_to"],
	)
	for r in rows:
		if r.allocated_to and r.allocated_to not in out.setdefault(r.reference_name, []):
			out[r.reference_name].append(r.allocated_to)
	return out


def _project_counts(user_ids) -> dict:
	"""How many projects each of these logins is on the team of."""
	if not user_ids:
		return {}
	pu = frappe.qb.DocType("Project User")
	rows = (
		frappe.qb.from_(pu)
		.select(pu.user, pu.parent)
		.distinct()
		.where(pu.user.isin(list(user_ids)) & (pu.parenttype == "Project"))
		.run(as_dict=True)
	)
	out: dict[str, int] = {}
	for r in rows:
		out[r["user"]] = out.get(r["user"], 0) + 1
	return out


def _team_people(departments) -> dict:
	"""Everyone in each department (assigned members, the lead, the admins), with their
	team role. Disabled logins are left out. Returns {department: [person dicts]}."""
	names = [d.name for d in departments]
	assigned = _assigned_by_department(names)
	admins = _admins_by_department(names)
	super_admins = _super_admin_users()

	ids = set()
	for d in departments:
		ids |= set(assigned.get(d.name, [])) | set(admins.get(d.name, []))
		if d.portal_team_lead:
			ids.add(d.portal_team_lead)
	info = {}
	if ids:
		for r in frappe.get_all(
			"User",
			filters={"name": ["in", list(ids)]},
			fields=["name", "full_name", "enabled", "user_type", "user_image"],
		):
			info[r.name] = r
	counts = _project_counts(ids)

	out = {}
	for d in departments:
		lead = d.portal_team_lead
		dept_admins = admins.get(d.name, [])
		ordered = list(dict.fromkeys([*dept_admins, *([lead] if lead else []), *assigned.get(d.name, [])]))
		people = []
		for u in ordered:
			u_info = info.get(u)
			if not u_info or not u_info.enabled:
				continue
			team_role = (
				"department_admin" if u in dept_admins else "team_lead" if u == lead else "team_member"
			)
			people.append(
				{
					"user": u,
					"full_name": u_info.full_name or u,
					"user_image": u_info.user_image,
					"team_role": team_role,
					"is_super_admin": u in super_admins,
					"role": "super_admin" if u in super_admins else team_role,
					"project_count": counts.get(u, 0),
				}
			)
		people.sort(key=lambda p: (_TEAM_ROLE_RANK[p["team_role"]], p["full_name"].lower()))
		out[d.name] = people
	return out


def _label(role_key: str) -> str:
	return helper.ROLE_LABELS.get(role_key, role_key)


@frappe.whitelist()
def get_teams():
	"""Teams with their people. A Super Admin / Department Admin sees every team; a Team
	Lead sees the team(s) they lead; everyone else gets an empty list rather than an error
	so the shared Dashboard widget still renders. Kept in the shape the Teams page and the
	Dashboard already read (members[].name / employee_name / designation / company_email),
	with the roles added."""
	helper.assert_portal_user()
	is_admin = helper.has_portal_staff_project_access()
	led_names = [] if is_admin else helper.led_department_names()
	if not is_admin and not (helper.is_team_lead() and led_names):
		return []
	departments = _portal_departments(None if is_admin else led_names)
	people_by_dept = _team_people(departments)
	can_edit_all = helper.is_super_admin()
	admin_teams = set(helper.admin_department_names()) if helper.is_dept_admin() else set()

	has_team_field = frappe.get_meta("Project").has_field("portal_team")
	result = []
	for dept in departments:
		people = people_by_dept.get(dept.name, [])
		members = [
			{
				"name": p["user"],
				"employee_name": p["full_name"],
				# The Teams page prints this under the name.
				"designation": None if p["role"] == "team_member" else _label(p["role"]),
				"company_email": p["user"],
				"role": p["role"],
				"team_role": p["team_role"],
			}
			for p in people
		]
		project_count = active_project_count = 0
		if has_team_field:
			project_count = frappe.db.count("Project", {"portal_team": dept.name})
			active_project_count = frappe.db.count("Project", {"portal_team": dept.name, "status": "Open"})
		result.append(
			{
				"name": dept.name,
				"department_name": dept.department_name,
				"office": dept.portal_office or "",
				"member_count": len(members),
				"members": members,
				"team_lead": dept.portal_team_lead or None,
				"project_count": project_count,
				"active_project_count": active_project_count,
				"can_edit": can_edit_all or dept.name in admin_teams,
			}
		)
	return result


@frappe.whitelist()
def get_org_chart():
	"""Everything the Org Chart page draws: Super Admins on top, then each team with its
	Department Admins, Team Lead and members, and what the caller may do to each person.

	Open to Super Admins and Department Admins (who run it) and Team Leads (who assign
	people from it to projects). Nobody else, and no client contact."""
	helper.assert_portal_user()
	helper.assert_org_chart_access()

	caller = frappe.session.user
	caller_is_super = helper.is_super_admin(caller)
	admin_teams = set(helper.admin_department_names(caller)) if helper.is_dept_admin(caller) else set()
	led_teams = set(helper.led_department_names(caller)) if helper.is_team_lead(caller) else set()

	departments = _portal_departments()
	people_by_dept = _team_people(departments)
	super_admins = _super_admin_users()

	# helper.can_reset_password_for() for the whole chart in a handful of queries.
	all_dept_admins = {u for users in _admins_by_department([d.name for d in departments]).values() for u in users}
	caller_is_dept_admin = helper.is_dept_admin(caller) and not caller_is_super
	scope_users = helper.department_member_users(admin_teams) if caller_is_dept_admin else set()

	def can_reset(target):
		if target == caller or target in ("Administrator", "Guest"):
			return False
		if caller_is_super:
			return True
		if not caller_is_dept_admin:
			return False
		return target not in super_admins and target not in all_dept_admins and target in scope_users

	teams = []
	in_a_team = set()
	for dept in departments:
		can_edit = caller_is_super or dept.name in admin_teams
		members = []
		for p in people_by_dept.get(dept.name, []):
			in_a_team.add(p["user"])
			target_is_admin_here = p["team_role"] == "department_admin"
			# Only a Super Admin touches a Department Admin or a Super Admin.
			may_touch = can_edit and (caller_is_super or (not target_is_admin_here and not p["is_super_admin"]))
			members.append(
				{
					**p,
					"role_label": _label(p["role"]),
					"team_role_label": _label(p["team_role"]),
					"can_change_role": may_touch,
					"can_remove": may_touch,
					"can_reset_password": can_reset(p["user"]),
				}
			)
		teams.append(
			{
				"name": dept.name,
				"department_name": dept.department_name,
				"office": dept.portal_office or "",
				"member_count": len(members),
				"members": members,
				"can_edit": can_edit,
				"is_mine": dept.name in admin_teams or dept.name in led_teams,
			}
		)

	super_admin_rows = []
	if super_admins:
		for r in frappe.get_all(
			"User",
			filters={"name": ["in", list(super_admins)]},
			fields=["name", "full_name", "user_image"],
			order_by="full_name asc",
		):
			super_admin_rows.append(
				{
					"user": r.name,
					"full_name": r.full_name or r.name,
					"user_image": r.user_image,
					"can_reset_password": can_reset(r.name),
				}
			)

	unassigned = []
	if helper.has_portal_staff_project_access(caller):
		loose = [
			r
			for r in frappe.get_all(
				"User",
				filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest", "Administrator"]]},
				fields=["name", "full_name"],
				order_by="full_name asc",
				limit_page_length=300,
			)
			if r.name not in in_a_team
		]
		loose_counts = _project_counts([r.name for r in loose])
		for r in loose:
			unassigned.append(
				{
					"user": r.name,
					"full_name": r.full_name or r.name,
					"is_super_admin": r.name in super_admins,
					"project_count": loose_counts.get(r.name, 0),
					"can_reset_password": can_reset(r.name),
				}
			)

	role = helper.get_portal_role(caller)
	return {
		"me": {
			"user": caller,
			"role": role,
			"role_label": _label(role),
			"is_super_admin": caller_is_super,
			"can_edit_any_team": caller_is_super or bool(admin_teams),
			"can_grant_admin": caller_is_super,
			"can_assign_to_projects": not helper.is_customer_only(caller),
			"can_reset_passwords": helper.has_portal_staff_project_access(caller),
		},
		"super_admins": super_admin_rows,
		"teams": teams,
		"unassigned": unassigned,
	}


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
	helper.assert_manage_team(team)
	doc = frappe.get_doc("Department", team)
	if department_name is not None and department_name.strip():
		doc.department_name = department_name.strip()
	if office is not None:
		doc.portal_office = office or None
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "department_name": doc.department_name, "office": doc.portal_office}


@frappe.whitelist()
def create_or_get_team(department_name, office=None):
	"""Create a new team (Department), or return the existing one if the exact
	name is already taken — same "no duplicate name" behaviour as
	projects.create_or_get_customer, for the analogous "Create team" button on
	the Project detail page's team picker. Only a Super Admin creates teams: a
	Department Admin looks after the ones they were given."""
	from erpnext import get_default_company

	if not helper.is_super_admin():
		frappe.throw(_("Only a Super Admin can create a team."), frappe.PermissionError)

	name = (department_name or "").strip()
	if len(name) < 2:
		frappe.throw(_("Team name is too short"))

	existing = frappe.db.get_value("Department", {"department_name": name}, "name")
	if existing:
		return {"name": existing, "department_name": name, "created": False}

	company = get_default_company()
	if not company:
		frappe.throw(_("Set a default Company first."))

	doc = frappe.get_doc(
		{
			"doctype": "Department",
			"department_name": name,
			"company": company,
			"parent_department": "All Departments",
			"is_group": 0,
			"portal_office": (office or "").strip(),
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "department_name": doc.department_name, "created": True}


@frappe.whitelist()
def get_assignable_users(team=None):
	"""Enabled staff logins not already assigned to `team`, for the Add Member picker.
	Client contacts are never offered: they are not part of the organisation."""
	if team:
		helper.assert_manage_team(team)
	else:
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
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest", "Administrator"]]},
		fields=["name", "full_name"],
		order_by="full_name asc",
		limit_page_length=500,
	)
	return [u for u in users if u.name not in assigned and not helper.is_customer_only(u.name)]


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


def _assert_org_person(user: str) -> None:
	"""Who can be placed in a team: an enabled staff login. Never a client contact, the
	built-in accounts, or a login that does not exist."""
	user = cstr(user).strip()
	if not user or user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		frappe.throw(_("User not found"))
	if not frappe.db.get_value("User", user, "enabled"):
		frappe.throw(_("{0} is disabled.").format(user))
	if helper.is_customer_only(user):
		frappe.throw(_("Client contacts cannot be part of a team: {0}").format(user), frappe.PermissionError)


def _assign_users_to_team(team: str, users: list) -> None:
	"""Team membership = assigning the Department doc to Users via Frappe's standard Assign To."""
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


@frappe.whitelist()
def add_team_member(team, user=None, user_group=None):
	"""Add people to a team: a Super Admin to any team, a Department Admin to theirs.

	`user_group` resolves to its member users and assigns all of them at once — same
	behaviour as picking "Assign To User Group" in Frappe's native assign dialog."""
	helper.assert_manage_team(team)
	if not frappe.db.exists("Department", team):
		frappe.throw(_("Team not found"))

	if user_group:
		users = frappe.get_all("User Group Member", filters={"parent": user_group}, pluck="user")
		if not users:
			frappe.throw(_("This User Group has no members"))
	else:
		if not user:
			frappe.throw(_("user or user_group is required"))
		users = [user]

	for u in users:
		_assert_org_person(u)
	_assign_users_to_team(team, users)
	return {"team": team, "users": users}


@frappe.whitelist(methods=["POST"])
def remove_team_member(team, user):
	"""Take someone out of a team. Only a Super Admin or the team's Department Admin may,
	and only a Super Admin removes a Department Admin. If they were the Team Lead, the team
	has no lead afterwards."""
	helper.assert_manage_team(team)
	user = cstr(user).strip()
	dept = frappe.get_doc("Department", team)
	admin_rows = [r for r in (dept.get("portal_department_admins") or []) if r.user == user]
	if admin_rows and not helper.is_super_admin():
		frappe.throw(_("Only a Super Admin can remove a Department Admin."), frappe.PermissionError)

	from frappe.desk.form.assign_to import remove as assign_remove

	assign_remove("Department", team, user, ignore_permissions=True)

	changed = False
	if dept.get("portal_team_lead") == user:
		dept.portal_team_lead = None
		changed = True
	for row in admin_rows:
		dept.remove(row)
		changed = True
	if changed:
		dept.save(ignore_permissions=True)  # the Department hook updates their roles
	return {"team": team, "user": user}


@frappe.whitelist(methods=["POST"])
def remove_team_lead(team):
	"""Remove the Team Lead of a team. They stay on the team as a Team Member."""
	helper.assert_manage_team(team)
	dept = frappe.get_doc("Department", team)
	if not dept.get("portal_team_lead"):
		frappe.throw(_("This team has no Team Lead."))
	former = dept.portal_team_lead
	dept.portal_team_lead = None
	dept.save(ignore_permissions=True)
	return {"team": team, "former_lead": former}


@frappe.whitelist(methods=["POST"])
def set_member_role(team, user, role):
	"""Change what someone is in one team: department_admin, team_lead or team_member.

	  * A Super Admin may do all three in any team.
	  * A Department Admin may make someone a Team Lead or a Team Member in the teams they
	    administer, but cannot make or change a Department Admin.
	  * A team has one Team Lead: naming a new one makes the previous lead a Team Member.
	  * The person is added to the team first if they are not on it yet.
	A person holds one role per team, so choosing one replaces any other they had there."""
	role = cstr(role).strip()
	if role not in _SETTABLE_TEAM_ROLES:
		frappe.throw(_("Role must be Department Admin, Team Lead or Team Member."))
	helper.assert_manage_team(team)
	if not frappe.db.exists("Department", team):
		frappe.throw(_("Team not found"))
	_assert_org_person(user)
	user = cstr(user).strip()
	caller_is_super = helper.is_super_admin()

	dept = frappe.get_doc("Department", team)
	admin_rows = [r for r in (dept.get("portal_department_admins") or []) if r.user == user]
	is_admin_here = bool(admin_rows)
	if (role == "department_admin" or is_admin_here) and not caller_is_super:
		frappe.throw(_("Only a Super Admin can make or change a Department Admin."), frappe.PermissionError)
	if helper.is_super_admin(user) and not caller_is_super:
		frappe.throw(_("Only a Super Admin can change a Super Admin's team role."), frappe.PermissionError)

	if user not in _assigned_by_department([team]).get(team, []):
		_assign_users_to_team(team, [user])

	lead_here = dept.get("portal_team_lead") == user
	if role == "team_member":
		if lead_here:
			dept.portal_team_lead = None
		for row in admin_rows:
			dept.remove(row)
	elif role == "team_lead":
		dept.portal_team_lead = user  # replaces the previous lead, who stays a member
		for row in admin_rows:
			dept.remove(row)
	else:  # department_admin
		if not is_admin_here:
			dept.append("portal_department_admins", {"user": user})
		if lead_here:
			dept.portal_team_lead = None
	dept.save(ignore_permissions=True)  # the Department hook updates their roles
	return {"team": team, "user": user, "role": role}
