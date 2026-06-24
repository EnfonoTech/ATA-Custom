<script setup>
import { ref, computed, onMounted, watch, reactive } from "vue";
import { call } from "@/api";
import { FeatherIcon } from "frappe-ui";

// ── Projects ──────────────────────────────────────────────────────────────────
const projects     = ref([]);
const projSearch   = ref("");
const loadingProj  = ref(false);

// ── Per-project file cache ────────────────────────────────────────────────────
const projCache    = reactive({});
const activeProj   = ref(null);
const activeFolder = ref("");
const fileSearch   = ref("");
const activeCategory = ref("");
const sortKey      = ref("date");
const sortAsc      = ref(false);
const loadingFiles = ref(false);

// ── Sidebar expand state ─────────────────────────────────────────────────────
const expandedYears   = ref(new Set(["2026", "2025"]));
const expandedFolders = ref(new Set());

// ── Helpers ───────────────────────────────────────────────────────────────────
function yearFromCode(code) {
	if (!code) return null;
	const m = String(code).match(/ATA-(\d{2})\d{2}/);
	if (m) return 2000 + parseInt(m[1]);
	if (/ATA-CDB/i.test(code)) return 2026;
	return null;
}
function yearFromProjectName(name) {
	const m = String(name || "").match(/^(\d{4})\s*[–—-]/);
	if (m) return 2000 + parseInt(m[1].slice(0, 2));
	return null;
}
function projectYear(p) {
	return yearFromCode(p.portal_project_code) || yearFromProjectName(p.project_name) || 0;
}

const EXT_ICON = {
	".jpg": "image", ".jpeg": "image", ".png": "image", ".tif": "image", ".tiff": "image",
	".pdf": "file-text",
	".dwg": "pen-tool", ".dxf": "pen-tool",
	".skp": "box", ".rvt": "box", ".rfa": "box", ".max": "box",
	".3dm": "box", ".fbx": "box", ".obj": "box", ".dae": "box",
	".xlsx": "bar-chart-2", ".xls": "bar-chart-2", ".xlsm": "bar-chart-2", ".csv": "bar-chart-2",
	".ppt": "monitor", ".pptx": "monitor",
	".psd": "layers", ".psb": "layers", ".ai": "layers", ".indd": "layers", ".idml": "layers",
};
function getExt(name) {
	const m = String(name || "").toLowerCase().match(/\.\w+$/);
	return m ? m[0] : "";
}
function extIcon(name) { return EXT_ICON[getExt(name)] || "file"; }

const CAT_MAP = {
	".ppt": "Presentation", ".pptx": "Presentation",
	".dwg": "Drawing",      ".dxf":  "Drawing",
	".skp": "3D Model",     ".rvt":  "3D Model",     ".rfa":  "3D Model", ".max": "3D Model",
	".3dm": "3D Model",     ".fbx":  "3D Model",     ".obj":  "3D Model", ".dae": "3D Model",
	".xlsx": "Feasibility", ".xls":  "Feasibility",  ".xlsm": "Feasibility", ".csv": "Feasibility",
	".psd": "Design Source",".psb":  "Design Source",".ai":   "Design Source",
	".indd": "Design Source",".idml":"Design Source",
	".jpg": "Renders",      ".jpeg": "Renders",      ".png":  "Renders",
	".tif": "Renders",      ".tiff": "Renders",
	".pdf": "Presentation",
};
function catFromExt(name) { return CAT_MAP[getExt(name)] || "Other"; }

// Dark-mode aware category styles (inline style strings)
const CAT_STYLE_MAP = {
	"Presentation":  "background:rgba(168,85,247,0.12);color:#c084fc;border:1px solid rgba(168,85,247,0.2)",
	"Drawing":       "background:rgba(59,130,246,0.12);color:#93c5fd;border:1px solid rgba(59,130,246,0.2)",
	"3D Model":      "background:rgba(6,182,212,0.12);color:#22d3ee;border:1px solid rgba(6,182,212,0.2)",
	"Feasibility":   "background:rgba(34,197,94,0.12);color:#86efac;border:1px solid rgba(34,197,94,0.2)",
	"Design Source": "background:rgba(249,115,22,0.12);color:#fdba74;border:1px solid rgba(249,115,22,0.2)",
	"Renders":       "background:rgba(236,72,153,0.12);color:#f9a8d4;border:1px solid rgba(236,72,153,0.2)",
	"Other":         "background:rgba(148,163,184,0.12);color:#94a3b8;border:1px solid rgba(148,163,184,0.2)",
};
function catStyle(cat) { return CAT_STYLE_MAP[cat] || CAT_STYLE_MAP["Other"]; }

function fmtDate(s) {
	if (!s) return "—";
	const d = new Date(String(s).replace(" ", "T"));
	if (isNaN(d)) return s;
	return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}
function fmtSize(b) {
	if (!b) return "—";
	if (b >= 1_048_576) return `${(b/1_048_576).toFixed(1)} MB`;
	if (b >= 1024)      return `${(b/1024).toFixed(1)} KB`;
	return `${b} B`;
}

// ── Year-grouped project tree ─────────────────────────────────────────────────
const yearGroups = computed(() => {
	const q = projSearch.value.trim().toLowerCase();
	const all = q
		? projects.value.filter(p =>
				String(p.project_name || "").toLowerCase().includes(q) ||
				String(p.portal_project_code || "").toLowerCase().includes(q) ||
				String(p.name || "").toLowerCase().includes(q))
		: projects.value;
	const byYear = new Map();
	for (const p of all) {
		const yr = projectYear(p) || "Other";
		if (!byYear.has(yr)) byYear.set(yr, []);
		byYear.get(yr).push(p);
	}
	return [...byYear.entries()]
		.sort(([a], [b]) => {
			if (a === "Other") return 1;
			if (b === "Other") return -1;
			return b - a;
		})
		.map(([year, projs]) => ({
			year: String(year),
			projects: projs.sort((a, b) =>
				String(a.project_name || "").localeCompare(String(b.project_name || ""), undefined, { numeric: true })
			),
		}));
});

