from __future__ import annotations

import json
import io
import zipfile

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, cstr, escape_html, flt, getdate, now_datetime, validate_email_address

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
	):
		if meta.has_field(fn):
			base.append(fn)
	return base


# Batch C: the old server-link fields moved to Portal Project Link (api/links.py), which
# only sends a path / URL to someone who may open it. The columns still exist on the
# Project (a not-yet-migrated site may still hold values), so they are removed from every
# project payload.
_LEGACY_LINK_FIELDS = ("portal_server_t", "portal_server_a", "portal_server_c")


def _strip_legacy_links(project_dict: dict) -> None:
	for key in _LEGACY_LINK_FIELDS:
		project_dict.pop(key, None)


def _attach_portal_links(projects: list) -> None:
	"""portal_links on each project row (links.links_for_projects: two queries in all).
	A client contact gets no key at all."""
	from portal_app.api import links

	by_project = links.links_for_projects([p["name"] for p in projects])
	for p in projects:
		if p["name"] in by_project:
			p["portal_links"] = by_project[p["name"]]


def _strip_internal_people(project_dict: dict) -> None:
	"""For client contacts: drop the team roster and every owner / modified_by, on the
	Project and on its child rows (e.g. milestones), which carry staff login emails."""
	for key in ("users", "owner", "modified_by"):
		project_dict.pop(key, None)
	for value in project_dict.values():
		if isinstance(value, list):
			for row in value:
				if isinstance(row, dict):
					row.pop("owner", None)
					row.pop("modified_by", None)


def refuse_client_project_todo(doc, method=None):
	"""doc_events ToDo.validate: a Desk "Assign To" on a Project for a client contact.
	frappe.desk.form.assign_to.add inserts this ToDo BEFORE it shares the Project with
	an assignee who cannot read it, so refusing here also prevents that share (which
	would let the contact read the whole Project record, possibly another customer's)."""
	if doc.reference_type != "Project" or not doc.allocated_to or doc.status in ("Cancelled", "Closed"):
		return
	if helper.is_customer_only(doc.allocated_to):
		frappe.throw(
			_("Client contacts cannot be assigned to a project. Use Customer portal users on the project page."),
			frappe.PermissionError,
		)


def refuse_client_project_users(doc, method=None):
	"""doc_events Project.validate: no client contact in the Project Users table (Desk
	edits included). A row there is internal team membership."""
	for row in doc.get("users") or []:
		if row.user and helper.is_customer_only(row.user):
			frappe.throw(
				_("Client contacts cannot be on the project team: {0}").format(row.user), frappe.PermissionError
			)


def sync_office_from_team(doc, method=None):
	"""doc_events Project.validate: the office is the team's office.

	ATA treats office and team as one choice, so `portal_office` is no longer typed in;
	it follows `portal_team` (Department.portal_office) on every save — portal, Desk
	or import. A project with no team has no office."""
	meta = frappe.get_meta("Project")
	if not (meta.has_field("portal_team") and meta.has_field("portal_office")):
		return
	team = doc.get("portal_team")
	doc.portal_office = frappe.db.get_value("Department", team, "portal_office") if team else None


def _lead_assignable_project_names(user=None) -> set:
	"""Projects a Department Coordinator (any project they can see) or a Team Manager (a
	project of their teams) may name the Project Lead of (_assert_may_set_project_manager).
	They are shown portal_project_manager on those, so they can see and clear it; it is a
	login id, the money stays behind can_view_project_value."""
	user = user or frappe.session.user
	if helper.is_customer_only(user):
		return set()
	names = set()
	if helper.is_dept_coordinator(user):
		names |= set(helper.get_allowed_project_names(user))
	if helper.is_team_manager(user):
		names |= helper.get_scope_project_names(user)
	return names


def _drop_unchanged_project_manager(project: str, payload: dict) -> None:
	"""Re-sending the current Lead Architect is not a change; neither is a blank from a
	caller who is never shown the field (list_projects strips it for non-staff).
	Without this, every Edit-modal save from a non-System-Manager was refused, and a
	team member's save would have cleared the lead."""
	if "portal_project_manager" not in payload:
		return
	new = cstr(payload.get("portal_project_manager")).strip() or None
	current = frappe.db.get_value("Project", project, "portal_project_manager") or None
	if new == current or (
		new is None
		and not helper.has_portal_staff_project_access()
		and project not in _lead_assignable_project_names()
	):
		payload.pop("portal_project_manager")


