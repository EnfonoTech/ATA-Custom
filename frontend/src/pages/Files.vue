<script setup>
import { ref, onMounted, watch, inject, computed, nextTick } from "vue";
import { call, uploadFile } from "@/api";
import { useRoute } from "vue-router";
import { FeatherIcon } from "frappe-ui";

const route = useRoute();
const portalCapabilities = inject("portalCapabilities", ref({}));
const refreshPortalCapabilities = inject("refreshPortalCapabilities", () => Promise.resolve());
const isCustomerPortalUser = computed(() => !!portalCapabilities.value?.is_customer_portal_user);
const projects = ref([]);
const project = ref(route.query.project || "");
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
const uploadCardRef = ref(null);
const folderPickerOpen = ref(false);
const folderPickerSearch = ref("");
const folderPickerExpanded = ref(new Set());
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
	// Expand all ancestors of current selection so user can see where they are.
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

async function handleFiles(fileList) {
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
	uploadBusy.value = true;
	uploadError.value = "";
	uploadInfo.value = "";
	let lastFolderLabel = "";
	let uploadedCount = 0;
	try {
		for (const f of fileList) {
			const res = await uploadFile("portal_app.api.files.upload_project_file", f, {
				project: project.value,
				is_private: isPrivateUpload.value ? "1" : "0",
				destination: destination.value,
				external_provider: externalProvider.value,
				target_folder: targetFolder.value,
			});
			if (res?.folder_label) lastFolderLabel = res.folder_label;
			uploadedCount += 1;
			if (res?.external_result && destination.value !== "erpnext") {
				uploadInfo.value = `External upload completed for ${f.name}.`;
			}
		}
		if (destination.value !== "external") await loadFiles();
		if (destination.value === "external") {
			uploadInfo.value = "Uploaded to external integration endpoint. ERPNext File was not created.";
		} else if (uploadedCount && lastFolderLabel) {
			uploadInfo.value = `Uploaded ${uploadedCount} file${uploadedCount === 1 ? "" : "s"} to ${lastFolderLabel}.`;
		}
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
	input.value = "";
}

function onDrop(e) {
	dragOver.value = false;
	handleFiles(e.dataTransfer?.files);
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

async function openShareModal(folderPath) {
	if (!folderPath || !canShareFolder.value) return;
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

function closeShareModal() {
	shareModalOpen.value = false;
	shareModalFolder.value = "";
	shareModalLabel.value = "";
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

watch(userSearchQ, (q) => {
	clearTimeout(userSearchTimer);
	const t = String(q || "").trim();
	if (t.length < 2) {
		userSearchHits.value = [];
		return;
	}
	userSearchTimer = setTimeout(async () => {
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
	}, 250);
});

async function shareWithUser(uid) {
	if (!project.value || !shareModalFolder.value || !uid) return;
	shareModalSaving.value = true;
	shareModalError.value = "";
	shareModalOk.value = "";
	try {
		await call({
			method: "portal_app.api.files.share_folder_with_user",
			type: "POST",
			args: {
				project: project.value,
				folder_path: shareModalFolder.value,
				user_id: uid,
				expires_days: userExpiryDays.value,
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
	if (!window.confirm(`Delete “${f.file_name}”? This removes the ERPNext File record and its attachment.`)) return;
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
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
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
							style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
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
							name="folder"
							class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
						/>
						<select v-model="project" class="portal-input pl-9">
							<option v-for="p in projects" :key="p.name" :value="p.name">
								{{ p.project_name }} ({{ p.name }})
							</option>
						</select>
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
							:style="folderView === 'grid' ? 'background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);' : ''"
							@click="folderView = 'grid'"
						>
							<FeatherIcon name="grid" class="h-3 w-3" /> Grid
						</button>
						<button
							type="button"
							class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition"
							:class="folderView === 'list' ? 'text-white' : 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'"
							:style="folderView === 'list' ? 'background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);' : ''"
							@click="folderView = 'list'"
						>
							<FeatherIcon name="list" class="h-3 w-3" /> Tree
						</button>
					</div>
				</div>
				<div v-if="folderView === 'grid'" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<div
						v-for="f in folderEntries"
						:key="`nav-grid-${f.name}`"
						class="flex flex-col overflow-hidden rounded-xl border text-sm transition"
						:class="
							folderFilter === f.name
								? 'portal-selected-ring bg-[color:var(--portal-accent-soft)]'
								: 'border-[color:var(--portal-border)] bg-white hover:border-[color:var(--portal-border-strong)] hover:shadow-md'
						"
					>
						<button
							type="button"
							class="flex-1 px-3 py-3 text-left transition"
							:style="{ paddingLeft: `${0.75 + Math.max(0, (f.depth || 0) - 1) * 0.9}rem` }"
							@click="folderFilter = f.name"
						>
							<p v-if="f.parentPath" class="mb-0.5 flex items-center gap-1 truncate text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
								<FeatherIcon v-if="(f.depth || 0) > 1" name="corner-down-right" class="h-3 w-3" />
								<span class="truncate">{{ f.parentPath }}</span>
							</p>
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
						<div
							v-if="!isCustomerPortalUser"
							class="flex flex-wrap justify-end gap-1 border-t border-gray-200/80 bg-white/60 px-2 py-1.5"
						>
							<button
								v-if="canManageProject && !f.isRoot"
								type="button"
								class="rounded-lg px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
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
								:title="'Manage who can access “' + f.label + '”'"
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
						v-for="f in folderEntries"
						:key="`nav-list-${f.name}`"
						class="flex w-full items-stretch border-b border-[color:var(--portal-border)] text-sm last:border-b-0 transition"
						:class="folderFilter === f.name ? 'bg-[color:var(--portal-accent-soft)]' : 'bg-white hover:bg-[color:var(--portal-bg)]'"
					>
						<button
							type="button"
							class="min-w-0 flex-1 px-3 py-2.5 text-left"
							:style="{ paddingLeft: `${0.75 + Math.max(0, (f.depth || 0) - 1) * 1.25}rem` }"
							@click="folderFilter = f.name"
						>
							<span v-if="f.parentPath" class="block truncate text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
								<span v-if="(f.depth || 0) > 1" class="mr-1 text-[color:var(--portal-subtle)]">↳</span>{{ f.parentPath }}
							</span>
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
							class="flex shrink-0 items-stretch divide-x divide-gray-200 border-l border-gray-200"
						>
							<button
								v-if="canManageProject && !f.isRoot"
								type="button"
								class="px-2 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
								title="Rename this subfolder (first level only)"
								:disabled="shareBusy || renameBusy"
								@click.stop="openRenameSubfolder(f.name)"
							>
								Rename
							</button>
							<button
								type="button"
								class="flex items-center gap-1 px-3 py-2 text-xs font-semibold text-[color:var(--portal-accent-strong)] transition hover:bg-[color:var(--portal-accent-soft)]"
								:title="'Manage who can access “' + f.label + '”'"
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
						class="ml-auto flex items-center gap-1 rounded-lg px-2 py-1 text-[color:var(--portal-muted)] transition hover:bg-white hover:text-[color:var(--portal-text)]"
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
					<div class="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-4 shadow-lg" @click.stop>
						<h3 class="text-lg font-semibold text-gray-900">Rename subfolder</h3>
						<p class="mt-1 text-xs text-gray-500">
							Renames only this folder segment (supports nested folders). Files already stored there keep the new path.
						</p>
						<label class="mt-3 block text-xs font-medium uppercase text-gray-500">New folder name</label>
						<input
							v-model="renameNewName"
							type="text"
							class="mt-1 w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
							autocomplete="off"
							@keyup.enter="confirmRenameSubfolder"
						/>
						<p v-if="renameError" class="mt-2 text-sm text-red-600">{{ renameError }}</p>
						<div class="mt-4 flex justify-end gap-2">
							<button
								type="button"
								class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
								:disabled="renameBusy"
								@click="closeRenameModal"
							>
								Cancel
							</button>
							<button
								type="button"
								class="rounded-lg bg-black px-3 py-2 text-sm font-medium text-white hover:bg-gray-900 disabled:opacity-50"
								:disabled="renameBusy"
								@click="confirmRenameSubfolder"
							>
								{{ renameBusy ? "Saving…" : "Rename" }}
							</button>
						</div>
					</div>
				</div>
			</div>
			<div v-if="project" class="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
				<div class="grid gap-3 sm:grid-cols-3">
					<div class="sm:col-span-2">
						<label class="mb-1 block text-xs font-medium uppercase text-gray-500">Search file</label>
						<input
							v-model="fileSearch"
							type="search"
							placeholder="Filter by file name"
							class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
						/>
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium uppercase text-gray-500">Subfolder filter</label>
						<select v-model="folderFilter" class="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm">
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
				class="rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-900"
			>
				<div class="mb-1 text-xs font-semibold uppercase tracking-wide text-indigo-700">Client portal guidance</div>
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
						class="group flex min-w-0 flex-1 items-center gap-3 rounded-2xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-4 py-3 text-left transition hover:border-[color:var(--portal-accent)] hover:bg-white"
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
							v-if="canShareFolder && targetFolder"
							class="portal-btn"
							:title="'Share “' + (folderLabelByName[targetFolder] || targetFolder) + '”'"
							@click="openShareModal(targetFolder)"
						>
							<FeatherIcon name="share-2" class="h-4 w-4" />
							Share
						</button>
						<button
							class="portal-btn portal-btn-primary"
							:disabled="!targetFolder || uploadBusy"
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
			</div>
			<p v-if="project && isCustomerPortalUser" class="rounded-xl border bg-gray-50 p-3 text-sm text-gray-600">
				Customer portal users can open files below; uploading is disabled.
			</p>

			<div class="grid gap-3 md:grid-cols-3">
				<div class="rounded-xl border border-gray-200 bg-white p-4 text-sm shadow-sm">
					<div class="mb-1 text-xs font-semibold uppercase text-gray-500">Frappe Drive</div>
					<p class="text-gray-700">
						{{ settings.use_frappe_drive ? "Enabled" : "Not enabled" }}
					</p>
					<a
						v-if="driveUrl"
						:href="driveUrl"
						target="_blank"
						rel="noopener"
						class="mt-2 inline-block text-blue-700 underline"
					>
						Open Frappe Drive
					</a>
				</div>
				<div class="rounded-xl border border-gray-200 bg-white p-4 text-sm shadow-sm">
					<div class="mb-1 text-xs font-semibold uppercase text-gray-500">Google Drive</div>
					<p class="text-gray-700">
						{{ settings.google_drive_enabled ? "Integration enabled (configured by admin)" : "Not enabled" }}
					</p>
					<a
						v-if="googleUrl"
						:href="googleUrl"
						target="_blank"
						rel="noopener"
						class="mt-2 inline-block text-blue-700 underline"
					>
						Open Google Drive
					</a>
					<p v-else-if="settings.google_drive_notes" class="mt-2 text-xs text-gray-500">
						{{ settings.google_drive_notes }}
					</p>
				</div>
				<div class="rounded-xl border border-gray-200 bg-white p-4 text-sm shadow-sm">
					<div class="mb-1 text-xs font-semibold uppercase text-gray-500">BIM 360 / ACC</div>
					<p class="text-gray-700">
						{{ settings.bim_360_enabled ? "Integration enabled (configured by admin)" : "Not enabled" }}
					</p>
					<a
						v-if="bimUrl"
						:href="bimUrl"
						target="_blank"
						rel="noopener"
						class="mt-2 inline-block text-blue-700 underline"
					>
						Open BIM 360 / ACC
					</a>
					<p v-else-if="settings.bim_360_notes" class="mt-2 text-xs text-gray-500">
						{{ settings.bim_360_notes }}
					</p>
				</div>
			</div>

			<div
				v-if="settings.file_access_note"
				class="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"
			>
				<strong>File policy:</strong> {{ settings.file_access_note }}
			</div>

			<div v-if="loading" class="text-gray-500">Loading…</div>

			<div v-else class="overflow-x-auto rounded-2xl border bg-white shadow-sm">
				<p v-if="fileListActionError" class="border-b border-red-100 bg-red-50 px-4 py-2 text-sm text-red-800">
					{{ fileListActionError }}
				</p>
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b bg-gray-50 text-gray-600">
							<th class="px-4 py-3">File</th>
							<th class="px-4 py-3">Size</th>
							<th class="px-4 py-3">Subfolder</th>
							<th class="px-4 py-3">Owner</th>
							<th class="px-4 py-3">Created</th>
							<th class="px-4 py-3">Link</th>
							<th v-if="showFileDeleteColumn" class="px-4 py-3">Delete</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="f in visibleFiles" :key="f.name" class="border-b border-gray-100">
							<td class="px-4 py-3">
								{{ f.file_name }}
								<span v-if="f.is_private" class="ml-1 text-xs text-gray-400">(private)</span>
							</td>
							<td class="px-4 py-3">{{ f.file_size ?? "—" }}</td>
							<td class="px-4 py-3">{{ subfolderLabel(f.folder) }}</td>
							<td class="px-4 py-3">{{ f.owner }}</td>
							<td class="px-4 py-3">{{ f.creation }}</td>
							<td class="px-4 py-3">
								<a
									v-if="f.file_url"
									:href="f.file_url"
									target="_blank"
									rel="noopener"
									class="text-blue-600 underline"
								>
									Open
								</a>
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
									class="text-xs text-gray-400"
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
				<p v-if="!visibleFiles.length && project" class="p-4 text-center text-gray-500">
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
				v-if="shareModalOpen"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
				@click.self="closeShareModal"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"></div>
				<div class="relative z-10 w-full max-w-lg rounded-2xl border border-[color:var(--portal-border)] bg-white shadow-2xl portal-anim-in">
					<div class="flex items-start justify-between gap-3 border-b border-[color:var(--portal-border)] px-5 py-4">
						<div class="min-w-0">
							<div class="flex items-center gap-2">
								<div
									class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
									style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
								>
									<FeatherIcon name="share-2" class="h-4 w-4" />
								</div>
								<h2 class="text-base font-semibold text-[color:var(--portal-text)]">Share folder</h2>
							</div>
							<p class="mt-1 truncate text-xs text-[color:var(--portal-muted)]">
								{{ shareModalLabel }}
							</p>
						</div>
						<button
							type="button"
							class="rounded-lg p-1.5 text-[color:var(--portal-muted)] transition hover:bg-gray-100 hover:text-[color:var(--portal-text)]"
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
										placeholder="Search by email or username"
										:disabled="shareModalSaving"
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

							<div
								v-if="userSearchHits.length"
								class="mt-2 max-h-48 overflow-auto rounded-xl border border-[color:var(--portal-border)] bg-white"
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
								v-else-if="userSearchQ.trim().length >= 2 && !userSearchBusy"
								class="mt-2 text-xs text-[color:var(--portal-muted)]"
							>
								No matching users.
							</p>
						</section>

						<!-- People with access -->
						<section>
							<p class="portal-section-title mb-2">People with access</p>
							<div v-if="shareModalLoading" class="text-sm text-[color:var(--portal-muted)]">Loading…</div>
							<div v-else-if="!userSharesForFolder.length" class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] p-4 text-center text-xs text-[color:var(--portal-muted)]">
								No people have direct access yet. Add someone above.
							</div>
							<ul v-else class="divide-y divide-[color:var(--portal-border)] rounded-xl border border-[color:var(--portal-border)] bg-white">
								<li
									v-for="s in userSharesForFolder"
									:key="s.name"
									class="flex items-center gap-3 px-3 py-2.5 text-sm"
								>
									<div
										class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
										style="background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%);"
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

						<!-- Public link -->
						<section v-if="shareTrackingAvailable">
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
	</div>
</template>
