# Copyright (c) 2026, Portal App and contributors
# For license information, please see license.txt

"""Portal Demo Seed Run

A self-cleaning seed runner. Creating a row creates the demo data and records
exactly what was created in the child tables. Deleting the row deletes those
records (in dependency order), so a demo can be wiped with one click.

Pre-existing records are tracked too (with `skipped=1`) and are left alone on
cleanup. This is what makes the doctype safe to run repeatedly without
destroying real data that happens to share an email or project code.
"""

from __future__ import annotations

import json
import traceback

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, now_datetime, today
from frappe.utils.file_manager import save_file
from frappe.utils.password import update_password


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
	{
		"email": "portal.client@demo.local",
		"first_name": "Demo",
		"last_name": "Client",
		"roles": ["Portal Customer"],
	},
]

DEMO_CUSTOMERS: list[dict] = [
	{"customer_name": "Demo — Northwind Industries", "customer_type": "Company"},
	{"customer_name": "Demo — Riverbank Holdings", "customer_type": "Company"},
]

DEMO_PROJECTS: list[dict] = [
	{
		"project_name": "Demo — HQ Campus Upgrade",
		"code": "DEMO-HQ",
		"stage": "Active",
		"manager": "portal.pm@demo.local",
		"team": ["portal.pm@demo.local", "portal.manager@demo.local", "portal.member1@demo.local"],
		"customer": "Demo — Northwind Industries",
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
		"customer": "Demo — Riverbank Holdings",
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
		"customer": "Demo — Northwind Industries",
		"cost": 950000,
		"tasks": [
			("Vendor RFP", "Open"),
			("Network rack layout", "Open"),
			("Safety review", "Open"),
		],
		"attach_readme": True,
	},
	{
		"project_name": "Demo — Solar Field Phase 2",
		"code": "DEMO-SOL",
		"stage": "On Hold",
		"manager": "portal.manager@demo.local",
		"team": ["portal.manager@demo.local", "portal.pm@demo.local"],
		"customer": "Demo — Riverbank Holdings",
		"cost": 1200000,
		"tasks": [("Permit resubmission", "Open")],
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


def _ensure_company():
	from erpnext import get_default_company

	company = get_default_company()
	if not company:
		frappe.throw(_("Set a default Company before running the demo seed (ERPNext)."))
	return company


class PortalDemoSeedRun(Document):
	# ------------------------------------------------------------------ Insert
	def before_insert(self):
		"""Run the seed; record exactly what we created."""
		self.run_at = now_datetime()
		self.run_by = frappe.session.user
		self.demo_password_hint = DEMO_PASSWORD
		self.status = "Active"

		summary = {"users": [], "customers": [], "projects": [], "tasks": [], "files": []}

		try:
			if int(self.include_users or 0):
				self._seed_users(summary)
			if int(self.include_customers or 0):
				self._seed_customers(summary)
			if int(self.include_projects or 0):
				self._seed_projects(summary)
		except Exception as exc:
			self.status = "Failed"
			self.notes = (self.notes or "") + f"\n\nSeed failed: {exc}\n{traceback.format_exc()}"
			frappe.log_error(traceback.format_exc(), "Portal Demo Seed Run: insert")
			# Roll back what we already created so the system stays clean.
			self._cleanup(best_effort=True)
			raise

		self.summary_json = json.dumps(summary, indent=2, default=str)

	# ------------------------------------------------------------------ Delete
	def on_trash(self):
		"""Delete every record we created in this run (skipped rows are preserved)."""
		self._cleanup(best_effort=True)

	# ============================================================== seed steps

	def _record(self, table, doctype, name, label="", skipped=False):
		self.append(
			table,
			{
				"record_doctype": doctype,
				"record_name": name,
				"record_label": label,
				"skipped": 1 if skipped else 0,
			},
		)

	def _seed_users(self, summary):
		# Make sure the Portal Customer role exists before granting it.
		try:
			from portal_app.api import helper

			helper.ensure_portal_customer_role()
		except Exception:
			pass

		for row in DEMO_USERS:
			email = row["email"]
			if frappe.db.exists("User", email):
				self._record("created_users", "User", email, row["first_name"] + " " + row.get("last_name", ""), skipped=True)
				summary["users"].append({"email": email, "status": "skipped"})
				continue
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
			for r in row.get("roles") or ["Projects User"]:
				doc.append("roles", {"role": r})
			doc.insert(ignore_permissions=True)
			update_password(email, DEMO_PASSWORD)
			self._record("created_users", "User", email, row["first_name"] + " " + row.get("last_name", ""))
			summary["users"].append({"email": email, "status": "created"})

	def _seed_customers(self, summary):
		# Customer is provided by ERPNext; if missing, skip silently.
		if not frappe.db.exists("DocType", "Customer"):
			return
		for row in DEMO_CUSTOMERS:
			cname = row["customer_name"]
			existing = frappe.db.get_value("Customer", {"customer_name": cname}, "name")
			if existing:
				self._record("created_customers", "Customer", existing, cname, skipped=True)
				summary["customers"].append({"name": existing, "status": "skipped"})
				continue
			doc = frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": cname,
					"customer_type": row.get("customer_type") or "Company",
				}
			)
			doc.insert(ignore_permissions=True)
			self._record("created_customers", "Customer", doc.name, cname)
			summary["customers"].append({"name": doc.name, "status": "created"})

	def _seed_projects(self, summary):
		company = _ensure_company()
		meta = frappe.get_meta("Project")

		for pj in DEMO_PROJECTS:
			code = pj["code"]
			existing = frappe.db.get_value("Project", {"portal_project_code": code}, "name")
			if existing:
				self._record("created_projects", "Project", existing, pj["project_name"], skipped=True)
				summary["projects"].append({"name": existing, "code": code, "status": "skipped"})
				if int(self.include_tasks or 0):
					self._seed_tasks_for(existing, pj, summary, project_pre_existing=True)
				continue

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
			if pj.get("customer"):
				cust = frappe.db.get_value("Customer", {"customer_name": pj["customer"]}, "name")
				if cust:
					doc.customer = cust
			doc.insert(ignore_permissions=True)

			for u in pj.get("team") or []:
				if frappe.db.exists("User", u):
					doc.append("users", {"user": u})
			doc.save(ignore_permissions=True)

			self._record("created_projects", "Project", doc.name, pj["project_name"])
			summary["projects"].append({"name": doc.name, "code": code, "status": "created"})

			if int(self.include_tasks or 0):
				self._seed_tasks_for(doc.name, pj, summary)
			if int(self.include_files or 0) and pj.get("attach_readme"):
				self._seed_file_for(doc.name, summary)

	def _seed_tasks_for(self, project_name, pj, summary, project_pre_existing=False):
		for subj, tstatus in pj.get("tasks") or []:
			if frappe.db.exists("Task", {"project": project_name, "subject": subj}):
				existing = frappe.db.get_value(
					"Task", {"project": project_name, "subject": subj}, "name"
				)
				if existing:
					self._record("created_tasks", "Task", existing, subj, skipped=True)
					summary["tasks"].append({"name": existing, "subject": subj, "status": "skipped"})
				continue
			t = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": subj,
					"project": project_name,
					"status": tstatus,
					"is_group": 0,
				}
			)
			t.insert(ignore_permissions=True)
			# If the project was pre-existing, mark the task skipped=true so cleanup
			# does not orphan tasks created on someone else's project. We still record
			# the task name so admins can audit it.
			self._record("created_tasks", "Task", t.name, subj, skipped=project_pre_existing)
			summary["tasks"].append({"name": t.name, "subject": subj, "status": "created"})

	def _seed_file_for(self, project_name, summary):
		body = (
			"Portal App — demo attachment\n"
			"Created by Portal Demo Seed Run.\n"
			f"Run: {self.name or 'pending'} on {self.run_at}\n"
		).encode("utf-8")
		fdoc = save_file(
			"portal-demo-readme.txt",
			body,
			"Project",
			project_name,
			is_private=0,
		)
		if fdoc:
			self._record("created_files", "File", fdoc.name, fdoc.file_name)
			summary["files"].append({"name": fdoc.name, "project": project_name, "status": "created"})

	# =========================================================== cleanup steps

	def _cleanup(self, best_effort: bool = False):
		"""Delete recorded records in reverse-dependency order.

		Order matters: files → tasks → projects → customers → users. Within each
		category, records flagged `skipped` are left alone (they pre-existed).
		"""
		for kind in ("created_files", "created_tasks", "created_projects", "created_customers", "created_users"):
			rows = list(self.get(kind) or [])
			for row in rows:
				if int(row.skipped or 0):
					continue
				dt, dn = row.record_doctype, row.record_name
				if not dt or not dn:
					continue
				try:
					if not frappe.db.exists(dt, dn):
						continue
					if dt == "Project":
						# Cascade attached files + project tasks not already removed.
						_cascade_project(dn)
					if dt == "User":
						# Detach this user from any Project users table they were on.
						_detach_user_from_projects(dn)
					frappe.delete_doc(dt, dn, force=1, ignore_permissions=True, ignore_missing=True)
				except Exception:
					if best_effort:
						frappe.log_error(traceback.format_exc(), f"Portal Demo Seed cleanup {dt}/{dn}")
						continue
					raise

		# Mark this run as cleaned (only meaningful when called outside on_trash).
		try:
			if frappe.db.exists(self.doctype, self.name):
				self.db_set("status", "Cleaned", commit=False)
		except Exception:
			pass


