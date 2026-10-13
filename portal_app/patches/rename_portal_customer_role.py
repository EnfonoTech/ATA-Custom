import frappe

OLD = "Portal Customer"
NEW = "Client Customer"


def execute():
	"""Rename the client role "Portal Customer" to "Client Customer".

	A rename, not a new role: Frappe updates every login's Has Role row and every
	permission row that points at it, so no client contact loses access. If a "Client
	Customer" role already exists (created by hand), the old one is merged into it.
	Runs before the schema sync, so nothing creates a second, empty "Client Customer"."""
	if not frappe.db.exists("Role", OLD):
		return
	frappe.rename_doc(
		"Role", OLD, NEW, force=True, merge=bool(frappe.db.exists("Role", NEW)), show_alert=False, rebuild_search=False
	)
	frappe.clear_cache()
