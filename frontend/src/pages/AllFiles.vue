<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { call } from "@/api";
import { FeatherIcon } from "frappe-ui";

// ── Projects ──────────────────────────────────────────────────────────────────
const projects     = ref([]);
const projSearch   = ref("");
const loadingProj  = ref(false);

// ── Per-project file cache ────────────────────────────────────────────────────
const projCache    = reactive({});          // { [projName]: { files, folders, root } }
const activeProj   = ref(null);
const activeFolder = ref("");
const fileSearch   = ref("");
const activeCategory = ref("");
const sortKey      = ref("date");           // "name" | "date" | "size"
const sortAsc      = ref(false);
const loadingFiles = ref(false);

// ── Sidebar expand state ─────────────────────────────────────────────────────
const expandedYears = ref(new Set(["2026", "2025"]));
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
	".dwg": "Drawing", ".dxf": "Drawing",
	".skp": "3D Model", ".rvt": "3D Model", ".rfa": "3D Model", ".max": "3D Model",
	".3dm": "3D Model", ".fbx": "3D Model", ".obj": "3D Model", ".dae": "3D Model",
	".xlsx": "Feasibility", ".xls": "Feasibility", ".xlsm": "Feasibility", ".csv": "Feasibility",
	".psd": "Design Source", ".psb": "Design Source", ".ai": "Design Source",
	".indd": "Design Source", ".idml": "Design Source",
	".jpg": "Renders", ".jpeg": "Renders", ".png": "Renders",
	".tif": "Renders", ".tiff": "Renders",
	".pdf": "Presentation",
};
function catFromExt(name) { return CAT_MAP[getExt(name)] || "Other"; }

const CAT_STYLE = {
	"Presentation":  "bg-purple-100 text-purple-800",
	"Drawing":       "bg-blue-100   text-blue-800",
	"3D Model":      "bg-cyan-100   text-cyan-800",
	"Feasibility":   "bg-green-100  text-green-800",
	"Design Source": "bg-orange-100 text-orange-800",
	"Renders":       "bg-pink-100   text-pink-800",
	"Other":         "bg-gray-100   text-gray-600",
};
function catStyle(cat) { return CAT_STYLE[cat] || "bg-gray-100 text-gray-600"; }

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
	// Sort: 2026 first, then descending, then "Other" last
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
		activeProj.value  = null;
		activeFolder.value = "";
		activeCategory.value = "";
		return;
	}
	activeProj.value  = p;
	activeFolder.value = "";
	activeCategory.value = "";
	if (projCache[p.name]) return; // already loaded
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

// ── Current project data ──────────────────────────────────────────────────────
const cacheEntry  = computed(() => activeProj.value ? (projCache[activeProj.value.name] || null) : null);
const allFiles    = computed(() => cacheEntry.value?.files  || []);
const allFolders  = computed(() => cacheEntry.value?.folders || []);
const projectRoot = computed(() => cacheEntry.value?.root   || "");

// ── Folder tree (flat ordered list) ──────────────────────────────────────────
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