def _assert_may_set_project_manager(project: str, payload: dict) -> None:
	"""Who may name (or clear) a project's Project Lead (portal_project_manager).

	portal_project_manager is not a label: helper.can_view_project_value() shows a
	project's money to the person it names. A Super Admin is unrestricted. A Department
	Admin may name anyone else or clear it, but may not take the role over from somebody
	else (that would be a way to unlock the project's money). A Department Coordinator
	(any project they can see) and a Team Manager (a project of their teams) may name or
	replace anyone who can see the project, or clear it, with the same rule about
	themselves. Everyone else can only claim an unassigned project for themselves.
	"""
	if payload.get("portal_project_manager") is None:
		return
	new_pm = cstr(payload.get("portal_project_manager")).strip()
	if new_pm and helper.is_customer_only(new_pm):
		frappe.throw(_("A client contact cannot be the Project Lead."), frappe.PermissionError)
	if helper.is_super_admin():
		return
	user = frappe.session.user
	current = frappe.db.get_value("Project", project, "portal_project_manager")
	if helper.is_dept_admin():
		if new_pm == user and current not in (None, "", user):
			frappe.throw(
				_("Ask a Super Admin to make you the Project Lead of a project somebody else leads."),
				frappe.PermissionError,
			)
		return
	if project in _lead_assignable_project_names(user):
		if new_pm == user and current not in (None, "", user):
			frappe.throw(
				_("Ask a Super Admin to make you the Project Lead of a project somebody else leads."),
				frappe.PermissionError,
			)
		if new_pm and project not in helper.get_allowed_project_names(new_pm):
			frappe.throw(
				_("{0} cannot see this project, so cannot be its Project Lead.").format(new_pm),
				frappe.PermissionError,
			)
		return
	if current not in (None, "", user):
		frappe.throw(
			_("Only a Super Admin, a Department Admin, a Department Coordinator or a Team Manager can reassign the Project Lead."),
			frappe.PermissionError,
		)


def _team_scope(units) -> set:
	"""The teams of these units (helper.teams_of_unit for each)."""
	out = set()
	for unit in units or []:
		out |= set(helper.teams_of_unit(unit))
	return out


def _assert_may_set_team(project: str, payload: dict) -> None:
	"""Which team a project belongs to (portal_team). A Super Admin is unrestricted; a
	Department Admin may only put it under a team of a unit they administer (or clear it),
	so they cannot push a project into somebody else's scope; a Department Coordinator the
	same with their departments' teams, and may only take it from a team of theirs (or
	from no team); the project's own Project Lead keeps the right they always had. A Team
	Manager does not re-allocate projects."""
	if payload.get("portal_team") is None:
		return
	team = cstr(payload.get("portal_team")).strip()
	if helper.is_super_admin():
		return
	is_admin = helper.is_dept_admin()
	is_coordinator = helper.is_dept_coordinator()
	if is_admin and (not team or team in _team_scope(helper.admin_department_names())):
		return
	if is_coordinator:
		mine = _team_scope(helper.coordinator_department_names())
		current = frappe.db.get_value("Project", project, "portal_team")
		if (not current or current in mine) and (not team or team in mine):
			return
	if is_admin or is_coordinator:
		frappe.throw(
			_("You can only put a project under one of your own department's teams."),
			frappe.PermissionError,
		)
	manager = frappe.db.get_value("Project", project, "portal_project_manager")
	if manager != frappe.session.user:
		frappe.throw(
			_("Only a Super Admin, a Department Admin, a Department Coordinator, or the project's own Project Lead can set its team."),
			frappe.PermissionError,
		)


def _assert_may_set_team_on_create(team: str) -> None:
	"""A new project has no Project Lead yet, so only the department rule of
	_assert_may_set_team applies: a Super Admin may pick any team, a Department Admin or
	Department Coordinator one of their units' teams. The team also decides who can see
	the project."""
	if not frappe.db.exists("Department", team):
		frappe.throw(_("Unknown team: {0}").format(team))
	if helper.is_super_admin():
		return
	if helper.is_dept_admin() and team in _team_scope(helper.admin_department_names()):
		return
	if helper.is_dept_coordinator() and team in _team_scope(helper.coordinator_department_names()):
		return
	frappe.throw(
		_("Only a Super Admin, or a Department Admin or Department Coordinator of that team, can create a project under it."),
		frappe.PermissionError,
	)


