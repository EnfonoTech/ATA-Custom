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

from portal_app.api.files import ensure_project_folders


def _new_demo_password() -> str:
	"""A fresh random password per seed run.

	This used to be a hardcoded constant in a PUBLIC repository, which meant every
	site that had ever run the seed shared one internet-published credential for
	accounts holding the Projects Manager role (i.e. the whole project portfolio).
	Never reintroduce a literal here.
	"""
	return "Dm-" + frappe.generate_hash(length=18) + "#1"


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

DEMO_CUSTOMERS: list[dict] = []  # No generic demo customers for ATA project list

_MANAGERS = [
	"portal.manager@demo.local",
	"portal.pm@demo.local",
	"portal.member1@demo.local",
	"portal.member2@demo.local",
]
_TEAMS = [
	["portal.pm@demo.local", "portal.manager@demo.local", "portal.member1@demo.local"],
	["portal.manager@demo.local", "portal.member2@demo.local"],
	["portal.pm@demo.local", "portal.member1@demo.local", "portal.member2@demo.local"],
	["portal.manager@demo.local", "portal.pm@demo.local"],
]


_STAGE_PCT = {"Done": 100, "On Hold": 65, "Review": 50, "Active": 35, "Planning": 10}
_STAGE_STATUS = {"Done": "Completed", "On Hold": "On Hold"}  # default "Open"


def _year_from_code(code: str) -> int:
	"""Derive calendar year from ATA project code prefix (e.g. '2201' → 2022)."""
	if code.startswith("CDB-"):
		return 2026
	try:
		return 2000 + int(code[:2])
	except (ValueError, IndexError):
		return 2024


def _p(
	code: str,
	name: str,
	stage: str,
	idx: int = 0,
	cost: int = 0,
	tasks: list | None = None,
	attach: bool = False,
) -> dict:
	return {
		"project_name": f"{code} – {name}",
		"code": f"ATA-{code}",
		"stage": stage,
		"year": _year_from_code(code),
		"manager": _MANAGERS[idx % len(_MANAGERS)],
		"team": _TEAMS[idx % len(_TEAMS)],
		"cost": cost,
		"tasks": tasks or [],
		"attach_readme": attach,
	}


