<script setup>
import { ref, computed, watch, nextTick, onMounted } from "vue";
import { call, uploadFile } from "@/api";
import { FeatherIcon } from "frappe-ui";

const props = defineProps({
	project: { type: String, required: true },
	folders: { type: Array, default: () => [] },
	projectRootPath: { type: String, default: "" },
	allowShare: { type: Boolean, default: false },
	disabled: { type: Boolean, default: false },
});

const emit = defineEmits(["uploaded", "openShare"]);

const isPrivateUpload = ref(false);
const destination = ref("erpnext");
const externalProvider = ref("frappe_drive");
const targetFolder = ref("");
const advancedUploadOpen = ref(false);

const fileInput = ref(null);
const folderInput = ref(null);
const uploadCardRef = ref(null);
const dragOver = ref(false);
const uploadBusy = ref(false);
const uploadError = ref("");
const uploadInfo = ref("");

const folderPickerOpen = ref(false);
const folderPickerSearch = ref("");
const folderPickerExpanded = ref(new Set());

// Confirm-before-upload modal — same flow as the Files hub: stage picked / dropped files
// so the user can review the auto-generated name (which embeds today's date), the category
// (target folder), and the date itself before the actual upload runs.
const confirmUploadOpen = ref(false);
const pendingUploads = ref([]);
// Folder upload — set when the user picks/drops a directory. Files preserve their
// internal structure under a wrapping folder named with the simplified pattern
// (`<categoryNumberPrefix>_<date>`); same-day repeats get `_v2`, `_v3`.
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
onMounted(loadFileTypes);

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

// Wrapping-folder name pattern: take the leading number of the category leaf
// (e.g. "01" from "01-DOCUMENTS", "02" from "02-FEASIBILITY") + ISO date.
// Falls back to the category slug when there's no number prefix.
function categoryNumberPrefix(categoryName) {
	const label = folderLabelByName.value?.[categoryName] || categoryName || "";
	const leaf = String(label).split("/").pop() || "";
	const match = leaf.trim().match(/^(\d+)/);
	if (match) return match[1];
	return categoryToSlug(categoryName);
}
function buildWrapperName(categoryName, isoDate) {
	return `${categoryNumberPrefix(categoryName)}_${isoDate}`;
}

