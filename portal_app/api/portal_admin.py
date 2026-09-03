import json

import frappe
from frappe import _
from frappe.utils import cint

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
	"""System Manager PLUS an explicit opt-in on this site.

	Seeding creates real, enabled login accounts and real Projects/Tasks/Files. On a
	production site that must never be one misclick away, so it additionally requires
	developer_mode or the "Allow portal demo seed" switch in Portal Project Settings —
	which is what the error message shown to users has always claimed.
	"""
	if frappe.session.user == "Guest":
		return False
	if "System Manager" not in frappe.get_roles():
		return False
	if cint(frappe.conf.get("developer_mode")):
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
		"can_edit_folder_template": helper.can_edit_portal_folder_template(),
	}


@frappe.whitelist()
def create_portal_user(
	email, full_name, password, roles_json=None, send_welcome_email=0, portal_linked_customer=None
):
	if not _can_create_users():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	helper.ensure_portal_customer_role()
	helper.ensure_user_portal_linked_customer_field()

	email = (email or "").strip().lower()
	full_name = (full_name or "").strip()
	password = password or ""
	portal_linked_customer = (portal_linked_customer or "").strip()

	if not email or not full_name or not password:
		frappe.throw(_("Valid email, full name, and password are required"))

	if frappe.db.exists("User", email):
		frappe.throw(_("User already exists"))

	# roles_json omitted entirely (e.g. a direct API caller) defaults to Projects User;
	# an explicitly-provided empty list (all checkboxes unticked in the form) must be
	# rejected, not silently fall back to the same default — it used to be
	# indistinguishable from "not provided" here, so unticking every role box was
	# accepted instead of refused.
	roles = None
	if roles_json:
		try:
			parsed = json.loads(roles_json)
		except Exception:
			frappe.throw(_("Invalid roles"))
		if not isinstance(parsed, list):
			frappe.throw(_("Invalid roles"))
		roles = [str(r).strip() for r in parsed if r]
	if roles is None:
		roles = ["Projects User"]

	if not roles:
		frappe.throw(_("Select at least one role"))

	for r in roles:
		if r not in ALLOWED_PORTAL_USER_ROLES:
			frappe.throw(_("Role {0} cannot be assigned from the portal").format(r))

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
		"send_welcome_email": cint(send_welcome_email),
		# A Portal Customer has no desk access, so it is a Website User. Frappe would
		# rewrite this anyway; being explicit keeps headcount queries honest and avoids
		# consuming a System User licence seat per client contact.
		"user_type": "Website User" if roles == ["Portal Customer"] else "System User",
		# new_password runs the site Password Policy and strength scoring during insert.
		# frappe.utils.password.update_password(), used previously, bypasses both, so a
		# 6-character password was accepted on a site that requires far more.
		"new_password": password,
	}
	if portal_linked_customer and frappe.get_meta("User").has_field("portal_linked_customer"):
		user_dict["portal_linked_customer"] = portal_linked_customer

	doc = frappe.get_doc(user_dict)
	for role in roles:
		doc.append("roles", {"role": role})

	doc.insert(ignore_permissions=True)

	return {"ok": True, "name": doc.name, "email": email}


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
