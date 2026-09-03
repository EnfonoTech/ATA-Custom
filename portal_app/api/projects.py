from __future__ import annotations

import json
import io
import zipfile

import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate

from erpnext import get_default_company

from portal_app.api import helper


def _normalize_folder_template_path(raw: str) -> str:
	v = cstr(raw or "").strip().replace("\\", "/")
	parts = [p.strip() for p in v.split("/") if p and p.strip()]
	if not parts:
		return ""
	if any(p in (".", "..") for p in parts):
		return ""
	return "/".join(parts)


def _project_fields():
	base = [
		"name",
		"project_name",
		"status",
		"customer",
		"expected_start_date",
		"expected_end_date",
		"estimated_costing",
		"percent_complete",
		"company",
	]
	meta = frappe.get_meta("Project")
	for fn in (
		"portal_project_code",
		"portal_project_manager",
		"portal_kanban_stage",
		"portal_office",
		"portal_phase",
		"portal_project_server",
		"portal_upcoming_milestone",
		"portal_milestone_date",
		"portal_server_t",
		"portal_server_a",
		"portal_server_c",
	):
		if meta.has_field(fn):
			base.append(fn)
	return base


def _assert_may_set_project_manager(project: str, payload: dict) -> None:
	"""Only a System Manager may hand the portal-manager role to someone else.

	portal_project_manager is not a label: helper.can_view_project_value() grants a
	Projects Manager sight of a project's money precisely when this field names them.
	Leaving it writable by any Projects Manager therefore lets them self-grant that
	permission on any project in the portfolio.
	"""
	if payload.get("portal_project_manager") is None:
		return
	if "System Manager" in frappe.get_roles():
		return
	current = frappe.db.get_value("Project", project, "portal_project_manager")
	if current not in (None, "", frappe.session.user):
		frappe.throw(
			_("Only a System Manager can reassign the portal project manager."),
			frappe.PermissionError,
		)


def _assert_may_set_team(project: str, payload: dict) -> None:
	"""A Projects Manager may only put their OWN projects (the ones where they are
	named as portal_project_manager) under a team — not any project in the
	portfolio, even though assert_manage_project already lets them edit any
	project's other fields. System Manager is unrestricted, same as everywhere
	else this two-tier rule shows up (see _assert_may_set_project_manager)."""
	if payload.get("portal_team") is None:
		return
	if "System Manager" in frappe.get_roles():
		return
	manager = frappe.db.get_value("Project", project, "portal_project_manager")
	if manager != frappe.session.user:
		frappe.throw(
			_("Only a System Manager, or the project's own Portal Project Manager, can set its team."),
			frappe.PermissionError,
		)


def _manageable_project_names(allowed_names: list) -> list:
	"""Which of `allowed_names` this caller may CHANGE, in O(1) queries.

	Mirrors helper.can_manage_project without calling it per project (it re-reads the
	Project table each time). Staff manage the whole portfolio; a Projects User manages
	only the projects they are on the team of; customer users manage nothing.
	"""
	# Staff first — Administrator carries the Portal Customer role too.
	if helper.has_portal_staff_project_access():
		return list(allowed_names)
	if helper.user_is_customer_portal_user():
		return []
	member_of = set(helper.project_member_names())
	return [n for n in allowed_names if n in member_of]


def _safe_order_by(sort_by: str, sort_order: str) -> str:
	"""Allowlist the sort inputs before they reach the query.

	Frappe's DatabaseQuery.validate_order_by_and_group_by() does reject sub-queries
	and blacklisted functions, so this is not an injection hole today — but relying on
	the framework's sanitiser as the only defence is fragile, and an unknown column
	otherwise surfaces to the user as a 500. Pin both halves to known values instead.
	"""
	allowed_fields = set(_project_fields()) | {"modified", "creation"}
	field = cstr(sort_by).strip() or "modified"
	if field not in allowed_fields:
		field = "modified"
	direction = "asc" if cstr(sort_order).strip().lower() == "asc" else "desc"
	return field + " " + direction


