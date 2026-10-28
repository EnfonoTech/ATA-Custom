"""Submissions to the client: the Portal Submission Type master, "Submit to client"
(one numbered submission folder in the client folder's Incoming), and the read-only
transmittal view behind the client landing page (/portal-app/client).

Access rules are the ones in files.py and helper.py; this module only reuses them.
Always call `files.<helper>` (module attribute) so tests can patch them.
"""

import os

import frappe
from frappe import _
from frappe.query_builder.functions import Lower
from frappe.utils import cint, cstr, flt
from frappe.utils.file_manager import save_file

from portal_app.api import files, helper

TYPE_DT = "Portal Submission Type"
# The submission folder name is at most this long, leaving room for "-NN.ext" on the
# copied files (File.file_name is varchar(140)).
STEM_MAX = 120
FILE_NAME_MAX = 140
# File.name / File.folder are varchar(255).
PATH_MAX = 255
SUBMIT_TRIES = 5


# ---------------------------------------------------------------------------------
# Submission types
# ---------------------------------------------------------------------------------
def _can_manage_submission_types(user=None) -> bool:
	"""Super Admin or Department Admin."""
	return helper.has_portal_staff_project_access(user)


def _assert_manage_submission_types() -> None:
	helper.assert_not_customer_only()
	if not _can_manage_submission_types():
		frappe.throw(
			_("Only a Super Admin or a Department Admin can manage submission types."),
			frappe.PermissionError,
		)


def _type_row(name) -> dict:
	return frappe.db.get_value(TYPE_DT, name, ["name", "type_name", "enabled"], as_dict=True)


def _type_name_match(type_name: str) -> str | None:
	"""Name of an existing type with this name in any letter case."""
	t = frappe.qb.DocType(TYPE_DT)
	rows = frappe.qb.from_(t).select(t.name).where(Lower(t.type_name) == cstr(type_name).lower()).run()
	return rows[0][0] if rows else None


@frappe.whitelist()
def list_submission_types(include_disabled=0):
	"""Submission types for the Submit to client form (enabled only), or for the Admin
	card (include_disabled, admin tier only)."""
	helper.assert_portal_user()
	helper.assert_not_customer_only()
	filters = {}
	if not (cint(include_disabled) and _can_manage_submission_types()):
		filters["enabled"] = 1
	return frappe.get_all(
		TYPE_DT,
		filters=filters,
		fields=["name", "type_name", "enabled"],
		order_by="type_name asc",
		limit_page_length=0,
	)


@frappe.whitelist(methods=["POST"])
def add_submission_type(type_name):
	_assert_manage_submission_types()
	raw = cstr(type_name)
	# A name with illegal characters goes straight to the controller, which refuses it.
	existing = None if files.SUBMISSION_NAME_ILLEGAL.search(raw) else _type_name_match(files._clean_name_part(raw))
	if existing:
		doc = frappe.get_doc(TYPE_DT, existing)
		if doc.enabled:
			frappe.throw(_("A submission type with this name already exists."))
		# Re-adding a disabled type turns it back on instead of failing.
		doc.enabled = 1
		doc.save(ignore_permissions=True)
		return _type_row(doc.name)
	doc = frappe.get_doc({"doctype": TYPE_DT, "type_name": raw, "enabled": 1})
	doc.insert(ignore_permissions=True)
	return _type_row(doc.name)


@frappe.whitelist(methods=["POST"])
def set_submission_type_enabled(type_name, enabled):
	_assert_manage_submission_types()
	type_name = cstr(type_name).strip()
	if not type_name or not frappe.db.exists(TYPE_DT, type_name):
		frappe.throw(_("Unknown submission type."))
	doc = frappe.get_doc(TYPE_DT, type_name)
	doc.enabled = 1 if cint(enabled) else 0
	doc.save(ignore_permissions=True)
	return _type_row(doc.name)


