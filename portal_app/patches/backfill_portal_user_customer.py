import frappe


def execute():
	"""Copy each login's single User.portal_linked_customer into Portal User Customer."""
	if not frappe.db.has_column("User", "portal_linked_customer"):
		return
	for user, customer in frappe.get_all(
		"User", filters={"portal_linked_customer": ["is", "set"]}, fields=["name", "portal_linked_customer"], as_list=True
	):
		if frappe.db.exists("Customer", customer) and not frappe.db.exists(
			"Portal User Customer", {"user": user, "customer": customer}
		):
			frappe.get_doc({"doctype": "Portal User Customer", "user": user, "customer": customer}).insert(
				ignore_permissions=True
			)
