import frappe


def run():
    # Get actual department name mapping: department_name → name
    all_depts = frappe.get_all("Department", fields=["name", "department_name"])
    dept_map = {d.department_name: d.name for d in all_depts}
    print("Department map:", dept_map)

    # Get all employees with broken department links
    employees = frappe.get_all(
        "Employee",
        fields=["name", "employee_name", "department"],
        limit=200,
    )

    fixed = 0
    for emp in employees:
        dept_label = emp.department  # this might be "ATA RIYADH HQ" (wrong)
        correct_name = dept_map.get(dept_label)
        if correct_name and correct_name != dept_label:
            frappe.db.set_value("Employee", emp.name, "department", correct_name)
            print(f"  Fixed: {emp.employee_name} → {correct_name}")
            fixed += 1

    frappe.db.commit()
    print(f"\nFixed {fixed} employees.")
