<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { call } from "@/api";
import { FeatherIcon } from "frappe-ui";

const router = useRouter();
const loading = ref(false);
const projects = ref([]);
const notAdmin = ref(false);
const error = ref("");
const okMsg = ref("");
const search = ref("");
const expandedProjects = ref(new Set());
const expandedFolders = ref(new Set());
const expandedUsers = ref(new Set());
const busyShare = ref("");
const filterMode = ref("all"); // all | mine
const viewMode = ref("project"); // project | user

async function loadShares() {
	loading.value = true;
	error.value = "";
	try {
		const res = await call({ method: "portal_app.api.files.list_managed_shares" });
		projects.value = res?.projects || [];
		notAdmin.value = !!res?.not_admin;
		if (projects.value.length === 1) {
			expandedProjects.value = new Set([projects.value[0].project]);
		}
	} catch (e) {
		console.error(e);
		error.value = e?.responseBody?.message || "Could not load shares.";
	} finally {
		loading.value = false;
	}
}

function onVisible() {
	if (document.visibilityState === "visible") loadShares();
}
function onFocus() {
	loadShares();
}

onMounted(() => {
	loadShares();
	document.addEventListener("visibilitychange", onVisible);
	window.addEventListener("focus", onFocus);
});
onBeforeUnmount(() => {
	document.removeEventListener("visibilitychange", onVisible);
	window.removeEventListener("focus", onFocus);
});

function toggleProject(name) {
	const next = new Set(expandedProjects.value);
	next.has(name) ? next.delete(name) : next.add(name);
	expandedProjects.value = next;
}
function toggleFolder(key) {
	const next = new Set(expandedFolders.value);
	next.has(key) ? next.delete(key) : next.add(key);
	expandedFolders.value = next;
}
function toggleUser(key) {
	const next = new Set(expandedUsers.value);
	next.has(key) ? next.delete(key) : next.add(key);
	expandedUsers.value = next;
}

function expandAll() {
	expandedProjects.value = new Set(projects.value.map((p) => p.project));
	const allFolders = new Set();
	const allUsers = new Set();
	for (const p of projects.value) {
		for (const f of p.folders) allFolders.add(`${p.project}::${f.folder_path}`);
	}
	for (const u of byUser.value) allUsers.add(u.key);
	expandedFolders.value = allFolders;
	expandedUsers.value = allUsers;
}
function collapseAll() {
	expandedProjects.value = new Set();
	expandedFolders.value = new Set();
	expandedUsers.value = new Set();
}

const filteredProjects = computed(() => {
	const q = search.value.trim().toLowerCase();
	const onlyMine = filterMode.value === "mine";
	// Default ("All shares" + no query): show every manageable project, every folder,
	// every file. The admin gets a complete browser with shares overlaid.
	if (!q && !onlyMine) return projects.value;
	return projects.value
		.map((p) => {
			const folders = p.folders
				.map((f) => {
					const userMatches = f.user_shares.filter((s) => {
						if (onlyMine && !s.created_by_user) return false;
						if (!q) return true;
						return [s.user, s.user_email, s.user_full_name]
							.filter(Boolean)
							.some((v) => String(v).toLowerCase().includes(q));
					});
					const linkMatches = f.link_shares.filter((s) => {
						if (onlyMine && !s.created_by_user) return false;
						if (!q) return true;
						return String(s.share_url || "").toLowerCase().includes(q);
					});
					const fileMatches = (f.files || []).filter((file) => {
						const fileShares = (file.shares || []).filter((s) => {
							if (onlyMine && !s.created_by_user) return false;
							if (!q) return true;
							return [s.user, s.user_email, s.user_full_name]
								.filter(Boolean)
								.some((v) => String(v).toLowerCase().includes(q));
						});
						const nameHit = !q || String(file.file_name || "").toLowerCase().includes(q);
						return nameHit || fileShares.length > 0;
					});
					const folderHit = String(f.folder_label || "").toLowerCase().includes(q);
					return {
						...f,
						user_shares: folderHit ? f.user_shares : userMatches,
						link_shares: folderHit ? f.link_shares : linkMatches,
						files: folderHit ? f.files || [] : fileMatches,
					};
				})
				.filter(
					(f) =>
						f.user_shares.length ||
						f.link_shares.length ||
						(f.files || []).length,
				);
			const projectHit =
				String(p.project_name || "").toLowerCase().includes(q) ||
				String(p.customer || "").toLowerCase().includes(q) ||
				String(p.project || "").toLowerCase().includes(q);
			return projectHit ? { ...p, folders: p.folders } : { ...p, folders };
		})
		.filter((p) => p.folders.length > 0);
});

