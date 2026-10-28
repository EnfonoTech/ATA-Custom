import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Lower

from portal_app.api import files

TYPE_NAME_MAX = 60


class PortalSubmissionType(Document):
	"""A kind of submission ATA sends to a client (Concept Submittal, ...). Its name goes
	into the submission folder name, so it must be a safe single path segment."""

	def before_naming(self):
		# autoname is field:type_name, and naming runs before validate: clean first so
		# the record name and type_name agree.
		self._clean_type_name()

	def validate(self):
		self._clean_type_name()
		# Compared in Python: the database collation would also call "concept submittal"
		# equal to this new row's own name and hide the clash.
		t = frappe.qb.DocType("Portal Submission Type")
		clashes = (
			frappe.qb.from_(t).select(t.name).where(Lower(t.type_name) == self.type_name.lower()).run(pluck=True)
		)
		if any(self.is_new() or c != self.name for c in clashes):
			frappe.throw(_("A submission type with this name already exists."))

	def _clean_type_name(self):
		raw = self.type_name or ""
		# Rejected, not stripped: a stored type is always safe to embed in a name.
		if files.SUBMISSION_NAME_ILLEGAL.search(raw):
			frappe.throw(_('A submission type name cannot contain / \\ : * ? " < > |'))
		self.type_name = files._clean_name_part(raw)
		if not self.type_name:
			frappe.throw(_("Enter a submission type name."))
		if len(self.type_name) > TYPE_NAME_MAX:
			frappe.throw(_("A submission type name can be at most {0} characters.").format(TYPE_NAME_MAX))
