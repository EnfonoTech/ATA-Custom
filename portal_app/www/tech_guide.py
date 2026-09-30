"""Controller for the technical guide at /tech-guide.

NOT public, unlike /handbook. It describes how access control, sharing and the
ERPNext integration work inside — useful to whoever maintains the site, and a map
for anyone probing it. So it needs a login and the System Manager role.

The template is `tech-guide.html`; this file must be `tech_guide.py` (Frappe swaps
hyphens for underscores when it looks for a www controller — see test_guide.py).
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/tech-guide"
		raise frappe.Redirect
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("The technical guide is for System Managers."), frappe.PermissionError)
	context.no_cache = 1
	context.title = _("ATA Project Portal — Technical Guide")
	return context
