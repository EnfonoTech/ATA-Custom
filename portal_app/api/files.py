import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils import cstr
import json
import base64
import hashlib
import hmac
import time
from contextlib import contextmanager
from urllib.parse import quote

from frappe.utils.file_manager import save_file
import requests

from portal_app.api import helper


@contextmanager
def _bypass_max_attachments():
	"""Disable Frappe's per-doctype max_attachments cap for the duration of an upload.

	The portal stores many files per Project under the standard folder layout, far above
	the default 4-attachment cap. The proper long-term fix is the Property Setter created
	in install.py (max_attachments=0 on Project), but until `bench migrate` runs we also
	monkey-patch File.validate_attachment_limit at runtime so users aren't blocked.
	"""
	from frappe.core.doctype.file.file import File as _File

	original = _File.validate_attachment_limit
	_File.validate_attachment_limit = lambda self: None
	try:
		yield
	finally:
		_File.validate_attachment_limit = original

PROJ_FOLD_DEFAULT = [
	"01-DOCUMENTS/01-CLIENT DATA/01-BUSINESS CARD",
	"01-DOCUMENTS/01-CLIENT DATA/02-TITLE DEED",
	"01-DOCUMENTS/01-CLIENT DATA/03-ID",
	"01-DOCUMENTS/01-CLIENT DATA/04-MASTER PLAN",
	"01-DOCUMENTS/01-CLIENT DATA/05-AUTHORIZATION LTR",
	"01-DOCUMENTS/01-CLIENT DATA/06-OTHERS",
	"01-DOCUMENTS/02-LOCATION",
	"01-DOCUMENTS/03-BUILDING SYSTEM",
	"01-DOCUMENTS/04-DRAWINGS",
	"01-DOCUMENTS/05-CONSTRUCTION PERMIT",
	"01-DOCUMENTS/06-SITE PICTURE",
	"02-CONCEPT/01-CONCEPT STUDIES/01-ARCHITECTURE",
	"02-CONCEPT/01-CONCEPT STUDIES/02-INTERIORS",
	"02-CONCEPT/01-CONCEPT STUDIES/03-LANDSCAPE",
	"02-CONCEPT/01-CONCEPT STUDIES/04-TECHNICAL",
	"02-CONCEPT/01-CONCEPT STUDIES/05-OPERATIONS",
	"02-CONCEPT/01-CONCEPT STUDIES/06-LIGHTNING",
	"02-CONCEPT/01-CONCEPT STUDIES/07-TRAFFIC",
	"02-CONCEPT/01-CONCEPT STUDIES/08-FIRE FIGHTING",
	"02-CONCEPT/01-CONCEPT STUDIES/09-PROJECT RENDERS",
	"02-CONCEPT/02-SKETCH UP",
	"02-CONCEPT/03-PERSPECTIVES",
	"02-CONCEPT/04-FEASIBILITY STUDY/REF",
	"02-CONCEPT/05-PRESENTATION",
	"02-CONCEPT/06-REFERENCES/ATTLAYERS",
	"02-CONCEPT/06-REFERENCES/SURVEY",
	"02-CONCEPT/07-SCHEDULES & GUIDELINES",
	"03-BALADIYA/01-DOCUMENTS",
	"03-BALADIYA/02-BALADIYA PLANS",
	"03-BALADIYA/03-AREA STATEMENT",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/1. ARCHITECTURAL",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/2. LANDSCAPE",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/3. INTERIOR DESIGN",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/4. CLIENT",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/5. BALADIYA",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/1. ARCHITECTURAL",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/2. LANDSCAPE",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/3. INTERIOR DESIGN",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/4. CLIENT",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/5. BALADIYA",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/02-STRUCTURAL/INCOMING",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/02-STRUCTURAL/OUTGOING",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/03-MECHANICAL/INCOMING",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/03-MECHANICAL/OUTGOING",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/INCOMING/1. ELECTRICAL DRAWINGS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/INCOMING/2. BILL OF QUANTITIES",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/INCOMING/3. PEN ASSIGNMENT",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/OUTGOING/1. ELECTRICAL DRAWINGS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/OUTGOING/2. BILL OF QUANTITIES",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/OUTGOING/3. PEN ASSIGNMENT",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/INCOMING/1. PLUMBING DRAWINGS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/INCOMING/2. PLUMBING CALCULATIONS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/INCOMING/3. PEN ASSIGNMENT",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/OUTGOING/1. PLUMBING DRAWINGS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/OUTGOING/2. PLUMBING CALCULATIONS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/OUTGOING/3. PEN ASSIGNMENT",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/1. SURVEY DRAWINGS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/2. DOCUMENTS",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/3. IMAGES",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/4. DATA",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/OUTGOING",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/07-TECHNICAL FEEDBACK/INCOMING",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/07-TECHNICAL FEEDBACK/OUTGOING",
	"04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/08-TECHNICAL FEASIBILITY",
	"05-SUPERVISION/01-DOCUMENT TRANSMITTAL",
	"05-SUPERVISION/02-PROJECTS",
	"06-CLIENT SUBMITTAL",
]