def _manageable_project_names(allowed_names: list) -> list:
	"""Which of `allowed_names` this caller may CHANGE, in O(1) queries
	(see helper.get_manageable_project_names)."""
	return helper.get_manageable_project_names(allowed=allowed_names)


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
		lead_assignable = _lead_assignable_project_names()
		for p in projects:
			p.pop("estimated_costing", None)
			if p["name"] not in lead_assignable:
				p.pop("portal_project_manager", None)
	else:
		value_visible = set(helper.get_value_visible_project_names())
		for p in projects:
			if p["name"] not in value_visible:
				p.pop("estimated_costing", None)
	for p in projects:
		_strip_legacy_links(p)
	_attach_portal_links(projects)
	return {"projects": projects}


@frappe.whitelist()
def get_project(name):
	helper.assert_project_access(name)
	doc = frappe.get_doc("Project", name)
	out = doc.as_dict()
	# Same rule as project_dashboard: strip EVERY Currency field (and the margin %),
	# not just estimated_costing — as_dict() carries all of ERPNext's billing amounts.
	if not helper.can_view_project_value(name):
		for df in frappe.get_meta("Project").fields:
			if df.fieldtype == "Currency":
				out.pop(df.fieldname, None)
		out.pop("per_gross_margin", None)
	if not helper.has_portal_staff_project_access() and name not in _lead_assignable_project_names():
		out.pop("portal_project_manager", None)
	_strip_legacy_links(out)
	if helper.is_customer_only():
		# Team roster (login emails) and audit users are internal.
		_strip_internal_people(out)
		return {"project": out}
	from portal_app.api import links

	return {
		"project": out,
		"portal_links": links.links_for_projects([name]).get(name, []),
		"can_manage_links": 1 if helper.can_manage_project_links(name) else 0,
	}


@frappe.whitelist()
def portfolio_dashboard():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	helper.assert_not_customer_only()

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
	if not helper.has_portal_staff_project_access() and name not in _lead_assignable_project_names():
		project_data.pop("portal_project_manager", None)
	_strip_legacy_links(project_data)
	if helper.is_customer_only():
		_strip_internal_people(project_data)

	# Tasks are ATA's internal work breakdown; client contacts do not get them here
	# either (the Tasks page and APIs refuse them).
	if helper.is_customer_only():
		tasks = []

	out = {
		"project": project_data,
		"tasks": tasks,
		"kanban_stage": stage,
		"customer_display_name": cust_display,
		# What this caller may do to the project's team (the Team card shows the matching buttons).
		"team_rights": {
			"can_add": helper.can_add_project_members(name),
			"can_remove": helper.can_remove_project_members(name),
		},
	}
	if not helper.is_customer_only():
		from portal_app.api import links

		out["portal_links"] = links.links_for_projects([name]).get(name, [])
		out["can_manage_links"] = 1 if helper.can_manage_project_links(name) else 0
	return out


