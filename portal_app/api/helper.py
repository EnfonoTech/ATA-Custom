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

	rows = frappe.db.sql(
		"SELECT DISTINCT parent FROM `tabProject User` WHERE user=%s",
		user,
	)
	return [r[0] for r in rows]


def assert_project_access(project_name: str) -> None:
	if project_name not in get_allowed_project_names():
		frappe.throw(_("No access to this project"), frappe.PermissionError)


def can_manage_project(project_name: str) -> bool:
	if has_portal_staff_project_access():
		return project_name in get_allowed_project_names()
	if user_is_customer_portal_user():
		return False
	if project_name not in get_allowed_project_names():
		return False
	meta = frappe.get_meta("Project")
	if meta.has_field("portal_project_manager"):
		pm = frappe.db.get_value("Project", project_name, "portal_project_manager")
		if pm and pm == frappe.session.user:
			return True
		# Desk projects often omit Portal Project Manager; treat document owner as manager when the field is blank.
		if not pm:
			owner = frappe.db.get_value("Project", project_name, "owner")
			if owner == frappe.session.user:
				return True
	return False


def assert_manage_project(project_name: str) -> None:
	if not can_manage_project(project_name):
		frappe.throw(
			_("Only the portal project manager or a Projects Manager can change this."),
			frappe.PermissionError,
		)


def can_edit_portal_folder_template(user=None) -> bool:
	"""Company-wide subfolder template in Portal Project Settings (desk single).

	Restricted to the dedicated Auditor role (or System Manager as a fallback).
	The template controls the standard project folder structure and is treated as
	an audit/governance artifact, so non-auditor staff cannot change it."""
	user = user or frappe.session.user
	if user == "Guest" or not user_can_use_portal(user):
		return False
	if user_is_customer_portal_user(user):
		return False
	roles = set(frappe.get_roles(user))
	if "Auditor" in roles:
		return True
	if "System Manager" in roles:
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
	try:
		if frappe.has_permission("Project", "create", user=frappe.session.user):
			return
	except Exception:
		pass
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
		"allow_portal_demo_seed": int(doc.get("allow_portal_demo_seed") or 0),
		"allow_any_portal_user_to_create_project": int(doc.get("allow_any_portal_user_to_create_project") or 0),
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