def _normalize_template_path(raw: str) -> str:
	"""Normalize a relative folder path from template rows/config."""
	v = cstr(raw or "").strip().replace("\\", "/")
	parts = [p.strip() for p in v.split("/") if p and p.strip()]
	if not parts:
		return ""
	if any(p in (".", "..") for p in parts):
		return ""
	return "/".join(parts)


def _folder_template() -> list[str]:
	"""Order: Portal Project Settings table → site_config JSON → built-in default."""
	if frappe.db.exists("DocType", "Portal Folder Template Row") and frappe.db.exists("DocType", "Portal Project Settings"):
		try:
			doc = frappe.get_single("Portal Project Settings")
			rows = doc.get("folder_template") or []
			out = []
			for row in sorted(rows, key=lambda r: int(getattr(r, "idx", 0) or 0)):
				v = _normalize_template_path(getattr(row, "folder_name", None) or "")
				if not v:
					continue
				out.append(v)
			if out:
				return out
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Portal: folder template from settings")

	raw = frappe.conf.get("PORTAL_PROJECT_FOLD_TEMPLATE_JSON")
	if raw:
		try:
			parsed = json.loads(raw)
			if isinstance(parsed, list):
				out = []
				for x in parsed:
					v = _normalize_template_path(x)
					if v:
						out.append(v)
				if out:
					return out
		except Exception:
			pass
	return list(PROJ_FOLD_DEFAULT)


def _ensure_folder(parent: str, file_name: str) -> str:
	file_name = cstr(file_name).strip().strip("/")
	if not file_name:
		return parent
	existing = frappe.db.get_value("File", {"folder": parent, "is_folder": 1, "file_name": file_name}, "name")
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"folder": parent,
			"is_folder": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_folder_path(parent: str, rel_path: str) -> str:
	"""Ensure nested folders under parent for a relative path like A/B/C."""
	cur = parent
	for segment in _normalize_template_path(rel_path).split("/"):
		if not segment:
			continue
		cur = _ensure_folder(cur, segment)
	return cur


def ensure_project_folders(project: str) -> dict:
	"""Create and return project root + subfolders in File manager tree."""
	attachments_root = frappe.db.get_value("File", {"is_attachments_folder": 1}, "name") or "Home/Attachments"
	project_root = _ensure_folder(attachments_root, project)
	subfolders = []
	seen = set()
	for rel in _folder_template():
		cur_parent = project_root
		current_parts = []
		for seg in rel.split("/"):
			current_parts.append(seg)
			cur_rel = "/".join(current_parts)
			if cur_rel in seen:
				cur_parent = f"{project_root}/{cur_rel}"
				continue
			fname = _ensure_folder(cur_parent, seg)
			subfolders.append({"name": fname, "label": cur_rel})
			seen.add(cur_rel)
			cur_parent = fname
	return {"project_root": project_root, "subfolders": subfolders}


def _b64url(data: bytes) -> str:
	return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
	padding = "=" * ((4 - len(data) % 4) % 4)
	return base64.urlsafe_b64decode((data + padding).encode())


def _share_secret() -> str:
	return cstr(frappe.conf.get("encryption_key") or frappe.conf.get("secret") or "portal_app_share_secret")


def _sign_share_payload(payload: dict) -> str:
	payload_raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
	payload_part = _b64url(payload_raw)
	sig = hmac.new(_share_secret().encode(), payload_part.encode(), hashlib.sha256).hexdigest()
	return f"{payload_part}.{sig}"


def _verify_share_token(token: str) -> dict:
	token = cstr(token).strip()
	if "." not in token:
		frappe.throw(_("Invalid share token"), frappe.PermissionError)
	payload_part, sig = token.rsplit(".", 1)
	expected_sig = hmac.new(_share_secret().encode(), payload_part.encode(), hashlib.sha256).hexdigest()
	if not hmac.compare_digest(expected_sig, sig):
		frappe.throw(_("Invalid share token signature"), frappe.PermissionError)
	try:
		payload = json.loads(_b64url_decode(payload_part).decode())
	except Exception:
		frappe.throw(_("Invalid share token payload"), frappe.PermissionError)
	exp = int(payload.get("exp") or 0)
	if exp and int(time.time()) > exp:
		frappe.throw(_("This share link has expired"), frappe.PermissionError)
	return payload


@frappe.whitelist()
def list_project_files(project):
	helper.assert_project_access(project)
	folders = ensure_project_folders(project)
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Project", "attached_to_name": project},
		fields=[
			"name",
			"file_name",
			"file_url",
			"folder",
			"is_folder",
			"is_private",
			"creation",
			"owner",
			"file_size",
		],
		order_by="creation desc",
	)
	return {"files": files, "settings": helper.get_portal_settings_dict(), "folders": folders}