DEMO_PROJECTS: list[dict] = [
	# ── 2022 (2201–2237) ─────────────────────────────────────────────────────
	_p(
		"2201",
		"AL BASSAM",
		"Done",
		0,
		350000,
		[("Concept Design", "Completed"), ("Schematic Design", "Completed")],
		True,
	),
	_p("2202", "WALEED BIN SAEDAN RESORT", "Done", 1, 1800000),
	_p("2203", "AL BUKAYRIYAH -2", "Done", 2, 420000),
	_p("2204", "AL MAJED TOWER", "Done", 3, 1200000),
	_p("2205", "AL MAJED OFFICES", "Done", 0, 950000),
	_p("2206", "KHALID AL AJLAAN", "Done", 1, 380000),
	_p("2207", "AL GAMMAS DIWANIYAH", "Done", 2, 290000),
	_p("2208", "AL MAJEEDIYA", "Done", 3, 460000),
	_p("2209", "AFRAS ROW LAND (AL KHOYOOL ARABIA-3)", "Done", 0, 320000),
	_p("2210", "AL QASSIM-6", "Done", 1, 400000),
	_p("2211", "AL QASSIM-7", "Done", 2, 400000),
	_p("2212", "OUD EDITION", "Done", 3, 550000),
	_p("2213", "ABDULLAH ALNIMER", "Done", 0, 310000),
	_p("2214", "SIKKAH 2", "Done", 1, 280000),
	_p("2215", "AL MAJEEDIYA 2", "Done", 2, 460000),
	_p("2216", "AL HASSAN PALACE", "Done", 3, 2100000),
	_p("2217", "MANAL PALACE", "Done", 0, 1750000),
	_p("2218", "TURKI ALKOSIR", "Done", 1, 340000),
	_p("2219", "ZOOD (GAMMAS)", "Done", 2, 370000),
	_p("2220", "AL ZALAL", "Done", 3, 490000),
	_p("2221", "GHAIMA 2", "Done", 0, 360000),
	_p("2222", "NMR TOWER", "Done", 1, 1100000),
	_p("2223", "YAMANY TOWER", "Done", 2, 980000),
	_p("2224", "AL KHURAJI GARDEN 1", "Done", 3, 430000),
	_p("2225", "AL KHURAJI GARDEN 2", "Done", 0, 430000),
	_p("2226", "AL BASATEEN COMMERCIAL (AL SHGREY)", "Done", 1, 870000),
	_p("2227", "SAMEEM TOWER", "Done", 2, 1050000),
	_p("2228", "AGNA 2", "Done", 3, 390000),
	_p("2229", "FIRST AVENUE 2", "Done", 0, 720000),
	_p("2230", "ASEEL AR RAWDAH (RAFEN)", "Done", 1, 410000),
	_p("2231", "ZOOD -2 (RESIDENTIAL)", "Done", 2, 380000),
	_p("2232", "SBS (SULTAN BIN SALMAN)", "Done", 3, 1600000),
	_p("2233", "AL DOHAYAN", "Done", 0, 330000),
	_p("2234", "SAMEEM 2", "Done", 1, 510000),
	_p("2235", "AGNA 3", "Done", 2, 400000),
	_p("2236", "SALEH ALMAHROOS", "Done", 3, 350000),
	_p("2237", "TAMASOK 2", "Done", 0, 480000),
	# ── 2023 (2301–2328) ─────────────────────────────────────────────────────
	_p(
		"2301",
		"MOHAMED HABIB RESIDENTIAL LAND",
		"Done",
		1,
		290000,
		[("Site Survey", "Completed"), ("Concept Approval", "Completed")],
	),
	_p("2302", "ZOOD COMPLEX (2219 + 2231)", "Done", 2, 750000),
	_p("2303", "ASEEL AR RAWDAH", "Done", 3, 420000),
	_p("2304", "SALEH AL MAHROOS", "Done", 0, 360000),
	_p("2305", "SALEH AL SALEH", "Done", 1, 340000),
	_p("2306", "ALMUSA TOWER", "Done", 2, 1150000),
	_p("2307", "AL RAMZE", "Done", 3, 380000),
	_p("2308", "ALHADAB (60MX60M)", "Done", 0, 520000),
	_p("2309", "AL BASATEEN HOUSES", "Done", 1, 460000),
	_p("2310", "AGNA 04 (UNIVERSITY)", "Done", 2, 430000),
	_p("2311", "AL FAQIH -2", "Done", 3, 370000),
	_p("2312", "AL NEGAIR-2", "Done", 0, 390000),
	_p("2313", "AGNA 5 AL TAKHASSUSI", "Done", 1, 410000),
	_p("2314", "AL TUWAIRY", "Done", 2, 320000),
	_p("2315", "ARAK (KING SAUD UNIVERSITY)", "On Hold", 3, 680000),
	_p("2316", "ALHATLAN -2 (MARHABA COMPANY)", "On Hold", 0, 450000),
	_p("2317", "AL QASSIM-8", "On Hold", 1, 410000),
	_p("2318", "AL QASSIM-6 B", "On Hold", 2, 410000),
	_p("2319", "AL RUGAIB", "On Hold", 3, 350000),
	_p("2320", "ZOOD KING SALMAN", "On Hold", 0, 390000),
	_p("2321", "AL JASSER COMPLEX", "On Hold", 1, 820000),
	_p("2322", "AL QASSIM CHAMBER COMMERCIAL AND INDUSTRY", "On Hold", 2, 1900000),
	_p("2323", "NAWAT", "On Hold", 3, 370000),
	_p("2324", "NMR MOSQUE", "On Hold", 0, 280000),
	_p("2325", "LAFEEF -2", "On Hold", 1, 440000),
	_p("2326", "AL ABDULKAREEM", "On Hold", 2, 350000),
	_p("2327", "AL NARJIS OFFICES (IBRAHIM ALMOUSA)", "On Hold", 3, 490000),
	_p("2328", "RAFED-02", "On Hold", 0, 380000),
	# ── 2024 (2401–2422) ─────────────────────────────────────────────────────
	_p(
		"2401",
		"ALTHEYAB TOWER",
		"Review",
		1,
		1250000,
		[("Design Development", "Open"), ("Municipality Submission", "Open")],
	),
	_p("2402", "THERA MOUNTAIN", "Review", 2, 2200000),
	_p("2403", "AL HAMDAN-1", "Review", 3, 430000),
	_p("2404", "REFAD", "Review", 0, 390000),
	_p("2405", "MAWRITH (TANMIYAT)", "Review", 1, 560000),
	_p("2406", "AL QASSIM TOWER", "Review", 2, 1100000),
	_p("2407", "AL RAKHEES", "Review", 3, 380000),
	_p("2408", "SAMEEM-2", "Review", 0, 530000),
	_p("2409", "TARAKUM OFFICE (MADAM LAMYA)", "Review", 1, 670000),
	_p("2410", "ADEL ALMOSA 1", "Active", 2, 450000),
	_p("2411", "AL HADAB-2 (AL NAKHIL)", "Active", 3, 540000),
	_p("2412", "TAMIM AL SALEM 2 COMMERCIAL", "Active", 0, 780000),
	_p("2413", "AL RUGAIB 2", "Active", 1, 400000),
	_p("2414", "AL QASEEM RESIDENCE", "Active", 2, 360000),
	_p("2415", "MUSAB AL MAGED", "Active", 3, 390000),
	_p("2416", "SBS", "Active", 0, 1650000),
	_p("2417", "SMSA", "Active", 1, 920000),
	_p("2418", "NAIF ALMOUSA", "Active", 2, 410000),
	_p("2419", "MAKAN MALL", "Active", 3, 2400000),
	_p("2420", "AL SALMAN-THALIA", "Active", 0, 370000),
	_p("2421", "TAMIM AL SALEM 3 RESIDENTIAL", "Active", 1, 480000),
	_p("2422", "AL EKRESH", "Active", 2, 340000),
	# ── 2025 (2501–2518) ─────────────────────────────────────────────────────
	_p(
		"2501",
		"AL NAKHEEL MOSQUE",
		"Active",
		3,
		310000,
		[("Concept Design", "Open"), ("Client Presentation", "Open")],
	),
	_p("2502", "AL MUHANNA", "Active", 0, 380000),
	_p("2503", "ABDULRAHMAN ALMUSA 2", "Active", 1, 420000),
	_p("2504", "WABEEL TOWER (AL TUWAJRI)", "Active", 2, 1300000),
	_p("2505", "YAQEEN", "Active", 3, 360000),
	_p("2506", "PRINCE ABDULAZIZ MASHOUR", "Active", 0, 1900000),
	_p("2507", "ENMA ALRWABI", "Active", 1, 440000),
	_p("2508", "AHMED ALTHEYAB REST HOUSES", "Active", 2, 560000),
	_p("2509", "NMR PAPILON ID", "Active", 3, 390000),
	_p("2510", "SAFA TOWER", "Active", 0, 1100000),
	_p("2511", "RASAF TOWER", "Active", 1, 1050000),
	_p("2512", "AL OBAID TOWER", "Planning", 2, 980000),
	_p("2513", "ALMUSA ALTAHLIYA", "Planning", 3, 430000),
	_p("2514", "PRINCE MUQIRIN (MIASEM)", "Planning", 0, 1700000),
	_p("2515", "AL AJLAN 01", "Planning", 1, 390000),
	_p("2516", "AL AJLAN 02", "Planning", 2, 390000),
	_p("2517", "MITHAQ HOLDING", "Planning", 3, 850000),
	_p("2518", "MAJED THEYAB", "Planning", 0, 420000),
	# ── 2026 (2601–2602) ─────────────────────────────────────────────────────
	_p("2601", "ABDULAZIZ AL THEYAB", "Planning", 1, 460000, [("Brief Review", "Open")]),
	_p("2602", "AL NAJEM", "Planning", 2, 380000),
	# ── 2026 Concept Design Brief (CDB-01–CDB-13) ────────────────────────────
	_p("CDB-01", "AL MEREJ", "Planning", 3, 0),
	_p("CDB-02", "AL RABIAH COMPLEX", "Planning", 0, 0),
	_p("CDB-03", "AL MOKAYMEN MOSQUE", "Planning", 1, 0),
	_p("CDB-04", "AL JARBAE COMPOUND", "Planning", 2, 0),
	_p("CDB-05", "ABDULAZIZ THEYAB", "Planning", 3, 0),
	_p("CDB-06", "LETHAM-2", "Planning", 0, 0),
	_p("CDB-07", "JAREED HOTEL – JEDDAH", "Planning", 1, 0),
	_p("CDB-08", "MASHEED", "Planning", 2, 0),
	_p("CDB-09", "AL HOWIRINY", "Planning", 3, 0),
	_p("CDB-10", "AL YASEEN TOWER 1.4", "Planning", 0, 0),
	_p("CDB-11", "NMR-LABAN", "Planning", 1, 0),
	_p("CDB-12", "NMR-KAFD", "Planning", 2, 0),
	_p("CDB-13", "MASHAR- HAIL", "Planning", 3, 0),
]