@frappe.whitelist()
def list_projects(sort_by="modified", sort_order="desc", status=None, customer=None, search=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = helper.get_allowed_project_names()
	if not names:
		return {"projects": []}

	filters = {"name": ["in", names]}
	if status:
		filters["status"] = status
	if customer:
		filters["customer"] = customer

	or_filters = None
	if search:
		or_filters = [
			["project_name", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
		]
		if frappe.get_meta("Project").has_field("portal_project_code"):
			or_filters.append(["portal_project_code", "like", f"%{search}%"])

	projects = frappe.get_all(
		"Project",
		filters=filters,
		or_filters=or_filters,
		fields=_project_fields(),
		order_by=_safe_order_by(sort_by, sort_order),
		limit_page_length=500,
	)
	if not helper.has_portal_staff_project_access():
		for p in projects:
			p.pop("estimated_costing", None)
			p.pop("portal_project_manager", None)
	else:
		value_visible = set(helper.get_value_visible_project_names())
		for p in projects:
			if p["name"] not in value_visible:
				p.pop("estimated_costing", None)
	return {"projects": projects}


@frappe.whitelist()
def get_project(name):
	helper.assert_project_access(name)
	doc = frappe.get_doc("Project", name)
	out = doc.as_dict()
	if not helper.has_portal_staff_project_access():
		out.pop("estimated_costing", None)
		out.pop("portal_project_manager", None)
	elif not helper.can_view_project_value(name):
		out.pop("estimated_costing", None)
	return {"project": out}


@frappe.whitelist()
def portfolio_dashboard():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = helper.get_allowed_project_names()
	if not names:
		return {
			"totals": {"projects": 0, "open_tasks": 0, "estimated_cost": 0},
			"by_status": [],
			"by_kanban": [],
		}

	placeholders = ",".join(["%s"] * len(names))

	status_rows = frappe.db.sql(
		f"""
		SELECT status, COUNT(*) AS c
		FROM `tabProject`
		WHERE name IN ({placeholders})
		GROUP BY status
		""",
		names,
		as_dict=True,
	)

	kf = helper.kanban_fieldname()
	kanban_rows = frappe.db.sql(
		f"""
		SELECT `{kf}` AS stage, COUNT(*) AS c
		FROM `tabProject`
		WHERE name IN ({placeholders})
		GROUP BY `{kf}`
		""",
		names,
		as_dict=True,
	)

	value_names = helper.get_value_visible_project_names()
	cost = 0
	if value_names:
		value_placeholders = ",".join(["%s"] * len(value_names))
		cost = flt(
			frappe.db.sql(
				f"""
				SELECT SUM(estimated_costing) FROM `tabProject`
				WHERE name IN ({value_placeholders})
				""",
				value_names,
			)[0][0]
			or 0
		)

	open_tasks = frappe.db.count(
		"Task",
		{
			"project": ["in", names],
			"status": ["not in", ["Cancelled", "Completed"]],
		},
	)

	return {
		"totals": {
			"projects": len(names),
			"open_tasks": open_tasks,
			"estimated_cost": cost,
		},
		"by_status": status_rows,
		"by_kanban": kanban_rows,
	}


@frappe.whitelist()
def project_dashboard(name):
	helper.assert_project_access(name)

	p = frappe.get_doc("Project", name)
	tasks = frappe.get_all(
		"Task",
		filters={"project": name},
		fields=["name", "subject", "status", "exp_start_date", "exp_end_date", "priority"],
		order_by="modified desc",
		limit_page_length=50,
	)

	kf = helper.kanban_fieldname()
	stage = p.get(kf) or p.get("status")

	cust_display = ""
	if p.get("customer"):
		cust_display = frappe.db.get_value("Customer", p.customer, "customer_name") or p.customer

	# as_dict() ships the whole Project row — unlike list_projects/kanban_board, which
	# only ever SELECT an explicit safe allow-list of fields (_project_fields()), this
	# loads every field including all of ERPNext's built-in costing/billing amounts.
	# Strip every Currency field on the doctype rather than naming them one by one —
	# a hardcoded list silently misses new fields (this one previously missed
	# total_purchase_cost, total_sales_amount and total_consumed_material_cost).
	project_data = p.as_dict()
	if not helper.can_view_project_value(name):
		for df in frappe.get_meta("Project").fields:
			if df.fieldtype == "Currency":
				project_data.pop(df.fieldname, None)
		# Not a Currency field, but a derived percentage of cost — still reveals margin.
		project_data.pop("per_gross_margin", None)
	if not helper.has_portal_staff_project_access():
		project_data.pop("portal_project_manager", None)

	return {
		"project": project_data,
		"tasks": tasks,
		"kanban_stage": stage,
		"customer_display_name": cust_display,
	}


@frappe.whitelist()
def kanban_board():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = helper.get_allowed_project_names()
	if not names:
		return {"columns": [], "field": helper.kanban_fieldname()}

	kf = helper.kanban_fieldname()
	fields = _project_fields()
	projects = frappe.get_all(
		"Project", filters={"name": ["in", names]}, fields=fields, limit_page_length=500
	)

	if not helper.has_portal_staff_project_access():
		for p in projects:
			p.pop("estimated_costing", None)
			p.pop("portal_project_manager", None)
	else:
		value_visible = set(helper.get_value_visible_project_names())
		for p in projects:
			if p["name"] not in value_visible:
				p.pop("estimated_costing", None)

	buckets = {}
	for p in projects:
		key = p.get(kf) or p.get("status") or "Unknown"
		buckets.setdefault(key, []).append(p)

	order = ["Planning", "Active", "On Hold", "Review", "Done", "Open", "Completed", "Cancelled", "Unknown"]
	columns = []
	seen = set()
	for st in order:
		if st in buckets:
			columns.append({"stage": st, "projects": buckets[st]})
			seen.add(st)
	for st in sorted(set(buckets.keys()) - seen):
		columns.append({"stage": st, "projects": buckets[st]})

	return {"columns": columns, "field": kf}


@frappe.whitelist()
def rename_project(project, project_name):
	"""Update Project.project_name (display title). Document name (ID) is unchanged."""
	helper.assert_manage_project(project)
	title = cstr(project_name or "").strip()
	if len(title) < 2:
		frappe.throw(_("Project title is too short"))

	doc = frappe.get_doc("Project", project)
	doc.project_name = title
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "project_name": doc.project_name}


@frappe.whitelist()
def update_project(project, **kwargs):
	"""Update editable project fields from the portal edit modal."""
	helper.assert_manage_project(project)
	_assert_may_set_project_manager(project, kwargs)
	_assert_may_set_team(project, kwargs)
	doc = frappe.get_doc("Project", project)

	for k in (
		"project_name",
		"status",
		"expected_start_date",
		"expected_end_date",
		"percent_complete",
		"notes",
	):
		v = kwargs.get(k)
		if v is not None:
			doc.set(k, v if v != "" else None)

	meta = frappe.get_meta("Project")
	for k in (
		"portal_project_manager",
		"portal_team",
		"portal_kanban_stage",
		"portal_office",
		"portal_phase",
		"portal_server_t",
		"portal_server_a",
		"portal_server_c",
		"portal_upcoming_milestone",
		"portal_milestone_date",
	):
		if meta.has_field(k):
			v = kwargs.get(k)
			if v is not None:
				doc.set(k, v if v != "" else None)

	# Apply the manager field (loop above) before this check, and pass its
	# resulting in-memory value through — so claiming an unassigned project and
	# pricing it in the same save is judged against who the user is about to
	# become, not the stale pre-save manager read from the database.
	if kwargs.get("estimated_costing") is not None and helper.can_view_project_value(
		project, effective_portal_project_manager=doc.portal_project_manager
	):
		v = kwargs.get("estimated_costing")
		doc.set("estimated_costing", v if v != "" else None)

	# The Gantt milestone modal already blocks this client-side, but that's
	# bypassable via a direct API call — enforce it here too, so a milestone
	# label can never be saved without the date it's meant to sit on.
	if meta.has_field("portal_upcoming_milestone") and doc.get("portal_upcoming_milestone") and not doc.get(
		"portal_milestone_date"
	):
		frappe.throw(_("Pick the date this milestone falls on."))

	requested_status = kwargs.get("status")
	doc.save(ignore_permissions=True)

	# ERPNext core's Project.validate() -> update_percent_complete() unconditionally
	# resets status to "Open" (or "Completed" at 100%) unless it's "Cancelled" —
	# clobbering any other status (e.g. "On Hold") we just set. Re-apply the
	# requested value directly, bypassing controller hooks, so it actually sticks.
	if requested_status and requested_status != "Cancelled" and doc.status != requested_status:
		frappe.db.set_value("Project", doc.name, "status", requested_status, update_modified=False)
		doc.status = requested_status

	return {"name": doc.name, "project_name": doc.project_name}


def _resync_upcoming_milestone_summary(doc) -> None:
	"""Keep the legacy single-value portal_upcoming_milestone/portal_milestone_date
	fields (still read by the Projects table's "Upcoming Milestone" column) pointing
	at the soonest not-yet-passed entry in the new portal_milestones list — falling
	back to the most recent past one if every entry is already behind us, so the
	column still shows *something* rather than going blank the day a milestone
	passes. The child table is the source of truth now; these two fields are just a
	denormalized summary other screens read without needing the list themselves."""
	from frappe.utils import getdate, nowdate

	meta = frappe.get_meta("Project")
	if not (meta.has_field("portal_upcoming_milestone") and meta.has_field("portal_milestone_date")):
		return

	rows = sorted(doc.get("portal_milestones") or [], key=lambda m: getdate(m.milestone_date))
	today = getdate(nowdate())
	upcoming = [m for m in rows if getdate(m.milestone_date) >= today]
	chosen = upcoming[0] if upcoming else (rows[-1] if rows else None)

	doc.portal_upcoming_milestone = chosen.title if chosen else ""
	doc.portal_milestone_date = chosen.milestone_date if chosen else None
	frappe.db.set_value(
		"Project",
		doc.name,
		{
			"portal_upcoming_milestone": doc.portal_upcoming_milestone,
			"portal_milestone_date": doc.portal_milestone_date,
		},
		update_modified=False,
	)


@frappe.whitelist()
def add_project_milestone(project, title, milestone_date):
	helper.assert_manage_project(project)
	title = cstr(title).strip()
	if not title:
		frappe.throw(_("Milestone title is required."))
	if not cstr(milestone_date).strip():
		frappe.throw(_("Pick the date this milestone falls on."))

	doc = frappe.get_doc("Project", project)
	doc.append("portal_milestones", {"title": title, "milestone_date": milestone_date})
	doc.save(ignore_permissions=True)
	_resync_upcoming_milestone_summary(doc)
	frappe.db.commit()
	return {"ok": True, "milestones": [m.as_dict() for m in doc.portal_milestones]}


@frappe.whitelist()
def delete_project_milestone(project, row_name):
	helper.assert_manage_project(project)
	doc = frappe.get_doc("Project", project)
	before = len(doc.portal_milestones or [])
	doc.portal_milestones = [m for m in (doc.portal_milestones or []) if m.name != row_name]
	if len(doc.portal_milestones) == before:
		frappe.throw(_("Milestone not found."))
	doc.save(ignore_permissions=True)
	_resync_upcoming_milestone_summary(doc)
	frappe.db.commit()
	return {"ok": True, "milestones": [m.as_dict() for m in doc.portal_milestones]}


@frappe.whitelist()
def get_portal_users():
	"""Return enabled non-guest users for Lead Architect dropdown.

	This is a full user directory (login email + name), so it is staff-only. Every
	caller already tolerates an empty list, so non-staff get [] instead of an error.
	"""
	helper.assert_portal_user()
	if not helper.has_portal_staff_project_access():
		return []
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "name": ["not in", ["Guest", "Administrator"]]},
		fields=["name", "full_name"],
		order_by="full_name asc",
		limit_page_length=200,
	)
	return users