@frappe.whitelist()
def list_project_folders(project):
	helper.assert_project_access(project)
	return ensure_project_folders(project)


@frappe.whitelist()
def delete_project_file(file_name):
	doc = frappe.get_doc("File", file_name)
	if doc.attached_to_doctype != "Project" or not doc.attached_to_name:
		frappe.throw(_("Not a project file"))
	project_name = doc.attached_to_name
	helper.assert_project_access(project_name)
	if doc.is_folder:
		frappe.throw(_("Folder rows cannot be deleted here; use ERPNext File Manager if needed."))
	if not helper.can_manage_project(project_name) and doc.owner != frappe.session.user:
		frappe.throw(
			_("Only the project manager or the user who uploaded this file can delete it."),
			frappe.PermissionError,
		)
	frappe.delete_doc("File", file_name, ignore_permissions=True)
	return {"ok": True}


@frappe.whitelist()
def rename_project_subfolder(project, folder_path, new_folder_name):
	"""Rename one folder segment under the project attachment root (supports nested levels)."""
	helper.assert_manage_project(project)
	new_segment = cstr(new_folder_name or "").strip()
	if not new_segment or "/" in new_segment or "\\" in new_segment or ".." in new_segment:
		frappe.throw(_("Invalid folder name. Use a single name without slashes."))
	folder_ctx = ensure_project_folders(project)
	root = folder_ctx["project_root"].replace("\\", "/")
	fp = cstr(folder_path or "").replace("\\", "/").strip()
	if not fp or fp == root:
		frappe.throw(_("Select a subfolder to rename"))
	if not fp.startswith(root + "/"):
		frappe.throw(_("This folder is not under this project’s portal tree"))
	fd = frappe.get_doc("File", fp)
	if not fd.is_folder:
		frappe.throw(_("Not a folder"))
	parent_path = fp.rsplit("/", 1)[0]
	if not parent_path.startswith(root):
		frappe.throw(_("Invalid folder parent path"))
	new_path = f"{parent_path}/{new_segment}"
	if new_path == fp:
		return {"old": fp, "new": new_path}
	if frappe.db.exists("File", new_path):
		frappe.throw(_("A file or folder with that name already exists"))
	frappe.rename_doc("File", fp, new_path, force=True, merge=False)
	return {"old": fp, "new": new_path}


def _resolve_share_folder(project: str, folder_hint: str) -> tuple[str, str]:
	"""Return (canonical File folder name, human label) for project root or a template subfolder."""
	folder_ctx = ensure_project_folders(project)
	root = folder_ctx["project_root"]
	hint = cstr(folder_hint).strip()
	if not hint:
		frappe.throw(_("Select a folder for the share link."))
	hint_norm = hint.replace("\\", "/")
	root_norm = root.replace("\\", "/")
	# Project root: entire project folder tree under File manager
	if hint in ("__project_root__", "__root__"):
		return root, _("Project folder (all files)")
	if hint_norm == root_norm:
		return root, _("Project folder (all files)")
	for row in folder_ctx["subfolders"]:
		path = row["name"]
		label = row.get("label") or ""
		path_norm = path.replace("\\", "/")
		if path_norm == hint_norm or label == hint:
			return path, label
		if path_norm.endswith("/" + hint.lstrip("/")) or path == hint:
			return path, label
	frappe.throw(_("Invalid project folder selected."))


def _share_doctype_available() -> bool:
	return bool(frappe.db.exists("DocType", "Portal Folder Share"))


def _share_record_for_token(token: str):
	"""Return Portal Folder Share dict for a signed token if it exists and is active."""
	if not _share_doctype_available():
		return None
	rows = frappe.get_all(
		"Portal Folder Share",
		filters={"share_token": token, "share_kind": "Link"},
		fields=["name", "project", "folder_path", "folder_label", "revoked", "expires_at"],
		limit_page_length=1,
	)
	return rows[0] if rows else None


def _share_record_active(rec: dict) -> bool:
	if not rec:
		return False
	if int(rec.get("revoked") or 0):
		return False
	exp = rec.get("expires_at")
	if exp:
		from frappe.utils import get_datetime, now_datetime

		if get_datetime(exp) < now_datetime():
			return False
	return True


def _expiry_datetime(days: int):
	from frappe.utils import add_days, now_datetime

	return add_days(now_datetime(), int(days))


