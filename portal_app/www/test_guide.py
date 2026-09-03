"""Controller for the hosted UAT tester guide at /test-guide.

NAMING — this is the bug that made the first version of this page fail open:
Frappe finds a www controller by taking the template basename and replacing
hyphens with underscores (frappe/website/page_renderers/template_page.py,
set_pymodule: `template_basepath.replace("-", "_") + ".py"`). So the template is
`test-guide.html` but this file MUST be `test_guide.py`. Named `test-guide.py`
it is silently never imported — get_context never runs, and any permission check
in it never executes while the page still serves happily at HTTP 200.

`no_cache` is module-level because that is where the website router reads it
(WEBPAGE_PY_MODULE_PROPERTIES). It keeps the credential table off the page cache.

The credentials themselves are NOT in this repository — EnfonoTech/ATA-Custom is
public, so committing them would publish them. They live in the site's
site_config.json under `ata_uat_accounts` and are injected here at render time.
To retire them, remove that key:

    bench --site <site> set-config ata_uat_accounts "[]"
    bench --site <site> clear-website-cache

The page is deliberately open on this pre-handover test site so testers can pick
up logins without an account. Before this site holds any real client data, delete
the UAT accounts and clear the config key — the page then shows a notice instead.
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	# Restricted again now that the site holds real client data. This page carries
	# UAT logins and internal test procedure; it was deliberately left open only
	# while ata was a throwaway test site. frappe.only_for raises PermissionError,
	# which Frappe renders as its standard 403 "Not Permitted" page with a login
	# link — verify with a logged-out request, never by reading this code, because
	# a controller Frappe fails to import performs no check at all (see the module
	# docstring on the hyphen/underscore trap that caused exactly that).
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
