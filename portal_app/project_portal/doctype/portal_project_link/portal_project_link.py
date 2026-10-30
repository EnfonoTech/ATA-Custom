import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

# open_url ends up in an <a href>: only http(s), no whitespace or control characters,
# so a stored "javascript:" / "data:" value can never become a clickable script.
_URL_SCHEME = re.compile(r"^https?://", re.I)
_URL_BAD_CHARS = re.compile(r"[\s\x00-\x1f\x7f]")
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
MAX_URL = 2000
MAX_PATH = 1000


class PortalProjectLink(Document):
	"""A project's T Server / Autodesk Server / ERP link (one per project and type).

	System-Manager-only in Desk and REST. The portal endpoints (api/links.py) check who
	may manage or open the link first and then write with ignore_permissions."""

	def validate(self):
		self._validate_unique()
		self._validate_open_url()
		self._validate_copy_path()
		self._validate_allowed_users()

	def _validate_unique(self):
		if frappe.db.exists(
			"Portal Project Link",
			{"project": self.project, "link_type": self.link_type, "name": ["!=", self.name or ""]},
		):
			frappe.throw(_("This project already has a {0} link.").format(_(self.link_type)))

	def _validate_open_url(self):
		# Spaces only: a newline or tab inside the value is refused, not silently dropped.
		url = cstr(self.open_url).strip(" ")
		if url:
			if len(url) > MAX_URL:
				frappe.throw(_("The link is too long (at most {0} characters).").format(MAX_URL))
			if not _URL_SCHEME.match(url) or _URL_BAD_CHARS.search(url):
				frappe.throw(_("The link must start with http:// or https://."))
		self.open_url = url or None

	def _validate_copy_path(self):
		path = cstr(self.copy_path).strip()
		if path:
			if len(path) > MAX_PATH:
				frappe.throw(_("The path is too long (at most {0} characters).").format(MAX_PATH))
			if _CONTROL_CHARS.search(path):
				frappe.throw(_("The path contains characters that are not allowed."))
		self.copy_path = path or None

	def _validate_allowed_users(self):
		from portal_app.api import helper

		seen = set()
		for row in list(self.get("allowed_users") or []):
			user = cstr(row.user).strip()
			if not user or user in seen:
				self.remove(row)
				continue
			if user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
				frappe.throw(_("{0} cannot be given access to a project link.").format(user))
			if not frappe.db.get_value("User", user, "enabled"):
				frappe.throw(_("{0} is disabled.").format(user))
			if helper.is_customer_only(user):
				frappe.throw(_("Client contacts cannot be given access to a project link: {0}").format(user))
			row.user = user
			seen.add(user)
		for idx, row in enumerate(self.get("allowed_users") or [], start=1):
			row.idx = idx


def on_doctype_update():
	# _validate_unique alone races: two concurrent save_project_link calls could both insert.
	frappe.db.add_unique("Portal Project Link", ["project", "link_type"])
