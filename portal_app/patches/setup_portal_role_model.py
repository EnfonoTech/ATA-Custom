import frappe

from portal_app import install
from portal_app.api import helper


def execute():
	"""Carry today's staff over to the five-role model.

	  * Create the Department Admin and Team Lead roles.
	  * Every Projects Manager who is not a Super Admin becomes a Department Admin of every
	    team: the same projects they could see and manage until now. A Super Admin can narrow
	    that from the Org Chart afterwards.
	  * Give anyone who already leads a team the Team Lead role.
	Idempotent: running it again changes nothing."""
	if not frappe.db.exists("DocType", "Department"):
		return
	# Patches run before after_migrate, which is what normally creates these.
	install.ensure_department_portal_custom_fields()
	helper.ensure_portal_customer_role()
	helper.ensure_portal_roles()

	teams = frappe.get_all(
		"Department",
		filters={"parent_department": "All Departments", "portal_office": ["!=", ""]},
		pluck="name",
	)

	def _holds(user, role):
		return bool(frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": role}))

	managers = []
	for user in set(
		frappe.get_all(
			"Has Role", filters={"parenttype": "User", "role": helper.LEGACY_PROJECTS_MANAGER_ROLE}, pluck="parent"
		)
	):
		if user in ("Administrator", "Guest") or not frappe.db.get_value("User", user, "enabled"):
			continue
		if _holds(user, helper.SUPER_ADMIN_ROLE):
			continue
		managers.append(user)

	for dept_name in teams:
		dept = frappe.get_doc("Department", dept_name)
		have = {r.user for r in (dept.get("portal_department_admins") or [])}
		missing = [u for u in managers if u not in have]
		if not missing:
			continue
		for user in missing:
			dept.append("portal_department_admins", {"user": user})
		dept.save(ignore_permissions=True)  # the Department hook adds their Department Admin role

	# A site with no teams yet: still keep those managers in the admin tier.
	for user in managers:
		if not _holds(user, helper.DEPT_ADMIN_ROLE):
			doc = frappe.get_doc("User", user)
			doc.append("roles", {"role": helper.DEPT_ADMIN_ROLE})
			doc.flags.ignore_permissions = True
			doc.save()

	if frappe.get_meta("Department").has_field("portal_team_lead"):
		for lead in set(frappe.get_all("Department", filters={"portal_team_lead": ["is", "set"]}, pluck="portal_team_lead")):
			helper.sync_portal_role_markers(lead)