@frappe.whitelist()
def kanban_board():
	helper.assert_not_customer_only()
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
	for p in projects:
		_strip_legacy_links(p)
	_attach_portal_links(projects)

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
	_drop_unchanged_project_manager(project, kwargs)
	_assert_may_set_project_manager(project, kwargs)
	_assert_may_set_team(project, kwargs)
	doc = frappe.get_doc("Project", project)
	prev_status = doc.status
	status_options = (frappe.get_meta("Project").get_field("status").options or "").split("\n")

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
		"portal_phase",
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

	# Callers that do not send a status (the Edit modal now sends only changed fields;
	# the team and Lead Architect savers never did) must not lose a portal-only status
	# such as "On Hold": ERPNext's validate() resets anything but Cancelled to Open /
	# Completed. Core values are left to ERPNext so 100% still auto-completes.
	requested_status = kwargs.get("status") or (prev_status if prev_status not in status_options else None)
	if doc.status and doc.status not in status_options:
		# A portal-only status would fail the Select check when the % Complete method is
		# Manual (validate() leaves it alone); the requested value is re-applied below.
		doc.status = "Open"
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
	filters = {"enabled": 1, "name": ["not in", ["Guest", "Administrator"]]}
	if not helper.has_portal_staff_project_access():
		# A Department Coordinator or Team Manager sets the Project Lead too, so they
		# need the picker; they get internal staff only, never client logins.
		# update_project still decides who may be set on which project.
		if not (helper.coordinator_department_names() or helper.led_department_names()):
			return []
		filters["user_type"] = "System User"
	users = frappe.get_all(
		"User",
		filters=filters,
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
	can_create = bool(settings.get("allow_any_portal_user_to_create_project"))
	if not can_create:
		# Deliberately do NOT fall back to ERPNext's core "Project create" permission —
		# see helper.assert_can_create_project for why. Only these two paths may create.
		if helper.has_portal_staff_project_access():
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
	# An admin who also carries the client role must still get the admin UI (manageable list, uploads, etc.)
	effective_customer_portal = is_customer_portal and not staff_project_access
	portal_role = helper.get_portal_role()

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
		# A Super Admin manages every team, a Department Admin the departments they
		# administer (see teams.get_org_chart for the per-team flags). A Team Manager does not
		# manage the team itself: they assign people to projects from the Org Chart.
		"can_manage_teams": helper.can_manage_teams() and not effective_customer_portal,
		# Super Admin / Department Admin only: management-level views (Dashboard, Teams)
		# and management-level fields (estimated cost, Project Lead).
		"is_manager": staff_project_access,
		"portal_user": frappe.session.user,
		# The portal role keys: super_admin, department_admin, department_coordinator,
		# team_lead (Team Manager), project_lead, team_member (Project Architect),
		# client_customer (see helper.get_portal_role).
		"portal_role": portal_role,
		"portal_role_label": helper.ROLE_LABELS.get(portal_role, ""),
		"is_super_admin": helper.is_super_admin(),
		"is_department_admin": helper.is_dept_admin(),
		"is_team_lead": helper.is_team_lead(),
		"is_team_manager": helper.is_team_manager(),
		"is_department_coordinator": helper.is_dept_coordinator(),
		"coordinator_department_names": helper.coordinator_department_names() if helper.is_dept_coordinator() else [],
		"portal_role_designations": helper.get_portal_designations(),
		# Who may name / replace a project's Project Lead (see _assert_may_set_project_manager).
		"can_assign_project_lead": not effective_customer_portal
		and (
			helper.is_super_admin()
			or helper.is_dept_admin()
			or helper.is_dept_coordinator()
			or helper.is_team_manager()
		),
		"can_view_org_chart": helper.can_view_org_chart(),
		# Change someone's role from the Org Chart (the server decides, team by team).
		"can_edit_org_roles": staff_project_access and not effective_customer_portal,
		"can_reset_passwords": staff_project_access and not effective_customer_portal,
		"admin_team_names": helper.admin_department_names() if helper.is_dept_admin() else [],
		"led_team_names": helper.led_department_names() if helper.is_team_lead() else [],
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
	):
		if meta.has_field(k):
			v = kwargs.get(k)
			if v not in (None, ""):
				doc.set(k, v)
			elif k == "portal_kanban_stage":
				doc.set(k, "Planning")

	team = cstr(kwargs.get("portal_team")).strip()
	if team and meta.has_field("portal_team"):
		_assert_may_set_team_on_create(team)
		doc.set("portal_team", team)

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


def _clean_team_users(users) -> list[str]:
	"""Validate a list of logins that are about to join a project team."""
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
		# A Project Users row makes someone an internal team member (whole file tree via
		# Shared, a Project DocShare). Client contacts get access through Customer
		# portal users instead.
		if helper.is_customer_only(u):
			frappe.throw(
				_("Client contacts cannot be added to the project team: {0}").format(u), frappe.PermissionError
			)
		if u in ("Administrator", "Guest"):
			frappe.throw(_("This account cannot be on a project team."), frappe.PermissionError)
		seen.add(u)
		clean.append(u)
	return clean


def _apply_project_team(project: str, new_users: list[str]) -> dict:
	"""Set the project's team to `new_users`, checking the right to add and the right to
	remove SEPARATELY (a Team Lead or Lead Architect may add people, only a Super Admin or
	Department Admin may take people off)."""
	doc = frappe.get_doc("Project", project)
	current = [row.user for row in doc.users]
	added = [u for u in new_users if u not in current]
	removed = [u for u in current if u not in new_users]
	if added and not helper.can_add_project_members(project):
		frappe.throw(
			_("You cannot add people to this project's team. Ask a Team Manager, Department Coordinator, Department Admin or Super Admin."),
			frappe.PermissionError,
		)
	if removed and not helper.can_remove_project_members(project):
		frappe.throw(
			_("Only a Super Admin, a Department Admin or a Department Coordinator can remove people from a project team."),
			frappe.PermissionError,
		)
	if not added and not removed:
		return {"ok": True, "users": current, "added": [], "removed": []}
	for row in list(doc.users):
		if row.user in removed:
			doc.remove(row)
	for u in added:
		doc.append("users", {"user": u})
	doc.save(ignore_permissions=True)
	final = [row.user for row in doc.users]
	_sync_project_assignment(project, final)
	return {"ok": True, "users": final, "added": added, "removed": removed}


