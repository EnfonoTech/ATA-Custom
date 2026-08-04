from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime

from portal_app.api import helper

FLAG_FIELD = "is_portal_daily_task"
ASSIGNED_FIELD = "portal_assigned_to"


def _ensure_fields():
	"""Verify the Event custom fields exist — never create them here.

	Creating Custom Fields from a whitelisted endpoint means any portal user can
	trigger DDL on a core doctype by loading a page, and two concurrent first-hits
	race each other. install.ensure_daily_task_custom_fields() owns them now and
	runs on install and on every migrate.
	"""
	meta = frappe.get_meta("Event")
	if meta.has_field(FLAG_FIELD) and meta.has_field(ASSIGNED_FIELD):
		return
	frappe.throw(_("Daily Task is not set up on this site yet. Run `bench migrate` and try again."))


def _require_portal_user():
	if not helper.user_can_use_portal():
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _get_task(name):
	doc = frappe.get_doc("Event", name)
	if not doc.get(FLAG_FIELD):
		frappe.throw(_("Not a Daily Task"))
	user = frappe.session.user
	if doc.get(ASSIGNED_FIELD) != user and doc.owner != user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return doc


@frappe.whitelist()
def get_tasks(start_date, end_date):
	"""The current user's own tasks within a date range (inclusive) — a
	personal, per-user reminder list for the 4-week Daily Task board."""
	_require_portal_user()
	_ensure_fields()
	rows = frappe.get_all(
		"Event",
		filters={
			FLAG_FIELD: 1,
			ASSIGNED_FIELD: frappe.session.user,
			"starts_on": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
		},
		fields=["name", "subject", "starts_on", "color", "status"],
		order_by="starts_on asc",
	)
	for r in rows:
		r["completed"] = r.pop("status") == "Completed"
	return rows


@frappe.whitelist()
def create_task(title, date, time, assigned_to=None, color=None):
	_require_portal_user()
	if not (title or "").strip():
		frappe.throw(_("Title is required"))
	if not date or not time:
		frappe.throw(_("Date and time are required"))
	_ensure_fields()

	target_user = frappe.session.user
	if assigned_to and assigned_to != frappe.session.user:
		if not helper.has_portal_staff_project_access():
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		target_user = assigned_to

	doc = frappe.get_doc(
		{
			"doctype": "Event",
			"subject": title.strip(),
			"starts_on": f"{date} {time}:00",
			"color": color or "#185FA5",
			"status": "Open",
			"event_type": "Private",
			FLAG_FIELD: 1,
			ASSIGNED_FIELD: target_user,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def update_task(name, title=None, date=None, time=None, color=None):
	_require_portal_user()
	doc = _get_task(name)

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
def toggle_task(name):
	_require_portal_user()
	doc = _get_task(name)
	doc.status = "Open" if doc.status == "Completed" else "Completed"
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "completed": doc.status == "Completed"}


@frappe.whitelist()
def delete_task(name):
	_require_portal_user()
	doc = _get_task(name)
	doc.delete(ignore_permissions=True)
	return {"ok": True}
