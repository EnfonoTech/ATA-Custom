"""Customer list batch B: R1 submission types + submission folders, R7 client transmittal
page (backend reads), R5 / R7 frontend contract (static checks).

Written before the implementation (TDD). Spec: .pipeline/spec.md, Test Plan 1-21.

Run with (on a development site, never production):
    bench --site <site> run-tests --module portal_app.tests.test_batch_b
"""

import importlib
import inspect
import os
import re
from unittest import mock

import frappe
from frappe.utils import today
from frappe.utils.file_manager import save_file

from portal_app import install
from portal_app.api import files, helper, portal_admin
from portal_app.tests.test_portal_roles import PortalRoleTestBase, _customer, _project, _user

TYPE_DT = "Portal Submission Type"
CONCEPT = "Concept Submittal"
TECHNICAL = "Technical Submittal"


def _submissions():
	"""Imported lazily so a missing module fails each test, not the whole file."""
	return importlib.import_module("portal_app.api.submissions")


def _seed_patch():
	return importlib.import_module("portal_app.patches.seed_portal_submission_types")


class BatchBBase(PortalRoleTestBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# Tolerant here so each test reports its own failure before the implementation
		# lands; test_default_types_are_seeded_once asserts the seed itself.
		seed = getattr(install, "seed_default_submission_types", None)
		if seed:
			seed()
		cls.cust2 = _customer("Batch B Customer Two")
		cls.client2 = _user("client2", (helper.PORTAL_CUSTOMER_ROLE,), "Website User")
		frappe.get_doc(
			{"doctype": helper.PORTAL_USER_CUSTOMER, "user": cls.client2, "customer": cls.cust2}
		).insert(ignore_permissions=True)
		cls.pf = _project("Batch B PF", customer=cls.cust2)
		# A login with no PORTAL_ROLES, no customer role and no Project User row: not a portal user.
		cls.non_portal = _user("batchbnonportal", (), "Website User")
		cls.root_pa = files.ensure_project_folders(cls.pa)["project_root"]
		files._ensure_client_folders(cls.pa)
		cls._counter = 0

	def setUp(self):
		super().setUp()
		files._forget_client_folders()

	# -- helpers ---------------------------------------------------------------------
	@classmethod
	def _unique(cls, prefix="batch-b"):
		cls._counter += 1
		return f"{prefix} {cls._counter} {frappe.generate_hash(length=6)}"

	def _fresh_project(self, label=None):
		"""A project of cls.cust, led by m1, with its folder tree and client folders."""
		frappe.set_user("Administrator")
		name = _project(label or self._unique("Batch B fresh"), [self.m1], lead=self.m1, customer=self.cust)
		files.ensure_project_folders(name)
		files._ensure_client_folders(name)
		files._forget_client_folders()
		return name

	@staticmethod
	def _fresh_name(file_name):
		"""`file_name` with a per-run suffix before the extension, so a file left on disk by an
		earlier run (only the DB rolls back) never makes save_file rename the source."""
		stem, ext = os.path.splitext(file_name)
		return f"{stem} {frappe.generate_hash(length=6)}{ext}"

	def _src(self, project, file_name, content=None, folder=None):
		"""A source file in the project (root by default), saved as Administrator."""
		user = frappe.session.user
		frappe.set_user("Administrator")
		folder = folder or files.ensure_project_folders(project)["project_root"]
		if content is None:
			content = ("content of " + file_name + " " + frappe.generate_hash(length=12)).encode()
		doc = save_file(file_name, content, "Project", project, folder=folder, is_private=1)
		frappe.set_user(user)
		return doc

	def _incoming(self, project):
		files._forget_client_folders()
		return files._client_incoming_path(project)

	def _below(self, folder):
		"""Every File (folder or file) name at any depth below `folder`."""
		return set(
			frappe.get_all("File", filters={"name": ["like", folder + "/%"]}, pluck="name")
		) | set(frappe.get_all("File", filters={"folder": ["like", folder + "%"]}, pluck="name"))

	def _children(self, folder):
		return frappe.get_all(
			"File", filters={"folder": folder}, fields=["name", "file_name", "is_folder", "folder"]
		)

	def assertRefused(self, fn, *args, **kwargs):
		with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
			fn(*args, **kwargs)


# =====================================================================================
# R1 — the Portal Submission Type master
# =====================================================================================
class TestSubmissionTypes(BatchBBase):
	def _cleanup_type(self, name):
		self.addCleanup(
			lambda: frappe.db.exists(TYPE_DT, name)
			and frappe.delete_doc(TYPE_DT, name, force=1, ignore_permissions=True)
		)

	def test_doctype_shape(self):
		meta = frappe.get_meta(TYPE_DT)
		self.assertEqual(meta.module, "Project Portal")
		self.assertEqual(meta.autoname, "field:type_name")
		tn = meta.get_field("type_name")
		self.assertEqual(tn.fieldtype, "Data")
		self.assertTrue(tn.reqd)
		self.assertTrue(tn.unique)
		en = meta.get_field("enabled")
		self.assertEqual(en.fieldtype, "Check")
		self.assertEqual(str(en.default), "1")

	def test_default_types_are_seeded_once(self):
		for t in (CONCEPT, TECHNICAL):
			self.assertTrue(frappe.db.exists(TYPE_DT, t))
			self.assertEqual(frappe.db.get_value(TYPE_DT, t, "enabled"), 1)
		self.assertEqual(install.DEFAULT_SUBMISSION_TYPES, [CONCEPT, TECHNICAL])
		before = frappe.db.count(TYPE_DT)
		install.seed_default_submission_types()
		install.seed_default_submission_types()
		_seed_patch().execute()
		_seed_patch().execute()
		self.assertEqual(frappe.db.count(TYPE_DT), before)

	def test_seed_never_edits_an_existing_row(self):
		frappe.db.set_value(TYPE_DT, TECHNICAL, "enabled", 0)
		self.addCleanup(frappe.db.set_value, TYPE_DT, TECHNICAL, "enabled", 1)
		install.seed_default_submission_types()
		_seed_patch().execute()
		self.assertEqual(frappe.db.get_value(TYPE_DT, TECHNICAL, "enabled"), 0)

	def test_patch_is_registered_post_model_sync(self):
		path = os.path.join(frappe.get_app_path("portal_app"), "patches.txt")
		with open(path) as fh:
			text = fh.read()
		post = text.split("[post_model_sync]", 1)[1]
		self.assertIn("portal_app.patches.seed_portal_submission_types", post)

	def test_seed_runs_from_after_install_not_after_migrate(self):
		with mock.patch.object(install, "seed_default_submission_types") as seed:
			with mock.patch.multiple(
				install,
				ensure_department_portal_custom_fields=mock.DEFAULT,
				ensure_project_portal_custom_fields=mock.DEFAULT,
				ensure_portal_customer_access=mock.DEFAULT,
				ensure_portal_roles=mock.DEFAULT,
				lift_project_attachment_limit=mock.DEFAULT,
				ensure_daily_task_custom_fields=mock.DEFAULT,
				ensure_portal_file_type_field=mock.DEFAULT,
				seed_default_portal_file_types=mock.DEFAULT,
			):
				install.after_install()
				self.assertEqual(seed.call_count, 1)
		# after_migrate is not run here (its custom-field DDL would commit); read its source
		self.assertNotIn("seed_default_submission_types", inspect.getsource(install.after_migrate))

	def _insert(self, type_name):
		return frappe.get_doc({"doctype": TYPE_DT, "type_name": type_name}).insert(ignore_permissions=True)

	def test_type_names_are_validated(self):
		for bad in ("a/b", "x:y", "q?r", 'say "hi"', "back\\slash", "pipe|d", "..", "", "   ", "A" * 61):
			with self.assertRaises(frappe.ValidationError, msg=repr(bad)):
				self._insert(bad)
				self._cleanup_type(bad)
		with self.assertRaises(frappe.ValidationError):
			self._insert("concept submittal")  # case-insensitive duplicate of a default

	def test_type_name_is_trimmed_and_spaces_collapsed(self):
		doc = self._insert("  Batch B   Spaced Type  ")
		self._cleanup_type(doc.name)
		self.assertEqual(doc.type_name, "Batch B Spaced Type")
		self.assertEqual(doc.name, "Batch B Spaced Type")

	def test_only_admin_tier_manages_types(self):
		sub = _submissions()
		for i, user in enumerate((self.super_admin, self.admin)):
			name = f"Meeting Documents {i}"
			self._cleanup_type(name)
			frappe.set_user(user)
			row = sub.add_submission_type(name)
			self.assertEqual(row["type_name"] if isinstance(row, dict) else row.type_name, name)
			sub.set_submission_type_enabled(name, 0)
			self.assertEqual(frappe.db.get_value(TYPE_DT, name, "enabled"), 0)
			sub.set_submission_type_enabled(name, 1)
			self.assertEqual(frappe.db.get_value(TYPE_DT, name, "enabled"), 1)

		for user in (self.lead, self.m1, self.client):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError, msg=user):
				sub.add_submission_type("Batch B Refused Type")
			with self.assertRaises(frappe.PermissionError, msg=user):
				sub.set_submission_type_enabled(CONCEPT, 0)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists(TYPE_DT, "Batch B Refused Type"))
		self.assertEqual(frappe.db.get_value(TYPE_DT, CONCEPT, "enabled"), 1)

	def test_add_duplicate_enabled_type_is_refused(self):
		sub = _submissions()
		frappe.set_user(self.super_admin)
		with self.assertRaises(frappe.ValidationError):
			sub.add_submission_type("CONCEPT SUBMITTAL")

	def test_set_enabled_on_unknown_type_is_refused(self):
		sub = _submissions()
		frappe.set_user(self.super_admin)
		with self.assertRaises(frappe.ValidationError):
			sub.set_submission_type_enabled("Batch B no such type", 1)

	def test_disabled_types_are_hidden_and_refused(self):
		sub = _submissions()
		name = "Batch B Disabled Type"
		self._cleanup_type(name)
		frappe.set_user(self.super_admin)
		sub.add_submission_type(name)
		sub.set_submission_type_enabled(name, 0)

		def listed(**kw):
			return {r["type_name"] for r in sub.list_submission_types(**kw)}

		frappe.set_user(self.m1)
		self.assertNotIn(name, listed())
		self.assertIn(CONCEPT, listed())
		self.assertNotIn(name, listed(include_disabled=1))  # m1 may not see disabled ones

		frappe.set_user(self.admin)
		self.assertIn(name, listed(include_disabled=1))
		self.assertNotIn(name, listed())

		rows = sub.list_submission_types()
		self.assertEqual([r["type_name"] for r in rows], sorted(r["type_name"] for r in rows))
		self.assertTrue(all({"name", "type_name", "enabled"} <= set(r) for r in rows))

		project = self._fresh_project()
		src = self._src(project, "disabled-type.txt")
		incoming = self._incoming(project)
		before = self._below(incoming)
		frappe.set_user(self.m1)
		with self.assertRaises(frappe.ValidationError):
			sub.submit_to_client(project, name, file_names=[src.name])
		with self.assertRaises(frappe.ValidationError):
			sub.submit_to_client(project, "Batch B no such type", file_names=[src.name])
		self.assertEqual(self._below(incoming), before)

		# re-adding the disabled name (any case) re-enables it rather than failing
		frappe.set_user(self.super_admin)
		sub.add_submission_type(name.upper())
		self.assertEqual(frappe.db.get_value(TYPE_DT, name, "enabled"), 1)
		self.assertEqual(frappe.db.count(TYPE_DT, {"type_name": ["like", name]}), 1)

	def test_client_cannot_list_types(self):
		sub = _submissions()
		frappe.set_user(self.client)
		with self.assertRaises(frappe.PermissionError):
			sub.list_submission_types()
		frappe.set_user(self.non_portal)  # not a portal user at all
		with self.assertRaises(frappe.PermissionError):
			sub.list_submission_types()

	def test_admin_capability_flag(self):
		for user, expected in (
			(self.super_admin, True),
			(self.admin, True),
			(self.lead, False),
			(self.m1, False),
			(self.client, False),
		):
			frappe.set_user(user)
			caps = portal_admin.get_portal_admin_capabilities()
			self.assertIs(bool(caps["can_manage_submission_types"]), expected, msg=user)

	def test_write_endpoints_are_post_only(self):
		sub = _submissions()
		for fn in (sub.submit_to_client, sub.add_submission_type, sub.set_submission_type_enabled):
			self.assertEqual(list(frappe.allowed_http_methods_for_whitelisted_func[fn]), ["POST"], fn.__name__)
		for fn in (sub.list_submission_types, sub.list_client_projects, sub.list_client_transmittals):
			self.assertIn(fn, frappe.whitelisted)
			self.assertIn("GET", frappe.allowed_http_methods_for_whitelisted_func[fn])
			self.assertNotIn(fn, frappe.guest_methods)