// ── Load & cache project files ────────────────────────────────────────────────
async function openProject(p) {
	if (activeProj.value?.name === p.name) {
		activeProj.value   = null;
		activeFolder.value = "";
		activeCategory.value = "";
		return;
	}
	activeProj.value   = p;
	activeFolder.value = "";
	activeCategory.value = "";
	if (projCache[p.name]) return;
	loadingFiles.value = true;
	try {
		const res = await call({
			method: "portal_app.api.files.list_project_files",
			args:   { project: p.name },
		});
		const fCtx = res?.folders || {};
		projCache[p.name] = {
			files:   (res?.files || []).filter(f => !f.is_folder),
			folders: fCtx.subfolders || [],
			root:    fCtx.project_root || "",
		};
	} finally {
		loadingFiles.value = false;
	}
}

const cacheEntry  = computed(() => activeProj.value ? (projCache[activeProj.value.name] || null) : null);
const allFiles    = computed(() => cacheEntry.value?.files  || []);
const allFolders  = computed(() => cacheEntry.value?.folders || []);
const projectRoot = computed(() => cacheEntry.value?.root   || "");

// ── Folder tree ───────────────────────────────────────────────────────────────
const treeNodes = computed(() => {
	const nodes = new Map();
	nodes.set("", { key: "", label: "All files", name: projectRoot.value, depth: 0, isRoot: true, parentKey: "" });
	const sorted = [...allFolders.value].sort((a, b) =>
		String(a.label || "").localeCompare(String(b.label || ""), undefined, { numeric: true }));
	for (const f of sorted) {
		const parts = (f.label || "").split("/");
		for (let i = 1; i <= parts.length; i++) {
			const key = parts.slice(0, i).join("/");
			if (nodes.has(key)) continue;
			const match = sorted.find(x => x.label === key);
			nodes.set(key, {
				key, label: parts[i - 1], name: match?.name || "",
				depth: i, isRoot: false, parentKey: parts.slice(0, i - 1).join("/"),
			});
		}
	}
	return nodes;
});

const flatTree = computed(() => {
	const out = [];
	function visit(key, visited = new Set()) {
		if (visited.has(key)) return;
		visited.add(key);
		const node = treeNodes.value.get(key);
		if (!node) return;
		out.push(node);
		const children = [...treeNodes.value.values()]
			.filter(n => n.parentKey === key && n.depth === node.depth + 1);
		if (node.isRoot || expandedFolders.value.has(key))
			for (const c of children) visit(c.key, visited);
	}
	visit("");
	return out;
});

function hasFolderChildren(key) {
	return [...treeNodes.value.values()].some(n => n.parentKey === key);
}
function toggleFolder(key) {
	const s = new Set(expandedFolders.value);
	s.has(key) ? s.delete(key) : s.add(key);
	expandedFolders.value = s;
}
function folderFileCount(node) {
	if (node.isRoot) return allFiles.value.length;
	return allFiles.value.filter(f => {
		const fo = f.folder || "";
		return fo === node.name || fo.startsWith(node.name + "/");
	}).length;
}

function relFolder(file) {
	const root = projectRoot.value;
	const fo   = file?.folder || "";
	if (!root || fo === root) return "";
	if (fo.startsWith(root + "/")) return fo.slice(root.length + 1);
	return fo;
}

// ── Visible files + categories ────────────────────────────────────────────────
const categoryTotals = computed(() => {
	const m = new Map();
	let base = allFiles.value;
	if (activeFolder.value && activeFolder.value !== projectRoot.value) {
		const af = activeFolder.value;
		base = base.filter(f => { const fo = f.folder||""; return fo === af || fo.startsWith(af+"/"); });
	}
	for (const f of base) {
		const c = catFromExt(f.file_name);
		m.set(c, (m.get(c) || 0) + 1);
	}
	return [...m.entries()].sort((a, b) => b[1] - a[1]);
});

const visibleFiles = computed(() => {
	let list = allFiles.value;
	if (activeFolder.value && activeFolder.value !== projectRoot.value) {
		const af = activeFolder.value;
		list = list.filter(f => { const fo = f.folder||""; return fo === af || fo.startsWith(af+"/"); });
	}
	if (activeCategory.value) list = list.filter(f => catFromExt(f.file_name) === activeCategory.value);
	const q = fileSearch.value.trim().toLowerCase();
	if (q) list = list.filter(f => String(f.file_name || "").toLowerCase().includes(q));
	return [...list].sort((a, b) => {
		let av, bv;
		if (sortKey.value === "name")  { av = a.file_name || ""; bv = b.file_name || ""; }
		else if (sortKey.value === "size") { av = a.file_size || 0; bv = b.file_size || 0; }
		else { av = a.creation || ""; bv = b.creation || ""; }
		return sortAsc.value ? (av < bv ? -1 : av > bv ? 1 : 0) : (bv < av ? -1 : bv > av ? 1 : 0);
	});
});

function setSort(key) {
	if (sortKey.value === key) sortAsc.value = !sortAsc.value;
	else { sortKey.value = key; sortAsc.value = key === "name"; }
}
function sortIcon(key) {
	if (sortKey.value !== key) return "chevrons-up-down";
	return sortAsc.value ? "chevron-up" : "chevron-down";
}

const folderLabel = computed(() => {
	if (!activeFolder.value || activeFolder.value === projectRoot.value) return "";
	return allFolders.value.find(f => f.name === activeFolder.value)?.label || "";
});

// ── Submit to Client Submittal ───────────────────────────────────────────────
const submitModalOpen = ref(false);
const submitFile      = ref(null);
const submitBusy      = ref(false);
const submitError     = ref("");
const submitOk        = ref("");

