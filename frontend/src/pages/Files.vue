<script setup>
import { ref, onMounted, watch, inject, computed, nextTick } from "vue";
import { call, uploadFile, ensureCsrfReady } from "@/api";
import { useRoute } from "vue-router";
import { FeatherIcon } from "frappe-ui";

const route = useRoute();
const portalCapabilities = inject("portalCapabilities", ref({}));
const refreshPortalCapabilities = inject("refreshPortalCapabilities", () => Promise.resolve());
const isCustomerPortalUser = computed(() => !!portalCapabilities.value?.is_customer_portal_user);
const projects = ref([]);
const project = ref(route.query.project || "");
const projectSearch = ref("");
const projectDropdownOpen = ref(false);
const filteredProjects = computed(() => {
	const q = projectSearch.value.trim().toLowerCase();
	if (!q) return projects.value;
	return projects.value.filter(
		(p) =>
			String(p.project_name || "").toLowerCase().includes(q) ||
			String(p.name || "").toLowerCase().includes(q),
	);
});
const selectedProjectLabel = computed(() => {
	const p = projects.value.find((x) => x.name === project.value);
	return p ? `${p.project_name} (${p.name})` : project.value || "";
});
function selectProject(p) {
	project.value = p.name;
	projectSearch.value = "";
	projectDropdownOpen.value = false;
}
function onProjectInputFocus() {
	projectSearch.value = "";
	projectDropdownOpen.value = true;
}
function onProjectBlur() {
	setTimeout(() => { projectDropdownOpen.value = false; }, 150);
}
const files = ref([]);
const folders = ref([]);
/** ERPNext File folder for this project (parent of template subfolders). */
const projectRootPath = ref("");
const settings = ref({});
const loading = ref(false);
const uploadBusy = ref(false);
const uploadError = ref("");
const uploadInfo = ref("");
const isPrivateUpload = ref(false);
const dragOver = ref(false);
const fileInput = ref(null);
const folderInput = ref(null);
const uploadCardRef = ref(null);
const filesScrollRoot = ref(null);

// Confirm-before-upload modal: stages files chosen via picker / drop zone / folder drop until
// the user reviews and accepts the auto-generated name (which embeds today's date), the category
// (target folder), and the date itself.
const confirmUploadOpen = ref(false);
const pendingUploads = ref([]);
// Folder upload — files preserve their internal structure under a wrapping folder
// auto-named `<categoryNumberPrefix>_<date>` (`_v2`, `_v3` for same-day repeats).
const pendingFolder = ref(null);
const isFolderMode = computed(() => !!pendingFolder.value);

// Portal File Type list (managed in ERP at /app/portal-file-type). Lets users tag each
// upload as AutoCAD / PDF / GAD / etc. — pre-selected by extension on stage, editable.
const fileTypes = ref([]);
async function loadFileTypes() {
	try {
		const res = await call({ method: "portal_app.api.files.list_portal_file_types" });
		fileTypes.value = (res?.types || []).map((t) => ({
			name: t.name,
			label: t.type_name || t.name,
			extensions: String(t.extensions || "")
				.split(",")
				.map((e) => e.trim().toLowerCase())
				.filter(Boolean),
		}));
	} catch {
		fileTypes.value = [];
	}
}

function detectFileType(originalName) {
	const lower = String(originalName || "").toLowerCase();
	const dot = lower.lastIndexOf(".");
	if (dot < 0) return "";
	const ext = lower.slice(dot);
	for (const t of fileTypes.value) {
		if (t.extensions.includes(ext)) return t.name;
	}
	return "";
}

// ─── Project File Classification ─────────────────────────────────────────────
const _EXT_MAP = {
	".ppt":  ["Presentation Files", "PowerPoint"],
	".pptx": ["Presentation Files", "PowerPoint"],
	".indd": ["Editable Design Source Files", "InDesign"],
	".idml": ["Editable Design Source Files", "InDesign"],
	".dwg":  ["Drawing / Layout Files", "AutoCAD / DWG"],
	".dxf":  ["Drawing / Layout Files", "CAD Exchange / DXF"],
	".skp":  ["3D Model Files", "SketchUp"],
	".rvt":  ["3D Model Files", "Revit"],
	".rfa":  ["3D Model Files", "Revit Family"],
	".max":  ["3D Model Files", "3ds Max"],
	".ls":   ["3D Model Files", "Lumion"],
	".ls12": ["3D Model Files", "Lumion"],
	".ls13": ["3D Model Files", "Lumion"],
	".ls14": ["3D Model Files", "Lumion"],
	".ls15": ["3D Model Files", "Lumion"],
	".3dm":  ["3D Model Files", "Rhino"],
	".fbx":  ["3D Model Files", "FBX Exchange"],
	".obj":  ["3D Model Files", "OBJ Exchange"],
	".dae":  ["3D Model Files", "Collada"],
	".exe":  ["3D Model Files", "Enscape Standalone"],
	".xls":  ["Feasibility / Area Calculation Files", "Excel"],
	".xlsx": ["Feasibility / Area Calculation Files", "Excel"],
	".xlsm": ["Feasibility / Area Calculation Files", "Excel Macro"],
	".csv":  ["Feasibility / Area Calculation Files", "CSV"],
	".psd":  ["Editable Design Source Files", "Photoshop"],
	".psb":  ["Editable Design Source Files", "Photoshop Large"],
	".ai":   ["Editable Design Source Files", "Illustrator"],
	".jpg":  ["Rendering / Image Files", "JPEG"],
	".jpeg": ["Rendering / Image Files", "JPEG"],
	".png":  ["Rendering / Image Files", "PNG"],
	".tif":  ["Rendering / Image Files", "TIFF"],
	".tiff": ["Rendering / Image Files", "TIFF"],
};
const _PDF_KW = [
	{ kw: ["presentation", "client", "concept", "package"],          r: ["Presentation Files", "PDF Presentation"] },
	{ kw: ["drawing", "plan", "section", "elevation", "municipality"], r: ["Drawing / Layout Files", "PDF Drawing"] },
	{ kw: ["feasibility", "area", "bua", "schedule", "report"],      r: ["Feasibility / Area Calculation Files", "PDF Feasibility Report"] },
	{ kw: ["submission", "final", "issued"],                          r: ["Submission Files", "PDF Submission"] },
];
const _DOC_TYPE_MAP = {
	"Presentation":       ["Presentation Files", "PDF Presentation"],
	"Drawing Sheet":      ["Drawing / Layout Files", "PDF Drawing"],
	"Feasibility Report": ["Feasibility / Area Calculation Files", "PDF Feasibility Report"],
	"Submission":         ["Submission Files", "PDF Submission"],
};
function _classifyPdf(name, docType) {
	if (docType && _DOC_TYPE_MAP[docType]) return _DOC_TYPE_MAP[docType];
	const lower = (name || "").toLowerCase();
	for (const { kw, r } of _PDF_KW) {
		if (kw.some((k) => lower.includes(k))) return r;
	}
	return ["Presentation Files", "PDF Presentation"];
}
function classifyFile(name, docType) {
	const dot = (name || "").lastIndexOf(".");
	const ext = dot >= 0 ? name.substring(dot).toLowerCase() : "";
	if (ext === ".pdf") return [..._classifyPdf(name, docType), ext];
	const hit = _EXT_MAP[ext];
	if (hit) return [...hit, ext];
	return ["Uncategorized", ext ? ext.substring(1).toUpperCase() : "", ext];
}
const PDF_DOC_TYPE_OPTIONS = ["", "Presentation", "Drawing Sheet", "Feasibility Report", "Submission", "General"];
// ─────────────────────────────────────────────────────────────────────────────

function todayIso() {
	const d = new Date();
	const mm = String(d.getMonth() + 1).padStart(2, "0");
	const dd = String(d.getDate()).padStart(2, "0");
	return `${d.getFullYear()}-${mm}-${dd}`;
}

function splitFileName(name) {
	const safe = String(name || "file");
	const i = safe.lastIndexOf(".");
	if (i <= 0) return { base: safe, ext: "" };
	return { base: safe.slice(0, i), ext: safe.slice(i) };
}

function categoryToSlug(categoryName) {
	const label = folderLabelByName.value?.[categoryName] || categoryName || "";
	const leaf = String(label).split("/").pop() || "uncategorised";
	return leaf
		.trim()
		.replace(/[\\/]+/g, "-")
		.replace(/\s+/g, "-")
		.replace(/[^a-zA-Z0-9_-]/g, "")
		.replace(/-+/g, "-")
		.replace(/^-|-$/g, "") || "uncategorised";
}

function buildAutoName(base, ext, isoDate, categorySlug) {
	const slug = categorySlug ? `_${categorySlug}` : "";
	return `${base}${slug}_${isoDate}${ext}`;
}