# =====================================================================================
# R1 — name helpers and the numbering rule (pure / near-pure functions)
# =====================================================================================
class TestNamingHelpers(BatchBBase):
	ILLEGAL = re.compile(r'[\/\\:*?"<>|\x00-\x1f]')

	def test_illegal_pattern_constant(self):
		for ch in '/\\:*?"<>|\x00\x1f':
			self.assertTrue(files.SUBMISSION_NAME_ILLEGAL.search(ch), repr(ch))
		self.assertFalse(files.SUBMISSION_NAME_ILLEGAL.search("Layout plan rev01 - A_1"))

	def test_clean_name_part(self):
		out = files._clean_name_part('  a/b\\c:d*e?f"g<h>i|j  ')
		self.assertFalse(self.ILLEGAL.search(out))
		self.assertNotIn("  ", out)
		self.assertEqual(out, out.strip())
		self.assertEqual(out.replace(" ", ""), "abcdefghij")

		trav = files._clean_name_part("../../etc")
		self.assertNotIn("/", trav)
		self.assertNotIn("..", trav)
		self.assertIn("etc", trav)

		self.assertEqual(files._clean_name_part("...dots at ends..."), "dots at ends")
		self.assertEqual(files._clean_name_part("tab\tand\nnewline"), "tab and newline")
		self.assertEqual(files._clean_name_part('/\\:*?"<>|'), "")
		self.assertEqual(files._clean_name_part(None), "")
		self.assertEqual(files._clean_name_part(""), "")

		long = files._clean_name_part("x" * 300)
		self.assertEqual(len(long), 100)
		self.assertLessEqual(len(files._clean_name_part("y " * 200, max_len=20)), 20)
		self.assertEqual(files._clean_name_part("abc" + " " * 30 + "def", max_len=5), "abc")  # re-stripped after cut

	def test_submission_stem(self):
		stem = _submissions()._submission_stem
		self.assertEqual(stem(1, "2026-10-28", CONCEPT, ""), "01_2026-10-28_Concept Submittal")
		self.assertEqual(stem(1, "2026-10-28", CONCEPT, None), "01_2026-10-28_Concept Submittal")
		self.assertEqual(
			stem(1, "2026-10-28", CONCEPT, "Layout plan rev01"),
			"01_2026-10-28_Concept Submittal - Layout plan rev01",
		)
		self.assertEqual(stem(12, "2026-10-28", TECHNICAL, ""), "12_2026-10-28_Technical Submittal")
		self.assertTrue(stem(100, "2026-10-28", CONCEPT, "").startswith("100_2026-10-28_"))

		long = stem(7, "2026-10-28", "T" * 60, "d" * 100)
		self.assertLessEqual(len(long), 120)
		self.assertTrue(long.startswith("07_2026-10-28_" + "T" * 60 + " - d"))  # the description is trimmed, not the type

	def test_next_submission_number_rule(self):
		project = self._fresh_project()
		root = files.ensure_project_folders(project)["project_root"]
		frappe.set_user("Administrator")

		empty = files._ensure_folder(root, "Batch B numbering empty")
		self.assertEqual(files._next_submission_number(empty), 1)

		mixed = files._ensure_folder(root, "Batch B numbering mixed")
		files._ensure_folder(mixed, "first")
		files._ensure_folder(mixed, "second")
		self._src(project, "loose.txt", folder=mixed)
		self.assertEqual(files._next_submission_number(mixed), 4)  # 3 children + 1

		gap = files._ensure_folder(root, "Batch B numbering gap")
		files._ensure_folder(gap, "07_x")
		self.assertEqual(files._next_submission_number(gap), 8)  # highest NN wins over the count

		legacy = files._ensure_folder(root, "Batch B numbering legacy")
		self._src(project, "03_2026-01-01_old.txt", folder=legacy)
		self._src(project, "notes.txt", folder=legacy)
		files._ensure_folder(legacy, "Drafts 99")  # trailing digits are not an NN
		self.assertEqual(files._next_submission_number(legacy), 4)  # count 3 wins over highest 3

		# grandchildren never count: direct children only
		deep = files._ensure_folder(root, "Batch B numbering deep")
		inner = files._ensure_folder(deep, "05_inner")
		files._ensure_folder(inner, "40_grandchild")
		self.assertEqual(files._next_submission_number(deep), 6)

	def test_lock_folder_uses_select_for_update(self):
		incoming = self._incoming(self.pa)
		with mock.patch.object(frappe.local.db, "get_value", wraps=frappe.local.db.get_value) as gv:
			files._lock_folder(incoming)
		self.assertTrue(
			any(
				c.args[:2] == ("File", incoming) and c.kwargs.get("for_update")
				for c in gv.call_args_list
			),
			gv.call_args_list,
		)


