import frappe

from portal_app.install import ensure_project_portal_custom_fields


def execute():
	ensure_project_portal_custom_fields()
	frappe.db.commit()
