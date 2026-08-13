import frappe
from frappe import _
from frappe.utils import cint, cstr

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
def change_my_password(current_password=None, new_password=None, logout_other_sessions=1):
	"""Let a signed-in portal user change their OWN password.

	Deliberately not reusing frappe.core.doctype.user.user.update_password: that
	endpoint is allow_guest (it also serves the forgot-password key flow) and it
	calls login_manager.login_as() plus writes frappe.local.response for a redirect,
	which is wrong for an XHR from the SPA.

	Only ever acts on frappe.session.user — there is no user argument to tamper
	with, so this cannot be pointed at somebody else's account.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	from frappe.utils.password import check_password, update_password

	user = frappe.session.user
	current_password = cstr(current_password)
	new_password = cstr(new_password)

	if not current_password or not new_password:
		frappe.throw(_("Enter your current password and the new one."))

	# check_password raises AuthenticationError on a mismatch. Catch and re-throw so
	# the SPA gets a readable sentence instead of a bare framework error.
	try:
		check_password(user, current_password)
	except frappe.AuthenticationError:
		frappe.throw(_("Your current password is not correct."), frappe.AuthenticationError)

	if new_password == current_password:
		frappe.throw(_("Your new password must be different from your current one."))
	if len(new_password) < 8:
		frappe.throw(_("Your new password must be at least 8 characters long."))

	# Honour the site's own policy rather than inventing a second, weaker one —
	# same gate and same feedback handler core uses in User.validate().
	if frappe.get_system_settings("enable_password_policy"):
		from frappe.core.doctype.user.user import handle_password_test_fail
		from frappe.utils.password_strength import test_password_strength

		u = frappe.get_cached_doc("User", user)
		user_data = (u.first_name, u.middle_name, u.last_name, u.email, u.birth_date)
		result = test_password_strength(new_password, user_inputs=user_data) or {}
		feedback = result.get("feedback") or {}
		if not feedback.get("password_policy_validation_passed", False):
			handle_password_test_fail(feedback)

	update_password(user, new_password, logout_all_sessions=cint(logout_other_sessions))
	frappe.db.commit()
	return {"ok": True, "logged_out_other_sessions": bool(cint(logout_other_sessions))}


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