# =====================================================================================
# R1 — submit_to_client
# =====================================================================================
class TestSubmitToClient(BatchBBase):
	def _submit(self, project, user=None, **kw):
		frappe.set_user(user or self.m1)
		kw.setdefault("submission_type", CONCEPT)
		return _submissions().submit_to_client(project, **kw)

	def test_submit_files_creates_one_named_folder(self):
		project = self._fresh_project()
		a = self._src(project, self._fresh_name("Plan A.TXT"))
		b = self._src(project, "plan-b.dwg")
		# a third file with content identical to b -> save_file's content-hash reuse path
		self._src(project, "plan-b-twin.dwg", content=b.get_content())
		incoming = self._incoming(project)

		res = self._submit(project, description="Layout plan rev01", file_names=frappe.as_json([a.name, b.name]))
		stem = f"01_{today()}_Concept Submittal - Layout plan rev01"
		self.assertEqual(res["folder_name"], stem)
		self.assertEqual(res["number"], 1)
		self.assertEqual(res["folder"], incoming + "/" + stem)

		frappe.set_user("Administrator")
		folder = frappe.get_doc("File", res["folder"])
		self.assertEqual(folder.is_folder, 1)
		self.assertEqual(folder.folder, incoming)
		# exactly one new entry in Incoming: the submission folder
		self.assertEqual([c.name for c in self._children(incoming)], [res["folder"]])

		copies = {c.file_name: c for c in self._children(res["folder"])}
		self.assertEqual(set(copies), {stem + ".TXT", stem + "-2.dwg"})  # picked order, original ext case
		self.assertEqual([f["file_name"] for f in res["files"]], [stem + ".TXT", stem + "-2.dwg"])
		for c in copies.values():
			doc = frappe.get_doc("File", c.name)
			self.assertEqual(doc.is_private, 1)
			self.assertEqual(doc.attached_to_doctype, "Project")
			self.assertEqual(doc.attached_to_name, project)
			self.assertEqual(doc.folder, res["folder"])
		self.assertEqual(frappe.get_doc("File", copies[stem + "-2.dwg"].name).get_content(), b.get_content())
		# the sources are untouched
		self.assertEqual(frappe.db.get_value("File", a.name, "file_name"), a.file_name)
		self.assertEqual(frappe.db.get_value("File", b.name, "folder"), files.ensure_project_folders(project)["project_root"])

		frappe.set_user(self.m1)
		listing = {f["name"]: f for f in files.list_project_files(project)["files"]}
		for c in copies.values():
			self.assertEqual(listing[c.name]["client_direction"], "incoming")

	def test_submit_without_description_and_file_list_as_python_list(self):
		project = self._fresh_project()
		a = self._src(project, "single.txt")
		res = self._submit(project, submission_type=TECHNICAL, file_names=[a.name, a.name])  # duplicate dropped
		stem = f"01_{today()}_Technical Submittal"
		self.assertEqual(res["folder_name"], stem)
		frappe.set_user("Administrator")
		self.assertEqual([c.file_name for c in self._children(res["folder"])], [stem + ".txt"])

	def test_numbers_increase_per_folder(self):
		project = self._fresh_project()
		a = self._src(project, self._fresh_name("n1.txt"))
		first = self._submit(project, file_names=[a.name])
		second = self._submit(project, submission_type=TECHNICAL, file_names=[a.name])
		self.assertEqual(second["number"], first["number"] + 1)
		self.assertTrue(second["folder_name"].startswith(f"{first['number'] + 1:02d}_{today()}_Technical Submittal"))

		frappe.set_user(self.m1)
		legacy = files.submit_to_client_submittal(a.name, project)
		self.assertEqual(legacy["sl_no"], first["number"] + 2)
		self.assertEqual(legacy["file_name"], f"{first['number'] + 2:02d}_{today()}_{a.file_name}")

		# another project's Incoming has its own sequence
		other = self._fresh_project()
		o = self._src(other, "other.txt")
		self.assertEqual(self._submit(other, file_names=[o.name])["number"], 1)

	def test_deleted_submission_number_is_not_reused(self):
		project = self._fresh_project()
		a = self._src(project, "del.txt")
		self._submit(project, file_names=[a.name])
		second = self._submit(project, file_names=[a.name])
		self._submit(project, file_names=[a.name])
		frappe.set_user("Administrator")
		for c in self._children(second["folder"]):
			frappe.delete_doc("File", c.name, force=1, ignore_permissions=True)
		frappe.delete_doc("File", second["folder"], force=1, ignore_permissions=True)
		self.assertEqual(self._submit(project, file_names=[a.name])["number"], 4)

	def test_legacy_endpoint_shares_lock_and_counter(self):
		project = self._fresh_project()
		a = self._src(project, "legacy.txt")
		incoming = self._incoming(project)
		frappe.set_user(self.m1)
		with mock.patch.object(files, "_lock_folder", wraps=files._lock_folder) as lock, mock.patch.object(
			files, "_next_submission_number", wraps=files._next_submission_number
		) as nxt:
			res = files.submit_to_client_submittal(a.name, project)
		lock.assert_called_with(incoming)
		nxt.assert_called_with(incoming)
		self.assertEqual(res["sl_no"], 1)

	def test_lock_is_taken_before_counting(self):
		project = self._fresh_project()
		a = self._src(project, "order.txt")
		incoming = self._incoming(project)
		calls = []
		real_lock, real_next = files._lock_folder, files._next_submission_number

		def lock(name):
			calls.append(("lock", name))
			return real_lock(name)

		def nxt(name):
			calls.append(("count", name))
			return real_next(name)

		with mock.patch.object(files, "_lock_folder", side_effect=lock), mock.patch.object(
			files, "_next_submission_number", side_effect=nxt
		):
			self._submit(project, file_names=[a.name])
		self.assertIn(("lock", incoming), calls)
		self.assertIn(("count", incoming), calls)
		self.assertLess(calls.index(("lock", incoming)), calls.index(("count", incoming)))

	def test_submit_folder_keeps_structure_and_names(self):
		project = self._fresh_project()
		frappe.set_user("Administrator")
		root = files.ensure_project_folders(project)["project_root"]
		drawings = files._ensure_folder(root, "02-DRAWINGS")
		src_folder = files._ensure_folder(drawings, "Batch B Set")
		sub = files._ensure_folder(src_folder, "Sub")
		x = self._src(project, self._fresh_name("x.txt"), folder=src_folder)
		y = self._src(project, self._fresh_name("file2.dwg"), folder=sub)
		outside = self._src(project, "not-in-set.txt", folder=drawings)

		res = self._submit(project, submission_type=TECHNICAL, folder_path=src_folder)
		stem = f"01_{today()}_Technical Submittal"
		self.assertEqual(res["folder_name"], stem)
		frappe.set_user("Administrator")
		top = {c.file_name: c for c in self._children(res["folder"])}
		self.assertEqual(set(top), {x.file_name, "Sub"})
		self.assertEqual(top["Sub"].is_folder, 1)
		nested = self._children(res["folder"] + "/Sub")
		self.assertEqual([c.file_name for c in nested], [y.file_name])
		self.assertEqual(
			frappe.get_doc("File", nested[0].name).get_content(), frappe.get_doc("File", y.name).get_content()
		)
		names = {f["file_name"] for f in res["files"]}
		self.assertEqual(names, {x.file_name, y.file_name})
		self.assertNotIn(outside.file_name, names)
		# source folder untouched
		self.assertEqual(frappe.db.get_value("File", x.name, "folder"), src_folder)

	def test_folder_with_lookalike_sibling_prefix_is_not_merged(self):
		# LIKE 'Set_A/%' also matches 'SetXA/...'; the Python _in_folder check must drop it.
		project = self._fresh_project()
		frappe.set_user("Administrator")
		root = files.ensure_project_folders(project)["project_root"]
		a = files._ensure_folder(root, "Set_A")
		b = files._ensure_folder(root, "SetXA")
		mine = self._src(project, self._fresh_name("mine.txt"), folder=a)
		self._src(project, self._fresh_name("theirs.txt"), folder=b)
		res = self._submit(project, folder_path=a)
		self.assertEqual({f["file_name"] for f in res["files"]}, {mine.file_name})

	def test_folder_copy_keeps_lookalike_subfolders_apart(self):
		# _ensure_folder would merge "Sub - A" and "sub-A"; the copy must keep both (D2).
		project = self._fresh_project()
		frappe.set_user("Administrator")
		root = files.ensure_project_folders(project)["project_root"]
		src_folder = files._ensure_folder(root, self._unique("Batch B lookalike set"))
		subs = [
			frappe.get_doc({"doctype": "File", "file_name": label, "folder": src_folder, "is_folder": 1})
			.insert(ignore_permissions=True)
			.name
			for label in ("Sub - A", "sub-A")
		]
		for s in subs:
			self._src(project, self._fresh_name("inner.txt"), folder=s)
		res = self._submit(project, folder_path=src_folder)
		frappe.set_user("Administrator")
		top = sorted(c.file_name for c in self._children(res["folder"]) if c.is_folder)
		self.assertEqual(top, sorted(["Sub - A", "sub-A"]))
		for label in ("Sub - A", "sub-A"):
			self.assertEqual(len(self._children(res["folder"] + "/" + label)), 1)

	def test_submit_refusals_create_nothing(self):
		project = self.pa
		frappe.set_user("Administrator")
		files._ensure_client_folders(project)
		incoming = self._incoming(project)
		client_root = files._client_folder_path(project)
		mine = self._src(project, "refusal-src.txt")
		folder_in_pa = files._ensure_folder(self.root_pa, "Batch B refusal folder")
		self._src(project, "refusal-in-folder.txt", folder=folder_in_pa)
		empty_folder = files._ensure_folder(self.root_pa, "Batch B empty folder")

		contracts = files._ensure_folder(files._ensure_folder("Home", "Contracts"), project)
		contract = self._src(project, "contract.txt", folder=contracts)

		pb_root = files.ensure_project_folders(self.pb)["project_root"]
		pb_folder = files._ensure_folder(pb_root, "Batch B pb folder")
		pb_file = self._src(self.pb, "pb-file.txt", folder=pb_folder)
		in_incoming = self._src(project, "already-incoming.txt", folder=incoming)
		before = self._below(client_root)
		sub = _submissions()

		cases = [
			# (user, kwargs, expected exception)
			(self.client, {"file_names": [mine.name]}, frappe.PermissionError),
			(self.outsider, {"file_names": [mine.name]}, frappe.PermissionError),
			(self.m2, {"file_names": [mine.name]}, frappe.PermissionError),
			(self.m1, {"file_names": [contract.name]}, frappe.PermissionError),
			(self.m1, {"file_names": [pb_file.name]}, None),
			(self.m1, {"file_names": ["no-such-file-xyz"]}, None),
			(self.m1, {"file_names": [folder_in_pa]}, None),  # a folder passed as a file
			(self.m1, {"folder_path": client_root}, None),
			(self.m1, {"folder_path": incoming}, None),
			(self.m1, {"folder_path": files._client_outgoing_path(project)}, None),
			(self.m1, {"folder_path": pb_folder}, None),
			(self.m1, {"folder_path": self.root_pa}, None),  # the root itself: not strictly under it
			(self.m1, {"folder_path": files._attachments_root()}, None),
			(self.m1, {"folder_path": self.root_pa + "/../" + self.pb}, None),
			(self.m1, {"folder_path": self.root_pa + "/Batch B no such folder"}, None),
			(self.m1, {"folder_path": empty_folder}, None),
			(self.m1, {"folder_path": mine.name}, None),  # a file passed as a folder
			(self.m1, {}, None),
			(self.m1, {"file_names": []}, None),
			(self.m1, {"file_names": "[]"}, None),
			(self.m1, {"file_names": [mine.name], "folder_path": folder_in_pa}, None),
			(self.m1, {"file_names": [mine.name], "submission_type": ""}, None),
		]
		with mock.patch.object(files, "_lock_folder", wraps=files._lock_folder) as lock:
			for user, kw, exc in cases:
				frappe.set_user(user)
				kw = dict(kw)
				kw.setdefault("submission_type", CONCEPT)
				with self.assertRaises(exc or (frappe.ValidationError, frappe.PermissionError), msg=(user, kw)):
					sub.submit_to_client(project, **kw)
				files._forget_client_folders()
				frappe.set_user("Administrator")
				self.assertEqual(self._below(client_root), before, msg=(user, kw))
			lock.assert_not_called()  # validation runs before the lock

		frappe.set_user(self.m1)
		with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
			sub.submit_to_client("", CONCEPT, file_names=[mine.name])
		with self.assertRaises(frappe.PermissionError):
			sub.submit_to_client(self.pb, CONCEPT, file_names=[pb_file.name])  # no access to pb
		self.assertTrue(frappe.db.exists("File", in_incoming.name))

	def test_caps_refuse_before_any_write(self):
		project = self._fresh_project()
		frappe.set_user("Administrator")
		root = files.ensure_project_folders(project)["project_root"]
		folder = files._ensure_folder(root, "Batch B caps")
		self._src(project, "c1.txt", content=b"0123456789", folder=folder)
		self._src(project, "c2.txt", content=b"abcdefghij", folder=folder)
		client_root = files._client_folder_path(project)
		before = self._below(client_root)
		with mock.patch.object(files, "_ZIP_DOWNLOAD_MAX_FILES", 1):
			self.assertRefused(self._submit, project, folder_path=folder)
		with mock.patch.object(files, "_ZIP_DOWNLOAD_MAX_BYTES", 15):
			self.assertRefused(self._submit, project, folder_path=folder)
		frappe.set_user("Administrator")
		self.assertEqual(self._below(client_root), before)

	def test_too_long_destination_path_is_refused_before_writing(self):
		project = self._fresh_project()
		frappe.set_user("Administrator")
		root = files.ensure_project_folders(project)["project_root"]
		top = files._ensure_folder(root, "L" * 100)
		deep = files._ensure_folder(top, "M" * 100)
		self._src(project, "deep.txt", folder=deep)
		incoming = self._incoming(project)
		desc = "d" * 100
		stem = _submissions()._submission_stem(1, today(), CONCEPT, desc)
		self.assertGreater(len(incoming + "/" + stem + "/" + "M" * 100), 255)  # precondition
		before = self._below(files._client_folder_path(project))
		with self.assertRaises(frappe.ValidationError):
			self._submit(project, description=desc, folder_path=top)
		frappe.set_user("Administrator")
		self.assertEqual(self._below(files._client_folder_path(project)), before)

	def test_hostile_description_cannot_escape_incoming(self):
		project = self._fresh_project()
		a = self._src(project, "hostile.txt")
		incoming = self._incoming(project)
		res = self._submit(project, description='../../../Home/x/..\\y:*?"<>|', file_names=[a.name])
		frappe.set_user("Administrator")
		folder = frappe.get_doc("File", res["folder"])
		self.assertEqual(folder.folder, incoming)
		self.assertEqual(folder.name, incoming + "/" + folder.file_name)
		self.assertNotIn("/", folder.file_name)
		self.assertNotIn("\\", folder.file_name)
		self.assertNotIn("..", folder.file_name)
		self.assertFalse(re.search(r'[:*?"<>|]', folder.file_name))
		self.assertFalse(frappe.db.exists("File", "Home/x"))
		for c in self._children(res["folder"]):
			self.assertNotIn("/", c.file_name)

	def test_description_is_cleaned_and_capped(self):
		project = self._fresh_project()
		a = self._src(project, "cap.txt")
		res = self._submit(project, description="  rev 02   final  " + "z" * 300, file_names=[a.name])
		self.assertTrue(res["folder_name"].startswith(f"01_{today()}_Concept Submittal - rev 02 final z"))
		self.assertLessEqual(len(res["folder_name"]), 120)
		frappe.set_user("Administrator")
		for c in self._children(res["folder"]):
			self.assertLessEqual(len(c.file_name), 140)
		# a description that cleans to nothing gives the bare stem
		res2 = self._submit(project, description=' /:*?"<>| ', file_names=[a.name])
		self.assertEqual(res2["folder_name"], f"02_{today()}_Concept Submittal")

	def test_duplicate_name_is_never_created(self):
		project = self._fresh_project()
		a = self._src(project, "dup.txt")
		incoming = self._incoming(project)
		frappe.set_user("Administrator")
		taken = f"01_{today()}_Technical Submittal"
		files._ensure_folder(incoming, taken)

		with mock.patch("portal_app.api.files._next_submission_number", return_value=1):
			res = self._submit(project, submission_type=TECHNICAL, file_names=[a.name])
		self.assertEqual(res["folder_name"], f"02_{today()}_Technical Submittal")
		self.assertEqual(res["number"], 2)
		frappe.set_user("Administrator")
		names = [c.file_name for c in self._children(incoming)]
		self.assertEqual(len(names), len(set(names)))

	def test_retry_gives_up_after_five_tries(self):
		project = self._fresh_project()
		a = self._src(project, "full.txt")
		incoming = self._incoming(project)
		frappe.set_user("Administrator")
		for n in range(1, 6):
			files._ensure_folder(incoming, f"{n:02d}_{today()}_Concept Submittal")
		before = self._below(incoming)
		with mock.patch("portal_app.api.files._next_submission_number", return_value=1):
			with self.assertRaises(frappe.ValidationError):
				self._submit(project, file_names=[a.name])
		frappe.set_user("Administrator")
		self.assertEqual(self._below(incoming), before)

	def test_primary_key_collision_is_retried(self):
		"""The exists() pre-check is blind (lock not effective): the insert hits the File PK,
		raises DuplicateEntryError, and the next number is taken."""
		project = self._fresh_project()
		a = self._src(project, "pk.txt")
		incoming = self._incoming(project)
		frappe.set_user("Administrator")
		taken = f"01_{today()}_Concept Submittal"
		files._ensure_folder(incoming, taken)
		real_exists = frappe.db.exists

		def blind_exists(dt, dn=None, *args, **kwargs):
			if dt == "File" and isinstance(dn, str) and dn.startswith(incoming + "/"):
				return None
			return real_exists(dt, dn, *args, **kwargs)

		with mock.patch("portal_app.api.files._next_submission_number", return_value=1), mock.patch.object(
			frappe.local.db, "exists", side_effect=blind_exists
		):
			res = self._submit(project, file_names=[a.name])
		self.assertEqual(res["number"], 2)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count("File", {"folder": incoming, "file_name": taken}), 1)

	def test_admin_tier_and_lead_may_submit(self):
		project = self._fresh_project()
		a = self._src(project, "tiers.txt")
		for user in (self.super_admin, self.admin):
			res = self._submit(project, user=user, file_names=[a.name])
			self.assertTrue(res["folder"].startswith(self._incoming(project) + "/"))

	def test_project_without_client_folder_gets_one_on_submit(self):
		frappe.set_user("Administrator")
		project = _project(self._unique("Batch B no client folder"), [self.m1], lead=self.m1, customer=self.cust)
		files.ensure_project_folders(project)
		a = self._src(project, "first.txt")
		res = self._submit(project, file_names=[a.name])
		files._forget_client_folders()
		self.assertEqual(frappe.db.get_value("File", res["folder"], "folder"), files._client_incoming_path(project))


