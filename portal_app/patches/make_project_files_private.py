"""Move already-uploaded project files out of public storage.

Until this patch, `upload_project_files_zip` hardcoded `is_private=0` and the
single-file upload defaulted to public, so every document attached to a Project —
including the template's "01-CLIENT DATA/02-TITLE DEED" and "03-ID" folders — was
written to sites/<site>/public/files and served at /files/<name> with no session
check at all. Anyone who knew or guessed the filename could download it
anonymously, and revoking a share did not take the file offline.

The flag must be flipped through the File document, not with frappe.db.set_value:
only File.save() relocates the bytes from public/files to private/files and
rewrites file_url. A bare DB update would leave the public copy on disk and the
old URL live, which is exactly the thing being fixed.

Idempotent: re-running only looks at rows that are still public.
"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "File"):
		return

	names = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Project",
			"is_private": 0,
			"is_folder": 0,
		},
		pluck="name",
	)
	if not names:
		return

	migrated = 0
	failed = 0
	for name in names:
		try:
			doc = frappe.get_doc("File", name)
			doc.is_private = 1
			doc.save(ignore_permissions=True)
			migrated += 1
		except Exception:
			failed += 1
			frappe.log_error(frappe.get_traceback(), "portal_app: make project file private " + name)

	frappe.db.commit()
	print(f"portal_app: made {migrated} project file(s) private, {failed} failed")