function todayIso() {
	const d  = new Date();
	const mm = String(d.getMonth() + 1).padStart(2, "0");
	const dd = String(d.getDate()).padStart(2, "0");
	return `${d.getFullYear()}-${mm}-${dd}`;
}
function openSubmitModal(f) {
	submitFile.value  = f;
	submitError.value = "";
	submitOk.value    = "";
	submitModalOpen.value = true;
}
function closeSubmitModal() {
	if (submitBusy.value) return;
	submitModalOpen.value = false;
	submitFile.value = null;
}
function previewSubmitName() {
	const f = submitFile.value;
	if (!f) return "";
	return `NN_${todayIso()}_${f.file_name || ""}`;
}
async function confirmSubmitToClient() {
	const f    = submitFile.value;
	const proj = activeProj.value?.name;
	if (!f || !proj) return;
	submitBusy.value  = true;
	submitError.value = "";
	submitOk.value    = "";
	try {
		const res = await call({
			method: "portal_app.api.files.submit_to_client_submittal",
			type: "POST",
			args: { file_name: f.name, project: proj },
		});
		submitOk.value = `Submitted as "${res.file_name}" (SL ${res.sl_no}) to Client Submittal.`;
		if (projCache[proj]) delete projCache[proj];
		setTimeout(() => { submitOk.value = ""; closeSubmitModal(); }, 3000);
	} catch (e) {
		const body = e?.responseBody;
		submitError.value = body?._server_messages
			? (() => { try { return JSON.parse(JSON.parse(body._server_messages)[0]).message; } catch { return body._server_messages; } })()
			: body?.message || e?.message || "Submission failed.";
	} finally {
		submitBusy.value = false;
	}
}

// ── Share file with users ─────────────────────────────────────────────────────
const shareModalOpen = ref(false);
const shareFile      = ref(null);
const shareSearch    = ref("");
const shareResults   = ref([]);
const searchBusy     = ref(false);
const sharesList     = ref([]);
const sharesLoading  = ref(false);
const shareError     = ref("");
const revokingSet    = ref(new Set());
const sharingSet     = ref(new Set());
let _searchTimer     = null;

function openShareModal(f) {
	shareFile.value    = f;
	shareSearch.value  = "";
	shareResults.value = [];
	shareError.value   = "";
	shareModalOpen.value = true;
	loadSharesList();
}
function closeShareModal() {
	shareModalOpen.value = false;
	shareFile.value      = null;
	sharesList.value     = [];
	shareResults.value   = [];
}
async function loadSharesList() {
	if (!shareFile.value || !activeProj.value) return;
	sharesLoading.value = true;
	try {
		const res = await call({
			method: "portal_app.api.files.list_folder_shares",
			args: { project: activeProj.value.name, folder_path: shareFile.value.name },
		});
		sharesList.value = (res?.shares || []).filter(s => s.share_kind === "User");
	} catch {
		sharesList.value = [];
	} finally {
		sharesLoading.value = false;
	}
}
function onShareSearch(txt) {
	clearTimeout(_searchTimer);
	if (!txt.trim()) { shareResults.value = []; searchBusy.value = false; return; }
	searchBusy.value = true;
	_searchTimer = setTimeout(async () => {
		try {
			const res = await call({
				method: "portal_app.api.projects.search_portal_users",
				args: { txt },
			});
			const already = new Set(sharesList.value.map(s => s.user));
			shareResults.value = (res || []).filter(u => !already.has(u.name));
		} catch {
			shareResults.value = [];
		} finally {
			searchBusy.value = false;
		}
	}, 280);
}
async function addShare(user) {
	if (!shareFile.value || !activeProj.value) return;
	const uid = user.name;
	sharingSet.value   = new Set([...sharingSet.value, uid]);
	shareSearch.value  = "";
	shareResults.value = [];
	shareError.value   = "";
	try {
		await call({
			method: "portal_app.api.files.share_file_with_user",
			type:   "POST",
			args: {
				project:      activeProj.value.name,
				file_name:    shareFile.value.name,
				user_id:      uid,
				expires_days: 30,
			},
		});
		await loadSharesList();
	} catch (e) {
		shareError.value = e?.responseBody?.message || e?.message || "Share failed.";
	} finally {
		const s = new Set(sharingSet.value); s.delete(uid); sharingSet.value = s;
	}
}
async function revokeShare(sh) {
	const id = sh.name;
	revokingSet.value = new Set([...revokingSet.value, id]);
	shareError.value  = "";
	try {
		await call({
			method: "portal_app.api.files.revoke_folder_share",
			type:   "POST",
			args:   { share_name: id },
		});
		sharesList.value = sharesList.value.filter(s => s.name !== id);
	} catch (e) {
		shareError.value = e?.responseBody?.message || e?.message || "Revoke failed.";
	} finally {
		const s = new Set(revokingSet.value); s.delete(id); revokingSet.value = s;
	}
}
function shareInitials(sh) {
	const name = sh.user_full_name || sh.user || "";
	return name.split(" ").slice(0, 2).map(w => (w[0] || "")).join("").toUpperCase() || "?";
}
function shareExpiry(sh) {
	if (!sh.expires_at) return "";
	const d = new Date(String(sh.expires_at).replace(" ", "T"));
	if (isNaN(d)) return "";
	return "Expires " + d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}
// ─────────────────────────────────────────────────────────────────────────────

onMounted(async () => {
	loadingProj.value = true;
	try {
		const res = await call({ method: "portal_app.api.projects.list_projects" });
		projects.value = res?.projects || [];
	} finally {
		loadingProj.value = false;
	}
});

watch(activeProj, () => {
	expandedFolders.value = new Set();
	activeCategory.value  = "";
});

watch(activeFolder, (newFolder) => {
	if (!newFolder || newFolder === projectRoot.value) return;
	const folder = allFolders.value.find(f => f.name === newFolder);
	if (!folder?.label) return;
	const parts = folder.label.split("/");
	if (parts.length <= 1) return;
	const next = new Set(expandedFolders.value);
	for (let i = 1; i < parts.length; i++) {
		next.add(parts.slice(0, i).join("/"));
	}
	expandedFolders.value = next;
});
</script>