@frappe.whitelist()
def sync_project_team(project, users):
	"""Set a project's whole team (the Team card). Adding and removing are checked
	separately, see _apply_project_team."""
	helper.assert_manage_project_team(project)
	return _apply_project_team(project, _clean_team_users(users))


@frappe.whitelist(methods=["POST"])
def add_project_members(project, users):
	"""Add people to a project's team without touching who is already on it. This is what
	"Assign to project" in the Org Chart and "Add from org chart" on the project page use."""
	if not helper.can_add_project_members(project):
		frappe.throw(
			_("You cannot add people to this project's team. Ask a Team Manager, Department Coordinator, Department Admin or Super Admin."),
			frappe.PermissionError,
		)
	doc = frappe.get_doc("Project", project)
	current = [row.user for row in doc.users]
	wanted = _clean_team_users(users)
	return _apply_project_team(project, current + [u for u in wanted if u not in current])


@frappe.whitelist(methods=["POST"])
def remove_project_members(project, users):
	"""Take people off a project's team. Super Admin / Department Admin only (a Team Lead
	or Lead Architect may add people but not remove them). The people who stay are not
	re-validated, so someone whose login was since disabled can still be taken off."""
	if not helper.can_remove_project_members(project):
		frappe.throw(
			_("Only a Super Admin, a Department Admin or a Department Coordinator can remove people from a project team."),
			frappe.PermissionError,
		)
	if isinstance(users, str):
		users = json.loads(users or "[]")
	if not isinstance(users, list):
		frappe.throw(_("users must be a list of user IDs"))
	gone = {u.strip() for u in users if isinstance(u, str) and u.strip()}
	doc = frappe.get_doc("Project", project)
	current = [row.user for row in doc.users]
	return _apply_project_team(project, [u for u in current if u not in gone])


@frappe.whitelist()
def get_assignable_projects(for_user=None):
	"""Projects the caller can put people on (the "Assign to project" picker). With
	`for_user`, each row also says whether that person is already on its team."""
	helper.assert_portal_user()
	if helper.is_customer_only():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	allowed = helper.get_allowed_project_names()
	if not allowed:
		return []
	if not (helper.is_super_admin() or helper.is_dept_admin() or helper.is_dept_coordinator() or helper.is_team_lead()):
		# A Project Lead may add people to the projects they lead.
		allowed = [n for n in allowed if frappe.db.get_value("Project", n, "portal_project_manager") == frappe.session.user]
		if not allowed:
			return []
	fields = ["name", "project_name", "status", "customer"]
	if frappe.get_meta("Project").has_field("portal_project_code"):
		fields.append("portal_project_code")
	rows = frappe.get_all(
		"Project",
		filters={"name": ["in", allowed]},
		fields=fields,
		order_by="modified desc",
		limit_page_length=500,
	)
	if for_user:
		on = set(
			frappe.get_all("Project User", filters={"user": for_user, "parenttype": "Project"}, pluck="parent")
		)
		for r in rows:
			r["already_on_team"] = 1 if r["name"] in on else 0
	return rows


def _sync_project_assignment(project, users):
	"""Mirror Project team membership into Frappe's standard Assign To (ToDo) so the
	portal's Team list and ERP's native "Assigned To" sidebar show the same people.
	Does not touch the Project Users table or any portal access-control logic."""
	import frappe.share as _share
	from portal_app.utils import assign_add_unchecked as assign_add
	from portal_app.utils import assign_remove_unchecked as assign_remove

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
		assign_add({"doctype": "Project", "name": project, "assign_to": to_add})
	for u in to_remove:
		assign_remove("Project", project, u)


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
	# Never promote a client contact to team member from a Desk "Assign To".
	if helper.is_customer_only(user):
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

	# A login may belong to several customers (Portal User Customer); ATA keeps one
	# Customer per project, so one client contact routinely spans several.


