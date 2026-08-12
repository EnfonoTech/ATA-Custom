"""Controller for /user-guide.

This page used to be public — it was written before the site held anything real,
and a generic how-to needs no login. That changed when ATA's live 2026 register and
66 staff accounts landed, and again when the guide gained screenshots of the running
system: those show real project names and real staff names.

So it now requires a login, like /handbook. Any portal user may read it.

NAMING — the controller for `user-guide.html` MUST be `user_guide.py` with an
underscore. Frappe resolves it as `template_basepath.replace("-", "_") + ".py"`
(frappe/website/page_renderers/template_page.py, set_pymodule). Name it with a
hyphen and Frappe never imports it, the check below never runs, and the page keeps
serving to everyone at HTTP 200 — which is exactly what happened once already on
/test-guide. After deploying, verify with a logged-out request, not by reading code.
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/user-guide"
		raise frappe.Redirect

	context.no_cache = 1
	context.title = _("ATA Project Portal — User Guide")
	return context