// Walk a webkitGetAsEntry directory tree, collecting `[{file, relativePath}]`.
function _readEntry(entry, path, out) {
	return new Promise((resolve) => {
		if (!entry) return resolve();
		if (entry.isFile) {
			entry.file((f) => {
				out.push({ file: f, relativePath: path });
				resolve();
			}, () => resolve());
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
		} else {
			resolve();
		}
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

function fmtFileSize(bytes) {
	if (bytes == null) return "—";
	const n = Number(bytes);
	if (Number.isNaN(n) || !n) return "—";
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
	if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
	return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`;
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

function folderOptionLabel(label) {
	const path = String(label || "");
	if (!path) return "";
	const parts = path.split("/");
	if (parts.length <= 1) return path;
	return `${"  ".repeat(parts.length - 1)}↳ ${parts[parts.length - 1]}  (${parts.slice(0, -1).join(" / ")})`;
}

watch(
	() => props.folders,
	(list) => {
		if (!list?.length) return;
		if (!targetFolder.value || !list.some((f) => f.name === targetFolder.value)) {
			targetFolder.value = list[0]?.name || "";
		}
	},
	{ immediate: true },
);

const folderLabelByName = computed(() => {
	const map = {};
	if (props.projectRootPath) map[props.projectRootPath] = "Project folder (all files)";
	for (const f of props.folders) map[f.name] = f.label;
	return map;
});

const targetFolderEntry = computed(
	() => props.folders.find((f) => f.name === targetFolder.value) || null,
);
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
	const root = { children: new Map() };
	for (const f of props.folders) {
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
					depth: i + 1,
				});
			} else if (i === segments.length - 1) {
				const node = cursor.children.get(seg);
				node.name = f.name;
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
	if (props.disabled) return;
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
	next.has(label) ? next.delete(label) : next.add(label);
	folderPickerExpanded.value = next;
}
async function pickFolder(name) {
	if (!name) return;
	targetFolder.value = name;
	folderPickerOpen.value = false;
	await nextTick();
	uploadCardRef.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function apiErr(e) {
	const body = e?.responseBody;
	if (body?._server_messages) {
		try {
			const arr = JSON.parse(body._server_messages);
			if (arr.length) return JSON.parse(arr[0]).message || arr[0];
		} catch {
			/* ignore */
		}
	}
	return e?.message || "Something went wrong.";
}

// Stage the dropped/picked files into the confirmation modal. Actual upload only runs when
// the user confirms in `confirmUploadAndRun`.
function handleFiles(fileList) {
	if (!fileList?.length) return;
	if (!props.project) {
		uploadError.value =
			"No project selected for this upload. Open a project (or pick one on the Files page) and try again.";
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
		return {
			originalFile: f,
			base,
			ext,
			name: buildAutoName(base, ext, today, categoryToSlug(category)),
			category,
			date: today,
			nameEdited: false,
			fileType: detectFileType(f.name),
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

async function _prepareWrapper(category, isoDate) {
	const wrapperBase = buildWrapperName(category, isoDate);
	const prep = await call({
		method: "portal_app.api.files.prepare_folder_upload",
		type: "POST",
		args: {
			project: props.project,
			target_folder: category,
			folder_name: wrapperBase,
		},
	});
	if (!prep?.folder_name) throw new Error("Folder reservation failed.");
	return { fileDoc: prep.folder_name, label: prep.folder_label || wrapperBase, baseName: prep.file_name || wrapperBase };
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
	let count = 0;
	try {
		// Group rows by category so each category gets its own wrapping folder this session.
		const byCategory = new Map();
		for (const r of pendingUploads.value) {
			if (!byCategory.has(r.category)) byCategory.set(r.category, []);
			byCategory.get(r.category).push(r);
		}
		const today = todayIso();
		for (const [category, rows] of byCategory) {
			const wrapper = await _prepareWrapper(category, today);
			lastFolderLabel = wrapper.label;
			for (const r of rows) {
				const renamed = new File([r.originalFile], r.name.trim(), {
					type: r.originalFile.type,
					lastModified: r.originalFile.lastModified,
				});
				await uploadFile("portal_app.api.files.upload_project_file", renamed, {
					project: props.project,
					is_private: isPrivateUpload.value ? "1" : "0",
					destination: destination.value,
					external_provider: externalProvider.value,
					target_folder: wrapper.fileDoc,
					relative_path: "",
					file_type: r.fileType || "",
				});
				count += 1;
			}
		}
		if (count) {
			const first = pendingUploads.value[0];
			const firstName = first?.name?.trim() || "";
			const when = fmtDate(new Date().toISOString());
			if (count === 1) {
				uploadInfo.value = `Uploaded “${firstName}” to ${lastFolderLabel} on ${when}.`;
			} else {
				uploadInfo.value = `Uploaded ${count} files (incl. “${firstName}”) to ${lastFolderLabel} on ${when}.`;
			}
		}
		emit("uploaded", { count, folderLabel: lastFolderLabel });
		setTimeout(() => (uploadInfo.value = ""), 6000);
		confirmUploadOpen.value = false;
		pendingUploads.value = [];
	} catch (e) {
		uploadError.value = apiErr(e);
	} finally {
		uploadBusy.value = false;
	}
}

// --- Folder upload mode -----------------------------------------------------
// Stage a directory upload (FileList from `<input webkitdirectory>` or entries from a
// dropped folder). Files preserve their internal structure under a wrapping folder
// auto-named `<categoryNumberPrefix>_<date>` (with `_v2`, `_v3` for same-day repeats).
function stageFolderUpload(entries) {
	const items = (entries || []).filter((e) => e.file);
	if (!items.length) return false;
	if (!props.project) {
		uploadError.value = "No project selected for this upload.";
		return false;
	}
	if (!targetFolder.value) {
		uploadError.value = "Pick a target subfolder before uploading.";
		return false;
	}
	const firstSeg = (p) => String(p || "").split("/")[0] || "";
	const roots = new Set(items.map((it) => firstSeg(it.relativePath || it.file.webkitRelativePath || "")).filter(Boolean));
	if (roots.size !== 1) {
		uploadError.value = "Pick or drop exactly one folder.";
		return false;
	}
	const sourceName = [...roots][0];
	const today = todayIso();
	pendingFolder.value = {
		sourceName,
		category: targetFolder.value,
		date: today,
		entries: items.map((it) => {
			const p = String(it.relativePath || it.file.webkitRelativePath || "");
			const trimmed = p.startsWith(sourceName + "/") ? p.slice(sourceName.length + 1) : "";
			const slashIdx = trimmed.lastIndexOf("/");
			const relativeDir = slashIdx >= 0 ? trimmed.slice(0, slashIdx) : "";
			return { file: it.file, relativeDir };
		}),
	};
	pendingUploads.value = [];
	uploadError.value = "";
	uploadInfo.value = "";
	confirmUploadOpen.value = true;
	return true;
}

const pendingFolderWrapperName = computed(() => {
	const f = pendingFolder.value;
	if (!f) return "";
	return buildWrapperName(f.category, f.date);
});

async function confirmFolderUploadAndRun() {
	const f = pendingFolder.value;
	if (!f) return;
	if (!f.category) { uploadError.value = "Folder needs a category (target folder)."; return; }
	uploadBusy.value = true;
	uploadError.value = "";
	uploadInfo.value = "";
	try {
		const wrapper = await _prepareWrapper(f.category, f.date);
		for (const e of f.entries) {
			await uploadFile("portal_app.api.files.upload_project_file", e.file, {
				project: props.project,
				is_private: isPrivateUpload.value ? "1" : "0",
				destination: destination.value,
				external_provider: externalProvider.value,
				target_folder: wrapper.fileDoc,
				relative_path: e.relativeDir || "",
			});
		}
		const when = fmtDate(new Date().toISOString());
		const fileCount = f.entries.length;
		uploadInfo.value = `Uploaded folder “${wrapper.baseName}” (${fileCount} file${fileCount === 1 ? "" : "s"}) to ${wrapper.label} on ${when}.`;
		emit("uploaded", { count: fileCount, folderLabel: wrapper.label, folderUpload: true });
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
	if (input) input.value = "";
}
function onFolderInput(e) {
	const input = e.target;
	const list = Array.from(input.files || []);
	const entries = list.map((f) => ({ file: f, relativePath: f.webkitRelativePath || "" }));
	stageFolderUpload(entries);
	if (input) input.value = "";
}
async function onDrop(e) {
	dragOver.value = false;
	const dt = e.dataTransfer;
	if (!dt) return;
	if (await _dropContainsDirectory(dt)) {
		const collected = await collectFromDataTransfer(dt);
		stageFolderUpload(collected);
		return;
	}
	handleFiles(dt.files);
}

function onShareClick() {
	if (!props.allowShare || !targetFolder.value) return;
	emit("openShare", targetFolder.value);
}

defineExpose({ uploadCardRef, scrollIntoView: () => uploadCardRef.value?.scrollIntoView({ behavior: "smooth", block: "start" }) });
</script>

<template>
	<div ref="uploadCardRef" class="portal-card-strong space-y-3 p-5">
		<div class="flex flex-wrap items-stretch gap-3">
			<button
				type="button"
				class="group flex min-w-0 flex-1 items-center gap-3 rounded-2xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-4 py-3 text-left transition hover:border-[color:var(--portal-accent)] hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
				:disabled="disabled || !folders.length"
				@click="openFolderPicker"
			>
				<span
					class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white"
					style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
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
					v-if="allowShare && targetFolder"
					class="portal-btn"
					:title="'Share “' + (folderLabelByName[targetFolder] || targetFolder) + '”'"
					@click="onShareClick"
				>
					<FeatherIcon name="share-2" class="h-4 w-4" />
					Share
				</button>
				<button
					class="portal-btn"
					:disabled="disabled || !targetFolder || uploadBusy"
					title="Upload an entire folder (structure preserved)"
					@click="folderInput?.click()"
				>
					<FeatherIcon name="folder-plus" class="h-4 w-4" />
					Upload folder
				</button>
				<button
					class="portal-btn portal-btn-primary"
					:disabled="disabled || !targetFolder || uploadBusy"
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
				style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%); color: #fff;"
			>
				<FeatherIcon name="upload-cloud" class="h-5 w-5" />
			</div>
			<p class="font-medium text-[color:var(--portal-text)]">Drop files or a folder here, or click to upload</p>
			<p class="text-xs text-[color:var(--portal-muted)]">
				Goes into <strong class="text-[color:var(--portal-text)]">{{ folderLabelByName[targetFolder] || targetFolder || "—" }}</strong>
			</p>
			<input ref="fileInput" type="file" class="hidden" multiple @change="onFileInput" />
			<input ref="folderInput" type="file" class="hidden" webkitdirectory directory multiple @change="onFolderInput" />
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

		<p v-if="uploadError" class="text-sm text-red-600">{{ uploadError }}</p>
		<p v-if="uploadInfo" class="text-sm text-green-700">{{ uploadInfo }}</p>

		<Teleport to="body">
			<div
				v-if="folderPickerOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="closeFolderPicker"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border border-[color:var(--portal-border)] bg-white shadow-2xl portal-anim-in">
					<div class="flex items-center justify-between gap-3 border-b border-[color:var(--portal-border)] px-5 py-4">
						<div class="flex items-center gap-2">
							<div
								class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
								style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
							>
								<FeatherIcon name="folder" class="h-4 w-4" />
							</div>
							<h2 class="text-base font-semibold text-[color:var(--portal-text)]">Choose folder</h2>
						</div>
						<button
							type="button"
							class="rounded-lg p-1.5 text-[color:var(--portal-muted)] transition hover:bg-gray-100 hover:text-[color:var(--portal-text)]"
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
								:class="targetFolder === node.name ? 'bg-[color:var(--portal-accent-soft)]' : 'hover:bg-white'"
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
				v-if="confirmUploadOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="cancelUploadConfirm"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-2xl rounded-2xl border border-[color:var(--portal-border)] bg-white shadow-2xl portal-anim-in" @click.stop>
					<div class="flex items-center justify-between gap-3 border-b border-[color:var(--portal-border)] px-5 py-4">
						<div class="flex items-center gap-2">
							<div class="flex h-9 w-9 items-center justify-center rounded-xl text-white" style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);">
								<FeatherIcon name="upload-cloud" class="h-4 w-4" />
							</div>
							<div>
								<h2 class="text-base font-semibold text-[color:var(--portal-text)]">{{ isFolderMode ? "Confirm folder upload" : "Confirm upload" }}</h2>
								<p v-if="isFolderMode" class="text-xs text-[color:var(--portal-muted)]">Folder structure preserved. Wrapper auto-named <strong>{{ pendingFolderWrapperName }}</strong>; same-day repeats become <strong>_v2</strong>, <strong>_v3</strong> …</p>
								<p v-else class="text-xs text-[color:var(--portal-muted)]">Files will be wrapped in a dated folder. Same-day repeats become <strong>_v2</strong>, <strong>_v3</strong> …</p>
							</div>
						</div>
						<button type="button" class="rounded-lg p-1.5 text-[color:var(--portal-muted)] transition hover:bg-gray-100 hover:text-[color:var(--portal-text)] disabled:opacity-50" :disabled="uploadBusy" @click="cancelUploadConfirm">
							<FeatherIcon name="x" class="h-4 w-4" />
						</button>
					</div>
					<div class="max-h-[60vh] space-y-3 overflow-auto px-5 py-4">
						<div class="flex flex-wrap items-center gap-2 rounded-xl border border-[color:var(--portal-accent)]/40 bg-[color:var(--portal-accent-soft)] px-3 py-2 text-xs text-[color:var(--portal-accent-strong)]">
							<FeatherIcon name="folder" class="h-3.5 w-3.5 shrink-0" />
							<span class="font-semibold">Destination:</span>
							<span class="truncate">{{ project }}</span>
							<span class="text-[color:var(--portal-subtle)]">/</span>
							<span class="truncate">{{ folderLabelByName[(isFolderMode ? pendingFolder.category : targetFolder)] || (isFolderMode ? pendingFolder.category : targetFolder) || "—" }}</span>
							<span class="text-[color:var(--portal-subtle)]">/</span>
							<span class="truncate font-semibold">{{ isFolderMode ? pendingFolderWrapperName : buildWrapperName(targetFolder, todayIso()) }}</span>
							<span class="ml-auto text-[10px] font-medium uppercase tracking-wide text-[color:var(--portal-muted)]">{{ isFolderMode ? "Folder upload" : "Editable per file below" }}</span>
						</div>
						<template v-if="isFolderMode">
							<div class="rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-3">
								<p class="mb-2 flex items-center gap-2 text-xs text-[color:var(--portal-muted)]">
									<FeatherIcon name="folder" class="h-3.5 w-3.5 shrink-0" />
									<span class="min-w-0 truncate">Source folder: {{ pendingFolder.sourceName }}</span>
									<span class="ml-auto shrink-0">{{ pendingFolder.entries.length }} file{{ pendingFolder.entries.length === 1 ? "" : "s" }}</span>
								</p>
								<div class="grid gap-2 sm:grid-cols-2">
									<label class="block">
										<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">Category (folder)</span>
										<select v-model="pendingFolder.category" class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm" :disabled="uploadBusy">
											<option v-if="projectRootPath" :value="projectRootPath">Project folder (all files)</option>
											<option v-for="f in folders" :key="`fcat-${f.name}`" :value="f.name">{{ folderOptionLabel(f.label) }}</option>
										</select>
									</label>
									<label class="block">
										<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">Date</span>
										<input v-model="pendingFolder.date" type="date" class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm" :disabled="uploadBusy" />
									</label>
								</div>
							</div>
							<div class="rounded-xl border border-[color:var(--portal-border)] bg-white">
								<p class="px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)] border-b border-[color:var(--portal-border)]">Files inside (structure preserved)</p>
								<ul class="max-h-48 overflow-auto divide-y divide-[color:var(--portal-border)] text-xs">
									<li v-for="(e, i) in pendingFolder.entries" :key="`fent-${i}`" class="flex items-center gap-2 px-3 py-1.5">
										<FeatherIcon name="file" class="h-3 w-3 shrink-0 text-[color:var(--portal-muted)]" />
										<span class="min-w-0 truncate">{{ e.relativeDir ? e.relativeDir + "/" : "" }}{{ e.file.name }}</span>
										<span class="ml-auto shrink-0 text-[color:var(--portal-muted)]">{{ fmtFileSize(e.file.size) }}</span>
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
									<input v-model="row.name" type="text" class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm" :disabled="uploadBusy" @input="onPendingNameChange(row)" />
								</label>
								<label class="block sm:col-span-2">
									<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">Category (folder)</span>
									<select v-model="row.category" class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm" :disabled="uploadBusy" @change="onPendingCategoryChange(row)">
										<option v-if="projectRootPath" :value="projectRootPath">Project folder (all files)</option>
										<option v-for="f in folders" :key="`pcat-${idx}-${f.name}`" :value="f.name">{{ folderOptionLabel(f.label) }}</option>
									</select>
								</label>
								<label class="block">
									<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">Date</span>
									<input v-model="row.date" type="date" class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm" :disabled="uploadBusy" @change="onPendingDateChange(row)" />
								</label>
								<label v-if="fileTypes.length" class="block sm:col-span-3">
									<span class="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-[color:var(--portal-subtle)]">File type</span>
									<select v-model="row.fileType" class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm" :disabled="uploadBusy">
										<option value="">— Not set —</option>
										<option v-for="t in fileTypes" :key="`ft-${idx}-${t.name}`" :value="t.name">{{ t.label }}</option>
									</select>
								</label>
							</div>
						</div>
						<p v-if="uploadError" class="text-sm text-red-600">{{ uploadError }}</p>
					</div>
					<div class="flex items-center justify-end gap-2 border-t border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-5 py-3">
						<button type="button" class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50" :disabled="uploadBusy" @click="cancelUploadConfirm">Cancel</button>
						<button type="button" class="flex items-center gap-2 rounded-lg bg-[color:var(--portal-accent)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50" :disabled="uploadBusy" @click="runConfirm">
							<FeatherIcon name="upload" class="h-4 w-4" />
							<template v-if="isFolderMode">
								{{ uploadBusy ? "Uploading…" : `Upload folder (${pendingFolder.entries.length} file${pendingFolder.entries.length === 1 ? "" : "s"})` }}
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
