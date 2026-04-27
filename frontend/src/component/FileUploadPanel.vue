<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { uploadFile } from "@/api";
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
const uploadCardRef = ref(null);
const dragOver = ref(false);
const uploadBusy = ref(false);
const uploadError = ref("");
const uploadInfo = ref("");

const folderPickerOpen = ref(false);
const folderPickerSearch = ref("");
const folderPickerExpanded = ref(new Set());

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

async function handleFiles(fileList) {
	if (!props.project || !fileList?.length || !targetFolder.value) return;
	uploadBusy.value = true;
	uploadError.value = "";
	uploadInfo.value = "";
	let lastFolderLabel = "";
	let count = 0;
	try {
		for (const f of fileList) {
			const res = await uploadFile("portal_app.api.files.upload_project_file", f, {
				project: props.project,
				is_private: isPrivateUpload.value ? "1" : "0",
				destination: destination.value,
				external_provider: externalProvider.value,
				target_folder: targetFolder.value,
			});
			if (res?.folder_label) lastFolderLabel = res.folder_label;
			count += 1;
		}
		if (count) {
			uploadInfo.value = lastFolderLabel
				? `Uploaded ${count} file${count === 1 ? "" : "s"} to ${lastFolderLabel}.`
				: `Uploaded ${count} file${count === 1 ? "" : "s"}.`;
		}
		emit("uploaded", { count, folderLabel: lastFolderLabel });
		setTimeout(() => (uploadInfo.value = ""), 4000);
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
function onDrop(e) {
	dragOver.value = false;
	handleFiles(e.dataTransfer?.files);
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
			<p class="font-medium text-[color:var(--portal-text)]">Drop files here or click to upload</p>
			<p class="text-xs text-[color:var(--portal-muted)]">
				Goes into <strong class="text-[color:var(--portal-text)]">{{ folderLabelByName[targetFolder] || targetFolder || "—" }}</strong>
			</p>
			<input ref="fileInput" type="file" class="hidden" multiple @change="onFileInput" />
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
	</div>
</template>