@frappe.whitelist()
def create_folder_share_link(project, folder_path=None, folder=None, expires_days=7):
	# Any user allocated to the project can create share links / share with people on
	# their team. This matches Drive-style collaboration where every member can share.
	helper.assert_project_access(project)
	# Prefer folder_path — avoids confusion with generic "folder" and matches portal UI.
	hint = cstr(folder_path or folder or "").strip()
	canonical, label = _resolve_share_folder(project, hint)
	try:
		expires_days = max(1, min(365, int(expires_days)))
	except Exception:
		expires_days = 7
	now = int(time.time())
	payload = {"p": project, "f": canonical, "iat": now, "exp": now + (expires_days * 86400)}
	token = _sign_share_payload(payload)
	url = frappe.utils.get_url(f"/portal-app/shared-folder?token={quote(token)}")

	share_name = None
	tracking_available = _share_doctype_available()
	if tracking_available:
		doc = frappe.get_doc(
			{
				"doctype": "Portal Folder Share",
				"project": project,
				"folder_path": canonical,
				"folder_label": label,
				"share_kind": "Link",
				"share_token": token,
				"share_url": url,
				"expires_at": _expiry_datetime(expires_days),
				"created_by_user": frappe.session.user,
			}
		)
		doc.insert(ignore_permissions=True)
		share_name = doc.name

	return {
		"url": url,
		"expires_days": expires_days,
		"folder": canonical,
		"folder_label": label,
		"share_name": share_name,
		"tracking_available": tracking_available,
	}


@frappe.whitelist()
def share_folder_with_user(project, folder_path, user_id, expires_days=30):
	"""Grant a portal user read access to all files in a folder (and its subfolders).

	Falls back to ERPNext-native DocShare alone when the Portal Folder Share doctype
	is not yet installed; the user still gets read access through Frappe's built-in
	sharing system, just without the audit log of who-shared-what.

	Any user allocated to the project may share its folders with a teammate (Drive-style
	collaboration). Revoking is restricted to managers + the user who created the share.
	"""
	helper.assert_project_access(project)
	tracking_available = _share_doctype_available()

	canonical, label = _resolve_share_folder(project, cstr(folder_path or "").strip())
	uid = cstr(user_id or "").strip()
	if not uid:
		frappe.throw(_("User is required."))
	if not frappe.db.exists("User", uid):
		frappe.throw(_("User {0} not found.").format(uid))
	if uid in {"Guest", "Administrator"}:
		frappe.throw(_("Cannot share folder with {0}.").format(uid))

	try:
		expires_days = max(1, min(365, int(expires_days)))
	except Exception:
		expires_days = 30

	user_row = frappe.db.get_value("User", uid, ["email", "full_name"], as_dict=True) or {}

	share_name = None
	expires_at_value = None
	if tracking_available:
		# Reuse an existing active record if present (extend its expiry instead of duplicating).
		existing = frappe.get_all(
			"Portal Folder Share",
			filters={
				"project": project,
				"folder_path": canonical,
				"share_kind": "User",
				"user": uid,
				"revoked": 0,
			},
			fields=["name"],
			limit_page_length=1,
		)
		if existing:
			doc = frappe.get_doc("Portal Folder Share", existing[0]["name"])
			doc.expires_at = _expiry_datetime(expires_days)
			doc.user_email = user_row.get("email") or doc.user_email
			doc.user_full_name = user_row.get("full_name") or doc.user_full_name
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Portal Folder Share",
					"project": project,
					"folder_path": canonical,
					"folder_label": label,
					"share_kind": "User",
					"user": uid,
					"user_email": user_row.get("email"),
					"user_full_name": user_row.get("full_name"),
					"expires_at": _expiry_datetime(expires_days),
					"created_by_user": frappe.session.user,
				}
			)
			doc.insert(ignore_permissions=True)
		share_name = doc.name
		expires_at_value = str(doc.expires_at) if doc.get("expires_at") else None

	# Grant ERPNext-native DocShare on:
	#  1. The File folder itself (so the user can list folder contents)
	#  2. Every File doc nested under that folder (so each individual file is readable)
	#  3. The parent Project doc (read only) so the user can navigate to it from the portal
	#
	# Frappe's File-level permission does not "cascade" — each child File doc needs its own
	# DocShare row for the user to actually open it. We also tag the Project so it appears
	# under the user's "Shared with me" view in this portal.
	docshare_ok = False
	docshare_count = 0

	def _grant(doctype, name, read=1, write=0):
		nonlocal docshare_count
		try:
			import frappe.share as _share

			_share.add(
				doctype,
				name,
				uid,
				read=read,
				write=write,
				flags={"ignore_share_permission": True},
				notify=0,
			)
			docshare_count += 1
			return True
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Portal: docshare grant {doctype}/{name}")
			return False

	docshare_ok = _grant("File", canonical)
	# Every nested File (folder OR file) under this folder.
	nested = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Project",
			"attached_to_name": project,
		},
		or_filters=[["folder", "=", canonical], ["folder", "like", canonical + "/%"]],
		fields=["name"],
		limit_page_length=2000,
	)
	for row in nested:
		_grant("File", row["name"])
	# Parent Project doc — read-only access for navigation.
	if frappe.db.exists("Project", project):
		_grant("Project", project)

	return {
		"ok": True,
		"share_name": share_name,
		"folder": canonical,
		"folder_label": label,
		"user": uid,
		"user_email": user_row.get("email"),
		"user_full_name": user_row.get("full_name"),
		"expires_at": expires_at_value,
		"docshare_ok": docshare_ok,
		"docshare_count": docshare_count,
		"tracking_available": tracking_available,
	}