@frappe.whitelist()
def get_portal_folder_template():
	"""Read Portal Project Settings.folder_template (ordered subfolder names for new projects).

	Returns the EFFECTIVE template — falling back to site_config, then the
	built-in default list — not just the raw (possibly empty) DB rows. An
	empty Portal Project Settings table doesn't mean "no template"; it means
	"use the built-in default", and every new project silently gets that
	full default tree regardless. Returning an empty list here made the
	editor show nothing while a complete standard was actually in effect,
	so an admin who saw "empty" and added one row would, on save, replace
	that entire real default with just their one new row for every future
	project — a serious, easy-to-trigger trap. `is_default` tells the
	frontend whether what's shown is this fallback rather than a real
	saved customization, so it can say so instead of implying it's empty.
	"""
	from portal_app.api.files import _folder_template

	helper.assert_can_edit_portal_folder_template()
	stored_rows: list[str] = []
	if frappe.db.exists("DocType", "Portal Project Settings"):
		doc = frappe.get_single("Portal Project Settings")
		for row in sorted(doc.get("folder_template") or [], key=lambda r: int(getattr(r, "idx", 0) or 0)):
			v = cstr(getattr(row, "folder_name", None) or "").strip()
			if v:
				stored_rows.append(v)

	if stored_rows:
		return {"rows": [{"folder_name": v} for v in stored_rows], "is_default": False}

	return {"rows": [{"folder_name": v} for v in _folder_template()], "is_default": True}


@frappe.whitelist()
def save_portal_folder_template(rows=None):
	"""Replace folder template rows (company-wide). Empty list falls back to site config / built-in default."""
	helper.assert_can_edit_portal_folder_template()
	# files._folder_template() memoises on frappe.local for the duration of the request.
	frappe.local._portal_folder_template = None
	if not frappe.db.exists("DocType", "Portal Project Settings"):
		frappe.throw(_("Portal Project Settings is not installed on this site."))

	if isinstance(rows, str):
		rows = json.loads(rows or "[]")
	if not isinstance(rows, list):
		frappe.throw(_("rows must be a list"))

	names = []
	for i, row in enumerate(rows):
		if isinstance(row, str):
			fn = row
		elif isinstance(row, dict):
			fn = row.get("folder_name")
		else:
			fn = None
		v = _normalize_folder_template_path(fn or "")
		if not v:
			continue
		if ".." in v.split("/"):
			frappe.throw(_("Invalid folder path at row {0}: {1}").format(i + 1, v))
		names.append(v)

	if len(names) > 200:
		frappe.throw(_("At most 200 subfolder rows are allowed."))

	seen = set()
	uniq = []
	for n in names:
		key = n.lower()
		if key in seen:
			continue
		seen.add(key)
		uniq.append(n)

	doc = frappe.get_single("Portal Project Settings")
	doc.folder_template = []
	for n in uniq:
		doc.append("folder_template", {"folder_name": n})
	doc.save(ignore_permissions=True)
	return {"ok": True, "rows": [{"folder_name": n} for n in uniq]}


def _finalize_template_paths(paths: set) -> list[str]:
	"""Shared tail end of both the ZIP and folder-picker template imports.

	If every path shares the same first segment (a single root folder wrapping
	the tree), that wrapper is stripped so the template starts from the
	contained folders. Non-leaf paths are dropped because the backend
	auto-creates ancestors when ensuring a leaf path; storing only leaves
	keeps the template list lean and easy to read.
	"""
	if paths:
		roots = {p.split("/", 1)[0] for p in paths}
		if len(roots) == 1:
			only_root = next(iter(roots))
			stripped = {p[len(only_root) + 1 :] for p in paths if "/" in p}
			if stripped:
				paths = {s for s in stripped if s}

	leaves = []
	all_paths = sorted(paths)
	for p in all_paths:
		prefix = p + "/"
		if any(other.startswith(prefix) for other in all_paths):
			continue
		leaves.append(p)

	def sort_key(path: str):
		return [seg.lower() for seg in path.split("/")]

	return sorted(leaves, key=sort_key)


def _collect_template_paths_from_zip_content(content: bytes) -> list[str]:
	"""Extract folder tree from a ZIP. Returns only leaf paths in a stable hierarchical order."""
	try:
		zf = zipfile.ZipFile(io.BytesIO(content))
	except Exception:
		frappe.throw(_("Invalid ZIP file"))
	paths = set()
	for info in zf.infolist():
		name = cstr(info.filename or "").strip().replace("\\", "/")
		if not name or name.startswith("__MACOSX/"):
			continue
		if name.startswith("/") or ":" in name:
			continue
		parts = [p for p in name.split("/") if p not in ("", ".", "..")]
		if not parts:
			continue
		dir_parts = parts if info.is_dir() else parts[:-1]
		if not dir_parts:
			continue
		norm = _normalize_folder_template_path("/".join(dir_parts))
		if norm:
			paths.add(norm)

	return _finalize_template_paths(paths)


