"""One-shot (ATA only): apply the client's six-level role hierarchy (Batch C).

    bench --site <site> execute portal_app.scripts.apply_ata_role_hierarchy.execute --kwargs "{'dry_run': 1}"

Review the printed plan, then run again with {'dry_run': 0}. Every action is an
"ensure", so a second run prints only "=" (unchanged) and "!" (skipped) lines.
Output prefix: + add, ~ change, = unchanged, ! skip / report.

Never touches: the PROTECTED logins (their legacy team rows stay as they are), Project,
Project User, Project ToDo, DocShare, Portal Folder Share. A missing user or team is
skipped (never created), except the Coordination team below. The pending departments
get their people recorded but no role (see helper.pending_unit_names).

`plan` lets the tests run the same code against fixture users (same shape as PLAN; a
missing key counts as empty). Department labels resolve to "<label> - <company abbr>".
This file names real staff: treat it as personal data (see scripts/README.md).
"""

import frappe
from frappe.utils import cint, cstr

from portal_app.api import helper

PROTECTED = ("khaled@ata.com.sa", "uat.pm@ata-test.local")

_D = "@ata.com.sa"

PLAN = {
	"departments": [
		{"label": "Concept", "pending": 0},
		{"label": "Technical", "pending": 0},
		{"label": "Supervision", "pending": 0},
		{"label": "Baladia", "pending": 1},
		{"label": "Structural", "pending": 1},
		{"label": "Coordination", "pending": 1},
		{"label": "Material", "pending": 1},
	],
	"existing_departments": ["Human Resources", "Accounts"],
	"new_teams": [{"label": "COORDINATION TEAM", "department": "Coordination"}],
	"team_parents": {
		"LISONE OFFICE 1 - ATA": "Concept",
		"LISONE OFFICE 2 -  GROUP 01 - ATA": "Concept",
		"LISONE OFFICE 2 -  GROUP 02 - ATA": "Concept",
		"MANILA OFFICE 01 - ATA": "Concept",
		"MANILA OFFICE 02 - ATA": "Concept",
		"ATA RIYADH HQ - ATA": "Concept",
		"ATA BIM TEAM - ATA": "Technical",
		"TD - CAIRO - ATA": "Technical",
		"ATA RIYADH SUPERVISION TEAM - ATA": "Supervision",
	},
	"super_admins": ["mohsin" + _D, "it.hq" + _D],
	"keep_super_admins": ["sabu" + _D],
	"designations": [
		{"user": "sabu" + _D, "role": "coordinator", "department": "Concept"},
		{"user": "sabu" + _D, "role": "admin", "department": "Concept"},
		{"user": "m.d" + _D, "role": "admin", "department": "Supervision"},
		{"user": "moe" + _D, "role": "admin", "department": "Human Resources"},
		{"user": "hr.riyadh" + _D, "role": "admin", "department": "Human Resources"},
		{"user": "katia" + _D, "role": "admin", "department": "Human Resources"},
		{"user": "accounts" + _D, "role": "admin", "department": "Accounts"},
		{"user": "alzard" + _D, "role": "admin", "department": "Baladia"},
		{"user": "momen" + _D, "role": "admin", "department": "Structural"},
		{"user": "m.haggag" + _D, "role": "admin", "department": "Coordination"},
		{"user": "samer" + _D, "role": "admin", "department": "Material"},
	],
	"team_managers": [
		{"user": "ana" + _D, "team": "LISONE OFFICE 1 - ATA"},
		{"user": "rita" + _D, "team": "LISONE OFFICE 2 -  GROUP 01 - ATA"},
		{"user": "tiago" + _D, "team": "LISONE OFFICE 2 -  GROUP 02 - ATA"},
		{"user": "gaius" + _D, "team": "MANILA OFFICE 01 - ATA"},
		{"user": "jonathan" + _D, "team": "MANILA OFFICE 02 - ATA"},
		{"user": "rey" + _D, "team": "ATA RIYADH HQ - ATA"},
		{"user": "m.d" + _D, "team": "ATA RIYADH SUPERVISION TEAM - ATA"},
		{"user": "m.haggag" + _D, "team": "COORDINATION TEAM - ATA"},
	],
	# ATA-MASTER-USER-LIST.txt (2026-10-28), everyone marked MEMBER: report only.
	"members": [
		*({"user": u + _D, "team": "ATA RIYADH HQ - ATA"} for u in ("rg", "daromero")),
		{"user": "ahmed.embaby" + _D, "team": "COORDINATION TEAM - ATA"},
		*(
			{"user": u + _D, "team": "LISONE OFFICE 1 - ATA"}
			for u in (
				"bruno", "diogo.brito", "marta", "martina", "Pimenta", "sandro.leite",
				"sara.alexandra", "sergio.c", "t.calais", "beatriz.velosa",
			)
		),
		*(
			{"user": u + _D, "team": "LISONE OFFICE 2 -  GROUP 01 - ATA"}
			for u in (
				"aleksandr.velgan", "antonio", "dalva", "filipa.leite", "filipa.lindo",
				"florbela", "joao.novais", "leonor", "vasco", "vera",
			)
		),
		*(
			{"user": u + _D, "team": "LISONE OFFICE 2 -  GROUP 02 - ATA"}
			for u in ("pedro.c", "rodrigo", "ruben.aires")
		),
		*({"user": u + _D, "team": None} for u in ("luis.peralta", "nuno")),  # standalone, no team
		*({"user": u + _D, "team": "MANILA OFFICE 01 - ATA"} for u in ("don", "arnel", "jjose", "shainna")),
		{"user": "jio" + _D, "team": "MANILA OFFICE 02 - ATA"},
		*(
			{"user": u + _D, "team": "ATA RIYADH SUPERVISION TEAM - ATA"}
			for u in (
				"momen", "a.elhadi", "abdelwahab", "amr.gaber", "ayman.refaat", "hamada.ramada",
				"hatem.salem", "jawdat.shaddad", "kazem.jarkas", "khalid.ali", "mohammed.amal",
				"naveed.ahmed", "osama", "osamaa.elmahdawy", "walid.khamis", "alaa.ahmed",
			)
		),
	],
	"protected": [],
}

