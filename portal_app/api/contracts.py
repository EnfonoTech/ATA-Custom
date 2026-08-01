from __future__ import annotations

import os

import frappe
from frappe import _
from frappe.utils import cstr
from frappe.utils.file_manager import save_file

from portal_app.api import helper

# Contracts live in their own folder tree (Home/Contracts/<project>), entirely
# separate from the general project Files area (Home/Attachments/<project>/...).
# Every endpoint here requires management-level access to the project — this
# is deliberately NOT visible to regular team members the way normal project
# files are.

# Signed contracts are either an office document or a scan of one.
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}


def _ensure_folder(file_name: str, parent: str) -> str:
    existing = frappe.db.get_value(
        "File", {"file_name": file_name, "folder": parent, "is_folder": 1}, "name"
    )
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": file_name,
            "folder": parent,
            "is_folder": 1,
            "is_private": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def ensure_project_contracts_folder(project: str) -> str:
    _ensure_folder("Contracts", "Home")
    return _ensure_folder(project, "Home/Contracts")


@frappe.whitelist()
def list_contract_files(project):
    helper.assert_manage_project(project)
    folder = ensure_project_contracts_folder(project)
    return frappe.get_all(
        "File",
        filters={"folder": folder, "is_folder": 0},
        fields=["name", "file_name", "file_url", "file_size", "creation", "owner"],
        order_by="creation desc",
    )


@frappe.whitelist()
def upload_contract_file(project):
    helper.assert_manage_project(project)

    upload = frappe.request.files.get("file")
    if not upload:
        frappe.throw(_("No file uploaded"))

    content = upload.stream.read()
    if not content:
        frappe.throw(_("Empty file"))

    fname = cstr(upload.filename or "contract")
    ext = os.path.splitext(fname)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        frappe.throw(
            _("Unsupported file type {0}. Allowed types: {1}").format(
                ext or "(none)", ", ".join(sorted(ALLOWED_EXTENSIONS))
            )
        )

    folder = ensure_project_contracts_folder(project)
    doc = save_file(fname, content, "Project", project, folder=folder, is_private=1)
    return {
        "name": doc.name,
        "file_name": doc.file_name,
        "file_url": doc.file_url,
        "file_size": doc.file_size,
    }


@frappe.whitelist()
def delete_contract_file(project, file_name):
    helper.assert_manage_project(project)
    folder = ensure_project_contracts_folder(project)
    doc = frappe.get_doc("File", file_name)
    if doc.folder != folder or doc.is_folder:
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    doc.delete(ignore_permissions=True)
    return {"ok": True}
