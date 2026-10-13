"""Controller for the public handbook at /handbook.

PUBLIC on purpose. It is the guide ATA hands to its own staff, and requiring a
login to read the instructions for logging in is a circle. It replaced the old
/user-guide, which said much the same thing.

Because it is public it must contain NO credentials and NO client data. Most
figures are drawn illustrations with generic example names. The newest ones are
screenshots of a DEMO copy of the portal (made-up people and projects, nothing
from the live register) and say so in their caption. A screenshot of the live
site must never be added: that would put this page behind a login.

Counts come from the database rather than being written into the page, so the
guide cannot drift out of date — but they are deliberately coarse (how many
projects exist, how many teams), never names.
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.title = _("ATA Project Portal — Handbook")

	# Coarse, non-identifying figures only — this page is world-readable.
	context.project_count = frappe.db.count("Project")
	context.register_2026 = (
		frappe.db.count("Project", {"portal_project_code": ["like", "26%"]})
		+ frappe.db.count("Project", {"portal_project_code": ["like", "CB-%"]})
	)
	context.historical_count = frappe.db.count("Project", {"portal_project_code": ["like", "ATA-%"]})
	context.team_count = frappe.db.count("Department", {"portal_office": ["!=", ""]})
	return context