const totals = computed(() => {
	let users = 0,
		links = 0,
		folders = 0,
		files = 0;
	for (const p of projects.value) {
		folders += p.folders.length;
		for (const f of p.folders) {
			users += f.user_shares.length;
			links += f.link_shares.length;
			const fs = f.files || [];
			files += fs.length;
			for (const file of fs) users += (file.shares || []).length;
		}
	}
	return { users, links, folders, files, projects: projects.value.length };
});

/** Pivot the same data into a "By user" view: one card per user with all the
 *  (project, folder, share) rows they have access to. Public links are listed
 *  under a synthetic "Public link" group at the end. */
const byUser = computed(() => {
	const userMap = new Map();
	const linkRows = [];
	const addUserShare = (s, ctx) => {
		const key = s.user || s.user_email || s.share_name;
		if (!userMap.has(key)) {
			userMap.set(key, {
				key,
				user: s.user,
				user_email: s.user_email,
				user_full_name: s.user_full_name,
				avatar_letter: (s.user_full_name || s.user_email || s.user || "?").charAt(0).toUpperCase(),
				rows: [],
			});
		}
		userMap.get(key).rows.push({ ...s, ...ctx });
	};
	for (const p of projects.value) {
		for (const f of p.folders) {
			for (const s of f.user_shares) {
				addUserShare(s, {
					project: p.project,
					project_name: p.project_name,
					project_status: p.status,
					customer: p.customer,
					folder_path: f.folder_path,
					folder_label: f.folder_label,
				});
			}
			for (const s of f.link_shares) {
				linkRows.push({
					...s,
					project: p.project,
					project_name: p.project_name,
					folder_path: f.folder_path,
					folder_label: f.folder_label,
				});
			}
			for (const file of f.files || []) {
				for (const s of file.shares || []) {
					addUserShare(s, {
						project: p.project,
						project_name: p.project_name,
						project_status: p.status,
						customer: p.customer,
						folder_path: f.folder_path,
						folder_label: `${f.folder_label} / ${file.file_name}`,
						is_file_share: true,
					});
				}
			}
		}
	}
	const users = [...userMap.values()].sort((a, b) =>
		String(a.user_full_name || a.user || "").localeCompare(
			String(b.user_full_name || b.user || ""),
			undefined,
			{ sensitivity: "base" },
		),
	);
	if (linkRows.length) {
		users.push({
			key: "__public_links__",
			isLinks: true,
			user_full_name: "Public links",
			user_email: `${linkRows.length} active link${linkRows.length === 1 ? "" : "s"}`,
			avatar_letter: "🔗",
			rows: linkRows,
		});
	}
	return users;
});

const filteredByUser = computed(() => {
	const q = search.value.trim().toLowerCase();
	const onlyMine = filterMode.value === "mine";
	if (!q && !onlyMine) return byUser.value;
	return byUser.value
		.map((u) => {
			const rows = u.rows.filter((r) => {
				if (onlyMine && !r.created_by_user) return false;
				if (!q) return true;
				return [
					u.user_full_name,
					u.user_email,
					u.user,
					r.project_name,
					r.project,
					r.folder_label,
					r.share_url,
				]
					.filter(Boolean)
					.some((v) => String(v).toLowerCase().includes(q));
			});
			return { ...u, rows };
		})
		.filter((u) => u.rows.length);
});

async function revokeShare(s) {
	if (!s?.share_name || !s.can_revoke) return;
	const who = s.share_kind === "Link" ? "this public link" : `${s.user_full_name || s.user || "this user"}'s access`;
	if (!window.confirm(`Revoke ${who}?`)) return;
	busyShare.value = s.share_name;
	error.value = "";
	okMsg.value = "";
	try {
		await call({
			method: "portal_app.api.files.revoke_folder_share",
			type: "POST",
			args: { share_name: s.share_name },
		});
		okMsg.value = "Revoked.";
		await loadShares();
		setTimeout(() => (okMsg.value = ""), 2500);
	} catch (e) {
		error.value = e?.responseBody?.message || "Could not revoke share.";
	} finally {
		busyShare.value = "";
	}
}

