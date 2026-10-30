from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, cstr

# The portal's six-level hierarchy (Batch C) and the Frappe data behind each level:
#   Super Admin             System Manager (the label the portal has always used for it)
#   Department Admin        "Department Admin"       + Department.portal_department_admins rows
#   Department Coordinator  "Department Coordinator" + Department.portal_department_coordinators rows
#   Team Manager            "Team Manager"           + Department.portal_team_lead (was "Team Lead")
#   Project Lead            Project.portal_project_manager (per project; was "Lead Architect")
#   Project Architect       "Projects User" (was "Team Member")
#   Client Customer         "Client Customer" (was "Portal Customer") + Portal User Customer rows
# Departments sit above teams in ERPNext's own Department tree: Department.portal_unit is
# "Department" or "Team" (blank + a Portal Office = a legacy team). A department marked
# portal_pending is recorded only: every reader below ignores it and its teams.
# The marker roles are kept in sync with the Department data by
# sync_department_role_markers (a Department doc_event), so a change made anywhere,
# portal or Desk, ends up the same.
SUPER_ADMIN_ROLE = "System Manager"
DEPT_ADMIN_ROLE = "Department Admin"
DEPT_COORDINATOR_ROLE = "Department Coordinator"
TEAM_MANAGER_ROLE = "Team Manager"
TEAM_LEAD_ROLE = TEAM_MANAGER_ROLE  # old name, kept for callers and tests
LEGACY_TEAM_LEAD_ROLE = "Team Lead"
TEAM_MEMBER_ROLE = "Projects User"
LEGACY_PROJECTS_MANAGER_ROLE = "Projects Manager"
PORTAL_ROLES = frozenset(
	{
		SUPER_ADMIN_ROLE,
		LEGACY_PROJECTS_MANAGER_ROLE,
		TEAM_MEMBER_ROLE,
		DEPT_ADMIN_ROLE,
		DEPT_COORDINATOR_ROLE,
		TEAM_MANAGER_ROLE,
	}
)
PORTAL_CUSTOMER_ROLE = "Client Customer"
LEGACY_PORTAL_CUSTOMER_ROLE = "Portal Customer"
PORTAL_HOME = "/portal-app"
DEPARTMENT_ADMIN_DOCTYPE = "Portal Department Admin"
DEPARTMENT_COORDINATOR_DOCTYPE = "Portal Department Coordinator"
PROJECT_LINK_DOCTYPE = "Portal Project Link"
LINK_TYPES = ("T Server", "Autodesk Server", "ERP")

# Role keys are stable (frontend, tests, open tabs); only the labels changed.
ROLE_LABELS = {
	"super_admin": "Super Admin",
	"department_admin": "Department Admin",
	"department_coordinator": "Department Coordinator",
	"team_lead": "Team Manager",
	"project_lead": "Project Lead",
	"team_member": "Project Architect",
	"client_customer": "Client Customer",
}
# New names accepted on input for the two renamed keys.
ROLE_KEY_ALIASES = {"team_manager": "team_lead", "project_architect": "team_member"}


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
	"""Create the Department Admin, Department Coordinator and Team Manager marker roles
	(Desk users, internal). Never the old "Team Lead": patches.rename_team_lead_role renames it."""
	created = False
	for role in (DEPT_ADMIN_ROLE, DEPT_COORDINATOR_ROLE, TEAM_MANAGER_ROLE):
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
	"""Team Manager marker role (the old Team Lead)."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	return TEAM_MANAGER_ROLE in frappe.get_roles(user)


is_team_manager = is_team_lead


def is_dept_coordinator(user=None) -> bool:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	return DEPT_COORDINATOR_ROLE in frappe.get_roles(user)


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
	"""The highest portal role key of a login: super_admin, department_admin,
	department_coordinator, client_customer, team_lead (Team Manager), project_lead or
	team_member (None if the login has no portal role at all)."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None
	if is_super_admin(user):
		return "super_admin"
	roles = set(frappe.get_roles(user))
	if DEPT_ADMIN_ROLE in roles:
		return "department_admin"
	if DEPT_COORDINATOR_ROLE in roles:
		return "department_coordinator"
	if PORTAL_CUSTOMER_ROLE in roles:
		return "client_customer"
	if TEAM_MANAGER_ROLE in roles:
		return "team_lead"
	if frappe.get_meta("Project").has_field("portal_project_manager") and frappe.db.exists(
		"Project", {"portal_project_manager": user}
	):
		return "project_lead"
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

	  Super Admin             the whole portfolio.
	  Department Admin        the projects of their department's teams (portal_team, or a
	                          team person on the team or as Project Lead), plus their own.
	                          A legacy team-level admin row also sees the projects that
	                          belong to no team yet (somebody has to triage them).
	  Department Coordinator  the same for the departments they coordinate, plus the
	                          unassigned projects (they allocate projects to teams).
	  Team Manager            the same for the teams they manage, plus their own.
	  Project Lead / Architect  only the projects they lead or are on the team of.
	  Client Customer         only the projects of their customers.
	A pending designation counts as if it did not exist.
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
	if roles & {DEPT_ADMIN_ROLE, DEPT_COORDINATOR_ROLE, TEAM_MANAGER_ROLE}:
		names |= get_scope_project_names(user)
	if sees_unassigned_projects(user):
		names |= set(get_unassigned_project_names())
	return sorted(names)


