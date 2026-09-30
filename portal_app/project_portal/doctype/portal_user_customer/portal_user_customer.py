import frappe
from frappe import _
from frappe.model.document import Document


class PortalUserCustomer(Document):
	def validate(self):
		if frappe.db.exists(
			"Portal User Customer",
			{"user": self.user, "customer": self.customer, "name": ["!=", self.name]},
		):
			frappe.throw(_("{0} already has access to {1}.").format(self.user, self.customer))
