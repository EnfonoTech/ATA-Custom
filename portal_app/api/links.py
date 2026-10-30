"""Per-project links (R3): T Server, Autodesk Server and ERP.

Each link type is one Portal Project Link row with a mapped-drive path (copy_path,
shown with Copy) and/or a URL (open_url, shown with Open), plus a list of users who may
open it. The project's link managers (helper.can_manage_project_links: Department
Coordinator / Department Admin of the project's department, Super Admin) always may.

The path and URL are only ever put in a response for someone who may open the link
(can_open = 1). Everyone else gets has_path / has_url only, so the browser has nothing
to leak. Client contacts get nothing at all."""

import json

import frappe
from frappe import _
from frappe.utils import cstr

from portal_app.api import helper


def _entry(link_type, row, can_open) -> dict:
	entry = {
		"link_type": link_type,
		"label": _(link_type),
		"has_path": 1 if row and row.get("copy_path") else 0,
		"has_url": 1 if row and row.get("open_url") else 0,
		"can_open": 1 if can_open else 0,
	}
	if can_open:
		entry["copy_path"] = (row.get("copy_path") if row else None) or ""
		entry["open_url"] = (row.get("open_url") if row else None) or ""
	return entry


def _managed_projects(project_names, user, visible) -> set:
	"""helper.can_manage_project_links for a whole list in a handful of queries."""
	if helper.is_super_admin(user):
		return set(project_names)
	if helper.is_customer_only(user) or not (helper.is_dept_admin(user) or helper.is_dept_coordinator(user)):
		return set()
	if not frappe.get_meta("Project").has_field("portal_team"):
		return set()
	admin_units = set(helper.admin_department_names(user)) if helper.is_dept_admin(user) else set()
	coord_units = set(helper.coordinator_department_names(user)) if helper.is_dept_coordinator(user) else set()
	teams = dict(
		frappe.get_all(
			"Project", filters={"name": ["in", list(project_names)]}, fields=["name", "portal_team"], as_list=True
		)
	)
	departments = {}
	out = set()
	for project, team in teams.items():
		if not team or project not in visible:
			continue
		if team in admin_units:
			out.add(project)
			continue
		if team not in departments:
			departments[team] = helper.team_department(team)
		dept = departments[team]
		if dept and (dept in admin_units or dept in coord_units):
			out.add(project)
	return out


def links_for_projects(project_names, user=None, _with_users=False) -> dict:
	"""{project: [T Server, Autodesk Server, ERP entries]} for `user` (default: the caller).

	Every entry is {link_type, label, has_path, has_url, can_open}; copy_path and open_url
	are added only when can_open. A client contact gets {} (no key at all). Two queries
	for the links and their allowed users, whatever the number of projects."""
	user = user or frappe.session.user
	names = [n for n in dict.fromkeys(project_names or []) if n]
	if not names or not user or user == "Guest" or helper.is_customer_only(user):
		return {}

	rows = []
	allowed_by_link = {}
	if frappe.db.table_exists(helper.PROJECT_LINK_DOCTYPE):
		rows = frappe.get_all(
			helper.PROJECT_LINK_DOCTYPE,
			filters={"project": ["in", names]},
			fields=["name", "project", "link_type", "copy_path", "open_url"],
		)
		if rows:
			for r in frappe.get_all(
				"Portal Project Link User",
				filters={"parent": ["in", [r.name for r in rows]], "parenttype": helper.PROJECT_LINK_DOCTYPE},
				fields=["parent", "user"],
				order_by="idx asc",
			):
				allowed_by_link.setdefault(r.parent, []).append(r.user)

	visible = set(names) if helper.is_super_admin(user) else set(helper.get_allowed_project_names(user))
	managed = _managed_projects(names, user, visible)
	by_key = {(r.project, r.link_type): r for r in rows}

	out = {}
	for project in names:
		entries = []
		for link_type in helper.LINK_TYPES:
			row = by_key.get((project, link_type))
			can_open = bool(row) and (
				project in managed or (user in allowed_by_link.get(row.name, []) and project in visible)
			)
			entry = _entry(link_type, row, can_open)
			if _with_users and project in managed:
				entry["copy_path"] = (row.get("copy_path") if row else None) or ""
				entry["open_url"] = (row.get("open_url") if row else None) or ""
				entry["allowed_users"] = allowed_by_link.get(row.name, []) if row else []
				entry["can_manage"] = 1
			entries.append(entry)
		out[project] = entries
	return out