def _ensure_company():
	"""Return default company name, or any company, or None (caller handles gracefully)."""
	company = None
	try:
		from erpnext import get_default_company

		company = get_default_company()
	except Exception:
		pass
	if not company and frappe.db.exists("DocType", "Company"):
		try:
			company = frappe.db.get_value("Company", {}, "name", order_by="creation asc")
		except Exception:
			pass
	return company


class PortalDemoSeedRun(Document):
	# ------------------------------------------------------------------ Insert
	def before_insert(self):
		"""Run the seed; record exactly what we created."""
		self.run_at = now_datetime()
		self.run_by = frappe.session.user
		demo_password = _new_demo_password()
		self.demo_password_hint = demo_password
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
				self._record(
					"created_users",
					"User",
					email,
					row["first_name"] + " " + row.get("last_name", ""),
					skipped=True,
				)
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
			update_password(email, self.demo_password_hint)
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

		# The docx importer passes its parsed list on the document instead of
		# reassigning the module global, which raced between concurrent requests and
		# could leave one admin's imported list installed for every later seed.
		for pj in self.flags.get("projects_override") or DEMO_PROJECTS:
			code = pj["code"]
			existing = frappe.db.get_value("Project", {"portal_project_code": code}, "name")
			if existing:
				self._record("created_projects", "Project", existing, pj["project_name"], skipped=True)
				summary["projects"].append({"name": existing, "code": code, "status": "skipped"})
				if int(self.include_tasks or 0):
					self._seed_tasks_for(existing, pj, summary, project_pre_existing=True)
				continue

			year = pj.get("year") or _year_from_code(pj["code"].replace("ATA-", ""))
			proj_dict = {
				"doctype": "Project",
				"project_name": pj["project_name"],
				"status": _STAGE_STATUS.get(pj["stage"], "Open"),
				"expected_start_date": f"{year}-01-01",
				"expected_end_date": f"{year}-12-31",
				"estimated_costing": pj.get("cost") or 0,
				"percent_complete": _STAGE_PCT.get(pj["stage"], 20),
			}
			if company and meta.has_field("company"):
				proj_dict["company"] = company
			doc = frappe.get_doc(proj_dict)
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
				existing = frappe.db.get_value("Task", {"project": project_name, "subject": subj}, "name")
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
		"""Create demo Project File records showing all category/type classifications."""
		has_pf = frappe.db.exists("DocType", "Project File")

		# Build the project folder tree and create a label→name lookup.
		folder_info = ensure_project_folders(project_name)
		project_root = folder_info.get("project_root", "")
		subfolder_map = {sf["label"]: sf["name"] for sf in folder_info.get("subfolders", [])}

		# One placeholder file per major category — covers every classification path.
		# (filename, document_type, folder_label, notes_for_demo)
		demo_files = [
			(
				"2201-concept-presentation.pptx",
				"",
				"02-CONCEPT/05-PRESENTATION",
				"Presentation Files / PowerPoint — classified by .pptx extension",
			),
			(
				"2201-floor-plan-ground.dwg",
				"",
				"03-BALADIYA/02-BALADIYA PLANS",
				"Drawing / Layout Files / AutoCAD — classified by .dwg extension",
			),
			(
				"2201-massing-model.skp",
				"",
				"02-CONCEPT/02-SKETCH UP",
				"3D Model Files / SketchUp — classified by .skp extension",
			),
			(
				"2201-area-feasibility.xlsx",
				"",
				"02-CONCEPT/04-FEASIBILITY STUDY/REF",
				"Feasibility / Area Calc Files / Excel — classified by .xlsx extension",
			),
			(
				"2201-exterior-render-01.jpg",
				"",
				"02-CONCEPT/03-PERSPECTIVES",
				"Rendering / Image Files / JPEG — classified by .jpg extension",
			),
			(
				"2201-design-artwork.ai",
				"",
				"02-CONCEPT/05-PRESENTATION",
				"Editable Design Source Files / Illustrator — classified by .ai extension",
			),
			(
				"2201-concept-package.pdf",
				"Presentation",
				"02-CONCEPT/05-PRESENTATION",
				"Presentation Files / PDF Presentation — Document Type = Presentation",
			),
			(
				"2201-drawing-submission.pdf",
				"Drawing Sheet",
				"03-BALADIYA/02-BALADIYA PLANS",
				"Drawing / Layout Files / PDF Drawing — Document Type = Drawing Sheet",
			),
			(
				"2201-feasibility-report.pdf",
				"Feasibility Report",
				"02-CONCEPT/04-FEASIBILITY STUDY/REF",
				"Feasibility / Area Calc Files / PDF — Document Type = Feasibility Report",
			),
			(
				"2201-issued-submission.pdf",
				"Submission",
				"03-BALADIYA/03-AREA STATEMENT",
				"Submission Files / PDF Submission — Document Type = Submission",
			),
		]

		for fname, doc_type, folder_label, note in demo_files:
			# Resolve the target folder; fall back to project root if label not found.
			folder_name = subfolder_map.get(folder_label) or project_root

			# Placeholder file content — clearly marked as demo data.
			body = (
				f"[ATA DEMO FILE]\n"
				f"Project: 2201 – AL BASSAM\n"
				f"File: {fname}\n"
				f"Classification: {note}\n"
				f"Created by Portal Demo Seed Run {self.name or '—'}.\n"
			).encode("utf-8")

			# Upload placeholder to Frappe Files so we have a real file_url.
			try:
				fdoc = save_file(fname, body, "Project", project_name, folder=folder_name, is_private=0)
			except Exception:
				continue
			if not fdoc:
				continue
			self._record("created_files", "File", fdoc.name, fname)
			summary["files"].append({"name": fdoc.name, "file": fname, "status": "created"})

			# Create a Project File record (dsi_erp doctype) if installed.
			if not has_pf:
				continue
			existing_pf = frappe.db.get_value("Project File", {"file_attachment": fdoc.file_url}, "name")
			if existing_pf:
				self._record("created_files", "Project File", existing_pf, fname, skipped=True)
				continue
			try:
				pf = frappe.get_doc(
					{
						"doctype": "Project File",
						"project_code": "2201",
						"project_name": "AL BASSAM",
						"project_stage": "Concept Design",
						"document_type": doc_type or "",
						"file_attachment": fdoc.file_url,
						"notes": note,
					}
				)
				pf.insert(ignore_permissions=True)
				self._record("created_files", "Project File", pf.name, fname)
				summary["files"].append({"name": pf.name, "file": fname, "status": "project_file_created"})
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Demo seed: Project File insert {fname}")

	# =========================================================== cleanup steps

	def _recorded_names(self, *kinds) -> set:
		"""Every (doctype, name) this run actually created — `skipped` rows excluded."""
		out = set()
		for kind in kinds:
			for row in self.get(kind) or []:
				if int(row.skipped or 0):
					continue
				if row.record_doctype and row.record_name:
					out.add((row.record_doctype, row.record_name))
		return out

	def _cleanup(self, best_effort: bool = False):
		"""Delete recorded records in reverse-dependency order.

		Order matters: files → tasks → projects → customers → users. Within each
		category, records flagged `skipped` are left alone (they pre-existed).
		"""
		# Cascades are restricted to what this run recorded. Deleting a seeded Project
		# used to wipe EVERY File and Task under it, so any real document a staff member
		# uploaded into a demo project during a walkthrough was destroyed with it.
		recorded = self._recorded_names(
			"created_files", "created_tasks", "created_projects", "created_customers", "created_users"
		)
		for kind in (
			"created_files",
			"created_tasks",
			"created_projects",
			"created_customers",
			"created_users",
		):
			rows = list(self.get(kind) or [])
			# Delete Project File records before File records to avoid FK constraint issues.
			rows_sorted = sorted(rows, key=lambda r: 0 if r.record_doctype == "Project File" else 1)
			for row in rows_sorted:
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
						_cascade_project(dn, recorded)
					if dt == "User":
						# Detach this user from any Project users table they were on.
						_detach_user_from_projects(dn, recorded)
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


