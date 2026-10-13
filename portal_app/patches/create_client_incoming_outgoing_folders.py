import frappe

from portal_app.api import files


def execute():
	"""Give every existing project the client folder's Incoming and Outgoing subfolders and
	sort the files that were sitting loose in the client folder: what a client uploaded goes
	to Outgoing, everything else (what ATA submitted) to Incoming.

	A project whose folder tree has not been created yet is skipped: it gets the whole
	template, these two folders included, the first time anyone opens its files. Creating
	just this branch for it would make the portal think the tree already exists."""
	if not frappe.db.exists("DocType", "File"):
		return
	root = frappe.db.get_value("File", {"is_attachments_folder": 1}, "name")
	if not root:
		return
	for row in frappe.get_all("File", filters={"is_folder": 1, "folder": root}, fields=["name", "file_name"]):
		project = row.file_name
		if not frappe.db.exists("Project", project):
			continue
		if not frappe.db.exists("File", {"is_folder": 1, "folder": row.name}):
			continue
		files.setup_client_folders(project)