# ---------------------------------------------------------------------------------
# Submit to client
# ---------------------------------------------------------------------------------
def _submission_stem(number, date_str, type_name, description) -> str:
	"""NN_YYYY-MM-DD_<Type>[ - <description>]. Only the description is trimmed, so the
	stem stays within STEM_MAX."""
	stem = f"{cint(number):02d}_{date_str}_{type_name}"
	room = STEM_MAX - len(stem) - 3
	desc = files._clean_name_part(description, max_len=room) if room > 0 else ""
	return stem + (f" - {desc}" if desc else "")


def _parse_file_names(file_names) -> list:
	"""Unique File names, in the order the user picked them."""
	if isinstance(file_names, str):
		file_names = frappe.parse_json(file_names) if file_names.strip() else []
	if not isinstance(file_names, (list, tuple)):
		file_names = [file_names] if file_names else []
	out = []
	for n in file_names:
		n = cstr(n).strip()
		if n and n not in out:
			out.append(n)
	return out


def _loose_file_sources(project: str, names: list) -> list:
	sources = []
	for name in names:
		row = frappe.db.get_value(
			"File",
			name,
			["name", "file_name", "folder", "file_size", "is_folder", "attached_to_doctype", "attached_to_name"],
			as_dict=True,
		)
		if not row or row.is_folder:
			frappe.throw(_("Choose files or one folder to submit."))
		if row.attached_to_doctype != "Project" or row.attached_to_name != project:
			frappe.throw(_("Invalid file"))
		if cstr(row.folder).startswith("Home/Contracts/"):
			frappe.throw(_("Contract files cannot be submitted to the client."), frappe.PermissionError)
		sources.append(row)
	return sources


def _folder_sources(project: str, folder_path) -> tuple:
	"""(folder, files at any depth below it) for a folder of this project that is not
	the client folder or inside it."""
	fp = cstr(folder_path).replace("\\", "/").strip().rstrip("/")
	project_root = files._attachments_root() + "/" + project
	if (
		not fp.startswith(project_root + "/")
		or any(p in ("", ".", "..") for p in fp.split("/"))
		or not frappe.db.get_value("File", {"name": fp, "is_folder": 1}, "name")
	):
		frappe.throw(_("Choose a folder of this project."))
	if files._in_folder(fp, files._client_folder_path(project)):
		frappe.throw(_("Choose a folder outside the client folder."))
	rows = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Project", "attached_to_name": project, "is_folder": 0},
		or_filters=[["folder", "=", fp], ["folder", "like", fp + "/%"]],
		fields=["name", "file_name", "folder", "file_size"],
		order_by="folder asc, file_name asc",
		limit_page_length=files._ZIP_DOWNLOAD_MAX_FILES + 1,
	)
	# LIKE treats "_" / "%" as wildcards: keep only what is really inside the folder.
	rows = [r for r in rows if files._in_folder(r.folder, fp)]
	if not rows:
		frappe.throw(_("That folder has no files to submit."))
	return fp, rows