@frappe.whitelist()
def import_portal_folder_template_from_paths(paths_json, project=None):
	"""Replace folder template from a flat list of relative file paths — the shape
	produced by a browser's <input webkitdirectory> folder picker (e.g.
	"MyTemplate/AA-FIRST/notes.txt"). Optionally apply now to one project,
	mirroring import_portal_folder_template_zip's own behaviour.

	The Admin page's "pick a folder from my computer" button called this exact
	method name for a real feature, but it was never implemented — every click
	failed with a raw "no attribute" server error instead of importing anything.
	"""
	helper.assert_can_edit_portal_folder_template()
	if isinstance(paths_json, str):
		try:
			raw_paths = json.loads(paths_json or "[]")
		except Exception:
			frappe.throw(_("Invalid paths"))
	else:
		raw_paths = paths_json or []
	if not isinstance(raw_paths, list):
		frappe.throw(_("paths_json must be a list"))

	paths = set()
	for raw in raw_paths:
		name = cstr(raw or "").strip().replace("\\", "/")
		if not name or name.startswith("/") or ":" in name:
			continue
		parts = [p for p in name.split("/") if p not in ("", ".", "..")]
		if len(parts) < 2:
			# A bare filename with no directory segment carries no folder info.
			continue
		norm = _normalize_folder_template_path("/".join(parts[:-1]))
		if norm:
			paths.add(norm)

	if not paths:
		frappe.throw(_("No folders found in the selected directory."))

	rows = _finalize_template_paths(paths)
	save_portal_folder_template(rows=rows)
	applied_project = cstr(project or "").strip()
	if applied_project:
		helper.assert_manage_project(applied_project)
		from portal_app.api.files import ensure_project_folders

		ensure_project_folders(applied_project)
	return {"ok": True, "rows": [{"folder_name": p} for p in rows], "count": len(rows)}


@frappe.whitelist()
def import_portal_folder_template_zip(project=None):
	"""Replace folder template from a ZIP tree. Optionally apply now to one project."""
	helper.assert_can_edit_portal_folder_template()
	upload = frappe.request.files.get("file")
	if not upload:
		frappe.throw(_("ZIP file is required"))
	fname = cstr(getattr(upload, "filename", "") or "").lower()
	if not fname.endswith(".zip"):
		frappe.throw(_("Only .zip files are supported"))
	content = upload.stream.read()
	if not content:
		frappe.throw(_("ZIP file is empty"))
	paths = _collect_template_paths_from_zip_content(content)
	save_portal_folder_template(rows=paths)
	applied_project = cstr(project or "").strip()
	if applied_project:
		helper.assert_manage_project(applied_project)
		from portal_app.api.files import ensure_project_folders

		ensure_project_folders(applied_project)
	return {"ok": True, "rows": [{"folder_name": p} for p in paths], "count": len(paths)}


@frappe.whitelist()
def set_project_stage(project, stage):
	"""Update project stage from portal Kanban board (manager-only)."""
	helper.assert_manage_project(project)

	stage = (stage or "").strip()
	if not stage:
		frappe.throw(_("Stage is required"))

	doc = frappe.get_doc("Project", project)
	fieldname = helper.kanban_fieldname()

	if fieldname == "status":
		doc.status = stage
	else:
		doc.set(fieldname, stage)
	doc.save(ignore_permissions=True)

	return {"ok": True, "project": doc.name, "stage": stage}


@frappe.whitelist()
def get_capabilities():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	settings = helper.get_portal_settings_dict()
	roles = set(frappe.get_roles())
	can_create = bool(settings.get("allow_any_portal_user_to_create_project"))
	if not can_create:
		# Deliberately do NOT fall back to ERPNext's core "Project create" permission —
		# see helper.assert_can_create_project for why. Only these two paths may create.
		if "Projects Manager" in roles or "System Manager" in roles:
			can_create = True

	allowed_names = helper.get_allowed_project_names()
	manageable = _manageable_project_names(allowed_names)
	# Projects where this user is explicitly listed in the Project Users table.
	# Used by the Projects page filter and the Shared-with-me page (so a team
	# member sees the project as part of "what I can access").
	team_member_names: list[str] = []
	if frappe.session.user not in ("Guest", "Administrator"):
		rows = frappe.db.sql(
			"SELECT DISTINCT parent FROM `tabProject User` WHERE user=%s",
			frappe.session.user,
		)
		team_member_names = [r[0] for r in rows if r and r[0] in allowed_names]

	is_customer_portal = helper.user_is_customer_portal_user()
	staff_project_access = helper.has_portal_staff_project_access()
	# Users with Portal Customer + Projects Manager must still get staff UI (manageable list, uploads, etc.)
	effective_customer_portal = is_customer_portal and not staff_project_access

	return {
		"can_create_project": can_create and not effective_customer_portal,
		"manageable_project_names": manageable if not effective_customer_portal else [],
		# Every project the current user is allocated to (project member, manager, or staff).
		# The portal uses this to show upload + share UI to all team members, not just managers.
		"allowed_project_names": allowed_names if not effective_customer_portal else [],
		# Projects where the user appears in the Project Users table — narrower than
		# allowed (excludes manager-via-role overrides). Powers the "I'm a team
		# member" filter on Projects and the Shared-with-me Team membership rows.
		"team_member_project_names": team_member_names if not effective_customer_portal else [],
		"is_customer_portal_user": effective_customer_portal,
		"can_manage_customers": helper.can_manage_customers_in_portal(),
		"can_edit_portal_folder_template": helper.can_edit_portal_folder_template()
		if not effective_customer_portal
		else False,
		"can_manage_teams": helper.can_manage_teams() and not effective_customer_portal,
		# System Manager / Projects Manager only — gates management-level views (Dashboard,
		# Org Chart, Teams) and management-level fields (estimated cost, project manager)
		# away from regular "Projects User" team members.
		"is_manager": staff_project_access,
		"portal_user": frappe.session.user,
	}


