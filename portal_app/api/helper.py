from __future__ import annotations

import frappe
from frappe import _

# The portal's five roles and the Frappe role behind each one:
#   Super Admin       System Manager (the label the portal has always used for it)
#   Department Admin  "Department Admin"  + Department.portal_department_admins rows (scope)
#   Team Lead         "Team Lead"         + Department.portal_team_lead            (scope)
#   Team Member       "Projects User"
#   Client Customer   "Client Customer"   (was "Portal Customer") + Portal User Customer rows
# The two marker roles are kept in sync with the Department data by
# sync_department_role_markers (a Department doc_event), so a change made anywhere,
# portal or Desk, ends up the same.
SUPER_ADMIN_ROLE = "System Manager"
DEPT_ADMIN_ROLE = "Department Admin"
TEAM_LEAD_ROLE = "Team Lead"
TEAM_MEMBER_ROLE = "Projects User"
LEGACY_PROJECTS_MANAGER_ROLE = "Projects Manager"
PORTAL_ROLES = frozenset(
	{SUPER_ADMIN_ROLE, LEGACY_PROJECTS_MANAGER_ROLE, TEAM_MEMBER_ROLE, DEPT_ADMIN_ROLE, TEAM_LEAD_ROLE}
)
PORTAL_CUSTOMER_ROLE = "Client Customer"
LEGACY_PORTAL_CUSTOMER_ROLE = "Portal Customer"
PORTAL_HOME = "/portal-app"
DEPARTMENT_ADMIN_DOCTYPE = "Portal Department Admin"

ROLE_LABELS = {
	"super_admin": "Super Admin",
	"department_admin": "Department Admin",
	"team_lead": "Team Lead",
	"team_member": "Team Member",
	"client_customer": "Client Customer",
}


def get_website_user_home_page(user):
	"""hooks.get_website_user_home_page: after Frappe's own /login or password reset a
	customer contact lands on the portal instead of /me. Returning None for anyone else
	lets Frappe fall through to its normal home-page resolution."""
	if user and user != "Guest" and is_customer_only(user):
		return PORTAL_HOME.strip("/")
	return None


def ensure_user_portal_linked_customer_field() -> None:
	"""Ensure User.portal_linked_customer exists in the database (avoids SQL errors if migrate was skipped)."""
	try:
		if frappe.db.has_column("User", "portal_linked_customer"):
			return
	except Exception:
		pass
	from portal_app.install import ensure_portal_customer_access

	ensure_portal_customer_access()


def ensure_portal_customer_role() -> None:
	"""Make sure the Client Customer role exists (avoids LinkValidationError on Has Role).

	The role used to be called "Portal Customer". If that one still exists it is RENAMED
	(Frappe updates every user's Has Role row and every permission row), never replaced
	by a fresh role, or every existing client contact would silently lose the role."""
	if frappe.db.exists("Role", PORTAL_CUSTOMER_ROLE):
		return
	if frappe.db.exists("Role", LEGACY_PORTAL_CUSTOMER_ROLE):
		frappe.rename_doc(
			"Role", LEGACY_PORTAL_CUSTOMER_ROLE, PORTAL_CUSTOMER_ROLE, force=True, show_alert=False, rebuild_search=False
		)
		frappe.db.commit()
		frappe.clear_cache()
		return
	doc = frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": PORTAL_CUSTOMER_ROLE,
			"desk_access": 0,
			"is_custom": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()


def ensure_portal_roles() -> None:
	"""Create the Department Admin and Team Lead marker roles (Desk users, internal)."""
	created = False
	for role in (DEPT_ADMIN_ROLE, TEAM_LEAD_ROLE):
		if frappe.db.exists("Role", role):
			continue
		frappe.get_doc(
			{"doctype": "Role", "role_name": role, "desk_access": 1, "is_custom": 1}
		).insert(ignore_permissions=True)
		created = True
	if created:
		frappe.clear_cache()


