import re

import frappe
from frappe import _
from frappe.utils import cint, cstr

from portal_app.api import helper

# Team roles, highest first. A person's ROLE in the chart is the highest portal role they
# hold (a Super Admin shows as Super Admin); their TEAM ROLE is what they are in one team.
_TEAM_ROLE_RANK = {"department_admin": 0, "team_lead": 1, "team_member": 2}
_SETTABLE_TEAM_ROLES = ("department_admin", "team_lead", "team_member")


def _team_sort_key(dept):
	m = re.search(r"(\d+)", dept["department_name"])
	return int(m.group(1)) if m else 999


def _portal_departments(only=None, include_pending=False):
	"""The departments the portal calls teams (helper.portal_team_names), each with the
	Department unit it sits under (parent_unit / parent_unit_label). `only` narrows to a
	list of names."""
	names = helper.portal_team_names(include_pending=include_pending)
	if only is not None:
		wanted = set(only)
		names = [n for n in names if n in wanted]
	if not names:
		return []
	has_lead = frappe.get_meta("Department").has_field("portal_team_lead")
	fields = ["name", "department_name", "portal_office"]
	if has_lead:
		fields.append("portal_team_lead")
	departments = frappe.get_all("Department", filters={"name": ["in", names]}, fields=fields)
	units = {}
	for d in departments:
		d.setdefault("portal_team_lead", None)
		d["parent_unit"] = helper.team_department(d.name)
		if d["parent_unit"] and d["parent_unit"] not in units:
			units[d["parent_unit"]] = (
				frappe.db.get_value("Department", d["parent_unit"], "department_name") or d["parent_unit"]
			)
		d["parent_unit_label"] = units.get(d["parent_unit"]) if d["parent_unit"] else None
	return sorted(departments, key=_team_sort_key)


def _visible_team_names(caller) -> list | None:
	"""The teams the caller sees on the Teams page and the Org Chart (None = every team,
	pending ones included, for a Super Admin): a Department Admin / Coordinator the teams of
	their units, a Team Manager the teams they manage."""
	if helper.is_super_admin(caller):
		return None
	out = set()
	for unit in helper.management_unit_names(caller):
		out |= set(helper.teams_of_unit(unit))
	if helper.is_team_lead(caller):
		out |= set(helper.led_department_names(caller))
	return sorted(out)


def _admin_units(caller) -> set:
	"""Units the caller administers as a Department Admin (helper.can_manage_team scope)."""
	if helper.is_super_admin(caller) or not helper.is_dept_admin(caller):
		return set()
	return set(helper.admin_department_names(caller))


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
	"""Teams with their people. A Super Admin sees every team; a Department Admin or
	Department Coordinator the teams of their own departments (a coordinator read-only);
	a Team Manager the team(s) they manage; everyone else gets an empty list rather than
	an error so the shared Dashboard widget still renders. Kept in the shape the Teams
	page and the Dashboard already read (members[].name / employee_name / designation /
	company_email), with the roles and the parent department added."""
	helper.assert_portal_user()
	caller = frappe.session.user
	visible = _visible_team_names(caller)
	if visible is not None and not visible:
		return []
	departments = _portal_departments(visible)
	people_by_dept = _team_people(departments)
	can_edit_all = helper.is_super_admin()
	admin_units = _admin_units(caller)

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
				"parent_unit": dept.parent_unit,
				"parent_unit_label": dept.parent_unit_label,
				"member_count": len(members),
				"members": members,
				"team_lead": dept.portal_team_lead or None,
				"project_count": project_count,
				"active_project_count": active_project_count,
				"can_edit": can_edit_all or dept.name in admin_units or dept.parent_unit in admin_units,
			}
		)
	return result


def _rows_by_unit(child_doctype, unit_names) -> dict:
	out: dict[str, list] = {}
	if not unit_names or not frappe.db.table_exists(child_doctype):
		return out
	for r in frappe.get_all(
		child_doctype,
		filters={"parent": ["in", list(unit_names)], "parenttype": "Department"},
		fields=["parent", "user"],
		order_by="idx asc",
	):
		if r.user and r.user not in out.setdefault(r.parent, []):
			out[r.parent].append(r.user)
	return out