def own_project_names(user=None) -> list[str]:
	"""Projects this login is on the team of, or is the Project Lead of."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return []
	names = set(project_member_names(user))
	if frappe.get_meta("Project").has_field("portal_project_manager"):
		names |= set(frappe.get_all("Project", filters={"portal_project_manager": user}, pluck="name"))
	return sorted(names)


# ---------------------------------------------------------------------------------------
# Unit model: Department units above teams (ERPNext Department tree + portal_unit)
# ---------------------------------------------------------------------------------------
def _has_unit_field() -> bool:
	return frappe.get_meta("Department").has_field("portal_unit")


def pending_unit_names() -> set:
	"""Units that are not active yet: every Department with portal_pending set, and
	everything under it (a team under a pending department is pending)."""
	if not frappe.get_meta("Department").has_field("portal_pending"):
		return set()
	out = set()
	for name in frappe.get_all("Department", filters={"portal_pending": 1}, pluck="name"):
		out.add(name)
		out |= set(frappe.db.get_descendants("Department", name))
	return out


def portal_team_names(include_pending=False) -> list:
	"""The departments the portal calls teams: portal_unit "Team", or (legacy) a blank
	portal_unit with a Portal Office. Wherever they sit in the tree. Pending teams are left
	out unless asked."""
	meta = frappe.get_meta("Department")
	if not meta.has_field("portal_office"):
		return []
	if not meta.has_field("portal_unit"):
		# Not migrated yet: the old rule (direct children of "All Departments" with an office).
		return frappe.get_all(
			"Department", filters={"parent_department": "All Departments", "portal_office": ["!=", ""]}, pluck="name"
		)
	d = frappe.qb.DocType("Department")
	blank_unit = d.portal_unit.isnull() | (d.portal_unit == "")
	has_office = d.portal_office.isnotnull() & (d.portal_office != "")
	names = (
		frappe.qb.from_(d).select(d.name).where((d.portal_unit == "Team") | (blank_unit & has_office)).run(pluck=True)
	)
	if include_pending:
		return list(names)
	pending = pending_unit_names()
	return [n for n in names if n not in pending]


def portal_department_names() -> list[str]:
	"""The teams (same meaning as before Batch C; every caller keeps working)."""
	return portal_team_names()


def portal_unit_department_names(include_pending=False) -> list:
	"""The Department units (portal_unit "Department"), the level above the teams."""
	if not _has_unit_field():
		return []
	names = frappe.get_all("Department", filters={"portal_unit": "Department"}, pluck="name")
	if include_pending:
		return names
	pending = pending_unit_names()
	return [n for n in names if n not in pending]


def teams_of_unit(name, include_pending=False) -> list:
	"""The teams a unit stands for: a team is itself, a Department unit is the teams under
	it, anything else none."""
	if not name:
		return []
	teams = portal_team_names(include_pending=include_pending)
	if name in teams:
		return [name]
	if not _has_unit_field() or frappe.db.get_value("Department", name, "portal_unit") != "Department":
		return []
	under = set(frappe.db.get_descendants("Department", name))
	return [t for t in teams if t in under]


def team_department(team):
	"""The Department unit a team belongs to: the nearest ancestor with portal_unit
	"Department" (at most five levels up), or None."""
	if not team or not _has_unit_field():
		return None
	current = team
	for _hop in range(5):
		parent = frappe.db.get_value("Department", current, "parent_department")
		if not parent:
			return None
		if frappe.db.get_value("Department", parent, "portal_unit") == "Department":
			return parent
		current = parent
	return None


# ---------------------------------------------------------------------------------------
# Designations (who holds what, where)
# ---------------------------------------------------------------------------------------
def admin_department_names(user=None, include_pending=False) -> list[str]:
	"""Units this login is a Department Admin of (Department.portal_department_admins):
	department-level rows and legacy team-level rows. Pending units are left out."""
	user = user or frappe.session.user
	if not user or user == "Guest" or not frappe.db.table_exists(DEPARTMENT_ADMIN_DOCTYPE):
		return []
	names = frappe.get_all(
		DEPARTMENT_ADMIN_DOCTYPE, filters={"user": user, "parenttype": "Department"}, pluck="parent"
	)
	names = list(dict.fromkeys(names))
	if include_pending:
		return names
	pending = pending_unit_names()
	return [n for n in names if n not in pending]


def coordinator_department_names(user=None, include_pending=False) -> list[str]:
	"""Units this login is a Department Coordinator of. Pending units are left out."""
	user = user or frappe.session.user
	if not user or user == "Guest" or not frappe.db.table_exists(DEPARTMENT_COORDINATOR_DOCTYPE):
		return []
	names = frappe.get_all(
		DEPARTMENT_COORDINATOR_DOCTYPE, filters={"user": user, "parenttype": "Department"}, pluck="parent"
	)
	names = list(dict.fromkeys(names))
	if include_pending:
		return names
	pending = pending_unit_names()
	return [n for n in names if n not in pending]


def scope_department_names(user=None) -> list[str]:
	"""The TEAMS an admin, coordinator or Team Manager looks after (name kept so callers
	keep working): the teams of the units they administer or coordinate, plus the teams
	they manage. Plain Project Architects have none."""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	out = set()
	if DEPT_ADMIN_ROLE in roles:
		for unit in admin_department_names(user):
			out |= set(teams_of_unit(unit))
	if DEPT_COORDINATOR_ROLE in roles:
		for unit in coordinator_department_names(user):
			out |= set(teams_of_unit(unit))
	if TEAM_MANAGER_ROLE in roles:
		out |= set(led_department_names(user))
	return sorted(out)


def management_unit_names(user=None) -> list[str]:
	"""The units (departments and legacy teams) this login administers or coordinates: the
	scope of the Org Chart, the Teams page and "people in my department"."""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	out = []
	if DEPT_ADMIN_ROLE in roles:
		out += admin_department_names(user)
	if DEPT_COORDINATOR_ROLE in roles:
		out += coordinator_department_names(user)
	return list(dict.fromkeys(out))


def sees_unassigned_projects(user=None) -> bool:
	"""Who sees the projects that belong to no team: a Super Admin; a Department
	Coordinator of an active department with at least one team (they allocate projects);
	a Department Admin only through a legacy team-level row. A department-level
	Department Admin does not."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	if is_super_admin(user):
		return True
	roles = set(frappe.get_roles(user))
	if DEPT_COORDINATOR_ROLE in roles and any(teams_of_unit(u) for u in coordinator_department_names(user)):
		return True
	if DEPT_ADMIN_ROLE in roles:
		teams = set(portal_team_names())
		if any(u in teams for u in admin_department_names(user)):
			return True
	return False


