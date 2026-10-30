import json

import frappe
from frappe import _
from frappe.utils import cint, cstr

from portal_app.api import helper


def _can_create_users() -> bool:
	if frappe.session.user == "Guest":
		return False
	if helper.is_super_admin():
		return True
	try:
		return bool(frappe.has_permission("User", "create", user=frappe.session.user))
	except Exception:
		return False


def _can_run_seed_via_portal() -> bool:
	"""Super Admin PLUS an explicit opt-in on this site.

	Seeding creates real, enabled login accounts and real Projects/Tasks/Files. On a
	production site that must never be one misclick away, so it additionally requires
	developer_mode or the "Allow portal demo seed" switch in Portal Project Settings —
	which is what the error message shown to users has always claimed.
	"""
	if frappe.session.user == "Guest":
		return False
	if not helper.is_super_admin():
		return False
	if cint(frappe.conf.get("developer_mode")):
		return True
	return bool(helper.get_portal_settings_dict().get("allow_portal_demo_seed"))


# The portal roles a login can be created with (see helper.ROLE_LABELS). project_lead
# is set per project, never at creation.
ROLE_KEYS = (
	"super_admin",
	"department_admin",
	"department_coordinator",
	"team_lead",
	"team_member",
	"client_customer",
)
SUPER_ADMIN_ROLE = helper.SUPER_ADMIN_ROLE


@frappe.whitelist()
def get_portal_admin_capabilities():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	# Imported here: submissions imports files, keep this module's import graph flat.
	from portal_app.api import submissions

	can_manage_teams = helper.can_manage_teams()
	return {
		"can_create_users": _can_create_users(),
		"can_run_demo_seed": _can_run_seed_via_portal(),
		"can_edit_folder_template": helper.can_edit_portal_folder_template(),
		# Only an existing Super Admin may hand that role to someone else — same
		# self-perpetuating-privilege guard as elsewhere in this app.
		"can_grant_super_admin": helper.is_super_admin(),
		"can_assign_team_roles": can_manage_teams,
		"can_assign_team_manager": can_manage_teams,
		"can_reset_passwords": helper.has_portal_staff_project_access(),
		# Change an existing user's role (change_user_role): Super Admin, Department Admin.
		"can_change_roles": bool(helper.role_change_scope().get("kind")),
		"can_manage_submission_types": submissions._can_manage_submission_types(),
		"portal_role": helper.get_portal_role(),
	}


@frappe.whitelist()
def list_teams_for_picker():
	"""Minimal {name, department_name} list for the team pickers (create user, roles)."""
	helper.assert_manage_teams()
	team_names = helper.portal_team_names()
	if not team_names:
		return []
	return frappe.get_all(
		"Department",
		filters={"name": ["in", team_names]},
		fields=["name", "department_name"],
		order_by="department_name asc",
	)


def _legacy_role_key(roles_json, is_super_admin, team_lead_of) -> str:
	"""Map the arguments an older, still-open browser tab sends (roles_json, is_super_admin,
	team_lead_of) to a role key, so a tab opened before this release does not break."""
	roles = []
	if roles_json:
		try:
			parsed = json.loads(roles_json)
		except Exception:
			frappe.throw(_("Invalid roles"))
		if not isinstance(parsed, list):
			frappe.throw(_("Invalid roles"))
		roles = [cstr(r).strip() for r in parsed if r]
	if cint(is_super_admin):
		return "super_admin"
	if helper.PORTAL_CUSTOMER_ROLE in roles or helper.LEGACY_PORTAL_CUSTOMER_ROLE in roles:
		return "client_customer"
	if team_lead_of:
		return "team_lead"
	if helper.LEGACY_PROJECTS_MANAGER_ROLE in roles:
		return "department_admin"
	return "team_member"