def _department_blocks(unit_names, super_admins) -> dict:
	"""For each Department unit: {label, pending, admins, coordinators, members} (members
	= open assignments on the unit itself). Disabled logins are left out."""
	unit_names = [u for u in unit_names if u]
	if not unit_names:
		return {}
	meta = frappe.get_meta("Department")
	fields = ["name", "department_name"] + (["portal_pending"] if meta.has_field("portal_pending") else [])
	rows = {r.name: r for r in frappe.get_all("Department", filters={"name": ["in", unit_names]}, fields=fields)}
	pending = helper.pending_unit_names()
	admins = _rows_by_unit(helper.DEPARTMENT_ADMIN_DOCTYPE, unit_names)
	coordinators = _rows_by_unit(helper.DEPARTMENT_COORDINATOR_DOCTYPE, unit_names)
	assigned = _assigned_by_department(unit_names)
	ids = set()
	for u in unit_names:
		ids |= set(admins.get(u, [])) | set(coordinators.get(u, [])) | set(assigned.get(u, []))
	info = {}
	if ids:
		for r in frappe.get_all(
			"User", filters={"name": ["in", list(ids)]}, fields=["name", "full_name", "enabled", "user_image"]
		):
			info[r.name] = r
	counts = _project_counts(ids)

	def people(users, unit_role):
		out = []
		for u in users:
			u_info = info.get(u)
			if not u_info or not u_info.enabled:
				continue
			out.append(
				{
					"user": u,
					"full_name": u_info.full_name or u,
					"user_image": u_info.user_image,
					"unit_role": unit_role,
					"unit_role_label": _label(unit_role),
					"is_super_admin": u in super_admins,
					"project_count": counts.get(u, 0),
				}
			)
		return sorted(out, key=lambda p: p["full_name"].lower())

	out = {}
	for u in unit_names:
		row = rows.get(u)
		if not row:
			continue
		unit_admins = admins.get(u, [])
		unit_coords = coordinators.get(u, [])
		out[u] = {
			"name": u,
			"label": row.department_name or u,
			"pending": u in pending,
			"admins": people(unit_admins, "department_admin"),
			"coordinators": people([x for x in unit_coords if x not in unit_admins], "department_coordinator"),
			"members": people(
				[x for x in assigned.get(u, []) if x not in unit_admins and x not in unit_coords], "team_member"
			),
		}
	return out


