import frappe
from frappe import _
from frappe.model.document import Document


class PortalUserCustomer(Document):
	"""One (login, customer) access grant. These rows are the ONLY thing that lets a
	Portal Customer see a customer's projects; User.portal_linked_customer just mirrors
	the first one for display."""

	def validate(self):
		if frappe.db.exists(
			"Portal User Customer",
			{"user": self.user, "customer": self.customer, "name": ["!=", self.name]},
		):
			frappe.throw(self.user + " " + _("already has access to") + " " + self.customer + ".")

	def after_insert(self):
		if frappe.get_meta("User").has_field("portal_linked_customer") and not frappe.db.get_value(
			"User", self.user, "portal_linked_customer"
		):
			frappe.db.set_value("User", self.user, "portal_linked_customer", self.customer, update_modified=False)
		frappe.get_doc("User", self.user).add_comment(
			"Info", _("Customer portal access granted:") + " " + self.customer
		)

	def on_trash(self):
		self._repoint_primary()
		self._revoke_shares()
		if frappe.db.exists("User", self.user):
			frappe.get_doc("User", self.user).add_comment(
				"Info", _("Customer portal access removed:") + " " + self.customer
			)

	def _repoint_primary(self):
		if not frappe.get_meta("User").has_field("portal_linked_customer"):
			return
		if frappe.db.get_value("User", self.user, "portal_linked_customer") != self.customer:
			return
		remaining = frappe.get_all(
			"Portal User Customer",
			filters={"user": self.user, "name": ["!=", self.name]},
			pluck="customer",
			order_by="creation asc",
			limit=1,
		)
		frappe.db.set_value(
			"User", self.user, "portal_linked_customer", remaining[0] if remaining else None, update_modified=False
		)

	def _revoke_shares(self):
		"""Folder/file shares made to this login on the customer's projects would
		otherwise keep working (File DocShares are honoured before the Project check)."""
		from portal_app.api.files import revoke_user_shares_on_projects

		projects = frappe.get_all("Project", filters={"customer": self.customer}, pluck="name")
		if projects:
			revoke_user_shares_on_projects(self.user, projects)
