import frappe
from frappe.desk.form.assign_to import add as assign_add


def run():
    """One-time backfill: for every active Employee with a linked User account,
    make sure their Employee.department is reflected as a Frappe "Assign To"
    (ToDo) on that Department doc — this is the data the Organization Chart
    and Teams page read to show team members."""

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active", "user_id": ["!=", ""], "department": ["!=", ""]},
        fields=["name", "employee_name", "department", "user_id"],
    )

    by_dept = {}
    for emp in employees:
        by_dept.setdefault(emp.department, []).append(emp)

    assigned = 0
    skipped_no_dept = 0
    skipped_already = 0

    for dept_name, dept_employees in by_dept.items():
        if not frappe.db.exists("Department", dept_name):
            skipped_no_dept += len(dept_employees)
            print(f"  Skipping — Department not found: {dept_name}")
            continue

        already_assigned = {
            r.allocated_to
            for r in frappe.get_all(
                "ToDo",
                filters={
                    "reference_type": "Department",
                    "reference_name": dept_name,
                    "status": ["not in", ("Cancelled", "Closed")],
                },
                fields=["allocated_to"],
            )
        }

        for emp in dept_employees:
            if emp.user_id in already_assigned:
                skipped_already += 1
                continue
            assign_add(
                {"doctype": "Department", "name": dept_name, "assign_to": [emp.user_id]},
                ignore_permissions=True,
            )
            already_assigned.add(emp.user_id)
            assigned += 1
            print(f"  Assigned {emp.employee_name} ({emp.user_id}) -> {dept_name}")

    frappe.db.commit()
    print(
        f"\nDone. Newly assigned: {assigned}, "
        f"already assigned: {skipped_already}, "
        f"skipped (department not found): {skipped_no_dept}"
    )
