"""One-off import of the client's 2026 project register and staff list.

Source files (supplied by ATA, 12 Aug 2026):
  ATA_2026_Project_List.xlsx   — 33 projects: 11 registered (2601-2611) + 22 concept briefs
  ATA MASTER USER LIST .xlsx   — 66 people across 7 groups

Run it, safely, as many times as you like:

    bench --site ata.enfonoerp.com execute portal_app.scripts.import_ata_2026.run           # DRY RUN, writes nothing
    bench --site ata.enfonoerp.com execute portal_app.scripts.import_ata_2026.run --kwargs "{'commit': True}"

Every step is keyed on something stable (project code, user email, department name),
so a second run reports "exists" instead of creating duplicates.

DECISIONS BAKED IN HERE — change them deliberately, not by accident:

* Every user is created with the **Projects User** role only. Nobody is elevated.
  In this app a Projects Manager sees EVERY project in the system, so elevation is
  the client's call, made per-person from the Admin page.
* Users are created **enabled but silent** — send_welcome_email is 0, so importing
  does not email 66 real ATA staff. They cannot log in until someone sends them a
  password reset.
* `Project.project_name` is UNIQUE in ERPNext. Two concept briefs share a name with
  a registered project ("ABDULAZIZ ALTHEYAB", "JAREED HOTEL - JEDDAH"), which would
  hard-fail the insert. They are suffixed "(Concept Brief)" rather than dropped.
  Both pairs are very likely the SAME job before and after it got a number — the
  client's own procedure is "assign number and move folder" — so they should be
  reviewed and merged rather than left as two live projects.
* Concept briefs get a synthetic code `CB-NN` taken from their folder index, since
  they have no project number. Registered projects use their real number.
* Office, team, phase, customer and dates are NOT set: the source files do not
  contain them, and guessing would put wrong data in front of the client.
* Project-to-person access is NOT set either, for the same reason. Until someone is
  added to a project's team, a Projects User sees nothing — that is the app working
  as designed, not a failed import.
"""

import frappe
from frappe import _

ROLE = "Projects User"