# =====================================================================================
# R7 — client transmittal reads
# =====================================================================================
class TestClientTransmittals(BatchBBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.pt = _project("Batch B transmittals", [cls.m1], lead=cls.m1, customer=cls.cust)
		files.ensure_project_folders(cls.pt)
		folders = files._ensure_client_folders(cls.pt)
		cls.pt_root = files.ensure_project_folders(cls.pt)["project_root"]
		sub = importlib.import_module("portal_app.api.submissions")

		def src(name, folder=None):
			return save_file(
				name,
				("batch b " + name + frappe.generate_hash(length=8)).encode(),
				"Project",
				cls.pt,
				folder=folder or cls.pt_root,
				is_private=1,
			)

		s1 = src("t1.txt")
		drawings = files._ensure_folder(cls.pt_root, "02-DRAWINGS")
		set_folder = files._ensure_folder(drawings, "T Set")
		nested = files._ensure_folder(set_folder, "Sub")
		cls.set_a = src(BatchBBase._fresh_name("t-set-a.txt"), set_folder).file_name
		cls.set_b = src(BatchBBase._fresh_name("t-set-b.dwg"), nested).file_name
		cls.internal = src("internal-only-secret.txt", drawings)
		cls.internal_root = src("internal-root-secret.txt")

		frappe.set_user(cls.m1)
		cls.sub1 = sub.submit_to_client(cls.pt, CONCEPT, description="first", file_names=[s1.name])
		cls.sub2 = sub.submit_to_client(cls.pt, TECHNICAL, folder_path=set_folder)
		cls.legacy = files.submit_to_client_submittal(s1.name, cls.pt)
		frappe.set_user("Administrator")
		cls.legacy_name = frappe.db.get_value(
			"File", {"folder": folders["incoming"], "file_name": cls.legacy["file_name"]}, "name"
		)
		up = save_file("client-reply.txt", b"client reply batch b", "Project", cls.pt, folder=folders["outgoing"], is_private=1)
		frappe.db.set_value("File", up.name, "owner", cls.client, update_modified=False)
		cls.client_upload = up.name
		cls.client_root = folders["root"]

	def test_client_sees_numbered_submissions(self):
		frappe.set_user(self.client)
		res = _submissions().list_client_transmittals(self.pt)
		self.assertEqual(res["project"], self.pt)
		self.assertIn("project_name", res)
		inc = res["incoming"]
		self.assertEqual([s["number"] for s in inc], [1, 2, 3])
		self.assertEqual([s["is_latest"] for s in inc], [False, False, True])
		self.assertEqual([s["kind"] for s in inc], ["folder", "folder", "file"])
		self.assertEqual(inc[0]["key"], self.sub1["folder"])
		self.assertEqual(inc[0]["title"], self.sub1["folder_name"])
		self.assertEqual(inc[1]["key"], self.sub2["folder"])
		self.assertEqual(inc[2]["key"], self.legacy_name)
		self.assertEqual(inc[2]["title"], self.legacy["file_name"])
		self.assertEqual(inc[2]["file_count"], 1)
		self.assertEqual([f["name"] for f in inc[2]["files"]], [self.legacy_name])

		folder_sub = inc[1]
		self.assertEqual(folder_sub["file_count"], 2)
		by_name = {f["file_name"]: f for f in folder_sub["files"]}
		self.assertEqual(set(by_name), {self.set_a, self.set_b})
		self.assertEqual(by_name[self.set_a]["relative_path"], "")
		self.assertEqual(by_name[self.set_b]["relative_path"], "Sub")
		self.assertEqual(
			[(f["relative_path"], f["file_name"]) for f in folder_sub["files"]],
			sorted((f["relative_path"], f["file_name"]) for f in folder_sub["files"]),
		)
		for s in inc:
			self.assertTrue({"key", "kind", "title", "number", "is_latest", "created", "file_count", "files"} <= set(s))
			for f in s["files"]:
				self.assertTrue({"name", "file_name", "file_size", "creation", "relative_path"} <= set(f))
				self.assertNotIn("owner", f)
				self.assertNotIn("file_url", f)

		out = res["outgoing"]
		self.assertEqual([s["number"] for s in out], [1])
		self.assertTrue(out[0]["is_latest"])
		self.assertEqual(out[0]["kind"], "file")
		self.assertEqual(out[0]["files"][0]["name"], self.client_upload)
		self.assertEqual(out[0]["files"][0].get("uploaded_by_client"), 1)
		self.assertTrue(res["can_upload"])

		frappe.set_user(self.m1)
		staff = _submissions().list_client_transmittals(self.pt)
		self.assertFalse(staff["can_upload"])
		self.assertEqual([s["number"] for s in staff["incoming"]], [1, 2, 3])

	def test_client_cannot_read_other_customers(self):
		sub = _submissions()
		for user, project in (
			(self.client, self.pf),
			(self.client, self.pb),
			(self.client2, self.pt),
			(self.client2, self.pa),
			(self.outsider, self.pt),
			(self.m3, self.pt),
		):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError, msg=(user, project)):
				sub.list_client_transmittals(project)
		frappe.set_user(self.client2)
		self.assertEqual(sub.list_client_transmittals(self.pf)["incoming"], [])

	def test_transmittals_never_leak_internal_paths(self):
		frappe.set_user(self.client)
		res = _submissions().list_client_transmittals(self.pt)
		blob = frappe.as_json(res)
		self.assertNotIn("internal-only-secret", blob)
		self.assertNotIn("internal-root-secret", blob)
		self.assertNotIn(self.internal.name, blob)
		self.assertNotIn(self.internal_root.name, blob)
		self.assertNotIn("/private/files/", blob)
		frappe.set_user("Administrator")
		for direction in ("incoming", "outgoing"):
			for s in res[direction]:
				if s["kind"] == "folder":
					self.assertTrue(s["key"].startswith(self.client_root + "/"), s["key"])
				for f in s["files"]:
					folder = frappe.db.get_value("File", f["name"], "folder")
					self.assertTrue(files._in_folder(folder, self.client_root), (f, folder))

	def test_lookalike_project_folder_is_not_listed(self):
		# Only Incoming / Outgoing are listed: a sibling folder whose name merely starts
		# with "Incoming" (prefix match without the "/") must never leak in.
		frappe.set_user("Administrator")
		lookalike = files._ensure_folder(self.client_root, "IncomingX")
		files._ensure_folder(lookalike, "99_should_not_show")
		frappe.set_user(self.client)
		res = _submissions().list_client_transmittals(self.pt)
		titles = [s["title"] for d in ("incoming", "outgoing") for s in res[d]]
		self.assertNotIn("99_should_not_show", titles)

	def test_listing_creates_nothing(self):
		frappe.set_user("Administrator")
		project = _project(self._unique("Batch B bare"), customer=self.cust)
		root = files._attachments_root() + "/" + project
		self.assertFalse(frappe.db.exists("File", root))
		count = frappe.db.count("File")
		for user in (self.client, self.super_admin):
			frappe.set_user(user)
			files._forget_client_folders()
			res = _submissions().list_client_transmittals(project)
			self.assertEqual(res["incoming"], [])
			self.assertEqual(res["outgoing"], [])
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("File", root))
		self.assertEqual(frappe.db.count("File"), count)

	def test_client_project_list_is_scoped(self):
		sub = _submissions()
		ours = {self.pa, self.pb, self.pf, self.pt}

		frappe.set_user(self.client)
		rows = sub.list_client_projects()
		names = {r["name"] for r in rows}
		self.assertTrue({self.pa, self.pt} <= names)
		self.assertFalse({self.pb, self.pf} & names)
		for r in rows:
			self.assertTrue(set(r) <= {"name", "project_name", "portal_project_code"}, r)
			self.assertIn("project_name", r)

		frappe.set_user(self.client2)
		self.assertEqual({r["name"] for r in sub.list_client_projects()} & ours, {self.pf})

		frappe.set_user(self.m1)
		self.assertEqual({r["name"] for r in sub.list_client_projects()} & ours, {self.pa, self.pt})

		# a Projects User with no project is a portal user: an empty list, not a refusal
		frappe.set_user(self.outsider)
		self.assertEqual(sub.list_client_projects(), [])

		frappe.set_user(self.non_portal)
		with self.assertRaises(frappe.PermissionError):
			sub.list_client_projects()

	def test_client_with_no_customers_gets_empty_list(self):
		frappe.set_user("Administrator")
		lonely = _user("lonelyclient", (helper.PORTAL_CUSTOMER_ROLE,), "Website User")
		frappe.set_user(lonely)
		try:
			rows = _submissions().list_client_projects()
		except frappe.PermissionError:
			rows = []  # a client with no customers is not a portal user: refused is acceptable
		self.assertEqual(rows, [])