def user_is_customer_portal_user(user=None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	return PORTAL_CUSTOMER_ROLE in frappe.get_roles(user)


def is_customer_only(user=None) -> bool:
	"""True only for a genuine client contact — never for staff.

	`user_is_customer_portal_user()` alone is NOT a safe test. Administrator holds
	EVERY role in Frappe, including Portal Customer, so it reports True for the
	superuser; the same happens to any staff member who is also given the role.
	get_allowed_project_names() avoids the trap by checking staff access first, and
	anything gating customer-only behaviour must do the same.
	"""
	if has_portal_staff_project_access(user):
		return False
	return user_is_customer_portal_user(user)


def assert_not_customer_only(user=None) -> None:
	"""Gate for internal working tools (tasks, Kanban, calendar, Gantt, daily tasks,
	AI chat). The sidebar hides them from client contacts; this makes the server agree,
	so opening the page by URL or calling the API directly returns nothing."""
	if is_customer_only(user):
		frappe.throw(_("This part of the portal is for ATA staff."), frappe.PermissionError)


def is_super_admin(user=None) -> bool:
	"""Super Admin = System Manager (and the built-in Administrator account)."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	if user == "Administrator":
		return True
	return SUPER_ADMIN_ROLE in frappe.get_roles(user)


def is_dept_admin(user=None) -> bool:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	return DEPT_ADMIN_ROLE in frappe.get_roles(user)


def is_team_lead(user=None) -> bool:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	return TEAM_LEAD_ROLE in frappe.get_roles(user)


def has_portal_staff_project_access(user=None) -> bool:
	"""The admin tier: Super Admin or Department Admin.

	Both get the management views (Dashboard, Teams, Org Chart editing) and the manager
	fields on projects. What each may SEE is still decided by get_allowed_project_names():
	a Super Admin sees the whole portfolio, a Department Admin sees their departments'
	projects. It also overrides customer-only scoping, so an admin who somehow also holds
	the client role is never treated as a client."""
	user = user or frappe.session.user
	if user == "Guest":
		return False
	return is_super_admin(user) or is_dept_admin(user)


def get_portal_role(user=None) -> str | None:
	"""The portal role key of a login: super_admin, department_admin, team_lead,
	team_member or client_customer (None if the login has no portal role at all)."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None
	if is_super_admin(user):
		return "super_admin"
	roles = set(frappe.get_roles(user))
	if DEPT_ADMIN_ROLE in roles:
		return "department_admin"
	if PORTAL_CUSTOMER_ROLE in roles:
		return "client_customer"
	if TEAM_LEAD_ROLE in roles:
		return "team_lead"
	if roles & {TEAM_MEMBER_ROLE, LEGACY_PROJECTS_MANAGER_ROLE} or frappe.db.exists(
		"Project User", {"user": user, "parenttype": "Project"}
	):
		return "team_member"
	return None


def get_portal_linked_customer(user=None) -> str | None:
	user = user or frappe.session.user
	if user == "Guest":
		return None
	if not frappe.get_meta("User").has_field("portal_linked_customer"):
		return None
	return frappe.db.get_value("User", user, "portal_linked_customer")


PORTAL_USER_CUSTOMER = "Portal User Customer"


def get_portal_linked_customers(user=None) -> list[str]:
	"""Every customer a portal login can see.

	Only Portal User Customer rows grant access. User.portal_linked_customer is a
	display value: every user has write on their OWN User record (Frappe's
	share_with_self), so a client contact could set that field to another customer
	and read that customer's projects. The legacy field is read only before the
	table exists (site not migrated yet)."""
	user = user or frappe.session.user
	if user == "Guest":
		return []
	if not frappe.db.table_exists(PORTAL_USER_CUSTOMER):
		primary = get_portal_linked_customer(user)
		return [primary] if primary else []
	rows = frappe.get_all(PORTAL_USER_CUSTOMER, filters={"user": user}, pluck="customer", order_by="creation asc")
	primary = get_portal_linked_customer(user)
	if primary in rows:
		rows.remove(primary)
		rows.insert(0, primary)
	return rows


def get_customer_contact_users(customer) -> list[str]:
	"""Every login with access to this customer (Portal User Customer rows)."""
	if not frappe.db.table_exists(PORTAL_USER_CUSTOMER):
		if not frappe.get_meta("User").has_field("portal_linked_customer"):
			return []
		return sorted(frappe.get_all("User", filters={"portal_linked_customer": customer}, pluck="name"))
	return sorted(set(frappe.get_all(PORTAL_USER_CUSTOMER, filters={"customer": customer}, pluck="user")))


def delete_portal_user_customer_rows(doc, method=None):
	"""doc_events on_trash for User / Customer: runs before Frappe's link check, so the
	access rows never block deleting the login or the customer."""
	if not frappe.db.table_exists(PORTAL_USER_CUSTOMER):
		return
	field = "user" if doc.doctype == "User" else "customer"
	frappe.db.delete(PORTAL_USER_CUSTOMER, {field: doc.name})


def drop_customer_rows_without_role(doc, method=None):
	"""doc_events User.on_update: taking the Portal Customer role away (e.g. in Desk)
	removes every customer the login had. Otherwise the rows would silently grant the
	old customers back the next time anyone re-adds the role."""
	if not frappe.db.table_exists(PORTAL_USER_CUSTOMER):
		return
	if any(r.role == PORTAL_CUSTOMER_ROLE for r in (doc.get("roles") or [])):
		return
	for name in frappe.get_all(PORTAL_USER_CUSTOMER, filters={"user": doc.name}, pluck="name"):
		# delete_doc, not a raw delete: PortalUserCustomer.on_trash revokes the
		# folder shares and a Deleted Document records who removed the access.
		frappe.delete_doc(PORTAL_USER_CUSTOMER, name, ignore_permissions=True)


def user_can_use_portal(user=None) -> bool:
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if user_is_customer_portal_user(user):
		# Allow sign-in; project/data access still requires a linked customer in get_allowed_project_names.
		return True
	roles = set(frappe.get_roles(user))
	if roles & PORTAL_ROLES:
		return True
	return bool(
		frappe.db.sql(
			"SELECT 1 FROM `tabProject User` WHERE user=%s LIMIT 1",
			user,
		)
	)


def get_allowed_project_names(user=None) -> list[str]:
	"""Every project this login may SEE.

	  Super Admin       the whole portfolio.
	  Department Admin  their departments' projects (portal_team, or anyone in the
	                    department on the team or as Lead Architect), plus projects with no
	                    team at all, which somebody has to triage, plus their own.
	  Team Lead         the same for the teams they lead, plus their own.
	  Team Member       only the projects they are on the team of or lead.
	  Client Customer   only the projects of their customers.
	"""
	user = user or frappe.session.user
	if not user_can_use_portal(user):
		return []

	if is_super_admin(user):
		return frappe.get_all("Project", pluck="name")

	roles = set(frappe.get_roles(user))
	is_admin = DEPT_ADMIN_ROLE in roles

	# A client contact (an admin who also holds the client role is still an admin).
	if not is_admin and PORTAL_CUSTOMER_ROLE in roles:
		custs = get_portal_linked_customers(user)
		if not custs:
			return []
		return frappe.get_all("Project", filters={"customer": ["in", custs]}, pluck="name")

	names = set(own_project_names(user))
	if is_admin or TEAM_LEAD_ROLE in roles:
		names |= get_scope_project_names(user)
	if is_admin:
		names |= set(get_unassigned_project_names())
	return sorted(names)


def own_project_names(user=None) -> list[str]:
	"""Projects this login is on the team of, or is the Lead Architect of."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return []
	names = set(project_member_names(user))
	if frappe.get_meta("Project").has_field("portal_project_manager"):
		names |= set(frappe.get_all("Project", filters={"portal_project_manager": user}, pluck="name"))
	return sorted(names)


def admin_department_names(user=None) -> list[str]:
	"""Departments this login is a Department Admin of (Department.portal_department_admins)."""
	user = user or frappe.session.user
	if not user or user == "Guest" or not frappe.db.table_exists(DEPARTMENT_ADMIN_DOCTYPE):
		return []
	return frappe.get_all(
		DEPARTMENT_ADMIN_DOCTYPE, filters={"user": user, "parenttype": "Department"}, pluck="parent"
	)


def scope_department_names(user=None) -> list[str]:
	"""The departments an admin or lead looks after: the ones they administer plus the
	ones they lead. Plain team members have none."""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	out = set()
	if DEPT_ADMIN_ROLE in roles:
		out |= set(admin_department_names(user))
	if TEAM_LEAD_ROLE in roles:
		out |= set(led_department_names(user))
	return sorted(out)


def department_member_users(dept_names) -> set[str]:
	"""Everyone in these departments: the assigned members, the lead and the admins."""
	dept_names = list(dept_names or [])
	if not dept_names:
		return set()
	users = set(
		frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Department",
				"reference_name": ["in", dept_names],
				"status": ["not in", ("Cancelled", "Closed")],
			},
			pluck="allocated_to",
		)
	)
	if frappe.get_meta("Department").has_field("portal_team_lead"):
		users |= set(frappe.get_all("Department", filters={"name": ["in", dept_names]}, pluck="portal_team_lead"))
	if frappe.db.table_exists(DEPARTMENT_ADMIN_DOCTYPE):
		users |= set(
			frappe.get_all(
				DEPARTMENT_ADMIN_DOCTYPE,
				filters={"parent": ["in", dept_names], "parenttype": "Department"},
				pluck="user",
			)
		)
	return {u for u in users if u}


def get_scope_project_names(user=None) -> set[str]:
	"""Projects connected to the departments this admin / lead looks after: the project
	belongs to the department (portal_team), or somebody from the department is on its
	team or is its Lead Architect."""
	depts = scope_department_names(user)
	if not depts:
		return set()
	people = department_member_users(depts)
	meta = frappe.get_meta("Project")
	out = set()
	if meta.has_field("portal_team"):
		out |= set(frappe.get_all("Project", filters={"portal_team": ["in", depts]}, pluck="name"))
	if people:
		pu = frappe.qb.DocType("Project User")
		out |= set(
			frappe.qb.from_(pu)
			.select(pu.parent)
			.distinct()
			.where((pu.user.isin(list(people))) & (pu.parenttype == "Project"))
			.run(pluck=True)
		)
		if meta.has_field("portal_project_manager"):
			out |= set(
				frappe.get_all("Project", filters={"portal_project_manager": ["in", list(people)]}, pluck="name")
			)
	return out


def get_unassigned_project_names() -> list[str]:
	"""Projects nobody is on and that belong to no team. Department Admins see them so
	someone can staff them; plain members never do."""
	p = frappe.qb.DocType("Project")
	pu = frappe.qb.DocType("Project User")
	query = (
		frappe.qb.from_(p)
		.left_join(pu)
		.on((pu.parent == p.name) & (pu.parenttype == "Project"))
		.select(p.name)
		.where(pu.name.isnull())
	)
	if frappe.get_meta("Project").has_field("portal_team"):
		query = query.where(p.portal_team.isnull() | (p.portal_team == ""))
	return query.run(pluck=True)


def assert_portal_user(user=None) -> None:
	"""Baseline gate for every whitelisted portal endpoint.

	`@frappe.whitelist()` only proves the caller has *a* session. It does not prove
	they are a portal user — a plain Website User, an Employee with no project, or a
	staff member whose portal access was revoked all still reach the endpoint. Any
	endpoint that returns portal data must call this first, even read-only lookups.
	"""
	if not user_can_use_portal(user):
		frappe.throw(_("You do not have access to the project portal."), frappe.PermissionError)


def assert_project_access(project_name: str) -> None:
	if project_name not in get_allowed_project_names():
		frappe.throw(_("No access to this project"), frappe.PermissionError)


def can_view_project_value(project_name: str, user=None, effective_portal_project_manager=None) -> bool:
	"""Whether `user` may see this project's monetary value (Dashboard "Value" column).

	A Super Admin sees every project's value. A Department Admin (and a legacy Projects
	Manager) only sees the value of the specific project(s) they are the Lead Architect
	of, not the whole portfolio.

	`effective_portal_project_manager` lets a caller pass the manager value a
	save is ABOUT to write, instead of the stale pre-save value from the DB —
	needed so that claiming an unassigned project and pricing it in the same
	update_project() call is judged against who the user is about to become,
	not who they were a moment before the save.
	"""
	user = user or frappe.session.user
	if user == "Guest":
		return False
	roles = set(frappe.get_roles(user))
	if SUPER_ADMIN_ROLE in roles:
		return True
	if roles & {DEPT_ADMIN_ROLE, LEGACY_PROJECTS_MANAGER_ROLE}:
		manager = (
			effective_portal_project_manager
			if effective_portal_project_manager is not None
			else frappe.db.get_value("Project", project_name, "portal_project_manager")
		)
		return manager == user
	return False


def get_value_visible_project_names(user=None) -> list[str]:
	"""Project names whose monetary value `user` may see — same rule as
	can_view_project_value, but for callers that need the whole list at once
	(e.g. portfolio totals, the AI chat's budget/cost answers)."""
	user = user or frappe.session.user
	if user == "Guest":
		return []
	roles = set(frappe.get_roles(user))
	if SUPER_ADMIN_ROLE in roles:
		return get_allowed_project_names(user)
	if roles & {DEPT_ADMIN_ROLE, LEGACY_PROJECTS_MANAGER_ROLE}:
		return frappe.get_all("Project", filters={"portal_project_manager": user}, pluck="name")
	return []


def project_member_names(user=None) -> list[str]:
	"""Projects this user is actually on the team of (Project User child rows).

	Distinct from get_allowed_project_names(), which is now the whole portfolio for
	internal staff. This is the narrower set that grants WRITE.
	"""
	user = user or frappe.session.user
	if user == "Guest":
		return []
	rows = frappe.db.sql(
		"SELECT DISTINCT parent FROM `tabProject User` WHERE user=%s",
		user,
	)
	return [r[0] for r in rows]


def can_manage_project(project_name: str, user=None) -> bool:
	"""Management-level action (edit, delete, team sync, sharing, folder rules, etc.).

	  * Super Admin: any project.
	  * Department Admin: any project they can see (their departments' projects).
	  * Team Lead: the projects of the teams they lead, and the ones they are on.
	  * Team Member: the projects they are on the team of, or lead.
	Client contacts manage nothing.
	"""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	# Staff FIRST. Administrator holds every role in Frappe, the client role
	# included, so testing "is client" before "is admin" locks the superuser out.
	if is_super_admin(user):
		return project_name in get_allowed_project_names(user)
	if is_customer_only(user):
		return False
	if project_name not in get_allowed_project_names(user):
		return False
	if is_dept_admin(user):
		return True
	if project_name in own_project_names(user):
		return True
	return is_team_lead(user) and project_name in get_scope_project_names(user)


def get_manageable_project_names(user=None, allowed=None) -> list[str]:
	"""can_manage_project() for a whole list at once (capabilities, the Shares page)."""
	user = user or frappe.session.user
	allowed = list(allowed) if allowed is not None else get_allowed_project_names(user)
	if is_super_admin(user) or is_dept_admin(user):
		return allowed
	if is_customer_only(user):
		return []
	mine = set(own_project_names(user))
	if is_team_lead(user):
		mine |= get_scope_project_names(user)
	return [n for n in allowed if n in mine]


def assert_manage_project(project_name: str) -> None:
	if not can_manage_project(project_name):
		frappe.throw(
			_("You can only change projects you are on the team of."),
			frappe.PermissionError,
		)


def can_manage_teams(user=None) -> bool:
	"""Team-wide actions (create a team, the pickers, User Groups): Super Admin and
	Department Admin. Changing ONE team's people is can_manage_team()."""
	return has_portal_staff_project_access(user)


def assert_manage_teams() -> None:
	if not can_manage_teams():
		frappe.throw(
			_("Only a Super Admin or a Department Admin can manage teams."),
			frappe.PermissionError,
		)


def led_department_names(user=None) -> list[str]:
	"""Departments this user is the designated portal_team_lead of."""
	user = user or frappe.session.user
	if not frappe.get_meta("Department").has_field("portal_team_lead"):
		return []
	return frappe.get_all("Department", filters={"portal_team_lead": user}, pluck="name")


def can_view_org_chart(user=None) -> bool:
	"""The organisation chart: admins to run it, Team Leads to assign people to projects."""
	user = user or frappe.session.user
	if not user or user == "Guest" or is_customer_only(user):
		return False
	return has_portal_staff_project_access(user) or is_team_lead(user)


def assert_org_chart_access() -> None:
	if not can_view_org_chart():
		frappe.throw(_("You cannot open the organisation chart."), frappe.PermissionError)


def can_manage_team(team_name: str, user=None) -> bool:
	"""Changing one team's people and roles (add, remove, lead, admins): the Super Admin,
	or the Department Admin of that department. A Team Lead assigns people to projects
	but does not change the team itself."""
	user = user or frappe.session.user
	if is_super_admin(user):
		return True
	if not is_dept_admin(user):
		return False
	return team_name in admin_department_names(user)


def assert_manage_team(team_name: str) -> None:
	if not can_manage_team(team_name):
		frappe.throw(
			_("Only a Super Admin, or this department's own Department Admin, can change this team."),
			frappe.PermissionError,
		)


def can_add_project_members(project_name: str, user=None) -> bool:
	"""Put people on a project's team: Super Admin and Department Admin for any project
	they can see; a Team Lead for the projects of their teams; the project's own Lead
	Architect for that one project."""
	user = user or frappe.session.user
	if not user or user == "Guest" or is_customer_only(user):
		return False
	if project_name not in get_allowed_project_names(user):
		return False
	if is_super_admin(user) or is_dept_admin(user) or is_team_lead(user):
		return True
	return frappe.db.get_value("Project", project_name, "portal_project_manager") == user


def can_remove_project_members(project_name: str, user=None) -> bool:
	"""Taking people OFF a project's team is for the Super Admin and the Department
	Admin only (a Team Lead and a Lead Architect can add, not remove)."""
	user = user or frappe.session.user
	if not user or user == "Guest" or is_customer_only(user):
		return False
	if not (is_super_admin(user) or is_dept_admin(user)):
		return False
	return project_name in get_allowed_project_names(user)


def can_manage_project_team(project_name: str, user=None) -> bool:
	"""Any change to a project's team (see can_add_project_members / can_remove_project_members)."""
	return can_add_project_members(project_name, user) or can_remove_project_members(project_name, user)


def assert_manage_project_team(project_name: str) -> None:
	if not can_manage_project_team(project_name):
		frappe.throw(
			_("Only a Super Admin, a Department Admin, a Team Lead or this project's Lead Architect can change its team."),
			frappe.PermissionError,
		)


def can_edit_portal_folder_template(user=None) -> bool:
	"""Company-wide subfolder template in Portal Project Settings (desk single).

	Restricted to the dedicated Auditor role (or System Manager as a fallback).
	The template controls the standard project folder structure and is treated as
	an audit/governance artifact, so non-auditor staff cannot change it."""
	user = user or frappe.session.user
	if user == "Guest":
		return False
	roles = set(frappe.get_roles(user))
	# System Manager is a super-user; bypass the portal-user gate entirely.
	if "System Manager" in roles:
		return True
	if not user_can_use_portal(user):
		return False
	if user_is_customer_portal_user(user):
		return False
	if "Auditor" in roles:
		return True
	return False


def assert_can_edit_portal_folder_template() -> None:
	if not can_edit_portal_folder_template():
		frappe.throw(
			_("You are not allowed to change the portal folder template."),
			frappe.PermissionError,
		)


def assert_can_create_project() -> None:
	if not user_can_use_portal():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if has_portal_staff_project_access():
		return
	if user_is_customer_portal_user():
		frappe.throw(_("Client Customers cannot create projects."), frappe.PermissionError)
	settings = get_portal_settings_dict()
	if settings.get("allow_any_portal_user_to_create_project"):
		return
	# Deliberately do NOT fall back to ERPNext's core "Project create" permission here —
	# the stock "Projects User" role grants that by default, which would silently let a
	# Team Member create projects from the portal even though the spec says they can't.
	# Only a Super Admin / Department Admin (above) or the explicit opt-in setting may.
	frappe.throw(_("You cannot create projects from the portal."), frappe.PermissionError)


def can_manage_customers_in_portal() -> bool:
	"""Search / create Customer and link to Project from the portal."""
	if not user_can_use_portal():
		return False
	if has_portal_staff_project_access():
		return True
	if user_is_customer_portal_user():
		return False
	try:
		if frappe.has_permission("Customer", "create", user=frappe.session.user):
			return True
	except Exception:
		pass
	for name in get_allowed_project_names():
		if can_manage_project(name):
			return True
	return False


def assert_can_manage_customers_in_portal() -> None:
	if not can_manage_customers_in_portal():
		frappe.throw(_("You cannot manage customers from the portal."), frappe.PermissionError)


def assert_customer_portal_can_upload(project_name: str) -> None:
	assert_project_access(project_name)
	if has_portal_staff_project_access():
		return
	if user_is_customer_portal_user():
		frappe.throw(_("Customer portal users cannot upload files."), frappe.PermissionError)


def kanban_fieldname() -> str:
	meta = frappe.get_meta("Project")
	return "portal_kanban_stage" if meta.has_field("portal_kanban_stage") else "status"


@frappe.whitelist()
def get_portal_workspace_settings():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return get_public_portal_settings()


_SERVER_ONLY_SETTINGS = ("frappe_drive_upload_webhook", "google_drive_upload_webhook", "bim_360_upload_webhook")


def get_public_portal_settings():
	"""Settings safe to hand to the browser. The external-upload webhook URLs are used
	only server-side (files.upload_project_file) and often embed a token, so they never
	leave the server — every signed-in user, client contacts included, reads this."""
	return {k: v for k, v in get_portal_settings_dict().items() if k not in _SERVER_ONLY_SETTINGS}


def get_portal_settings_dict():
	if not frappe.db.exists("DocType", "Portal Project Settings"):
		return {}
	doc = frappe.get_single("Portal Project Settings")
	return {
		"company_logo": doc.get("company_logo") or "",
		"company_name": doc.get("company_name") or "",
		"company_tagline": doc.get("company_tagline") or "",
		"allow_portal_demo_seed": int(doc.get("allow_portal_demo_seed") or 0),
		"allow_any_portal_user_to_create_project": int(
			doc.get("allow_any_portal_user_to_create_project") or 0
		),
		"use_frappe_drive": int(doc.get("use_frappe_drive") or 0),
		"frappe_drive_site_url": doc.get("frappe_drive_site_url") or "",
		"frappe_drive_upload_webhook": doc.get("frappe_drive_upload_webhook") or "",
		"google_drive_enabled": int(doc.get("google_drive_enabled") or 0),
		"google_drive_notes": doc.get("google_drive_notes") or "",
		"google_drive_upload_webhook": doc.get("google_drive_upload_webhook") or "",
		"bim_360_enabled": int(doc.get("bim_360_enabled") or 0),
		"bim_360_notes": doc.get("bim_360_notes") or "",
		"bim_360_upload_webhook": doc.get("bim_360_upload_webhook") or "",
		"file_access_note": doc.get("file_access_note") or "",
		"client_portal_intro": doc.get("client_portal_intro") or "",
	}


def can_reset_password_for(target: str, caller: str | None = None) -> bool:
	"""May `caller` reset `target`'s password from the portal?

	  * Super Admin: any enabled login except the built-in accounts, clients included.
	  * Department Admin: the Team Leads and Team Members of the departments they
	    administer. Never a Super Admin, another Department Admin or a client.
	  * Nobody else. Your own password is changed from Profile.
	"""
	caller = caller or frappe.session.user
	if not caller or caller == "Guest" or not target or target in ("Administrator", "Guest"):
		return False
	if target == caller:
		return False
	if is_super_admin(caller):
		return True
	if not is_dept_admin(caller):
		return False
	if is_super_admin(target) or is_dept_admin(target) or is_customer_only(target):
		return False
	depts = admin_department_names(caller)
	return bool(depts) and target in department_member_users(depts)


def sync_portal_role_markers(user: str) -> None:
	"""Make a login's Department Admin / Team Lead roles match the Department data.

	The roles are markers; the Department rows decide the scope. Anyone who administers
	or leads a department also needs the base Team Member role, or the portal would not
	let them in at all."""
	if not user or user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		return
	wants = {
		DEPT_ADMIN_ROLE: bool(admin_department_names(user)),
		TEAM_LEAD_ROLE: bool(led_department_names(user)),
	}
	ensure_portal_roles()
	doc = frappe.get_doc("User", user)
	have = {r.role for r in doc.roles}
	changed = False
	for role, wanted in wants.items():
		if wanted and role not in have:
			doc.append("roles", {"role": role})
			changed = True
		elif not wanted and role in have:
			for row in list(doc.roles):
				if row.role == role:
					doc.remove(row)
			changed = True
	if any(wants.values()) and TEAM_MEMBER_ROLE not in have and PORTAL_CUSTOMER_ROLE not in have:
		doc.append("roles", {"role": TEAM_MEMBER_ROLE})
		changed = True
	if changed:
		doc.flags.ignore_permissions = True
		doc.save()


def sync_department_role_markers(doc, method=None):
	"""doc_events Department.on_update: whoever is (or just stopped being) this
	department's Team Lead or Department Admin gets (or loses) the matching role, no
	matter whether the change was made in the portal or in Desk."""
	users = set()
	if doc.get("portal_team_lead"):
		users.add(doc.portal_team_lead)
	users |= {r.user for r in (doc.get("portal_department_admins") or []) if r.user}
	before = doc.get_doc_before_save()
	if before:
		if before.get("portal_team_lead"):
			users.add(before.portal_team_lead)
		users |= {r.user for r in (before.get("portal_department_admins") or []) if r.user}
	for user in users:
		sync_portal_role_markers(user)


def project_has_permission(doc, ptype=None, user=None, debug=False):
	"""Controller permission hook for the Project doctype (registered in hooks.py).

	Registering this on "File" instead does NOT work: File.is_downloadable() calls the
	file.py module's has_permission() function by direct reference, not through the
	hook-dispatching frappe.has_permission(), so a File-scoped app hook is silently
	never consulted for that path. Project's own `ref_doc.has_permission("read")` call
	(used below by File's fallback), however, goes through the full dispatcher — so the
	hook belongs on Project.

	Frappe core's own File.has_permission() falls back to the attached document's
	permission when a file has no more specific grant — so for a Project-attached
	file, it delegates to Project's permission. ERPNext's stock role permissions give
	"Projects User" blanket read access to every Project, with no per-project scoping.
	That means any portal-role holder who knows (or guesses) a private file's raw
	/private/files/<...> URL can read it directly, completely bypassing this app's own
	project scoping (get_allowed_project_names / assert_project_access) — even after
	being removed from a project's team, or for a project they were never on.

	A controller has_permission hook can only DENY, never grant, permission beyond what
	the standard role-based check already allows (see
	frappe.permissions.has_controller_permissions), so this only tightens things. It
	only applies to users who actually hold a portal-relevant role (Team Member, Team Lead,
	Department Admin or Client Customer) — a Super Admin already gets every project via
	get_allowed_project_names() and is never restricted here, and any other Desk user
	with no portal role at all (HR, Accounts, etc., who may reference Project links for
	unrelated reasons) is left completely untouched.
	"""
	if ptype not in ("read", "select"):
		return None
	user = user or frappe.session.user
	if user in ("Administrator", "Guest"):
		return None
	if is_super_admin(user):
		return None
	roles = set(frappe.get_roles(user))
	if not (
		roles & {TEAM_MEMBER_ROLE, DEPT_ADMIN_ROLE, TEAM_LEAD_ROLE, LEGACY_PROJECTS_MANAGER_ROLE}
		or PORTAL_CUSTOMER_ROLE in roles
	):
		return None
	if doc.name in get_allowed_project_names(user):
		return None
	return False