@frappe.whitelist()
def list_folder_shares(project, folder_path=None):
	"""Return active shares for one folder, or all folders in a project (folder_path omitted).

	When the Portal Folder Share doctype is not yet installed, returns the ERPNext-native
	DocShare entries for the requested folder so users can still see who has access via
	Frappe's built-in sharing system. Visible to any user allocated to the project.
	"""
	helper.assert_project_access(project)
	if not _share_doctype_available():
		return {"shares": _list_native_docshares(project, folder_path), "tracking_available": False}

	filters = {"project": project, "revoked": 0}
	if folder_path:
		canonical, _label = _resolve_share_folder(project, cstr(folder_path or "").strip())
		filters["folder_path"] = canonical

	rows = frappe.get_all(
		"Portal Folder Share",
		filters=filters,
		fields=[
			"name",
			"project",
			"folder_path",
			"folder_label",
			"share_kind",
			"user",
			"user_email",
			"user_full_name",
			"share_url",
			"expires_at",
			"created_by_user",
			"creation",
			"last_accessed_at",
			"access_count",
		],
		order_by="creation desc",
		limit_page_length=200,
	)

	from frappe.utils import get_datetime, now_datetime

	now_dt = now_datetime()
	shares = []
	for r in rows:
		exp = r.get("expires_at")
		if exp and get_datetime(exp) < now_dt:
			continue
		shares.append(r)
	return {"shares": shares, "tracking_available": True}


def _list_native_docshares(project: str, folder_path: str | None) -> list[dict]:
	"""Read ERPNext DocShare rows on a File folder so the modal works even when our
	Portal Folder Share tracking doctype hasn't been installed yet."""
	if not folder_path:
		return []
	try:
		canonical, label = _resolve_share_folder(project, cstr(folder_path).strip())
	except Exception:
		return []
	rows = frappe.get_all(
		"DocShare",
		filters={"share_doctype": "File", "share_name": canonical, "user": ["!=", ""]},
		fields=["name", "user", "read", "write", "share", "creation"],
		order_by="creation desc",
		limit_page_length=200,
	)
	out = []
	for r in rows:
		u = frappe.db.get_value("User", r.get("user"), ["email", "full_name"], as_dict=True) or {}
		out.append(
			{
				"name": r.get("name"),
				"project": project,
				"folder_path": canonical,
				"folder_label": label,
				"share_kind": "User",
				"user": r.get("user"),
				"user_email": u.get("email"),
				"user_full_name": u.get("full_name"),
				"share_url": None,
				"expires_at": None,
				"created_by_user": None,
				"creation": r.get("creation"),
				"native": True,
			}
		)
	return out


@frappe.whitelist()
def revoke_folder_share(share_name):
	"""Revoke a share by record name. Removes ERPNext DocShare for user shares.

	When the Portal Folder Share doctype isn't installed, falls back to revoking the
	corresponding ERPNext DocShare row directly (the share modal will pass us the
	DocShare row name in that case).
	"""
	if not _share_doctype_available():
		# Fallback: treat share_name as a DocShare row.
		try:
			row = frappe.db.get_value(
				"DocShare",
				share_name,
				["share_doctype", "share_name", "user"],
				as_dict=True,
			)
		except Exception:
			row = None
		if not row:
			frappe.throw(_("Share record not found."))
		if row.get("share_doctype") != "File":
			frappe.throw(_("Not a folder share."))
		project_for_folder = frappe.db.get_value(
			"File",
			{"name": row.get("share_name"), "is_folder": 1},
			"file_name",
		)
		if project_for_folder:
			# Native DocShare rows have no created_by audit, so only managers may revoke.
			helper.assert_manage_project(project_for_folder)
		try:
			import frappe.share as _share

			_share.remove("File", row.get("share_name"), row.get("user"))
		except Exception:
			frappe.delete_doc("DocShare", share_name, ignore_permissions=True)
		return {"ok": True, "share_name": share_name, "native": True}

	doc = frappe.get_doc("Portal Folder Share", share_name)
	# Project members can revoke shares they themselves created. Managers can revoke any.
	helper.assert_project_access(doc.project)
	if not helper.can_manage_project(doc.project) and doc.created_by_user != frappe.session.user:
		frappe.throw(
			_("You can only revoke shares you created yourself. Ask a project manager to revoke this one."),
			frappe.PermissionError,
		)
	if int(doc.revoked or 0):
		return {"ok": True, "already_revoked": True}

	from frappe.utils import now_datetime

	doc.revoked = 1
	doc.revoked_by = frappe.session.user
	doc.revoked_at = now_datetime()
	doc.save(ignore_permissions=True)

	if doc.share_kind == "User" and doc.user and doc.folder_path:
		_revoke_folder_docshares(doc.project, doc.folder_path, doc.user)

	return {"ok": True, "share_name": doc.name}


