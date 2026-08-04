import frappe


def run():
	# 1. Custom Field
	if not frappe.db.exists("Custom Field", "Department-portal_office"):
		cf = frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Department",
				"label": "Portal Office",
				"fieldname": "portal_office",
				"fieldtype": "Select",
				"options": "RIYADH\nLISBON\nMANILA",
				"insert_after": "department_name",
				"in_list_view": 1,
			}
		)
		cf.insert(ignore_permissions=True)
		print("Custom field created")
	else:
		print("Custom field already exists")

	frappe.db.commit()

	# 2. Set office on departments
	# Map department_name → office (Frappe appends company abbr to `name`)
	DEPT_OFFICE = {
		"ATA RIYADH HQ": "RIYADH",
		"ATA RIYADH SUPERVISION TEAM": "RIYADH",
		"LISBON OFFICE 1": "LISBON",
		"LISBON OFFICE 2 - ID TEAM": "LISBON",
		"LISBON OFFICE 2 - CD TEAM": "LISBON",
		"MANILA OFFICE 01": "MANILA",
		"MANILA OFFICE 02": "MANILA",
	}

	all_depts = frappe.get_all("Department", fields=["name", "department_name"])
	for dept in all_depts:
		office = DEPT_OFFICE.get(dept.department_name)
		if office:
			frappe.db.set_value("Department", dept.name, "portal_office", office)
			print(f"  {dept.department_name} → {office}")

	frappe.db.commit()
	print("Done.")
