import frappe

from portal_app import install
from portal_app.api import helper


def execute():
	"""Mark every existing portal team as portal_unit "Team" (Batch C).

	A team used to be "a Department with a Portal Office". Departments now sit above the
	teams, so the type is stored explicitly. Only rows with an office and a blank
	portal_unit are touched; nothing is reparented here (that is site-specific, see
	scripts/apply_ata_role_hierarchy.py). Idempotent."""
	if not frappe.db.exists("DocType", "Department"):
		return
	# Patches run before after_migrate, which is what normally creates these.
	install.ensure_department_portal_custom_fields()
	helper.ensure_portal_roles()
	if not frappe.get_meta("Department").has_field("portal_unit"):
		return
	d = frappe.qb.DocType("Department")
	names = (
		frappe.qb.from_(d)
		.select(d.name)
		.where(
			(d.portal_office.isnotnull())
			& (d.portal_office != "")
			& (d.portal_unit.isnull() | (d.portal_unit == ""))
		)
		.run(pluck=True)
	)
	for name in names:
		frappe.db.set_value("Department", name, "portal_unit", "Team", update_modified=False)