def _team_people_users(teams) -> set[str]:
	"""Everyone on these TEAMS: the assigned members (open ToDo), the Team Manager and the
	team's own admin rows. Never department-level admins or coordinators."""
	teams = list(teams or [])
	if not teams:
		return set()
	users = set(
		frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Department",
				"reference_name": ["in", teams],
				"status": ["not in", ("Cancelled", "Closed")],
			},
			pluck="allocated_to",
		)
	)
	if frappe.get_meta("Department").has_field("portal_team_lead"):
		users |= set(frappe.get_all("Department", filters={"name": ["in", teams]}, pluck="portal_team_lead"))
	if frappe.db.table_exists(DEPARTMENT_ADMIN_DOCTYPE):
		users |= set(
			frappe.get_all(
				DEPARTMENT_ADMIN_DOCTYPE,
				filters={"parent": ["in", teams], "parenttype": "Department"},
				pluck="user",
			)
		)
	return {u for u in users if u}


def department_member_users(dept_names) -> set[str]:
	"""Everyone in these units: each unit is expanded to its teams (teams_of_unit), and
	the open assignments, Team Managers, admin rows and coordinator rows of the units and
	their teams all count. Used for "people in my department" (role changes, password
	reset, Org Chart)."""
	units = list(dept_names or [])
	if not units:
		return set()
	everything = set(units)
	for unit in units:
		everything |= set(teams_of_unit(unit))
	everything = list(everything)
	users = _team_people_users(everything)
	if frappe.db.table_exists(DEPARTMENT_COORDINATOR_DOCTYPE):
		users |= set(
			frappe.get_all(
				DEPARTMENT_COORDINATOR_DOCTYPE,
				filters={"parent": ["in", everything], "parenttype": "Department"},
				pluck="user",
			)
		)
	return {u for u in users if u}