def _revoke_folder_docshares(project: str, folder: str, user: str) -> None:
	"""Drop the DocShares we granted in share_folder_with_user.

	Removes:
	  - The folder itself
	  - Every File doc under that folder (attached to this Project)
	  - The parent Project doc — but ONLY if the user has no other active Portal
	    Folder Share for this project (otherwise other shares would break).
	"""
	import frappe.share as _share

	def _safe_remove(doctype, name):
		try:
			_share.remove(doctype, name, user)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Portal: docshare remove {doctype}/{name}")

	_safe_remove("File", folder)
	nested = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Project",
			"attached_to_name": project,
		},
		or_filters=[["folder", "=", folder], ["folder", "like", folder + "/%"]],
		fields=["name"],
		limit_page_length=2000,
	)
	for row in nested:
		_safe_remove("File", row["name"])

	# Only drop the Project share if no other active Portal Folder Share remains for
	# (project, user). Otherwise the other share would lose its navigability.
	other_active = frappe.db.count(
		"Portal Folder Share",
		{"project": project, "user": user, "share_kind": "User", "revoked": 0},
	)
	if not other_active:
		_safe_remove("Project", project)


@frappe.whitelist()
def list_shared_with_me():
	"""Return all folders + files shared with the current user, grouped by project.

	Combines two sources:
	  - Portal Folder Share rows (Auditor-tracked, with expiry / revoke)
	  - Native ERPNext DocShare rows on File / Project (so things shared from Desk also show up)

	Each project entry includes the folders the user can access plus the actual files
	visible inside those folders. The portal renders this on the "Shared with me" page.
	"""
	if frappe.session.user in ("Guest", "Administrator"):
		return {"projects": []}

	user = frappe.session.user
	from frappe.utils import get_datetime, now_datetime

	now_dt = now_datetime()
	folders_by_project: dict[str, list[dict]] = {}

	# 1. Portal Folder Share (preferred — has expiry + audit info)
	if _share_doctype_available():
		rows = frappe.get_all(
			"Portal Folder Share",
			filters={"user": user, "share_kind": "User", "revoked": 0},
			fields=[
				"name",
				"project",
				"folder_path",
				"folder_label",
				"expires_at",
				"created_by_user",
				"creation",
			],
			limit_page_length=500,
		)
		for r in rows:
			exp = r.get("expires_at")
			if exp and get_datetime(exp) < now_dt:
				continue
			folders_by_project.setdefault(r["project"], []).append(
				{
					"share_name": r["name"],
					"folder_path": r["folder_path"],
					"folder_label": r.get("folder_label") or r["folder_path"],
					"expires_at": str(r["expires_at"]) if r.get("expires_at") else None,
					"shared_by": r.get("created_by_user"),
					"shared_on": str(r.get("creation")) if r.get("creation") else None,
					"native": False,
				}
			)

	# 2. Native ERPNext DocShare on File folders (covers shares done from Desk)
	docshare_rows = frappe.get_all(
		"DocShare",
		filters={"share_doctype": "File", "user": user, "read": 1},
		fields=["share_name", "creation"],
		limit_page_length=2000,
	)
	for r in docshare_rows:
		fname = r["share_name"]
		# Only include folders whose name pattern looks like a project folder
		# (Home/Attachments/<project>/...). This filters out non-project share noise.
		file_row = frappe.db.get_value(
			"File",
			fname,
			["is_folder", "folder", "file_name", "attached_to_doctype", "attached_to_name"],
			as_dict=True,
		)
		if not file_row:
			continue
		project = None
		# Folder rows: derive project from path "Home/Attachments/<project>/..."
		parts = fname.split("/")
		if len(parts) >= 3 and parts[0] == "Home" and parts[1] == "Attachments":
			project = parts[2]
		elif file_row.get("attached_to_doctype") == "Project":
			project = file_row.get("attached_to_name")
		if not project or not frappe.db.exists("Project", project):
			continue
		# Skip if a Portal Folder Share already covers this folder.
		if any(f["folder_path"] == fname for f in folders_by_project.get(project, [])):
			continue
		# Build a label relative to the project root.
		project_root = f"Home/Attachments/{project}"
		label = fname[len(project_root) + 1 :] if fname.startswith(project_root + "/") else fname
		folders_by_project.setdefault(project, []).append(
			{
				"share_name": r.get("share_name") or fname,
				"folder_path": fname,
				"folder_label": label or _("Project folder (all files)"),
				"expires_at": None,
				"shared_by": None,
				"shared_on": str(r.get("creation")) if r.get("creation") else None,
				"native": True,
			}
		)

	# Hydrate projects with metadata + the actual files visible per folder.
	projects_out = []
	for project, folders in folders_by_project.items():
		project_meta = (
			frappe.db.get_value(
				"Project",
				project,
				["name", "project_name", "status", "customer"],
				as_dict=True,
			)
			or {"name": project, "project_name": project}
		)
		# Sort folders by depth then name so the project root sits first.
		folders.sort(key=lambda f: (f["folder_label"].count("/"), f["folder_label"].lower()))
		# Files visible to this user under each folder.
		for folder in folders:
			fpath = folder["folder_path"]
			files = frappe.get_all(
				"File",
				filters={
					"attached_to_doctype": "Project",
					"attached_to_name": project,
					"is_folder": 0,
				},
				or_filters=[["folder", "=", fpath], ["folder", "like", fpath + "/%"]],
				fields=["name", "file_name", "file_url", "folder", "file_size", "is_private", "creation"],
				order_by="creation desc",
				limit_page_length=400,
			)
			folder["file_count"] = len(files)
			folder["files"] = files
		projects_out.append(
			{
				"project": project_meta.get("name") or project,
				"project_name": project_meta.get("project_name") or project,
				"status": project_meta.get("status"),
				"customer": project_meta.get("customer"),
				"folders": folders,
			}
		)

	projects_out.sort(key=lambda p: (p.get("project_name") or "").lower())
	return {"projects": projects_out}


