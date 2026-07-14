import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def ensure_department_portal_custom_fields():
	if not frappe.db.exists("DocType", "Department"):
		return

	create_custom_fields(
		{
			"Department": [
				{
					"fieldname": "portal_office",
					"label": "Portal Office",
					"fieldtype": "Data",
					"insert_after": "department_name",
					"in_list_view": 1,
					"description": "Office location tag used by the portal Teams page (e.g. RIYADH, LISBON, MANILA)",
				},
			]
		},
		update=True,
	)
	frappe.clear_cache(doctype="Department")


def ensure_project_portal_custom_fields():
	if not frappe.db.exists("DocType", "Project"):
		return

	create_custom_fields(
		{
			"Project": [
				{
					"fieldname": "portal_project_code",
					"label": "Portal Project Code",
					"fieldtype": "Data",
					"insert_after": "project_name",
					"description": "Short reference code for the portal (FR-PM-001)",
				},
				{
					"fieldname": "portal_project_manager",
					"label": "Portal Project Manager",
					"fieldtype": "Link",
					"options": "User",
					"insert_after": "portal_project_code",
					"description": "Manager with full project control in the portal",
				},
				{
					"fieldname": "portal_kanban_stage",
					"label": "Portal Kanban Stage",
					"fieldtype": "Select",
					"options": "Planning\nActive\nOn Hold\nReview\nDone",
					"default": "Planning",
					"insert_after": "status",
					"in_list_view": 1,
					"description": "Visual workflow stage for Kanban (FR-PM-002)",
				},
				{
					"fieldname": "portal_office",
					"label": "Portal Office",
					"fieldtype": "Data",
					"insert_after": "portal_kanban_stage",
					"description": "Office location for this project (e.g. RIYADH, LISBON, MANILA)",
				},
				{
					"fieldname": "portal_phase",
					"label": "Portal Phase",
					"fieldtype": "Select",
					"options": "\nSchematic Design\nCD\nCD+\nDD\nTD\nFC\nConstruction",
					"insert_after": "portal_office",
					"description": "Architectural phase of this project",
				},
				{
					"fieldname": "portal_project_server",
					"label": "Portal Project Server",
					"fieldtype": "Data",
					"insert_after": "portal_project_manager",
					"description": "Project server name or URL shown in the portal",
				},
				{
					"fieldname": "portal_upcoming_milestone",
					"label": "Portal Upcoming Milestone",
					"fieldtype": "Data",
					"insert_after": "portal_project_server",
					"description": "Next upcoming milestone for this project",
				},
				{
					"fieldname": "portal_server_t",
					"label": "T-Server (Google Drive)",
					"fieldtype": "Data",
					"insert_after": "portal_upcoming_milestone",
					"description": "Link to this project's folder on Google Drive",
				},
				{
					"fieldname": "portal_server_a",
					"label": "A-Server (Autodesk)",
					"fieldtype": "Data",
					"insert_after": "portal_server_t",
					"description": "Link to this project on the Autodesk (BIM) server",
				},
				{
					"fieldname": "portal_server_c",
					"label": "C-Server (Client / AWS)",
					"fieldtype": "Data",
					"insert_after": "portal_server_a",
					"description": "Link to this project's client folder on the AWS server",
				},
				{
					"fieldname": "portal_team",
					"label": "Portal Team",
					"fieldtype": "Link",
					"options": "Department",
					"insert_after": "portal_office",
					"description": "Team (Department) this project belongs to — groups it on the portal Gantt Chart",
				},
			]
		},
		update=True,
	)

	frappe.clear_cache(doctype="Project")


def ensure_portal_customer_access():
	"""Link User → Customer for client portal login; role Portal Customer."""
	if not frappe.db.exists("DocType", "User"):
		return

	from portal_app.api import helper

	helper.ensure_portal_customer_role()

	create_custom_fields(
		{
			"User": [
				{
					"fieldname": "portal_linked_customer",
					"label": "Portal linked Customer",
					"fieldtype": "Link",
					"options": "Customer",
					"insert_after": "last_name",
					"description": "If the user has role Portal Customer, they only see Projects with this Customer.",
				},
			]
		},
		update=True,
	)

	frappe.clear_cache(doctype="User")


def lift_project_attachment_limit():
	"""Remove Frappe's per-doctype max_attachments cap on Project.

	The portal manages folder structure and ZIP imports under each project; the default
	cap (e.g. 4 attachments per Project) makes uploading a real document set impossible.
	A Property Setter is the supported way to override doctype meta without forking the
	Project doctype JSON, and it survives `bench migrate`.
	"""
	if not frappe.db.exists("DocType", "Project"):
		return
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	make_property_setter(
		"Project",
		"max_attachments",
		"max_attachments",
		"0",
		"Int",
		for_doctype=True,
		validate_fields_for_doctype=False,
	)
	frappe.clear_cache(doctype="Project")


DEFAULT_PORTAL_FILE_TYPES = [
	{"type_name": "AutoCAD", "extensions": ".dwg,.dxf"},
	{"type_name": "PDF Document", "extensions": ".pdf"},
	{"type_name": "GAD File", "extensions": ".gad"},
	{"type_name": "Document", "extensions": ".doc,.docx,.odt,.rtf,.txt"},
	{"type_name": "Spreadsheet", "extensions": ".xls,.xlsx,.csv,.ods"},
	{"type_name": "Presentation", "extensions": ".ppt,.pptx,.odp"},
	{"type_name": "Image", "extensions": ".jpg,.jpeg,.png,.gif,.webp,.bmp,.tiff"},
	{"type_name": "3D Model", "extensions": ".skp,.obj,.stl,.fbx,.3ds,.blend"},
	{"type_name": "Archive", "extensions": ".zip,.rar,.7z,.tar,.gz"},
	{"type_name": "Other", "extensions": ""},
]


def ensure_portal_file_type_field():
	"""Add `portal_file_type` link field on File so uploads can be tagged by type."""
	if not frappe.db.exists("DocType", "File"):
		return
	create_custom_fields(
		{
			"File": [
				{
					"fieldname": "portal_file_type",
					"label": "Portal File Type",
					"fieldtype": "Link",
					"options": "Portal File Type",
					"insert_after": "folder",
					"description": "File type tag set by the portal upload UI (AutoCAD, PDF, GAD, etc.).",
				},
			]
		},
		update=True,
	)
	frappe.clear_cache(doctype="File")


def seed_default_portal_file_types():
	"""Seed the default file-type list. Idempotent — only inserts missing rows; never edits user-modified entries."""
	if not frappe.db.exists("DocType", "Portal File Type"):
		return
	for entry in DEFAULT_PORTAL_FILE_TYPES:
		if frappe.db.exists("Portal File Type", entry["type_name"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Portal File Type",
				"type_name": entry["type_name"],
				"extensions": entry.get("extensions", ""),
			}
		)
		doc.insert(ignore_permissions=True)


def after_install():
	ensure_department_portal_custom_fields()
	ensure_project_portal_custom_fields()
	ensure_portal_customer_access()
	lift_project_attachment_limit()
	ensure_portal_file_type_field()
	seed_default_portal_file_types()


def after_migrate():
	"""Re-apply custom fields so new installs / restores get User.portal_linked_customer."""
	ensure_department_portal_custom_fields()
	ensure_project_portal_custom_fields()
	ensure_portal_customer_access()
	lift_project_attachment_limit()
	ensure_portal_file_type_field()
	seed_default_portal_file_types()