// Wrapping-folder name pattern: leading number prefix of the category leaf + ISO date.
// Falls back to category slug when there's no number prefix.
function categoryNumberPrefix(categoryName) {
	const label = folderLabelByName.value?.[categoryName] || categoryName || "";
	const leaf = String(label).split("/").pop() || "";
	const match = leaf.trim().match(/^(\d+)/);
	if (match) return match[1];
	return categoryToSlug(categoryName);
}
function buildWrapperName(categoryName, isoDate, fileBase = "") {
	// Series prefix (01, 02, …) is assigned by the backend based on how many
	// wrapper folders already exist in the target subfolder. The frontend only
	// constructs the date+name portion so the user can preview and edit it.
	if (fileBase) {
		const slug = fileBase.replace(/[^a-zA-Z0-9_]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
		return `${isoDate}_${slug}`;
	}
	return isoDate;
}

// Walk a webkitGetAsEntry tree, collecting `[{file, relativePath}]`.
function _readEntry(entry, path, out) {
	return new Promise((resolve) => {
		if (!entry) return resolve();
		if (entry.isFile) {
			entry.file((f) => { out.push({ file: f, relativePath: path }); resolve(); }, () => resolve());
		} else if (entry.isDirectory) {
			const reader = entry.createReader();
			const all = [];
			const readBatch = () => {
				reader.readEntries(async (entries) => {
					if (!entries.length) {
						const sub = `${path ? path + "/" : ""}${entry.name}`;
						await Promise.all(all.map((e) => _readEntry(e, sub, out)));
						resolve();
						return;
					}
					all.push(...entries);
					readBatch();
				}, () => resolve());
			};
			readBatch();
		} else { resolve(); }
	});
}
async function collectFromDataTransfer(dt) {
	const out = [];
	const items = dt?.items;
	if (items?.length) {
		const entries = [];
		for (const it of items) {
			const e = typeof it.webkitGetAsEntry === "function" ? it.webkitGetAsEntry() : null;
			if (e) entries.push(e);
		}
		if (entries.length) {
			await Promise.all(entries.map((e) => _readEntry(e, "", out)));
			return out;
		}
	}
	for (const f of dt?.files || []) out.push({ file: f, relativePath: "" });
	return out;
}
async function _dropContainsDirectory(dt) {
	const items = dt?.items;
	if (!items?.length) return false;
	for (const it of items) {
		const ent = typeof it.webkitGetAsEntry === "function" ? it.webkitGetAsEntry() : null;
		if (ent && ent.isDirectory) return true;
	}
	return false;
}

function regenerateAutoName(row) {
	row.name = buildAutoName(row.base, row.ext, row.date, categoryToSlug(row.category));
}

function onPendingDateChange(row) {
	if (!row.nameEdited) regenerateAutoName(row);
}

function onPendingCategoryChange(row) {
	if (!row.nameEdited) regenerateAutoName(row);
}

function onPendingNameChange(row) {
	row.nameEdited = true;
}

function scrollFilesPage(where) {
	const el = filesScrollRoot.value;
	if (!el) return;
	const top = where === "bottom" ? el.scrollHeight : 0;
	el.scrollTo({ top, behavior: "smooth" });
}
const folderPickerOpen = ref(false);
const folderPickerSearch = ref("");
const folderPickerExpanded = ref(new Set());
// Separate expansion state for the main "Tree" view on the page (independent of the picker dialog).
// Keys: subfolder labels (e.g. "Drawings/Plans") plus a sentinel `__root__:<projectRootPath>` for the project root row.
const folderTreeExpanded = ref(new Set());

// Bulk-select state for the file list
const selectedFileNames = ref([]);
const selectedFileSet = computed(() => new Set(selectedFileNames.value));
const allVisibleSelected = computed(
	() => visibleFiles.value.length > 0 && visibleFiles.value.every((f) => selectedFileSet.value.has(f.name)),
);
const someVisibleSelected = computed(
	() => visibleFiles.value.some((f) => selectedFileSet.value.has(f.name)),
);
function toggleFileSelection(name) {
	const set = new Set(selectedFileNames.value);
	set.has(name) ? set.delete(name) : set.add(name);
	selectedFileNames.value = [...set];
}
function toggleSelectAllVisible() {
	if (allVisibleSelected.value) {
		const ids = new Set(visibleFiles.value.map((f) => f.name));
		selectedFileNames.value = selectedFileNames.value.filter((n) => !ids.has(n));
	} else {
		const set = new Set(selectedFileNames.value);
		for (const f of visibleFiles.value) set.add(f.name);
		selectedFileNames.value = [...set];
	}
}
function clearFileSelection() {
	selectedFileNames.value = [];
}
function fmtDate(s) {
	if (!s) return "—";
	const dt = new Date(String(s).replace(" ", "T"));
	if (Number.isNaN(dt.getTime())) return String(s);
	return dt.toLocaleString(undefined, {
		year: "numeric",
		month: "short",
		day: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

function fmtFileSize(bytes) {
	if (bytes == null) return "—";
	const n = Number(bytes);
	if (Number.isNaN(n) || !n) return "—";
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
	if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
	return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`;
}
async function downloadSelectedZip() {
	if (!project.value || !selectedFileNames.value.length) return;
	try {
		const url = `/api/method/portal_app.api.files.download_files_zip`;
		const fd = new FormData();
		fd.append("project", project.value);
		fd.append("file_names", JSON.stringify(selectedFileNames.value));
		// Frappe never sets a csrf_token cookie, so reading document.cookie always
		// produced undefined and this POST was rejected as a CSRF failure every time.
		const csrf = await ensureCsrfReady();
		const res = await fetch(url, {
			method: "POST",
			credentials: "include",
			headers: csrf ? { "X-Frappe-CSRF-Token": csrf } : {},
			body: fd,
		});
		if (!res.ok) throw new Error("ZIP download failed");
		const blob = await res.blob();
		const a = document.createElement("a");
		a.href = URL.createObjectURL(blob);
		a.download = `${project.value}-files.zip`;
		document.body.appendChild(a);
		a.click();
		a.remove();
		URL.revokeObjectURL(a.href);
	} catch (e) {
		fileListActionError.value = "Could not download the ZIP. Try again, or check the Error Log.";
	}
}
const destination = ref("erpnext");
const externalProvider = ref("frappe_drive");
const targetFolder = ref("");
const advancedUploadOpen = ref(false);
const shareBusy = ref(false);
const shareBusyFor = ref("");
const shareInfo = ref("");
const shareError = ref("");
const shareDays = ref(7);
/** Bumps when project/folder changes so in-flight share responses cannot repopulate stale links. */
const shareEpoch = ref(0);
/** Collapsed by default; opens when user expands or after a successful share (until reset). */
const sharePanelOpen = ref(false);
const renameOpen = ref(false);
const renameFolderPath = ref("");
const renameNewName = ref("");
const renameBusy = ref(false);
const renameError = ref("");

const shareModalOpen = ref(false);
const shareModalFolder = ref("");
const shareModalLabel = ref("");
const shareModalLoading = ref(false);
const shareModalSaving = ref(false);
const shareModalError = ref("");
const shareModalOk = ref("");
const folderShares = ref([]);
const shareTrackingAvailable = ref(true);
const userSearchQ = ref("");
const userSearchHits = ref([]);
const userSearchBusy = ref(false);
const userExpiryDays = ref(30);
const notifyOnShare = ref(false);
const linkExpiryDays = ref(7);
let userSearchTimer;

const linkSharesForFolder = computed(() =>
	folderShares.value.filter((s) => s.share_kind === "Link"),
);
const userSharesForFolder = computed(() =>
	folderShares.value.filter((s) => s.share_kind === "User"),
);
const activeLinkShare = computed(() => linkSharesForFolder.value[0] || null);

function fmtShareExpiry(s) {
	if (!s?.expires_at) return "no expiry";
	const dt = new Date(String(s.expires_at).replace(" ", "T"));
	if (Number.isNaN(dt.getTime())) return s.expires_at;
	return dt.toLocaleDateString();
}
const fileListActionError = ref("");
const deleteBusyName = ref("");
const folderFilter = ref("");
const fileSearch = ref("");
const folderView = ref("grid");

/**
 * Any user allocated to the project can share its folders / individual files with
 * teammates (Drive-style collaboration). Customer-portal users are excluded.
 */
const canShareFolder = computed(() => {
	if (isCustomerPortalUser.value) return false;
	const allowed = portalCapabilities.value?.allowed_project_names || [];
	return !!project.value && allowed.includes(project.value);
});

/** Tighter capability — only project managers can rename / hard-edit folder structure. */
const canManageProject = computed(() => {
	const names = portalCapabilities.value?.manageable_project_names || [];
	return !!project.value && names.includes(project.value);
});

const sessionUser = computed(() => portalCapabilities.value?.portal_user || "");

/** Project manager: any file. Team member: own uploads only (matches API). */
function canDeleteThisFile(f) {
	if (!f || f.is_folder || isCustomerPortalUser.value || !project.value) return false;
	if (canManageProject.value) return true;
	return !!sessionUser.value && f.owner === sessionUser.value;
}

/** Show column whenever the user may open this project’s files (not customer portal). Row-level button still respects manager vs owner. */
const showFileDeleteColumn = computed(() => !isCustomerPortalUser.value && !!project.value);

const canEditFolderTemplate = computed(
	() => !!portalCapabilities.value?.can_edit_portal_folder_template && !isCustomerPortalUser.value,
);

const manageableCount = computed(() => (portalCapabilities.value?.manageable_project_names || []).length);

function scrollToPortalHighlight() {
	const raw = route.query.highlight;
	const key = Array.isArray(raw) ? raw[0] : raw;
	if (!key || typeof key !== "string") return;
	const map = { "file-help": "portal-scroll-file-help", template: "portal-scroll-template" };
	const elId = map[key.trim()];
	if (!elId) return;
	nextTick(() => {
		document.getElementById(elId)?.scrollIntoView({ behavior: "smooth", block: "start" });
	});
}

function firstUrl(text) {
	const m = String(text || "").match(/https?:\/\/[^\s)]+/i);
	return m ? m[0] : "";
}

const driveUrl = computed(() => settings.value?.frappe_drive_site_url || "");
const googleUrl = computed(() => firstUrl(settings.value?.google_drive_notes));
const bimUrl = computed(() => firstUrl(settings.value?.bim_360_notes));
const folderLabelByName = computed(() => {
	const map = {};
	const root = projectRootPath.value;
	if (root) map[root] = "Project folder (all files)";
	for (const f of folders.value) map[f.name] = f.label;
	return map;
});
const visibleFiles = computed(() => {
	const q = fileSearch.value.trim().toLowerCase();
	const root = projectRootPath.value;
	return (files.value || []).filter((f) => {
		if (folderFilter.value) {
			if (root && folderFilter.value === root) {
				const fp = String(f.folder || "");
				if (!(fp === root || fp.startsWith(`${root}/`))) return false;
			} else if (f.folder !== folderFilter.value) {
				return false;
			}
		}
		if (q && !String(f.file_name || "").toLowerCase().includes(q)) return false;
		return true;
	});
});
const folderEntries = computed(() => {
	const rows = [];
	const root = projectRootPath.value;
	if (root) {
		const c = (files.value || []).filter((x) => {
			const fp = String(x.folder || "");
			return fp === root || fp.startsWith(`${root}/`);
		}).length;
		rows.push({
			name: root,
			label: "Project folder (all files)",
			leafLabel: "Project folder (all files)",
			parentPath: "",
			depth: 0,
			isRoot: true,
			fileCount: c,
		});
	}
	const list = (folders.value || []).slice();
	list.sort((a, b) => String(a.label || "").localeCompare(String(b.label || ""), undefined, { numeric: true }));
	for (const f of list) {
		const label = String(f.label || "");
		const parts = label.split("/");
		const depth = parts.length;
		const leafLabel = parts[parts.length - 1] || label;
		const parentPath = parts.slice(0, -1).join(" / ");
		rows.push({
			name: f.name,
			label: label,
			leafLabel,
			parentPath,
			depth,
			isRoot: false,
			fileCount: (files.value || []).filter((x) => x.folder === f.name).length,
		});
	}
	return rows;
});

/**
 * Tree-shaped projection of `folders` for the on-page "Tree" view. Unlike `folderEntries`
 * (which always emits every folder), this only emits a node's descendants when that node is
 * expanded — so the user explores one branch at a time instead of seeing the entire hierarchy
 * up front.
 */
const folderTreeView = computed(() => {
	const rows = [];
	const root = projectRootPath.value;
	const rootKey = root ? `__root__:${root}` : "";
	const rootExpanded = !root || folderTreeExpanded.value.has(rootKey);

	const treeRoot = { children: new Map() };
	for (const f of folders.value) {
		const segments = String(f.label || "").split("/").filter(Boolean);
		let cursor = treeRoot;
		const accumulated = [];
		for (let i = 0; i < segments.length; i++) {
			const seg = segments[i];
			accumulated.push(seg);
			if (!cursor.children.has(seg)) {
				cursor.children.set(seg, {
					children: new Map(),
					name: i === segments.length - 1 ? f.name : "",
					label: accumulated.join("/"),
					seg,
				});
			} else if (i === segments.length - 1) {
				const node = cursor.children.get(seg);
				node.name = f.name;
			}
			cursor = cursor.children.get(seg);
		}
	}

	const fileCountFor = (folderName) =>
		(files.value || []).filter((x) => x.folder === folderName).length;

	if (root) {
		const rootCount = (files.value || []).filter((x) => {
			const fp = String(x.folder || "");
			return fp === root || fp.startsWith(`${root}/`);
		}).length;
		rows.push({
			name: root,
			label: "Project folder (all files)",
			leafLabel: "Project folder (all files)",
			parentPath: "",
			depth: 0,
			isRoot: true,
			hasChildren: treeRoot.children.size > 0,
			fileCount: rootCount,
			expanded: rootExpanded,
			expandKey: rootKey,
		});
	}

	if (rootExpanded) {
		const walk = (node, depth, parentPath) => {
			const sorted = [...node.children.values()].sort((a, b) =>
				String(a.seg || "").localeCompare(String(b.seg || ""), undefined, { numeric: true }),
			);
			for (const child of sorted) {
				const expanded = folderTreeExpanded.value.has(child.label);
				rows.push({
					name: child.name,
					label: child.label,
					leafLabel: child.seg,
					parentPath,
					depth,
					isRoot: false,
					hasChildren: child.children.size > 0,
					fileCount: child.name ? fileCountFor(child.name) : 0,
					expanded,
					expandKey: child.label,
				});
				if (expanded && child.children.size > 0) {
					walk(child, depth + 1, parentPath ? `${parentPath} / ${child.seg}` : child.seg);
				}
			}
		};
		walk(treeRoot, 1, "");
	}
	return rows;
});

function toggleFolderTreeNode(key) {
	if (!key) return;
	const next = new Set(folderTreeExpanded.value);
	next.has(key) ? next.delete(key) : next.add(key);
	folderTreeExpanded.value = next;
}

function subfolderLabel(folderPath) {
	const path = String(folderPath || "");
	if (!path) return "—";
	if (folderLabelByName.value[path]) return folderLabelByName.value[path];
	const parts = path.split("/");
	return parts[parts.length - 1] || path;
}

function folderOptionLabel(label) {
	const path = String(label || "");
	if (!path) return "";
	const parts = path.split("/");
	if (parts.length <= 1) return path;
	return `${"  ".repeat(parts.length - 1)}↳ ${parts[parts.length - 1]}  (${parts.slice(0, -1).join(" / ")})`;
}

const targetFolderEntry = computed(() => folders.value.find((f) => f.name === targetFolder.value) || null);
const targetFolderLeafLabel = computed(() => {
	const entry = targetFolderEntry.value;
	if (!entry) return "";
	const parts = String(entry.label || "").split("/");
	return parts[parts.length - 1] || entry.label;
});
const targetFolderParentLabel = computed(() => {
	const entry = targetFolderEntry.value;
	if (!entry) return "";
	const parts = String(entry.label || "").split("/");
	if (parts.length <= 1) return "";
	return parts.slice(0, -1).join(" / ");
});

const folderTree = computed(() => {
	const root = { children: new Map(), name: "", label: "", entry: null, depth: 0 };
	for (const f of folders.value) {
		const segments = String(f.label || "").split("/").filter(Boolean);
		let cursor = root;
		const accumulated = [];
		for (let i = 0; i < segments.length; i++) {
			const seg = segments[i];
			accumulated.push(seg);
			if (!cursor.children.has(seg)) {
				cursor.children.set(seg, {
					children: new Map(),
					name: i === segments.length - 1 ? f.name : "",
					label: accumulated.join("/"),
					seg,
					entry: i === segments.length - 1 ? f : null,
					depth: i + 1,
				});
			} else if (i === segments.length - 1) {
				const node = cursor.children.get(seg);
				node.name = f.name;
				node.entry = f;
			}
			cursor = cursor.children.get(seg);
		}
	}
	const flatten = (node) => {
		const list = [];
		const sorted = [...node.children.values()].sort((a, b) =>
			String(a.seg || "").localeCompare(String(b.seg || ""), undefined, { numeric: true }),
		);
		for (const child of sorted) {
			list.push({
				name: child.name,
				label: child.label,
				seg: child.seg,
				depth: child.depth,
				hasChildren: child.children.size > 0,
			});
			if (folderPickerExpanded.value.has(child.label) || folderPickerSearch.value) {
				list.push(...flatten(child));
			}
		}
		return list;
	};
	return flatten(root);
});

const folderTreeFiltered = computed(() => {
	const q = folderPickerSearch.value.trim().toLowerCase();
	if (!q) return folderTree.value;
	return folderTree.value.filter((n) => n.label.toLowerCase().includes(q));
});

function openFolderPicker() {
	folderPickerSearch.value = "";
	if (targetFolderEntry.value?.label) {
		const segs = targetFolderEntry.value.label.split("/");
		const next = new Set(folderPickerExpanded.value);
		for (let i = 1; i < segs.length; i++) {
			next.add(segs.slice(0, i).join("/"));
		}
		folderPickerExpanded.value = next;
	}
	folderPickerOpen.value = true;
}

function closeFolderPicker() {
	folderPickerOpen.value = false;
}

function toggleFolderNode(label) {
	const next = new Set(folderPickerExpanded.value);
	if (next.has(label)) {
		next.delete(label);
	} else {
		next.add(label);
	}
	folderPickerExpanded.value = next;
}

function pickFolder(name) {
	if (!name) return;
	targetFolder.value = name;
	folderPickerOpen.value = false;
}

const loadProjects = async () => {
	try {
		const res = await call({ method: "portal_app.api.projects.list_projects" });
		projects.value = res.projects || [];
		if (!project.value && projects.value.length) {
			project.value = projects.value[0].name;
		}
	} catch (e) {
		console.error(e);
	}
};

const loadFiles = async () => {
	if (!project.value) {
		files.value = [];
		return;
	}
	loading.value = true;
	fileListActionError.value = "";
	try {
		const res = await call({
			method: "portal_app.api.files.list_project_files",
			args: { project: project.value },
		});
		files.value = res.files || [];
		settings.value = res.settings || {};
		projectRootPath.value = res.folders?.project_root || "";
		folders.value = res.folders?.subfolders || [];
		const deepLinkFolder = String(route.query.folder || "");
		if (deepLinkFolder && folders.value.some((f) => f.name === deepLinkFolder)) {
			folderFilter.value = deepLinkFolder;
			targetFolder.value = deepLinkFolder;
			if (String(route.query.share || "") === "1" && canShareFolder.value) {
				// Hopped over from ProjectDetail's Share button — open the modal directly.
				await nextTick();
				openShareModal(deepLinkFolder);
			}
		} else {
			folderFilter.value = "";
			if (!targetFolder.value || !folders.value.some((f) => f.name === targetFolder.value)) {
				targetFolder.value = folders.value[0]?.name || "";
			}
		}
	} catch (e) {
		console.error(e);
	} finally {
		loading.value = false;
	}
};

onMounted(async () => {
	try {
		await refreshPortalCapabilities();
	} catch (e) {
		console.error(e);
	}
	await loadProjects();
	await loadFiles();
	loadFileTypes();
	scrollToPortalHighlight();
});

watch(project, loadFiles);

watch(
	() => [route.query.highlight, loading.value],
	() => {
		if (!loading.value) scrollToPortalHighlight();
	},
);

function resetShareUi() {
	shareEpoch.value += 1;
	shareInfo.value = "";
	shareError.value = "";
	shareBusy.value = false;
	shareBusyFor.value = "";
	sharePanelOpen.value = false;
}

watch([project, targetFolder, folderFilter], () => {
	resetShareUi();
});
watch(project, () => clearFileSelection());

// Reset main-tree expansion when switching projects, then auto-open the new project root so
// top-level subfolders are immediately visible (a fully-collapsed root would feel empty).
watch(projectRootPath, (root) => {
	const next = new Set();
	if (root) next.add(`__root__:${root}`);
	folderTreeExpanded.value = next;
});

watch(folderFilter, async (newPath, oldPath) => {
	if (!newPath || newPath === oldPath) return;
	if (isCustomerPortalUser.value) return;
	// Picking a folder card always means "I want to do something with this folder",
	// so make it the upload target and slide the upload zone into view.
	if (newPath !== projectRootPath.value) {
		targetFolder.value = newPath;
	}
	await nextTick();
	uploadCardRef.value?.scrollIntoView({ behavior: "smooth", block: "start" });
});

watch(
	() => route.query.project,
	(p) => {
		if (p) project.value = p;
	},
);

function apiErr(e) {
	const body = e?.responseBody;
	if (body?._server_messages) {
		try {
			const arr = JSON.parse(body._server_messages);
			if (arr.length) return JSON.parse(arr[0]).message || arr[0];
		} catch {
			return String(body._server_messages[0]);
		}
	}
	return body?.message || body?.exc || "Upload failed.";
}

// Stage the dropped/picked files into the confirmation modal. The actual upload only runs when
// the user clicks "Upload" in `confirmUploadAndRun` — this is what gives them a chance to rename,
// re-categorize (target folder), or set a date per file.
function handleFiles(fileList) {
	if (!fileList?.length) return;
	if (!project.value) {
		uploadError.value =
			"Pick a project from the dropdown above before uploading. The page reloads the project list in the background — refresh once if it stays empty.";
		return;
	}
	if (!targetFolder.value) {
		uploadError.value = "Pick a target subfolder before uploading.";
		return;
	}
	uploadError.value = "";
	uploadInfo.value = "";
	const today = todayIso();
	pendingUploads.value = Array.from(fileList).map((f) => {
		const { base, ext } = splitFileName(f.name);
		const category = targetFolder.value;
		const [fileClassification, fileSubCategory] = classifyFile(f.name, "");
		return {
			originalFile: f,
			base,
			ext,
			name: buildAutoName(base, ext, today, categoryToSlug(category)),
			category,
			date: today,
			nameEdited: false,
			fileType: detectFileType(f.name),
			fileClassification,
			fileSubCategory,
			documentType: "",
		};
	});
	confirmUploadOpen.value = true;
}

function cancelUploadConfirm() {
	if (uploadBusy.value) return;
	confirmUploadOpen.value = false;
	pendingUploads.value = [];
	pendingFolder.value = null;
}

function runConfirm() {
	return isFolderMode.value ? confirmFolderUploadAndRun() : confirmUploadAndRun();
}

async function _prepareWrapper(category, isoDate, fileBase = "") {
	const nameWithoutSeries = buildWrapperName(category, isoDate, fileBase);
	const prep = await call({
		method: "portal_app.api.files.prepare_folder_upload",
		type: "POST",
		args: {
			project: project.value,
			target_folder: category,
			folder_name: nameWithoutSeries,
		},
	});
	if (!prep?.folder_name) throw new Error("Folder reservation failed.");
	return {
		fileDoc: prep.folder_name,
		label: prep.folder_label || prep.file_name || nameWithoutSeries,
		baseName: prep.file_name || nameWithoutSeries,
		series: prep.series || "01",
		version: prep.version || 1,
	};
}

async function confirmUploadAndRun() {
	if (!pendingUploads.value.length) return;
	for (const r of pendingUploads.value) {
		if (!String(r.name || "").trim()) {
			uploadError.value = "Each file needs a name.";
			return;
		}
		if (!r.category) {
			uploadError.value = "Each file needs a category (target folder).";
			return;
		}
	}
	uploadBusy.value = true;
	uploadError.value = "";
	uploadInfo.value = "";
	let lastFolderLabel = "";
	let uploadedCount = 0;
	try {
		// External-only uploads bypass the wrap-in-folder flow (no ERPNext File doc created).
		if (destination.value === "external") {
			for (const r of pendingUploads.value) {
				const renamed = new File([r.originalFile], r.name.trim(), {
					type: r.originalFile.type,
					lastModified: r.originalFile.lastModified,
				});
				await uploadFile("portal_app.api.files.upload_project_file", renamed, {
					project: project.value,
					is_private: isPrivateUpload.value ? "1" : "0",
					destination: destination.value,
					external_provider: externalProvider.value,
					target_folder: r.category,
					file_type: r.fileType || "",
				});
				uploadedCount += 1;
			}
			uploadInfo.value = "Uploaded to external integration endpoint. ERPNext File was not created.";
		} else {
			// Group rows by category so each category gets its own dated wrapping folder.
			const byCategory = new Map();
			for (const r of pendingUploads.value) {
				if (!byCategory.has(r.category)) byCategory.set(r.category, []);
				byCategory.get(r.category).push(r);
			}
			const today = todayIso();
			for (const [category, rows] of byCategory) {
				// Include filename in wrapper when only one file goes into this category.
				const fileBase = rows.length === 1 ? (rows[0].base || "") : "";
				const wrapper = await _prepareWrapper(category, today, fileBase);
				lastFolderLabel = wrapper.label;
				for (const r of rows) {
					const renamed = new File([r.originalFile], r.name.trim(), {
						type: r.originalFile.type,
						lastModified: r.originalFile.lastModified,
					});
					await uploadFile("portal_app.api.files.upload_project_file", renamed, {
						project: project.value,
						is_private: isPrivateUpload.value ? "1" : "0",
						destination: destination.value,
						external_provider: externalProvider.value,
						target_folder: wrapper.fileDoc,
						relative_path: "",
						file_type: r.fileType || "",
						file_classification: r.fileClassification || "",
						file_sub_category: r.fileSubCategory || "",
						document_type: r.documentType || "",
					});
					uploadedCount += 1;
				}
			}
			await loadFiles();
			if (uploadedCount) {
				const first = pendingUploads.value[0];
				const firstName = first?.name?.trim() || "";
				const when = fmtDate(new Date().toISOString());
				if (uploadedCount === 1) {
					uploadInfo.value = `Uploaded "${firstName}" to ${lastFolderLabel} on ${when}.`;
				} else {
					uploadInfo.value = `Uploaded ${uploadedCount} files (incl. "${firstName}") to ${lastFolderLabel} on ${when}.`;
				}
			}
		}
		setTimeout(() => (uploadInfo.value = ""), 6000);
		confirmUploadOpen.value = false;
		pendingUploads.value = [];
	} catch (e) {
		uploadError.value = apiErr(e);
	} finally {
		uploadBusy.value = false;
	}
}

// Suggest the best matching ERPNext subfolder for a given classification category.
function suggestFolderForCategory(classification) {
	const lower = (classification || "").toLowerCase();
	const HINTS = [
		{ keys: ["presentation"],              search: ["presentation"] },
		{ keys: ["drawing", "layout"],         search: ["drawing", "layout", "dwg", "cad"] },
		{ keys: ["3d model"],                  search: ["sketch", "3d", "model", "revit", "lumion"] },
		{ keys: ["feasibility", "area"],       search: ["feasibility", "area", "calculation"] },
		{ keys: ["editable design", "source"], search: ["editable", "source", "design"] },
		{ keys: ["rendering", "image"],        search: ["perspective", "render", "image", "visual"] },
		{ keys: ["submission"],                search: ["submission", "transmittal"] },
	];
	// Only match against direct category folders (depth ≤ 2) so deep subfolders like
	// "02-CONCEPT/01-CONCEPT STUDIES/09-PROJECT RENDERS" don't steal the match from
	// the intended "02-CONCEPT/03-PERSPECTIVES".
	const categoryFolders = folders.value.filter((f) => (f.label || "").split("/").length <= 2);
	for (const { keys, search } of HINTS) {
		if (keys.some((k) => lower.includes(k))) {
			const match = categoryFolders.find((f) =>
				search.some((s) => (f.label || "").toLowerCase().includes(s)),
			);
			if (match) return match.name;
		}
	}
	return categoryFolders[0]?.name || folders.value[0]?.name || targetFolder.value || "";
}

// Stage folder upload → show confirmation dialog with editable name
function doFolderUpload(entries) {
	const items = (entries || []).filter((e) => e.file);
	if (!items.length) return;
	if (!project.value) { uploadError.value = "Pick a project before uploading."; return; }
	if (!targetFolder.value) { uploadError.value = "Click a destination subfolder first, then drop your folder."; return; }

	const firstSeg = (p) => String(p || "").split("/")[0] || "";
	const roots = new Set(items.map((it) => firstSeg(it.relativePath || it.file.webkitRelativePath || "")).filter(Boolean));
	if (roots.size !== 1) { uploadError.value = "Select exactly one folder."; return; }
	const sourceName = [...roots][0];

	const files = items.map((it) => {
		const p = String(it.relativePath || it.file.webkitRelativePath || "");
		const trimmed = p.startsWith(sourceName + "/") ? p.slice(sourceName.length + 1) : p;
		const slashIdx = trimmed.lastIndexOf("/");
		const [classification, subCategory] = classifyFile(it.file.name, "");
		return {
			file: it.file,
			relativeDir: slashIdx >= 0 ? trimmed.slice(0, slashIdx) : "",
			classification,
			subCategory,
		};
	});

	const sourceSlug = sourceName.replace(/[^a-zA-Z0-9_]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
	// wrapperName is the date+name part only — backend prepends the series number (01, 02…)
	const wrapperName = buildWrapperName(targetFolder.value, todayIso(), sourceSlug);

	pendingFolder.value = { sourceName, wrapperName, targetFolder: targetFolder.value, files };
	pendingUploads.value = [];
	uploadError.value = "";
	uploadInfo.value = "";
	confirmUploadOpen.value = true;
}

async function confirmFolderUploadAndRun() {
	const f = pendingFolder.value;
	if (!f) return;
	if (!f.targetFolder) { uploadError.value = "Select a destination subfolder."; return; }
	if (!String(f.wrapperName || "").trim()) { uploadError.value = "Enter a folder name."; return; }

	uploadBusy.value = true;
	uploadError.value = "";
	uploadInfo.value = "";
	let done = 0;
	try {
		const prep = await call({
			method: "portal_app.api.files.prepare_folder_upload",
			type: "POST",
			args: { project: project.value, target_folder: f.targetFolder, folder_name: f.wrapperName.trim() },
		});
		if (!prep?.folder_name) throw new Error("Folder creation failed.");
		const wrapperDoc = prep.folder_name;
		for (const e of f.files) {
			uploadInfo.value = `Uploading "${f.wrapperName}" — ${done}/${f.files.length}…`;
			await uploadFile("portal_app.api.files.upload_project_file", e.file, {
				project: project.value,
				is_private: isPrivateUpload.value ? "1" : "0",
				destination: destination.value,
				external_provider: externalProvider.value,
				target_folder: wrapperDoc,
				relative_path: e.relativeDir || "",
				file_classification: e.classification || "",
				file_sub_category: e.subCategory || "",
			});
			done++;
		}
		await loadFiles();
		uploadInfo.value = `"${f.wrapperName}" uploaded — ${f.files.length} file${f.files.length === 1 ? "" : "s"}.`;
		setTimeout(() => (uploadInfo.value = ""), 6000);
		confirmUploadOpen.value = false;
		pendingFolder.value = null;
	} catch (e) {
		uploadError.value = apiErr(e);
	} finally {
		uploadBusy.value = false;
	}
}


function onFileInput(e) {
	const input = e.target;
	handleFiles(input.files);
	input.value = "";
}
function onFolderInput(e) {
	const input = e.target;
	const list = Array.from(input.files || []);
	const entries = list.map((f) => ({ file: f, relativePath: f.webkitRelativePath || "" }));
	doFolderUpload(entries);
	if (input) input.value = "";
}

// Drag-and-drop directly onto a folder card — uploads land in that folder.
const dropTargetFolder = ref("");
function onFolderDragOver(e, f) {
	if (!e.dataTransfer || !Array.from(e.dataTransfer.types || []).includes("Files")) return;
	if (isCustomerPortalUser.value || !project.value) return;
	if (f.isRoot && !canShareFolder.value) return;
	e.dataTransfer.dropEffect = "copy";
	dropTargetFolder.value = f.name;
}
function onFolderDragLeave(e, f) {
	if (dropTargetFolder.value === f.name) dropTargetFolder.value = "";
}
async function onFolderDrop(e, f) {
	if (isCustomerPortalUser.value) return;
	dropTargetFolder.value = "";
	const dt = e.dataTransfer;
	if (!dt || !project.value) return;
	// Temporarily switch the upload target to this folder, run the upload, then leave it set
	// (matches the auto-set-target behaviour when clicking a folder card).
	targetFolder.value = f.name;
	if (await _dropContainsDirectory(dt)) {
		const collected = await collectFromDataTransfer(dt);
		doFolderUpload(collected);
		return;
	}
	await handleFiles(dt.files);
}

async function onDrop(e) {
	dragOver.value = false;
	const dt = e.dataTransfer;
	if (!dt) return;
	if (await _dropContainsDirectory(dt)) {
		const collected = await collectFromDataTransfer(dt);
		doFolderUpload(collected);
		return;
	}
	handleFiles(dt.files);
}

// Collect all files recursively from a FileSystemDirectoryHandle (showDirectoryPicker API)
async function collectFromDirHandle(handle, pathPrefix) {
	const results = [];
	async function walk(dir, prefix) {
		for await (const [name, entry] of dir.entries()) {
			if (entry.kind === "file") {
				const file = await entry.getFile();
				results.push({ file, relativePath: prefix + name });
			} else if (entry.kind === "directory") {
				await walk(entry, prefix + name + "/");
			}
		}
	}
	await walk(handle, pathPrefix + "/");
	return results;
}

async function onFolderButtonClick() {
	uploadError.value = "";
	// Modern API: proper folder picker in Chrome/Edge/Safari
	if (window.showDirectoryPicker) {
		try {
			const dirHandle = await window.showDirectoryPicker({ mode: "read" });
			const entries = await collectFromDirHandle(dirHandle, dirHandle.name);
			if (entries.length) doFolderUpload(entries);
		} catch (e) {
			if (e.name !== "AbortError") uploadError.value = String(e.message || e);
		}
		return;
	}
	// Firefox fallback: webkitdirectory (navigate INTO folder then click Open)
	folderInput.value?.click();
}

// ── ZIP upload ──────────────────────────────────────────────────────────────
const zipInput = ref(null);
const zipBusy = ref(false);
const zipMsg = ref("");

async function onZipInput(e) {
	const file = e.target.files?.[0];
	if (e.target) e.target.value = "";
	if (!file) return;
	if (!targetFolder.value) {
		uploadError.value = "Select a destination subfolder first.";
		return;
	}
	const destLabel = folderLabelByName.value[targetFolder.value] || targetFolder.value;
	if (!confirm(`Upload and extract "${file.name}" into:\n  ${destLabel}\n\nAll files inside the ZIP will be created there, preserving the folder structure.`)) return;
	zipBusy.value = true;
	uploadError.value = "";
	zipMsg.value = "";
	try {
		const res = await uploadFile(
			"portal_app.api.files.upload_project_files_zip",
			file,
			{ project: project.value, target_folder: targetFolder.value },
		);
		zipMsg.value = `ZIP extracted: ${res?.uploaded ?? 0} file(s) uploaded${res?.failed ? `, ${res.failed} failed` : ""}.`;
		await loadFilesAndFolders();
		setTimeout(() => (zipMsg.value = ""), 6000);
	} catch (err) {
		const body = err?.responseBody;
		uploadError.value = body?._server_messages
			? (() => { try { return JSON.parse(JSON.parse(body._server_messages)[0]).message; } catch { return body._server_messages; } })()
			: body?.message || String(err?.message || "ZIP upload failed.");
	} finally {
		zipBusy.value = false;
	}
}

async function createShareLinkForFolder(folderPath) {
	if (!project.value || !folderPath) return;
	if (!canShareFolder.value) {
		shareError.value =
			"You need project manager access on this project to create share links (portal project manager, Projects Manager, or System Manager).";
		shareInfo.value = "";
		await nextTick();
		document.getElementById("portal-share-result")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
		return;
	}
	const epochAtStart = shareEpoch.value;
	shareBusy.value = true;
	shareBusyFor.value = folderPath;
	shareError.value = "";
	shareInfo.value = "";
	try {
		const res = await call({
			method: "portal_app.api.files.create_folder_share_link",
			type: "POST",
			args: {
				project: project.value,
				folder_path: folderPath,
				expires_days: shareDays.value,
			},
		});
		if (epochAtStart !== shareEpoch.value) return;
		shareInfo.value = res?.url || "";
		sharePanelOpen.value = true;
		try {
			await navigator.clipboard.writeText(shareInfo.value);
		} catch {
			// ignore clipboard failures
		}
		await nextTick();
		document.getElementById("portal-share-result")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
	} catch (e) {
		if (epochAtStart !== shareEpoch.value) return;
		shareError.value = apiErr(e);
		sharePanelOpen.value = true;
		await nextTick();
		document.getElementById("portal-share-result")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
	} finally {
		shareBusy.value = false;
		shareBusyFor.value = "";
	}
}

function createShareLink() {
	return createShareLinkForFolder(targetFolder.value);
}

// Share modal supports two target kinds: a folder, or a single file. The state
// is kept lean — `shareModalFolder` holds either a folder path or a File doc
// name; `shareModalKind` distinguishes them so we hit the right backend.
const shareModalKind = ref("folder"); // "folder" | "file"

async function openShareModal(folderPath) {
	if (!folderPath || !canShareFolder.value) return;
	shareModalKind.value = "folder";
	shareModalFolder.value = folderPath;
	const entry = folderEntries.value.find((f) => f.name === folderPath);
	shareModalLabel.value = entry?.label || folderPath;
	shareModalOpen.value = true;
	shareModalError.value = "";
	shareModalOk.value = "";
	userSearchQ.value = "";
	userSearchHits.value = [];
	await loadFolderShares();
}

async function openShareModalForFile(file) {
	if (!file?.name || !canShareFolder.value) return;
	shareModalKind.value = "file";
	shareModalFolder.value = file.name;
	shareModalLabel.value = file.file_name || file.name;
	shareModalOpen.value = true;
	shareModalError.value = "";
	shareModalOk.value = "";
	userSearchQ.value = "";
	userSearchHits.value = [];
	await loadFolderShares();
}

function closeShareModal() {
	shareModalOpen.value = false;
	shareModalFolder.value = "";
	shareModalLabel.value = "";
	shareModalKind.value = "folder";
	folderShares.value = [];
	userSearchQ.value = "";
	userSearchHits.value = [];
	shareModalError.value = "";
	shareModalOk.value = "";
}

async function loadFolderShares() {
	if (!project.value || !shareModalFolder.value) return;
	shareModalLoading.value = true;
	try {
		const res = await call({
			method: "portal_app.api.files.list_folder_shares",
			args: { project: project.value, folder_path: shareModalFolder.value },
		});
		folderShares.value = res?.shares || [];
		shareTrackingAvailable.value = res?.tracking_available !== false;
	} catch (e) {
		shareModalError.value = apiErr(e);
		folderShares.value = [];
		shareTrackingAvailable.value = true;
	} finally {
		shareModalLoading.value = false;
	}
}

async function runUserSearch(text) {
	const t = String(text || "").trim();
	userSearchBusy.value = true;
	try {
		const res = await call({
			method: "portal_app.api.projects.search_portal_users",
			args: { txt: t },
		});
		const hits = Array.isArray(res) ? res : res?.message || [];
		const alreadyShared = new Set(userSharesForFolder.value.map((s) => s.user));
		userSearchHits.value = hits.filter((u) => !alreadyShared.has(u.name));
	} catch (e) {
		userSearchHits.value = [];
	} finally {
		userSearchBusy.value = false;
	}
}

watch(userSearchQ, (q) => {
	clearTimeout(userSearchTimer);
	userSearchTimer = setTimeout(() => runUserSearch(q), 200);
});

function onUserSearchFocus() {
	// Pop the dropdown immediately with the latest matches (or top-N when empty).
	if (!userSearchHits.value.length) runUserSearch(userSearchQ.value);
}

async function shareWithUser(uid) {
	if (!project.value || !shareModalFolder.value || !uid) return;
	shareModalSaving.value = true;
	shareModalError.value = "";
	shareModalOk.value = "";
	try {
		const isFile = shareModalKind.value === "file";
		await call({
			method: isFile
				? "portal_app.api.files.share_file_with_user"
				: "portal_app.api.files.share_folder_with_user",
			type: "POST",
			args: isFile
				? {
					project: project.value,
					file_name: shareModalFolder.value,
					user_id: uid,
					expires_days: userExpiryDays.value,
					notify: notifyOnShare.value ? 1 : 0,
				}
				: {
					project: project.value,
					folder_path: shareModalFolder.value,
					user_id: uid,
					expires_days: userExpiryDays.value,
					notify: notifyOnShare.value ? 1 : 0,
				},
		});
		shareModalOk.value = "Access granted.";
		userSearchQ.value = "";
		userSearchHits.value = [];
		await loadFolderShares();
		setTimeout(() => (shareModalOk.value = ""), 2200);
	} catch (e) {
		shareModalError.value = apiErr(e);
	} finally {
		shareModalSaving.value = false;
	}
}

async function revokeShare(shareName) {
	if (!shareName) return;
	if (!window.confirm("Revoke this access? The user/link will lose access immediately.")) return;
	shareModalSaving.value = true;
	shareModalError.value = "";
	try {
		await call({
			method: "portal_app.api.files.revoke_folder_share",
			type: "POST",
			args: { share_name: shareName },
		});
		shareModalOk.value = "Access revoked.";
		await loadFolderShares();
		setTimeout(() => (shareModalOk.value = ""), 2200);
	} catch (e) {
		shareModalError.value = apiErr(e);
	} finally {
		shareModalSaving.value = false;
	}
}

async function createOrCopyShareLink() {
	if (!project.value || !shareModalFolder.value) return;
	shareModalSaving.value = true;
	shareModalError.value = "";
	shareModalOk.value = "";
	try {
		const res = await call({
			method: "portal_app.api.files.create_folder_share_link",
			type: "POST",
			args: {
				project: project.value,
				folder_path: shareModalFolder.value,
				expires_days: linkExpiryDays.value,
			},
		});
		const url = res?.url || "";
		try {
			await navigator.clipboard.writeText(url);
			shareModalOk.value = "Link created and copied to clipboard.";
		} catch {
			shareModalOk.value = "Link created.";
		}
		await loadFolderShares();
		setTimeout(() => (shareModalOk.value = ""), 2500);
	} catch (e) {
		shareModalError.value = apiErr(e);
	} finally {
		shareModalSaving.value = false;
	}
}

async function copyShareLink(url) {
	if (!url) return;
	try {
		await navigator.clipboard.writeText(url);
		shareModalOk.value = "Link copied to clipboard.";
		setTimeout(() => (shareModalOk.value = ""), 2000);
	} catch {
		shareModalOk.value = url;
	}
}

function openRenameSubfolder(folderPath) {
	if (!folderPath || folderPath === projectRootPath.value) return;
	renameFolderPath.value = folderPath;
	const parts = String(folderPath).replace(/\\/g, "/").split("/");
	renameNewName.value = parts[parts.length - 1] || "";
	renameError.value = "";
	renameOpen.value = true;
}

function closeRenameModal() {
	renameOpen.value = false;
	renameFolderPath.value = "";
	renameNewName.value = "";
	renameError.value = "";
}

async function confirmRenameSubfolder() {
	if (!project.value || !renameFolderPath.value) return;
	renameBusy.value = true;
	renameError.value = "";
	try {
		const res = await call({
			method: "portal_app.api.files.rename_project_subfolder",
			type: "POST",
			args: {
				project: project.value,
				folder_path: renameFolderPath.value,
				new_folder_name: renameNewName.value,
			},
		});
		const oldP = res?.old;
		const newP = res?.new;
		if (oldP && newP) {
			if (folderFilter.value === oldP) folderFilter.value = newP;
			if (targetFolder.value === oldP) targetFolder.value = newP;
		}
		closeRenameModal();
		await loadFiles();
	} catch (e) {
		renameError.value = apiErr(e);
	} finally {
		renameBusy.value = false;
	}
}

async function deleteProjectFile(f) {
	if (!f?.name || f.is_folder) return;
	fileListActionError.value = "";
	if (!window.confirm(`Delete "${f.file_name}"? This removes the ERPNext File record and its attachment.`)) return;
	deleteBusyName.value = f.name;
	try {
		await call({
			method: "portal_app.api.files.delete_project_file",
			type: "POST",
			args: { file_name: f.name },
		});
		await loadFiles();
	} catch (e) {
		fileListActionError.value = apiErr(e);
	} finally {
		deleteBusyName.value = "";
	}
}
</script>

<template>
	<div ref="filesScrollRoot" class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<!-- Floating scroll-to-top / scroll-to-bottom controls -->
		<div class="pointer-events-none fixed bottom-6 right-6 z-30 flex flex-col gap-2">
			<button
				type="button"
				class="pointer-events-auto flex h-10 w-10 items-center justify-center rounded-full border border-[color:var(--portal-border)] shadow-lg backdrop-blur transition hover:bg-[color:var(--portal-accent-soft)] hover:text-[color:var(--portal-accent-strong)]" style="background:var(--portal-surface);color:var(--portal-text)"
				title="Scroll to top"
				@click="scrollFilesPage('top')"
			>
				<FeatherIcon name="chevrons-up" class="h-4 w-4" />
			</button>
			<button
				type="button"
				class="pointer-events-auto flex h-10 w-10 items-center justify-center rounded-full border border-[color:var(--portal-border)] shadow-lg backdrop-blur transition hover:bg-[color:var(--portal-accent-soft)] hover:text-[color:var(--portal-accent-strong)]" style="background:var(--portal-surface);color:var(--portal-text)"
				title="Scroll to bottom"
				@click="scrollFilesPage('bottom')"
			>
				<FeatherIcon name="chevrons-down" class="h-4 w-4" />
			</button>
		</div>
		<div class="mx-auto max-w-5xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative">
					<span class="portal-pill portal-pill-accent">
						<FeatherIcon name="paperclip" class="h-3 w-3" />
						Files
					</span>
					<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
						Project files
					</h1>
					<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
						Files attached to ERPNext Project records. Frappe Drive / Google Drive / BIM 360 flags live in
						<strong class="text-[color:var(--portal-text)]">Portal Project Settings</strong> (desk).
					</p>
				</div>
			</div>

			<router-link
				v-if="canEditFolderTemplate"
				to="/file-tools"
				custom
				v-slot="{ navigate }"
			>
				<button
					type="button"
					class="portal-callout flex w-full items-center justify-between gap-3 text-left transition hover:shadow-md"
					@click="navigate"
					@keydown.enter="navigate"
				>
					<span class="flex items-center gap-3">
						<span
							class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
							style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
						>
							<FeatherIcon name="sliders" class="h-4 w-4" />
						</span>
						<span class="min-w-0">
							<span class="block text-sm font-semibold text-[color:var(--portal-text)]">
								Manage the company-wide folder template
							</span>
							<span class="block text-xs text-[color:var(--portal-muted)]">
								Edit subfolder paths or import a ZIP structure on the dedicated File tools page (Auditor only).
							</span>
						</span>
					</span>
					<FeatherIcon name="arrow-up-right" class="h-4 w-4 text-[color:var(--portal-muted)]" />
				</button>
			</router-link>

			<div class="portal-card-strong p-4">
				<label class="portal-section-title mb-2 block">Active project</label>
				<div class="flex flex-wrap items-center gap-3">
					<div class="relative min-w-[260px] flex-1">
						<FeatherIcon
							name="search"
							class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
						/>
						<input
							type="text"
							:value="projectDropdownOpen ? projectSearch : selectedProjectLabel"
							:placeholder="selectedProjectLabel || 'Search projects…'"
							class="portal-input pl-9"
							autocomplete="off"
							@focus="onProjectInputFocus"
							@blur="onProjectBlur"
							@input="(e) => { projectSearch = e.target.value; projectDropdownOpen = true; }"
						/>
						<div
							v-if="projectDropdownOpen && filteredProjects.length"
							class="absolute left-0 right-0 top-full z-50 mt-1 max-h-72 overflow-y-auto rounded-xl border border-[color:var(--portal-border)] shadow-lg" style="background:var(--portal-surface-dropdown)"
						>
							<button
								v-for="p in filteredProjects"
								:key="p.name"
								type="button"
								class="flex w-full items-start gap-2 px-3 py-2 text-left text-sm transition hover:bg-[color:var(--portal-accent-soft)]"
								:class="p.name === project ? 'bg-[color:var(--portal-accent-soft)] font-semibold text-[color:var(--portal-accent-strong)]' : 'text-[color:var(--portal-text)]'"
								@mousedown.prevent="selectProject(p)"
							>
								<FeatherIcon name="folder" class="mt-0.5 h-3.5 w-3.5 shrink-0 text-[color:var(--portal-muted)]" />
								<span class="min-w-0">
									<span class="block truncate font-medium">{{ p.project_name }}</span>
									<span class="block truncate text-[11px] text-[color:var(--portal-muted)]">{{ p.name }}</span>
								</span>
							</button>
							<div v-if="!filteredProjects.length" class="px-3 py-3 text-sm text-[color:var(--portal-muted)]">
								No projects match "{{ projectSearch }}"
							</div>
						</div>
					</div>
				</div>
			</div>

			<div
				v-if="project && !isCustomerPortalUser"
				id="portal-scroll-file-help"
				class="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-4 text-sm text-emerald-950 shadow-sm"
			>
				<p class="font-semibold text-emerald-900">What you can do on this page</p>
				<ul class="mt-2 list-inside list-disc space-y-1.5 text-xs leading-relaxed text-emerald-900/90">
					<li>
						<strong>Delete</strong> is the last column in the file table below. Project managers (including
						<strong>Projects Manager</strong> and users set as <strong>Portal Project Manager</strong> on the project) can remove any
						file; other team members only see <strong>Delete</strong> on rows where <strong>Owner</strong> is them.
					</li>
					<li v-if="canShareFolder">
						For this project you can use <strong>Share link</strong> and <strong>Rename</strong> on each subfolder card.
					</li>
					<li v-else-if="manageableCount > 0">
						Share/rename subfolders is limited to projects you manage in the portal; pick a managed project to see those
						actions.
					</li>
					<li v-if="canEditFolderTemplate">
						Edit the <strong>default subfolder template</strong> on the dedicated
						<router-link to="/file-tools" class="font-medium underline">File tools</router-link>
						page (Auditor only).
					</li>
				</ul>
				<p class="mt-2 text-[11px] text-emerald-800/80">
					Tip: open
					<router-link to="/profile" class="font-medium underline">Profile</router-link>
					to confirm roles; if you were recently given <strong>Projects Manager</strong>, refresh this page so permissions update.
				</p>
			</div>

			<div v-if="project" class="portal-card-strong p-5">
				<div class="mb-4 flex flex-wrap items-center justify-between gap-2">
					<div>
						<h2 class="flex items-center gap-2 text-base font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="folder-tree" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Project folder &amp; subfolders
						</h2>
						<p class="mt-1 text-xs text-[color:var(--portal-muted)]">
							Pick the project root for all files, or a specific subfolder. Share links and renames match your selection.
						</p>
					</div>
					<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] p-0.5" style="background: var(--portal-bg-dim);">
						<button
							type="button"
							class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition"
							:class="folderView === 'grid' ? 'text-white' : 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'"
							:style="folderView === 'grid' ? 'background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);' : ''"
							@click="folderView = 'grid'"
						>
							<FeatherIcon name="grid" class="h-3 w-3" /> Grid
						</button>
						<button
							type="button"
							class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition"
							:class="folderView === 'list' ? 'text-white' : 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'"
							:style="folderView === 'list' ? 'background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);' : ''"
							@click="folderView = 'list'"
						>
							<FeatherIcon name="list" class="h-3 w-3" /> Tree
						</button>
					</div>
				</div>
				<div v-if="folderView === 'grid'" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<div
						v-for="f in folderTreeView"
						:key="`nav-grid-${f.expandKey || f.name}`"
						class="flex flex-col overflow-hidden rounded-xl border text-sm transition"
						style="background:var(--portal-surface)"
						:class="[
							folderFilter === f.name
								? 'portal-selected-ring bg-[color:var(--portal-accent-soft)]'
								: 'border-[color:var(--portal-border)] hover:border-[color:var(--portal-border-strong)] hover:shadow-md',
							dropTargetFolder === f.name ? 'ring-2 ring-[color:var(--portal-accent)] bg-[color:var(--portal-accent-soft)]' : '',
						]"
						:data-folder="f.name"
						@dragover.prevent="onFolderDragOver($event, f)"
						@dragleave="onFolderDragLeave($event, f)"
						@drop.prevent="onFolderDrop($event, f)"
					>
						<div class="flex items-stretch">
							<button
								v-if="f.hasChildren"
								type="button"
								class="flex w-9 shrink-0 items-center justify-center text-[color:var(--portal-muted)] transition hover:bg-[color:var(--portal-bg)] hover:text-[color:var(--portal-text)]"
								:title="f.expanded ? 'Collapse' : 'Expand'"
								@click.stop="toggleFolderTreeNode(f.expandKey)"
							>
								<FeatherIcon
									:name="f.expanded ? 'chevron-down' : 'chevron-right'"
									class="h-4 w-4"
								/>
							</button>
							<span v-else class="w-9 shrink-0"></span>
							<button
								type="button"
								class="flex-1 px-1 py-3 text-left transition"
								:style="{ paddingLeft: `${Math.max(0, (f.depth || 0) - 1) * 0.6}rem` }"
								@click="folderFilter = f.name"
							>
								<p class="flex items-center gap-1.5 truncate font-medium text-[color:var(--portal-text)]">
									<FeatherIcon
										:name="f.isRoot ? 'folder' : (f.fileCount > 0 ? 'folder' : 'folder-minus')"
										class="h-4 w-4 shrink-0"
										:class="folderFilter === f.name ? 'text-[color:var(--portal-accent)]' : 'text-[color:var(--portal-muted)]'"
									/>
									<span class="truncate">{{ f.leafLabel || f.label }}</span>
								</p>
								<p class="mt-1 text-xs text-[color:var(--portal-muted)]">{{ f.fileCount }} {{ f.fileCount === 1 ? "file" : "files" }}</p>
							</button>
						</div>
						<div
							v-if="!isCustomerPortalUser"
							class="flex flex-wrap justify-end gap-1 border-t border-[color:var(--portal-border)] px-2 py-1.5" style="background:var(--portal-surface-alt)"
						>
							<button
								v-if="canManageProject && !f.isRoot"
								type="button"
								class="rounded-lg px-2 py-1 text-xs font-medium transition hover:bg-white/5 disabled:opacity-50"
								style="color:var(--portal-muted)"
								title="Change this subfolder’s name in ERPNext File (first level only)"
								:disabled="shareBusy || renameBusy"
								@click.stop="openRenameSubfolder(f.name)"
							>
								Rename
							</button>
							<button
								v-if="canShareFolder"
								type="button"
								class="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-[color:var(--portal-accent-strong)] transition hover:bg-[color:var(--portal-accent-soft)]"
								:title="'Manage who can access \'' + f.label + '\''"
								@click.stop="openShareModal(f.name)"
							>
								<FeatherIcon name="share-2" class="h-3 w-3" />
								Share
							</button>
							<span v-else class="px-1 text-xs text-[color:var(--portal-subtle)]" title="Only project managers can share folders.">—</span>
						</div>
					</div>
				</div>
				<div v-else class="overflow-hidden rounded-xl border border-[color:var(--portal-border)]">
					<div
						v-for="f in folderTreeView"
						:key="`nav-list-${f.expandKey || f.name}`"
						class="flex w-full items-stretch border-b border-[color:var(--portal-border)] text-sm last:border-b-0 transition"
						:class="folderFilter === f.name ? 'bg-[color:var(--portal-accent-soft)]' : 'hover:bg-white/5'"
					>
						<div
							class="flex shrink-0 items-center"
							:style="{ paddingLeft: `${0.5 + (f.depth || 0) * 1.1}rem` }"
						>
							<button
								v-if="f.hasChildren"
								type="button"
								class="flex h-7 w-7 items-center justify-center rounded text-[color:var(--portal-muted)] transition hover:bg-white/5 hover:text-[color:var(--portal-text)]"
								:title="f.expanded ? 'Collapse' : 'Expand'"
								@click.stop="toggleFolderTreeNode(f.expandKey)"
							>
								<FeatherIcon
									:name="f.expanded ? 'chevron-down' : 'chevron-right'"
									class="h-3.5 w-3.5"
								/>
							</button>
							<span v-else class="h-7 w-7"></span>
						</div>
						<button
							type="button"
							class="min-w-0 flex-1 px-1 py-2.5 text-left"
							@click="folderFilter = f.name"
						>
							<span class="flex items-center gap-1.5 truncate font-medium text-[color:var(--portal-text)]">
								<FeatherIcon
									name="folder"
									class="h-3.5 w-3.5 shrink-0"
									:class="folderFilter === f.name ? 'text-[color:var(--portal-accent)]' : 'text-[color:var(--portal-muted)]'"
								/>
								<span class="truncate">{{ f.leafLabel || f.label }}</span>
							</span>
							<span class="ml-5 text-xs text-[color:var(--portal-muted)]">{{ f.fileCount }} {{ f.fileCount === 1 ? "file" : "files" }}</span>
						</button>
						<div
							v-if="canShareFolder && !isCustomerPortalUser"
							class="flex shrink-0 items-stretch divide-x divide-[color:var(--portal-border)] border-l border-[color:var(--portal-border)]"
						>
							<button
								v-if="canManageProject && !f.isRoot"
								type="button"
								class="px-2 py-2 text-xs font-medium transition hover:bg-white/5 disabled:opacity-50"
								style="color:var(--portal-muted)"
								title="Rename this subfolder (first level only)"
								:disabled="shareBusy || renameBusy"
								@click.stop="openRenameSubfolder(f.name)"
							>
								Rename
							</button>
							<button
								type="button"
								class="flex items-center gap-1 px-3 py-2 text-xs font-semibold text-[color:var(--portal-accent-strong)] transition hover:bg-[color:var(--portal-accent-soft)]"
								:title="'Manage who can access \'' + f.label + '\''"
								@click.stop="openShareModal(f.name)"
							>
								<FeatherIcon name="share-2" class="h-3 w-3" />
								Share
							</button>
						</div>
						<span
							v-else-if="!isCustomerPortalUser"
							class="flex shrink-0 items-center border-l border-[color:var(--portal-border)] px-2 text-xs text-[color:var(--portal-subtle)]"
							title="Only project managers can share folders."
						>
							—
						</span>
					</div>
				</div>
				<div
					v-if="folderFilter"
					class="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-3 py-2 text-xs"
				>
					<FeatherIcon name="filter" class="h-3.5 w-3.5 text-[color:var(--portal-accent)]" />
					<span class="text-[color:var(--portal-muted)]">Showing files in:</span>
					<span class="flex flex-wrap items-center gap-1 font-medium text-[color:var(--portal-text)]">
						<template v-for="(seg, i) in (folderLabelByName[folderFilter] || folderFilter).split('/')" :key="`crumb-${i}`">
							<span v-if="i > 0" class="text-[color:var(--portal-subtle)]">/</span>
							<span>{{ seg }}</span>
						</template>
					</span>
					<button
						type="button"
						class="ml-auto flex items-center gap-1 rounded-lg px-2 py-1 text-[color:var(--portal-muted)] transition hover:bg-white/5 hover:text-[color:var(--portal-text)]"
						@click="folderFilter = ''"
					>
						<FeatherIcon name="x" class="h-3 w-3" /> Clear filter
					</button>
				</div>
				<div class="mt-3 flex flex-wrap gap-2">
					<button class="portal-btn portal-btn-ghost text-xs" @click="folderFilter = ''">
						<FeatherIcon name="layers" class="h-3.5 w-3.5" />
						Show all files
					</button>
					<button
						class="portal-btn portal-btn-ghost text-xs"
						@click="targetFolder = folderFilter || targetFolder"
					>
						<FeatherIcon name="upload" class="h-3.5 w-3.5" />
						Use this folder for upload
					</button>
				</div>
				<div
					v-if="renameOpen"
					class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
					@click.self="!renameBusy && closeRenameModal()"
				>
					<div class="w-full max-w-md rounded-2xl border border-[color:var(--portal-border)] p-4 shadow-lg" style="background:var(--portal-surface)" @click.stop>
						<h3 class="text-lg font-semibold text-[color:var(--portal-text)]">Rename subfolder</h3>
						<p class="mt-1 text-xs text-[color:var(--portal-muted)]">
							Renames only this folder segment (supports nested folders). Files already stored there keep the new path.
						</p>
						<label class="mt-3 block text-xs font-medium uppercase text-[color:var(--portal-muted)]">New folder name</label>
						<input
							v-model="renameNewName"
							type="text"
							class="mt-1 w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm"
							style="background:var(--portal-bg);color:var(--portal-text)"
							autocomplete="off"
							@keyup.enter="confirmRenameSubfolder"
						/>
						<p v-if="renameError" class="mt-2 text-sm text-red-600">{{ renameError }}</p>
						<div class="mt-4 flex justify-end gap-2">
							<button
								type="button"
								class="portal-btn disabled:opacity-50"
								:disabled="renameBusy"
								@click="closeRenameModal"
							>
								Cancel
							</button>
							<button
								type="button"
								class="portal-btn portal-btn-primary disabled:opacity-50"
								:disabled="renameBusy"
								@click="confirmRenameSubfolder"
							>
								{{ renameBusy ? "Saving…" : "Rename" }}
							</button>
						</div>
					</div>
				</div>
			</div>
			<div v-if="project" class="rounded-2xl border border-[color:var(--portal-border)] p-4 shadow-sm" style="background:var(--portal-surface)">
				<div class="grid gap-3 sm:grid-cols-3">
					<div class="sm:col-span-2">
						<label class="mb-1 block text-xs font-medium uppercase text-[color:var(--portal-muted)]">Search file</label>
						<input
							v-model="fileSearch"
							type="search"
							placeholder="Filter by file name"
							class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm"
							style="background:var(--portal-bg);color:var(--portal-text)"
						/>
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium uppercase text-[color:var(--portal-muted)]">Subfolder filter</label>
						<select v-model="folderFilter" class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm" style="background:var(--portal-bg);color:var(--portal-text)">
							<option value="">All locations</option>
							<option v-if="projectRootPath" :value="projectRootPath">Project folder (all files)</option>
							<option v-for="f in folders" :key="`filter-${f.name}`" :value="f.name">
								{{ folderOptionLabel(f.label) }}
							</option>
						</select>
					</div>
				</div>
			</div>

			<div
				v-if="settings.client_portal_intro"
				class="rounded-2xl border border-[color:var(--portal-accent)]/30 p-4 text-sm text-[color:var(--portal-accent-strong)]"
				style="background:var(--portal-accent-soft)"
			>
				<div class="mb-1 text-xs font-semibold uppercase tracking-wide text-[color:var(--portal-accent)]">Client portal guidance</div>
				<div v-html="settings.client_portal_intro"></div>
			</div>

			<div
				v-if="project && !isCustomerPortalUser"
				ref="uploadCardRef"
				class="portal-card-strong space-y-3 p-5"
			>
				<div class="flex flex-wrap items-stretch gap-3">
					<button
						type="button"
						class="group flex min-w-0 flex-1 items-center gap-3 rounded-2xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-4 py-3 text-left transition hover:border-[color:var(--portal-accent)] hover:bg-white/5"
						@click="openFolderPicker"
					>
						<span
							class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white"
							style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
						>
							<FeatherIcon name="folder" class="h-4 w-4" />
						</span>
						<span class="min-w-0 flex-1">
							<span class="block text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
								Upload to
							</span>
							<span class="block truncate text-sm font-semibold text-[color:var(--portal-text)]">
								{{ targetFolderLeafLabel || "Choose a subfolder…" }}
							</span>
							<span v-if="targetFolderParentLabel" class="block truncate text-[11px] text-[color:var(--portal-muted)]">
								{{ targetFolderParentLabel }}
							</span>
						</span>
						<FeatherIcon name="chevron-down" class="h-4 w-4 shrink-0 text-[color:var(--portal-muted)] transition group-hover:text-[color:var(--portal-text)]" />
					</button>
					<div class="flex shrink-0 items-center gap-2">
						<button
							v-if="canShareFolder && targetFolder"
							class="portal-btn"
							:title="'Share \'' + (folderLabelByName[targetFolder] || targetFolder) + '\''"
							@click="openShareModal(targetFolder)"
						>
							<FeatherIcon name="share-2" class="h-4 w-4" />
							Share
						</button>
						<button
							class="portal-btn"
							:disabled="uploadBusy || zipBusy"
							title="Upload a folder — all contents preserved"
							@click="onFolderButtonClick"
						>
							<FeatherIcon name="folder-plus" class="h-4 w-4" />
							Upload folder
						</button>
						<button
							class="portal-btn"
							:disabled="!targetFolder || uploadBusy || zipBusy"
							title="Upload a ZIP file — extracts folder structure into the selected destination"
							@click="zipInput?.click()"
						>
							<FeatherIcon name="archive" class="h-4 w-4" />
							{{ zipBusy ? "Extracting…" : "Upload ZIP" }}
						</button>
						<button
							class="portal-btn portal-btn-primary"
							:disabled="!targetFolder || uploadBusy || zipBusy"
							@click="fileInput?.click()"
						>
							<FeatherIcon name="upload" class="h-4 w-4" />
							{{ uploadBusy ? "Uploading…" : "Upload files" }}
						</button>
					</div>
				</div>

				<div
					class="flex min-h-[120px] cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-4 py-6 text-center text-sm transition"
					:class="
						dragOver
							? 'border-[color:var(--portal-accent)] bg-[color:var(--portal-accent-soft)]'
							: 'border-[color:var(--portal-border-strong)] bg-[color:var(--portal-bg)] hover:border-[color:var(--portal-accent)] hover:bg-[color:var(--portal-accent-soft)]'
					"
					@dragover.prevent="dragOver = true"
					@dragleave.prevent="dragOver = false"
					@drop.prevent="onDrop"
					@click="fileInput?.click()"
				>
					<div
						class="flex h-10 w-10 items-center justify-center rounded-xl"
						style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%); color: #fff;"
					>
						<FeatherIcon name="upload-cloud" class="h-5 w-5" />
					</div>
					<p class="font-medium text-[color:var(--portal-text)]">Drop files or a folder here, or click to upload files</p>
					<p class="text-xs text-[color:var(--portal-muted)]">
						Goes into <strong class="text-[color:var(--portal-text)]">{{ folderLabelByName[targetFolder] || targetFolder || "—" }}</strong>
					</p>
					<p class="text-[11px] text-[color:var(--portal-subtle)]">To upload a whole folder, use <strong>Upload folder</strong> button above or drag-and-drop the folder here</p>
					<input ref="fileInput" type="file" class="hidden" multiple @change="onFileInput" />
					<input ref="folderInput" type="file" class="hidden" webkitdirectory directory multiple @change="onFolderInput" />
					<input ref="zipInput" type="file" class="hidden" accept=".zip,application/zip" @change="onZipInput" />
				</div>

				<div class="flex flex-wrap items-center gap-3">
					<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-3 py-1.5 text-sm text-[color:var(--portal-text)]">
						<input v-model="isPrivateUpload" type="checkbox" class="rounded border-gray-300" />
						<FeatherIcon name="lock" class="h-3.5 w-3.5 text-[color:var(--portal-muted)]" />
						Private upload
					</label>
					<button
						type="button"
						class="portal-btn portal-btn-ghost text-xs"
						@click="advancedUploadOpen = !advancedUploadOpen"
					>
						<FeatherIcon :name="advancedUploadOpen ? 'chevron-up' : 'chevron-down'" class="h-3.5 w-3.5" />
						{{ advancedUploadOpen ? "Hide advanced options" : "Advanced options" }}
					</button>
				</div>

				<div v-if="advancedUploadOpen" class="grid gap-3 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-3 sm:grid-cols-2">
					<div>
						<label class="portal-section-title mb-1 block">Store in</label>
						<select v-model="destination" class="portal-input">
							<option value="erpnext">ERPNext File only</option>
							<option value="external">External platform only</option>
							<option value="both">Both ERPNext + External</option>
						</select>
					</div>
					<div v-if="destination !== 'erpnext'">
						<label class="portal-section-title mb-1 block">External provider</label>
						<select v-model="externalProvider" class="portal-input">
							<option value="frappe_drive">Frappe Drive</option>
							<option value="google_drive">Google Drive</option>
							<option value="bim360">BIM 360 / ACC</option>
						</select>
					</div>
				</div>

				<div v-if="uploadBusy && uploadInfo" class="flex items-center gap-3 rounded-xl border border-[color:var(--portal-accent)]/40 px-4 py-3" style="background:var(--portal-accent-soft)">
					<span class="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
					<span class="text-sm font-medium text-[color:var(--portal-accent-strong)]">{{ uploadInfo }}</span>
				</div>
				<p v-if="uploadError" class="text-sm text-red-600">{{ uploadError }}</p>
				<p v-if="!uploadBusy && uploadInfo" class="text-sm text-green-700">{{ uploadInfo }}</p>
				<p v-if="zipMsg" class="text-sm text-green-700">{{ zipMsg }}</p>
			</div>
			<p v-if="project && isCustomerPortalUser" class="rounded-xl border border-[color:var(--portal-border)] p-3 text-sm text-[color:var(--portal-muted)]" style="background:var(--portal-surface-alt)">
				Customer portal users can open files below; uploading is disabled.
			</p>

			<div class="grid gap-3 md:grid-cols-3">
				<div class="rounded-xl border border-[color:var(--portal-border)] p-4 text-sm shadow-sm" style="background:var(--portal-surface)">
					<div class="mb-1 text-xs font-semibold uppercase text-[color:var(--portal-subtle)]">Frappe Drive</div>
					<p class="text-[color:var(--portal-text)]">
						{{ settings.use_frappe_drive ? "Enabled" : "Not enabled" }}
					</p>
					<a
						v-if="driveUrl"
						:href="driveUrl"
						target="_blank"
						rel="noopener"
						class="mt-2 inline-block text-[color:var(--portal-accent-strong)] underline"
					>
						Open Frappe Drive
					</a>
				</div>
				<div class="rounded-xl border border-[color:var(--portal-border)] p-4 text-sm shadow-sm" style="background:var(--portal-surface)">
					<div class="mb-1 text-xs font-semibold uppercase text-[color:var(--portal-subtle)]">Google Drive</div>
					<p class="text-[color:var(--portal-text)]">
						{{ settings.google_drive_enabled ? "Integration enabled (configured by admin)" : "Not enabled" }}
					</p>
					<a
						v-if="googleUrl"
						:href="googleUrl"
						target="_blank"
						rel="noopener"
						class="mt-2 inline-block text-[color:var(--portal-accent-strong)] underline"
					>
						Open Google Drive
					</a>
					<p v-else-if="settings.google_drive_notes" class="mt-2 text-xs text-[color:var(--portal-muted)]">
						{{ settings.google_drive_notes }}
					</p>
				</div>
				<div class="rounded-xl border border-[color:var(--portal-border)] p-4 text-sm shadow-sm" style="background:var(--portal-surface)">
					<div class="mb-1 text-xs font-semibold uppercase text-[color:var(--portal-subtle)]">BIM 360 / ACC</div>
					<p class="text-[color:var(--portal-text)]">
						{{ settings.bim_360_enabled ? "Integration enabled (configured by admin)" : "Not enabled" }}
					</p>
					<a
						v-if="bimUrl"
						:href="bimUrl"
						target="_blank"
						rel="noopener"
						class="mt-2 inline-block text-[color:var(--portal-accent-strong)] underline"
					>
						Open BIM 360 / ACC
					</a>
					<p v-else-if="settings.bim_360_notes" class="mt-2 text-xs text-[color:var(--portal-muted)]">
						{{ settings.bim_360_notes }}
					</p>
				</div>
			</div>

			<div
				v-if="settings.file_access_note"
				class="rounded-xl border border-[color:var(--portal-accent)]/30 p-3 text-sm text-[color:var(--portal-accent-strong)]" style="background:var(--portal-accent-soft)"
			>
				<strong>File policy:</strong> {{ settings.file_access_note }}
			</div>

			<div v-if="loading" class="text-[color:var(--portal-muted)]">Loading…</div>

			<div v-else class="overflow-x-auto rounded-2xl border border-[color:var(--portal-border)] shadow-sm" style="background:var(--portal-surface)">
				<p v-if="fileListActionError" class="border-b border-red-100 bg-red-50 px-4 py-2 text-sm text-red-800">
					{{ fileListActionError }}
				</p>
				<div
					v-if="selectedFileNames.length"
					class="flex flex-wrap items-center justify-between gap-2 border-b border-[color:var(--portal-border)] bg-[color:var(--portal-accent-soft)] px-4 py-2.5 text-xs"
				>
					<span class="font-medium text-[color:var(--portal-accent-strong)]">
						{{ selectedFileNames.length }} file{{ selectedFileNames.length === 1 ? "" : "s" }} selected
					</span>
					<div class="flex items-center gap-2">
						<button class="portal-btn portal-btn-primary text-xs" @click="downloadSelectedZip">
							<FeatherIcon name="download" class="h-3.5 w-3.5" />
							Download as ZIP
						</button>
						<button class="portal-btn portal-btn-ghost text-xs" @click="clearFileSelection">Clear</button>
					</div>
				</div>
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-[color:var(--portal-border)] text-[color:var(--portal-muted)]" style="background: var(--portal-bg-dim);">
							<th class="px-3 py-3 w-9">
								<input
									type="checkbox"
									class="rounded border-gray-300"
									:checked="allVisibleSelected"
									:indeterminate.prop="someVisibleSelected && !allVisibleSelected"
									@change="toggleSelectAllVisible"
								/>
							</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">File</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Size</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Subfolder</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Owner</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Upload date</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Link</th>
							<th v-if="canShareFolder" class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Share</th>
							<th v-if="showFileDeleteColumn" class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Delete</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="f in visibleFiles"
							:key="f.name"
							class="border-b border-[color:var(--portal-border)] transition"
							:class="selectedFileSet.has(f.name) ? 'bg-[color:var(--portal-accent-soft)]' : ''"
						>
							<td class="px-3 py-3">
								<input
									type="checkbox"
									class="rounded border-gray-300"
									:checked="selectedFileSet.has(f.name)"
									@change="toggleFileSelection(f.name)"
								/>
							</td>
							<td class="px-4 py-3">
								{{ f.file_name }}
								<span v-if="f.is_private" class="ml-1 text-xs text-[color:var(--portal-subtle)]">(private)</span>
							</td>
							<td class="px-4 py-3">{{ fmtFileSize(f.file_size) }}</td>
							<td class="px-4 py-3">{{ subfolderLabel(f.folder) }}</td>
							<td class="px-4 py-3">{{ f.owner }}</td>
							<td class="px-4 py-3 whitespace-nowrap">{{ fmtDate(f.creation) }}</td>
							<td class="px-4 py-3">
								<a
									v-if="f.file_url"
									:href="f.file_url"
									target="_blank"
									rel="noopener"
									class="text-[color:var(--portal-accent)] hover:underline"
								>
									Open
								</a>
							</td>
							<td v-if="canShareFolder" class="px-4 py-3">
								<button
									v-if="!f.is_folder"
									type="button"
									class="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-[color:var(--portal-accent-strong)] transition hover:bg-[color:var(--portal-accent-soft)]"
									:title="'Share \'' + f.file_name + '\' with a teammate'"
									@click="openShareModalForFile(f)"
								>
									<FeatherIcon name="share-2" class="h-3 w-3" />
									Share
								</button>
								<span v-else class="text-xs text-[color:var(--portal-subtle)]">—</span>
							</td>
							<td v-if="showFileDeleteColumn" class="px-4 py-3">
								<button
									v-if="canDeleteThisFile(f)"
									type="button"
									class="text-xs font-medium text-red-700 hover:underline disabled:opacity-50"
									:disabled="!!deleteBusyName"
									@click="deleteProjectFile(f)"
								>
									{{ deleteBusyName === f.name ? "Deleting…" : "Delete" }}
								</button>
								<span
									v-else
									class="text-xs text-[color:var(--portal-subtle)]"
									:title="
										f.is_folder
											? 'Folders are not removed from this list.'
											: 'Only a project manager or the file owner can delete this file.'
									"
								>
									—
								</span>
							</td>
						</tr>
					</tbody>
				</table>
				<p v-if="!visibleFiles.length && project" class="p-4 text-center text-[color:var(--portal-muted)]">
					<span v-if="isCustomerPortalUser">No files attached to this project yet.</span>
					<span v-else>No files yet — upload above or attach from the Project form in ERPNext.</span>
				</p>
			</div>
		</div>

		<Teleport to="body">
			<div
				v-if="folderPickerOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="closeFolderPicker"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border border-[color:var(--portal-border)] shadow-2xl portal-anim-in" style="background:var(--portal-surface)">
					<div class="flex items-center justify-between gap-3 border-b border-[color:var(--portal-border)] px-5 py-4">
						<div class="flex items-center gap-2">
							<div
								class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
								style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
							>
								<FeatherIcon name="folder" class="h-4 w-4" />
							</div>
							<div>
								<h2 class="text-base font-semibold text-[color:var(--portal-text)]">Choose folder</h2>
							</div>
						</div>
						<button
							type="button"
							class="rounded-lg p-1.5 transition hover:bg-white/5" style="color:var(--portal-muted)"
							@click="closeFolderPicker"
						>
							<FeatherIcon name="x" class="h-4 w-4" />
						</button>
					</div>
					<div class="px-5 py-3">
						<div class="relative mb-2">
							<FeatherIcon
								name="search"
								class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
							/>
							<input
								v-model="folderPickerSearch"
								type="search"
								class="portal-input pl-9"
								placeholder="Search folders…"
								autofocus
							/>
						</div>
						<div class="max-h-[55vh] overflow-auto rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-1">
							<div
								v-for="node in folderTreeFiltered"
								:key="node.label"
								class="flex items-center gap-1 rounded-lg transition"
								:class="targetFolder === node.name ? 'bg-[color:var(--portal-accent-soft)]' : 'hover:bg-white/5'"
							>
								<button
									v-if="node.hasChildren && !folderPickerSearch"
									type="button"
									class="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[color:var(--portal-muted)] transition hover:text-[color:var(--portal-text)]"
									:style="{ marginLeft: `${(node.depth - 1) * 1.1}rem` }"
									@click.stop="toggleFolderNode(node.label)"
								>
									<FeatherIcon
										:name="folderPickerExpanded.has(node.label) ? 'chevron-down' : 'chevron-right'"
										class="h-3.5 w-3.5"
									/>
								</button>
								<span
									v-else
									class="h-7 w-7 shrink-0"
									:style="{ marginLeft: folderPickerSearch ? '0' : `${(node.depth - 1) * 1.1}rem` }"
								></span>
								<button
									type="button"
									class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition"
									:class="targetFolder === node.name ? 'text-[color:var(--portal-accent-strong)]' : 'text-[color:var(--portal-text)]'"
									@click="pickFolder(node.name)"
								>
									<FeatherIcon
										name="folder"
										class="h-3.5 w-3.5 shrink-0"
										:class="targetFolder === node.name ? 'text-[color:var(--portal-accent)]' : 'text-[color:var(--portal-muted)]'"
									/>
									<span class="truncate" :class="folderPickerSearch ? '' : 'font-medium'">
										<template v-if="folderPickerSearch">{{ node.label }}</template>
										<template v-else>{{ node.seg }}</template>
									</span>
									<FeatherIcon
										v-if="targetFolder === node.name"
										name="check"
										class="ml-auto h-3.5 w-3.5 shrink-0 text-[color:var(--portal-accent)]"
									/>
								</button>
							</div>
							<div
								v-if="folderTreeFiltered.length === 0"
								class="px-3 py-6 text-center text-xs text-[color:var(--portal-muted)]"
							>
								No folders match that search.
							</div>
						</div>
					</div>
					<div class="flex items-center justify-end gap-2 border-t border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-5 py-3">
						<button class="portal-btn" @click="closeFolderPicker">Done</button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="shareModalOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="closeShareModal"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-lg rounded-2xl border border-[color:var(--portal-border)] shadow-2xl portal-anim-in" style="background:var(--portal-surface)">
					<div class="flex items-start justify-between gap-3 border-b border-[color:var(--portal-border)] px-5 py-4">
						<div class="min-w-0">
							<div class="flex items-center gap-2">
								<div
									class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
									style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
								>
									<FeatherIcon :name="shareModalKind === 'file' ? 'file' : 'share-2'" class="h-4 w-4" />
								</div>
								<h2 class="text-base font-semibold text-[color:var(--portal-text)]">
									{{ shareModalKind === "file" ? "Share file" : "Share folder" }}
								</h2>
							</div>
							<p class="mt-1 truncate text-xs text-[color:var(--portal-muted)]">
								{{ shareModalLabel }}
							</p>
						</div>
						<button
							type="button"
							class="rounded-lg p-1.5 transition hover:bg-white/5" style="color:var(--portal-muted)"
							@click="closeShareModal"
						>
							<FeatherIcon name="x" class="h-4 w-4" />
						</button>
					</div>

					<div class="space-y-5 px-5 py-4">
						<div
							v-if="!shareTrackingAvailable && !shareModalLoading"
							class="rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-3 py-2 text-xs text-[color:var(--portal-muted)]"
						>
							<FeatherIcon name="info" class="mr-1 inline h-3 w-3" />
							Using ERPNext native sharing. Per-share expiry and public link sharing become available after the Portal app migration runs (creates the share-tracking doctype). Adding/revoking users still works.
						</div>

						<!-- Add people -->
						<section>
							<p class="portal-section-title mb-2">Add people</p>
							<div class="flex items-center gap-2">
								<div class="relative min-w-0 flex-1">
									<FeatherIcon
										name="search"
										class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
									/>
									<input
										v-model="userSearchQ"
										type="search"
										class="portal-input pl-9"
										placeholder="Search by email, username, or full name"
										:disabled="shareModalSaving"
										@focus="onUserSearchFocus"
									/>
								</div>
								<div v-if="shareTrackingAvailable" class="flex shrink-0 items-center gap-1">
									<label class="text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
										Days
									</label>
									<input
										v-model.number="userExpiryDays"
										type="number"
										min="1"
										max="365"
										class="portal-input w-16 px-2"
									/>
								</div>
							</div>
							<label class="mt-2 flex items-center gap-2 text-xs text-[color:var(--portal-muted)]">
								<input v-model="notifyOnShare" type="checkbox" class="rounded border-gray-300" />
								<FeatherIcon name="mail" class="h-3 w-3" />
								Email the user when I add them
							</label>

							<div
								v-if="userSearchHits.length"
								class="mt-2 max-h-48 overflow-auto rounded-xl border border-[color:var(--portal-border)]" style="background:var(--portal-surface-alt)"
							>
								<button
									v-for="u in userSearchHits"
									:key="u.name"
									type="button"
									class="flex w-full items-center justify-between gap-2 border-b border-[color:var(--portal-border)] px-3 py-2 text-left text-sm transition last:border-b-0 hover:bg-[color:var(--portal-accent-soft)] disabled:opacity-50"
									:disabled="shareModalSaving"
									@click="shareWithUser(u.name)"
								>
									<span class="min-w-0">
										<span class="block truncate font-medium text-[color:var(--portal-text)]">
											{{ u.full_name || u.name }}
										</span>
										<span class="block truncate text-xs text-[color:var(--portal-muted)]">{{ u.email || u.name }}</span>
									</span>
									<span class="shrink-0 text-xs font-semibold text-[color:var(--portal-accent-strong)]">+ Add</span>
								</button>
							</div>
							<p
								v-else-if="userSearchBusy"
								class="mt-2 flex items-center gap-2 text-xs text-[color:var(--portal-muted)]"
							>
								<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
								Loading users…
							</p>
							<p
								v-else
								class="mt-2 text-xs text-[color:var(--portal-muted)]"
							>
								No matching users. Try a different name or email.
							</p>
						</section>

						<!-- People with access -->
						<section>
							<p class="portal-section-title mb-2">People with access</p>
							<div v-if="shareModalLoading" class="text-sm text-[color:var(--portal-muted)]">Loading…</div>
							<div v-else-if="!userSharesForFolder.length" class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] p-4 text-center text-xs text-[color:var(--portal-muted)]">
								No people have direct access yet. Add someone above.
							</div>
							<ul v-else class="divide-y divide-[color:var(--portal-border)] rounded-xl border border-[color:var(--portal-border)]" style="background:var(--portal-surface-alt)">
								<li
									v-for="s in userSharesForFolder"
									:key="s.name"
									class="flex items-center gap-3 px-3 py-2.5 text-sm"
								>
									<div
										class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
										style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
									>
										{{ (s.user_full_name || s.user_email || s.user || '?').charAt(0).toUpperCase() }}
									</div>
									<div class="min-w-0 flex-1">
										<p class="truncate font-medium text-[color:var(--portal-text)]">
											{{ s.user_full_name || s.user || s.user_email }}
										</p>
										<p class="truncate text-xs text-[color:var(--portal-muted)]">
											{{ s.user_email || s.user }}
											<span v-if="s.expires_at"> · expires {{ fmtShareExpiry(s) }}</span>
											<span v-else-if="s.native"> · ERPNext share</span>
										</p>
									</div>
									<button
										class="portal-btn portal-btn-danger text-xs"
										:disabled="shareModalSaving"
										@click="revokeShare(s.name)"
									>
										Revoke
									</button>
								</li>
							</ul>
						</section>

						<!-- Public link (folder shares only — single-file links not implemented) -->
						<section v-if="shareTrackingAvailable && shareModalKind === 'folder'">
							<p class="portal-section-title mb-2">Anyone with the link</p>
							<div
								v-if="!activeLinkShare"
								class="flex flex-wrap items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-3"
							>
								<FeatherIcon name="link" class="h-4 w-4 text-[color:var(--portal-muted)]" />
								<span class="text-sm text-[color:var(--portal-muted)]">No active link.</span>
								<div class="ml-auto flex items-center gap-2">
									<label class="text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
										Expiry (days)
									</label>
									<input
										v-model.number="linkExpiryDays"
										type="number"
										min="1"
										max="365"
										class="portal-input w-16 px-2"
									/>
									<button class="portal-btn portal-btn-primary text-xs" :disabled="shareModalSaving" @click="createOrCopyShareLink">
										<FeatherIcon name="link-2" class="h-3.5 w-3.5" />
										Create link
									</button>
								</div>
							</div>
							<div
								v-else
								class="space-y-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-3"
							>
								<div class="flex items-center gap-2">
									<FeatherIcon name="link" class="h-4 w-4 text-[color:var(--portal-accent)]" />
									<a
										:href="activeLinkShare.share_url"
										target="_blank"
										rel="noopener"
										class="min-w-0 flex-1 truncate text-sm text-[color:var(--portal-accent-strong)] underline"
									>
										{{ activeLinkShare.share_url }}
									</a>
									<button class="portal-btn text-xs" @click="copyShareLink(activeLinkShare.share_url)">
										<FeatherIcon name="copy" class="h-3.5 w-3.5" />
										Copy
									</button>
								</div>
								<div class="flex flex-wrap items-center justify-between gap-2 text-xs text-[color:var(--portal-muted)]">
									<span>Expires {{ fmtShareExpiry(activeLinkShare) }} · {{ activeLinkShare.access_count || 0 }} opens</span>
									<button class="portal-btn portal-btn-danger text-xs" :disabled="shareModalSaving" @click="revokeShare(activeLinkShare.name)">
										Revoke link
									</button>
								</div>
							</div>
						</section>

						<p v-if="shareModalError" class="text-sm text-red-600">{{ shareModalError }}</p>
						<p v-if="shareModalOk" class="text-sm text-green-700">{{ shareModalOk }}</p>
					</div>

					<div class="flex items-center justify-end gap-2 border-t border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-5 py-3">
						<button class="portal-btn" @click="closeShareModal">Done</button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="confirmUploadOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="cancelUploadConfirm"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-2xl rounded-2xl border border-[color:var(--portal-border)] shadow-2xl portal-anim-in" style="background:var(--portal-surface)" @click.stop>
					<div class="flex items-center justify-between gap-3 border-b border-[color:var(--portal-border)] px-5 py-4">
						<div class="flex items-center gap-2">
							<div class="flex h-9 w-9 items-center justify-center rounded-xl text-white" style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);">
								<FeatherIcon name="upload-cloud" class="h-4 w-4" />
							</div>
							<div>
								<h2 class="text-base font-semibold text-[color:var(--portal-text)]">{{ isFolderMode ? "Confirm folder upload" : "Confirm upload" }}</h2>
								<p v-if="isFolderMode" class="text-xs text-[color:var(--portal-muted)]">Review the folder name and destination, then upload.</p>
								<p v-else class="text-xs text-[color:var(--portal-muted)]">Files will be wrapped in a dated folder. Same-day repeats become <strong>_v2</strong>, <strong>_v3</strong> …</p>
							</div>
						</div>
						<button type="button" class="rounded-lg p-1.5 transition hover:bg-white/5 disabled:opacity-50" style="color:var(--portal-muted)" :disabled="uploadBusy" @click="cancelUploadConfirm">
							<FeatherIcon name="x" class="h-4 w-4" />
						</button>
					</div>
					<div class="max-h-[60vh] space-y-3 overflow-auto px-5 py-4">
						<!-- Single-file upload: destination banner -->
						<div v-if="!isFolderMode" class="flex flex-wrap items-center gap-2 rounded-xl border border-[color:var(--portal-accent)]/40 bg-[color:var(--portal-accent-soft)] px-3 py-2 text-xs text-[color:var(--portal-accent-strong)]">
							<FeatherIcon name="folder" class="h-3.5 w-3.5 shrink-0" />
							<span class="font-semibold">Destination:</span>
							<span class="truncate">{{ folderLabelByName[targetFolder] || targetFolder || "—" }}</span>
							<span class="text-[color:var(--portal-subtle)]">/</span>
							<span class="truncate font-mono font-semibold">NN_{{ buildWrapperName(targetFolder, todayIso()) }}</span>
							<span class="ml-auto text-[10px] font-medium uppercase tracking-wide text-[color:var(--portal-muted)]">NN = auto series (01, 02…)</span>
						</div>

						<!-- Folder upload confirmation -->
						<template v-if="isFolderMode">
							<!-- Folder name (editable, follows naming convention) -->
							<div class="space-y-3 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-4 py-4">
								<div>
									<label class="portal-section-title mb-1 block">Folder name</label>
									<div class="flex items-center gap-2">
										<span class="rounded-lg border border-[color:var(--portal-accent)]/60 px-3 py-2 font-mono text-sm font-bold text-[color:var(--portal-accent)]" style="background:var(--portal-accent-soft)">NN_</span>
										<input v-model="pendingFolder.wrapperName" type="text" class="min-w-0 flex-1 rounded-xl border border-[color:var(--portal-border)] px-3 py-2 font-mono text-sm" style="background:var(--portal-bg);color:var(--portal-text)" :disabled="uploadBusy" />
									</div>
									<p class="mt-1 text-[11px] text-[color:var(--portal-muted)]">
										<strong>NN</strong> = auto series (01, 02, 03…) assigned on upload based on how many folders already exist in the destination.
										Re-uploading the same folder increments to the next number automatically.
									</p>
								</div>
								<div>
									<label class="portal-section-title mb-1 block">Upload into</label>
									<select v-model="pendingFolder.targetFolder" class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm" style="background:var(--portal-bg);color:var(--portal-text)" :disabled="uploadBusy">
										<option value="">— Select destination —</option>
										<option v-if="projectRootPath" :value="projectRootPath">Project folder (root)</option>
										<option v-for="f in folders" :key="`ff-${f.name}`" :value="f.name">{{ folderOptionLabel(f.label) }}</option>
									</select>
									<p class="mt-1 text-[11px] text-[color:var(--portal-muted)]">
										Will create <strong class="font-mono">{{ pendingFolder.wrapperName }}</strong> inside <strong>{{ folderLabelByName[pendingFolder.targetFolder] || "selected subfolder" }}</strong>
									</p>
								</div>
							</div>
							<!-- File preview -->
							<div class="overflow-hidden rounded-xl border border-[color:var(--portal-border)]" style="background:var(--portal-surface-alt)">
								<div class="flex items-center justify-between border-b border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-4 py-2">
									<span class="text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-muted)]">
										{{ pendingFolder.files.length }} file{{ pendingFolder.files.length === 1 ? "" : "s" }} — auto-classified by type
									</span>
								</div>
								<ul class="max-h-52 overflow-auto divide-y divide-[color:var(--portal-border)] text-xs">
									<li v-for="(e, ei) in pendingFolder.files" :key="`fe-${ei}`" class="flex flex-wrap items-center gap-x-3 gap-y-0.5 px-4 py-2 text-[color:var(--portal-text)]">
										<FeatherIcon name="file" class="h-3 w-3 shrink-0 text-[color:var(--portal-muted)]" />
										<span class="min-w-0 flex-1 truncate font-mono text-[11px]">
											<span class="text-[color:var(--portal-subtle)]">{{ e.relativeDir ? e.relativeDir + "/" : "" }}</span>{{ e.file.name }}
										</span>
										<span
											v-if="e.classification"
											class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold text-[color:var(--portal-accent-strong)]" style="background:var(--portal-accent-soft)"
										>{{ e.classification }}</span>
										<span class="shrink-0 text-[color:var(--portal-muted)]">{{ fmtFileSize(e.file.size) }}</span>
									</li>
								</ul>
							</div>
						</template>
						<div v-else v-for="(row, idx) in pendingUploads" :key="`pending-${idx}`" class="rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-3">
							<p class="mb-2 flex items-center gap-2 text-xs text-[color:var(--portal-muted)]">
								<FeatherIcon name="file" class="h-3.5 w-3.5 shrink-0" />
								<span class="min-w-0 truncate">Original: {{ row.originalFile.name }}</span>
								<span class="ml-auto shrink-0">{{ fmtFileSize(row.originalFile.size) }}</span>
							</p>
							<div class="grid gap-2 sm:grid-cols-3">
								<label class="block sm:col-span-3">
									<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">File name</span>
									<input v-model="row.name" type="text" class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm" style="background:var(--portal-bg);color:var(--portal-text)" :disabled="uploadBusy" @input="onPendingNameChange(row)" />
								</label>
								<label class="block sm:col-span-2">
									<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">Category (folder)</span>
									<select v-model="row.category" class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm" style="background:var(--portal-bg);color:var(--portal-text)" :disabled="uploadBusy" @change="onPendingCategoryChange(row)">
										<option v-if="projectRootPath" :value="projectRootPath">Project folder (all files)</option>
										<option v-for="f in folders" :key="`pcat-${idx}-${f.name}`" :value="f.name">{{ folderOptionLabel(f.label) }}</option>
									</select>
								</label>
								<label class="block">
									<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">Date</span>
									<input v-model="row.date" type="date" class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm" style="background:var(--portal-bg);color:var(--portal-text)" :disabled="uploadBusy" @change="onPendingDateChange(row)" />
								</label>
								<label v-if="fileTypes.length" class="block sm:col-span-3">
									<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">File type</span>
									<select v-model="row.fileType" class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-2 text-sm" style="background:var(--portal-bg);color:var(--portal-text)" :disabled="uploadBusy">
										<option value="">— Not set —</option>
										<option v-for="t in fileTypes" :key="`ft-${idx}-${t.name}`" :value="t.name">{{ t.label }}</option>
									</select>
								</label>
								<!-- File Classification -->
								<div class="block sm:col-span-3 rounded-xl border border-[color:var(--portal-border)] px-3 py-2" style="background:var(--portal-surface-alt)">
									<p class="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-muted)]">File Classification (auto-detected)</p>
									<div class="flex flex-wrap items-center gap-2">
										<span class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold text-[color:var(--portal-accent-strong)]" style="background:var(--portal-accent-soft)">
											{{ row.fileClassification || "Uncategorized" }}
										</span>
										<span v-if="row.fileSubCategory" class="text-xs text-[color:var(--portal-accent-strong)]">· {{ row.fileSubCategory }}</span>
									</div>
									<div v-if="row.ext === '.pdf'" class="mt-2">
										<label class="block">
											<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-muted)]">Document Type (refine PDF classification)</span>
											<select
												v-model="row.documentType"
												class="w-full rounded-xl border border-[color:var(--portal-border)] px-3 py-1.5 text-sm" style="background:var(--portal-bg);color:var(--portal-text)"
												:disabled="uploadBusy"
												@change="() => { const [c, s] = classifyFile(row.originalFile.name, row.documentType); row.fileClassification = c; row.fileSubCategory = s; }"
											>
												<option v-for="opt in PDF_DOC_TYPE_OPTIONS" :key="opt" :value="opt">{{ opt || '— Auto-detect from filename —' }}</option>
											</select>
										</label>
									</div>
								</div>
							</div>
						</div>
						<p v-if="uploadError" class="text-sm text-red-600">{{ uploadError }}</p>
					</div>
					<div class="flex items-center justify-end gap-2 border-t border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-5 py-3">
						<button type="button" class="portal-btn disabled:opacity-50" :disabled="uploadBusy" @click="cancelUploadConfirm">Cancel</button>
						<button type="button" class="flex items-center gap-2 rounded-lg bg-[color:var(--portal-accent)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50" :disabled="uploadBusy" @click="runConfirm">
							<FeatherIcon name="upload" class="h-4 w-4" />
							<template v-if="isFolderMode">
								{{ uploadBusy ? "Uploading…" : `Upload "${pendingFolder.wrapperName}" (${pendingFolder.files.length} file${pendingFolder.files.length===1?"":"s"})` }}
							</template>
							<template v-else>
								{{ uploadBusy ? "Uploading…" : `Upload ${pendingUploads.length} file${pendingUploads.length === 1 ? "" : "s"}` }}
							</template>
						</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