_KEYS = (
	"departments",
	"existing_departments",
	"new_teams",
	"team_parents",
	"super_admins",
	"keep_super_admins",
	"designations",
	"team_managers",
	"members",
	"protected",
)


class _Run:
	def __init__(self, plan, dry_run, clear_old_logo):
		plan = PLAN if plan is None else plan
		self.plan = {k: plan.get(k) or ({} if k == "team_parents" else []) for k in _KEYS}
		self.dry_run = bool(cint(dry_run))
		self.clear_old_logo = bool(cint(clear_old_logo))
		self.protected = {u.lower() for u in (*PROTECTED, *self.plan["protected"])}
		self.company = self._company()
		self.abbr = frappe.db.get_value("Company", self.company, "abbr") if self.company else ""
		self.planned = set()  # units a dry run would create (they do not exist yet)
		self.counts = {"+": 0, "~": 0, "=": 0, "!": 0}

	# -- output -----------------------------------------------------------------------
	def say(self, mark, text):
		self.counts[mark] += 1
		print(f"{mark} {text}")

	# -- lookups ----------------------------------------------------------------------
	@staticmethod
	def _company():
		from erpnext import get_default_company

		return get_default_company() or (frappe.get_all("Company", pluck="name", limit=1) or [None])[0]

	def dept_name(self, label):
		return f"{label} - {self.abbr}"

	def exists(self, name):
		return bool(name) and (name in self.planned or frappe.db.exists("Department", name))

	def resolve_team(self, name):
		"""Exact name first, then a whitespace-collapsed, case-insensitive match.
		Returns (name, None) or (None, reason)."""
		if name in self.planned or frappe.db.exists("Department", name):
			return name, None
		want = " ".join(cstr(name).split()).lower()
		hits = [n for n in frappe.get_all("Department", pluck="name") if " ".join(n.split()).lower() == want]
		if len(hits) == 1:
			return hits[0], None
		return None, ("ambiguous" if hits else "not found")

	def resolve_user(self, user):
		"""Case-insensitive. Returns the stored name or None."""
		user = cstr(user).strip()
		if not user:
			return None
		for name in frappe.get_all("User", filters={"name": ["like", user]}, pluck="name"):
			if name.lower() == user.lower():
				return name
		return None

	def person(self, user, what):
		"""The login to write for, or None (missing / protected, reported)."""
		if cstr(user).strip().lower() in self.protected:
			self.say("!", f"SKIP {what}: {user} is protected, never written")
			return None
		found = self.resolve_user(user)
		if not found:
			self.say("!", f"SKIP {what}: user {user} not found")
			return None
		if found.lower() in self.protected:
			self.say("!", f"SKIP {what}: {found} is protected, never written")
			return None
		return found

	def save(self, doc):
		if not self.dry_run:
			doc.save(ignore_permissions=True)

	# -- A. departments ---------------------------------------------------------------
	def departments(self):
		for row in self.plan["departments"]:
			name = self.dept_name(row["label"])
			pending = cint(row.get("pending"))
			if not frappe.db.exists("Department", name):
				self.say("+", f"department {name} (Department{', pending' if pending else ''})")
				if self.dry_run:
					self.planned.add(name)
				if not self.dry_run:
					frappe.get_doc(
						{
							"doctype": "Department",
							"department_name": row["label"],
							"company": self.company,
							"parent_department": "All Departments",
							"is_group": 1,
							"portal_unit": "Department",
							"portal_pending": pending,
						}
					).insert(ignore_permissions=True)
				continue
			doc = frappe.get_doc("Department", name)
			want = {"is_group": 1, "portal_unit": "Department", "portal_pending": pending}
			diff = {k: v for k, v in want.items() if (cint(doc.get(k)) if k != "portal_unit" else doc.get(k)) != v}
			if diff:
				self.say("~", f"department {name}: " + ", ".join(f"{k} -> {v}" for k, v in diff.items()))
				doc.update(diff)
				self.save(doc)
			else:
				self.say("=", f"department {name}")

		for label in self.plan["existing_departments"]:
			name = self.dept_name(label)
			if not frappe.db.exists("Department", name):
				self.say("!", f"SKIP existing department {name}: not found")
				continue
			if frappe.db.get_value("Department", name, "portal_unit") == "Department":
				self.say("=", f"department {name}")
				continue
			self.say("~", f"department {name}: portal_unit -> Department")
			doc = frappe.get_doc("Department", name)
			doc.portal_unit = "Department"
			self.save(doc)

		for row in self.plan["new_teams"]:
			name = self.dept_name(row["label"])
			parent = self.dept_name(row["department"])
			if not self.exists(parent):
				self.say("!", f"SKIP team {name}: department {parent} not found")
				continue
			if not frappe.db.exists("Department", name):
				self.say("+", f"team {name} under {parent}")
				if self.dry_run:
					self.planned.add(name)
				if not self.dry_run:
					frappe.get_doc(
						{
							"doctype": "Department",
							"department_name": row["label"],
							"company": self.company,
							"parent_department": parent,
							"is_group": 0,
							"portal_unit": "Team",
						}
					).insert(ignore_permissions=True)
				continue
			doc = frappe.get_doc("Department", name)
			if doc.parent_department == parent and doc.get("portal_unit") == "Team":
				self.say("=", f"team {name}")
				continue
			self.say("~", f"team {name}: under {parent}, portal_unit Team")
			doc.parent_department = parent
			doc.portal_unit = "Team"
			self.save(doc)

	# -- B. reparent the teams --------------------------------------------------------
	def team_parents(self):
		for team, label in self.plan["team_parents"].items():
			parent = self.dept_name(label)
			found, why = self.resolve_team(team)
			if not found:
				self.say("!", f"SKIP move {team}: team {why}")
				continue
			if not self.exists(parent):
				self.say("!", f"SKIP move {found}: department {parent} not found")
				continue
			if found in self.planned:
				self.say("=", f"team {found} (created under its department)")
				continue
			doc = frappe.get_doc("Department", found)
			if doc.parent_department == parent and doc.get("portal_unit") == "Team":
				self.say("=", f"team {found} under {parent}")
				continue
			self.say("~", f"team {found}: {doc.parent_department} -> {parent}, portal_unit Team")
			doc.parent_department = parent
			doc.portal_unit = "Team"
			self.save(doc)

	# -- C. Super Admins --------------------------------------------------------------
	def super_admins(self):
		for user in self.plan["super_admins"]:
			found = self.person(user, "Super Admin")
			if not found:
				continue
			doc = frappe.get_doc("User", found)
			have = {r.role for r in doc.roles}
			missing = [r for r in (helper.SUPER_ADMIN_ROLE, helper.TEAM_MEMBER_ROLE) if r not in have]
			if not missing:
				self.say("=", f"{found} is a Super Admin")
				continue
			self.say("+", f"{found} roles: {', '.join(missing)}")
			for role in missing:
				doc.append("roles", {"role": role})
			if not self.dry_run:
				doc.flags.ignore_permissions = True
				doc.save()
		for user in self.plan["keep_super_admins"]:
			found = self.resolve_user(user)
			if not found:
				self.say("!", f"SKIP {user}: user not found")
			elif helper.SUPER_ADMIN_ROLE in frappe.get_roles(found):
				self.say("=", f"{found} keeps System Manager")
			else:
				self.say("!", f"{found} does not hold System Manager (not changed)")

	# -- D. department designations ---------------------------------------------------
	def designations(self):
		fields = {"admin": "portal_department_admins", "coordinator": "portal_department_coordinators"}
		for row in self.plan["designations"]:
			role = row.get("role")
			if role not in fields:
				self.say("!", f"SKIP {row.get('user')}: unknown role {role}")
				continue
			unit = self.dept_name(row["department"])
			what = f"{role} of {unit}"
			found = self.person(row["user"], what)
			if not found:
				continue
			if not self.exists(unit):
				self.say("!", f"SKIP {found} {what}: department not found")
				continue
			if unit in self.planned:
				self.say("+", f"{found} {what}")
				continue
			if found not in helper.unit_assigned_users(unit):
				self.say("+", f"{found} assigned to {unit}")
				if not self.dry_run:
					from portal_app.api import teams

					teams._assign_users_to_team(unit, [found])
			doc = frappe.get_doc("Department", unit)
			if found in {r.user for r in doc.get(fields[role]) or []}:
				self.say("=", f"{found} {what}")
				continue
			self.say("+", f"{found} {what}")
			doc.append(fields[role], {"user": found})
			self.save(doc)

	# -- E. Team Managers -------------------------------------------------------------
	def team_managers(self):
		from portal_app.api import teams

		for row in self.plan["team_managers"]:
			found = self.person(row["user"], f"Team Manager of {row['team']}")
			if not found:
				continue
			team, why = self.resolve_team(row["team"])
			if not team:
				self.say("!", f"SKIP {found} Team Manager of {row['team']}: team {why}")
				continue
			if team in self.planned:
				self.say("+", f"{found} Team Manager of {team}")
				continue
			current = frappe.db.get_value("Department", team, "portal_team_lead")
			if current and current != found:
				self.say("!", f"SKIP conflict: {team} is already managed by {current} (wanted {found})")
				continue
			if found not in teams._assigned_by_department([team]).get(team, []):
				self.say("+", f"{found} joins {team}")
				if not self.dry_run:
					teams._assign_users_to_team(team, [found])
			if current == found:
				self.say("=", f"{found} Team Manager of {team}")
				continue
			self.say("+", f"{found} Team Manager of {team}")
			doc = frappe.get_doc("Department", team)
			doc.portal_team_lead = found
			self.save(doc)

	# -- F. members: report only ------------------------------------------------------
	def members(self):
		from portal_app.api import teams

		for row in self.plan["members"]:
			found = self.resolve_user(row["user"])
			if not found:
				self.say("!", f"member {row['user']}: user not found")
				continue
			enabled = frappe.db.get_value("User", found, "enabled")
			team = row.get("team")
			if not team:
				self.say("=" if enabled else "!", f"member {found}: {'enabled' if enabled else 'DISABLED'}, no team in the list")
				continue
			resolved, why = self.resolve_team(team)
			if not resolved or resolved in self.planned:
				self.say("!", f"member {found}: team {team} {why or 'not created yet'}")
				continue
			on_team = found in teams._assigned_by_department([resolved]).get(resolved, [])
			ok = enabled and on_team
			self.say(
				"=" if ok else "!",
				f"member {found}: {'enabled' if enabled else 'DISABLED'}, "
				f"{'on' if on_team else 'NOT on'} {resolved} (report only)",
			)

	# -- G. logo ----------------------------------------------------------------------
	def logo(self):
		settings = "Portal Project Settings"
		if not frappe.db.exists("DocType", settings) or not frappe.get_meta(settings).has_field("company_logo"):
			return
		logo = frappe.db.get_single_value(settings, "company_logo")
		if not logo:
			self.say("=", "Portal Project Settings.company_logo is empty (the bundled ATA logo shows)")
			return
		if not self.clear_old_logo:
			self.say("=", f"Portal Project Settings.company_logo = {logo} (overrides the bundled logo; clear_old_logo=1 clears it)")
			return
		self.say("~", f"clear Portal Project Settings.company_logo (was {logo})")
		if not self.dry_run:
			frappe.db.set_single_value(settings, "company_logo", None)

	def run(self):
		if not frappe.get_meta("Department").has_field("portal_unit"):
			frappe.throw("Run bench migrate first (Department.portal_unit is missing).")
		print(f"{'DRY RUN' if self.dry_run else 'APPLY'} — company {self.company} ({self.abbr})")
		self.departments()
		self.team_parents()
		self.super_admins()
		self.designations()
		self.team_managers()
		self.members()
		self.logo()
		c = self.counts
		print(
			f"Done: {c['+']} added, {c['~']} changed, {c['=']} unchanged, {c['!']} skipped / reported."
			+ (" Nothing was written (dry run)." if self.dry_run else "")
		)


def execute(dry_run=1, clear_old_logo=0, plan=None):
	"""See the module docstring. Defaults to a dry run."""
	_Run(plan, dry_run, clear_old_logo).run()
