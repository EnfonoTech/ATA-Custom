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
	for fn in ("portal_project_code", "portal_project_manager", "portal_kanban_stage"):
		if meta.has_field(fn):
			base.append(fn)
	return base


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
		order_by=f"{sort_by} {sort_order}",
		limit_page_length=500,
	)
	return {"projects": projects}


@frappe.whitelist()
def get_project(name):
	helper.assert_project_access(name)
	doc = frappe.get_doc("Project", name)
	out = doc.as_dict()
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

	cost = flt(
		frappe.db.sql(
			f"""
			SELECT SUM(estimated_costing) FROM `tabProject`
			WHERE name IN ({placeholders})
			""",
			names,
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

	return {
		"project": p.as_dict(),
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
	projects = frappe.get_all("Project", filters={"name": ["in", names]}, fields=fields, limit_page_length=500)

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
def get_portal_folder_template():
	"""Read Portal Project Settings.folder_template (ordered subfolder names for new projects)."""
	helper.assert_can_edit_portal_folder_template()
	if not frappe.db.exists("DocType", "Portal Project Settings"):
		return {"rows": []}
	doc = frappe.get_single("Portal Project Settings")
	rows = doc.get("folder_template") or []
	out = []
	for row in sorted(rows, key=lambda r: int(getattr(r, "idx", 0) or 0)):
		out.append({"folder_name": cstr(getattr(row, "folder_name", None) or "").strip()})
	return {"rows": [r for r in out if r["folder_name"]]}


@frappe.whitelist()
def save_portal_folder_template(rows=None):
	"""Replace folder template rows (company-wide). Empty list falls back to site config / built-in default."""
	helper.assert_can_edit_portal_folder_template()
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


def _collect_template_paths_from_zip_content(content: bytes) -> list[str]:
	"""Extract folder tree from a ZIP. Returns only leaf paths in a stable hierarchical order.

	If every entry shares the same first segment (a single root folder wrapping the tree),
	that wrapper is stripped so the template starts from the contained folders.
	Intermediate folders are dropped because the backend auto-creates ancestors when ensuring
	a leaf path; storing only leaves keeps the template list lean and easy to read.
	"""
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
		if "Projects Manager" in roles or "System Manager" in roles:
			can_create = True
		else:
			try:
				can_create = bool(frappe.has_permission("Project", "create", user=frappe.session.user))
			except Exception:
				can_create = False

	allowed_names = helper.get_allowed_project_names()
	manageable = [name for name in allowed_names if helper.can_manage_project(name)]

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
		"is_customer_portal_user": effective_customer_portal,
		"can_manage_customers": helper.can_manage_customers_in_portal(),
		"can_edit_portal_folder_template": helper.can_edit_portal_folder_template()
		if not effective_customer_portal
		else False,
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
	for k in ("portal_project_code", "portal_project_manager", "portal_kanban_stage"):
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
	if meta.has_field("portal_project_manager") and not doc.get("portal_project_manager"):
		doc.portal_project_manager = frappe.session.user
	doc.save(ignore_permissions=True)
	try:
		from portal_app.api.files import ensure_project_folders

		ensure_project_folders(doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Portal: Failed creating project folders")

	return {"name": doc.name, "project_name": doc.project_name}


@frappe.whitelist()
def sync_project_team(project, users):
	helper.assert_manage_project(project)
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

	return {"ok": True, "users": [row.user for row in doc.users]}


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
		_assert_user_eligible_for_customer_link(u, cust)
		_attach_portal_customer_user(u, cust)

	for u in old_set - new_set:
		_detach_portal_customer_user(u, cust)

	return {"ok": True, "users": sorted(new_set)}


@frappe.whitelist()
def create_customer_portal_user_from_project(project, email, full_name, password):
	helper.assert_manage_project(project)
	helper.ensure_portal_customer_role()
	helper.ensure_user_portal_linked_customer_field()
	cust = _project_customer_required(project)

	email = (email or "").strip().lower()
	full_name = (full_name or "").strip()
	password = password or ""

	if not email or not full_name or len(password) < 6:
		frappe.throw(_("Valid email, full name, and password (min 6 characters) are required"))

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
		"send_welcome_email": 0,
		"user_type": "System User",
	}
	if frappe.get_meta("User").has_field("portal_linked_customer"):
		user_dict["portal_linked_customer"] = cust

	doc = frappe.get_doc(user_dict)
	doc.append("roles", {"role": helper.PORTAL_CUSTOMER_ROLE})
	doc.flags.ignore_permissions = True
	doc.insert()

	from frappe.utils.password import update_password

	update_password(email, password)

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
		frappe.throw(_("Only project managers or assigned users can update this task."), frappe.PermissionError)

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
