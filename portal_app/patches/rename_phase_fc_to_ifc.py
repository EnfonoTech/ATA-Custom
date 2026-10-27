import frappe


def execute():
	"""Phase "FC" is now "IFC" (Issued for Construction).

	A Select field refuses a stored value that is no longer in its options, so any
	project still holding "FC" could not be saved again. Direct update: no document
	logic is needed and `modified` stays as it was. Safe to run twice.
	"""
	if not frappe.db.has_column("Project", "portal_phase"):
		return
	frappe.db.sql(
		"UPDATE `tabProject` SET portal_phase = %s WHERE portal_phase = %s",
		("IFC", "FC"),
	)
	frappe.db.commit()