def unit_assigned_users(unit) -> set[str]:
	"""People ASSIGNED to a unit or one of its teams (open ToDo, Team Managers), without
	the admin / coordinator rows: "is this person already in the department?"."""
	units = [unit, *teams_of_unit(unit, include_pending=True)]
	users = set(
		frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Department",
				"reference_name": ["in", units],
				"status": ["not in", ("Cancelled", "Closed")],
			},
			pluck="allocated_to",
		)
	)
	if frappe.get_meta("Department").has_field("portal_team_lead"):
		users |= set(frappe.get_all("Department", filters={"name": ["in", units]}, pluck="portal_team_lead"))
	return {u for u in users if u}


def _projects_tied_to_departments(depts) -> set[str]:
	"""Projects that belong to one of these teams: the project's portal_team is one of
	them, or somebody from the team is on its team or is its Project Lead."""
	depts = list(depts or [])
	if not depts:
		return set()
	people = _team_people_users(depts)
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


def get_scope_project_names(user=None) -> set[str]:
	"""Projects connected to the teams this admin / coordinator / Team Manager looks
	after: the project belongs to the team (portal_team), or somebody from the team is on
	its team or is its Project Lead."""
	return _projects_tied_to_departments(scope_department_names(user))


def get_unassigned_project_names() -> list[str]:
	"""Projects that belong to no team at all: no portal_team, and nobody from any active
	team is on the team or is the Project Lead. Super Admins, Department Coordinators and
	legacy team-level Department Admins see them so somebody can put them under a team
	(Project page, Portal Team); nobody else does."""
	tied = _projects_tied_to_departments(portal_team_names())
	return [name for name in frappe.get_all("Project", pluck="name") if name not in tied]


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
	  * Department Admin / Department Coordinator: any project they can see.
	  * Team Manager: the projects of the teams they manage, and the ones they are on.
	  * Project Lead / Architect: the projects they are on the team of, or lead.
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
	if is_dept_admin(user) or is_dept_coordinator(user):
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
	if is_dept_coordinator(user):
		return allowed
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


def can_manage_project_records(project_name: str, user=None) -> bool:
	"""can_manage_project() without the Department Coordinator grant: Contracts (list,
	upload, delete, the contracts zip) and deleting the project. A Coordinator gets
	explicit rights only (spec Q7), so on a project that is not their own (an unassigned
	one, say) they keep the visibility but not these."""
	user = user or frappe.session.user
	if not can_manage_project(project_name, user):
		return False
	if has_portal_staff_project_access(user) or not is_dept_coordinator(user):
		return True
	if project_name in own_project_names(user):
		return True
	return is_team_lead(user) and project_name in get_scope_project_names(user)


def assert_manage_project_records(project_name: str) -> None:
	if not can_manage_project_records(project_name):
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


def led_department_names(user=None, include_pending=False) -> list[str]:
	"""Teams this user is the Team Manager of (Department.portal_team_lead). Pending teams
	are left out."""
	user = user or frappe.session.user
	if not frappe.get_meta("Department").has_field("portal_team_lead"):
		return []
	names = frappe.get_all("Department", filters={"portal_team_lead": user}, pluck="name")
	if include_pending:
		return names
	pending = pending_unit_names()
	return [n for n in names if n not in pending]


managed_team_names = led_department_names