@frappe.whitelist()
def create_project(project_name, company=None, **kwargs):
	helper.assert_can_create_project()
	if not (project_name or "").strip():
		frappe.throw(_("Project title is required"))

	company = company or get_default_company()
	if not company:
		frappe.throw(_("Set a default Company or pass company"))

	doc = frappe.get_doc(
		{
			"doctype": "Project",
			"project_name": project_name.strip(),
			"company": company,
			"naming_series": "PROJ-.####",
		}
	)

	for k in ("expected_start_date", "expected_end_date", "customer", "estimated_costing", "status"):
		v = kwargs.get(k)
		if v not in (None, ""):
			doc.set(k, v)

	meta = frappe.get_meta("Project")
	for k in (
		"portal_project_code",
		"portal_project_manager",
		"portal_kanban_stage",
		"portal_phase",
		"portal_office",
	):
		if meta.has_field(k):
			v = kwargs.get(k)
			if v not in (None, ""):
				doc.set(k, v)
			elif k == "portal_kanban_stage":
				doc.set(k, "Planning")

	for k in ("expected_start_date", "expected_end_date"):
		if doc.get(k):
			try:
				doc.set(k, getdate(doc.get(k)))
			except Exception:
				pass

	doc.insert(ignore_permissions=True)
	doc.append("users", {"user": frappe.session.user})
	doc.save(ignore_permissions=True)
	try:
		from portal_app.api.files import ensure_project_folders

		ensure_project_folders(doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Portal: Failed creating project folders")

	return {"name": doc.name, "project_name": doc.project_name}


@frappe.whitelist()
def sync_project_team(project, users):
	helper.assert_manage_project_team(project)
	if isinstance(users, str):
		users = json.loads(users or "[]")
	if not isinstance(users, list):
		frappe.throw(_("users must be a list of user IDs"))

	seen = set()
	clean = []
	for u in users:
		if not u or not isinstance(u, str):
			continue
		u = u.strip()
		if not u or u in seen:
			continue
		if not frappe.db.exists("User", u):
			frappe.throw(_("Unknown user: {0}").format(u))
		if not frappe.db.get_value("User", u, "enabled"):
			frappe.throw(_("User is disabled: {0}").format(u))
		seen.add(u)
		clean.append(u)

	doc = frappe.get_doc("Project", project)
	for row in list(doc.users):
		doc.remove(row)
	for u in clean:
		doc.append("users", {"user": u})
	doc.save(ignore_permissions=True)

	_sync_project_assignment(project, clean)

	return {"ok": True, "users": [row.user for row in doc.users]}


def _sync_project_assignment(project, users):
	"""Mirror Project team membership into Frappe's standard Assign To (ToDo) so the
	portal's Team list and ERP's native "Assigned To" sidebar show the same people.
	Does not touch the Project Users table or any portal access-control logic."""
	import frappe.share as _share
	from frappe.desk.form.assign_to import add as assign_add
	from frappe.desk.form.assign_to import remove as assign_remove

	current = set(
		frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "Project",
				"reference_name": project,
				"status": ["not in", ("Cancelled", "Closed")],
			},
			pluck="allocated_to",
		)
	)
	target = set(users)

	to_add = list(target - current)
	to_remove = current - target
	if not to_add and not to_remove:
		return

	# assign_add() only auto-shares a doc with the assignee when they don't
	# already have read access to it — and that auto-share step checks the
	# CALLING user's own DocPerm "share" permission on Project, which
	# ignore_permissions=True does not bypass (it's a separate, lower-level
	# RBAC check). ERPNext's stock role permissions grant "share" on Project
	# to Projects Manager but not to System Manager, so a pure System Manager
	# caller would hit "No permission to share Project ...".
	#
	# sync_project_team() has already independently verified via
	# assert_manage_project() that this user may manage this specific
	# project, so pre-share it here using frappe.share's own
	# ignore_share_permission flag (the officially supported bypass) instead
	# of swapping frappe.session.user — an earlier version of this fix used
	# frappe.set_user()/restore, which corrupted the CALLING user's own live
	# session because Frappe persists frappe.session.user back to the
	# Session record at the end of the request; that approach is not safe
	# to use mid-request and must not be reintroduced here.
	for u in to_add:
		_share.add_docshare(
			"Project", project, user=u, read=1, flags={"ignore_share_permission": True}
		)

	if to_add:
		assign_add({"doctype": "Project", "name": project, "assign_to": to_add}, ignore_permissions=True)
	for u in to_remove:
		assign_remove("Project", project, u, ignore_permissions=True)


def sync_project_access_from_todo(doc, method=None):
	"""Doc event on ToDo: keep Project Users (portal access) in sync with "Assign To" /
	"Assign To User Group" done from ERP Desk directly on a Project — not just from the
	portal's own Team UI. This is the other direction of _sync_project_assignment, so
	assigning a project from either side has the same effect on both.

	Wrapped defensively: some existing projects have bad link data (e.g. an invalid
	portal_project_manager) that makes Project.save() fail — that must not break the
	underlying ToDo assign/unassign action itself.
	"""
	if doc.reference_type != "Project":
		return
	project = doc.reference_name
	user = doc.allocated_to
	if not project or not user or not frappe.db.exists("Project", project):
		return

	is_active = method != "on_trash" and doc.status not in ("Cancelled", "Closed")

	try:
		proj = frappe.get_doc("Project", project)
		existing = {row.user for row in proj.users}
		if is_active and user not in existing:
			proj.append("users", {"user": user})
			proj.save(ignore_permissions=True)
		elif not is_active and user in existing:
			still_assigned = frappe.db.exists(
				"ToDo",
				{
					"reference_type": "Project",
					"reference_name": project,
					"allocated_to": user,
					"status": ["not in", ("Cancelled", "Closed")],
				},
			)
			if not still_assigned:
				for row in list(proj.users):
					if row.user == user:
						proj.remove(row)
				proj.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			title="sync_project_access_from_todo failed",
			message=frappe.get_traceback(),
		)


@frappe.whitelist()
def search_customers(txt=""):
	"""Customer typeahead. Empty `txt` returns the most recently modified customers
	so the picker can show options as soon as the user clicks the field."""
	helper.assert_can_manage_customers_in_portal()

	txt = (txt or "").strip()
	safe = cstr(txt).replace("%", "").replace("_", "").strip()[:100]

	kwargs = dict(
		fields=["name", "customer_name", "customer_type"],
		limit_page_length=25,
		order_by="modified desc",
	)
	if safe:
		kwargs["or_filters"] = [
			["name", "like", f"%{safe}%"],
			["customer_name", "like", f"%{safe}%"],
		]

	return frappe.get_all("Customer", **kwargs)


@frappe.whitelist()
def create_or_get_customer(customer_name):
	helper.assert_can_manage_customers_in_portal()

	name = (customer_name or "").strip()
	if len(name) < 2:
		frappe.throw(_("Customer name is too short"))

	existing = frappe.db.sql(
		"""
		SELECT name FROM `tabCustomer`
		WHERE lower(customer_name) = lower(%s)
		LIMIT 1
		""",
		name,
	)
	if existing:
		return {"name": existing[0][0], "customer_name": name, "created": False}

	cg, terr = _default_customer_group_and_territory()
	if not cg or not terr:
		frappe.throw(
			_("Set default Customer Group and Territory in Selling Settings, or create masters first."),
		)

	doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": name,
			"customer_group": cg,
			"territory": terr,
		}
	)
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "customer_name": doc.customer_name, "created": True}