def _cascade_project(project_name: str, recorded: set):
	"""Delete the Files/Tasks THIS RUN created under the project, before the project.

	Anything not in `recorded` is real data someone added to the project after seeding
	and is deliberately left in place. If that leaves children behind, the Project
	delete below fails and is logged — far better than silently destroying it.
	"""
	left_behind = []
	for f in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Project", "attached_to_name": project_name},
		pluck="name",
	):
		if ("File", f) not in recorded:
			left_behind.append("File/" + f)
			continue
		try:
			frappe.delete_doc("File", f, force=1, ignore_permissions=True, ignore_missing=True)
		except Exception:
			frappe.log_error(traceback.format_exc(), f"Portal Demo Seed cascade File/{f}")
	for t in frappe.get_all("Task", filters={"project": project_name}, pluck="name"):
		if ("Task", t) not in recorded:
			left_behind.append("Task/" + t)
			continue
		try:
			frappe.delete_doc("Task", t, force=1, ignore_permissions=True, ignore_missing=True)
		except Exception:
			frappe.log_error(traceback.format_exc(), f"Portal Demo Seed cascade Task/{t}")

	if left_behind:
		frappe.log_error(
			"Left in place (not created by this seed run):\n" + "\n".join(left_behind),
			f"Portal Demo Seed cleanup kept real data under {project_name}",
		)

	# Drop DocShare rows pointing at this seeded project only.
	try:
		frappe.db.delete("DocShare", {"share_doctype": "Project", "share_name": project_name})
	except Exception:
		pass


def _detach_user_from_projects(user_id: str, recorded: set):
	"""Remove the user from Project Users rows before deleting the User.

	DocShare removal is limited to shares on projects this run created. Deleting every
	DocShare belonging to the user, as this previously did, would revoke real access on
	real projects if the demo account had ever been shared anything else.
	"""
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

	seeded_projects = [n for (dt, n) in recorded if dt == "Project"]
	if seeded_projects:
		try:
			frappe.db.delete(
				"DocShare",
				{"user": user_id, "share_doctype": "Project", "share_name": ["in", seeded_projects]},
			)
		except Exception:
			pass
