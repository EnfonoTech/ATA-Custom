import frappe
from frappe import _
from frappe.utils import cstr

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
			out["portal_linked_customer_name"] = (
				frappe.db.get_value("Customer", cust, "customer_name") or cust
			)
	return out


@frappe.whitelist()
def list_notifications(limit=20):
	"""Recent Frappe Notification Log rows for the current user.

	Frappe writes Notification Log entries on assignments / shares / mentions; this is
	the same source the desk bell uses. We return up to `limit` rows + an unread count.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	try:
		limit = max(1, min(100, int(limit)))
	except Exception:
		limit = 20
	try:
		rows = frappe.get_all(
			"Notification Log",
			filters={"for_user": frappe.session.user},
			fields=[
				"name",
				"subject",
				"document_type",
				"document_name",
				"read",
				"creation",
				"type",
			],
			order_by="creation desc",
			limit_page_length=limit,
			ignore_permissions=True,
		)
		unread = frappe.db.count(
			"Notification Log",
			{"for_user": frappe.session.user, "read": 0},
		)
	except Exception:
		# Notification Log isn't installed or query failed — return empty.
		return {"items": [], "unread": 0}
	return {"items": rows, "unread": unread}


@frappe.whitelist()
def mark_notifications_read(names=None):
	"""Mark a list of Notification Log rows as read (or all when names is None)."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	import json

	if isinstance(names, str):
		try:
			names = json.loads(names)
		except Exception:
			names = [n.strip() for n in names.split(",") if n.strip()]
	try:
		if names:
			frappe.db.sql(
				"UPDATE `tabNotification Log` SET `read`=1 WHERE for_user=%s AND name IN ({})".format(
					",".join(["%s"] * len(names))
				),
				[frappe.session.user, *names],
			)
		else:
			frappe.db.sql(
				"UPDATE `tabNotification Log` SET `read`=1 WHERE for_user=%s",
				frappe.session.user,
			)
	except Exception:
		# Previously this swallowed the failure and still returned ok:True, so the UI
		# cleared the badge while the rows stayed unread.
		frappe.log_error(frappe.get_traceback(), "Portal: mark notifications read")
		frappe.throw(_("Could not mark notifications as read. Please try again."))
	return {"ok": True}


@frappe.whitelist()
def update_my_profile(full_name=None, mobile_no=None, language=None, time_zone=None):
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("User", frappe.session.user)
	if full_name is not None:
		# User.full_name is derived by User.validate() from first/middle/last name, so
		# assigning it directly was silently discarded on save and the rename never took.
		parts = cstr(full_name).strip().split(None, 1)
		if parts:
			doc.first_name = parts[0]
			doc.last_name = parts[1] if len(parts) > 1 else ""
	if mobile_no is not None:
		doc.mobile_no = mobile_no
	if language is not None:
		doc.language = language
	if time_zone is not None:
		doc.time_zone = time_zone

	doc.save(ignore_permissions=True)
	return get_my_profile()