@frappe.whitelist()
def get_org_chart():
	"""Everything the Org Chart page draws: Super Admins on top, then each department with
	its Department Admins, Department Coordinators and members, and under it its teams
	(Team Manager, then Project Architects), and what the caller may do to each person.

	Who sees what: a Super Admin everything (pending departments flagged); a Department
	Admin or Coordinator their own units; a Team Manager their teams. Nobody else, and no
	client contact. The flat `teams` list is kept for older callers. Read-only."""
	helper.assert_portal_user()
	helper.assert_org_chart_access()

	caller = frappe.session.user
	caller_is_super = helper.is_super_admin(caller)
	admin_units = _admin_units(caller)
	led_teams = set(helper.led_department_names(caller)) if helper.is_team_lead(caller) else set()
	mgmt_units = set() if caller_is_super else set(helper.management_unit_names(caller))

	departments = _portal_departments(_visible_team_names(caller), include_pending=caller_is_super)
	pending = helper.pending_unit_names() if caller_is_super else set()
	people_by_dept = _team_people(departments)
	super_admins = _super_admin_users()

	# helper.can_reset_password_for() for the whole chart in a handful of queries.
	all_dept_admins = (
		set(frappe.get_all(helper.DEPARTMENT_ADMIN_DOCTYPE, filters={"parenttype": "Department"}, pluck="user"))
		if frappe.db.table_exists(helper.DEPARTMENT_ADMIN_DOCTYPE)
		else set()
	)
	caller_is_dept_admin = helper.is_dept_admin(caller) and not caller_is_super
	scope_users = helper.department_member_users(admin_units) if caller_is_dept_admin else set()

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
		can_edit = caller_is_super or dept.name in admin_units or dept.parent_unit in admin_units
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
				"parent_unit": dept.parent_unit,
				"parent_unit_label": dept.parent_unit_label,
				"pending": dept.name in pending,
				"member_count": len(members),
				"members": members,
				"can_edit": can_edit,
				"is_mine": dept.name in admin_units
				or dept.name in led_teams
				or dept.name in mgmt_units
				or dept.parent_unit in mgmt_units,
			}
		)

	# Departments above the teams.
	if caller_is_super:
		unit_names = helper.portal_unit_department_names(include_pending=True)
	else:
		active_units = set(helper.portal_unit_department_names())
		unit_names = [u for u in mgmt_units if u in active_units]
	unit_names = list(dict.fromkeys([*unit_names, *(t["parent_unit"] for t in teams if t["parent_unit"])]))
	blocks = _department_blocks(unit_names, super_admins)
	department_rows = []
	for unit in sorted(blocks, key=lambda u: blocks[u]["label"].lower()):
		block = blocks[unit]
		for group in ("admins", "coordinators", "members"):
			for p in block[group]:
				in_a_team.add(p["user"])
				p["can_reset_password"] = can_reset(p["user"])
		department_rows.append(
			{
				**block,
				"teams": [t for t in teams if t["parent_unit"] == unit],
				"can_edit": caller_is_super or unit in admin_units,
			}
		)
	loose_teams = [t for t in teams if not t["parent_unit"] or t["parent_unit"] not in blocks]
	if loose_teams:
		department_rows.append(
			{
				"name": "",
				"label": _("Other teams"),
				"pending": False,
				"admins": [],
				"coordinators": [],
				"members": [],
				"teams": loose_teams,
				"can_edit": False,
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
	scope = helper.role_change_scope(caller)
	if scope["kind"] == "super_admin":
		assignable_roles = list(helper.SETTABLE_ROLE_KEYS)
	elif scope["kind"] == "department_admin":
		assignable_roles = ["department_coordinator", "team_lead", "team_member"]
	else:
		assignable_roles = []
	return {
		"me": {
			"user": caller,
			"role": role,
			"role_label": _label(role),
			"role_designations": helper.get_portal_designations(caller),
			"is_super_admin": caller_is_super,
			"can_edit_any_team": caller_is_super or bool(admin_units),
			"can_grant_admin": caller_is_super,
			"can_assign_to_projects": not helper.is_customer_only(caller),
			"can_reset_passwords": helper.has_portal_staff_project_access(caller),
			"can_change_roles": bool(assignable_roles),
			"assignable_roles": assignable_roles,
		},
		"super_admins": super_admin_rows,
		"departments": department_rows,
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

	team_names = helper.portal_team_names()
	departments = (
		frappe.get_all(
			"Department",
			filters={"name": ["in", team_names]},
			fields=["name", "department_name", "portal_office"],
		)
		if team_names
		else []
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
	team_names = helper.portal_team_names()
	if not team_names:
		return []
	rows = frappe.get_all(
		"Department",
		filters={"name": ["in", team_names], "portal_office": ["!=", ""]},
		fields=["portal_office"],
		distinct=True,
	)
	return sorted({r.portal_office for r in rows if r.portal_office})


@frappe.whitelist()
def get_team_options():
	"""Teams for the Team picker on Create / Edit project: [{name, department_name, office}].

	The picker sets Project.portal_team, and the office follows from it. A Department
	Admin or Department Coordinator is offered only the teams of their own units, which
	is what the server allows them to set (projects._assert_may_set_team); everyone else
	who can open the form sees every team and the server refuses a team they may not use.
	No people, only names and office tags, which get_offices already hands to every
	portal user."""
	helper.assert_portal_user()
	helper.assert_not_customer_only()
	only = None
	if not helper.is_super_admin() and (helper.is_dept_admin() or helper.is_dept_coordinator()):
		only = set()
		for unit in helper.management_unit_names():
			only |= set(helper.teams_of_unit(unit))
	return [
		{
			"name": d.name,
			"department_name": d.department_name,
			"office": d.portal_office or "",
			"parent_unit": d.parent_unit,
			"parent_unit_label": d.parent_unit_label,
		}
		for d in _portal_departments(only)
	]


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


def _assert_department_unit(department) -> None:
	"""`department` must be an existing Department unit (portal_unit "Department")."""
	department = cstr(department).strip()
	if (
		not department
		or not frappe.db.exists("Department", department)
		or frappe.db.get_value("Department", department, "portal_unit") != "Department"
	):
		frappe.throw(_("{0} is not a portal department.").format(department or _("(blank)")))


def _make_group(department) -> None:
	"""A team can only sit under a group node (NestedSet): turn a leaf department into one."""
	if not frappe.db.get_value("Department", department, "is_group"):
		doc = frappe.get_doc("Department", department)
		doc.is_group = 1
		doc.save(ignore_permissions=True)


@frappe.whitelist()
def create_or_get_team(department_name, office=None, department=None):
	"""Create a new team (Department), or return the existing one if the exact
	name is already taken — same "no duplicate name" behaviour as
	projects.create_or_get_customer, for the analogous "Create team" button on
	the Project detail page's team picker. Only a Super Admin creates teams: a
	Department Admin looks after the ones they were given. With `department` the
	team is created under that Department unit."""
	from erpnext import get_default_company

	if not helper.is_super_admin():
		frappe.throw(_("Only a Super Admin can create a team."), frappe.PermissionError)
	if department:
		_assert_department_unit(department)

	name = (department_name or "").strip()
	if len(name) < 2:
		frappe.throw(_("Team name is too short"))

	existing = frappe.db.get_value("Department", {"department_name": name}, "name")
	if existing:
		return {"name": existing, "department_name": name, "created": False}

	company = get_default_company()
	if not company:
		frappe.throw(_("Set a default Company first."))

	parent = "All Departments"
	if department:
		_make_group(department)
		parent = department
	doc = frappe.get_doc(
		{
			"doctype": "Department",
			"department_name": name,
			"company": company,
			"parent_department": parent,
			"is_group": 0,
			"portal_office": (office or "").strip(),
		}
	)
	if frappe.get_meta("Department").has_field("portal_unit"):
		doc.portal_unit = "Team"
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "department_name": doc.department_name, "created": True}


def _assert_super_admin_for_departments() -> None:
	if not helper.is_super_admin():
		frappe.throw(_("Only a Super Admin can change the portal departments."), frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def create_portal_department(department_name, pending=0):
	"""Create a portal department (the level above the teams) under "All Departments", or
	return the existing one on an exact name match. Super Admin only. A pending
	department records its people but grants nothing until it is activated."""
	from erpnext import get_default_company

	_assert_super_admin_for_departments()
	name = cstr(department_name).strip()
	if len(name) < 2:
		frappe.throw(_("Department name is too short"))
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
			"is_group": 1,
			"portal_unit": "Department",
			"portal_pending": cint(pending),
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "department_name": doc.department_name, "created": True}


@frappe.whitelist(methods=["POST"])
def set_department_pending(department, pending):
	"""Activate a pending department (pending=0) or put one back on hold (pending=1).
	Super Admin only. The Department hook then grants or takes away the marker roles of
	everyone recorded on it and its teams."""
	_assert_super_admin_for_departments()
	_assert_department_unit(department)
	doc = frappe.get_doc("Department", cstr(department).strip())
	doc.portal_pending = cint(pending)
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "pending": cint(doc.portal_pending)}


@frappe.whitelist(methods=["POST"])
def set_team_department(team, department):
	"""Move a team under a portal department. Super Admin only. The team's name, people,
	projects and office stay as they are."""
	_assert_super_admin_for_departments()
	team = cstr(team).strip()
	if team not in helper.portal_team_names(include_pending=True):
		frappe.throw(_("{0} is not a portal team.").format(team))
	_assert_department_unit(department)
	department = cstr(department).strip()
	_make_group(department)
	doc = frappe.get_doc("Department", team)
	doc.parent_department = department
	if frappe.get_meta("Department").has_field("portal_unit"):
		doc.portal_unit = "Team"
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "department": department}


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
	from portal_app.utils import assign_add_unchecked as assign_add

	# assign_add() auto-shares the doc with an assignee who lacks read access to it,
	# and that auto-share checks the CALLING user's own "share" DocPerm on Department
	# — ignore_permissions=True does not bypass this separate, lower-level RBAC check.
	# Pre-share it via frappe.share's own ignore_share_permission flag instead (same
	# fix already applied to _sync_project_assignment for the equivalent Project case).
	for u in users:
		_share.add_docshare("Department", team, user=u, read=1, flags={"ignore_share_permission": True})

	assign_add({"doctype": "Department", "name": team, "assign_to": users})


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
	and only a Super Admin removes a Department Admin. If they were the Team Manager, the
	team has no manager afterwards."""
	helper.assert_manage_team(team)
	user = cstr(user).strip()
	dept = frappe.get_doc("Department", team)
	admin_rows = [r for r in (dept.get("portal_department_admins") or []) if r.user == user]
	if admin_rows and not helper.is_super_admin():
		frappe.throw(_("Only a Super Admin can remove a Department Admin."), frappe.PermissionError)

	from portal_app.utils import assign_remove_unchecked as assign_remove

	assign_remove("Department", team, user)

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
	"""Remove the Team Manager of a team. They stay on the team as a Project Architect."""
	helper.assert_manage_team(team)
	dept = frappe.get_doc("Department", team)
	if not dept.get("portal_team_lead"):
		frappe.throw(_("This team has no Team Manager."))
	former = dept.portal_team_lead
	dept.portal_team_lead = None
	dept.save(ignore_permissions=True)
	return {"team": team, "former_lead": former}


@frappe.whitelist(methods=["POST"])
def set_member_role(team, user, role):
	"""Change what someone is in one team: department_admin, team_lead (Team Manager) or
	team_member (Project Architect); team_manager / project_architect are accepted too.

	  * A Super Admin may do all three in any team.
	  * A Department Admin may make someone a Team Manager or a Project Architect in the
	    teams they administer, but cannot make or change a Department Admin.
	  * A team has one Team Manager: naming a new one makes the previous one a Project
	    Architect.
	  * The person is added to the team first if they are not on it yet.
	A person holds one role per team, so choosing one replaces any other they had there."""
	role = helper.normalize_role_key(role)
	if role not in _SETTABLE_TEAM_ROLES:
		frappe.throw(_("Role must be Department Admin, Team Manager or Project Architect."))
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