def can_view_org_chart(user=None) -> bool:
	"""The organisation chart: admins to run it, Department Coordinators and Team Managers
	to assign people to projects."""
	user = user or frappe.session.user
	if not user or user == "Guest" or is_customer_only(user):
		return False
	return has_portal_staff_project_access(user) or is_dept_coordinator(user) or is_team_lead(user)


def assert_org_chart_access() -> None:
	if not can_view_org_chart():
		frappe.throw(_("You cannot open the organisation chart."), frappe.PermissionError)


def can_manage_team(team_name: str, user=None) -> bool:
	"""Changing one team's people and roles (add, remove, manager, admins): the Super
	Admin, or a Department Admin of that team or of its department. A Department
	Coordinator or Team Manager assigns people to projects but does not change the team."""
	user = user or frappe.session.user
	if is_super_admin(user):
		return True
	if not is_dept_admin(user):
		return False
	units = set(admin_department_names(user))
	if not units:
		return False
	return team_name in units or team_department(team_name) in units


def assert_manage_team(team_name: str) -> None:
	if not can_manage_team(team_name):
		frappe.throw(
			_("Only a Super Admin, or this department's own Department Admin, can change this team."),
			frappe.PermissionError,
		)


def can_add_project_members(project_name: str, user=None) -> bool:
	"""Put people on a project's team: Super Admin, Department Admin and Department
	Coordinator for any project they can see; a Team Manager for the projects of their
	teams; the project's own Project Lead for that one project."""
	user = user or frappe.session.user
	if not user or user == "Guest" or is_customer_only(user):
		return False
	if project_name not in get_allowed_project_names(user):
		return False
	if is_super_admin(user) or is_dept_admin(user) or is_dept_coordinator(user) or is_team_lead(user):
		return True
	return frappe.db.get_value("Project", project_name, "portal_project_manager") == user


def can_remove_project_members(project_name: str, user=None) -> bool:
	"""Taking people OFF a project's team is for the Super Admin, the Department Admin and
	the Department Coordinator only (a Team Manager and a Project Lead can add, not remove)."""
	user = user or frappe.session.user
	if not user or user == "Guest" or is_customer_only(user):
		return False
	if not (is_super_admin(user) or is_dept_admin(user) or is_dept_coordinator(user)):
		return False
	return project_name in get_allowed_project_names(user)


def can_manage_project_team(project_name: str, user=None) -> bool:
	"""Any change to a project's team (see can_add_project_members / can_remove_project_members)."""
	return can_add_project_members(project_name, user) or can_remove_project_members(project_name, user)