@frappe.whitelist(methods=["POST"])
def create_portal_user(
	email,
	full_name,
	password=None,
	role=None,
	send_welcome_email=0,
	portal_linked_customer=None,
	team=None,
	teams_json=None,
	roles_json=None,
	is_super_admin=0,
	team_lead_of=None,
):
	"""Create a login with one of the portal roles.

	  super_admin             the whole portal (Frappe System Manager)
	  department_admin        looks after one or more departments (`teams_json`)
	  department_coordinator  coordinates one or more departments (`teams_json`)
	  team_lead               Team Manager of `team` (team_manager accepted too)
	  team_member             a Project Architect, optionally on `team` (project_architect too)
	  client_customer         an external client contact of `portal_linked_customer`
	"""
	if not _can_create_users():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	helper.ensure_portal_customer_role()
	helper.ensure_portal_roles()
	helper.ensure_user_portal_linked_customer_field()

	email = (email or "").strip().lower()
	full_name = (full_name or "").strip()
	password = password or ""
	portal_linked_customer = (portal_linked_customer or "").strip()
	team = cstr(team or team_lead_of).strip()

	if not email or not full_name:
		frappe.throw(_("Valid email and full name are required"))
	frappe.utils.validate_email_address(email, throw=True)
	if not password and not cint(send_welcome_email):
		frappe.throw(_("Either send the welcome email or set a password, otherwise they cannot sign in."))

	if frappe.db.exists("User", email):
		frappe.throw(_("User already exists"))

	role_key = helper.normalize_role_key(role) or _legacy_role_key(roles_json, is_super_admin, team_lead_of)
	if role_key not in ROLE_KEYS:
		frappe.throw(_("Pick a role for this person."))

	teams = []
	if teams_json:
		try:
			parsed = json.loads(teams_json)
		except Exception:
			frappe.throw(_("Invalid teams"))
		if not isinstance(parsed, list):
			frappe.throw(_("Invalid teams"))
		teams = [cstr(t).strip() for t in parsed if t]
	if role_key == "department_admin" and not teams and team:
		teams = [team]

	if role_key == "super_admin" and not helper.is_super_admin():
		# Granting full ERP admin access is a privilege only an existing Super
		# Admin may hand out — not merely anyone who can create portal users.
		frappe.throw(_("Only a Super Admin can create another Super Admin."), frappe.PermissionError)
	if role_key == "department_admin":
		if not helper.is_super_admin():
			frappe.throw(_("Only a Super Admin can create a Department Admin."), frappe.PermissionError)
		if not teams:
			frappe.throw(_("Pick the department(s) this Department Admin will look after."))
	if role_key == "department_coordinator":
		if not teams:
			frappe.throw(_("Pick the department(s) this Department Coordinator will coordinate."))
		mine = set(helper.admin_department_names()) if helper.is_dept_admin() else set()
		for t in teams:
			if frappe.db.get_value("Department", t, "portal_unit") != "Department":
				frappe.throw(_("{0} is not a portal department.").format(t))
			if not helper.is_super_admin() and t not in mine:
				frappe.throw(
					_("Only a Super Admin or this department's Department Admin can create its Coordinator."),
					frappe.PermissionError,
				)
	if role_key == "team_lead" and not team:
		frappe.throw(_("Pick the team this Team Manager will manage."))

	is_client = role_key == "client_customer"
	if is_client:
		if team or teams:
			frappe.throw(_("A Client Customer cannot be part of a team."))
		if not portal_linked_customer:
			frappe.throw(_("Pick the customer this portal user belongs to."))
		if not frappe.db.exists("Customer", portal_linked_customer):
			frappe.throw(_("Invalid Customer for portal link."))
	else:
		portal_linked_customer = ""
		for t in teams or ([team] if team else []):
			if not frappe.db.exists("Department", t):
				frappe.throw(_("Team not found"))
			# Placing someone in a team is a team edit: Super Admin, or that team's Department Admin.
			helper.assert_manage_team(t)

	roles = (
		[helper.PORTAL_CUSTOMER_ROLE]
		if is_client
		else [helper.SUPER_ADMIN_ROLE, helper.TEAM_MEMBER_ROLE]
		if role_key == "super_admin"
		else [helper.TEAM_MEMBER_ROLE]
	)

	parts = full_name.split(None, 1)
	first_name = parts[0]
	last_name = parts[1] if len(parts) > 1 else ""

	user_dict = {
		"doctype": "User",
		"email": email,
		"first_name": first_name,
		"last_name": last_name,
		"enabled": 1,
		"send_welcome_email": cint(send_welcome_email),
		# A Client Customer has no desk access, so it is a Website User. Frappe would
		# rewrite this anyway; being explicit keeps headcount queries honest and avoids
		# consuming a System User licence seat per client contact.
		"user_type": "Website User" if is_client else "System User",
	}
	if password:
		# new_password runs the site Password Policy and strength scoring during insert.
		# frappe.utils.password.update_password(), used previously, bypasses both, so a
		# 6-character password was accepted on a site that requires far more.
		user_dict["new_password"] = password
	if is_client:
		# update_password() sends a Website User here after the welcome/reset link.
		user_dict["redirect_url"] = helper.PORTAL_HOME
	if portal_linked_customer and frappe.get_meta("User").has_field("portal_linked_customer"):
		user_dict["portal_linked_customer"] = portal_linked_customer

	doc = frappe.get_doc(user_dict)
	for r in roles:
		doc.append("roles", {"role": r})

	# Queue the welcome mail; sending it inside the request commits mid-request and an
	# SMTP failure would then surface after the user already exists.
	doc.flags.delay_emails = True
	doc.insert(ignore_permissions=True)
	if is_client:
		frappe.get_doc(
			{"doctype": helper.PORTAL_USER_CUSTOMER, "user": doc.name, "customer": portal_linked_customer}
		).insert(ignore_permissions=True)

	# Team placement and team roles go through the same code the Org Chart uses, so the
	# rules (and the Department Admin / Team Lead roles) are identical.
	if not is_client:
		from portal_app.api import teams as teams_api

		if role_key == "department_admin":
			for t in teams:
				teams_api.set_member_role(t, doc.name, "department_admin")
		elif role_key == "department_coordinator":
			for t in teams:
				_add_designation(doc.name, "department_coordinator", t)
		elif role_key == "team_lead":
			teams_api.set_member_role(team, doc.name, "team_lead")
		elif team:
			teams_api.add_team_member(team, doc.name)

	return {
		"ok": True,
		"name": doc.name,
		"email": email,
		"role": role_key,
		"email_sent": bool(doc.flags.email_sent),
	}


