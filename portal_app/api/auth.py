import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cstr

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
				"team or a project, or to give you a portal role (Super Admin, Department Admin, "
				"Team Lead, Team Member or Client Customer)."
			),
			frappe.PermissionError,
		)
	return {"valid": True}


@frappe.whitelist(methods=["GET"])
def get_csrf_token():
	"""The session's CSRF token for the SPA's POSTs.

	Frappe only enforces CSRF once the session holds a token (it gets one as soon as
	the user opens Desk), and frappe.sessions.get_csrf_token is not whitelisted, so the
	SPA had no way to learn it and every portal POST then failed with "Invalid Request".
	GET-only and login-only; the response is readable by same-origin script only.
	"""
	from frappe.sessions import get_csrf_token as _session_csrf_token

	return _session_csrf_token()


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def request_password_reset(email=None):
	"""The "Forgot password?" form on the portal sign-in screen.

	Guest-callable on purpose: the person asking cannot sign in. It always answers the
	same way, whether or not the address belongs to a portal login, so it cannot be used to
	find out who has an account, and it is rate limited per IP. The link mail is queued
	(never sent inside the request) and, for a client, lands the person back on the portal
	once they have chosen a password."""
	answer = {
		"ok": True,
		"message": _("If that address belongs to a portal login, a reset link is on its way."),
	}
	email = cstr(email).strip().lower()
	if not email or "@" not in email or len(email) > 140:
		return answer
	user = frappe.db.get_value("User", {"name": email, "enabled": 1}, "name") or frappe.db.get_value(
		"User", {"email": email, "enabled": 1}, "name"
	)
	if not user or user in ("Administrator", "Guest") or not helper.user_can_use_portal(user):
		return answer
	try:
		doc = frappe.get_doc("User", user)
		if helper.is_customer_only(user):
			doc.db_set("redirect_url", helper.PORTAL_HOME)
		link = doc.reset_password(send_email=False)
		doc.send_login_mail(
			_("Password Reset"),
			"password_reset",
			{"link": link},
			now=False,
			custom_template=frappe.db.get_system_setting("reset_password_template"),
		)
	except Exception:
		# Never tell a stranger what went wrong; the administrator sees it in the Error Log.
		frappe.log_error(frappe.get_traceback(), "Portal: forgot-password mail")
	return answer