@frappe.whitelist()
def extend_folder_share(share_name, expires_days=30):
	if not _share_doctype_available():
		frappe.throw(_("Per-share expiry tracking is unavailable on this site. Re-share to refresh access."))
	doc = frappe.get_doc("Portal Folder Share", share_name)
	helper.assert_project_access(doc.project)
	if not helper.can_manage_project(doc.project) and doc.created_by_user != frappe.session.user:
		frappe.throw(
			_("You can only extend shares you created yourself."),
			frappe.PermissionError,
		)
	try:
		expires_days = max(1, min(365, int(expires_days)))
	except Exception:
		expires_days = 30
	if int(doc.revoked or 0):
		frappe.throw(_("This share has been revoked."))
	doc.expires_at = _expiry_datetime(expires_days)
	doc.save(ignore_permissions=True)
	return {"ok": True, "expires_at": str(doc.expires_at)}


@frappe.whitelist(allow_guest=True)
def get_shared_folder_files(token):
	payload = _verify_share_token(token)
	project = cstr(payload.get("p")).strip()
	folder = cstr(payload.get("f")).strip()
	if not project or not folder:
		frappe.throw(_("Invalid share link payload"), frappe.PermissionError)

	# If a Portal Folder Share record exists for this token (newer flow),
	# verify it is still active. Older tokens without a record remain valid until expiry.
	rec = _share_record_for_token(token)
	if rec is not None and not _share_record_active(rec):
		frappe.throw(_("This share link has been revoked or expired."), frappe.PermissionError)

	# Best-effort access tracking.
	if rec:
		try:
			from frappe.utils import now_datetime

			frappe.db.set_value(
				"Portal Folder Share",
				rec["name"],
				{
					"last_accessed_at": now_datetime(),
					"access_count": int(rec.get("access_count") or 0) + 1,
				},
				update_modified=False,
			)
			frappe.db.commit()
		except Exception:
			pass

	# Guest must not run ensure_project_folders. Derive label from path / project id.
	norm = folder.replace("\\", "/") if folder else ""
	last = norm.split("/")[-1] if norm else ""
	folder_label_resolved = (
		_("Project folder (all files)") if last == project else last
	)
	# Files directly in this folder or in nested folders under it.
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Project",
			"attached_to_name": project,
			"is_private": 0,
			"is_folder": 0,
		},
		or_filters=[["folder", "=", folder], ["folder", "like", folder + "/%"]],
		fields=["name", "file_name", "file_url", "creation", "file_size"],
		order_by="creation desc",
	)
	project_title = frappe.db.get_value("Project", project, "project_name") or project
	return {
		"project": project,
		"project_name": project_title,
		"folder": folder,
		"folder_label": folder_label_resolved,
		"files": files,
		"expires_at": int(payload.get("exp") or 0),
	}