@frappe.whitelist(methods=["POST"])
def set_super_admin(user, enabled=1):
	"""Make someone a Super Admin, or take the role away. Super Admins only. You cannot
	change your own role, and the last Super Admin cannot be removed (nobody would be left
	to manage roles)."""
	if not helper.is_super_admin():
		frappe.throw(_("Only a Super Admin can change who is a Super Admin."), frappe.PermissionError)
	user = cstr(user).strip()
	if not user or user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		frappe.throw(_("User not found"))
	if not frappe.db.get_value("User", user, "enabled"):
		frappe.throw(_("{0} is disabled.").format(user))
	if helper.is_customer_only(user):
		frappe.throw(_("A Client Customer cannot be a Super Admin."), frappe.PermissionError)
	if user == frappe.session.user:
		frappe.throw(_("You cannot change your own role. Ask another Super Admin."), frappe.PermissionError)

	enabled = bool(cint(enabled))
	doc = frappe.get_doc("User", user)
	have = {r.role for r in doc.roles}
	if enabled:
		if helper.SUPER_ADMIN_ROLE in have:
			return {"ok": True, "user": user, "is_super_admin": True}
		doc.append("roles", {"role": helper.SUPER_ADMIN_ROLE})
		if helper.TEAM_MEMBER_ROLE not in have:
			doc.append("roles", {"role": helper.TEAM_MEMBER_ROLE})
	else:
		if helper.SUPER_ADMIN_ROLE not in have:
			return {"ok": True, "user": user, "is_super_admin": False}
		remaining = [u for u in _super_admin_names() if u != user]
		if not remaining:
			frappe.throw(_("This is the last Super Admin. Make someone else a Super Admin first."))
		for row in list(doc.roles):
			if row.role == helper.SUPER_ADMIN_ROLE:
				doc.remove(row)
	doc.flags.ignore_permissions = True
	doc.save()
	return {"ok": True, "user": user, "is_super_admin": enabled}


# ---------------------------------------------------------------------------------------
# R4: change an existing user's role
# ---------------------------------------------------------------------------------------
_UNIT_ROLES = ("department_admin", "department_coordinator", "team_lead")
_ROW_FIELD = {
	"department_admin": "portal_department_admins",
	"department_coordinator": "portal_department_coordinators",
}


def _role_change_scope() -> dict:
	"""The caller's authority in the role changer, or PermissionError."""
	helper.assert_portal_user()
	scope = helper.role_change_scope()
	if not scope.get("kind"):
		frappe.throw(_("You cannot change people's roles."), frappe.PermissionError)
	return scope


def _clean_role(role) -> str:
	role = helper.normalize_role_key(role)
	if role == "project_lead":
		frappe.throw(_("Project Lead is set on each project (Project page → Project Lead)."))
	if role not in helper.SETTABLE_ROLE_KEYS:
		frappe.throw(_("Unknown role: {0}").format(role))
	return role


def _clean_unit(role, unit, caller_is_super):
	"""The unit a role applies to: a Department unit for department_admin /
	department_coordinator, a team for team_lead, none otherwise. Pending units are for
	Super Admins only."""
	if role not in _UNIT_ROLES:
		return None
	unit = cstr(unit).strip()
	if not unit:
		frappe.throw(_("Pick the department or team for this role."))
	if not frappe.db.exists("Department", unit):
		frappe.throw(_("Department or team not found: {0}").format(unit))
	if role == "team_lead":
		if unit not in helper.portal_team_names(include_pending=True):
			frappe.throw(_("{0} is not a portal team.").format(unit))
	elif frappe.db.get_value("Department", unit, "portal_unit") != "Department":
		frappe.throw(_("{0} is not a portal department.").format(unit))
	if not caller_is_super and unit in helper.pending_unit_names():
		frappe.throw(
			_("Only a Super Admin can assign people to a department that is not active yet."),
			frappe.PermissionError,
		)
	return unit


def _assert_may_assign(caller, user, role, unit, scope) -> None:
	allowed = helper.assignable_roles_for(caller, user, scope)
	if not allowed or role not in allowed or (unit and unit not in allowed[role]):
		frappe.throw(_("You cannot give {0} this role.").format(user), frappe.PermissionError)