async function copyLink(url) {
	if (!url) return;
	try {
		await navigator.clipboard.writeText(url);
		okMsg.value = "Link copied.";
		setTimeout(() => (okMsg.value = ""), 2000);
	} catch {
		/* ignore */
	}
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
	const d = new Date(String(s).replace(" ", "T"));
	if (Number.isNaN(d.getTime())) return s;
	return d.toLocaleDateString();
}
function fmtDateTime(s) {
	if (!s) return "";
	const d = new Date(String(s).replace(" ", "T"));
	if (Number.isNaN(d.getTime())) return s;
	return d.toLocaleString();
}
function statusPillClass(status) {
	const t = String(status || "").toLowerCase();
	if (t === "completed") return "portal-pill-success";
	if (t === "cancelled") return "portal-pill-danger";
	if (t === "open") return "portal-pill-accent";
	return "portal-pill-muted";
}
function openProject(name) {
	router.push("/projects/" + encodeURIComponent(name));
}
function openFolderInFiles(project, folderPath) {
	router.push({
		path: "/files",
		query: { project, folder: folderPath, share: "1" },
	});
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-6xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="shield" class="h-3 w-3" />
							Manage shares
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							Active shares across your projects
						</h1>
						<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Audit who has access to what — and revoke quickly. You can revoke any share on projects you manage, plus any share you created yourself on shared projects.
						</p>
					</div>
					<button class="portal-btn" @click="loadShares" :disabled="loading">
						<FeatherIcon name="refresh-cw" class="h-4 w-4" :class="loading ? 'animate-spin' : ''" />
						Refresh
					</button>
				</div>
			</div>

			<!-- KPIs -->
			<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #4f46e5, #6366f1); color: #fff;">
						<FeatherIcon name="briefcase" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Projects</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ totals.projects }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #06b6d4, #22d3ee); color: #fff;">
						<FeatherIcon name="folder" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Folders</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ totals.folders }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: #fff;">
						<FeatherIcon name="file" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Files</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ totals.files }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #fff;">
						<FeatherIcon name="users" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">User grants</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ totals.users }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #db2777, #f472b6); color: #fff;">
						<FeatherIcon name="link" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Public links</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ totals.links }}</p>
					</div>
				</div>
			</div>

			<!-- View mode + filters -->
			<div class="portal-card-strong p-3 space-y-3">
				<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-0.5 text-xs">
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium"
						:class="viewMode === 'project' ? 'bg-white text-[color:var(--portal-text)] shadow-sm' : 'text-[color:var(--portal-muted)]'"
						@click="viewMode = 'project'"
					>
						<FeatherIcon name="folder" class="h-3.5 w-3.5" />
						By project
					</button>
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium"
						:class="viewMode === 'user' ? 'bg-white text-[color:var(--portal-text)] shadow-sm' : 'text-[color:var(--portal-muted)]'"
						@click="viewMode = 'user'"
					>
						<FeatherIcon name="users" class="h-3.5 w-3.5" />
						By user
					</button>
				</div>
				<div class="grid gap-3 md:grid-cols-[1fr_auto_auto]">
					<div class="relative">
						<FeatherIcon
							name="search"
							class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
						/>
						<input
							v-model="search"
							type="search"
							class="portal-input pl-9"
							placeholder="Search by project, folder, user, email, or link…"
						/>
					</div>
					<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-0.5 text-xs">
						<button
							class="rounded-lg px-3 py-1.5 font-medium"
							:class="filterMode === 'all' ? 'bg-white text-[color:var(--portal-text)] shadow-sm' : 'text-[color:var(--portal-muted)]'"
							@click="filterMode = 'all'"
						>
							All shares
						</button>
						<button
							class="rounded-lg px-3 py-1.5 font-medium"
							:class="filterMode === 'mine' ? 'bg-white text-[color:var(--portal-text)] shadow-sm' : 'text-[color:var(--portal-muted)]'"
							@click="filterMode = 'mine'"
						>
							Created by me
						</button>
					</div>
					<div class="flex items-center gap-2">
						<button class="portal-btn portal-btn-ghost text-xs" @click="expandAll">Expand all</button>
						<button class="portal-btn portal-btn-ghost text-xs" @click="collapseAll">Collapse</button>
					</div>
				</div>
			</div>

			<p v-if="okMsg" class="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{{ okMsg }}</p>
			<p v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

			<div v-if="loading" class="portal-card-strong flex items-center justify-center gap-2 p-10 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading shares…
			</div>

			<div
				v-else-if="notAdmin"
				class="portal-card-strong flex flex-col items-center justify-center gap-3 p-10 text-center"
			>
				<div
					class="flex h-12 w-12 items-center justify-center rounded-2xl text-white"
					style="background: linear-gradient(135deg, #f87171 0%, #fb923c 100%);"
				>
					<FeatherIcon name="lock" class="h-5 w-5" />
				</div>
				<p class="text-base font-semibold text-[color:var(--portal-text)]">Project admin only</p>
				<p class="max-w-md text-sm text-[color:var(--portal-muted)]">
					This page is for portal project managers. Project members can still share folders from
					<router-link to="/files" class="font-medium underline">Files</router-link> and revoke their own grants from each folder's Share modal.
				</p>
			</div>

			<div
				v-else-if="!projects.length"
				class="portal-card-strong flex flex-col items-center justify-center gap-3 p-10 text-center"
			>
				<div
					class="flex h-12 w-12 items-center justify-center rounded-2xl text-white"
					style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
				>
					<FeatherIcon name="inbox" class="h-5 w-5" />
				</div>
				<p class="text-base font-semibold text-[color:var(--portal-text)]">No active shares</p>
				<p class="max-w-md text-sm text-[color:var(--portal-muted)]">
					When you or a teammate shares a folder from <router-link to="/files" class="font-medium underline">Files</router-link> on one of your projects, the grants appear here.
				</p>
			</div>

			<div
				v-else-if="viewMode === 'project' && !filteredProjects.length"
				class="portal-card-strong p-10 text-center text-sm text-[color:var(--portal-muted)]"
			>
				Nothing matches your filter.
			</div>
			<div
				v-else-if="viewMode === 'user' && !filteredByUser.length"
				class="portal-card-strong p-10 text-center text-sm text-[color:var(--portal-muted)]"
			>
				Nothing matches your filter.
			</div>

			<div v-else-if="viewMode === 'project'" class="space-y-3">
				<div
					v-for="p in filteredProjects"
					:key="p.project"
					class="portal-card-strong overflow-hidden p-0"
				>
					<button
						type="button"
						class="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-[color:var(--portal-bg)]"
						@click="toggleProject(p.project)"
					>
						<FeatherIcon
							:name="expandedProjects.has(p.project) ? 'chevron-down' : 'chevron-right'"
							class="h-4 w-4 shrink-0 text-[color:var(--portal-muted)]"
						/>
						<div
							class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white"
							style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
						>
							<FeatherIcon name="folder" class="h-4 w-4" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="truncate text-sm font-semibold text-[color:var(--portal-text)]">
								{{ p.project_name }}
							</p>
							<p class="truncate text-xs text-[color:var(--portal-muted)]">
								<span v-if="p.customer">{{ p.customer }} · </span>
								<span class="font-mono">{{ p.project }}</span>
							</p>
						</div>
						<span v-if="p.status" class="portal-pill" :class="statusPillClass(p.status)">{{ p.status }}</span>
						<span v-if="!p.is_manageable" class="portal-pill portal-pill-muted">read-only</span>
						<span class="portal-pill portal-pill-muted">{{ p.counts?.folders || 0 }} folder{{ (p.counts?.folders || 0) === 1 ? "" : "s" }}</span>
						<span class="portal-pill portal-pill-muted">{{ p.counts?.files || 0 }} file{{ (p.counts?.files || 0) === 1 ? "" : "s" }}</span>
						<span class="portal-pill portal-pill-accent">{{ (p.counts?.user_shares || 0) + (p.counts?.file_shares || 0) }} share{{ ((p.counts?.user_shares || 0) + (p.counts?.file_shares || 0)) === 1 ? "" : "s" }}</span>
						<span v-if="p.counts?.link_shares" class="portal-pill portal-pill-muted">{{ p.counts.link_shares }} link{{ p.counts.link_shares === 1 ? "" : "s" }}</span>
						<button
							class="portal-btn portal-btn-ghost text-xs"
							@click.stop="openProject(p.project)"
						>
							<FeatherIcon name="external-link" class="h-3.5 w-3.5" />
							Open
						</button>
					</button>

					<div v-if="expandedProjects.has(p.project)" class="border-t border-[color:var(--portal-border)] bg-[color:var(--portal-bg)]">
						<div
							v-for="f in p.folders"
							:key="`${p.project}::${f.folder_path}`"
							class="border-b border-[color:var(--portal-border)] last:border-b-0"
						>
							<button
								type="button"
								class="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm transition hover:bg-white"
								@click="toggleFolder(`${p.project}::${f.folder_path}`)"
							>
								<FeatherIcon
									:name="expandedFolders.has(`${p.project}::${f.folder_path}`) ? 'chevron-down' : 'chevron-right'"
									class="h-3.5 w-3.5 shrink-0 text-[color:var(--portal-muted)]"
								/>
								<FeatherIcon
									:name="f.is_file_share ? 'file' : 'folder'"
									class="h-3.5 w-3.5 shrink-0"
									:class="f.is_file_share ? 'text-[color:var(--portal-warning)]' : 'text-[color:var(--portal-accent)]'"
								/>
								<span class="min-w-0 flex-1 truncate font-medium text-[color:var(--portal-text)]">
									{{ f.folder_label }}
								</span>
								<span v-if="(f.files || []).length" class="portal-pill portal-pill-muted">
									{{ (f.files || []).length }} file{{ (f.files || []).length === 1 ? "" : "s" }}
								</span>
								<span v-if="f.user_shares.length" class="portal-pill portal-pill-accent">
									{{ f.user_shares.length }} user{{ f.user_shares.length === 1 ? "" : "s" }}
								</span>
								<span v-if="f.link_shares.length" class="portal-pill portal-pill-muted">
									{{ f.link_shares.length }} link{{ f.link_shares.length === 1 ? "" : "s" }}
								</span>
								<span
									v-if="!f.user_shares.length && !f.link_shares.length"
									class="portal-pill"
									style="background: rgba(148, 163, 184, 0.12); color: rgb(100, 116, 139); border-color: rgba(148, 163, 184, 0.25);"
								>
									no shares
								</span>
								<button
									class="portal-btn portal-btn-ghost text-xs"
									@click.stop="openFolderInFiles(p.project, f.folder_path)"
								>
									<FeatherIcon name="settings" class="h-3.5 w-3.5" />
									Manage
								</button>
							</button>

							<div
								v-if="expandedFolders.has(`${p.project}::${f.folder_path}`)"
								class="bg-white"
							>
								<!-- User shares -->
								<div
									v-for="s in f.user_shares"
									:key="s.share_name"
									class="flex flex-wrap items-center gap-3 border-t border-[color:var(--portal-border)] px-12 py-2.5"
								>
									<div
										class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
										style="background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%);"
									>
										{{ (s.user_full_name || s.user_email || s.user || '?').charAt(0).toUpperCase() }}
									</div>
									<div class="min-w-0 flex-1">
										<p class="truncate text-sm font-medium text-[color:var(--portal-text)]">
											{{ s.user_full_name || s.user || s.user_email }}
										</p>
										<p class="truncate text-xs text-[color:var(--portal-muted)]">
											{{ s.user_email || s.user }}
											<span v-if="s.expires_at"> · expires {{ fmtDate(s.expires_at) }}</span>
											<span v-else-if="s.native"> · ERPNext share</span>
											<span v-if="s.created_by_user"> · shared by {{ s.created_by_user }}</span>
										</p>
									</div>
									<button
										class="portal-btn portal-btn-danger text-xs"
										:disabled="!s.can_revoke || busyShare === s.share_name"
										:title="s.can_revoke ? 'Revoke this user\'s access' : 'Only a project manager (or the user who created the share) can revoke this'"
										@click="revokeShare(s)"
									>
										<FeatherIcon name="x" class="h-3.5 w-3.5" />
										{{ busyShare === s.share_name ? "Revoking…" : "Revoke" }}
									</button>
								</div>

								<!-- Link shares -->
								<div
									v-for="s in f.link_shares"
									:key="s.share_name"
									class="flex flex-wrap items-center gap-3 border-t border-[color:var(--portal-border)] px-12 py-2.5"
								>
									<div
										class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white"
										style="background: linear-gradient(135deg, #db2777, #f472b6);"
									>
										<FeatherIcon name="link" class="h-3.5 w-3.5" />
									</div>
									<div class="min-w-0 flex-1">
										<p class="truncate text-sm font-medium text-[color:var(--portal-text)]">
											Public link · {{ s.access_count || 0 }} opens
										</p>
										<p class="truncate text-xs text-[color:var(--portal-muted)]">
											<a :href="s.share_url" target="_blank" rel="noopener" class="text-[color:var(--portal-accent-strong)] hover:underline">{{ s.share_url }}</a>
											<span v-if="s.expires_at"> · expires {{ fmtDate(s.expires_at) }}</span>
											<span v-if="s.last_accessed_at"> · last open {{ fmtDateTime(s.last_accessed_at) }}</span>
										</p>
									</div>
									<button
										class="portal-btn text-xs"
										@click="copyLink(s.share_url)"
									>
										<FeatherIcon name="copy" class="h-3.5 w-3.5" />
										Copy
									</button>
									<button
										class="portal-btn portal-btn-danger text-xs"
										:disabled="!s.can_revoke || busyShare === s.share_name"
										@click="revokeShare(s)"
									>
										<FeatherIcon name="x" class="h-3.5 w-3.5" />
										{{ busyShare === s.share_name ? "Revoking…" : "Revoke" }}
									</button>
								</div>

								<!-- Files inside this folder -->
								<div v-if="(f.files || []).length" class="border-t border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-12 py-2">
									<p class="portal-section-title mb-1.5">Files in this folder ({{ (f.files || []).length }})</p>
									<div
										v-for="file in f.files"
										:key="file.name"
										class="flex flex-wrap items-center gap-3 rounded-lg border border-[color:var(--portal-border)] bg-white px-3 py-2 text-sm transition hover:border-[color:var(--portal-accent)] mb-1.5 last:mb-0"
									>
										<FeatherIcon name="file" class="h-3.5 w-3.5 shrink-0 text-[color:var(--portal-muted)]" />
										<div class="min-w-0 flex-1">
											<p class="flex items-center gap-2 truncate font-medium text-[color:var(--portal-text)]">
												<a v-if="file.file_url" :href="file.file_url" target="_blank" rel="noopener" class="truncate hover:underline">
													{{ file.file_name }}
												</a>
												<span v-else class="truncate">{{ file.file_name }}</span>
												<span v-if="file.is_private" class="text-[10px] text-[color:var(--portal-subtle)]">(private)</span>
											</p>
											<p class="truncate text-[11px] text-[color:var(--portal-muted)]">
												{{ fmtFileSize(file.file_size) }} · uploaded by {{ file.owner }} · {{ fmtDate(file.creation) }}
											</p>
										</div>
										<!-- Per-file shares -->
										<div v-if="(file.shares || []).length" class="flex flex-wrap items-center gap-1.5">
											<span
												v-for="s in file.shares"
												:key="s.share_name"
												class="inline-flex items-center gap-1 rounded-full border border-[color:var(--portal-border)] bg-[color:var(--portal-accent-soft)] px-2 py-0.5 text-[11px] text-[color:var(--portal-accent-strong)]"
												:title="(s.user_full_name || s.user) + (s.expires_at ? ' · expires ' + fmtDate(s.expires_at) : '')"
											>
												<span class="flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-semibold text-white" style="background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%);">
													{{ (s.user_full_name || s.user_email || s.user || '?').charAt(0).toUpperCase() }}
												</span>
												<span class="truncate max-w-[120px]">{{ s.user_full_name || s.user || s.user_email }}</span>
												<button
													class="rounded p-0.5 text-red-700 transition hover:bg-red-50 disabled:opacity-50"
													:disabled="!s.can_revoke || busyShare === s.share_name"
													:title="'Revoke this user\'s access to ' + file.file_name"
													@click="revokeShare(s)"
												>
													<FeatherIcon name="x" class="h-3 w-3" />
												</button>
											</span>
										</div>
										<span v-else class="text-[11px] text-[color:var(--portal-muted)]">no file-level shares</span>
									</div>
								</div>

								<div
									v-if="!f.user_shares.length && !f.link_shares.length && !(f.files || []).length"
									class="px-12 py-3 text-xs text-[color:var(--portal-muted)]"
								>
									This folder is empty and has no shares.
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- By User view -->
			<div v-else-if="viewMode === 'user'" class="space-y-3">
				<div
					v-for="u in filteredByUser"
					:key="u.key"
					class="portal-card-strong overflow-hidden p-0"
				>
					<button
						type="button"
						class="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-[color:var(--portal-bg)]"
						@click="toggleUser(u.key)"
					>
						<FeatherIcon
							:name="expandedUsers.has(u.key) ? 'chevron-down' : 'chevron-right'"
							class="h-4 w-4 shrink-0 text-[color:var(--portal-muted)]"
						/>
						<div
							class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white"
							:style="
								u.isLinks
									? 'background: linear-gradient(135deg, #db2777, #f472b6);'
									: 'background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%);'
							"
						>
							{{ u.avatar_letter }}
						</div>
						<div class="min-w-0 flex-1">
							<p class="truncate text-sm font-semibold text-[color:var(--portal-text)]">
								{{ u.user_full_name || u.user || u.user_email }}
							</p>
							<p class="truncate text-xs text-[color:var(--portal-muted)]">
								{{ u.user_email || u.user }}
							</p>
						</div>
						<span class="portal-pill portal-pill-muted">
							{{ u.rows.length }} grant{{ u.rows.length === 1 ? "" : "s" }}
						</span>
					</button>

					<div v-if="expandedUsers.has(u.key)" class="border-t border-[color:var(--portal-border)] bg-[color:var(--portal-bg)]">
						<div
							v-for="r in u.rows"
							:key="`${r.share_name}::${r.project}::${r.folder_path}`"
							class="flex flex-wrap items-center gap-3 border-b border-[color:var(--portal-border)] bg-white px-5 py-2.5 last:border-b-0"
						>
							<div
								class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-white"
								:style="
									u.isLinks
										? 'background: linear-gradient(135deg, #db2777, #f472b6);'
										: 'background: linear-gradient(135deg, #4f46e5, #6366f1);'
								"
							>
								<FeatherIcon :name="u.isLinks ? 'link' : 'folder'" class="h-3.5 w-3.5" />
							</div>
							<div class="min-w-0 flex-1">
								<p class="truncate text-sm font-medium text-[color:var(--portal-text)]">
									{{ r.project_name }}
									<span class="text-[color:var(--portal-muted)]"> · </span>
									<span class="text-[color:var(--portal-muted)]">{{ r.folder_label }}</span>
								</p>
								<p class="truncate text-xs text-[color:var(--portal-muted)]">
									<a
										v-if="u.isLinks && r.share_url"
										:href="r.share_url"
										target="_blank"
										rel="noopener"
										class="text-[color:var(--portal-accent-strong)] hover:underline"
									>
										{{ r.share_url }}
									</a>
									<span v-else class="font-mono">{{ r.project }}</span>
									<span v-if="r.expires_at"> · expires {{ fmtDate(r.expires_at) }}</span>
									<span v-else-if="r.native"> · ERPNext share</span>
									<span v-if="r.created_by_user"> · shared by {{ r.created_by_user }}</span>
									<span v-if="u.isLinks"> · {{ r.access_count || 0 }} opens</span>
								</p>
							</div>
							<button
								class="portal-btn portal-btn-ghost text-xs"
								@click="openFolderInFiles(r.project, r.folder_path)"
							>
								<FeatherIcon name="settings" class="h-3.5 w-3.5" />
								Manage
							</button>
							<button
								v-if="u.isLinks && r.share_url"
								class="portal-btn text-xs"
								@click="copyLink(r.share_url)"
							>
								<FeatherIcon name="copy" class="h-3.5 w-3.5" />
								Copy
							</button>
							<button
								class="portal-btn portal-btn-danger text-xs"
								:disabled="!r.can_revoke || busyShare === r.share_name"
								@click="revokeShare(r)"
							>
								<FeatherIcon name="x" class="h-3.5 w-3.5" />
								{{ busyShare === r.share_name ? "Revoking…" : "Revoke" }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