PROJECTS = [
 {
  "code": "2601",
  "name": "ABDULAZIZ ALTHEYAB",
  "concept": false,
  "folder": "2601 - ABDULAZIZ ALTHEYAB"
 },
 {
  "code": "2602",
  "name": "AL NAJEM",
  "concept": false,
  "folder": "2602 - AL NAJEM"
 },
 {
  "code": "2603",
  "name": "JAREED HOTEL - JEDDAH",
  "concept": false,
  "folder": "2603 - JAREED HOTEL - JEDDAH"
 },
 {
  "code": "2604",
  "name": "ALHOWIRINY",
  "concept": false,
  "folder": "2604 - ALHOWIRINY"
 },
 {
  "code": "2605",
  "name": "NAIF ALMUSA - 2",
  "concept": false,
  "folder": "2605 - NAIF ALMUSA - 2"
 },
 {
  "code": "2606",
  "name": "NMR KAFD",
  "concept": false,
  "folder": "2606 - NMR KAFD"
 },
 {
  "code": "2607",
  "name": "NMR LABAN",
  "concept": false,
  "folder": "2607 - NMR LABAN"
 },
 {
  "code": "2608",
  "name": "MIRQAH REAL ESTATE",
  "concept": false,
  "folder": "2608 - MIRQAH REAL ESTATE"
 },
 {
  "code": "2609",
  "name": "AL HAMADI COMPLEX",
  "concept": false,
  "folder": "2609 - AL HAMADI COMPLEX"
 },
 {
  "code": "2610",
  "name": "LETHAM 02",
  "concept": false,
  "folder": "2610 - LETHAM 02"
 },
 {
  "code": "2611",
  "name": "JAREED DABBAB - TD",
  "concept": false,
  "folder": "2611 - JAREED DABBAB - TD"
 },
 {
  "code": "CB-01",
  "name": "AL MEREJ",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 01-AL MEREJ"
 },
 {
  "code": "CB-02",
  "name": "AL RABIAH COMPLEX",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 02-AL RABIAH COMPLEX"
 },
 {
  "code": "CB-03",
  "name": "AL MOKAYMEN MOSQUE",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 03-AL MOKAYMEN MOSQUE"
 },
 {
  "code": "CB-04",
  "name": "AL JARBAE COMPOUND",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 04-AL JARBAE COMPOUND"
 },
 {
  "code": "CB-05",
  "name": "ABDULAZIZ ALTHEYAB (Concept Brief)",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 05-ABDULAZIZ ALTHEYAB",
  "renamed": true
 },
 {
  "code": "CB-06",
  "name": "LETHAM-2",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 06-LETHAM-2"
 },
 {
  "code": "CB-07",
  "name": "JAREED HOTEL - JEDDAH (Concept Brief)",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 07-JAREED HOTEL - JEDDAH",
  "renamed": true
 },
 {
  "code": "CB-08",
  "name": "ALNAJEM",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 08-ALNAJEM"
 },
 {
  "code": "CB-09",
  "name": "MASHEED",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 09-MASHEED"
 },
 {
  "code": "CB-10",
  "name": "NAIF ALMUSA -2",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 10-NAIF ALMUSA -2"
 },
 {
  "code": "CB-11",
  "name": "Faisal Resort -02",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 11-Faisal Resort -02"
 },
 {
  "code": "CB-12",
  "name": "ABDURAHMAN ALMUSA",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 12-ABDURAHMAN ALMUSA"
 },
 {
  "code": "CB-13",
  "name": "AL AMARIA FARM LAND",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 13-AL AMARIA FARM LAND"
 },
 {
  "code": "CB-14",
  "name": "OSUS MECCA",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 14-OSUS MECCA"
 },
 {
  "code": "CB-15",
  "name": "OMA TOWERS",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 15-OMA TOWERS"
 },
 {
  "code": "CB-16",
  "name": "AL ARD",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 16-AL ARD"
 },
 {
  "code": "CB-17",
  "name": "HAWTAT SUDAIR HOSPITAL",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 17-HAWTAT SUDAIR HOSPITAL"
 },
 {
  "code": "CB-18",
  "name": "AL RUWAITA 1",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 18-AL RUWAITA 1"
 },
 {
  "code": "CB-19",
  "name": "AL RUWAITA 2",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 19-AL RUWAITA 2"
 },
 {
  "code": "CB-20",
  "name": "AL RUWAITA 3",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 20-AL RUWAITA 3"
 },
 {
  "code": "CB-21",
  "name": "AL RUWAITA 4",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 21-AL RUWAITA 4"
 },
 {
  "code": "CB-22",
  "name": "AL QASSIM MOSQUE",
  "concept": true,
  "folder": "00001 CONCEPT DESIGN BRIEF / 22-AL QASSIM MOSQUE"
 }
]