def _assert_not_last_super_admin(user) -> None:
	if not [u for u in _super_admin_names() if u != user]:
		frappe.throw(_("This is the last Super Admin. Make someone else a Super Admin first."))


def _save_user_roles(user, add=(), remove=()) -> None:
	doc = frappe.get_doc("User", user)
	have = {r.role for r in doc.roles}
	changed = False
	for role in remove:
		for row in list(doc.roles):
			if row.role == role:
				doc.remove(row)
				changed = True
	for role in add:
		if role not in have:
			doc.append("roles", {"role": role})
			changed = True
	if changed:
		doc.flags.ignore_permissions = True
		doc.save()


def _unit_rows(user) -> dict:
	"""{unit: {"admin", "coordinator", "lead"}}: the Department rows naming this user,
	pending units included."""
	out: dict[str, set] = {}
	for key, units in (
		("admin", helper.admin_department_names(user, include_pending=True)),
		("coordinator", helper.coordinator_department_names(user, include_pending=True)),
		("lead", helper.led_department_names(user, include_pending=True)),
	):
		for unit in units:
			out.setdefault(unit, set()).add(key)
	return out


def _drop_from_unit(unit, user, kinds) -> None:
	"""Remove this user's admin / coordinator rows and Team Manager field on one unit.
	Saved through the document, so the Department hook syncs the marker roles. Team
	membership (ToDo) is never touched."""
	doc = frappe.get_doc("Department", unit)
	changed = False
	if "lead" in kinds and doc.get("portal_team_lead") == user:
		doc.portal_team_lead = None
		changed = True
	for kind, field in (("admin", "portal_department_admins"), ("coordinator", "portal_department_coordinators")):
		if kind not in kinds:
			continue
		for row in list(doc.get(field) or []):
			if row.user == user:
				doc.remove(row)
				changed = True
	if changed:
		doc.save(ignore_permissions=True)


def _remove_designations(caller, user, scope) -> None:
	"""keep_other_roles=0: take away every unit designation the caller controls. A Super
	Admin controls all of them (pending ones included); a Department Admin the
	coordinator / Team Manager designations inside their own units, and their own
	Department Admin rows when they change themselves."""
	rows = _unit_rows(user)
	if scope["kind"] == "super_admin":
		for unit, kinds in rows.items():
			_drop_from_unit(unit, user, kinds)
		return
	units = set(scope["units"])
	teams = set(scope["teams"])
	for unit, kinds in rows.items():
		mine = set()
		if "coordinator" in kinds and unit in units:
			mine.add("coordinator")
		if "lead" in kinds and (unit in teams or unit in units):
			mine.add("lead")
		if "admin" in kinds and unit in units and user == caller:
			mine.add("admin")
		if mine:
			_drop_from_unit(unit, user, mine)


def _add_designation(user, role, unit=None) -> None:
	"""Give one designation. Team Manager: the person joins the team (ToDo) if needed and
	replaces the previous manager, who stays a member. Department Admin / Coordinator: a
	row on the department, and the person is assigned to it if they are not in it yet."""
	from portal_app.api import teams as teams_api

	if role == "super_admin":
		_save_user_roles(user, add=(helper.SUPER_ADMIN_ROLE, helper.TEAM_MEMBER_ROLE))
		return
	if role == "team_member":
		if not helper.user_is_customer_portal_user(user):
			_save_user_roles(user, add=(helper.TEAM_MEMBER_ROLE,))
		return
	if role == "team_lead":
		if user not in teams_api._assigned_by_department([unit]).get(unit, []):
			teams_api._assign_users_to_team(unit, [user])
		doc = frappe.get_doc("Department", unit)
		if doc.get("portal_team_lead") != user:
			doc.portal_team_lead = user
			doc.save(ignore_permissions=True)
		return
	field = _ROW_FIELD[role]
	if user not in helper.unit_assigned_users(unit):
		teams_api._assign_users_to_team(unit, [user])
	doc = frappe.get_doc("Department", unit)
	if user not in {r.user for r in doc.get(field) or []}:
		doc.append(field, {"user": user})
		doc.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def change_user_role(user, role, unit=None, keep_other_roles=0):
	"""Change an existing user's role from the portal (Org Chart, Admin page).

	  * Super Admin: any enabled staff login (themselves included), any role, any unit.
	  * Department Admin: the people of their own units (themselves included, never a
	    Super Admin or another Department Admin): Department Coordinator of one of their
	    departments, Team Manager of one of their teams, or Project Architect.
	By default ("change") the designations the caller controls are removed first;
	keep_other_roles=1 ("also make") only adds. The last Super Admin cannot be demoted.
	Project teams, Project Leads, shares and team membership are never touched."""
	from portal_app.api import teams as teams_api

	scope = _role_change_scope()
	caller = frappe.session.user
	user = cstr(user).strip()
	teams_api._assert_org_person(user)
	role = _clean_role(role)
	is_super = scope["kind"] == "super_admin"
	unit = _clean_unit(role, unit, is_super)
	_assert_may_assign(caller, user, role, unit, scope)

	keep = cint(keep_other_roles)
	drop_super_admin = (
		not keep and is_super and role != "super_admin" and helper.SUPER_ADMIN_ROLE in frappe.get_roles(user)
	)
	if drop_super_admin:
		_assert_not_last_super_admin(user)
	if not keep:
		_remove_designations(caller, user, scope)
		if drop_super_admin:
			_save_user_roles(user, remove=(helper.SUPER_ADMIN_ROLE,))
	_add_designation(user, role, unit)
	return {"ok": True, "user": user, "designations": helper.get_portal_designations(user)}


