import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


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


def after_install():
	ensure_project_portal_custom_fields()
	ensure_portal_customer_access()
	lift_project_attachment_limit()


def after_migrate():
	"""Re-apply custom fields so new installs / restores get User.portal_linked_customer."""
	ensure_project_portal_custom_fields()
	ensure_portal_customer_access()
	lift_project_attachment_limit()
