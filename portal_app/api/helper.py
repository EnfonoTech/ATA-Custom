from __future__ import annotations

import frappe
from frappe import _

PORTAL_ROLES = frozenset({"System Manager", "Projects Manager", "Projects User"})
PORTAL_CUSTOMER_ROLE = "Portal Customer"


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
	"""Create Role so Has Role child rows can link to it (avoids LinkValidationError)."""
	if frappe.db.exists("Role", PORTAL_CUSTOMER_ROLE):
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


def has_portal_staff_project_access(user=None) -> bool:
	"""System / Projects Manager: full project portfolio in ERPNext; overrides customer-only portal scoping."""
	user = user or frappe.session.user
	if user == "Guest":
		return False
	roles = set(frappe.get_roles(user))
	return "System Manager" in roles or "Projects Manager" in roles


def get_portal_linked_customer(user=None) -> str | None:
	user = user or frappe.session.user
	if user == "Guest":
		return None
	if not frappe.get_meta("User").has_field("portal_linked_customer"):
		return None
	return frappe.db.get_value("User", user, "portal_linked_customer")


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
	user = user or frappe.session.user
	if not user_can_use_portal(user):
		return []

	if has_portal_staff_project_access(user):
		return frappe.get_all("Project", pluck="name")

	if user_is_customer_portal_user(user):
		cust = get_portal_linked_customer(user)
		if not cust:
			return []
		return frappe.get_all("Project", filters={"customer": cust}, pluck="name")

	# Internal staff (Projects User) READ the whole portfolio. ATA is one practice and
	# people need to find each other's drawings; the restriction that matters is WRITE,
	# handled by can_manage_project() below, and MONEY, handled by
	# can_view_project_value(). Portal Customers are scoped to their own customer above
	# and are unaffected by this.
	return frappe.get_all("Project", pluck="name")


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

	System Manager gets full portfolio oversight — every project's value. A
	Projects Manager only sees the value of the specific project(s) they are
	assigned to as Portal Project Manager, not the whole portfolio.

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
	if "System Manager" in roles:
		return True
	if "Projects Manager" in roles:
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
	if "System Manager" in roles:
		return get_allowed_project_names(user)
	if "Projects Manager" in roles:
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


def can_manage_project(project_name: str) -> bool:
	"""Management-level action (edit, delete, team sync, sharing, folder rules, etc.).

	Two ways in:
	  * System Manager / Projects Manager — anywhere in the portfolio.
	  * A Projects User who is ON that project's team — that project only.

	Read access is deliberately wider than this: every internal user can now SEE the
	whole portfolio (get_allowed_project_names), but can only change the projects they
	belong to. Customer portal users can never manage anything.
	"""
	# Staff FIRST. Administrator holds every role in Frappe, Portal Customer
	# included, so testing "is customer" before "is staff" locks the superuser out
	# of managing anything.
	if has_portal_staff_project_access():
		return project_name in get_allowed_project_names()
	if user_is_customer_portal_user():
		return False
	return project_name in project_member_names()


def assert_manage_project(project_name: str) -> None:
	if not can_manage_project(project_name):
		frappe.throw(
			_("You can only change projects you are on the team of."),
			frappe.PermissionError,
		)


def can_manage_teams(user=None) -> bool:
	"""Editing Teams (Department) info and member assignment is a staff-level action."""
	return has_portal_staff_project_access(user)


def assert_manage_teams() -> None:
	if not can_manage_teams():
		frappe.throw(
			_("Only a Projects Manager or System Manager can manage teams."),
			frappe.PermissionError,
		)


def can_manage_project_team(project_name: str, user=None) -> bool:
	"""Adding/removing a project's own members (Project User rows) is either a
	staff-level action, or something the project's own portal_project_manager may
	do for that one project — same two-tier shape as _assert_may_set_team."""
	user = user or frappe.session.user
	if has_portal_staff_project_access(user):
		return True
	return frappe.db.get_value("Project", project_name, "portal_project_manager") == user


def assert_manage_project_team(project_name: str) -> None:
	if not can_manage_project_team(project_name):
		frappe.throw(
			_("Only a Projects Manager, System Manager, or this project's own lead can manage its team."),
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
	roles = set(frappe.get_roles())
	if "Projects Manager" in roles or "System Manager" in roles:
		return
	if user_is_customer_portal_user():
		frappe.throw(_("Customer portal users cannot create projects."), frappe.PermissionError)
	settings = get_portal_settings_dict()
	if settings.get("allow_any_portal_user_to_create_project"):
		return
	# Deliberately do NOT fall back to ERPNext's core "Project create" permission here —
	# the stock "Projects User" role grants that by default, which would silently let a
	# Projects User create projects from the portal even though the spec says they can't.
	# Only System Manager / Projects Manager (above) or the explicit opt-in setting may.
	frappe.throw(_("You cannot create projects from the portal."), frappe.PermissionError)


def can_manage_customers_in_portal() -> bool:
	"""Search / create Customer and link to Project from the portal."""
	if not user_can_use_portal():
		return False
	roles = set(frappe.get_roles())
	if "System Manager" in roles or "Projects Manager" in roles:
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
	return get_portal_settings_dict()


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
	only applies to users who actually hold a portal-relevant role (Projects User or
	Portal Customer) — System Manager / Projects Manager already get every project via
	get_allowed_project_names() and are never restricted here, and any other Desk user
	with no portal role at all (HR, Accounts, etc., who may reference Project links for
	unrelated reasons) is left completely untouched.
	"""
	if ptype not in ("read", "select"):
		return None
	user = user or frappe.session.user
	if user in ("Administrator", "Guest"):
		return None
	if has_portal_staff_project_access(user):
		return None
	if "Projects User" not in frappe.get_roles(user) and not user_is_customer_portal_user(user):
		return None
	if doc.name in get_allowed_project_names(user):
		return None
	return False
