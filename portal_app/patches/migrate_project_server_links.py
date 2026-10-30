import json
import os
import re

import frappe
from frappe.utils import cstr, now_datetime

from portal_app.api import helper
from portal_app.project_portal.doctype.portal_project_link.portal_project_link import (
	_CONTROL_CHARS,
	_URL_BAD_CHARS,
	_URL_SCHEME,
	MAX_PATH,
	MAX_URL,
)

# Project field -> Portal Project Link type.
FIELD_TO_TYPE = (
	("portal_server_t", "T Server"),
	("portal_server_a", "Autodesk Server"),
	("portal_server_c", "ERP"),
)
_URL = re.compile(r"^https?://", re.I)
_WHITESPACE = re.compile(r"\s")
COMMIT_EVERY = 50


def execute():
	run(dry_run=0)


def _target(value: str) -> str:
	"""A clean http(s) URL becomes open_url; anything else (a pasted T:\\ path, plain text,
	a URL with spaces in it) stays copy_path, so nothing is dropped."""
	if _URL.match(value) and not _WHITESPACE.search(value):
		return "open_url"
	return "copy_path"


def _would_fail(target: str, value: str):
	"""The Portal Project Link controller's rules for this value (None: it passes), so the
	dry run shows what apply would roll back and log."""
	if target == "open_url":
		if len(value) > MAX_URL:
			return f"longer than {MAX_URL} characters"
		if not _URL_SCHEME.match(value) or _URL_BAD_CHARS.search(value):
			return "not a clean http(s) URL"
		return None
	if len(value) > MAX_PATH:
		return f"longer than {MAX_PATH} characters"
	if _CONTROL_CHARS.search(value):
		return "contains control characters"
	return None


def _allowed_users(project: str, lead) -> list:
	"""Today's "everyone on the project can open it": the Project Users and the Project
	Lead, minus disabled logins, client contacts and the built-in accounts."""
	users = frappe.get_all("Project User", filters={"parent": project, "parenttype": "Project"}, pluck="user")
	if lead:
		users.append(lead)
	out = []
	for u in dict.fromkeys(u for u in users if u):
		if u in ("Administrator", "Guest") or not frappe.db.get_value("User", u, "enabled"):
			continue
		if helper.is_customer_only(u):
			continue
		out.append(u)
	return out


def run(dry_run=1):
	"""Move Project.portal_server_t/a/c into Portal Project Link rows.

	`dry_run=1` (the default) only reads Project and prints what would happen, so it can
	be run before `bench migrate`:
	    bench --site <site> execute portal_app.patches.migrate_project_server_links.run --kwargs "{'dry_run': 1}"
	An existing link of the same type is never overwritten (only its empty fields are
	filled). A JSON backup of every original value is written before the first project
	is cleared. Idempotent: once the fields are empty there is nothing left to do."""
	dry_run = int(dry_run or 0)
	if not frappe.db.exists("DocType", "Project"):
		return
	fields = [(f, t) for f, t in FIELD_TO_TYPE if frappe.db.has_column("Project", f)]
	if not fields:
		return
	has_lead = frappe.db.has_column("Project", "portal_project_manager")
	rows = frappe.get_all(
		"Project",
		or_filters=[[f, "!=", ""] for f, _t in fields],
		fields=["name", *(f for f, _t in fields), *(["portal_project_manager"] if has_lead else [])],
		order_by="name asc",
	)
	link_table = frappe.db.table_exists(helper.PROJECT_LINK_DOCTYPE)

	if dry_run:
		count = failing = 0
		for row in rows:
			users = _allowed_users(row.name, row.get("portal_project_manager"))
			for field, link_type in fields:
				value = cstr(row.get(field)).strip()
				if not value:
					continue
				count += 1
				target = _target(value)
				print(f"{row.name} {field} -> {link_type}.{target} ({len(users)} allowed users)")
				reason = _would_fail(target, value)
				if reason:
					failing += 1
					print(f"! WOULD FAIL {row.name} {field}: {reason}")
		print(
			f"Total: {count} value(s) on {len(rows)} project(s), {failing} would fail. Dry run, nothing written."
		)
		return

	if not rows:
		return
	if not link_table:
		frappe.throw("Portal Project Link does not exist yet. Run bench migrate first.")

	backup = {row.name: {f: row.get(f) for f, _t in fields if cstr(row.get(f)).strip()} for row in rows}
	path = frappe.get_site_path("private", "backups", f"portal_server_links_{now_datetime():%Y%m%d_%H%M%S}.json")
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as fh:
		json.dump(backup, fh, indent=1, default=str)

	failed = []
	for i, row in enumerate(rows, start=1):
		try:
			frappe.db.savepoint("portal_server_link")
			users = _allowed_users(row.name, row.get("portal_project_manager"))
			cleared = {}
			for field, link_type in fields:
				value = cstr(row.get(field)).strip()
				if not value:
					continue
				target = _target(value)
				existing = frappe.db.get_value(
					helper.PROJECT_LINK_DOCTYPE, {"project": row.name, "link_type": link_type}
				)
				if existing:
					doc = frappe.get_doc(helper.PROJECT_LINK_DOCTYPE, existing)
					changed = False
					if not cstr(doc.get(target)).strip():
						doc.set(target, value)
						changed = True
					if not doc.get("allowed_users") and users:
						for u in users:
							doc.append("allowed_users", {"user": u})
						changed = True
					if changed:
						doc.save(ignore_permissions=True)
				else:
					doc = frappe.get_doc(
						{
							"doctype": helper.PROJECT_LINK_DOCTYPE,
							"project": row.name,
							"link_type": link_type,
							target: value,
							"allowed_users": [{"user": u} for u in users],
						}
					)
					doc.insert(ignore_permissions=True)
				cleared[field] = None
			if cleared:
				frappe.db.set_value("Project", row.name, cleared, update_modified=False)
		except Exception:
			frappe.db.rollback(save_point="portal_server_link")
			frappe.log_error(title="Portal: server link migration", message=frappe.get_traceback())
			failed.append(row.name)
		if i % COMMIT_EVERY == 0:
			frappe.db.commit()
	print(
		f"Portal server links: {len(rows) - len(failed)} project(s) migrated, {len(failed)} failed"
		f"{' (' + ', '.join(failed) + ')' if failed else ''}. Failed values are kept on the project"
		f" and in the backup {path}; see Error Log 'Portal: server link migration'."
	)