def _default_customer_group_and_territory():
	cg = frappe.db.get_single_value("Selling Settings", "customer_group")
	terr = frappe.db.get_single_value("Selling Settings", "territory")
	if not cg:
		row = frappe.db.sql("SELECT name FROM `tabCustomer Group` ORDER BY lft ASC LIMIT 1")
		cg = row[0][0] if row else None
	if not terr:
		row = frappe.db.sql("SELECT name FROM `tabTerritory` ORDER BY lft ASC LIMIT 1")
		terr = row[0][0] if row else None
	return cg, terr


@frappe.whitelist()
def set_project_customer(project, customer=None):
	helper.assert_manage_project(project)

	doc = frappe.get_doc("Project", project)
	cust = (customer or "").strip()
	if cust:
		if not frappe.db.exists("Customer", cust):
			frappe.throw(_("Unknown Customer: {0}").format(cust))
		doc.customer = cust
	else:
		doc.customer = None

	doc.save(ignore_permissions=True)

	cust_display = ""
	if doc.customer:
		cust_display = frappe.db.get_value("Customer", doc.customer, "customer_name") or doc.customer

	return {"ok": True, "customer": doc.customer, "customer_display_name": cust_display}


def _project_customer_required(project):
	cust = frappe.db.get_value("Project", project, "customer")
	if not cust:
		frappe.throw(_("Set a Customer on the project before managing customer portal users."))
	return cust


def _assert_user_eligible_for_customer_link(user, customer):
	helper.ensure_user_portal_linked_customer_field()
	if not frappe.get_meta("User").has_field("portal_linked_customer"):
		frappe.throw(
			_("Could not add field portal_linked_customer on User. Run bench migrate for site {0}.").format(
				getattr(frappe.local, "site", "") or "this site"
			),
			frappe.ValidationError,
		)
	# A customer portal contact must be an external party. Linking an internal user
	# would strip their staff scoping and pin them to one customer's portfolio, and
	# linking Administrator would lock the superuser out of the portal entirely.
	if user in ("Administrator", "Guest"):
		frappe.throw(_("This account cannot be linked as a customer contact."), frappe.PermissionError)
	if helper.has_portal_staff_project_access(user) or frappe.db.exists("Project User", {"user": user}):
		frappe.throw(
			_("This is an internal user and cannot be linked as a customer portal contact:")
			+ " "
			+ cstr(user),
			frappe.PermissionError,
		)

	existing = frappe.db.get_value("User", user, "portal_linked_customer")
	if existing and existing != customer:
		frappe.throw(
			_("User {0} is already linked to another customer ({1}).").format(user, existing),
			frappe.LinkValidationError,
		)


def _attach_portal_customer_user(user, customer):
	helper.ensure_portal_customer_role()
	doc = frappe.get_doc("User", user)
	doc.flags.ignore_permissions = True
	if frappe.get_meta("User").has_field("portal_linked_customer"):
		doc.portal_linked_customer = customer
	has_pc = any(r.role == helper.PORTAL_CUSTOMER_ROLE for r in doc.roles)
	if not has_pc:
		doc.append("roles", {"role": helper.PORTAL_CUSTOMER_ROLE})
	doc.save()


def _detach_portal_customer_user(user, customer):
	if not frappe.get_meta("User").has_field("portal_linked_customer"):
		return
	if frappe.db.get_value("User", user, "portal_linked_customer") != customer:
		return
	doc = frappe.get_doc("User", user)
	doc.flags.ignore_permissions = True
	if frappe.get_meta("User").has_field("portal_linked_customer"):
		doc.portal_linked_customer = None
	for row in list(doc.roles):
		if row.role == helper.PORTAL_CUSTOMER_ROLE:
			doc.remove(row)
	doc.save()


@frappe.whitelist()
def get_customer_portal_users(project):
	helper.assert_manage_project(project)
	cust = _project_customer_required(project)
	helper.ensure_user_portal_linked_customer_field()
	if not frappe.get_meta("User").has_field("portal_linked_customer"):
		return {"users": []}

	users = frappe.get_all(
		"User",
		filters={"portal_linked_customer": cust, "enabled": 1},
		fields=["name", "full_name", "email"],
		order_by="name asc",
		limit_page_length=200,
	)
	return {"users": users}


@frappe.whitelist()
def sync_customer_portal_users(project, users):
	helper.assert_manage_project(project)
	helper.ensure_portal_customer_role()
	helper.ensure_user_portal_linked_customer_field()
	cust = _project_customer_required(project)

	if isinstance(users, str):
		users = json.loads(users or "[]")
	if not isinstance(users, list):
		frappe.throw(_("users must be a list of user IDs"))

	seen = set()
	new_list = []
	for u in users:
		if not u or not isinstance(u, str):
			continue
		u = u.strip()
		if not u or u in seen:
			continue
		if not frappe.db.exists("User", u):
			frappe.throw(_("Unknown user: {0}").format(u))
		if not frappe.db.get_value("User", u, "enabled"):
			frappe.throw(_("User is disabled: {0}").format(u))
		seen.add(u)
		new_list.append(u)

	new_set = set(new_list)
	old_set = set(
		frappe.get_all(
			"User",
			filters={"portal_linked_customer": cust},
			pluck="name",
		)
	)

	for u in new_set - old_set:
		# Mutating an existing account's roles is a User write, not a project action.
		if not frappe.has_permission("User", "write", user=frappe.session.user):
			frappe.throw(_("You are not allowed to modify user accounts."), frappe.PermissionError)
		_assert_user_eligible_for_customer_link(u, cust)
		_attach_portal_customer_user(u, cust)

	for u in old_set - new_set:
		_detach_portal_customer_user(u, cust)

	return {"ok": True, "users": sorted(new_set)}


@frappe.whitelist()
def create_customer_portal_user_from_project(project, email, full_name, password=None):
	helper.assert_manage_project(project)
	# Managing a project is not authority to mint a login on the ERPNext site.
	if not frappe.has_permission("User", "create", user=frappe.session.user):
		frappe.throw(_("You are not allowed to create user accounts."), frappe.PermissionError)
	helper.ensure_portal_customer_role()
	helper.ensure_user_portal_linked_customer_field()
	cust = _project_customer_required(project)

	email = cstr(email).strip().lower()
	full_name = cstr(full_name).strip()
	password = cstr(password)

	if not email or not full_name:
		frappe.throw(_("Valid email and full name are required"))

	if frappe.db.exists("User", email):
		_assert_user_eligible_for_customer_link(email, cust)
		_attach_portal_customer_user(email, cust)
		return {"name": email, "email": email, "attached": True, "created": False}

	parts = full_name.split(None, 1)
	first_name = parts[0]
	last_name = parts[1] if len(parts) > 1 else ""

	user_dict = {
		"doctype": "User",
		"email": email,
		"first_name": first_name,
		"last_name": last_name,
		"enabled": 1,
		# No password supplied -> send the standard welcome/set-password email instead
		# of having a manager choose someone else's credential.
		"send_welcome_email": 0 if password else 1,
		"user_type": "Website User",
	}
	if frappe.get_meta("User").has_field("portal_linked_customer"):
		user_dict["portal_linked_customer"] = cust
	if password:
		# new_password runs Frappe's own password policy and strength scoring on insert.
		# frappe.utils.password.update_password(), used previously, bypasses both.
		user_dict["new_password"] = password

	doc = frappe.get_doc(user_dict)
	doc.append("roles", {"role": helper.PORTAL_CUSTOMER_ROLE})
	doc.flags.ignore_permissions = True
	doc.insert()

	return {"name": doc.name, "email": email, "created": True, "attached": True}