@frappe.whitelist(methods=["POST"])
def remove_user_designation(user, role, unit=None):
	"""Take one designation away (same authority as change_user_role). The last Super
	Admin cannot be removed."""
	from portal_app.api import teams as teams_api

	scope = _role_change_scope()
	caller = frappe.session.user
	user = cstr(user).strip()
	teams_api._assert_org_person(user)
	role = _clean_role(role)
	if role == "team_member":
		frappe.throw(_("Project Architect is the base role. Change the role instead."))
	unit = _clean_unit(role, unit, scope["kind"] == "super_admin")
	# A Department Admin may not make themselves Coordinator, but may still step down.
	self_step_down = (
		scope["kind"] == "department_admin"
		and user == caller
		and role == "department_coordinator"
		and unit in scope["departments"]
	)
	if not self_step_down:
		_assert_may_assign(caller, user, role, unit, scope)
	if role == "super_admin":
		if helper.SUPER_ADMIN_ROLE in frappe.get_roles(user):
			_assert_not_last_super_admin(user)
			_save_user_roles(user, remove=(helper.SUPER_ADMIN_ROLE,))
	else:
		kind = {"department_admin": "admin", "department_coordinator": "coordinator", "team_lead": "lead"}[role]
		_drop_from_unit(unit, user, {kind})
	return {"ok": True, "user": user, "designations": helper.get_portal_designations(user)}


def _unit_labels(names) -> dict:
	names = list({n for n in names if n})
	if not names:
		return {}
	return dict(
		frappe.get_all("Department", filters={"name": ["in", names]}, fields=["name", "department_name"], as_list=True)
	)


@frappe.whitelist()
def get_user_designations(user=None):
	"""A user's designations and what the caller may set for them (the Change role
	dialog). Your own are always readable. Read-only."""
	helper.assert_portal_user()
	caller = frappe.session.user
	user = cstr(user).strip() or caller
	scope = helper.role_change_scope(caller)
	assignable = helper.assignable_roles_for(caller, user, scope) if scope.get("kind") else {}
	if user != caller and not assignable:
		frappe.throw(_("You cannot change this person's role."), frappe.PermissionError)
	units = {u for unit_list in assignable.values() for u in unit_list}
	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name") or user,
		"designations": helper.get_portal_designations(user),
		"assignable": assignable,
		"unit_labels": _unit_labels(units),
		"pending_units": sorted(helper.pending_unit_names() & units),
	}


@frappe.whitelist()
def search_role_changeable_users(txt=""):
	"""Logins whose role the caller may change (the Admin page's Change role tool)."""
	scope = _role_change_scope()
	caller = frappe.session.user
	safe = cstr(txt).replace("%", "").replace("_", "").strip()[:100]
	kwargs = dict(
		filters=[["enabled", "=", 1], ["name", "not in", ["Guest", "Administrator"]]],
		fields=["name", "full_name", "user_type"],
		order_by="full_name asc",
		limit_page_length=60,
	)
	if safe:
		kwargs["or_filters"] = [
			["name", "like", "%" + safe + "%"],
			["full_name", "like", "%" + safe + "%"],
		]
	out = []
	for r in frappe.get_all("User", **kwargs):
		if helper.assignable_roles_for(caller, r.name, scope):
			out.append(
				{
					"name": r.name,
					"full_name": r.full_name or r.name,
					"role_label": helper.ROLE_LABELS.get(helper.get_portal_role(r.name), ""),
				}
			)
		if len(out) >= 20:
			break
	return out


def _super_admin_names() -> list:
	holders = set(
		frappe.get_all("Has Role", filters={"parenttype": "User", "role": helper.SUPER_ADMIN_ROLE}, pluck="parent")
	)
	holders -= {"Administrator", "Guest"}
	if not holders:
		return []
	return frappe.get_all("User", filters={"name": ["in", list(holders)], "enabled": 1}, pluck="name")


