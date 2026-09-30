"""Remove Project DocShares held by client contacts (Portal Customer, not staff).

Folder/file shares and team sync used to add a read DocShare on the parent Project
for every recipient. For a client contact that opened the whole Project record
(every Currency field) through /api/resource/Project, and the portal's
has_permission hook cannot deny past a share. Access to shared files does not need
it: File DocShares and the portal endpoints cover that. Safe to re-run.
"""

import frappe

from portal_app.api import helper


def execute():
	holders = set(
		frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": helper.PORTAL_CUSTOMER_ROLE},
			pluck="parent",
		)
	)
	for user in holders:
		if not helper.is_customer_only(user):
			continue
		for name in frappe.get_all("DocShare", filters={"user": user, "share_doctype": "Project"}, pluck="name"):
			frappe.delete_doc("DocShare", name, ignore_permissions=True, flags={"ignore_share_permission": True})