@frappe.whitelist()
def search_portal_users(txt=""):
	if not helper.user_can_use_portal():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if helper.user_is_customer_portal_user() and not helper.has_portal_staff_project_access():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	txt = (txt or "").strip()
	safe = cstr(txt).replace("%", "").replace("_", "").strip()[:100]
	filters = [
		["enabled", "=", 1],
		["name", "not in", ["Guest", "Administrator"]],
	]
	kwargs = dict(
		filters=filters,
		fields=["name", "full_name", "email", "user_image"],
		limit_page_length=25,
		order_by="full_name asc",
	)
	if safe:
		# Match by username (User.name = email), email, or full name so users can be
		# found by however they're known — display name, login, or address.
		kwargs["or_filters"] = [
			["name", "like", f"%{safe}%"],
			["email", "like", f"%{safe}%"],
			["full_name", "like", f"%{safe}%"],
		]

	return frappe.get_all("User", **kwargs)


@frappe.whitelist()
def search_projects(query=""):
	"""Project combobox for the Tasks quick-create form — scoped to projects the
	caller can create tasks in (same rule create_task enforces)."""
	allowed_names = helper.get_allowed_project_names()
	manageable = _manageable_project_names(allowed_names)
	if not manageable:
		return []

	query = (query or "").strip()
	safe = cstr(query).replace("%", "").replace("_", "").strip()[:100]
	filters = {"name": ["in", manageable]}
	or_filters = None
	if safe:
		or_filters = [
			["project_name", "like", f"%{safe}%"],
			["name", "like", f"%{safe}%"],
		]
		if frappe.get_meta("Project").has_field("portal_project_code"):
			or_filters.append(["portal_project_code", "like", f"%{safe}%"])

	fields = ["name", "project_name"]
	if frappe.get_meta("Project").has_field("portal_project_code"):
		fields.append("portal_project_code")

	return frappe.get_all(
		"Project",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="project_name asc",
		limit_page_length=25,
	)


@frappe.whitelist()
def search_assignable_users(query=""):
	"""Assignee combobox for the Tasks quick-create form."""
	return search_portal_users(query)


def _task_is_assigned_to_user(task_name: str, user: str) -> bool:
	val = frappe.db.get_value("Task", task_name, "_assign") or ""
	return f'"{user}"' in cstr(val)


def _assert_task_access(task_name: str) -> str:
	project = frappe.db.get_value("Task", task_name, "project")
	if not project:
		frappe.throw(_("Task has no linked project"), frappe.PermissionError)
	helper.assert_project_access(project)
	return project


@frappe.whitelist()
def list_tasks(status=None, priority=None, project=None, search=None, only_mine=0):
	"""Task workspace feed (FR-TM-001/002/003): filters + my tasks + project scope."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	allowed = helper.get_allowed_project_names()
	if not allowed:
		return {"tasks": [], "summary": {"total": 0, "open": 0, "overdue": 0}}

	filters = {"project": ["in", allowed]}
	if status:
		filters["status"] = status
	if priority:
		filters["priority"] = priority
	if project and project in allowed:
		filters["project"] = project

	or_filters = None
	safe = cstr(search).replace("%", "").replace("_", "").strip()[:120]
	if safe:
		or_filters = [
			["name", "like", f"%{safe}%"],
			["subject", "like", f"%{safe}%"],
		]

	if int(only_mine or 0):
		filters["_assign"] = ["like", f'%"{frappe.session.user}"%']

	tasks = frappe.get_all(
		"Task",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name",
			"subject",
			"project",
			"status",
			"priority",
			"progress",
			"exp_start_date",
			"exp_end_date",
			"expected_time",
			"_assign",
		],
		order_by="exp_end_date asc, modified desc",
		limit_page_length=500,
	)

	today = getdate()
	overdue = 0
	open_count = 0
	for t in tasks:
		st = cstr(t.get("status"))
		is_closed = st in ("Completed", "Cancelled")
		if not is_closed:
			open_count += 1
		if t.get("exp_end_date") and not is_closed:
			try:
				if getdate(t.exp_end_date) < today:
					overdue += 1
			except Exception:
				pass

	mine_open = frappe.get_all(
		"Task",
		filters={
			"project": ["in", allowed],
			"_assign": ["like", f'%"{frappe.session.user}"%'],
			"status": ["not in", ["Completed", "Cancelled"]],
		},
		fields=["name", "subject", "project", "status", "priority", "progress", "exp_end_date"],
		order_by="exp_end_date asc, modified desc",
		limit_page_length=8,
	)

	return {
		"tasks": tasks,
		"summary": {"total": len(tasks), "open": open_count, "overdue": overdue},
		"mine_open": mine_open,
	}


@frappe.whitelist()
def update_task(task, status=None, priority=None, progress=None, exp_start_date=None, exp_end_date=None):
	"""Inline task updates with access control for portal task board."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if helper.user_is_customer_portal_user() and not helper.has_portal_staff_project_access():
		frappe.throw(_("Customer portal users have view-only task access."), frappe.PermissionError)

	task = (task or "").strip()
	if not task:
		frappe.throw(_("Task is required"))
	project = _assert_task_access(task)

	can_edit = helper.can_manage_project(project) or _task_is_assigned_to_user(task, frappe.session.user)
	if not can_edit:
		frappe.throw(
			_("Only project managers or assigned users can update this task."), frappe.PermissionError
		)

	doc = frappe.get_doc("Task", task)
	if status not in (None, ""):
		doc.status = status
	if priority not in (None, ""):
		doc.priority = priority
	if progress not in (None, ""):
		try:
			p = float(progress)
		except Exception:
			frappe.throw(_("Progress must be numeric"))
		doc.progress = max(0, min(100, p))
	if exp_start_date not in (None, ""):
		doc.exp_start_date = getdate(exp_start_date)
	if exp_end_date not in (None, ""):
		doc.exp_end_date = getdate(exp_end_date)

	doc.save(ignore_permissions=True)
	return {"ok": True, "task": doc.name}