def assert_manage_project_team(project_name: str) -> None:
	if not can_manage_project_team(project_name):
		frappe.throw(
			_(
				"Only a Super Admin, a Department Admin, a Department Coordinator, a Team Manager or this project's Project Lead can change its team."
			),
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
	  * Department Admin: the people of the units they administer (their teams' Team
	    Managers and Project Architects, Department Coordinators). Never a Super Admin,
	    another Department Admin or a client.
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
	"""Make a login's Department Admin / Department Coordinator / Team Manager roles match
	the Department data (pending units grant nothing).

	The roles are markers; the Department rows decide the scope. Anyone who administers,
	coordinates or manages a unit also needs the base Projects User role, or the portal
	would not let them in at all. A stray legacy "Team Lead" row (the rename patch did not
	run) is dropped. System Manager is never touched."""
	if not user or user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		return
	wants = {
		DEPT_ADMIN_ROLE: bool(admin_department_names(user)),
		DEPT_COORDINATOR_ROLE: bool(coordinator_department_names(user)),
		TEAM_MANAGER_ROLE: bool(led_department_names(user)),
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
	if LEGACY_TEAM_LEAD_ROLE in have:
		for row in list(doc.roles):
			if row.role == LEGACY_TEAM_LEAD_ROLE:
				doc.remove(row)
		changed = True
	if any(wants.values()) and TEAM_MEMBER_ROLE not in have and PORTAL_CUSTOMER_ROLE not in have:
		doc.append("roles", {"role": TEAM_MEMBER_ROLE})
		changed = True
	if changed:
		doc.flags.ignore_permissions = True
		doc.save()


def _unit_people(doc) -> set:
	"""Everyone named on a Department doc: Team Manager, admin rows, coordinator rows."""
	if not doc:
		return set()
	users = set()
	if doc.get("portal_team_lead"):
		users.add(doc.portal_team_lead)
	users |= {r.user for r in (doc.get("portal_department_admins") or []) if r.user}
	users |= {r.user for r in (doc.get("portal_department_coordinators") or []) if r.user}
	return users


def sync_department_role_markers(doc, method=None):
	"""doc_events Department.on_update: whoever is (or just stopped being) this unit's
	Team Manager, Department Admin or Department Coordinator gets (or loses) the matching
	role, no matter whether the change was made in the portal or in Desk. When the unit is
	activated / made pending or moved in the tree, everyone named on the units under it is
	synced too, so activating a department grants the roles in one save."""
	users = _unit_people(doc)
	before = doc.get_doc_before_save()
	users |= _unit_people(before)
	moved = before is not None and (
		cint(before.get("portal_pending")) != cint(doc.get("portal_pending"))
		or (before.get("parent_department") or None) != (doc.get("parent_department") or None)
	)
	if moved:
		under = frappe.db.get_descendants("Department", doc.name)
		if under:
			if frappe.get_meta("Department").has_field("portal_team_lead"):
				users |= set(frappe.get_all("Department", filters={"name": ["in", under]}, pluck="portal_team_lead"))
			for child in (DEPARTMENT_ADMIN_DOCTYPE, DEPARTMENT_COORDINATOR_DOCTYPE):
				if frappe.db.table_exists(child):
					users |= set(
						frappe.get_all(
							child, filters={"parent": ["in", under], "parenttype": "Department"}, pluck="user"
						)
					)
	for user in users:
		if user:
			sync_portal_role_markers(user)


# ---------------------------------------------------------------------------------------
# Designations of one person (Profile, Org Chart, role changes)
# ---------------------------------------------------------------------------------------
def _designation(role, unit=None, unit_label=None, pending=False, **extra) -> dict:
	return {
		"role": role,
		"label": ROLE_LABELS.get(role, role),
		"unit": unit,
		"unit_label": unit_label,
		"pending": bool(pending),
		**extra,
	}


def get_portal_designations(user=None) -> list[dict]:
	"""Every designation a login holds, highest first: super_admin; each Department Admin
	row; each Department Coordinator row; each team they manage; project_lead (with the
	number of projects they lead); team_member. Rows on pending units are included with
	`pending: True` (recorded only, they grant nothing)."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return []
	if user == "Administrator":
		return [_designation("super_admin")]
	out = []
	if is_super_admin(user):
		out.append(_designation("super_admin"))
	pending = pending_unit_names()
	admin_units = admin_department_names(user, include_pending=True)
	coord_units = coordinator_department_names(user, include_pending=True)
	led = led_department_names(user, include_pending=True)
	labels = {}
	every = list({*admin_units, *coord_units, *led})
	if every:
		labels = dict(frappe.get_all("Department", filters={"name": ["in", every]}, fields=["name", "department_name"], as_list=True))
	for role, units in (("department_admin", admin_units), ("department_coordinator", coord_units), ("team_lead", led)):
		for unit in units:
			out.append(_designation(role, unit, labels.get(unit) or unit, unit in pending))
	if frappe.get_meta("Project").has_field("portal_project_manager"):
		count = frappe.db.count("Project", {"portal_project_manager": user})
		if count:
			out.append(_designation("project_lead", count=count))
	if is_customer_only(user):
		out.append(_designation("client_customer"))
	elif TEAM_MEMBER_ROLE in frappe.get_roles(user) or frappe.db.exists(
		"Project User", {"user": user, "parenttype": "Project"}
	):
		out.append(_designation("team_member"))
	return out


# Roles that can be SET from the role changer (portal_admin.change_user_role).
# project_lead is per project; client_customer is a different kind of login.
SETTABLE_ROLE_KEYS = ("super_admin", "department_admin", "department_coordinator", "team_lead", "team_member")


def normalize_role_key(role) -> str:
	role = cstr(role).strip()
	return ROLE_KEY_ALIASES.get(role, role)


def role_change_scope(caller=None) -> dict:
	"""What a caller may do in the role changer, computed once: Super Admin (everything),
	Department Admin (units U and their people), or nothing."""
	caller = caller or frappe.session.user
	if is_super_admin(caller):
		return {"kind": "super_admin"}
	if not is_dept_admin(caller) or is_customer_only(caller):
		return {"kind": None}
	units = admin_department_names(caller)
	if not units:
		return {"kind": None}
	dept_units = set(portal_unit_department_names())
	teams = set()
	for unit in units:
		teams |= set(teams_of_unit(unit))
	return {
		"kind": "department_admin",
		"units": units,
		"departments": [u for u in units if u in dept_units],
		"teams": sorted(teams),
		"people": department_member_users(units),
		"admins": set(frappe.get_all(DEPARTMENT_ADMIN_DOCTYPE, filters={"parenttype": "Department"}, pluck="user"))
		if frappe.db.table_exists(DEPARTMENT_ADMIN_DOCTYPE)
		else set(),
	}


def assignable_roles_for(caller, target, scope=None) -> dict:
	"""{role key: [units]} that `caller` may give `target` (an empty dict: none at all).

	  Super Admin       any enabled staff login (incl. themselves): every settable role,
	                    any unit, pending ones included.
	  Department Admin  people of their own units (incl. themselves), never a Super Admin
	                    or another Department Admin: Department Coordinator of one of their
	                    departments (not themselves), Team Manager of one of their teams,
	                    Project Architect.
	  anyone else       nothing.
	"""
	caller = caller or frappe.session.user
	target = cstr(target).strip()
	if not target or target in ("Administrator", "Guest") or not frappe.db.exists("User", target):
		return {}
	if not frappe.db.get_value("User", target, "enabled") or is_customer_only(target):
		return {}
	scope = scope or role_change_scope(caller)
	if scope["kind"] == "super_admin":
		departments = portal_unit_department_names(include_pending=True)
		return {
			"super_admin": [],
			"department_admin": departments,
			"department_coordinator": departments,
			"team_lead": portal_team_names(include_pending=True),
			"team_member": [],
		}
	if scope["kind"] != "department_admin":
		return {}
	if target != caller:
		if target not in scope["people"] or is_super_admin(target) or target in scope["admins"]:
			return {}
	roles = {
		"department_coordinator": list(scope["departments"]),
		"team_lead": list(scope["teams"]),
		"team_member": [],
	}
	if target == caller:
		# Self-change goes downwards only (spec 7): a Coordinator sees unassigned projects
		# (sees_unassigned_projects), which a Department Admin must not grant themselves.
		roles.pop("department_coordinator")
	return roles


# ---------------------------------------------------------------------------------------
# Project links (R3)
# ---------------------------------------------------------------------------------------
def can_manage_project_links(project_name: str, user=None) -> bool:
	"""Who manages a project's T Server / Autodesk Server / ERP links: a Super Admin; or,
	for a project they can see whose team belongs to department D, an active Department
	Coordinator or Department Admin of D, or a legacy admin row on the team itself. A
	project with no team: Super Admin only."""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return False
	if is_super_admin(user):
		return True
	if is_customer_only(user) or not (is_dept_admin(user) or is_dept_coordinator(user)):
		return False
	if not frappe.get_meta("Project").has_field("portal_team"):
		return False
	team = frappe.db.get_value("Project", project_name, "portal_team")
	if not team or project_name not in get_allowed_project_names(user):
		return False
	admin_units = set(admin_department_names(user)) if is_dept_admin(user) else set()
	coord_units = set(coordinator_department_names(user)) if is_dept_coordinator(user) else set()
	if team in admin_units:
		return True
	dept = team_department(team)
	return bool(dept) and (dept in admin_units or dept in coord_units)


project_link_managers_can = can_manage_project_links


def can_open_project_link(link_row, user=None) -> bool:
	"""May `user` open (receive the path / URL of) this Portal Project Link row: a link
	manager, or someone on its allowed list who can still see the project. Never a client."""
	user = user or frappe.session.user
	if not user or user == "Guest" or not link_row:
		return False
	if is_customer_only(user):
		return False
	project = link_row.get("project")
	if can_manage_project_links(project, user):
		return True
	allowed = {r.get("user") if isinstance(r, dict) else r.user for r in (link_row.get("allowed_users") or [])}
	return user in allowed and project in get_allowed_project_names(user)


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
		roles & {TEAM_MEMBER_ROLE, DEPT_ADMIN_ROLE, DEPT_COORDINATOR_ROLE, TEAM_MANAGER_ROLE, LEGACY_PROJECTS_MANAGER_ROLE}
		or PORTAL_CUSTOMER_ROLE in roles
	):
		return None
	if doc.name in get_allowed_project_names(user):
		return None
	return False