def _attach_portal_customer_user(user, customer):
	helper.ensure_portal_customer_role()
	if not frappe.db.exists(helper.PORTAL_USER_CUSTOMER, {"user": user, "customer": customer}):
		frappe.get_doc({"doctype": helper.PORTAL_USER_CUSTOMER, "user": user, "customer": customer}).insert(
			ignore_permissions=True
		)
	doc = frappe.get_doc("User", user)
	doc.flags.ignore_permissions = True
	changed = False
	if frappe.get_meta("User").has_field("portal_linked_customer") and not doc.portal_linked_customer:
		doc.portal_linked_customer = customer
		changed = True
	if not any(r.role == helper.PORTAL_CUSTOMER_ROLE for r in doc.roles):
		doc.append("roles", {"role": helper.PORTAL_CUSTOMER_ROLE})
		changed = True
	if changed:
		doc.save()


def _detach_portal_customer_user(user, customer):
	"""Remove ONE customer from a login; the Portal Customer role goes only with the last.

	delete_doc, not a raw delete: PortalUserCustomer.on_trash re-points the primary,
	revokes the login's shares on that customer's projects and leaves an audit trail."""
	names = frappe.get_all(helper.PORTAL_USER_CUSTOMER, filters={"user": user, "customer": customer}, pluck="name")
	if not names:
		return
	for name in names:
		frappe.delete_doc(helper.PORTAL_USER_CUSTOMER, name, ignore_permissions=True)
	if helper.get_portal_linked_customers(user):
		return
	doc = frappe.get_doc("User", user)
	doc.flags.ignore_permissions = True
	for row in list(doc.roles):
		if row.role == helper.PORTAL_CUSTOMER_ROLE:
			doc.remove(row)
	doc.save()


def _can_link_customer_logins() -> bool:
	"""Attaching a login to a customer hands it that customer's whole portfolio, so it
	takes a manager (or whoever may create logins), not just any project team member.

	NOT frappe.has_permission("User", "write"): with no doc that falls back to "is any
	User shared with me for write", and every user has a write share on their own User
	record (share_with_self), so it was True for everyone."""
	return helper.has_portal_staff_project_access() or bool(
		frappe.has_permission("User", "create", user=frappe.session.user)
	)


@frappe.whitelist()
def get_customer_portal_users(project):
	helper.assert_manage_project(project)
	cust = _project_customer_required(project)
	helper.ensure_user_portal_linked_customer_field()
	if not frappe.get_meta("User").has_field("portal_linked_customer"):
		return {"users": []}

	users = frappe.get_all(
		"User",
		filters={"name": ["in", helper.get_customer_contact_users(cust) or [""]], "enabled": 1},
		fields=["name", "full_name", "email", "last_login"],
		order_by="name asc",
		limit_page_length=200,
	)
	for u in users:
		u["can_reset"] = _is_resettable_customer_contact(u.name, cust)
	return {
		"users": users,
		"can_invite": bool(frappe.has_permission("User", "create", user=frappe.session.user)),
		"can_link_existing": _can_link_customer_logins(),
		"can_reset_password": _can_reset_customer_portal_passwords(),
	}


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
	# Enabled only: the UI list hides disabled contacts, so counting them here would
	# silently detach them on the next add/remove click.
	old_set = set(
		frappe.get_all(
			"User",
			filters={"name": ["in", helper.get_customer_contact_users(cust) or [""]], "enabled": 1},
			pluck="name",
		)
	)

	notified = {}
	if (new_set - old_set) and not _can_link_customer_logins():
		frappe.throw(
			_("Only a Super Admin or a Department Admin can add customer portal users."),
			frappe.PermissionError,
		)
	for u in new_set - old_set:
		_assert_user_eligible_for_customer_link(u, cust)
		_attach_portal_customer_user(u, cust)
		# Tell them: an access notice, or the welcome (set-password) mail if they have
		# never set a password. Queued, so a mail failure cannot undo the link.
		notified[u] = _send_portal_invite(u, cust)

	for u in old_set - new_set:
		_detach_portal_customer_user(u, cust)

	return {"ok": True, "users": sorted(new_set), "notified": notified}


def _can_reset_customer_portal_passwords(user=None) -> bool:
	return helper.is_super_admin(user or frappe.session.user)


def _user_has_password(user) -> bool:
	auth = frappe.qb.Table("__Auth")
	rows = (
		frappe.qb.from_(auth)
		.select(auth.name)
		.where((auth.doctype == "User") & (auth.name == user) & (auth.fieldname == "password"))
		.limit(1)
		.run()
	)
	return bool(rows)


