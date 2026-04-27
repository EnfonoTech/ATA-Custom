"""
Showcase / demo data for Project Portal client demos.

Safe to run multiple times: skips records that already exist (by email or portal project code).

Run from bench (recommended):
    bench --site <yoursite> execute portal_app.demo_seed.seed_showcase

Or from the portal Admin page (System Manager + Portal Project Settings flag).
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_days, today
from frappe.utils.file_manager import save_file
from frappe.utils.password import update_password

from erpnext import get_default_company

DEMO_PASSWORD = "ChangeMe-Demo#1"

DEMO_USERS: list[dict] = [
	{
		"email": "portal.manager@demo.local",
		"first_name": "Demo",
		"last_name": "Manager",
		"roles": ["Projects Manager", "Projects User"],
	},
	{
		"email": "portal.pm@demo.local",
		"first_name": "River",
		"last_name": "PM",
		"roles": ["Projects User"],
	},
	{
		"email": "portal.member1@demo.local",
		"first_name": "Alex",
		"last_name": "Chen",
		"roles": ["Projects User"],
	},
	{
		"email": "portal.member2@demo.local",
		"first_name": "Sam",
		"last_name": "Jordan",
		"roles": ["Projects User"],
	},
]

DEMO_PROJECTS: list[dict] = [
	{
		"project_name": "Demo — HQ Campus Upgrade",
		"code": "DEMO-HQ",
		"stage": "Active",
		"manager": "portal.pm@demo.local",
		"team": ["portal.pm@demo.local", "portal.manager@demo.local", "portal.member1@demo.local"],
		"cost": 420000,
		"tasks": [
			("Structural assessment", "Open"),
			("MEP coordination", "Open"),
			("Client sign-off — phase 1", "Completed"),
		],
		"attach_readme": True,
	},
	{
		"project_name": "Demo — Retail Fit-Out (North)",
		"code": "DEMO-RTL",
		"stage": "Review",
		"manager": "portal.manager@demo.local",
		"team": ["portal.manager@demo.local", "portal.member2@demo.local"],
		"cost": 185000,
		"tasks": [
			("Fixture procurement", "Open"),
			("Lighting mock-up", "Open"),
		],
		"attach_readme": False,
	},
	{
		"project_name": "Demo — Warehouse Automation",
		"code": "DEMO-WH",
		"stage": "Planning",
		"manager": "portal.pm@demo.local",
		"team": ["portal.pm@demo.local", "portal.member1@demo.local", "portal.member2@demo.local"],
		"cost": 950000,
		"tasks": [
			("Vendor RFP", "Open"),
			("Network rack layout", "Open"),
			("Safety review", "Open"),
		],
		"attach_readme": False,
	},
	{
		"project_name": "Demo — Solar Field Phase 2",
		"code": "DEMO-SOL",
		"stage": "On Hold",
		"manager": "portal.manager@demo.local",
		"team": ["portal.manager@demo.local", "portal.pm@demo.local"],
		"cost": 1200000,
		"tasks": [
			("Permit resubmission", "Open"),
		],
		"attach_readme": False,
	},
	{
		"project_name": "Demo — Mobile App Rollout",
		"code": "DEMO-APP",
		"stage": "Done",
		"manager": "portal.pm@demo.local",
		"team": ["portal.pm@demo.local", "portal.member1@demo.local"],
		"cost": 78000,
		"tasks": [
			("UAT closure", "Completed"),
			("Store training videos", "Completed"),
		],
		"attach_readme": False,
	},
]


def _meta():
	return frappe.get_meta("Project")


def ensure_demo_user(row: dict) -> str:
	email = row["email"]
	if frappe.db.exists("User", email):
		return "skipped"

	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": row["first_name"],
			"last_name": row.get("last_name") or "",
			"enabled": 1,
			"send_welcome_email": 0,
			"user_type": "System User",
		}
	)
	for role in row.get("roles") or ["Projects User"]:
		doc.append("roles", {"role": role})
	doc.insert(ignore_permissions=True)
	update_password(email, DEMO_PASSWORD)
	return "created"


def ensure_demo_project(pj: dict, company: str) -> tuple[str, str]:
	code = pj["code"]
	existing = frappe.db.get_value("Project", {"portal_project_code": code}, "name")
	if existing:
		return existing, "skipped"

	meta = _meta()
	doc = frappe.get_doc(
		{
			"doctype": "Project",
			"project_name": pj["project_name"],
			"company": company,
			"naming_series": "PROJ-.####",
			"status": "Open",
			"expected_start_date": add_days(today(), -45),
			"expected_end_date": add_days(today(), 120),
			"estimated_costing": pj.get("cost") or 0,
			"percent_complete": 35 if pj["stage"] == "Active" else 20,
		}
	)
	if meta.has_field("portal_project_code"):
		doc.portal_project_code = code
	if meta.has_field("portal_kanban_stage"):
		doc.portal_kanban_stage = pj["stage"]
	if meta.has_field("portal_project_manager") and pj.get("manager"):
		doc.portal_project_manager = pj["manager"]

	doc.insert(ignore_permissions=True)

	for u in pj.get("team") or []:
		if frappe.db.exists("User", u):
			doc.append("users", {"user": u})
	doc.save(ignore_permissions=True)
	return doc.name, "created"


def ensure_task(project: str, subject: str, status: str) -> str:
	if frappe.db.exists("Task", {"project": project, "subject": subject}):
		return "skipped"
	t = frappe.get_doc(
		{
			"doctype": "Task",
			"subject": subject,
			"project": project,
			"status": status,
			"is_group": 0,
		}
	)
	t.insert(ignore_permissions=True)
	return "created"


def attach_demo_file(project_name: str) -> str:
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Project",
			"attached_to_name": project_name,
			"file_name": "portal-demo-readme.txt",
		},
		limit=1,
	)
	if files:
		return "skipped"
	body = (
		"Portal App — demo attachment\n"
		"This file was created by the showcase seed script.\n"
		f"Demo login passwords are documented in docs/END_USER_GUIDE.md (Demo section).\n"
	).encode("utf-8")
	save_file("portal-demo-readme.txt", body, "Project", project_name, is_private=0)
	return "created"


def run_seed() -> dict:
	"""Create demo users, projects, tasks, and a sample file. Idempotent."""
	company = get_default_company()
	if not company:
		return {"ok": False, "error": "Set a default Company before seeding (ERPNext)."}

	summary = {"users": [], "projects": [], "tasks": [], "files": []}

	for row in DEMO_USERS:
		summary["users"].append({"email": row["email"], "status": ensure_demo_user(row)})

	for pj in DEMO_PROJECTS:
		name, st = ensure_demo_project(pj, company)
		summary["projects"].append({"code": pj["code"], "name": name, "status": st})
		proj_name = name

		for subj, tstatus in pj.get("tasks") or []:
			ts = ensure_task(proj_name, subj, tstatus)
			summary["tasks"].append({"project": proj_name, "subject": subj, "status": ts})

		if pj.get("attach_readme"):
			fs = attach_demo_file(proj_name)
			summary["files"].append({"project": proj_name, "status": fs})

	frappe.db.commit()
	return {
		"ok": True,
		"demo_password_hint": DEMO_PASSWORD,
		"summary": summary,
	}


def seed_showcase():
	"""Entry point for `bench execute portal_app.demo_seed.seed_showcase`."""
	frappe.set_user("Administrator")
	out = run_seed()
	frappe.db.commit()
	print(json.dumps(out, indent=2, default=str))
	return out
