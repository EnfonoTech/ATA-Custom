<script setup>
import { ref, onMounted, watch, inject, computed } from "vue";
import { call } from "@/api";
import { useRouter, useRoute } from "vue-router";
import { Button, TextInput, FeatherIcon } from "frappe-ui";

const router = useRouter();
const route = useRoute();
const projects = ref([]);
const loading = ref(true);
const search = ref("");
const status = ref("");
const viewMode = ref("year");
const expandedYears = ref({});
// Membership filter: "all" (default), "team" (I'm a team member), "manage" (I manage)
const membershipFilter = ref("all");

const portalCapabilities = inject("portalCapabilities", ref({}));
const refreshPortalCapabilities = inject("refreshPortalCapabilities", async () => {});

const canCreate = computed(() => !!portalCapabilities.value?.can_create_project);

const showNew = ref(false);
const creating = ref(false);
const createError = ref("");
const newForm = ref({
	project_name: "",
	portal_project_code: "",
	expected_start_date: "",
	expected_end_date: "",
	customer: "",
});

async function load() {
	loading.value = true;
	try {
		const args = {};
		if (search.value.trim()) args.search = search.value.trim();
		if (status.value) args.status = status.value;
		const res = await call({
			method: "portal_app.api.projects.list_projects",
			args,
		});
		projects.value = res.projects || [];
	} catch (e) {
		console.error(e);
	} finally {
		loading.value = false;
	}
}

onMounted(load);

let debounce;
watch([search, status], () => {
	clearTimeout(debounce);
	debounce = setTimeout(load, 300);
});

watch(projects, (list) => {
	const next = {};
	for (const y of Object.keys(groupedProjectsByYear.value)) {
		next[y] = expandedYears.value[y] ?? true;
	}
	expandedYears.value = next;
});

watch(
	[() => route.query.create, canCreate],
	() => {
		if (route.query.create === "1" && canCreate.value) {
			openNew();
		}
	},
	{ immediate: true },
);

function openNew() {
	createError.value = "";
	newForm.value = {
		project_name: "",
		portal_project_code: "",
		expected_start_date: "",
		expected_end_date: "",
		customer: "",
	};
	showNew.value = true;
}

function closeNew() {
	showNew.value = false;
	if (route.query.create === "1") {
		router.replace({ path: "/projects", query: {} });
	}
}

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
	return body?.message || body?.exc || "Request failed.";
}

async function submitCreate() {
	if (!newForm.value.project_name?.trim()) {
		createError.value = "Enter a project title.";
		return;
	}
	creating.value = true;
	createError.value = "";
	try {
		const args = {
			project_name: newForm.value.project_name.trim(),
		};
		if (newForm.value.portal_project_code?.trim()) args.portal_project_code = newForm.value.portal_project_code.trim();
		if (newForm.value.expected_start_date) args.expected_start_date = newForm.value.expected_start_date;
		if (newForm.value.expected_end_date) args.expected_end_date = newForm.value.expected_end_date;
		if (newForm.value.customer?.trim()) args.customer = newForm.value.customer.trim();

		const res = await call({
			method: "portal_app.api.projects.create_project",
			type: "POST",
			args,
		});
		await refreshPortalCapabilities();
		closeNew();
		await load();
		if (res?.name) {
			router.push("/projects/" + encodeURIComponent(res.name));
		}
	} catch (e) {
		createError.value = apiErr(e);
	} finally {
		creating.value = false;
	}
}

function fmtMoney(n) {
	if (n == null || n === "") return "—";
	const x = Number(n);
	return Number.isFinite(x) ? x.toLocaleString() : String(n);
}

function statusClass(s) {
	const t = String(s || "").toLowerCase();
	if (t === "completed") return "bg-green-100 text-green-700";
	if (t === "cancelled") return "bg-red-100 text-red-700";
	if (t === "open") return "bg-blue-100 text-blue-700";
	return "bg-gray-100 text-gray-700";
}

function statusPillClass(s) {
	const t = String(s || "").toLowerCase();
	if (t === "completed") return "portal-pill-success";
	if (t === "cancelled") return "portal-pill-danger";
	if (t === "open") return "portal-pill-accent";
	return "portal-pill-muted";
}

function projectYear(p) {
	const candidates = [p?.expected_start_date, p?.expected_end_date];
	for (const v of candidates) {
		const t = String(v || "").trim();
		const m = t.match(/^(\d{4})[-/]/);
		if (m) return m[1];
		const d = new Date(t);
		if (!Number.isNaN(d.getTime())) return String(d.getFullYear());
	}
	return "No Year";
}