// ── Relative folder path ─────────────────────────────────────────────────────
function relFolder(file) {
	const root = projectRoot.value;
	const fo   = file.folder || "";
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

// ── Breadcrumb label ──────────────────────────────────────────────────────────
const folderLabel = computed(() => {
	if (!activeFolder.value || activeFolder.value === projectRoot.value) return "";
	return allFolders.value.find(f => f.name === activeFolder.value)?.label || "";
});

onMounted(async () => {
	loadingProj.value = true;
	try {
		const res = await call({ method: "portal_app.api.projects.list_projects" });
		projects.value = res?.projects || [];
	} finally {
		loadingProj.value = false;
	}
});

// Reset folder/category when project changes
watch(activeProj, () => {
	expandedFolders.value = new Set();
	activeCategory.value  = "";
});

import { reactive } from "vue";
</script>

<template>
	<div class="flex h-full overflow-hidden" style="background: #f4f6fb;">

		<!-- ══ LEFT SIDEBAR ═══════════════════════════════════════════════════ -->
		<aside
			class="flex w-80 shrink-0 flex-col overflow-hidden"
			style="
				background: linear-gradient(180deg,#ffffff 0%,#f8faff 100%);
				border-right: 1px solid rgba(99,102,241,.15);
				box-shadow: 2px 0 16px rgba(79,70,229,.06);
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
						<p class="text-sm font-bold leading-tight text-[color:var(--portal-text)]">File Browser</p>
						<p class="text-[10px] text-[color:var(--portal-subtle)]">Browse by year · project · folder</p>
					</div>
				</div>
				<div class="relative">
					<FeatherIcon name="search" class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
					<input
						v-model="projSearch"
						type="search"
						placeholder="Search projects…"
						class="w-full rounded-xl border border-gray-200 bg-gray-50 py-2 pl-9 pr-3 text-sm shadow-sm transition focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-200"
					/>
				</div>
			</div>

			<!-- Loading -->
			<div v-if="loadingProj" class="flex flex-1 items-center justify-center">
				<span class="h-5 w-5 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></span>
			</div>

			<!-- Year → Project → Folder tree -->
			<div v-else class="min-h-0 flex-1 overflow-y-auto px-2 pb-4">

				<template v-for="group in yearGroups" :key="group.year">
					<!-- Year header -->
					<button
						type="button"
						class="mt-1.5 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left transition hover:bg-indigo-50/60"
						@click="expandedYears.has(group.year) ? expandedYears.delete(group.year) : expandedYears.add(group.year)"
					>
						<FeatherIcon
							:name="expandedYears.has(group.year) ? 'chevron-down' : 'chevron-right'"
							class="h-3.5 w-3.5 shrink-0 text-indigo-400 transition-transform"
						/>
						<span class="flex-1 text-sm font-bold text-[color:var(--portal-text)]">
							{{ group.year === "0" ? "Other" : group.year }}
						</span>
						<span class="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-700">
							{{ group.projects.length }}
						</span>
					</button>

					<!-- Projects under this year -->
					<template v-if="expandedYears.has(group.year)">
						<template v-for="p in group.projects" :key="p.name">
							<!-- Project row -->
							<button
								type="button"
								class="ml-2 mt-0.5 flex w-[calc(100%-0.5rem)] items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition"
								:class="
									activeProj?.name === p.name
										? 'font-semibold shadow-sm'
										: 'text-gray-700 hover:bg-white hover:shadow-sm'
								"
								:style="
									activeProj?.name === p.name
										? 'background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%); color:#fff;'
										: ''
								"
								@click="openProject(p)"
							>
								<span
									class="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg"
									:style="
										activeProj?.name === p.name
											? 'background:rgba(255,255,255,0.25); color:#fff;'
											: 'background:#e0e7ff; color:var(--portal-accent);'
									"
								>
									<FeatherIcon :name="activeProj?.name === p.name ? 'folder-open' : 'folder'" class="h-3.5 w-3.5" />
								</span>
								<span class="min-w-0 flex-1 truncate leading-snug" :title="p.project_name">{{ p.project_name }}</span>
								<span
									v-if="projCache[p.name]"
									class="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold" :class="activeProj?.name === p.name ? 'bg-white/20 text-white' : 'bg-indigo-100 text-indigo-600'"
								>{{ projCache[p.name].files.length }}</span>
								<FeatherIcon
									v-if="activeProj?.name === p.name"
									name="chevron-down"
									class="h-3 w-3 shrink-0 text-indigo-400"
								/>
							</button>

							<!-- Folder tree (inline under project) -->
							<template v-if="activeProj?.name === p.name && !loadingFiles && cacheEntry">
								<div class="ml-8 mt-0.5 space-y-0.5">
									<button
										v-for="node in flatTree"
										:key="node.key"
										type="button"
										class="flex w-full items-center gap-1.5 rounded-lg py-1.5 pr-2 text-left text-xs transition"
										:style="{ paddingLeft: `${0.5 + node.depth * 0.65}rem` }"
										:class="
											activeFolder === node.name
												? 'font-bold text-indigo-800 bg-indigo-100'
												: 'text-gray-600 hover:bg-indigo-50/70 hover:text-gray-900'
										"
										
										@click="activeFolder = node.name; activeCategory = ''"
									>
										<button
											v-if="hasFolderChildren(node.key)"
											type="button"
											class="flex h-4 w-4 shrink-0 items-center justify-center rounded text-gray-400 hover:bg-gray-200"
											@click.stop="toggleFolder(node.key)"
										>
											<FeatherIcon :name="expandedFolders.has(node.key) || node.isRoot ? 'chevron-down' : 'chevron-right'" class="h-2.5 w-2.5" />
										</button>
										<span v-else class="h-4 w-4 shrink-0"></span>
										<FeatherIcon
											:name="activeFolder === node.name ? 'folder-open' : 'folder'"
											class="h-3.5 w-3.5 shrink-0"
											:class="activeFolder === node.name ? 'text-indigo-700' : 'text-gray-400'"
										/>
										<span class="min-w-0 flex-1 truncate">{{ node.label }}</span>
										<span
											v-if="folderFileCount(node)"
											class="ml-1 shrink-0 rounded-full px-1.5 py-0.5 text-[10px]"
											:class="activeFolder === node.name ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-500'"
										>{{ folderFileCount(node) }}</span>
									</button>
								</div>
								<!-- Loading indicator inside project -->
								<div v-if="loadingFiles" class="ml-8 mt-1 flex items-center gap-1.5 py-1 text-xs text-gray-400">
									<span class="h-3 w-3 animate-spin rounded-full border border-indigo-400 border-t-transparent"></span>
									Loading…
								</div>
							</template>
						</template>
					</template>
				</template>

				<p v-if="!yearGroups.length" class="py-10 text-center text-xs text-gray-400">
					{{ projSearch ? "No projects match." : "No projects found." }}
				</p>
			</div>
		</aside>

		<!-- ══ MAIN PANEL ════════════════════════════════════════════════════ -->
		<main class="flex min-w-0 flex-1 flex-col overflow-hidden">

			<!-- ── Top bar ─────────────────────────────────────────────────── -->
			<div
				class="shrink-0 border-b px-5 py-3"
				style="background: rgba(255,255,255,0.92); backdrop-filter: blur(8px); border-color: rgba(99,102,241,.1); box-shadow: 0 1px 8px rgba(79,70,229,.04);"
			>
				<div class="flex flex-wrap items-center gap-3">
					<!-- Breadcrumb -->
					<div class="flex min-w-0 flex-1 items-center gap-1.5 text-sm">
						<template v-if="activeProj">
							<FeatherIcon name="folder-open" class="h-4 w-4 shrink-0 text-indigo-500" />
							<button
								class="font-semibold text-gray-800 transition hover:text-indigo-600"
								@click="activeFolder = ''; activeCategory = ''"
							>{{ activeProj.project_name }}</button>
							<template v-if="folderLabel">
								<FeatherIcon name="chevron-right" class="h-3.5 w-3.5 shrink-0 text-gray-300" />
								<span class="truncate text-gray-500">{{ folderLabel }}</span>
								<button
									class="flex h-5 w-5 items-center justify-center rounded-full text-gray-400 transition hover:bg-gray-200"
									@click="activeFolder = ''; activeCategory = ''"
								>
									<FeatherIcon name="x" class="h-3 w-3" />
								</button>
							</template>
						</template>
						<span v-else class="text-gray-400">Select a project from the sidebar</span>
					</div>

					<template v-if="activeProj && !loadingFiles && cacheEntry">
						<!-- File search -->
						<div class="relative w-48 shrink-0">
							<FeatherIcon name="search" class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
							<input
								v-model="fileSearch"
								type="search"
								placeholder="Search files…"
								class="w-full rounded-xl border border-gray-200 bg-gray-50 py-1.5 pl-8 pr-3 text-sm transition focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-200"
							/>
						</div>
						<!-- File count pill -->
						<span class="shrink-0 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
							{{ visibleFiles.length }} / {{ allFiles.length }} files
						</span>
					</template>
				</div>

				<!-- Category filter chips -->
				<div v-if="activeProj && cacheEntry && categoryTotals.length" class="mt-2.5 flex flex-wrap items-center gap-1.5">
					<button
						type="button"
						class="rounded-full px-3 py-1 text-xs font-semibold transition"
						:class="
							!activeCategory
								? 'bg-indigo-600 text-white shadow-sm'
								: 'bg-gray-100 text-gray-600 hover:bg-indigo-50 hover:text-indigo-700'
						"
						@click="activeCategory = ''"
					>All</button>
					<button
						v-for="[cat, cnt] in categoryTotals"
						:key="cat"
						type="button"
						class="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition"
						:class="
							activeCategory === cat
								? 'bg-indigo-600 text-white shadow-sm'
								: `${catStyle(cat)} hover:opacity-90`
						"
						@click="activeCategory = activeCategory === cat ? '' : cat"
					>
						{{ cat }}
						<span
							class="rounded-full px-1.5"
							:class="activeCategory === cat ? 'bg-white/30' : 'bg-black/10'"
						>{{ cnt }}</span>
					</button>
					<!-- Clear category filter -->
					<button
						v-if="activeCategory"
						type="button"
						class="ml-1 flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600 transition hover:bg-red-100"
						@click="activeCategory = ''"
					>
						<FeatherIcon name="x" class="h-3 w-3" />
						Clear
					</button>
				</div>
			</div>

			<!-- ── Loading ──────────────────────────────────────────────────── -->
			<div v-if="loadingFiles" class="flex flex-1 items-center justify-center gap-2">
				<span class="h-6 w-6 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"></span>
				<span class="text-sm text-gray-400">Loading files…</span>
			</div>

			<!-- ── No project selected ──────────────────────────────────────── -->
			<div v-else-if="!activeProj" class="flex flex-1 flex-col items-center justify-center gap-5 text-center">
				<div
					class="flex h-24 w-24 items-center justify-center rounded-3xl"
					style="background: linear-gradient(135deg,rgba(79,70,229,.06),rgba(56,189,248,.05));"
				>
					<FeatherIcon name="folder" class="h-12 w-12 text-indigo-200" />
				</div>
				<div>
					<p class="text-lg font-bold text-gray-700">Browse project files</p>
					<p class="mt-1 text-sm text-gray-400">Expand a year group and click a project to see its files.</p>
				</div>
			</div>

			<!-- ── Empty ────────────────────────────────────────────────────── -->
			<div v-else-if="cacheEntry && !visibleFiles.length" class="flex flex-1 flex-col items-center justify-center gap-3 text-center">
				<FeatherIcon name="inbox" class="h-12 w-12 text-gray-300" />
				<p class="text-sm font-medium text-gray-500">No files match the current filters.</p>
				<button
					class="rounded-xl border border-gray-200 bg-white px-4 py-1.5 text-xs font-medium text-gray-600 shadow-sm transition hover:bg-gray-50"
					@click="fileSearch = ''; activeFolder = ''; activeCategory = ''"
				>Clear filters</button>
			</div>

			<!-- ── File table ────────────────────────────────────────────────── -->
			<div v-else-if="cacheEntry" class="min-h-0 flex-1 overflow-auto">
				<table class="w-full text-sm">
					<thead class="sticky top-0 z-10">
						<tr
							class="border-b text-[10px] font-semibold uppercase tracking-wide text-gray-500"
							style="background:rgba(248,249,252,0.96); backdrop-filter:blur(6px); border-color:rgba(99,102,241,.1);"
						>
							<th class="px-5 py-3 text-left">
								<button class="flex items-center gap-1 transition hover:text-indigo-600" @click="setSort('name')">
									File <FeatherIcon :name="sortIcon('name')" class="h-3 w-3" />
								</button>
							</th>
							<th class="px-5 py-3 text-left">Folder</th>
							<th class="px-5 py-3 text-left">Category</th>
							<th class="px-5 py-3 text-left">
								<button class="flex items-center gap-1 transition hover:text-indigo-600" @click="setSort('date')">
									Date <FeatherIcon :name="sortIcon('date')" class="h-3 w-3" />
								</button>
							</th>
							<th class="px-5 py-3 text-right">
								<button class="flex items-center gap-1 justify-end transition hover:text-indigo-600" @click="setSort('size')">
									Size <FeatherIcon :name="sortIcon('size')" class="h-3 w-3" />
								</button>
							</th>
						</tr>
					</thead>
					<tbody class="divide-y" style="divide-color: rgba(99,102,241,.06);">
						<tr
							v-for="f in visibleFiles"
							:key="f.name"
							class="group transition hover:bg-indigo-50/30"
						>
							<!-- File -->
							<td class="max-w-xs px-5 py-3">
								<a
									v-if="f.file_url"
									:href="f.file_url"
									target="_blank"
									class="flex items-center gap-3 text-gray-800"
								>
									<span
										class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-sm transition group-hover:shadow-md"
										style="background: linear-gradient(135deg,rgba(79,70,229,.08),rgba(56,189,248,.08));"
									>
										<FeatherIcon :name="extIcon(f.file_name)" class="h-4 w-4 text-indigo-500" />
									</span>
									<span class="min-w-0 truncate font-medium group-hover:text-indigo-700 group-hover:underline">{{ f.file_name }}</span>
								</a>
								<span v-else class="flex items-center gap-3 text-gray-700">
									<span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gray-100">
										<FeatherIcon :name="extIcon(f.file_name)" class="h-4 w-4 text-gray-400" />
									</span>
									<span class="truncate">{{ f.file_name }}</span>
								</span>
							</td>
							<!-- Folder chip -->
							<td class="px-5 py-3">
								<button
									v-if="relFolder(f)"
									type="button"
									class="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-[11px] font-medium text-gray-500 shadow-sm transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
									:title="relFolder(f)"
									@click="activeFolder = f.folder; activeCategory = ''"
								>
									<FeatherIcon name="folder" class="h-3 w-3 shrink-0" />
									<span class="max-w-[150px] truncate">{{ relFolder(f).split("/").pop() }}</span>
								</button>
								<span v-else class="text-[11px] text-gray-300">—</span>
							</td>
							<!-- Category -->
							<td class="px-5 py-3">
								<button
									v-if="catFromExt(f.file_name) !== 'Other'"
									type="button"
									class="inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-semibold transition hover:opacity-80"
									:class="catStyle(catFromExt(f.file_name))"
									@click="activeCategory = catFromExt(f.file_name)"
								>{{ catFromExt(f.file_name) }}</button>
								<span v-else class="text-[11px] text-gray-300">—</span>
							</td>
							<!-- Date -->
							<td class="whitespace-nowrap px-5 py-3 text-xs text-gray-400">{{ fmtDate(f.creation) }}</td>
							<!-- Size -->
							<td class="whitespace-nowrap px-5 py-3 text-right text-xs text-gray-400">{{ fmtSize(f.file_size) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</main>
	</div>
</template>
