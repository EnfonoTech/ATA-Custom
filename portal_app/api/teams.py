import re
import frappe


def _team_sort_key(dept):
    m = re.search(r"(\d+)", dept["department_name"])
    return int(m.group(1)) if m else 999


@frappe.whitelist()
def get_teams():
    departments = frappe.get_all(
        "Department",
        filters={"parent_department": "All Departments", "portal_office": ["!=", ""]},
        fields=["name", "department_name", "portal_office"],
    )
    departments = sorted(departments, key=_team_sort_key)

    result = []
    for dept in departments:
        members = frappe.get_all(
            "Employee",
            filters={"department": dept.name, "status": "Active"},
            fields=["name", "employee_name", "designation", "company_email"],
            order_by="employee_name asc",
        )
        if not members:
            continue

        project_count = 0
        active_project_count = 0
        if frappe.get_meta("Project").has_field("portal_team"):
            project_count = frappe.db.count("Project", {"portal_team": dept.name})
            active_project_count = frappe.db.count("Project", {"portal_team": dept.name, "status": "Open"})

        result.append({
            "name": dept.name,
            "department_name": dept.department_name,
            "office": dept.portal_office or "",
            "member_count": len(members),
            "members": members,
            "project_count": project_count,
            "active_project_count": active_project_count,
        })

    return result


@frappe.whitelist()
def get_team_summary():
    total = frappe.db.count("Employee", {"status": "Active"})

    departments = frappe.get_all(
        "Department",
        filters={"parent_department": "All Departments", "portal_office": ["!=", ""]},
        fields=["name", "department_name", "portal_office"],
    )
    departments = sorted(departments, key=_team_sort_key)

    dept_counts = []
    for dept in departments:
        count = frappe.db.count("Employee", {"department": dept.name, "status": "Active"})
        if count > 0:
            dept_counts.append({
                "name": dept.name,
                "label": dept.department_name,
                "office": dept.portal_office or "",
                "count": count,
            })

    return {"total": total, "departments": dept_counts}


@frappe.whitelist()
def get_offices():
    rows = frappe.get_all(
        "Department",
        filters={"portal_office": ["!=", ""]},
        fields=["portal_office"],
        distinct=True,
    )
    return sorted({r.portal_office for r in rows if r.portal_office})
