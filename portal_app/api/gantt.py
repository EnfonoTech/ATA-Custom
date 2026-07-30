from __future__ import annotations

import re

import frappe

from portal_app.api import helper


def _team_sort_key(dept):
    m = re.search(r"(\d+)", dept["department_name"])
    return int(m.group(1)) if m else 999


@frappe.whitelist()
def get_gantt_data(office=None, team=None):
    """Team-grouped project timeline data for the portal Gantt Chart page.

    Grouping uses Project.portal_team (Link -> Department), which already holds
    real data for this portal — no new field needed. Scoped to whatever projects
    the current user is allowed to see (same rule as the Projects page).
    """
    allowed = helper.get_allowed_project_names()
    if not allowed:
        return {"teams": [], "unassigned": []}

    filters = {"name": ["in", allowed]}
    if team:
        filters["portal_team"] = team

    fields = [
        "name",
        "project_name",
        "status",
        "percent_complete",
        "expected_start_date",
        "expected_end_date",
        "portal_team",
    ]
    meta = frappe.get_meta("Project")
    for f in ("portal_phase", "portal_upcoming_milestone", "portal_milestone_date"):
        if meta.has_field(f):
            fields.append(f)

    projects = frappe.get_all("Project", filters=filters, fields=fields)

    departments = frappe.get_all(
        "Department",
        filters={"parent_department": "All Departments", "portal_office": ["!=", ""]},
        fields=["name", "department_name", "portal_office"],
    )
    if office and office != "ALL":
        departments = [d for d in departments if d.portal_office == office]
    departments = sorted(departments, key=_team_sort_key)
    dept_names = {d.name for d in departments}

    by_team: dict[str, list] = {}
    unassigned = []
    for p in projects:
        t = p.get("portal_team")
        if t and t in dept_names:
            by_team.setdefault(t, []).append(p)
        elif not team:
            unassigned.append(p)

    teams_out = []
    for d in departments:
        team_projects = by_team.get(d.name, [])
        if not team_projects:
            continue
        teams_out.append(
            {
                "name": d.name,
                "department_name": d.department_name,
                "office": d.portal_office or "",
                "projects": team_projects,
            }
        )

    return {"teams": teams_out, "unassigned": unassigned if not team else []}
