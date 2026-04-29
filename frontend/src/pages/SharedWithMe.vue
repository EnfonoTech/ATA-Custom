<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from "vue";
import { useRouter } from "vue-router";
import { call } from "@/api";
import { FeatherIcon } from "frappe-ui";

const router = useRouter();
const loading = ref(true);
const projects = ref([]);
const error = ref("");
const expandedProjects = ref(new Set());
const expandedFolders = ref(new Set());
const search = ref("");

async function loadShared() {
	loading.value = true;
	error.value = "";
	try {
		const res = await call({ method: "portal_app.api.files.list_shared_with_me" });
		projects.value = res?.projects || [];
		// Auto-expand the first project for quick access.
		if (projects.value.length === 1) {
			expandedProjects.value = new Set([projects.value[0].project]);
		}
	} catch (e) {
		console.error(e);
		error.value = e?.responseBody?.message || "Could not load shared files.";
	} finally {
		loading.value = false;
	}
}

function onVisible() {
	if (document.visibilityState === "visible") loadShared();
}
function onFocus() {
	loadShared();
}

onMounted(() => {
	loadShared();
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

const filteredProjects = computed(() => {
	const q = search.value.trim().toLowerCase();
	if (!q) return projects.value;
	return projects.value
		.map((p) => {
			const folders = p.folders.map((f) => {
				const filteredFiles = f.files.filter((file) =>
					String(file.file_name || "").toLowerCase().includes(q),
				);
				const folderHit = String(f.folder_label || "").toLowerCase().includes(q);
				return folderHit ? { ...f } : { ...f, files: filteredFiles };
			});
			const projectHit =
				String(p.project_name || "").toLowerCase().includes(q) ||
				String(p.customer || "").toLowerCase().includes(q);
			const filteredFolders = projectHit
				? folders
				: folders.filter(
					(f) => f.files.length > 0 || String(f.folder_label || "").toLowerCase().includes(q),
				);
			return { ...p, folders: filteredFolders };
		})
		.filter((p) => p.folders.length > 0);
});

const totalFolders = computed(() => projects.value.reduce((n, p) => n + p.folders.length, 0));
const totalFiles = computed(() =>
	projects.value.reduce((n, p) => n + p.folders.reduce((m, f) => m + (f.file_count || 0), 0), 0),
);

function fileSize(bytes) {
	if (bytes == null) return "—";
	const n = Number(bytes);
	if (Number.isNaN(n) || !n) return "—";
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
	if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
	return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function fmtDate(s) {
	if (!s) return "";
	const d = new Date(String(s).replace(" ", "T"));
	if (Number.isNaN(d.getTime())) return s;
	return d.toLocaleDateString();
}

function statusPillClass(s) {
	const t = String(s || "").toLowerCase();
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
		query: { project, folder: folderPath },
	});
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-5xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="share-2" class="h-3 w-3" />
							Shared with me
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							Files shared with you
						</h1>
						<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Folders and individual files other people have shared with you, grouped by project. Sources include portal share grants and ERPNext native shares.
						</p>
					</div>
					<button class="portal-btn" @click="loadShared" :disabled="loading">
						<FeatherIcon name="refresh-cw" class="h-4 w-4" :class="loading ? 'animate-spin' : ''" />
						Refresh
					</button>
				</div>
			</div>

			<!-- KPIs -->
			<div class="grid gap-3 sm:grid-cols-3">
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #4f46e5, #6366f1); color: #fff;">
						<FeatherIcon name="folder" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Projects</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ projects.length }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: #fff;">
						<FeatherIcon name="folder-plus" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Folders</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ totalFolders }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #db2777, #f472b6); color: #fff;">
						<FeatherIcon name="file" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Files</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ totalFiles }}</p>
					</div>
				</div>
			</div>

			<div class="portal-card-strong p-3">
				<div class="relative">
					<FeatherIcon
						name="search"
						class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
					/>
					<input
						v-model="search"
						type="search"
						class="portal-input pl-9"
						placeholder="Search by project, folder, or file name…"
					/>
				</div>
			</div>

			<div v-if="loading" class="portal-card-strong flex items-center justify-center gap-2 p-10 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading shared files…
			</div>

			<div
				v-else-if="error"
				class="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 shadow-sm"
			>
				{{ error }}
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
				<p class="text-base font-semibold text-[color:var(--portal-text)]">Nothing shared with you yet</p>
				<p class="max-w-md text-sm text-[color:var(--portal-muted)]">
					When a project manager shares a folder or file with you, it will appear here grouped by project.
				</p>
			</div>

			<div
				v-else-if="!filteredProjects.length"
				class="portal-card-strong p-10 text-center text-sm text-[color:var(--portal-muted)]"
			>
				Nothing matches your search.
			</div>

			<div v-else class="space-y-3">
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
						<span class="portal-pill portal-pill-muted">{{ p.folders.length }} folder{{ p.folders.length === 1 ? "" : "s" }}</span>
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
								<FeatherIcon name="folder" class="h-3.5 w-3.5 shrink-0 text-[color:var(--portal-accent)]" />
								<span class="min-w-0 flex-1 truncate font-medium text-[color:var(--portal-text)]">
									{{ f.folder_label }}
								</span>
								<span class="portal-pill portal-pill-muted">{{ f.file_count }} file{{ f.file_count === 1 ? "" : "s" }}</span>
								<span v-if="f.expires_at" class="hidden text-[11px] text-[color:var(--portal-muted)] sm:inline">
									Expires {{ fmtDate(f.expires_at) }}
								</span>
								<span v-else-if="f.native" class="hidden portal-pill portal-pill-muted sm:inline-flex">
									ERPNext share
								</span>
								<button
									class="portal-btn portal-btn-ghost text-xs"
									@click.stop="openFolderInFiles(p.project, f.folder_path)"
								>
									<FeatherIcon name="folder-plus" class="h-3.5 w-3.5" />
									Open in Files
								</button>
							</button>

							<div
								v-if="expandedFolders.has(`${p.project}::${f.folder_path}`)"
								class="bg-white"
							>
								<div
									v-if="!f.files.length"
									class="px-12 py-3 text-xs text-[color:var(--portal-muted)]"
								>
									No files in this folder yet.
								</div>
								<div
									v-for="file in f.files"
									:key="file.name"
									class="flex items-center gap-3 border-t border-[color:var(--portal-border)] px-12 py-2.5 text-sm transition hover:bg-[color:var(--portal-accent-soft)]"
								>
									<FeatherIcon name="file" class="h-3.5 w-3.5 shrink-0 text-[color:var(--portal-muted)]" />
									<div class="min-w-0 flex-1">
										<p class="truncate font-medium text-[color:var(--portal-text)]">
											{{ file.file_name }}
											<span v-if="file.is_private" class="ml-1 text-[10px] text-[color:var(--portal-subtle)]">
												(private)
											</span>
										</p>
										<p class="truncate text-[11px] text-[color:var(--portal-muted)]">
											{{ fileSize(file.file_size) }} · {{ fmtDate(file.creation) }}
										</p>
									</div>
									<a
										v-if="file.file_url"
										:href="file.file_url"
										target="_blank"
										rel="noopener"
										class="portal-btn portal-btn-ghost text-xs"
									>
										<FeatherIcon name="download" class="h-3.5 w-3.5" />
										Open
									</a>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
