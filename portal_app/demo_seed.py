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
_STAGE_STATUS = {"Done": "Completed", "On Hold": "On Hold"}


def _year_from_code(code: str) -> int:
	if code.startswith("CDB-"):
		return 2026
	try:
		return 2000 + int(code[:2])
	except (ValueError, IndexError):
		return 2024


def _p(code: str, name: str, stage: str, idx: int = 0, cost: int = 0,
       tasks: list | None = None, attach: bool = False) -> dict:
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
	_p("2201", "AL BASSAM",                           "Done",   0, 350000, [("Concept Design", "Completed"), ("Schematic Design", "Completed")], True),
	_p("2202", "WALEED BIN SAEDAN RESORT",             "Done",   1, 1800000),
	_p("2203", "AL BUKAYRIYAH -2",                    "Done",   2, 420000),
	_p("2204", "AL MAJED TOWER",                      "Done",   3, 1200000),
	_p("2205", "AL MAJED OFFICES",                    "Done",   0, 950000),
	_p("2206", "KHALID AL AJLAAN",                    "Done",   1, 380000),
	_p("2207", "AL GAMMAS DIWANIYAH",                 "Done",   2, 290000),
	_p("2208", "AL MAJEEDIYA",                        "Done",   3, 460000),
	_p("2209", "AFRAS ROW LAND (AL KHOYOOL ARABIA-3)","Done",   0, 320000),
	_p("2210", "AL QASSIM-6",                         "Done",   1, 400000),
	_p("2211", "AL QASSIM-7",                         "Done",   2, 400000),
	_p("2212", "OUD EDITION",                         "Done",   3, 550000),
	_p("2213", "ABDULLAH ALNIMER",                    "Done",   0, 310000),
	_p("2214", "SIKKAH 2",                            "Done",   1, 280000),
	_p("2215", "AL MAJEEDIYA 2",                      "Done",   2, 460000),
	_p("2216", "AL HASSAN PALACE",                    "Done",   3, 2100000),
	_p("2217", "MANAL PALACE",                        "Done",   0, 1750000),
	_p("2218", "TURKI ALKOSIR",                       "Done",   1, 340000),
	_p("2219", "ZOOD (GAMMAS)",                       "Done",   2, 370000),
	_p("2220", "AL ZALAL",                            "Done",   3, 490000),
	_p("2221", "GHAIMA 2",                            "Done",   0, 360000),
	_p("2222", "NMR TOWER",                           "Done",   1, 1100000),
	_p("2223", "YAMANY TOWER",                        "Done",   2, 980000),
	_p("2224", "AL KHURAJI GARDEN 1",                 "Done",   3, 430000),
	_p("2225", "AL KHURAJI GARDEN 2",                 "Done",   0, 430000),
	_p("2226", "AL BASATEEN COMMERCIAL (AL SHGREY)",  "Done",   1, 870000),
	_p("2227", "SAMEEM TOWER",                        "Done",   2, 1050000),
	_p("2228", "AGNA 2",                              "Done",   3, 390000),
	_p("2229", "FIRST AVENUE 2",                      "Done",   0, 720000),
	_p("2230", "ASEEL AR RAWDAH (RAFEN)",             "Done",   1, 410000),
	_p("2231", "ZOOD -2 (RESIDENTIAL)",               "Done",   2, 380000),
	_p("2232", "SBS (SULTAN BIN SALMAN)",             "Done",   3, 1600000),
	_p("2233", "AL DOHAYAN",                          "Done",   0, 330000),
	_p("2234", "SAMEEM 2",                            "Done",   1, 510000),
	_p("2235", "AGNA 3",                              "Done",   2, 400000),
	_p("2236", "SALEH ALMAHROOS",                     "Done",   3, 350000),
	_p("2237", "TAMASOK 2",                           "Done",   0, 480000),
	# ── 2023 (2301–2328) ─────────────────────────────────────────────────────
	_p("2301", "MOHAMED HABIB RESIDENTIAL LAND",      "Done",   1, 290000, [("Site Survey", "Completed"), ("Concept Approval", "Completed")]),
	_p("2302", "ZOOD COMPLEX (2219 + 2231)",          "Done",   2, 750000),
	_p("2303", "ASEEL AR RAWDAH",                     "Done",   3, 420000),
	_p("2304", "SALEH AL MAHROOS",                    "Done",   0, 360000),
	_p("2305", "SALEH AL SALEH",                      "Done",   1, 340000),
	_p("2306", "ALMUSA TOWER",                        "Done",   2, 1150000),
	_p("2307", "AL RAMZE",                            "Done",   3, 380000),
	_p("2308", "ALHADAB (60MX60M)",                   "Done",   0, 520000),
	_p("2309", "AL BASATEEN HOUSES",                  "Done",   1, 460000),
	_p("2310", "AGNA 04 (UNIVERSITY)",                "Done",   2, 430000),
	_p("2311", "AL FAQIH -2",                         "Done",   3, 370000),
	_p("2312", "AL NEGAIR-2",                         "Done",   0, 390000),
	_p("2313", "AGNA 5 AL TAKHASSUSI",                "Done",   1, 410000),
	_p("2314", "AL TUWAIRY",                          "Done",   2, 320000),
	_p("2315", "ARAK (KING SAUD UNIVERSITY)",         "On Hold",3, 680000),
	_p("2316", "ALHATLAN -2 (MARHABA COMPANY)",       "On Hold",0, 450000),
	_p("2317", "AL QASSIM-8",                         "On Hold",1, 410000),
	_p("2318", "AL QASSIM-6 B",                       "On Hold",2, 410000),
	_p("2319", "AL RUGAIB",                           "On Hold",3, 350000),
	_p("2320", "ZOOD KING SALMAN",                    "On Hold",0, 390000),
	_p("2321", "AL JASSER COMPLEX",                   "On Hold",1, 820000),
	_p("2322", "AL QASSIM CHAMBER COMMERCIAL AND INDUSTRY", "On Hold", 2, 1900000),
	_p("2323", "NAWAT",                               "On Hold",3, 370000),
	_p("2324", "NMR MOSQUE",                          "On Hold",0, 280000),
	_p("2325", "LAFEEF -2",                           "On Hold",1, 440000),
	_p("2326", "AL ABDULKAREEM",                      "On Hold",2, 350000),
	_p("2327", "AL NARJIS OFFICES (IBRAHIM ALMOUSA)", "On Hold",3, 490000),
	_p("2328", "RAFED-02",                            "On Hold",0, 380000),
	# ── 2024 (2401–2422) ─────────────────────────────────────────────────────
	_p("2401", "ALTHEYAB TOWER",                      "Review", 1, 1250000, [("Design Development", "Open"), ("Municipality Submission", "Open")]),
	_p("2402", "THERA MOUNTAIN",                      "Review", 2, 2200000),
	_p("2403", "AL HAMDAN-1",                         "Review", 3, 430000),
	_p("2404", "REFAD",                               "Review", 0, 390000),
	_p("2405", "MAWRITH (TANMIYAT)",                  "Review", 1, 560000),
	_p("2406", "AL QASSIM TOWER",                     "Review", 2, 1100000),
	_p("2407", "AL RAKHEES",                          "Review", 3, 380000),
	_p("2408", "SAMEEM-2",                            "Review", 0, 530000),
	_p("2409", "TARAKUM OFFICE (MADAM LAMYA)",        "Review", 1, 670000),
	_p("2410", "ADEL ALMOSA 1",                       "Active", 2, 450000),
	_p("2411", "AL HADAB-2 (AL NAKHIL)",              "Active", 3, 540000),
	_p("2412", "TAMIM AL SALEM 2 COMMERCIAL",         "Active", 0, 780000),
	_p("2413", "AL RUGAIB 2",                         "Active", 1, 400000),
	_p("2414", "AL QASEEM RESIDENCE",                 "Active", 2, 360000),
	_p("2415", "MUSAB AL MAGED",                      "Active", 3, 390000),
	_p("2416", "SBS",                                 "Active", 0, 1650000),
	_p("2417", "SMSA",                                "Active", 1, 920000),
	_p("2418", "NAIF ALMOUSA",                        "Active", 2, 410000),
	_p("2419", "MAKAN MALL",                          "Active", 3, 2400000),
	_p("2420", "AL SALMAN-THALIA",                    "Active", 0, 370000),
	_p("2421", "TAMIM AL SALEM 3 RESIDENTIAL",        "Active", 1, 480000),
	_p("2422", "AL EKRESH",                           "Active", 2, 340000),
	# ── 2025 (2501–2518) ─────────────────────────────────────────────────────
	_p("2501", "AL NAKHEEL MOSQUE",                   "Active", 3, 310000, [("Concept Design", "Open"), ("Client Presentation", "Open")]),
	_p("2502", "AL MUHANNA",                          "Active", 0, 380000),
	_p("2503", "ABDULRAHMAN ALMUSA 2",                "Active", 1, 420000),
	_p("2504", "WABEEL TOWER (AL TUWAJRI)",           "Active", 2, 1300000),
	_p("2505", "YAQEEN",                              "Active", 3, 360000),
	_p("2506", "PRINCE ABDULAZIZ MASHOUR",            "Active", 0, 1900000),
	_p("2507", "ENMA ALRWABI",                        "Active", 1, 440000),
	_p("2508", "AHMED ALTHEYAB REST HOUSES",          "Active", 2, 560000),
	_p("2509", "NMR PAPILON ID",                      "Active", 3, 390000),
	_p("2510", "SAFA TOWER",                          "Active", 0, 1100000),
	_p("2511", "RASAF TOWER",                         "Active", 1, 1050000),
	_p("2512", "AL OBAID TOWER",                      "Planning",2, 980000),
	_p("2513", "ALMUSA ALTAHLIYA",                    "Planning",3, 430000),
	_p("2514", "PRINCE MUQIRIN (MIASEM)",             "Planning",0, 1700000),
	_p("2515", "AL AJLAN 01",                         "Planning",1, 390000),
	_p("2516", "AL AJLAN 02",                         "Planning",2, 390000),
	_p("2517", "MITHAQ HOLDING",                      "Planning",3, 850000),
	_p("2518", "MAJED THEYAB",                        "Planning",0, 420000),
	# ── 2026 (2601–2602) ─────────────────────────────────────────────────────
	_p("2601", "ABDULAZIZ AL THEYAB",                 "Planning",1, 460000, [("Brief Review", "Open")]),
	_p("2602", "AL NAJEM",                            "Planning",2, 380000),
	# ── 2026 Concept Design Brief (CDB-01–CDB-13) ────────────────────────────
	_p("CDB-01", "AL MEREJ",                          "Planning",3, 0),
	_p("CDB-02", "AL RABIAH COMPLEX",                 "Planning",0, 0),
	_p("CDB-03", "AL MOKAYMEN MOSQUE",                "Planning",1, 0),
	_p("CDB-04", "AL JARBAE COMPOUND",                "Planning",2, 0),
	_p("CDB-05", "ABDULAZIZ THEYAB",                  "Planning",3, 0),
	_p("CDB-06", "LETHAM-2",                          "Planning",0, 0),
	_p("CDB-07", "JAREED HOTEL – JEDDAH",        "Planning",1, 0),
	_p("CDB-08", "MASHEED",                           "Planning",2, 0),
	_p("CDB-09", "AL HOWIRINY",                       "Planning",3, 0),
	_p("CDB-10", "AL YASEEN TOWER 1.4",               "Planning",0, 0),
	_p("CDB-11", "NMR-LABAN",                         "Planning",1, 0),
	_p("CDB-12", "NMR-KAFD",                          "Planning",2, 0),
	_p("CDB-13", "MASHAR- HAIL",                      "Planning",3, 0),
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

	year = pj.get("year") or _year_from_code(pj["code"].replace("ATA-", ""))
	meta = _meta()
	doc = frappe.get_doc(
		{
			"doctype": "Project",
			"project_name": pj["project_name"],
			"company": company,
			"naming_series": "PROJ-.####",
			"status": _STAGE_STATUS.get(pj["stage"], "Open"),
			"expected_start_date": f"{year}-01-01",
			"expected_end_date": f"{year}-12-31",
			"estimated_costing": pj.get("cost") or 0,
			"percent_complete": _STAGE_PCT.get(pj["stage"], 20),
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
