"""/user-guide now redirects to /handbook.

The two pages had grown into near-duplicates — same role table, same folder
explanation, same sharing rules — which meant every correction had to be made
twice and they would inevitably drift apart. The handbook won because it is the
client-facing one.

Kept as a redirect rather than deleted: the address is already in commit
messages, the desk workspace and probably a bookmark or two, and a 404 teaches
people the portal is unreliable.
"""

import frappe


def get_context(context):
	frappe.local.flags.redirect_location = "/handbook"
	raise frappe.Redirect
