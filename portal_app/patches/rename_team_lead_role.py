import frappe

OLD = "Team Lead"
NEW = "Team Manager"


def execute():
	"""Rename the marker role "Team Lead" to "Team Manager" (Batch C labels).

	A rename, not a new role: Frappe updates every login's Has Role row and every
	permission row that points at it, so no Team Manager loses the role. If a "Team
	Manager" role already exists, the old one is merged into it. Runs before the schema
	sync, so nothing creates a second, empty "Team Manager" first."""
	if not frappe.db.exists("Role", OLD):
		return
	frappe.rename_doc(
		"Role", OLD, NEW, force=True, merge=bool(frappe.db.exists("Role", NEW)), show_alert=False, rebuild_search=False
	)
	frappe.clear_cache()
