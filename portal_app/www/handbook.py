"""Controller for the client handover handbook at /handbook.

Unlike /user-guide, this page is NOT public. It is illustrated with screenshots of
the live site, which show ATA's real project names and real staff names — that is
client-confidential, so a login is required.

Any portal user may read it: it is the handover guide their own staff are meant to
use. It is not restricted to managers, because the people who most need it are the
ones with the least access.

NAMING — the controller for `handbook.html` must be `handbook.py`. Frappe finds it
via `template_basepath.replace("-", "_") + ".py"`, so a hyphenated page name needs an
underscored module (see www/test_guide.py, where getting that wrong meant the
permission check silently never ran while the page still served HTTP 200).

`no_cache` is module-level because that is where the website router reads it. It
matters here: the page greets the reader by name and adapts to their role, so a copy
rendered for one user must never be served to another from cache.
"""

import frappe
from frappe import _

from portal_app.api import helper

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		# Send them to log in and come back, rather than a bare 403.
		frappe.local.flags.redirect_location = "/login?redirect-to=/handbook"
		raise frappe.Redirect

	context.no_cache = 1
	context.title = _("ATA Project Portal — Handbook")

	roles = set(frappe.get_roles())
	context.user_full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	context.is_staff = helper.has_portal_staff_project_access()
	context.is_customer = helper.user_is_customer_portal_user()
	context.role_label = (
		_("System Manager") if "System Manager" in roles
		else _("Projects Manager") if "Projects Manager" in roles
		else _("Client contact") if context.is_customer
		else _("Projects User")
	)

	# Real figures, so the handbook never contradicts what the reader sees on screen.
	context.project_count = frappe.db.count("Project")
	context.my_project_count = len(helper.get_allowed_project_names())
	context.team_count = frappe.db.count("Department", {"portal_office": ["!=", ""]})

	return context