def reset_password_for(user: str, mode: str = "email", new_password=None) -> dict:
	"""Reset a login's password. `email` sends a reset link (valid for the System Settings
	"reset password link expiry"); `set` sets the password directly and signs them out
	everywhere. The caller must already have been checked.

	The mail is QUEUED, never sent inside the request: EmailQueue.send() commits mid-request
	and an SMTP failure there would surface after the link had already been generated."""
	doc = frappe.get_doc("User", user)
	mode = cstr(mode).strip() or "email"
	if mode == "email":
		if helper.is_customer_only(user):
			# update_password() sends a Website User here after they set the password.
			doc.db_set("redirect_url", helper.PORTAL_HOME)
		try:
			# password_reset_mail() hard-codes now=True; queue the same mail instead.
			link = doc.reset_password(send_email=False)
			doc.send_login_mail(
				_("Password Reset"),
				"password_reset",
				{"link": link},
				now=False,
				custom_template=frappe.db.get_system_setting("reset_password_template"),
			)
		except frappe.OutgoingEmailError:
			frappe.clear_last_message()
			frappe.throw(_("No outgoing email account is configured, so the reset link could not be sent."))
		return {"ok": True, "mode": "email", "email": doc.email}

	if mode == "set":
		new_password = cstr(new_password)
		if len(new_password) < 8:
			frappe.throw(_("The new password must be at least 8 characters."))
		doc.flags.ignore_permissions = True
		# new_password on save runs the site Password Policy, then updates __Auth.
		doc.new_password = new_password
		doc.save()
		from frappe.sessions import clear_sessions

		clear_sessions(user=user, force=True)
		return {"ok": True, "mode": "set", "email": doc.email}

	frappe.throw(_("Unknown reset mode."))


@frappe.whitelist(methods=["POST"])
def reset_user_password(user, mode="email", new_password=None):
	"""Reset someone's password from the Org Chart or the Admin page. Who may reset whom:
	see helper.can_reset_password_for. Setting a password directly is for Super Admins; a
	Department Admin sends the reset link, which the person uses themselves."""
	user = cstr(user).strip()
	if not frappe.db.exists("User", user) or not frappe.db.get_value("User", user, "enabled"):
		frappe.throw(_("User not found"))
	if not helper.can_reset_password_for(user):
		frappe.throw(_("You cannot reset this person's password."), frappe.PermissionError)
	if cstr(mode).strip() == "set" and not helper.is_super_admin():
		frappe.throw(
			_("Only a Super Admin can set a password directly. Send the reset link instead."),
			frappe.PermissionError,
		)
	return reset_password_for(user, mode, new_password)


@frappe.whitelist()
def search_resettable_users(txt=""):
	"""Logins whose password the caller may reset (the Admin page's reset tool)."""
	if not helper.has_portal_staff_project_access():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	safe = cstr(txt).replace("%", "").replace("_", "").strip()[:100]
	kwargs = dict(
		filters=[["enabled", "=", 1], ["name", "not in", ["Guest", "Administrator"]]],
		fields=["name", "full_name", "user_type"],
		order_by="full_name asc",
		limit_page_length=60,
	)
	if safe:
		kwargs["or_filters"] = [
			["name", "like", "%" + safe + "%"],
			["full_name", "like", "%" + safe + "%"],
		]
	rows = frappe.get_all("User", **kwargs)
	out = []
	for r in rows:
		if helper.can_reset_password_for(r.name):
			out.append(
				{
					"name": r.name,
					"full_name": r.full_name or r.name,
					"role_label": helper.ROLE_LABELS.get(helper.get_portal_role(r.name), ""),
				}
			)
		if len(out) >= 20:
			break
	return out


def run_demo_seed():
	"""Legacy seed entry point — deliberately NOT whitelisted.

	This path creates users and projects without recording what it created, so there
	is no teardown: cleaning up afterwards means hand-writing a bench script and
	guessing which rows were seeded. `create_demo_seed_run` supersedes it and tracks
	every document. Reachable via `bench execute` only.
	"""
	if not _can_run_seed_via_portal():
		frappe.throw(
			_(
				"Demo seed is only for System Managers, and requires Developer Mode or Allow portal demo seed in settings."
			),
			frappe.PermissionError,
		)

	from portal_app.demo_seed import run_seed

	return run_seed()


def _assert_can_run_demo_seed():
	if not _can_run_seed_via_portal():
		frappe.throw(
			_(
				"Demo seed is only for System Managers, and requires Developer Mode or Allow portal demo seed in settings."
			),
			frappe.PermissionError,
		)


