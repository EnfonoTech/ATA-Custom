"""Controller for the hosted UAT test guide at /test-guide.

Unlike /user-guide, this page is NOT public. It carries the throwaway UAT account
credentials, so it is restricted to System Managers and never cached.

Two things matter here and both are easy to get wrong:

1. `no_cache` must be module-level. Frappe's website router reads it when deciding
   whether to cache the rendered page. Without it a copy rendered for a System
   Manager could be served from cache to somebody else — which would defeat the
   role check entirely.

2. The credentials are NOT in this repository. `EnfonoTech/ATA-Custom` is a public
   repo, so committing test passwords would publish them. They live in the site's
   `site_config.json` under `ata_uat_accounts` and are injected at render time.
   Populate it with the provisioning script, or by hand:

       bench --site <site> set-config -p ata_uat_accounts '[{...}]'

   If the key is absent the page still renders and simply tells the tester to ask
   an administrator for the logins.
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	# Throws PermissionError for anyone who is not a System Manager, including Guest.
	frappe.only_for("System Manager")

	context.no_cache = 1
	context.title = _("ATA Project Portal — Tester Guide")

	accounts = frappe.conf.get("ata_uat_accounts") or []
	# Defend against a malformed site_config entry rather than 500-ing the page.
	if not isinstance(accounts, list):
		accounts = []
	context.uat_accounts = [a for a in accounts if isinstance(a, dict) and a.get("email")]
	context.site_url = frappe.utils.get_url()

	return context