def _welcome_link_pending(user) -> bool:
	"""A set-password link that has not been used and has not expired yet."""
	row = frappe.db.get_value(
		"User", user, ["reset_password_key", "last_reset_password_key_generated_on"], as_dict=True
	)
	if not row or not row.reset_password_key:
		return False
	expiry = cint(frappe.get_system_settings("reset_password_link_expiry_duration"))
	if not expiry:
		return True
	if not row.last_reset_password_key_generated_on:
		return False
	return now_datetime() < add_to_date(row.last_reset_password_key_generated_on, seconds=expiry)


def _send_portal_access_notice(user, customer, pending_welcome=False):
	"""Tell an existing login that it can now see this customer's projects."""
	doc = frappe.get_doc("User", user)
	customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
	inviter = frappe.utils.get_fullname(frappe.session.user) or frappe.session.user
	login_url = frappe.utils.get_url(helper.PORTAL_HOME + "/login")
	link = '<a href="' + escape_html(login_url) + '">' + escape_html(login_url) + "</a>"
	body = (
		"<p>"
		+ _("Hi {0},").format(escape_html(doc.full_name or doc.email))
		+ "</p><p>"
		+ _("{0} has given you access to the {1} projects on the client portal.").format(
			"<strong>" + escape_html(inviter) + "</strong>",
			"<strong>" + escape_html(customer_name) + "</strong>",
		)
		+ "</p><p>"
		+ (
			_("Use the set-password link in your earlier welcome email, or Forgot Password at {0}.").format(link)
			if pending_welcome
			else _("Sign in at {0} with your existing password.").format(link)
		)
		+ "</p>"
	)
	# Queued, never sent inside the request: EmailQueue.send() commits mid-request and
	# an SMTP failure there would surface after the link was already saved.
	frappe.sendmail(
		recipients=[doc.email],
		subject=_("You now have access to {0} projects").format(customer_name),
		message=body,
		now=False,
	)


def _send_portal_invite(user, customer) -> bool:
	"""Invite an EXISTING user to the portal. A user who has never set a password gets
	Frappe's welcome mail (set-password link); one who has gets an access notice."""
	try:
		if _user_has_password(user):
			_send_portal_access_notice(user, customer)
		elif _welcome_link_pending(user):
			# A new welcome mail would overwrite reset_password_key and kill the link in
			# the one they already have (e.g. added to three projects in a row).
			_send_portal_access_notice(user, customer, pending_welcome=True)
		else:
			doc = frappe.get_doc("User", user)
			doc.db_set("redirect_url", helper.PORTAL_HOME)
			doc.flags.delay_emails = True
			doc.send_welcome_mail_to_user()
		return True
	except frappe.OutgoingEmailError:
		frappe.clear_last_message()
		return False