@frappe.whitelist()
def create_demo_seed_run(
	run_label: str = "Portal demo run",
	include_users: int = 1,
	include_customers: int = 1,
	include_projects: int = 1,
	include_tasks: int = 1,
	include_files: int = 1,
	notes: str | None = None,
):
	"""Create a Portal Demo Seed Run record. The doctype's `before_insert` hook
	creates the demo data and records every doc in the run's child tables, so
	deleting the run later wipes only what this run added.
	"""
	_assert_can_run_demo_seed()
	if not frappe.db.exists("DocType", "Portal Demo Seed Run"):
		frappe.throw(_("Run `bench migrate` to install the Portal Demo Seed Run doctype."))

	doc = frappe.get_doc(
		{
			"doctype": "Portal Demo Seed Run",
			"run_label": (run_label or "Portal demo run").strip()[:140] or "Portal demo run",
			"include_users": cint(include_users),
			"include_customers": cint(include_customers),
			"include_projects": cint(include_projects),
			"include_tasks": cint(include_tasks),
			"include_files": cint(include_files),
			"notes": notes or "",
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return _serialize_run(doc)


@frappe.whitelist()
def list_demo_seed_runs():
	"""Recent seed runs for the Admin page."""
	_assert_can_run_demo_seed()
	if not frappe.db.exists("DocType", "Portal Demo Seed Run"):
		return {"runs": []}
	rows = frappe.get_all(
		"Portal Demo Seed Run",
		fields=["name", "run_label", "status", "run_at", "run_by", "demo_password_hint", "creation"],
		order_by="creation desc",
		limit_page_length=50,
	)
	# Hydrate counts so the UI doesn't have to fetch every run separately.
	out = []
	for r in rows:
		counts = {}
		for kind, child in (
			("users", "created_users"),
			("customers", "created_customers"),
			("projects", "created_projects"),
			("tasks", "created_tasks"),
			("files", "created_files"),
		):
			counts[kind] = frappe.db.count(
				"Portal Demo Seed Item",
				{"parent": r["name"], "parentfield": child},
			)
		out.append({**r, "counts": counts})
	return {"runs": out}


@frappe.whitelist()
def delete_demo_seed_run(name: str):
	"""Delete a Portal Demo Seed Run. The doctype's `on_trash` hook wipes every
	record this run created (preserving rows it merely re-found on disk)."""
	_assert_can_run_demo_seed()
	if not frappe.db.exists("DocType", "Portal Demo Seed Run"):
		frappe.throw(_("Portal Demo Seed Run doctype is not installed."))
	if not name or not frappe.db.exists("Portal Demo Seed Run", name):
		frappe.throw(_("Seed run not found."))
	frappe.delete_doc("Portal Demo Seed Run", name, ignore_permissions=True, force=1)
	frappe.db.commit()
	return {"ok": True, "name": name}


@frappe.whitelist()
def parse_project_list_docx():
	"""Parse an uploaded .docx file and return the project list it contains.
	Expects the same format as ATA project list.docx:
	  NNNN – PROJECT NAME  (lines starting with a 4-digit code)
	  CDB-NN – PROJECT NAME
	"""
	_assert_can_run_demo_seed()
	uploaded = frappe.request.files.get("file")
	if not uploaded:
		frappe.throw(_("No file uploaded."))

	import zipfile
	import xml.etree.ElementTree as ET
	import io
	import re as _re

	content = uploaded.read()
	if not content:
		frappe.throw(_("Uploaded file is empty."))

	# Cap the upload before parsing: the whole archive is buffered in memory and the
	# XML is expanded, so an unbounded file is a trivial memory-exhaustion vector.
	if len(content) > 20 * 1024 * 1024:
		frappe.throw(_("File is too large. The project list must be under 20 MB."))

	try:
		zf = zipfile.ZipFile(io.BytesIO(content))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Portal: docx parse")
		frappe.throw(_("Could not open the uploaded file. Make sure it is a valid .docx."))

	# Reject a decompression bomb before any member is read.
	if sum(i.file_size for i in zf.infolist()) > 200 * 1024 * 1024:
		frappe.throw(_("The uploaded document expands to too much data."))

	# Support both .docx (word/document.xml) and plain XML files.
	xml_bytes = None
	try:
		if "word/document.xml" in zf.namelist():
			xml_bytes = zf.open("word/document.xml").read()
		else:
			# Try any XML entry
			for name in zf.namelist():
				if name.endswith(".xml") and "document" in name.lower():
					xml_bytes = zf.open(name).read()
					break
	except Exception as e:
		frappe.throw(_(f"Could not read document XML: {e}"))

	if not xml_bytes:
		frappe.throw(_("No document XML found inside the file. Make sure it is a valid .docx."))

	try:
		root = ET.fromstring(xml_bytes)
	except Exception as e:
		frappe.throw(_(f"Could not parse document XML: {e}"))

	# Word XML namespace — try to detect it from the root tag.
	ns_uri = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
	if root.tag.startswith("{"):
		ns_uri = root.tag.split("}")[0][1:]
	ns = {"w": ns_uri}

	# Collect all paragraph text (including inside tables).
	def _para_text(para):
		parts = []
		for r in para.findall(".//w:r", ns):
			t = r.find("w:t", ns)
			if t is not None:
				parts.append(t.text or "")
		return "".join(parts).strip()

	# Separator: en-dash, em-dash, figure-dash, minus-sign, or plain hyphen followed by space
	_SEP = r"[‒–—―−\-]"
	_CODE = r"(?:CDB-\d+|\d{3,4})"
	pattern = _re.compile(rf"^({_CODE})\s*{_SEP}+\s*(.+)$")

	projects = []
	seen_codes = set()
	for para in root.findall(".//w:p", ns):
		line = _para_text(para)
		if not line:
			continue
		m = pattern.match(line)
		if m:
			code = m.group(1).strip()
			name = m.group(2).strip()
			if code not in seen_codes:
				seen_codes.add(code)
				projects.append({"code": code, "name": name})

	return {"projects": projects, "count": len(projects)}


@frappe.whitelist()
def create_demo_seed_run_from_docx(
	run_label: str = "Portal demo run",
	projects_json: str = "[]",
	include_users: int = 1,
	include_files: int = 1,
):
	"""Create a seed run using a project list parsed from a .docx file."""
	_assert_can_run_demo_seed()
	if not frappe.db.exists("DocType", "Portal Demo Seed Run"):
		frappe.throw(_("Run `bench migrate` to install the Portal Demo Seed Run doctype."))

	import json as _json

	try:
		raw_projects = _json.loads(projects_json or "[]")
	except Exception:
		frappe.throw(_("Invalid projects_json"))

	# Patch the DEMO_PROJECTS on the seed run doctype module temporarily
	from portal_app.project_portal.doctype.portal_demo_seed_run import portal_demo_seed_run as _mod
	from frappe.utils import add_days, today as _today

	_STAGE_PCT = _mod._STAGE_PCT
	_STAGE_STATUS = _mod._STAGE_STATUS
	_MANAGERS = _mod._MANAGERS
	_TEAMS = _mod._TEAMS

	def _year_from_code(code):
		if code.startswith("CDB-"):
			return 2026
		try:
			return 2000 + int(code[:2])
		except Exception:
			return 2024

	def _stage_for_year(year):
		if year <= 2022:
			return "Done"
		if year == 2023:
			return "On Hold"
		if year == 2024:
			return "Review"
		if year == 2025:
			return "Active"
		return "Planning"

	generated = []
	for i, p in enumerate(raw_projects):
		code = str(p.get("code") or "").strip()
		name = str(p.get("name") or "").strip()
		if not code or not name:
			continue
		year = _year_from_code(code)
		stage = _stage_for_year(year)
		generated.append(
			{
				"project_name": f"{code} – {name}",
				"code": f"ATA-{code}",
				"stage": stage,
				"year": year,
				"manager": _MANAGERS[i % len(_MANAGERS)],
				"team": _TEAMS[i % len(_TEAMS)],
				"cost": 0,
				"tasks": [],
				"attach_readme": False,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Portal Demo Seed Run",
			"run_label": (run_label or "Portal demo run").strip()[:140] or "Portal demo run",
			"include_users": cint(include_users),
			"include_customers": 0,
			"include_projects": 1,
			"include_tasks": 0,
			"include_files": cint(include_files),
		}
	)
	# Pass the parsed list on the document. Reassigning the module-level DEMO_PROJECTS
	# (the previous approach) raced across concurrent requests in the same worker and
	# could permanently leave one admin's import installed for every later seed.
	doc.flags.projects_override = generated
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return _serialize_run(doc)


@frappe.whitelist()
def clear_all_demo_data():
	"""Delete every Active Portal Demo Seed Run (and the records they created)."""
	_assert_can_run_demo_seed()
	if not frappe.db.exists("DocType", "Portal Demo Seed Run"):
		frappe.throw(_("Portal Demo Seed Run doctype is not installed."))
	names = frappe.get_all("Portal Demo Seed Run", filters={"status": "Active"}, pluck="name")
	for name in names:
		frappe.delete_doc("Portal Demo Seed Run", name, ignore_permissions=True, force=1)
	frappe.db.commit()
	return {"ok": True, "deleted": len(names)}


def _serialize_run(doc) -> dict:
	out = {
		"name": doc.name,
		"run_label": doc.run_label,
		"status": doc.status,
		"run_at": str(doc.run_at) if doc.run_at else None,
		"run_by": doc.run_by,
		"demo_password_hint": doc.demo_password_hint,
		"counts": {
			"users": len(doc.get("created_users") or []),
			"customers": len(doc.get("created_customers") or []),
			"projects": len(doc.get("created_projects") or []),
			"tasks": len(doc.get("created_tasks") or []),
			"files": len(doc.get("created_files") or []),
		},
	}
	try:
		out["summary"] = json.loads(doc.summary_json or "{}")
	except Exception:
		out["summary"] = {}
	return out
