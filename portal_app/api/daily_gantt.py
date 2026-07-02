from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime

from portal_app.api import helper

FLAG_FIELD = "is_portal_daily_gantt"
PROJECT_FIELD = "portal_project"


def _ensure_fields():
    """Lazily add the two small custom fields Daily Gantt needs on the standard
    Event doctype, instead of shipping a whole new DocType for what's really
    just a title + time + color + optional project reminder."""
    meta = frappe.get_meta("Event")
    if not meta.has_field(FLAG_FIELD):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Event",
                "fieldname": FLAG_FIELD,
                "label": "Is Portal Daily Gantt",
                "fieldtype": "Check",
                "default": "0",
                "insert_after": "subject",
                "hidden": 1,
            }
        ).insert(ignore_permissions=True)
    if not meta.has_field(PROJECT_FIELD):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Event",
                "fieldname": PROJECT_FIELD,
                "label": "Portal Project",
                "fieldtype": "Link",
                "options": "Project",
                "insert_after": FLAG_FIELD,
            }
        ).insert(ignore_permissions=True)
    frappe.clear_cache(doctype="Event")


def _require_portal_user():
    if not helper.user_can_use_portal():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def _get_milestone(name):
    doc = frappe.get_doc("Event", name)
    if not doc.get(FLAG_FIELD):
        frappe.throw(_("Not a Daily Gantt milestone"))
    return doc


@frappe.whitelist()
def get_milestones(start_date, end_date):
    """Milestones within a date range (inclusive), for the 4-week Daily Gantt board."""
    _require_portal_user()
    _ensure_fields()
    rows = frappe.get_all(
        "Event",
        filters={
            FLAG_FIELD: 1,
            "starts_on": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
        },
        fields=["name", "subject", "starts_on", "color", "status", f"{PROJECT_FIELD} as project"],
        order_by="starts_on asc",
    )
    for r in rows:
        r["completed"] = r.pop("status") == "Completed"
    return rows


@frappe.whitelist()
def create_milestone(title, date, time, project=None, color=None):
    _require_portal_user()
    if not (title or "").strip():
        frappe.throw(_("Title is required"))
    if not date or not time:
        frappe.throw(_("Date and time are required"))
    _ensure_fields()

    doc = frappe.get_doc(
        {
            "doctype": "Event",
            "subject": title.strip(),
            "starts_on": f"{date} {time}:00",
            "color": color or "#185FA5",
            "status": "Open",
            "event_type": "Public",
            FLAG_FIELD: 1,
        }
    )
    if project:
        doc.set(PROJECT_FIELD, project)
    doc.insert(ignore_permissions=True)
    return {"name": doc.name}


@frappe.whitelist()
def update_milestone(name, title=None, date=None, time=None, color=None):
    _require_portal_user()
    doc = _get_milestone(name)

    if title is not None and title.strip():
        doc.subject = title.strip()
    if date or time:
        cur = get_datetime(doc.starts_on)
        new_date = date or cur.strftime("%Y-%m-%d")
        new_time = time or cur.strftime("%H:%M")
        doc.starts_on = f"{new_date} {new_time}:00"
    if color:
        doc.color = color
    doc.save(ignore_permissions=True)
    return {"name": doc.name}


@frappe.whitelist()
def toggle_milestone(name):
    _require_portal_user()
    doc = _get_milestone(name)
    doc.status = "Open" if doc.status == "Completed" else "Completed"
    doc.save(ignore_permissions=True)
    return {"name": doc.name, "completed": doc.status == "Completed"}


@frappe.whitelist()
def delete_milestone(name):
    _require_portal_user()
    doc = _get_milestone(name)
    doc.delete(ignore_permissions=True)
    return {"ok": True}