<template>
	<div class="flex h-full overflow-hidden" style="background: var(--portal-bg);">

		<!-- ══ LEFT SIDEBAR ═══════════════════════════════════════════════════ -->
		<aside
			class="flex w-80 shrink-0 flex-col overflow-hidden"
			style="
				background: linear-gradient(180deg, var(--portal-surface) 0%, var(--portal-bg) 100%);
				border-right: 1px solid var(--portal-border);
				box-shadow: 2px 0 16px rgba(0,0,0,0.12);
				min-width: 320px;
			"
		>
			<!-- Sidebar brand + search -->
			<div class="px-4 pt-5 pb-3">
				<div class="mb-3 flex items-center gap-2.5">
					<div
						class="flex h-8 w-8 items-center justify-center rounded-xl text-white shadow-md"
						style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
					>
						<FeatherIcon name="folder-open" class="h-4 w-4" />
					</div>
					<div>
						<p class="text-sm font-bold leading-tight" style="color:var(--portal-text)">File Browser</p>
						<p class="text-[10px]" style="color:var(--portal-subtle)">Browse by year · project · folder</p>
					</div>
				</div>
				<div class="relative">
					<FeatherIcon name="search" class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2" style="color:var(--portal-subtle)" />
					<input
						v-model="projSearch"
						type="search"
						placeholder="Search projects…"
						class="w-full rounded-xl py-2 pl-9 pr-3 text-sm shadow-sm transition focus:outline-none"
						style="border: 1px solid var(--portal-border); background: var(--portal-surface-alt); color: var(--portal-text);"
					/>
				</div>
			</div>

			<!-- Loading -->
			<div v-if="loadingProj" class="flex flex-1 items-center justify-center">
				<span class="h-5 w-5 animate-spin rounded-full border-2 border-t-transparent" style="border-color:var(--portal-accent);border-top-color:transparent"></span>
			</div>

			<!-- Year → Project → Folder tree -->
			<div v-else class="min-h-0 flex-1 overflow-y-auto px-2 pb-4">

				<template v-for="group in yearGroups" :key="group.year">
					<!-- Year header -->
					<button
						type="button"
						class="mt-1.5 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left transition"
						style="color:var(--portal-text)"
						:style="expandedYears.has(group.year) ? 'background:rgba(245,158,11,0.06)' : ''"
						@mouseover="e => !expandedYears.has(group.year) && (e.currentTarget.style.background='rgba(255,255,255,0.04)')"
						@mouseleave="e => !expandedYears.has(group.year) && (e.currentTarget.style.background='')"
						@click="expandedYears.has(group.year) ? expandedYears.delete(group.year) : expandedYears.add(group.year)"
					>
						<FeatherIcon
							:name="expandedYears.has(group.year) ? 'chevron-down' : 'chevron-right'"
							class="h-3.5 w-3.5 shrink-0 transition-transform"
							style="color:var(--portal-accent)"
						/>
						<span class="flex-1 text-sm font-bold">
							{{ group.year === "0" ? "Other" : group.year }}
						</span>
						<span class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
							style="background:var(--portal-accent-soft);color:var(--portal-accent)">
							{{ group.projects.length }}
						</span>
					</button>

					<!-- Projects under this year -->
					<template v-if="expandedYears.has(group.year)">
						<template v-for="p in group.projects" :key="p.name">
							<!-- Project row -->
							<button
								type="button"
								class="ml-1 mt-0.5 flex w-[calc(100%-0.25rem)] items-center gap-2.5 rounded-xl px-3 py-2.5 text-left transition"
								:class="activeProj?.name === p.name ? 'shadow-lg' : 'hover:shadow-md'"
								:style="activeProj?.name === p.name
									? 'background:linear-gradient(135deg,var(--portal-accent) 0%,var(--portal-accent-strong) 100%);color:#fff;'
									: 'color:var(--portal-text)'"
								@mouseover="e => activeProj?.name !== p.name && (e.currentTarget.style.background='rgba(255,255,255,0.05)')"
								@mouseleave="e => activeProj?.name !== p.name && (e.currentTarget.style.background='')"
								@click="openProject(p)"
							>
								<!-- Folder icon (portal accent) -->
								<span
									class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl shadow-sm"
									:style="activeProj?.name === p.name
										? 'background:rgba(255,255,255,0.2);'
										: 'background:var(--portal-accent-soft);'"
								>
									<FeatherIcon
										:name="activeProj?.name === p.name ? 'folder-open' : 'folder'"
										class="h-4 w-4"
										:style="activeProj?.name === p.name ? 'color:#fff' : 'color:var(--portal-accent)'"
									/>
								</span>
								<!-- Name + code -->
								<span class="min-w-0 flex-1" :title="p.project_name">
									<span
										class="block truncate text-sm font-bold leading-snug"
										:style="activeProj?.name === p.name ? 'color:#fff' : 'color:var(--portal-text)'"
									>{{ p.project_name }}</span>
									<span
										v-if="p.portal_project_code"
										class="block truncate text-[10px] font-semibold tracking-wide"
										:style="activeProj?.name === p.name ? 'color:rgba(255,255,255,0.7)' : 'color:var(--portal-accent)'">
										{{ p.portal_project_code }}
									</span>
								</span>
								<!-- File count badge -->
								<span
									v-if="projCache[p.name]"
									class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold"
									:style="activeProj?.name === p.name ? 'background:rgba(255,255,255,0.25);color:#fff' : 'background:var(--portal-accent-soft);color:var(--portal-accent)'"
								>{{ projCache[p.name].files.length }}</span>
								<FeatherIcon
									v-if="activeProj?.name === p.name"
									name="chevron-down"
									class="h-3.5 w-3.5 shrink-0"
									style="color:rgba(255,255,255,0.7)"
								/>
							</button>

							<!-- Folder tree (inline under project) -->
							<template v-if="activeProj?.name === p.name && !loadingFiles && cacheEntry">
								<div class="ml-6 mt-1 space-y-0.5 border-l-2 pl-2" style="border-color:var(--portal-border)">
									<button
										v-for="node in flatTree"
										:key="node.key"
										type="button"
										class="flex w-full items-center gap-1.5 rounded-lg py-1.5 pr-2 text-left transition"
										:style="{
											paddingLeft: `${0.25 + (node.depth - 1) * 0.75}rem`,
											background: activeFolder === node.name ? 'var(--portal-accent)' : '',
											color: activeFolder === node.name ? 'var(--portal-accent-fg)' : 'var(--portal-muted)',
										}"
										:class="[
											node.isRoot ? 'text-xs font-bold' : node.depth <= 2 ? 'text-xs font-semibold' : 'text-[11px] font-medium',
										]"
										@click="activeFolder = node.name; activeCategory = ''"
									>
										<!-- Expand/collapse toggle -->
										<button
											v-if="hasFolderChildren(node.key)"
											type="button"
											class="flex h-4 w-4 shrink-0 items-center justify-center rounded transition"
											:style="activeFolder === node.name ? 'color:rgba(255,255,255,0.7)' : 'color:var(--portal-subtle)'"
											@click.stop="toggleFolder(node.key)"
										>
											<FeatherIcon :name="expandedFolders.has(node.key) || node.isRoot ? 'chevron-down' : 'chevron-right'" class="h-2.5 w-2.5" />
										</button>
										<span v-else class="h-4 w-4 shrink-0"></span>
										<!-- Folder icon -->
										<FeatherIcon
											:name="activeFolder === node.name ? 'folder-open' : 'folder'"
											class="h-3.5 w-3.5 shrink-0 transition"
											:style="activeFolder === node.name ? 'color:rgba(255,255,255,0.9)' : 'color:var(--portal-accent)'"
										/>
										<!-- Label -->
										<span class="min-w-0 flex-1 truncate">{{ node.label }}</span>
										<!-- File count -->
										<span
											v-if="folderFileCount(node)"
											class="ml-1 shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-bold"
											:style="activeFolder === node.name ? 'background:rgba(255,255,255,0.25);color:#fff' : 'background:var(--portal-accent-soft);color:var(--portal-accent)'"
										>{{ folderFileCount(node) }}</span>
									</button>
								</div>
								<div v-if="loadingFiles" class="ml-8 mt-1 flex items-center gap-1.5 py-1 text-xs" style="color:var(--portal-subtle)">
									<span class="h-3 w-3 animate-spin rounded-full border border-t-transparent" style="border-color:var(--portal-accent);border-top-color:transparent"></span>
									Loading…
								</div>
							</template>
						</template>
					</template>
				</template>

				<p v-if="!yearGroups.length" class="py-10 text-center text-xs" style="color:var(--portal-subtle)">
					{{ projSearch ? "No projects match." : "No projects found." }}
				</p>
			</div>
		</aside>

		<!-- ══ MAIN PANEL ════════════════════════════════════════════════════ -->
		<main class="flex min-w-0 flex-1 flex-col overflow-hidden">

			<!-- ── Top bar ─────────────────────────────────────────────────── -->
			<div
				class="shrink-0 border-b px-5 py-3"
				style="background: var(--portal-surface); backdrop-filter: blur(8px); border-color: var(--portal-border); box-shadow: var(--portal-shadow-sm);"
			>
				<div class="flex flex-wrap items-center gap-3">
					<!-- Breadcrumb -->
					<div class="flex min-w-0 flex-1 items-center gap-1.5 text-sm">
						<template v-if="activeProj">
							<FeatherIcon name="folder-open" class="h-4 w-4 shrink-0" style="color:var(--portal-accent)" />
							<button
								class="font-semibold transition"
								style="color:var(--portal-text)"
								@click="activeFolder = ''; activeCategory = ''"
							>{{ activeProj.project_name }}</button>
							<template v-if="folderLabel">
								<FeatherIcon name="chevron-right" class="h-3.5 w-3.5 shrink-0" style="color:var(--portal-border-strong)" />
								<span class="truncate" style="color:var(--portal-muted)">{{ folderLabel }}</span>
								<button
									class="flex h-5 w-5 items-center justify-center rounded-full transition"
									style="color:var(--portal-subtle)"
									@click="activeFolder = ''; activeCategory = ''"
								>
									<FeatherIcon name="x" class="h-3 w-3" />
								</button>
							</template>
						</template>
						<span v-else style="color:var(--portal-subtle)">Select a project from the sidebar</span>
					</div>

					<template v-if="activeProj && !loadingFiles && cacheEntry">
						<!-- File search -->
						<div class="relative w-48 shrink-0">
							<FeatherIcon name="search" class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2" style="color:var(--portal-subtle)" />
							<input
								v-model="fileSearch"
								type="search"
								placeholder="Search files…"
								class="w-full rounded-xl py-1.5 pl-8 pr-3 text-sm transition focus:outline-none"
								style="border: 1px solid var(--portal-border); background: var(--portal-surface-alt); color: var(--portal-text);"
							/>
						</div>
						<!-- File count pill -->
						<span class="shrink-0 rounded-full px-3 py-1 text-xs font-semibold"
							style="background:var(--portal-accent-soft);color:var(--portal-accent)">
							{{ visibleFiles.length }} / {{ allFiles.length }} files
						</span>
					</template>
				</div>

				<!-- Category filter chips -->
				<div v-if="activeProj && cacheEntry && categoryTotals.length" class="mt-2.5 flex flex-wrap items-center gap-1.5">
					<button
						type="button"
						class="rounded-full px-3 py-1 text-xs font-semibold transition"
						:style="!activeCategory
							? 'background:var(--portal-accent);color:var(--portal-accent-fg)'
							: 'background:var(--portal-surface-alt);color:var(--portal-muted)'"
						@click="activeCategory = ''"
					>All</button>
					<button
						v-for="[cat, cnt] in categoryTotals"
						:key="cat"
						type="button"
						class="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition hover:opacity-90"
						:style="activeCategory === cat
							? 'background:var(--portal-accent);color:var(--portal-accent-fg)'
							: catStyle(cat)"
						@click="activeCategory = activeCategory === cat ? '' : cat"
					>
						{{ cat }}
						<span
							class="rounded-full px-1.5"
							:class="activeCategory === cat ? 'bg-black/10' : 'bg-white/10'"
						>{{ cnt }}</span>
					</button>
					<!-- Clear category filter -->
					<button
						v-if="activeCategory"
						type="button"
						class="ml-1 flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold transition"
						style="background:var(--portal-danger-soft);color:var(--portal-danger);border:1px solid rgba(239,68,68,0.2)"
						@click="activeCategory = ''"
					>
						<FeatherIcon name="x" class="h-3 w-3" />
						Clear
					</button>
				</div>
			</div>

			<!-- ── Loading ──────────────────────────────────────────────────── -->
			<div v-if="loadingFiles" class="flex flex-1 items-center justify-center gap-2">
				<span class="h-6 w-6 animate-spin rounded-full border-2 border-t-transparent"
					style="border-color:var(--portal-accent);border-top-color:transparent"></span>
				<span class="text-sm" style="color:var(--portal-subtle)">Loading files…</span>
			</div>

			<!-- ── No project selected ──────────────────────────────────────── -->
			<div v-else-if="!activeProj" class="flex flex-1 flex-col items-center justify-center gap-5 text-center">
				<div
					class="flex h-24 w-24 items-center justify-center rounded-3xl"
					style="background: linear-gradient(135deg,rgba(245,158,11,.06),rgba(56,189,248,.05));"
				>
					<FeatherIcon name="folder" class="h-12 w-12" style="color:var(--portal-border-strong)" />
				</div>
				<div>
					<p class="text-lg font-bold" style="color:var(--portal-text)">Browse project files</p>
					<p class="mt-1 text-sm" style="color:var(--portal-subtle)">Expand a year group and click a project to see its files.</p>
				</div>
			</div>

			<!-- ── Empty ────────────────────────────────────────────────────── -->
			<div v-else-if="cacheEntry && !visibleFiles.length" class="flex flex-1 flex-col items-center justify-center gap-3 text-center">
				<FeatherIcon name="inbox" class="h-12 w-12" style="color:var(--portal-border-strong)" />
				<p class="text-sm font-medium" style="color:var(--portal-muted)">No files match the current filters.</p>
				<button
					class="rounded-xl px-4 py-1.5 text-xs font-medium transition portal-btn"
					@click="fileSearch = ''; activeFolder = ''; activeCategory = ''"
				>Clear filters</button>
			</div>

			<!-- ── File table ────────────────────────────────────────────────── -->
			<div v-else-if="cacheEntry" class="min-h-0 flex-1 overflow-auto">
				<table class="w-full text-sm">
					<thead class="sticky top-0 z-10">
						<tr
							class="border-b text-[10px] font-semibold uppercase tracking-wide"
							style="background:var(--portal-surface);border-color:var(--portal-border);color:var(--portal-muted)"
						>
							<th class="px-5 py-3 text-left">
								<button class="flex items-center gap-1 transition hover:opacity-80" @click="setSort('name')">
									File <FeatherIcon :name="sortIcon('name')" class="h-3 w-3" />
								</button>
							</th>
							<th class="px-5 py-3 text-left">Folder</th>
							<th class="px-5 py-3 text-left">Category</th>
							<th class="px-5 py-3 text-left">
								<button class="flex items-center gap-1 transition hover:opacity-80" @click="setSort('date')">
									Date <FeatherIcon :name="sortIcon('date')" class="h-3 w-3" />
								</button>
							</th>
							<th class="w-36 px-3 py-3 text-center">
								<div class="inline-flex items-center gap-2">
									<span class="inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide"
										style="background:var(--portal-accent-soft);color:var(--portal-accent)">
										<FeatherIcon name="send" class="h-3 w-3" />
										Actions
									</span>
								</div>
							</th>
							<th class="px-5 py-3 text-right">
								<button class="flex items-center gap-1 justify-end transition hover:opacity-80" @click="setSort('size')">
									Size <FeatherIcon :name="sortIcon('size')" class="h-3 w-3" />
								</button>
							</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="f in visibleFiles"
							:key="f.name"
							class="group border-b transition"
							style="border-color:var(--portal-border)"
							@mouseover="e => e.currentTarget.style.background='rgba(245,158,11,0.04)'"
							@mouseleave="e => e.currentTarget.style.background=''"
						>
							<!-- File -->
							<td class="max-w-xs px-5 py-3">
								<a
									v-if="f.file_url"
									:href="f.file_url"
									target="_blank"
									class="flex items-center gap-3"
									style="color:var(--portal-text)"
								>
									<span
										class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-sm transition group-hover:shadow-md"
										style="background:var(--portal-surface-alt)"
									>
										<FeatherIcon :name="extIcon(f.file_name)" class="h-4 w-4" style="color:var(--portal-accent)" />
									</span>
									<span class="min-w-0 truncate font-medium group-hover:underline" style="color:var(--portal-text)">{{ f.file_name }}</span>
								</a>
								<span v-else class="flex items-center gap-3" style="color:var(--portal-muted)">
									<span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl" style="background:var(--portal-surface-alt)">
										<FeatherIcon :name="extIcon(f.file_name)" class="h-4 w-4" style="color:var(--portal-subtle)" />
									</span>
									<span class="truncate">{{ f.file_name }}</span>
								</span>
							</td>
							<!-- Folder chip -->
							<td class="px-5 py-3">
								<button
									v-if="relFolder(f)"
									type="button"
									class="flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-medium transition"
									style="border:1px solid var(--portal-border);background:var(--portal-surface-alt);color:var(--portal-muted)"
									:title="relFolder(f)"
									@click="activeFolder = f.folder; activeCategory = ''"
								>
									<FeatherIcon name="folder" class="h-3 w-3 shrink-0" style="color:var(--portal-accent)" />
									<span class="max-w-[150px] truncate">{{ relFolder(f).split("/").pop() }}</span>
								</button>
								<span v-else class="text-[11px]" style="color:var(--portal-border-strong)">—</span>
							</td>
							<!-- Category -->
							<td class="px-5 py-3">
								<button
									v-if="catFromExt(f.file_name) !== 'Other'"
									type="button"
									class="inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-semibold transition hover:opacity-80"
									:style="catStyle(catFromExt(f.file_name))"
									@click="activeCategory = catFromExt(f.file_name)"
								>{{ catFromExt(f.file_name) }}</button>
								<span v-else class="text-[11px]" style="color:var(--portal-border-strong)">—</span>
							</td>
							<!-- Date -->
							<td class="whitespace-nowrap px-5 py-3 text-xs font-bold" style="color:var(--portal-text)">{{ fmtDate(f.creation) }}</td>
							<!-- Actions: Submit + Share -->
							<td class="px-3 py-3 text-center">
								<div class="flex items-center justify-center gap-1.5">
									<!-- Submit to Client -->
									<button
										type="button"
										class="inline-flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-[11px] font-bold shadow-sm transition active:scale-95"
										style="border-color:rgba(245,158,11,0.35);background:var(--portal-accent-soft);color:var(--portal-accent)"
										title="Submit to 06-CLIENT SUBMITTAL with SL.NO + date naming"
										@click.stop="openSubmitModal(f)"
									>
										<FeatherIcon name="send" class="h-3 w-3" />
										Submit
									</button>
									<!-- Share -->
									<button
										type="button"
										class="inline-flex items-center justify-center rounded-lg border px-2 py-1.5 transition active:scale-95"
										style="border-color:rgba(59,130,246,0.3);background:rgba(59,130,246,0.08);color:#93c5fd"
										title="Share this file with team members"
										@click.stop="openShareModal(f)"
									>
										<FeatherIcon name="share-2" class="h-3.5 w-3.5" />
									</button>
								</div>
							</td>
							<!-- Size -->
							<td class="whitespace-nowrap px-5 py-3 text-right text-xs" style="color:var(--portal-subtle)">{{ fmtSize(f.file_size) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</main>

		<!-- ══ SUBMIT MODAL ══════════════════════════════════════════════════ -->
		<Teleport to="body">
			<div
				v-if="submitModalOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="closeSubmitModal"
			>
				<div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-lg rounded-2xl shadow-2xl" style="background:var(--portal-surface);border:1px solid var(--portal-border)" @click.stop>
					<!-- Header -->
					<div class="flex items-center justify-between gap-3 border-b px-5 py-4" style="border-color:var(--portal-border)">
						<div class="flex items-center gap-3">
							<div class="flex h-10 w-10 items-center justify-center rounded-2xl text-white shadow-md"
								style="background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);">
								<FeatherIcon name="send" class="h-5 w-5" />
							</div>
							<div>
								<h2 class="text-base font-bold" style="color:var(--portal-text)">Submit to Client</h2>
								<p class="text-xs" style="color:var(--portal-muted)">Copies to <strong>06-CLIENT SUBMITTAL</strong> with serial + date naming</p>
							</div>
						</div>
						<button type="button" class="rounded-lg p-1.5 transition" style="color:var(--portal-subtle)" :disabled="submitBusy" @click="closeSubmitModal">
							<FeatherIcon name="x" class="h-4 w-4" />
						</button>
					</div>

					<!-- Body -->
					<div class="space-y-4 px-5 py-5">
						<!-- Source file -->
						<div class="flex items-center gap-3 rounded-xl px-4 py-3" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border)">
							<span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" style="background:var(--portal-surface)">
								<FeatherIcon :name="extIcon(submitFile?.file_name || '')" class="h-5 w-5" style="color:var(--portal-accent)" />
							</span>
							<div class="min-w-0">
								<p class="truncate text-sm font-semibold" style="color:var(--portal-text)">{{ submitFile?.file_name }}</p>
								<p class="text-[11px]" style="color:var(--portal-muted)">{{ relFolder(submitFile) || activeProj?.project_name || "Project root" }}</p>
							</div>
						</div>

						<!-- Generated name preview -->
						<div class="rounded-xl border px-4 py-3" style="border-color:rgba(245,158,11,0.25);background:rgba(245,158,11,0.06)">
							<p class="mb-1.5 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider" style="color:var(--portal-accent)">
								<FeatherIcon name="tag" class="h-3 w-3" />
								Will be saved as
							</p>
							<p class="font-mono text-sm font-bold break-all" style="color:var(--portal-text)">{{ previewSubmitName() }}</p>
							<div class="mt-2 flex flex-wrap gap-3 text-[11px]" style="color:var(--portal-muted)">
								<span class="flex items-center gap-1"><span class="font-bold" style="color:var(--portal-accent)">NN</span> = auto serial (01, 02…)</span>
								<span class="flex items-center gap-1"><span class="font-bold" style="color:var(--portal-accent)">Date</span> = today ({{ todayIso() }})</span>
							</div>
						</div>

						<p v-if="submitError" class="rounded-xl px-3 py-2 text-sm" style="background:var(--portal-danger-soft);color:var(--portal-danger);border:1px solid rgba(239,68,68,0.2)">{{ submitError }}</p>
						<p v-if="submitOk" class="rounded-xl px-3 py-2 text-sm font-medium" style="background:var(--portal-success-soft);color:var(--portal-success);border:1px solid rgba(34,197,94,0.2)">
							<FeatherIcon name="check-circle" class="mr-1 inline h-4 w-4" />{{ submitOk }}
						</p>
					</div>

					<!-- Footer -->
					<div class="flex items-center justify-end gap-2 border-t px-5 py-4" style="border-color:var(--portal-border);background:rgba(0,0,0,0.15)">
						<button
							type="button"
							class="portal-btn rounded-xl px-4 py-2 text-sm font-medium"
							:disabled="submitBusy"
							@click="closeSubmitModal"
						>Cancel</button>
						<button
							type="button"
							class="flex items-center gap-2 rounded-xl px-5 py-2 text-sm font-bold text-white shadow-md transition hover:opacity-90 disabled:opacity-50"
							style="background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);"
							:disabled="submitBusy || !!submitOk"
							@click="confirmSubmitToClient"
						>
							<span v-if="submitBusy" class="flex items-center gap-2">
								<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
								Submitting…
							</span>
							<span v-else class="flex items-center gap-2">
								<FeatherIcon name="send" class="h-4 w-4" />
								Confirm &amp; Submit to Client
							</span>
						</button>
					</div>
				</div>
			</div>
		</Teleport>

		<!-- ══ SHARE MODAL ═══════════════════════════════════════════════════ -->
		<Teleport to="body">
			<div
				v-if="shareModalOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="closeShareModal"
			>
				<div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl shadow-2xl" style="background:var(--portal-surface);border:1px solid var(--portal-border)" @click.stop>
					<!-- Header -->
					<div class="flex items-center justify-between gap-3 border-b px-5 py-4" style="border-color:var(--portal-border)">
						<div class="flex items-center gap-3">
							<div class="flex h-10 w-10 items-center justify-center rounded-2xl shadow-md"
								style="background:rgba(59,130,246,0.15);color:#3b82f6">
								<FeatherIcon name="share-2" class="h-5 w-5" />
							</div>
							<div>
								<h2 class="text-base font-bold" style="color:var(--portal-text)">Share File</h2>
								<p class="max-w-[220px] truncate text-xs" style="color:var(--portal-muted)">{{ shareFile?.file_name }}</p>
							</div>
						</div>
						<button type="button" class="rounded-lg p-1.5 transition" style="color:var(--portal-subtle)" @click="closeShareModal">
							<FeatherIcon name="x" class="h-4 w-4" />
						</button>
					</div>

					<!-- Body -->
					<div class="px-5 py-4 space-y-4">

						<!-- User search -->
						<div>
							<label class="mb-1.5 block text-[11px] font-semibold uppercase tracking-wider" style="color:var(--portal-muted)">
								Add people
							</label>
							<div class="relative">
								<FeatherIcon name="search" class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2" style="color:var(--portal-subtle)" />
								<input
									v-model="shareSearch"
									type="text"
									placeholder="Search by name or email…"
									class="w-full rounded-xl py-2.5 pl-9 pr-3 text-sm transition focus:outline-none"
									style="border:1px solid var(--portal-border);background:var(--portal-surface-alt);color:var(--portal-text)"
									@input="onShareSearch(shareSearch)"
								/>
								<span v-if="searchBusy" class="absolute right-3 top-1/2 -translate-y-1/2">
									<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-t-transparent inline-block"
										style="border-color:var(--portal-accent);border-top-color:transparent"></span>
								</span>
							</div>
							<!-- Dropdown results -->
							<div v-if="shareResults.length"
								class="mt-1 rounded-xl border overflow-hidden shadow-lg"
								style="border-color:var(--portal-border);background:var(--portal-surface-dropdown)">
								<button
									v-for="u in shareResults"
									:key="u.name"
									type="button"
									class="flex w-full items-center gap-3 px-3 py-2.5 text-left transition"
									style="color:var(--portal-text)"
									@mouseover="e => e.currentTarget.style.background='rgba(59,130,246,0.08)'"
									@mouseleave="e => e.currentTarget.style.background=''"
									@click="addShare(u)"
								>
									<span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
										:style="`background:hsl(${Math.abs(u.name.charCodeAt(0) * 37) % 360},60%,45%)`">
										{{ (u.full_name || u.name || '?')[0].toUpperCase() }}
									</span>
									<span class="min-w-0 flex-1">
										<p class="truncate text-sm font-semibold" style="color:var(--portal-text)">{{ u.full_name || u.name }}</p>
										<p class="truncate text-[11px]" style="color:var(--portal-muted)">{{ u.email || u.name }}</p>
									</span>
									<span v-if="sharingSet.has(u.name)" class="shrink-0">
										<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-t-transparent inline-block"
											style="border-color:#3b82f6;border-top-color:transparent"></span>
									</span>
									<FeatherIcon v-else name="plus" class="h-3.5 w-3.5 shrink-0" style="color:#3b82f6" />
								</button>
							</div>
							<p v-else-if="shareSearch.trim() && !searchBusy" class="mt-1 text-xs" style="color:var(--portal-subtle)">No users found.</p>
						</div>

						<!-- Error -->
						<p v-if="shareError" class="rounded-xl px-3 py-2 text-xs" style="background:var(--portal-danger-soft);color:var(--portal-danger)">{{ shareError }}</p>

						<!-- Existing shares -->
						<div>
							<div class="mb-2 flex items-center justify-between">
								<span class="text-[11px] font-semibold uppercase tracking-wider" style="color:var(--portal-muted)">
									Shared with
								</span>
								<span class="rounded-full px-2 py-0.5 text-[10px] font-bold"
									style="background:var(--portal-accent-soft);color:var(--portal-accent)">
									{{ sharesList.length }}
								</span>
							</div>

							<!-- Loading -->
							<div v-if="sharesLoading" class="flex items-center gap-2 py-3" style="color:var(--portal-subtle)">
								<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-t-transparent"
									style="border-color:var(--portal-accent);border-top-color:transparent"></span>
								<span class="text-xs">Loading…</span>
							</div>

							<!-- Empty state -->
							<div v-else-if="!sharesList.length"
								class="rounded-xl border border-dashed py-6 text-center"
								style="border-color:var(--portal-border-strong)">
								<FeatherIcon name="users" class="mx-auto h-8 w-8 mb-2" style="color:var(--portal-border-strong)" />
								<p class="text-xs" style="color:var(--portal-subtle)">Not shared with anyone yet.</p>
								<p class="text-[11px] mt-0.5" style="color:var(--portal-border-strong)">Use the search above to add teammates.</p>
							</div>

							<!-- Shares list -->
							<div v-else class="space-y-2 max-h-56 overflow-y-auto">
								<div
									v-for="sh in sharesList"
									:key="sh.name"
									class="flex items-center gap-3 rounded-xl px-3 py-2.5"
									style="background:var(--portal-surface-alt);border:1px solid var(--portal-border)"
								>
									<!-- Avatar -->
									<span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
										:style="`background:hsl(${Math.abs((sh.user||'').charCodeAt(0) * 37) % 360},60%,40%)`">
										{{ shareInitials(sh) }}
									</span>
									<!-- Info -->
									<div class="min-w-0 flex-1">
										<p class="truncate text-sm font-semibold" style="color:var(--portal-text)">{{ sh.user_full_name || sh.user }}</p>
										<p class="truncate text-[11px]" style="color:var(--portal-subtle)">
											{{ sh.user_email || sh.user }}
											<span v-if="shareExpiry(sh)" class="ml-1 opacity-70">· {{ shareExpiry(sh) }}</span>
										</p>
									</div>
									<!-- Revoke -->
									<button
										type="button"
										class="flex shrink-0 items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold transition"
										style="background:var(--portal-danger-soft);color:var(--portal-danger);border:1px solid rgba(239,68,68,0.2)"
										:disabled="revokingSet.has(sh.name)"
										@click="revokeShare(sh)"
									>
										<span v-if="revokingSet.has(sh.name)" class="h-3 w-3 animate-spin rounded-full border border-t-transparent inline-block"
											style="border-color:var(--portal-danger);border-top-color:transparent"></span>
										<FeatherIcon v-else name="x" class="h-3 w-3" />
										Revoke
									</button>
								</div>
							</div>
						</div>
					</div>

					<!-- Footer -->
					<div class="flex items-center justify-end border-t px-5 py-3" style="border-color:var(--portal-border);background:rgba(0,0,0,0.1)">
						<button type="button" class="portal-btn rounded-xl px-4 py-2 text-sm font-medium" @click="closeShareModal">Done</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