GROUPS = [
 {
  "department": "ATA RIYADH HQ",
  "office": "RIYADH",
  "members": [
   "mohsin@ata.com.sa",
   "it.hq@ata.com.sa",
   "sabu@ata.com.sa",
   "moe@ata.com.sa",
   "hr.riyadh@ata.com.sa",
   "accounts@ata.com.sa",
   "rey@ata.com.sa",
   "rg@ata.com.sa",
   "daromero@ata.com.sa",
   "alzard@ata.com.sa",
   "momen@ata.com.sa",
   "m.haggag@ata.com.sa",
   "ahmed.embaby@ata.com.sa",
   "samer@ata.com.sa",
   "m.d@ata.com.sa"
  ]
 },
 {
  "department": "LISONE OFFICE 1",
  "office": "LISBON",
  "members": [
   "ana@ata.com.sa",
   "katia@ata.com.sa",
   "bruno@ata.com.sa",
   "diogo.brito@ata.com.sa",
   "marta@ata.com.sa",
   "martina@ata.com.sa",
   "pimenta@ata.com.sa",
   "sandro.leite@ata.com.sa",
   "sara.alexandra@ata.com.sa",
   "sergio.c@ata.com.sa",
   "t.calais@ata.com.sa",
   "beatriz.velosa@ata.com.sa"
  ]
 },
 {
  "department": "LISONE OFFICE 2 -  GROUP 01",
  "office": "LISBON",
  "members": [
   "rita@ata.com.sa",
   "aleksandr.velgan@ata.com.sa",
   "antonio@ata.com.sa",
   "dalva@ata.com.sa",
   "filipa.leite@ata.com.sa",
   "filipa.lindo@ata.com.sa",
   "florbela@ata.com.sa",
   "joao.novais@ata.com.sa",
   "leonor@ata.com.sa",
   "vasco@ata.com.sa",
   "vera@ata.com.sa"
  ]
 },
 {
  "department": "LISONE OFFICE 2 -  GROUP 02",
  "office": "LISBON",
  "members": [
   "tiago@ata.com.sa",
   "pedro.c@ata.com.sa",
   "rodrigo@ata.com.sa",
   "ruben.aires@ata.com.sa",
   "luis.peralta@ata.com.sa",
   "nuno@ata.com.sa"
  ]
 },
 {
  "department": "MANILA OFFICE 01",
  "office": "MANILA",
  "members": [
   "gaius@ata.com.sa",
   "don@ata.com.sa",
   "arnel@ata.com.sa",
   "jjose@ata.com.sa",
   "shainna@ata.com.sa"
  ]
 },
 {
  "department": "MANILA OFFICE 02",
  "office": "MANILA",
  "members": [
   "jonathan@ata.com.sa",
   "jio@ata.com.sa"
  ]
 },
 {
  "department": "ATA RIYADH SUPERVISION TEAM",
  "office": "RIYADH",
  "members": [
   "m.d@ata.com.sa",
   "momen@ata.com.sa",
   "a.elhadi@ata.com.sa",
   "abdelwahab@ata.com.sa",
   "amr.gaber@ata.com.sa",
   "ayman.refaat@ata.com.sa",
   "hamada.ramada@ata.com.sa",
   "hatem.salem@ata.com.sa",
   "jawdat.shaddad@ata.com.sa",
   "kazem.jarkas@ata.com.sa",
   "khalid.ali@ata.com.sa",
   "mohammed.amal@ata.com.sa",
   "naveed.ahmed@ata.com.sa",
   "osama@ata.com.sa",
   "osamaa.elmahdawy@ata.com.sa",
   "walid.khamis@ata.com.sa",
   "alaa.ahmed@ata.com.sa"
  ]
 }
]