@frappe.whitelist(methods=["POST"])
def create_customer_portal_user_from_project(project, email, full_name, password=None, send_welcome_email=1):
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
	send_welcome_email = cint(send_welcome_email)

	if not email or not full_name:
		frappe.throw(_("Valid email and full name are required"))
	validate_email_address(email, throw=True)

	if frappe.db.exists("User", email):
		if not frappe.db.get_value("User", email, "enabled"):
			frappe.throw(_("{0} is a disabled login. Re-enable it in Desk before inviting them.").format(email))
		_assert_user_eligible_for_customer_link(email, cust)
		# The typed password is never applied to an existing login; one that has no
		# password yet can only get in through the welcome link.
		if not send_welcome_email and not _user_has_password(email):
			frappe.throw(_("{0} already exists but has no password yet. Tick Send a welcome email.").format(email))
		_attach_portal_customer_user(email, cust)
		email_sent = _send_portal_invite(email, cust) if send_welcome_email else False
		return {"name": email, "email": email, "attached": True, "created": False, "email_sent": email_sent}

	if not send_welcome_email and not password:
		frappe.throw(_("Either send the welcome email or set a password, otherwise they cannot sign in."))

	parts = full_name.split(None, 1)
	first_name = parts[0]
	last_name = parts[1] if len(parts) > 1 else ""

	user_dict = {
		"doctype": "User",
		"email": email,
		"first_name": first_name,
		"last_name": last_name,
		"enabled": 1,
		# Frappe's welcome mail carries a set-password link; with a password also
		# given, the password is set first and the link still lets them change it.
		"send_welcome_email": send_welcome_email,
		"user_type": "Website User",
		# update_password() sends a Website User to redirect_url after they set their
		# password from the welcome link; without it they land on /me.
		"redirect_url": helper.PORTAL_HOME,
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
	# Queue the welcome mail instead of sending it inside this request (see
	# _send_portal_access_notice); email_sent then means "queued".
	doc.flags.delay_emails = True
	doc.insert()
	if not frappe.db.exists(helper.PORTAL_USER_CUSTOMER, {"user": doc.name, "customer": cust}):
		frappe.get_doc({"doctype": helper.PORTAL_USER_CUSTOMER, "user": doc.name, "customer": cust}).insert(
			ignore_permissions=True
		)

	return {
		"name": doc.name,
		"email": email,
		"created": True,
		"attached": True,
		"email_sent": bool(doc.flags.email_sent),
	}


def _is_resettable_customer_contact(user, customer) -> bool:
	try:
		_assert_resettable_customer_contact(user, customer)
		return True
	except (frappe.PermissionError, frappe.DoesNotExistError, frappe.ValidationError):
		frappe.clear_last_message()
		return False


def _assert_resettable_customer_contact(user, customer):
	"""Only an enabled, external contact of THIS project's customer may have their
	password reset from a project — never staff, Administrator, or another customer's
	contact, whatever the caller's own rights."""
	if not user or user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		frappe.throw(_("Unknown customer portal user."), frappe.DoesNotExistError)
	if not frappe.db.get_value("User", user, "enabled"):
		frappe.throw(_("This user is disabled."))
	if (
		helper.has_portal_staff_project_access(user)
		or frappe.db.exists("Project User", {"user": user})
		or not helper.user_is_customer_portal_user(user)
		or customer not in helper.get_portal_linked_customers(user)
	):
		frappe.throw(
			_("Only a customer portal user of this project's customer can be reset here."),
			frappe.PermissionError,
		)


@frappe.whitelist(methods=["POST"])
def reset_customer_portal_user_password(project, user, mode="email", new_password=None):
	helper.assert_manage_project(project)
	if not _can_reset_customer_portal_passwords():
		frappe.throw(
			_("Only a Super Admin can reset a Client Customer's password."), frappe.PermissionError
		)
	cust = _project_customer_required(project)
	user = cstr(user).strip()
	_assert_resettable_customer_contact(user, cust)

	from portal_app.api.portal_admin import reset_password_for

	return reset_password_for(user, mode, new_password)


@frappe.whitelist()
def search_portal_users(txt="", customer_portal=0, staff_only=0):
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
	if cint(customer_portal):
		# Customer-portal picker: only external (Website User) logins — staff can never
		# be linked as a customer contact, so listing them only produced errors.
		filters.append(["user_type", "=", "Website User"])
	elif cint(staff_only):
		# Task assignees: ATA staff logins only (create_task refuses anyone else).
		filters.append(["user_type", "=", "System User"])
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
	return search_portal_users(query, staff_only=1)


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
	helper.assert_not_customer_only()
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
	helper.assert_not_customer_only()
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
	helper.assert_not_customer_only()
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
	helper.assert_not_customer_only()
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
def create_task(project, subject, status="Open", priority="Medium", exp_end_date=None, assigned_to=None):
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
	# The quick-create form always sent assigned_to, but this method had no such
	# argument, so Frappe dropped it and every task was created unassigned.
	assignee = cstr(assigned_to or "").strip()
	if assignee:
		if not frappe.db.get_value("User", {"name": assignee, "enabled": 1, "user_type": "System User"}):
			frappe.throw(_("Assign the task to an active ATA staff login."))
		if helper.is_customer_only(assignee):
			frappe.throw(_("Tasks cannot be assigned to customer portal users."))
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
	if assignee:
		import frappe.share as _share
		from portal_app.utils import assign_add_unchecked as assign_add

		# assign_to.add() shares the Task with an assignee who cannot read it, and that
		# share step checks the CALLER's own Task share permission (Projects Manager-only
		# logins have none), which rolled the whole create back. Pre-share with the
		# supported bypass, as _sync_project_assignment does for Projects.
		if not frappe.has_permission("Task", "read", doc=doc, user=assignee):
			_share.add_docshare(
				"Task", doc.name, user=assignee, read=1, flags={"ignore_share_permission": True}, notify=0
			)
		assign_add({"assign_to": [assignee], "doctype": "Task", "name": doc.name})
	frappe.db.commit()
	return {
		"ok": True,
		"name": doc.name,
		"assigned_to": assignee or None,
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
	helper.assert_not_customer_only()
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
	helper.assert_manage_project_records(project)
	frappe.delete_doc("Project", project, ignore_permissions=True)
	return {"deleted": project}
