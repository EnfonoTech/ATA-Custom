import frappe
from frappe import _

from portal_app.api import helper


@frappe.whitelist(allow_guest=True)
def get_logged_user():
	if frappe.session.user == "Guest":
		return {
			"user": None,
			"roles": [],
			"profile_image": None,
			"portal_ok": False,
		}

	full_name, profile_image = frappe.db.get_value(
		"User",
		frappe.session.user,
		["full_name", "user_image"],
	)
	return {
		"user": frappe.session.user,
		"full_name": full_name,
		"roles": frappe.get_roles(frappe.session.user),
		"profile_image": profile_image,
		"portal_ok": helper.user_can_use_portal(),
	}


@frappe.whitelist(allow_guest=True)
def check_portal_access():
	user = frappe.session.user
	if user == "Guest":
		return {"valid": False, "guest": True}
	if not helper.user_can_use_portal(user):
		frappe.local.login_manager.logout()
		frappe.throw(
			_(
				"You do not have access to the project portal. Ask an administrator to add you to a "
				"project team, assign Projects User / Projects Manager (or System Manager), or give you "
				"the Portal Customer role."
			),
			frappe.PermissionError,
		)
	return {"valid": True}
