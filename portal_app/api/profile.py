import frappe
from frappe import _

from portal_app.api import helper


@frappe.whitelist()
def get_my_profile():
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	u = frappe.get_doc("User", frappe.session.user)
	out = {
		"name": u.name,
		"full_name": u.full_name,
		"email": u.email,
		"mobile_no": u.mobile_no,
		"language": u.language,
		"user_image": u.user_image,
		"time_zone": u.time_zone,
		"roles": frappe.get_roles(),
		"portal_ok": helper.user_can_use_portal(),
		"is_customer_portal_user": helper.user_is_customer_portal_user(),
	}
	if frappe.get_meta("User").has_field("portal_linked_customer"):
		cust = u.get("portal_linked_customer")
		out["portal_linked_customer"] = cust
		if cust:
			out["portal_linked_customer_name"] = frappe.db.get_value("Customer", cust, "customer_name") or cust
	return out


@frappe.whitelist()
def update_my_profile(full_name=None, mobile_no=None, language=None, time_zone=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("User", frappe.session.user)
	if full_name is not None:
		doc.full_name = full_name
	if mobile_no is not None:
		doc.mobile_no = mobile_no
	if language is not None:
		doc.language = language
	if time_zone is not None:
		doc.time_zone = time_zone

	doc.save(ignore_permissions=True)
	return get_my_profile()