USERS = [
 {
  "email": "a.elhadi@ata.com.sa",
  "full_name": "Abdel Moneim Elhadi",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "abdelwahab@ata.com.sa",
  "full_name": "Ahmed Abdelwahab",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "accounts@ata.com.sa",
  "full_name": "MUZAMIL HUSSAIN MOHAMMED",
  "client_roles": [
   "ACCOUNTANT"
  ]
 },
 {
  "email": "ahmed.embaby@ata.com.sa",
  "full_name": "Ahmed Alaa Embaby",
  "client_roles": [
   "COORDINATION TEAM MEMBER"
  ]
 },
 {
  "email": "alaa.ahmed@ata.com.sa",
  "full_name": "Alaa Ibrahim ahmed",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "aleksandr.velgan@ata.com.sa",
  "full_name": "Aleksandr Velgan",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "alzard@ata.com.sa",
  "full_name": "Ahmad Alzard",
  "client_roles": [
   "BALADIA DEPT MANAGER"
  ]
 },
 {
  "email": "amr.gaber@ata.com.sa",
  "full_name": "Amr Gaber",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "ana@ata.com.sa",
  "full_name": "Ana Tendeiro",
  "client_roles": [
   "MANAGER"
  ]
 },
 {
  "email": "antonio@ata.com.sa",
  "full_name": "António Pedro",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "arnel@ata.com.sa",
  "full_name": "Arnel M. Pawa-an",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "ayman.refaat@ata.com.sa",
  "full_name": "Ayman Mahmoud Refaat",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "beatriz.velosa@ata.com.sa",
  "full_name": "Ana Beatriz da Silva Naves Velosa",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "bruno@ata.com.sa",
  "full_name": "Bruno Madaleno",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "dalva@ata.com.sa",
  "full_name": "Dalva Fernandes",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "daromero@ata.com.sa",
  "full_name": "Dexter Romero",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "diogo.brito@ata.com.sa",
  "full_name": "Diogo Brito",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "don@ata.com.sa",
  "full_name": "DON ARDIE",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "filipa.leite@ata.com.sa",
  "full_name": "Filipa Leite",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "filipa.lindo@ata.com.sa",
  "full_name": "Filipa Lindo",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "florbela@ata.com.sa",
  "full_name": "Florbela Antunes",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "gaius@ata.com.sa",
  "full_name": "Gaius Kabigting",
  "client_roles": [
   "MANAGER"
  ]
 },
 {
  "email": "hamada.ramada@ata.com.sa",
  "full_name": "Hamada Ramadan",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "hatem.salem@ata.com.sa",
  "full_name": "Hatem Salem",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "hr.riyadh@ata.com.sa",
  "full_name": "ATA RIYADH HR",
  "client_roles": [
   "HR"
  ]
 },
 {
  "email": "it.hq@ata.com.sa",
  "full_name": "IT HQ",
  "client_roles": [
   "OWNER"
  ]
 },
 {
  "email": "jawdat.shaddad@ata.com.sa",
  "full_name": "Jawdat Shaddad",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "jio@ata.com.sa",
  "full_name": "Jio Marco Araullo",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "jjose@ata.com.sa",
  "full_name": "Jovaany Jose",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "joao.novais@ata.com.sa",
  "full_name": "João Novais",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "jonathan@ata.com.sa",
  "full_name": "Jonathan Sadsad",
  "client_roles": [
   "MANAGER"
  ]
 },
 {
  "email": "katia@ata.com.sa",
  "full_name": "Kátia Tendeiro",
  "client_roles": [
   "HR"
  ]
 },
 {
  "email": "kazem.jarkas@ata.com.sa",
  "full_name": "Kazem Mohammed Jarkas",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "khalid.ali@ata.com.sa",
  "full_name": "Khalid Mohamed Ali El khalid",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "leonor@ata.com.sa",
  "full_name": "Leonor Contreiras",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "luis.peralta@ata.com.sa",
  "full_name": "Luis Peralta",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "m.d@ata.com.sa",
  "full_name": "Mahmoud Daif",
  "client_roles": [
   "MANAGER",
   "SUPERVISION  TEAM MANAGER"
  ]
 },
 {
  "email": "m.haggag@ata.com.sa",
  "full_name": "Mohamed Haggag",
  "client_roles": [
   "COORDINATION TEAM MANAGER"
  ]
 },
 {
  "email": "marta@ata.com.sa",
  "full_name": "Marta Pereira",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "martina@ata.com.sa",
  "full_name": "Martina Darbutaitė",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "moe@ata.com.sa",
  "full_name": "Mohamed Qasem",
  "client_roles": [
   "HR"
  ]
 },
 {
  "email": "mohammed.amal@ata.com.sa",
  "full_name": "Mohammed Amal",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "mohsin@ata.com.sa",
  "full_name": "Abdulmohsin Thiab",
  "client_roles": [
   "OWNER"
  ]
 },
 {
  "email": "momen@ata.com.sa",
  "full_name": "Momen Abdel Razzaq",
  "client_roles": [
   "MEMBER",
   "STRUCTURAL DEPT. MANAGER"
  ]
 },
 {
  "email": "naveed.ahmed@ata.com.sa",
  "full_name": "Naveed Ahmed",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "nuno@ata.com.sa",
  "full_name": "Nuno Calado",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "osama@ata.com.sa",
  "full_name": "Osama Kiwan",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "osamaa.elmahdawy@ata.com.sa",
  "full_name": "Osama Ahmed El Mahdawy",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "pedro.c@ata.com.sa",
  "full_name": "Pedro Cardia",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "pimenta@ata.com.sa",
  "full_name": "Pedro Miguel Pimenta",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "rey@ata.com.sa",
  "full_name": "Reynaldo Pabilona",
  "client_roles": [
   "TEAM MANAGER"
  ]
 },
 {
  "email": "rg@ata.com.sa",
  "full_name": "Roderick Garcia",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "rita@ata.com.sa",
  "full_name": "Rita Campino",
  "client_roles": [
   "MANAGER"
  ]
 },
 {
  "email": "rodrigo@ata.com.sa",
  "full_name": "Rodrigo Silvestre",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "ruben.aires@ata.com.sa",
  "full_name": "Rúben Aires",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "sabu@ata.com.sa",
  "full_name": "Sabu Klbm",
  "client_roles": [
   "OWNER"
  ]
 },
 {
  "email": "samer@ata.com.sa",
  "full_name": "Samer Mohamed Abdullah Hassan",
  "client_roles": [
   "MATERIAL TEAM MANAGER"
  ]
 },
 {
  "email": "sandro.leite@ata.com.sa",
  "full_name": "Sandro Leite",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "sara.alexandra@ata.com.sa",
  "full_name": "Sara Alexandra Albuquerque",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "sergio.c@ata.com.sa",
  "full_name": "Sergio Calais",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "shainna@ata.com.sa",
  "full_name": "Shainna Pilapil",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "t.calais@ata.com.sa",
  "full_name": "Tiago Calais",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "tiago@ata.com.sa",
  "full_name": "Tiago Guerreiro",
  "client_roles": [
   "MANAGER"
  ]
 },
 {
  "email": "vasco@ata.com.sa",
  "full_name": "Vasco Antunes",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "vera@ata.com.sa",
  "full_name": "Vera Nunes",
  "client_roles": [
   "MEMBER"
  ]
 },
 {
  "email": "walid.khamis@ata.com.sa",
  "full_name": "Walid Mohamed Khamis",
  "client_roles": [
   "MEMBER"
  ]
 }
]


