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
	out["portal_linked_customers"] = [
		{"name": c, "customer_name": frappe.db.get_value("Customer", c, "customer_name") or c}
		for c in helper.get_portal_linked_customers(frappe.session.user)
	]
	# The portal role (the highest one: Super Admin, Department Admin, Department
	# Coordinator, Team Manager, Project Lead, Project Architect or Client Customer), every
	# designation the login holds, and the teams they apply to, for the Profile page.
	role = helper.get_portal_role(frappe.session.user)
	out["portal_role"] = role
	out["portal_role_label"] = helper.ROLE_LABELS.get(role, "")

	def _team_names(names):
		return [frappe.db.get_value("Department", n, "department_name") or n for n in names]

	out["admin_team_names"] = _team_names(helper.admin_department_names()) if helper.is_dept_admin() else []
	out["led_team_names"] = _team_names(helper.led_department_names()) if helper.is_team_lead() else []
	out["designations"] = helper.get_portal_designations(frappe.session.user)
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

		# Compare the score here rather than reading a
		# feedback["password_policy_validation_passed"] flag: the util in
		# frappe.utils.password_strength only ever fills feedback with
		# {warning, suggestions}. That flag is added by the *wrapper* in
		# frappe.core.doctype.user.user.test_password_strength, so reading it off
		# the util's result always came back None and rejected every password.
		# This is the same comparison that wrapper makes.
		score = cint(result.get("score"))
		minimum = cint(frappe.get_system_settings("minimum_password_score")) or 0
		if not (score and score >= minimum):
			handle_password_test_fail(result.get("feedback") or {})

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


def _should_follow_browser_time_zone(current: str | None, browser_tz: str, system_tz: str) -> bool:
	"""Whether the user's saved Time Zone should be replaced by the browser's.

	current     the User's time_zone now (None/"" when never set)
	browser_tz  what the browser reports; already checked to be a known zone
	system_tz   System Settings time zone (Asia/Riyadh on ATA)
	"""
	# Empty, or still the system default, means nobody chose it: follow the browser.
	# Any other value was picked on Profile and is kept.
	return not current or current == system_tz


@frappe.whitelist(methods=["POST"])
def sync_browser_time_zone(time_zone=None):
	"""Called once per browser tab by the portal layout with the browser's IANA zone.

	ATA works from Riyadh, Cairo, Lisbon and Manila, and Frappe shows every date-time in
	the user's Time Zone (or the system one when that is empty). The rule for when the
	browser overrides a saved value is _should_follow_browser_time_zone. POST, because a
	GET request is rolled back."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	from frappe.utils import get_system_timezone
	from frappe.utils.momentjs import get_all_timezones

	tz = cstr(time_zone).strip()
	if tz not in get_all_timezones():
		return {"changed": False, "time_zone": None}

	current = frappe.db.get_value("User", frappe.session.user, "time_zone")
	if current == tz or not _should_follow_browser_time_zone(current, tz, get_system_timezone()):
		return {"changed": False, "time_zone": current}

	doc = frappe.get_doc("User", frappe.session.user)
	doc.time_zone = tz
	doc.save(ignore_permissions=True)
	return {"changed": True, "time_zone": tz}