@frappe.whitelist()
def upload_project_file():
	project = frappe.form_dict.get("project")
	if not project:
		frappe.throw(_("project is required"))
	helper.assert_customer_portal_can_upload(project)

	upload = frappe.request.files.get("file")
	if not upload:
		frappe.throw(_("No file uploaded"))

	content = upload.stream.read()
	if not content:
		frappe.throw(_("Empty file"))

	fname = upload.filename or "upload"
	is_private = cint(frappe.form_dict.get("is_private", 0))
	destination = cstr(frappe.form_dict.get("destination") or "erpnext").strip().lower()
	external_provider = cstr(frappe.form_dict.get("external_provider") or "").strip().lower()
	target_folder = cstr(frappe.form_dict.get("target_folder") or "").strip()

	if destination not in {"erpnext", "external", "both"}:
		frappe.throw(_("Invalid destination. Use erpnext, external, or both."))

	settings = helper.get_portal_settings_dict()

	def _provider_label(p):
		return {
			"frappe_drive": "Frappe Drive",
			"google_drive": "Google Drive",
			"bim360": "BIM 360 / ACC",
		}.get(p, p)

	def _provider_enabled(p):
		if p == "frappe_drive":
			return bool(settings.get("use_frappe_drive"))
		if p == "google_drive":
			return bool(settings.get("google_drive_enabled"))
		if p == "bim360":
			return bool(settings.get("bim_360_enabled"))
		return False

	def _provider_webhook(p):
		key_map = {
			"frappe_drive": "frappe_drive_upload_webhook",
			"google_drive": "google_drive_upload_webhook",
			"bim360": "bim_360_upload_webhook",
		}
		fallback_env_map = {
			"frappe_drive": "PORTAL_FRAPPE_DRIVE_UPLOAD_WEBHOOK",
			"google_drive": "PORTAL_GOOGLE_DRIVE_UPLOAD_WEBHOOK",
			"bim360": "PORTAL_BIM360_UPLOAD_WEBHOOK",
		}
		cfg_key = key_map.get(p)
		webhook = cstr(settings.get(cfg_key) if cfg_key else "").strip()
		if webhook:
			return webhook
		# Backward-compatible fallback for existing installs
		env_key = fallback_env_map.get(p)
		return cstr(frappe.conf.get(env_key) if env_key else "").strip()

	def _send_external():
		if not external_provider:
			frappe.throw(_("Select an external provider for external upload mode."))
		if not _provider_enabled(external_provider):
			frappe.throw(_("{0} is not enabled in Portal Project Settings.").format(_provider_label(external_provider)))
		webhook = _provider_webhook(external_provider)
		if not webhook:
			frappe.throw(
				_(
					"External webhook is not configured for {0}. Set it in Portal Project Settings."
				).format(
					_provider_label(external_provider),
				)
			)

		files = {"file": (fname, content)}
		data = {
			"project": project,
			"is_private": str(is_private),
			"provider": external_provider,
			"uploaded_by": frappe.session.user,
		}
		resp = requests.post(webhook, files=files, data=data, timeout=90)
		if resp.status_code >= 400:
			frappe.throw(
				_("External upload failed for {0}: HTTP {1}").format(_provider_label(external_provider), resp.status_code)
			)
		try:
			payload = resp.json()
		except Exception:
			payload = {"raw": resp.text}
		return payload

	external_result = None
	if destination in {"external", "both"}:
		external_result = _send_external()

	doc = None
	folder_label_resolved = None
	if destination in {"erpnext", "both"}:
		folder_ctx = ensure_project_folders(project)
		valid_folders = {x["name"]: x.get("label") for x in folder_ctx["subfolders"]}
		# Allow uploading directly into the project root as well.
		if folder_ctx.get("project_root"):
			valid_folders[folder_ctx["project_root"]] = _("Project folder (all files)")
		if not target_folder:
			frappe.throw(_("Select a target project folder before upload."))
		if target_folder not in valid_folders:
			frappe.throw(_("Invalid target folder selected."))
		folder_label_resolved = valid_folders.get(target_folder)
		with _bypass_max_attachments():
			doc = save_file(fname, content, "Project", project, folder=target_folder, is_private=is_private)
		# Belt-and-braces: if some hook reset the folder, force it back.
		if doc and doc.folder != target_folder:
			frappe.db.set_value("File", doc.name, "folder", target_folder, update_modified=False)
			doc.folder = target_folder

	return {
		"name": doc.name if doc else None,
		"file_url": doc.file_url if doc else None,
		"file_name": doc.file_name if doc else fname,
		"folder": doc.folder if doc else None,
		"folder_label": folder_label_resolved,
		"destination": destination,
		"external_provider": external_provider or None,
		"external_result": external_result,
	}


@frappe.whitelist()
def get_file_download_url(file_name):
	f = frappe.get_doc("File", file_name)
	if f.attached_to_doctype != "Project":
		frappe.throw(_("Invalid file"))

	helper.assert_project_access(f.attached_to_name)

	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return {"url": f.file_url, "file_name": f.file_name}