@frappe.whitelist()
def list_task_comments(task):
	"""Read-only thread for a Task. Anyone with access to the task's project can see them."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	task = cstr(task or "").strip()
	if not task:
		return {"comments": []}
	_assert_task_access(task)
	rows = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Task",
			"reference_name": task,
			"comment_type": "Comment",
		},
		fields=["name", "owner", "creation", "content"],
		order_by="creation asc",
		limit_page_length=200,
		ignore_permissions=True,
	)
	# Hydrate owner full name for nicer display.
	users = {r["owner"] for r in rows if r.get("owner")}
	user_meta = {}
	if users:
		for u in frappe.get_all(
			"User",
			filters={"name": ["in", list(users)]},
			fields=["name", "full_name", "user_image"],
			ignore_permissions=True,
		):
			user_meta[u["name"]] = u
	for r in rows:
		meta = user_meta.get(r.get("owner")) or {}
		r["author_full_name"] = meta.get("full_name")
		r["author_image"] = meta.get("user_image")
	return {"comments": rows}


@frappe.whitelist()
def add_task_comment(task, content):
	"""Append a comment to a Task using Frappe's built-in Comment doctype."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if helper.user_is_customer_portal_user() and not helper.has_portal_staff_project_access():
		frappe.throw(_("Customer portal users have view-only task access."), frappe.PermissionError)
	task = cstr(task or "").strip()
	body = cstr(content or "").strip()
	if not task or not body:
		frappe.throw(_("Task and content are required."))
	_assert_task_access(task)
	can_edit = helper.can_manage_project(
		frappe.db.get_value("Task", task, "project")
	) or _task_is_assigned_to_user(task, frappe.session.user)
	if not can_edit:
		frappe.throw(
			_("Only project managers or assigned users can comment on this task."),
			frappe.PermissionError,
		)
	if len(body) > 5000:
		body = body[:5000]
	doc = frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": "Task",
			"reference_name": task,
			"content": body,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True, "name": doc.name}


@frappe.whitelist()
def create_task(project, subject, status="Open", priority="Medium", exp_end_date=None):
	"""Quick-create a Task on a project the caller can manage.

	Restricted to project managers (Portal Project Manager / Projects Manager / System
	Manager) — collaborators can update tasks but creating new ones is a manager action.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	subject = cstr(subject or "").strip()
	if not subject:
		frappe.throw(_("Subject is required."))
	project = cstr(project or "").strip()
	if not project:
		frappe.throw(_("Pick a project for this task."))
	helper.assert_manage_project(project)

	allowed_statuses = {"Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled"}
	allowed_priorities = {"Low", "Medium", "High", "Urgent"}
	doc = frappe.get_doc(
		{
			"doctype": "Task",
			"subject": subject[:140],
			"project": project,
			"status": status if status in allowed_statuses else "Open",
			"priority": priority if priority in allowed_priorities else "Medium",
			"exp_end_date": exp_end_date or None,
			"is_group": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"ok": True,
		"name": doc.name,
		"subject": doc.subject,
		"project": doc.project,
		"status": doc.status,
		"priority": doc.priority,
	}


def _calendar_title_matches(search_l: str, title: str | None, extra: str | None = None) -> bool:
	if not search_l:
		return True
	title = (title or "").lower()
	extra = (extra or "").lower()
	return search_l in title or search_l in extra


def _cal_norm(d):
	if not d:
		return None
	try:
		return getdate(d)
	except Exception:
		return None


def _project_calendar_range(p) -> tuple:
	"""Use expected start/end; if missing, fall back to actual dates (often filled when expected is blank)."""
	es, ee = _cal_norm(p.get("expected_start_date")), _cal_norm(p.get("expected_end_date"))
	as_, ae = _cal_norm(p.get("actual_start_date")), _cal_norm(p.get("actual_end_date"))
	start = es or as_
	end = ee or ae
	if not start and not end:
		return None, None
	if not start:
		start = end
	if not end:
		end = start
	if end < start:
		end = start
	return start, end


def _task_calendar_range(t) -> tuple:
	"""Expected task dates, then actual, then closing date as a single-day anchor."""
	es, ee = _cal_norm(t.get("exp_start_date")), _cal_norm(t.get("exp_end_date"))
	as_, ae = _cal_norm(t.get("act_start_date")), _cal_norm(t.get("act_end_date"))
	closing = _cal_norm(t.get("closing_date"))
	start = es or as_
	end = ee or ae or (closing if not start and closing else None)
	if not start and not end:
		return None, None
	if not start:
		start = end
	if not end:
		end = start
	if end < start:
		end = start
	return start, end


@frappe.whitelist()
def calendar_events(search=None, type_filter="all", project=None):
	"""Calendar feed with optional search (title / id), type (all|project|task), and project scope."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = helper.get_allowed_project_names()
	if not names:
		return {"events": [], "projects": []}

	project_pick = (cstr(project) or "").strip()
	if project_pick and project_pick not in names:
		project_pick = ""

	active_names = [project_pick] if project_pick else names

	project_options = frappe.get_all(
		"Project",
		filters={"name": ["in", names]},
		fields=["name", "project_name"],
		order_by="project_name asc",
	)

	tf = (cstr(type_filter) or "all").strip().lower()
	if tf not in ("all", "project", "task"):
		tf = "all"

	search_l = cstr(search).replace("%", "").replace("_", "").strip().lower()[:120]

	events = []

	if tf in ("all", "project"):
		for p in frappe.get_all(
			"Project",
			filters={"name": ["in", active_names]},
			fields=[
				"name",
				"project_name",
				"expected_start_date",
				"expected_end_date",
				"actual_start_date",
				"actual_end_date",
				"status",
			],
		):
			start, end = _project_calendar_range(p)
			if not start:
				continue
			title = p.project_name or p.name
			if not _calendar_title_matches(search_l, title, p.name):
				continue
			events.append(
				{
					"id": p.name,
					"title": title,
					"start": str(start),
					"end": str(end),
					"extendedProps": {
						"project": p.name,
						"status": p.status,
						"type": "project",
					},
				}
			)

	if tf in ("all", "task"):
		tasks = frappe.get_all(
			"Task",
			filters={"project": ["in", active_names]},
			fields=[
				"name",
				"subject",
				"project",
				"exp_start_date",
				"exp_end_date",
				"act_start_date",
				"act_end_date",
				"closing_date",
				"status",
			],
			limit_page_length=500,
		)
		for t in tasks:
			start, end = _task_calendar_range(t)
			if not start:
				continue
			title = t.subject or t.name
			if not _calendar_title_matches(search_l, title, t.name):
				continue
			events.append(
				{
					"id": f"task-{t.name}",
					"title": title,
					"start": str(start),
					"end": str(end),
					"extendedProps": {
						"project": t.project,
						"type": "task",
						"status": t.status,
						"task": t.name,
					},
				}
			)

	return {"events": events, "projects": project_options}


@frappe.whitelist()
def delete_project(project):
	helper.assert_manage_project(project)
	frappe.delete_doc("Project", project, ignore_permissions=True)
	return {"deleted": project}
