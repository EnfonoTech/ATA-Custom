import frappe

from portal_app.install import ensure_portal_customer_access


def execute():
	ensure_portal_customer_access()
	frappe.db.commit()
