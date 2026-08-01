<script setup>
import { ref, computed, onMounted, inject } from "vue";
import { FeatherIcon } from "frappe-ui";
import { call, uploadFile } from "@/api";

const portalCapabilities = inject("portalCapabilities", ref({}));
const manageableNames = computed(() => portalCapabilities.value?.manageable_project_names || []);

const loading  = ref(true);
const projects = ref([]);
const projectFilter = ref("");

const selectedProject = ref("");
const files    = ref([]);
const filesLoading = ref(false);
const uploadBusy = ref(false);
const error = ref("");

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
	return body?.message || body?.exc || "Something went wrong.";
}

const manageableProjects = computed(() => {
	const list = projects.value.filter((p) => manageableNames.value.includes(p.name));
	if (!projectFilter.value.trim()) return list;
	const q = projectFilter.value.trim().toLowerCase();
	return list.filter((p) => (p.project_name || p.name).toLowerCase().includes(q));
});

async function loadProjects() {
	loading.value = true;
	try {
		const res = await call({ method: "portal_app.api.projects.list_projects" });
		projects.value = res?.projects || [];
	} catch (e) {
		error.value = apiErr(e);
	} finally {
		loading.value = false;
	}
}

async function loadFiles() {
	if (!selectedProject.value) return;
	filesLoading.value = true;
	error.value = "";
	try {
		files.value = await call({
			method: "portal_app.api.contracts.list_contract_files",
			args: { project: selectedProject.value },
		});
	} catch (e) {
		error.value = apiErr(e);
		files.value = [];
	} finally {
		filesLoading.value = false;
	}
}

function selectProject(name) {
	selectedProject.value = name;
	loadFiles();
}

async function onFilePicked(e) {
	const picked = Array.from(e.target.files || []);
	e.target.value = "";
	if (!picked.length || !selectedProject.value) return;
	uploadBusy.value = true;
	error.value = "";
	try {
		for (const file of picked) {
			await uploadFile("portal_app.api.contracts.upload_contract_file", file, {
				project: selectedProject.value,
			});
		}
		await loadFiles();
	} catch (e) {
		error.value = apiErr(e);
	} finally {
		uploadBusy.value = false;
	}
}

async function removeFile(f) {
	if (!confirm(`Delete "${f.file_name}"? This cannot be undone.`)) return;
	try {
		await call({
			method: "portal_app.api.contracts.delete_contract_file",
			type: "POST",
			args: { project: selectedProject.value, file_name: f.name },
		});
		await loadFiles();
	} catch (e) {
		error.value = apiErr(e);
	}
}

function fmtSize(bytes) {
	const n = Number(bytes) || 0;
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
	return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}
function fmtDate(d) {
	if (!d) return "—";
	try {
		return new Date(String(d).replace(" ", "T")).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
	} catch {
		return String(d);
	}
}

onMounted(loadProjects);
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-5xl space-y-5">

			<!-- Header -->
			<div class="portal-hero portal-anim-in">
				<span class="portal-pill portal-pill-accent">
					<FeatherIcon name="lock" class="h-3 w-3" />
					Management Only
				</span>
				<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
					Contracts
				</h1>
				<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
					A restricted upload area for contract documents — kept separate from the shared project Files, visible only to project managers.
				</p>
			</div>

			<div class="grid gap-5" style="grid-template-columns: 260px 1fr;">
				<!-- Project picker -->
				<div class="portal-card-strong p-3 space-y-2 self-start">
					<input v-model="projectFilter" type="text" placeholder="Search projects…" class="portal-input w-full text-sm" />
					<div v-if="loading" class="text-xs px-2 py-3 text-center" style="color:var(--portal-muted);">Loading…</div>
					<div v-else class="space-y-1 max-h-[60vh] overflow-y-auto">
						<button
							v-for="p in manageableProjects" :key="p.name"
							type="button"
							class="w-full text-left rounded-lg px-3 py-2 text-xs font-medium transition"
							:style="selectedProject === p.name ? 'background:var(--portal-accent);color:#fff;' : 'color:var(--portal-text);'"
							@click="selectProject(p.name)"
						>
							{{ p.project_name || p.name }}
						</button>
						<p v-if="!manageableProjects.length" class="text-xs px-2 py-3 text-center" style="color:var(--portal-muted);">
							No manageable projects found.
						</p>
					</div>
				</div>

				<!-- Contract files -->
				<div class="portal-card-strong overflow-hidden">
					<div v-if="!selectedProject" class="p-10 text-center text-sm" style="color:var(--portal-muted);">
						Pick a project on the left to view or upload its contracts.
					</div>
					<template v-else>
						<div class="flex items-center justify-between px-4 py-3 border-b" style="border-color:var(--portal-border);">
							<h3 class="text-sm font-semibold" style="color:var(--portal-text);">
								{{ (projects.find(p => p.name === selectedProject) || {}).project_name || selectedProject }}
							</h3>
							<label class="portal-btn portal-btn-primary cursor-pointer">
								<FeatherIcon name="upload" class="h-4 w-4" />
								{{ uploadBusy ? "Uploading…" : "Upload Contract" }}
								<input type="file" multiple accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" class="hidden" :disabled="uploadBusy" @change="onFilePicked" />
							</label>
						</div>

						<p v-if="error" class="px-4 pt-3 text-xs text-red-600">{{ error }}</p>

						<div v-if="filesLoading" class="p-6 text-center text-sm" style="color:var(--portal-muted);">Loading…</div>
						<div v-else-if="!files.length" class="p-10 text-center text-sm" style="color:var(--portal-muted);">
							No contracts uploaded yet for this project.
						</div>
						<div v-else class="divide-y" style="border-color:var(--portal-border);">
							<div v-for="f in files" :key="f.name" class="flex items-center gap-3 px-4 py-3">
								<FeatherIcon name="file-text" class="h-4 w-4 flex-shrink-0" style="color:var(--portal-accent);" />
								<a :href="f.file_url" target="_blank" rel="noopener" class="flex-1 min-w-0 text-sm font-medium truncate hover:underline" style="color:var(--portal-text);">
									{{ f.file_name }}
								</a>
								<span class="text-xs flex-shrink-0" style="color:var(--portal-muted);">{{ fmtSize(f.file_size) }}</span>
								<span class="text-xs flex-shrink-0" style="color:var(--portal-muted);">{{ fmtDate(f.creation) }}</span>
								<button class="flex-shrink-0 text-gray-300 hover:text-red-500" @click="removeFile(f)">
									<FeatherIcon name="trash-2" class="h-4 w-4" />
								</button>
							</div>
						</div>
					</template>
				</div>
			</div>

		</div>
	</div>
</template>