@frappe.whitelist()
def get_project_links(project):
	"""The three links of one project for the project page. A link manager also gets the
	values of every link and its allowed users ({user, full_name}). Read-only."""
	helper.assert_portal_user()
	if helper.is_customer_only():
		frappe.throw(_("Project links are for ATA staff."), frappe.PermissionError)
	project = cstr(project).strip()
	helper.assert_project_access(project)
	can_manage = helper.can_manage_project_links(project)
	entries = links_for_projects([project], _with_users=can_manage).get(project, [])
	if can_manage:
		users = {u for e in entries for u in e.get("allowed_users") or []}
		names = (
			dict(frappe.get_all("User", filters={"name": ["in", list(users)]}, fields=["name", "full_name"], as_list=True))
			if users
			else {}
		)
		for e in entries:
			e["allowed_users"] = [{"user": u, "full_name": names.get(u) or u} for u in e.get("allowed_users") or []]
	return {"project": project, "links": entries, "can_manage": 1 if can_manage else 0}


def _parse_users(allowed_users) -> list:
	if isinstance(allowed_users, str):
		try:
			allowed_users = json.loads(allowed_users or "[]")
		except Exception:
			frappe.throw(_("Invalid list of users."))
	if not isinstance(allowed_users, list):
		frappe.throw(_("Invalid list of users."))
	out = []
	for u in allowed_users:
		u = cstr(u.get("user") if isinstance(u, dict) else u).strip()
		if u and u not in out:
			out.append(u)
	return out


@frappe.whitelist(methods=["POST"])
def save_project_link(project, link_type, copy_path=None, open_url=None, allowed_users=None):
	"""Create, change or remove one link of a project. Link managers only.

	`None` leaves a field as it is, "" clears it. `allowed_users` (a JSON list) replaces
	the whole list; everyone on it must be able to see the project. A link left with no
	path, no URL and nobody allowed is deleted. Returns get_project_links(project)."""
	helper.assert_portal_user()
	if helper.is_customer_only():
		frappe.throw(_("Project links are for ATA staff."), frappe.PermissionError)
	project = cstr(project).strip()
	helper.assert_project_access(project)
	if not helper.can_manage_project_links(project):
		frappe.throw(
			_("Only this project's Department Coordinator, Department Admin or a Super Admin can change its links."),
			frappe.PermissionError,
		)
	link_type = cstr(link_type).strip()
	if link_type not in helper.LINK_TYPES:
		frappe.throw(_("Unknown link type: {0}").format(link_type))

	users = None
	if allowed_users is not None:
		users = _parse_users(allowed_users)
		for u in users:
			if not frappe.db.exists("User", u):
				frappe.throw(_("User not found: {0}").format(u))
			if helper.is_customer_only(u):
				frappe.throw(_("Client contacts cannot be given access to a project link: {0}").format(u))
			if project not in helper.get_allowed_project_names(u):
				frappe.throw(_("{0} cannot see this project, so cannot be given its link.").format(u))

	name = frappe.db.get_value(helper.PROJECT_LINK_DOCTYPE, {"project": project, "link_type": link_type})
	if name:
		doc = frappe.get_doc(helper.PROJECT_LINK_DOCTYPE, name)
	else:
		doc = frappe.get_doc({"doctype": helper.PROJECT_LINK_DOCTYPE, "project": project, "link_type": link_type})
	if copy_path is not None:
		doc.copy_path = cstr(copy_path)
	if open_url is not None:
		doc.open_url = cstr(open_url)
	if users is not None:
		doc.set("allowed_users", [{"user": u} for u in users])

	empty = not cstr(doc.copy_path).strip() and not cstr(doc.open_url).strip() and not doc.get("allowed_users")
	if empty:
		if name:
			frappe.delete_doc(helper.PROJECT_LINK_DOCTYPE, name, ignore_permissions=True)
	elif name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)
	return get_project_links(project)


def delete_project_links(doc, method=None):
	"""doc_events Project.on_trash: drop the project's links first, or Frappe's
	check_if_doc_is_linked refuses to delete a project that has one (LinkExistsError)."""
	if not frappe.db.table_exists(helper.PROJECT_LINK_DOCTYPE):
		return
	for name in frappe.get_all(helper.PROJECT_LINK_DOCTYPE, filters={"project": doc.name}, pluck="name"):
		frappe.delete_doc(helper.PROJECT_LINK_DOCTYPE, name, ignore_permissions=True, force=True)