def _split_name(full_name):
	parts = (full_name or "").strip().split(None, 1)
	if not parts:
		return "Unknown", ""
	return parts[0], (parts[1] if len(parts) > 1 else "")


def run(commit=False):
	"""Import departments, users and projects. Dry run unless commit=True."""
	commit = bool(commit)
	log = []
	stats = {"dept_created": 0, "dept_exists": 0, "user_created": 0, "user_exists": 0,
	         "assign_created": 0, "assign_exists": 0, "proj_created": 0, "proj_exists": 0}

	company_abbr = frappe.db.get_value("Company", {"name": "ATA"}, "abbr") or \
		frappe.db.get_value("Company", {}, "abbr")

	# ── 1. Departments (the portal's "Teams") ───────────────────────────────
	dept_names = {}
	for g in GROUPS:
		dn = g["department"]
		existing = frappe.db.get_value("Department", {"department_name": dn}, "name")
		if existing:
			dept_names[dn] = existing
			stats["dept_exists"] += 1
			# portal_office is what puts a department on the Teams page at all.
			if g["office"] and frappe.db.get_value("Department", existing, "portal_office") != g["office"]:
				log.append(f"dept  UPDATE office  {dn} -> {g['office']}")
				if commit:
					frappe.db.set_value("Department", existing, "portal_office", g["office"])
			continue
		log.append(f"dept  CREATE  {dn}  office={g['office']}")
		stats["dept_created"] += 1
		if commit:
			doc = frappe.get_doc({
				"doctype": "Department",
				"department_name": dn,
				"parent_department": "All Departments",
				"company": "ATA",
				"is_group": 0,
				"portal_office": g["office"],
			})
			doc.insert(ignore_permissions=True)
			dept_names[dn] = doc.name
		else:
			dept_names[dn] = f"{dn} - {company_abbr}"

	# ── 2. Users ────────────────────────────────────────────────────────────
	for u in USERS:
		if frappe.db.exists("User", u["email"]):
			stats["user_exists"] += 1
			continue
		first, last = _split_name(u["full_name"])
		log.append(f"user  CREATE  {u['email']:<34} {u['full_name']}  [{', '.join(u['client_roles'])}]")
		stats["user_created"] += 1
		if commit:
			doc = frappe.get_doc({
				"doctype": "User",
				"email": u["email"],
				"first_name": first,
				"last_name": last,
				"enabled": 1,
				# Deliberate: importing must not email 66 real staff.
				"send_welcome_email": 0,
				"user_type": "System User",
			})
			doc.append("roles", {"role": ROLE})
			doc.insert(ignore_permissions=True)

	# ── 3. Team membership = Frappe "Assign To" (ToDo) on the Department ────
	# This is what teams.py reads; Employee.department is NOT used by the portal.
	from frappe.desk.form.assign_to import add as assign_add

	for g in GROUPS:
		dept = dept_names.get(g["department"])
		if not dept:
			continue
		for email in g["members"]:
			if commit and not frappe.db.exists("User", email):
				continue
			already = frappe.db.exists("ToDo", {
				"reference_type": "Department", "reference_name": dept,
				"allocated_to": email, "status": ["not in", ("Cancelled", "Closed")],
			})
			if already:
				stats["assign_exists"] += 1
				continue
			stats["assign_created"] += 1
			log.append(f"team  ASSIGN  {email:<34} -> {g['department']}")
			if commit:
				try:
					assign_add({"doctype": "Department", "name": dept,
					            "assign_to": [email], "description": f"Portal team: {g['department']}"},
					           ignore_permissions=True)
				except Exception:
					frappe.log_error(frappe.get_traceback(), f"ATA import: assign {email}")

	# ── 4. Projects ─────────────────────────────────────────────────────────
	for p in PROJECTS:
		existing = frappe.db.get_value("Project", {"portal_project_code": p["code"]}, "name")
		if existing:
			stats["proj_exists"] += 1
			continue
		stats["proj_created"] += 1
		log.append(f"proj  CREATE  {p['code']:<8} {p['name']}")
		if commit:
			doc = frappe.get_doc({
				"doctype": "Project",
				"project_name": p["name"],
				"portal_project_code": p["code"],
				"company": "ATA",
				"status": "Open",
				"portal_kanban_stage": "Planning",
				# office / team / phase / customer / dates deliberately unset — not in source
				"notes": f"Imported from the client's 2026 register. Source folder: {p['folder']}",
			})
			doc.insert(ignore_permissions=True)

	if commit:
		frappe.db.commit()

	print("\n".join(log) if log else "nothing to do — everything already present")
	print()
	print("DRY RUN — nothing written. Re-run with commit=True to apply." if not commit else "COMMITTED.")
	print(f"  departments  created {stats['dept_created']:>3}  existing {stats['dept_exists']:>3}")
	print(f"  users        created {stats['user_created']:>3}  existing {stats['user_exists']:>3}")
	print(f"  assignments  created {stats['assign_created']:>3}  existing {stats['assign_exists']:>3}")
	print(f"  projects     created {stats['proj_created']:>3}  existing {stats['proj_exists']:>3}")
	return stats