def _assert_within_caps(sources: list) -> None:
	max_files = files._ZIP_DOWNLOAD_MAX_FILES
	max_bytes = files._ZIP_DOWNLOAD_MAX_BYTES
	if len(sources) > max_files:
		frappe.throw(_("Too many files to submit at once (max {0}).").format(max_files))
	if sum(flt(s.file_size) for s in sources) > max_bytes:
		frappe.throw(_("Submission too large (max {0} MB).").format(max_bytes // (1024 * 1024)))


def _copy_plan(stem: str, folder_path: str, sources: list, fp) -> list:
	"""[(source, relative_dir, new_file_name)]. Loose files get stem[-N].ext; a folder's
	files keep their names and sub-structure. Refuses names that would not fit."""
	plan = []
	for i, src in enumerate(sources):
		if fp is None:
			ext = os.path.splitext(cstr(src.file_name))[1]
			plan.append((src, "", stem + ("" if i == 0 else f"-{i + 1}") + ext))
		else:
			rel = "" if src.folder == fp else src.folder[len(fp) + 1 :]
			plan.append((src, rel, src.file_name))
	for _src, rel, name in plan:
		dest = folder_path + ("/" + rel if rel else "")
		if len(cstr(name)) > FILE_NAME_MAX or len(dest) > PATH_MAX:
			frappe.throw(_("This name is too long. Use a shorter description."))
	return plan


def _ensure_exact_folder_path(parent: str, rel: str) -> str:
	"""Create parent/rel segment by segment, matching each existing folder by its exact
	file_name. files._ensure_folder_path would merge lookalike siblings ("Sub - A" and
	"sub-A") through its normalised-label fallback; a submitted folder is copied as it is."""
	cur = parent
	for seg in rel.split("/"):
		existing = frappe.db.get_value("File", {"folder": cur, "is_folder": 1, "file_name": seg}, "name")
		cur = existing or frappe.get_doc(
			{"doctype": "File", "file_name": seg, "folder": cur, "is_folder": 1}
		).insert(ignore_permissions=True).name
	return cur


@frappe.whitelist(methods=["POST"])
def submit_to_client(project, submission_type, description=None, file_names=None, folder_path=None):
	"""Create ONE submission folder NN_YYYY-MM-DD_<Type>[ - <description>] in the client
	folder's Incoming and copy the chosen files (or one folder) into it."""
	project = cstr(project).strip()
	if not project:
		frappe.throw(_("project is required"))
	helper.assert_not_customer_only()
	helper.assert_manage_project(project)

	type_name = cstr(submission_type).strip()
	row = _type_row(type_name) if type_name else None
	if not row or not row.enabled:
		frappe.throw(_("Choose an enabled submission type."))

	desc = files._clean_name_part(description, max_len=100)

	names = _parse_file_names(file_names)
	has_folder = bool(cstr(folder_path).strip())
	if bool(names) == has_folder:
		frappe.throw(_("Choose files or one folder to submit."))
	if names:
		fp, sources = None, _loose_file_sources(project, names)
	else:
		fp, sources = _folder_sources(project, folder_path)
	_assert_within_caps(sources)

	# Every check passed: take the lock on Incoming, then number.
	target = files._ensure_client_folders(project)["incoming"]
	files._lock_folder(target)

	today = frappe.utils.today()
	folder_doc = plan = stem = n = None
	for _attempt in range(SUBMIT_TRIES):
		n = files._next_submission_number(target) if n is None else n + 1
		stem = _submission_stem(n, today, row.type_name, desc)
		plan = _copy_plan(stem, target + "/" + stem, sources, fp)
		if frappe.db.exists("File", target + "/" + stem):
			continue
		try:
			folder_doc = frappe.get_doc(
				{"doctype": "File", "file_name": stem, "folder": target, "is_folder": 1}
			).insert(ignore_permissions=True)
		except frappe.DuplicateEntryError:
			# The File primary key is the full path: this number was taken meanwhile.
			frappe.clear_last_message()
			continue
		break
	if not folder_doc:
		frappe.throw(_("Could not number this submission. Please try again."))

	copied = []
	dest_folders = {"": folder_doc.name}
	for src, rel, new_name in plan:
		if rel not in dest_folders:
			dest_folders[rel] = _ensure_exact_folder_path(folder_doc.name, rel)
		dest = dest_folders[rel]
		content = frappe.get_doc("File", src.name).get_content()
		with files._bypass_max_attachments():
			doc = save_file(new_name, content, "Project", project, folder=dest, is_private=1)
		# Same two fix-ups as files.submit_to_client_submittal: a hook may reset the
		# folder, and save_file reuses the name of a File with the same content.
		if doc.folder != dest:
			frappe.db.set_value("File", doc.name, "folder", dest, update_modified=False)
		if doc.file_name != new_name:
			frappe.db.set_value("File", doc.name, "file_name", new_name, update_modified=False)
			doc.file_name = new_name
		copied.append({"name": doc.name, "file_name": doc.file_name})

	return {"folder": folder_doc.name, "folder_name": stem, "number": n, "files": copied}


# ---------------------------------------------------------------------------------
# Client landing page (read-only)
# ---------------------------------------------------------------------------------
@frappe.whitelist()
def list_client_projects():
	"""The projects this login may see, for the client page's picker. No customer,
	money or team fields."""
	helper.assert_portal_user()
	fields = ["name", "project_name"]
	if frappe.get_meta("Project").has_field("portal_project_code"):
		fields.append("portal_project_code")
	return frappe.get_all(
		"Project",
		filters={"name": ["in", helper.get_allowed_project_names() or [""]]},
		fields=fields,
		order_by="project_name asc",
		limit_page_length=500,
	)


def _submissions_in(direction_folder: str, folders: list, file_rows: list) -> list:
	"""Numbered submissions of one direction folder: its direct subfolders (with every
	file below them) plus the loose files directly in it, oldest first."""
	items = []
	for s in folders:
		if s.folder != direction_folder:
			continue
		inside = [f for f in file_rows if files._in_folder(f.folder, s.name)]
		for f in inside:
			f["relative_path"] = "" if f.folder == s.name else f.folder[len(s.name) + 1 :]
		inside.sort(key=lambda f: (f["relative_path"], cstr(f.file_name)))
		items.append({"key": s.name, "kind": "folder", "title": s.file_name, "created": s.creation, "files": inside})
	for f in file_rows:
		if f.folder == direction_folder:
			f["relative_path"] = ""
			items.append({"key": f.name, "kind": "file", "title": f.file_name, "created": f.creation, "files": [f]})
	items.sort(key=lambda i: (i["created"], i["key"]))
	for idx, item in enumerate(items):
		item["number"] = idx + 1
		item["is_latest"] = idx == len(items) - 1
		item["file_count"] = len(item["files"])
		item["files"] = [
			{
				"name": f.name,
				"file_name": f.file_name,
				"file_size": f.file_size,
				"creation": f.creation,
				"relative_path": f["relative_path"],
				"uploaded_by_client": cint(f.get("uploaded_by_client")),
			}
			for f in item["files"]
		]
	return items


@frappe.whitelist()
def list_client_transmittals(project):
	"""Incoming / Outgoing of the project's client folder as numbered submissions
	(oldest = 1). Read-only: never creates folders (GET requests are rolled back)."""
	helper.assert_portal_user()
	project = cstr(project).strip()
	helper.assert_project_access(project)
	result = {
		"project": project,
		"project_name": frappe.db.get_value("Project", project, "project_name"),
		"incoming": [],
		"outgoing": [],
		"can_upload": helper.is_customer_only(),
	}
	root = files._client_folder_path(project)
	if not frappe.db.exists("File", root):
		return result
	inc = root + "/" + files.CLIENT_INCOMING
	out = root + "/" + files.CLIENT_OUTGOING

	def in_client_dirs(folder):
		return files._in_folder(folder, inc) or files._in_folder(folder, out)

	folders = frappe.get_all(
		"File",
		filters={"is_folder": 1},
		or_filters=[["folder", "in", [inc, out]], ["name", "like", inc + "/%"], ["name", "like", out + "/%"]],
		fields=["name", "file_name", "folder", "creation"],
		limit_page_length=0,
	)
	folders = [f for f in folders if in_client_dirs(f.folder)]
	rows = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Project", "attached_to_name": project, "is_folder": 0},
		or_filters=[["folder", "in", [inc, out]], ["folder", "like", inc + "/%"], ["folder", "like", out + "/%"]],
		fields=["name", "file_name", "folder", "creation", "file_size", "owner"],
		order_by="creation asc",
		limit_page_length=0,
	)
	rows = [f for f in rows if in_client_dirs(f.folder) and files._customer_may_read_file(project, f.name, f.folder)]
	files._flag_client_uploads(rows)

	result["incoming"] = _submissions_in(inc, folders, [f for f in rows if files._in_folder(f.folder, inc)])
	result["outgoing"] = _submissions_in(out, folders, [f for f in rows if files._in_folder(f.folder, out)])
	return result