# =====================================================================================
# R5 / R7 / R1 frontend — static contract checks (no JS test runner in this repo)
# =====================================================================================
class TestFrontendContract(BatchBBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.src = os.path.join(os.path.dirname(frappe.get_app_path("portal_app")), "frontend", "src")

	def _read(self, rel):
		path = os.path.join(self.src, rel)
		self.assertTrue(os.path.exists(path), path)
		with open(path, encoding="utf-8") as fh:
			return fh.read()

	def test_i18n_dictionary(self):
		js = self._read("i18n/clientPortal.js")
		self.assertIn("export const MESSAGES", js)
		self.assertIn("export function useClientLang", js)
		self.assertIn("portal_client_lang", js)
		self.assertIn("try", js)  # storage access wrapped
		for ar in ("الوارد", "الصادر", "الأحدث (النهائي)", "تسجيل الخروج", "بوابة العميل"):
			self.assertIn(ar, js)
		for key in (
			"title", "chooseProject", "noProjects", "incoming", "outgoing", "incomingHint", "outgoingHint",
			"submissionN", "latest", "fileCount", "download", "back", "backToProjects", "empty", "upload",
			"uploading", "uploaded", "uploadFailed", "loading", "error", "signOut", "language", "sentOn",
		):
			self.assertRegex(js, r"\b" + key + r"\s*:", key)
		self.assertIn("ar-u-ca-gregory-nu-latn", self._read("pages/ClientTransmittals.vue") + js)

	def test_client_page(self):
		vue = self._read("pages/ClientTransmittals.vue")
		self.assertRegex(vue, r':dir="dir"')
		self.assertRegex(vue, r':lang="lang"')
		self.assertIn("portal_app.api.submissions.list_client_transmittals", vue)
		self.assertIn("portal_app.api.submissions.list_client_projects", vue)
		self.assertIn("portal_app.api.files.download_project_file", vue)
		self.assertIn("__client_outgoing__", vue)
		self.assertIn("rtl:rotate-180", vue)
		self.assertIn("<bdi", vue)
		self.assertNotIn("file_url", vue)
		self.assertNotIn("document.documentElement.dir", vue)  # never flips <html>
		for cls_attr in re.findall(r'class="([^"]*)"', vue):  # logical utilities only
			self.assertNotRegex(cls_attr, r"(?<![\w:-])(ml|mr|pl|pr|left|right)-[\w\[]|(?<![\w-])text-(left|right)\b", cls_attr)

	def test_router(self):
		js = self._read("router/index.js")
		self.assertIn("ClientTransmittals.vue", js)
		self.assertRegex(js, r'path:\s*"/client"')
		self.assertIn("is_customer_portal_user", js)
		self.assertIn("can_manage_submission_types", js)

	def test_files_page_explorer_navigation(self):
		vue = self._read("pages/Files.vue")
		for token in ("currentFolder", "childFolders", "showAllFiles", "SubmitToClientModal"):
			self.assertIn(token, vue)
		for gone in ("folderTreeView", "folderTreeExpanded", "toggleFolderTreeNode"):
			self.assertNotIn(gone, vue)

	def test_submit_modal_and_callers(self):
		modal = self._read("component/SubmitToClientModal.vue")
		self.assertIn("portal_app.api.submissions.submit_to_client", modal)
		self.assertIn("portal_app.api.submissions.list_submission_types", modal)
		self.assertIn('maxlength="100"', modal)
		all_files = self._read("pages/AllFiles.vue")
		self.assertIn("SubmitToClientModal", all_files)
		self.assertNotIn("confirmSubmitToClient", all_files)
		self.assertNotIn("previewSubmitName", all_files)
		admin = self._read("pages/Admin.vue")
		self.assertIn("can_manage_submission_types", admin)
		self.assertIn("add_submission_type", admin)
		self.assertIn("set_submission_type_enabled", admin)