def _cascade_project(project_name: str):
	"""Delete all File rows + Tasks attached to the project, before the project itself."""
	for f in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Project", "attached_to_name": project_name},
		pluck="name",
	):
		try:
			frappe.delete_doc("File", f, force=1, ignore_permissions=True, ignore_missing=True)
		except Exception:
			frappe.log_error(traceback.format_exc(), f"Portal Demo Seed cascade File/{f}")
	for t in frappe.get_all("Task", filters={"project": project_name}, pluck="name"):
		try:
			frappe.delete_doc("Task", t, force=1, ignore_permissions=True, ignore_missing=True)
		except Exception:
			frappe.log_error(traceback.format_exc(), f"Portal Demo Seed cascade Task/{t}")
	# Drop any DocShare rows pointing at the project (avoids dangling shares).
	try:
		frappe.db.delete("DocShare", {"share_doctype": "Project", "share_name": project_name})
	except Exception:
		pass


def _detach_user_from_projects(user_id: str):
	"""Remove the user from every Project Users child table before deleting the User."""
	rows = frappe.get_all(
		"Project User",
		filters={"user": user_id},
		fields=["name", "parent"],
	)
	for row in rows:
		try:
			frappe.db.delete("Project User", {"name": row["name"]})
		except Exception:
			pass
	# Drop DocShares attributed to the user too.
	try:
		frappe.db.delete("DocShare", {"user": user_id})
	except Exception:
		pass