const visibleProjects = computed(() => {
	if (membershipFilter.value === "all") return projects.value;
	const teamSet = new Set(portalCapabilities.value?.team_member_project_names || []);
	const manageSet = new Set(portalCapabilities.value?.manageable_project_names || []);
	return projects.value.filter((p) => {
		if (membershipFilter.value === "team") return teamSet.has(p.name);
		if (membershipFilter.value === "manage") return manageSet.has(p.name);
		return true;
	});
});

const groupedProjectsByYear = computed(() => {
	const out = {};
	for (const p of visibleProjects.value) {
		const y = projectYear(p);
		if (!out[y]) out[y] = [];
		out[y].push(p);
	}
	const order = Object.keys(out).sort((a, b) => {
		if (a === "No Year") return 1;
		if (b === "No Year") return -1;
		return Number(b) - Number(a);
	});
	return order.reduce((acc, y) => {
		acc[y] = out[y];
		return acc;
	}, {});
});

function toggleYear(y) {
	expandedYears.value[y] = !expandedYears.value[y];
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-7xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="folder" class="h-3 w-3" />
							Portfolio
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							Projects
						</h1>
						<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Search, filter and jump into a project workspace. Switch between Year, Cards and Table views.
						</p>
					</div>
					<div class="flex items-center gap-2">
						<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] bg-white p-0.5 shadow-sm">
							<button
								type="button"
								class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition"
								:class="viewMode === 'year' ? 'text-white' : 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'"
								:style="
									viewMode === 'year'
										? 'background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);'
										: ''
								"
								@click="viewMode = 'year'"
							>
								<FeatherIcon name="calendar" class="h-3.5 w-3.5" /> Year
							</button>
							<button
								type="button"
								class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition"
								:class="viewMode === 'cards' ? 'text-white' : 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'"
								:style="
									viewMode === 'cards'
										? 'background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);'
										: ''
								"
								@click="viewMode = 'cards'"
							>
								<FeatherIcon name="grid" class="h-3.5 w-3.5" /> Cards
							</button>
							<button
								type="button"
								class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition"
								:class="viewMode === 'table' ? 'text-white' : 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'"
								:style="
									viewMode === 'table'
										? 'background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);'
										: ''
								"
								@click="viewMode = 'table'"
							>
								<FeatherIcon name="list" class="h-3.5 w-3.5" /> Table
							</button>
						</div>
						<button v-if="canCreate" class="portal-btn portal-btn-primary" @click="openNew">
							<FeatherIcon name="plus" class="h-4 w-4" />
							New project
						</button>
					</div>
				</div>
			</div>

			<div class="portal-card-strong p-4">
				<div class="mb-3 flex flex-wrap items-center gap-2 text-sm text-[color:var(--portal-muted)]">
					<span class="portal-pill portal-pill-muted">
						<FeatherIcon name="folder" class="h-3 w-3" />
						{{ visibleProjects.length }} of {{ projects.length }} projects
					</span>
					<span class="portal-pill portal-pill-accent">
						<FeatherIcon name="circle" class="h-3 w-3" />
						Open {{ visibleProjects.filter((p) => p.status === "Open").length }}
					</span>
					<span class="portal-pill portal-pill-success">
						<FeatherIcon name="check-circle" class="h-3 w-3" />
						Completed {{ visibleProjects.filter((p) => p.status === "Completed").length }}
					</span>
				</div>
				<div class="mb-3 inline-flex rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-0.5 text-xs">
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium"
						:class="membershipFilter === 'all' ? 'bg-white text-[color:var(--portal-text)] shadow-sm' : 'text-[color:var(--portal-muted)]'"
						@click="membershipFilter = 'all'"
					>
						<FeatherIcon name="layers" class="h-3.5 w-3.5" />
						All accessible
					</button>
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium"
						:class="membershipFilter === 'team' ? 'bg-white text-[color:var(--portal-text)] shadow-sm' : 'text-[color:var(--portal-muted)]'"
						@click="membershipFilter = 'team'"
					>
						<FeatherIcon name="users" class="h-3.5 w-3.5" />
						I'm a team member
						<span class="portal-pill portal-pill-muted">
							{{ (portalCapabilities.team_member_project_names || []).length }}
						</span>
					</button>
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium"
						:class="membershipFilter === 'manage' ? 'bg-white text-[color:var(--portal-text)] shadow-sm' : 'text-[color:var(--portal-muted)]'"
						@click="membershipFilter = 'manage'"
					>
						<FeatherIcon name="shield" class="h-3.5 w-3.5" />
						I manage
						<span class="portal-pill portal-pill-muted">
							{{ (portalCapabilities.manageable_project_names || []).length }}
						</span>
					</button>
				</div>
				<div class="flex flex-wrap gap-3">
					<div class="relative min-w-[200px] flex-1">
						<FeatherIcon
							name="search"
							class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
						/>
						<input
							v-model="search"
							type="search"
							placeholder="Search name or code"
							class="portal-input pl-9"
						/>
					</div>
					<select v-model="status" class="portal-input max-w-[200px]">
						<option value="">All statuses</option>
						<option value="Open">Open</option>
						<option value="Completed">Completed</option>
						<option value="Cancelled">Cancelled</option>
					</select>
				</div>
			</div>

			<div v-if="loading" class="flex items-center gap-2 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading…
			</div>
			<div v-else-if="viewMode === 'table'" class="portal-card-strong overflow-x-auto p-0">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-[color:var(--portal-border)] text-[color:var(--portal-muted)]" style="background: var(--portal-bg-dim);">
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Project</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Code</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Status</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Stage</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Client</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">Start</th>
							<th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider">End</th>
							<th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider">Est. cost</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="p in visibleProjects"
							:key="p.name"
							class="cursor-pointer border-b border-[color:var(--portal-border)] transition hover:bg-[color:var(--portal-accent-soft)]"
							@click="router.push('/projects/' + encodeURIComponent(p.name))"
						>
							<td class="px-4 py-3 font-medium text-[color:var(--portal-text)]">{{ p.project_name }}</td>
							<td class="px-4 py-3 text-[color:var(--portal-muted)]">{{ p.portal_project_code || "—" }}</td>
							<td class="px-4 py-3">
								<span class="portal-pill" :class="statusPillClass(p.status)">{{ p.status }}</span>
							</td>
							<td class="px-4 py-3">{{ p.portal_kanban_stage || "—" }}</td>
							<td class="px-4 py-3">{{ p.customer || "—" }}</td>
							<td class="px-4 py-3">{{ p.expected_start_date || "—" }}</td>
							<td class="px-4 py-3">{{ p.expected_end_date || "—" }}</td>
							<td class="px-4 py-3 text-right font-semibold text-[color:var(--portal-text)]">{{ fmtMoney(p.estimated_costing) }}</td>
						</tr>
						<tr v-if="!visibleProjects.length">
							<td colspan="8" class="p-10 text-center text-[color:var(--portal-muted)]">No projects match your filters.</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-else-if="viewMode === 'cards'" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
				<div
					v-for="p in visibleProjects"
					:key="p.name"
					class="portal-card cursor-pointer p-5 transition hover:-translate-y-0.5"
					@click="router.push('/projects/' + encodeURIComponent(p.name))"
				>
					<div class="mb-3 flex items-start justify-between gap-2">
						<div class="min-w-0">
							<div class="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
								<FeatherIcon name="folder" class="h-3 w-3" />
								<span class="truncate">{{ p.portal_project_code || p.name }}</span>
							</div>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">{{ p.project_name || p.name }}</p>
						</div>
						<span class="portal-pill" :class="statusPillClass(p.status)">{{ p.status }}</span>
					</div>
					<div class="space-y-2 text-sm text-[color:var(--portal-muted)]">
						<p class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="user" class="h-3.5 w-3.5" />Client</span>
							<span class="truncate font-medium text-[color:var(--portal-text)]">{{ p.customer || "—" }}</span>
						</p>
						<p class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="trello" class="h-3.5 w-3.5" />Stage</span>
							<span class="font-medium text-[color:var(--portal-text)]">{{ p.portal_kanban_stage || "—" }}</span>
						</p>
						<p class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="calendar" class="h-3.5 w-3.5" />Timeline</span>
							<span class="font-medium text-[color:var(--portal-text)]">{{ p.expected_start_date || "—" }} → {{ p.expected_end_date || "—" }}</span>
						</p>
						<p class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="dollar-sign" class="h-3.5 w-3.5" />Cost</span>
							<span class="font-semibold text-[color:var(--portal-text)]">{{ fmtMoney(p.estimated_costing) }}</span>
						</p>
					</div>
				</div>
				<div
					v-if="!visibleProjects.length"
					class="sm:col-span-2 xl:col-span-3 rounded-2xl border border-dashed border-[color:var(--portal-border-strong)] bg-white p-10 text-center text-[color:var(--portal-muted)]"
				>
					No projects match your filters.
				</div>
			</div>
			<div v-else class="space-y-4">
				<div
					v-for="(yearProjects, year) in groupedProjectsByYear"
					:key="year"
					class="portal-card-strong overflow-hidden"
				>
					<button
						type="button"
						class="flex w-full items-center justify-between px-4 py-3 text-left transition hover:bg-[color:var(--portal-accent-soft)]"
						@click="toggleYear(year)"
					>
						<div class="flex items-center gap-3">
							<span
								class="rounded-lg px-2.5 py-1 text-xs font-semibold text-white"
								style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);"
							>{{ year }}</span>
							<span class="text-sm text-[color:var(--portal-muted)]">{{ yearProjects.length }} projects</span>
						</div>
						<FeatherIcon
							:name="expandedYears[year] ? 'chevron-up' : 'chevron-down'"
							class="h-4 w-4 text-[color:var(--portal-muted)]"
						/>
					</button>
					<div v-if="expandedYears[year]" class="grid gap-3 border-t border-[color:var(--portal-border)] p-4 sm:grid-cols-2 xl:grid-cols-3">
						<div
							v-for="p in yearProjects"
							:key="p.name"
							class="portal-card cursor-pointer p-4 transition hover:-translate-y-0.5"
							@click="router.push('/projects/' + encodeURIComponent(p.name))"
						>
							<div class="mb-2 flex items-start justify-between gap-2">
								<div class="min-w-0">
									<div class="text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
										{{ p.portal_project_code || p.name }}
									</div>
									<p class="mt-1 truncate text-sm font-semibold text-[color:var(--portal-text)]">{{ p.project_name || p.name }}</p>
								</div>
								<span class="portal-pill" :class="statusPillClass(p.status)">{{ p.status }}</span>
							</div>
							<div class="space-y-1 text-xs text-[color:var(--portal-muted)]">
								<p class="flex justify-between gap-2"><span>Client</span><span class="truncate font-medium text-[color:var(--portal-text)]">{{ p.customer || "—" }}</span></p>
								<p class="flex justify-between gap-2"><span>Stage</span><span class="font-medium text-[color:var(--portal-text)]">{{ p.portal_kanban_stage || "—" }}</span></p>
								<p class="flex justify-between gap-2"><span>Timeline</span><span class="font-medium text-[color:var(--portal-text)]">{{ p.expected_start_date || "—" }} → {{ p.expected_end_date || "—" }}</span></p>
								<p class="flex justify-between gap-2"><span>Est. cost</span><span class="font-semibold text-[color:var(--portal-text)]">{{ fmtMoney(p.estimated_costing) }}</span></p>
							</div>
						</div>
					</div>
				</div>
				<div
					v-if="!visibleProjects.length"
					class="rounded-2xl border border-dashed border-[color:var(--portal-border-strong)] bg-white p-10 text-center text-[color:var(--portal-muted)]"
				>
					No projects match your filters.
				</div>
			</div>
		</div>

		<Teleport to="body">
			<div
				v-if="showNew"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="closeNew"></div>
				<div class="relative z-10 w-full max-w-lg rounded-2xl border border-[color:var(--portal-border)] bg-white p-6 shadow-2xl portal-anim-in">
					<div class="mb-4 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<div
								class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
								style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
							>
								<FeatherIcon name="plus" class="h-4 w-4" />
							</div>
							<h2 class="text-lg font-semibold text-[color:var(--portal-text)]">New project</h2>
						</div>
						<button
							type="button"
							class="rounded-lg p-2 text-[color:var(--portal-muted)] transition hover:bg-gray-100 hover:text-[color:var(--portal-text)]"
							@click="closeNew"
						>
							<FeatherIcon name="x" class="h-4 w-4" />
						</button>
					</div>
					<div class="space-y-3">
						<div>
							<label class="portal-section-title mb-1 block">Title *</label>
							<TextInput v-model="newForm.project_name" class="w-full rounded-xl" placeholder="e.g. HQ fit-out" />
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Portal code</label>
							<TextInput v-model="newForm.portal_project_code" class="w-full rounded-xl" placeholder="Optional short code" />
						</div>
						<div class="grid gap-3 sm:grid-cols-2">
							<div>
								<label class="portal-section-title mb-1 block">Start</label>
								<input
									v-model="newForm.expected_start_date"
									type="date"
									class="portal-input"
								/>
							</div>
							<div>
								<label class="portal-section-title mb-1 block">End</label>
								<input
									v-model="newForm.expected_end_date"
									type="date"
									class="portal-input"
								/>
							</div>
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Customer (link name)</label>
							<TextInput
								v-model="newForm.customer"
								class="w-full rounded-xl"
								placeholder="ERPNext Customer name if applicable"
							/>
						</div>
						<p v-if="createError" class="text-sm text-red-600">{{ createError }}</p>
						<div class="flex justify-end gap-2 pt-2">
							<button class="portal-btn portal-btn-ghost" @click="closeNew">Cancel</button>
							<Button
								variant="solid"
								class="rounded-xl"
								style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); color: #fff;"
								:loading="creating"
								@click="submitCreate"
							>
								Create project
							</Button>
						</div>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
