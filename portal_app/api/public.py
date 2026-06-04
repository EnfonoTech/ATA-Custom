import frappe


@frappe.whitelist(allow_guest=True)
def get_branding():
	"""Return branding fields from Portal Project Settings without requiring a session.

	Called by the login page before the user authenticates.
	Only non-sensitive display fields are exposed (logo URL, name, tagline, dimensions).
	"""
	if not frappe.db.exists("DocType", "Portal Project Settings"):
		return {}
	try:
		doc = frappe.get_single("Portal Project Settings")
		return {
			"company_logo": doc.get("company_logo") or "",
			"company_name": doc.get("company_name") or "",
			"company_tagline": doc.get("company_tagline") or "",
			"logo_width": int(doc.get("logo_width") or 0),
			"logo_height": int(doc.get("logo_height") or 0),
		}
	except Exception:
		return {}
