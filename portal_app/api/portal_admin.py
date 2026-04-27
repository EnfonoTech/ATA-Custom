import json

import frappe
from frappe import _

from portal_app.api import helper


def _can_create_users() -> bool:
	if frappe.session.user == "Guest":
		return False
	if "System Manager" in frappe.get_roles():
		return True
	try:
		return bool(frappe.has_permission("User", "create", user=frappe.session.user))
	except Exception:
		return False


def _can_run_seed_via_portal() -> bool:
	if frappe.session.user == "Guest":
		return False
	if "System Manager" not in frappe.get_roles():
		return False
	if frappe.conf.get("developer_mode"):
		return True

	return bool(helper.get_portal_settings_dict().get("allow_portal_demo_seed"))


ALLOWED_PORTAL_USER_ROLES = frozenset({"Projects User", "Projects Manager", "Portal Customer"})


@frappe.whitelist()
def get_portal_admin_capabilities():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return {
		"can_create_users": _can_create_users(),
		"can_run_demo_seed": _can_run_seed_via_portal(),
	}


@frappe.whitelist()
def create_portal_user(email, full_name, password, roles_json=None, send_welcome_email=0, portal_linked_customer=None):
	if not _can_create_users():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	helper.ensure_portal_customer_role()
	helper.ensure_user_portal_linked_customer_field()

	email = (email or "").strip().lower()
	full_name = (full_name or "").strip()
	password = password or ""
	portal_linked_customer = (portal_linked_customer or "").strip()

	if not email or not full_name or len(password) < 6:
		frappe.throw(_("Valid email, full name, and password (min 6 characters) are required"))

	if frappe.db.exists("User", email):
		frappe.throw(_("User already exists"))

	roles = ["Projects User"]
	if roles_json:
		try:
			parsed = json.loads(roles_json)
			if isinstance(parsed, list) and parsed:
				roles = [str(r).strip() for r in parsed if r]
		except Exception:
			frappe.throw(_("Invalid roles"))

	for r in roles:
		if r not in ALLOWED_PORTAL_USER_ROLES:
			frappe.throw(_("Role {0} cannot be assigned from the portal").format(r))

	if not roles:
		frappe.throw(_("Select at least one role"))

	if "Portal Customer" in roles:
		if not portal_linked_customer:
			frappe.throw(_("Portal Customer role requires a linked Customer (ID)."))
		if not frappe.db.exists("Customer", portal_linked_customer):
			frappe.throw(_("Invalid Customer for portal link."))

	parts = full_name.split(None, 1)
	first_name = parts[0]
	last_name = parts[1] if len(parts) > 1 else ""

	user_dict = {
		"doctype": "User",
		"email": email,
		"first_name": first_name,
		"last_name": last_name,
		"enabled": 1,
		"send_welcome_email": int(send_welcome_email or 0),
		"user_type": "System User",
	}
	if portal_linked_customer and frappe.get_meta("User").has_field("portal_linked_customer"):
		user_dict["portal_linked_customer"] = portal_linked_customer

	doc = frappe.get_doc(user_dict)
	for role in roles:
		doc.append("roles", {"role": role})

	doc.insert(ignore_permissions=True)

	from frappe.utils.password import update_password

	update_password(email, password)

	return {"ok": True, "name": doc.name, "email": email}


@frappe.whitelist()
def run_demo_seed():
	"""Legacy seed entry point. Kept for backward compatibility — prefer
	`create_demo_seed_run` which records what it created so it can be cleaned up."""
	if not _can_run_seed_via_portal():
		frappe.throw(
			_("Demo seed is only for System Managers, and requires Developer Mode or Allow portal demo seed in settings."),
			frappe.PermissionError,
		)

	from portal_app.demo_seed import run_seed

	return run_seed()


def _assert_can_run_demo_seed():
	if not _can_run_seed_via_portal():
		frappe.throw(
			_("Demo seed is only for System Managers, and requires Developer Mode or Allow portal demo seed in settings."),
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
			"include_users": int(include_users or 0),
			"include_customers": int(include_customers or 0),
			"include_projects": int(include_projects or 0),
			"include_tasks": int(include_tasks or 0),
			"include_files": int(include_files or 0),
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
