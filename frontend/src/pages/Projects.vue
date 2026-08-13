<script setup>
import { ref, onMounted, onBeforeUnmount, watch, inject, computed } from "vue";
import { call } from "@/api";
import { useRouter, useRoute } from "vue-router";
import { Button, TextInput, FeatherIcon } from "frappe-ui";
import { useToast } from "@/composables/useToast";

const router = useRouter();
const route = useRoute();
const toaster = useToast();
const projects = ref([]);
const loading = ref(true);
const search = ref("");
const status = ref("");
const viewMode = ref("table");
const expandedYears = ref({});
// Membership filter: "all" (default), "team" (I'm a team member), "manage" (I manage)
const membershipFilter = ref("all");

const portalCapabilities = inject("portalCapabilities", ref({}));
const refreshPortalCapabilities = inject("refreshPortalCapabilities", async () => {});

const canCreate = computed(() => !!portalCapabilities.value?.can_create_project);
const isManager = computed(() => !!portalCapabilities.value?.is_manager);

// ── ERP Server popup (Client link + Project Files) ───────────────────────────
// Teleported centered modal (same pattern as "New project") — never clipped.
const erpDropdownProject = ref(null);
function toggleErpDropdown(p) {
	erpDropdownProject.value = erpDropdownProject.value?.name === p.name ? null : p;
}
function closeErpDropdown() { erpDropdownProject.value = null; }
function goToProjectFiles(p) {
	closeErpDropdown();
	router.push({ path: "/files", query: { project: p.name } });
}

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

// ── Customer picker for "New project" (search-as-you-type, or full list on focus) ──
const newCustomerSearchQ = ref("");
const newCustomerHits = ref([]);
const newCustomerPickerRef = ref(null);
let newCustomerSearchTimer = null;

async function runNewCustomerSearch(q) {
	try {
		newCustomerHits.value = await call({
			method: "portal_app.api.projects.search_customers",
			args: { txt: (q || "").trim() },
		});
	} catch (e) {
		console.error(e);
		newCustomerHits.value = [];
	}
}
watch(newCustomerSearchQ, (q) => {
	clearTimeout(newCustomerSearchTimer);
	newCustomerSearchTimer = setTimeout(() => runNewCustomerSearch(q), 200);
});
function onNewCustomerFocus() {
	if (!newCustomerHits.value.length) runNewCustomerSearch(newCustomerSearchQ.value);
}
function linkNewCustomer(name) {
	newForm.value.customer = name;
	newCustomerSearchQ.value = "";
	newCustomerHits.value = [];
}
function onDocClickCloseNewCustomerPicker(e) {
	if (newCustomerPickerRef.value && !newCustomerPickerRef.value.contains(e.target)) {
		newCustomerHits.value = [];
	}
}
onMounted(() => document.addEventListener("click", onDocClickCloseNewCustomerPicker));
onBeforeUnmount(() => document.removeEventListener("click", onDocClickCloseNewCustomerPicker));

// ── Edit Project ─────────────────────────────────────────────────────────────
const showEdit   = ref(false);
const saving     = ref(false);
const editError  = ref("");
const portalUsers = ref([]);
const editForm   = ref({});
const canManage  = computed(() => (portalCapabilities.value?.manageable_project_names || []).length > 0);

async function openEdit(p, e) {
	e.stopPropagation();
	editError.value = "";
	editForm.value = {
		name:                   p.name,
		project_name:           p.project_name || "",
		status:                 p.status || "Open",
		portal_office:          p.portal_office || "",
		portal_phase:           p.portal_phase || "",
		portal_project_manager: p.portal_project_manager || "",
		estimated_costing:      p.estimated_costing || "",
		expected_start_date:    p.expected_start_date || "",
		expected_end_date:      p.expected_end_date || "",
		percent_complete:       p.percent_complete || 0,
		notes:                  p.notes || "",
		portal_server_t:        p.portal_server_t || "",
		portal_server_a:        p.portal_server_a || "",
		portal_server_c:        p.portal_server_c || "",
	};
	if (!portalUsers.value.length) {
		try {
			portalUsers.value = await call({ method: "portal_app.api.projects.get_portal_users" });
		} catch { portalUsers.value = []; }
	}
	showEdit.value = true;
}

function closeEdit() { showEdit.value = false; }

async function submitEdit() {
	if (!editForm.value.project_name?.trim()) { editError.value = "Project name required."; return; }
	saving.value = true; editError.value = "";
	try {
		await call({
			method: "portal_app.api.projects.update_project",
			type: "POST",
			args: { project: editForm.value.name, ...editForm.value },
		});
		showEdit.value = false;
		await load();
	} catch (e) { editError.value = apiErr(e); }
	finally { saving.value = false; }
}

function canEditProject(p) {
	return (portalCapabilities.value?.manageable_project_names || []).includes(p.name);
}

// ── Add Member ────────────────────────────────────────────────────────────────
const showMembers   = ref(false);
const membersProject = ref(null);
const membersList   = ref([]);
const savingMembers = ref(false);
const memberSearch  = ref("");

async function openMembers(p, e) {
	e.stopPropagation();
	membersProject.value = p;
	membersList.value = [p.portal_project_manager || ""];
	if (!portalUsers.value.length) {
		try { portalUsers.value = await call({ method: "portal_app.api.projects.get_portal_users" }); } catch { portalUsers.value = []; }
	}
	showMembers.value = true;
}

function closeMembers() { showMembers.value = false; membersProject.value = null; }

function toggleMember(username) {
	const idx = membersList.value.indexOf(username);
	if (idx >= 0) membersList.value.splice(idx, 1);
	else membersList.value.push(username);
}

async function saveMembers() {
	if (!membersProject.value || !membersList.value[0]) return;
	savingMembers.value = true;
	try {
		await call({
			method: "portal_app.api.projects.update_project",
			type: "POST",
			args: { project: membersProject.value.name, portal_project_manager: membersList.value[0] },
		});
		closeMembers();
		await load();
	} catch (e) { console.error(e); }
	finally { savingMembers.value = false; }
}

const filteredUsers = computed(() => {
	const q = memberSearch.value.toLowerCase();
	return (portalUsers.value || []).filter(u =>
		!q || (u.full_name || u.name).toLowerCase().includes(q)
	);
});

// ── Delete Project ────────────────────────────────────────────────────────────
const confirmDelete = ref(null);

async function deleteProject(p, e) {
	e.stopPropagation();
	if (confirmDelete.value !== p.name) {
		confirmDelete.value = p.name;
		setTimeout(() => { if (confirmDelete.value === p.name) confirmDelete.value = null; }, 3000);
		return;
	}
	confirmDelete.value = null;
	try {
		await call({ method: "portal_app.api.projects.delete_project", type: "POST", args: { project: p.name } });
		await load();
	} catch (e) {
		toaster.error(apiErr(e), { title: "Could not delete project" });
	}
}

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

const officeOptions = ref([]);

onMounted(async () => {
	load();
	try {
		const offices = await call({ method: "portal_app.api.teams.get_offices" });
		if (Array.isArray(offices)) officeOptions.value = offices;
	} catch {}
});

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

async function openNew() {
	createError.value = "";
	newForm.value = {
		project_name: "",
		portal_project_code: "",
		expected_start_date: "",
		expected_end_date: "",
		customer: "",
		portal_phase: "",
		portal_project_manager: "",
	};
	newCustomerSearchQ.value = "";
	newCustomerHits.value = [];
	if (!portalUsers.value.length) {
		try {
			portalUsers.value = await call({ method: "portal_app.api.projects.get_portal_users" });
		} catch { portalUsers.value = []; }
	}
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
		if (newForm.value.portal_phase) args.portal_phase = newForm.value.portal_phase;
		if (newForm.value.portal_project_manager) args.portal_project_manager = newForm.value.portal_project_manager;

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

function rowBgStyle(p) {
	const isHold = ["On Hold","Cancelled","Hold","Temp Hold"].includes(p.status);
	return { opacity: isHold ? 0.6 : 1 };
}

function progressColor(pct) {
	const n = Number(pct || 0);
	if (n >= 80) return "#10B981";
	if (n >= 40) return "#185FA5";
	return "#F59E0B";
}

function fmtMoney(n) {
	if (n == null || n === "") return "—";
	const x = Number(n);
	return Number.isFinite(x) ? `SAR ${x.toLocaleString()}` : String(n);
}

function statusClass(s) {
	const t = String(s || "").toLowerCase();
	if (t === "completed") return "portal-pill-success";
	if (t === "cancelled") return "portal-pill-danger";
	if (t === "open") return "portal-pill-accent";
	return "portal-pill-muted";
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

function printProjects() {
	viewMode.value = "table";
	setTimeout(() => window.print(), 150);
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-7xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-center justify-between gap-3">
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
					<div class="flex items-center gap-2 ml-auto shrink-0">
						<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] p-0.5 shadow-sm" style="background:var(--portal-surface)">
							<button
								type="button"
								class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition"
								:class="viewMode === 'year' ? 'text-white' : 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'"
								:style="
									viewMode === 'year'
										? 'background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);'
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
										? 'background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);'
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
										? 'background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);'
										: ''
								"
								@click="viewMode = 'table'"
							>
								<FeatherIcon name="list" class="h-3.5 w-3.5" /> Table
							</button>
						</div>
						<button
							class="portal-btn portal-btn-ghost"
							@click="printProjects"
						>
							<FeatherIcon name="printer" class="h-4 w-4" />
							Print
						</button>
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
				<div class="mb-3 inline-flex rounded-xl border border-[color:var(--portal-border)] p-0.5 text-xs" style="background:var(--portal-surface-alt)">
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition"
						:style="membershipFilter === 'all'
							? 'background:var(--portal-accent);color:var(--portal-accent-fg)'
							: 'color:var(--portal-muted)'"
						@click="membershipFilter = 'all'"
					>
						<FeatherIcon name="layers" class="h-3.5 w-3.5" />
						All accessible
					</button>
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition"
						:style="membershipFilter === 'team'
							? 'background:var(--portal-accent);color:var(--portal-accent-fg)'
							: 'color:var(--portal-muted)'"
						@click="membershipFilter = 'team'"
					>
						<FeatherIcon name="users" class="h-3.5 w-3.5" />
						I'm a team member
						<span class="portal-pill portal-pill-muted">
							{{ (portalCapabilities.team_member_project_names || []).length }}
						</span>
					</button>
					<button
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition"
						:style="membershipFilter === 'manage'
							? 'background:var(--portal-accent);color:var(--portal-accent-fg)'
							: 'color:var(--portal-muted)'"
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
						<tr class="text-white text-xs font-semibold uppercase tracking-wider" style="background:#0F172A;">
							<th class="px-4 py-3">Project</th>
							<th class="px-4 py-3">Assignee</th>
							<th class="px-4 py-3">Phase</th>
							<th class="px-4 py-3">Status</th>
							<th v-if="isManager" class="px-4 py-3">Lead Architect</th>
							<th class="px-4 py-3">Servers</th>
							<th class="px-4 py-3">Upcoming Milestone</th>
							<th class="px-4 py-3">Progress</th>
							<th class="px-4 py-3 text-right">Actions</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="p in visibleProjects"
							:key="p.name"
							class="cursor-pointer border-b border-[color:var(--portal-border)] transition"
							:style="rowBgStyle(p)"
							@click="router.push('/projects/' + encodeURIComponent(p.name))"
							@mouseenter="$event.currentTarget.style.filter='brightness(0.95)'"
							@mouseleave="$event.currentTarget.style.filter=''"
						>
							<!-- Project -->
							<td class="px-4 py-3">
								<div class="font-semibold text-sm" style="color:var(--portal-text);">{{ p.project_name }}</div>
								<div v-if="p.portal_project_code" class="text-[10px] mt-0.5" style="color:var(--portal-muted);">{{ p.portal_project_code }}</div>
							</td>
							<!-- Office -->
							<td class="px-4 py-3 text-xs font-medium" style="color:var(--portal-text);">{{ p.portal_office || "—" }}</td>
							<!-- Phase -->
							<td class="px-4 py-3 text-xs font-medium" style="color:var(--portal-text);">{{ p.portal_phase || "—" }}</td>
							<!-- Status -->
							<td class="px-4 py-3">
								<span class="portal-pill" :class="statusPillClass(p.status)">{{ p.status }}</span>
							</td>
							<!-- Lead Architect -->
							<td v-if="isManager" class="px-4 py-3 text-xs" style="color:var(--portal-text);">{{ p.portal_project_manager || "—" }}</td>
							<!-- Servers (T = Google Drive, A = Autodesk, ERP = Client link + this project's uploaded files) -->
							<td class="px-4 py-3">
								<div class="flex items-center gap-1">
									<a
										v-for="s in [['t', p.portal_server_t, '#185FA5'], ['a', p.portal_server_a, '#276749']]"
										:key="s[0]"
										:href="s[1] || undefined"
										:target="s[1] ? '_blank' : undefined"
										rel="noopener noreferrer"
										:title="s[1] ? (s[0].toUpperCase() + '-Server') : (s[0].toUpperCase() + '-Server not set')"
										class="flex h-6 w-6 items-center justify-center rounded-md text-[10px] font-bold uppercase transition"
										:style="s[1] ? { background: s[2] + '22', color: s[2], cursor: 'pointer' } : { background: 'rgba(128,128,128,0.1)', color: 'var(--portal-subtle)', cursor: 'default' }"
										@click.stop="!s[1] && $event.preventDefault()"
									>{{ s[0] }}</a>

									<!-- ERP Server — two portions: the client's own server link, and this project's uploaded data (Files hub) -->
									<button
										type="button"
										class="flex h-6 w-6 items-center justify-center rounded-md text-[10px] font-bold uppercase transition"
										style="background:#9B233522;color:#9B2335;cursor:pointer;"
										title="ERP Server — client link & project files"
										@click.stop="toggleErpDropdown(p)"
									>erp</button>
								</div>
							</td>
							<!-- Upcoming Milestone -->
							<td class="px-4 py-3 text-xs" style="color:var(--portal-muted);">{{ p.portal_upcoming_milestone || "—" }}</td>
							<!-- Progress bar -->
							<td class="px-4 py-3" style="min-width:110px;">
								<div class="flex items-center gap-2">
									<div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background:rgba(128,128,128,0.2);">
										<div class="h-full rounded-full transition-all" :style="{ width: (p.percent_complete || 0) + '%', background: progressColor(p.percent_complete) }"></div>
									</div>
									<span class="text-[10px] font-semibold w-7 text-right" style="color:var(--portal-muted);">{{ Math.round(p.percent_complete || 0) }}%</span>
								</div>
							</td>
							<!-- Actions -->
							<td class="px-4 py-3 text-right">
								<div class="flex items-center justify-end gap-1">
									<!-- View -->
									<button
										class="rounded-lg p-1.5 transition hover:bg-[color:var(--portal-surface-alt)]"
										title="View project"
										@click.stop="router.push('/projects/' + encodeURIComponent(p.name))"
									>
										<FeatherIcon name="eye" class="h-3.5 w-3.5" style="color:var(--portal-muted);"/>
									</button>
									<!-- Add Member -->
									<button
										v-if="canEditProject(p)"
										class="rounded-lg p-1.5 transition hover:bg-[color:var(--portal-surface-alt)]"
										title="Manage members"
										@click.stop="openMembers(p, $event)"
									>
										<FeatherIcon name="user-plus" class="h-3.5 w-3.5" style="color:var(--portal-muted);"/>
									</button>
									<!-- Edit -->
									<button
										v-if="canEditProject(p)"
										class="rounded-lg p-1.5 transition hover:bg-[color:var(--portal-accent-soft)]"
										title="Edit project"
										@click.stop="openEdit(p, $event)"
									>
										<FeatherIcon name="edit-2" class="h-3.5 w-3.5" style="color:var(--portal-accent);"/>
									</button>
									<!-- Delete -->
									<button
										v-if="canEditProject(p)"
										class="rounded-lg p-1.5 transition"
										:class="confirmDelete === p.name ? 'bg-red-100' : 'hover:bg-red-50'"
										:title="confirmDelete === p.name ? 'Click again to confirm delete' : 'Delete project'"
										@click.stop="deleteProject(p, $event)"
									>
										<FeatherIcon name="trash-2" class="h-3.5 w-3.5" :style="{ color: confirmDelete === p.name ? '#dc2626' : '#9ca3af' }"/>
									</button>
								</div>
							</td>
						</tr>
						<tr v-if="!visibleProjects.length">
							<td colspan="9" class="p-10 text-center text-[color:var(--portal-muted)]">No projects match your filters.</td>
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
						<p v-if="isManager" class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="user" class="h-3.5 w-3.5" />Lead Architecture</span>
							<span class="truncate font-medium text-[color:var(--portal-text)]">{{ p.portal_project_manager || "—" }}</span>
						</p>
						<p class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="trello" class="h-3.5 w-3.5" />Stage</span>
							<span class="font-medium text-[color:var(--portal-text)]">{{ p.portal_kanban_stage || "—" }}</span>
						</p>
						<p class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="calendar" class="h-3.5 w-3.5" />Timeline</span>
							<span class="font-medium text-[color:var(--portal-text)]">{{ p.expected_start_date || "—" }} → {{ p.expected_end_date || "—" }}</span>
						</p>
						<p v-if="isManager" class="flex items-center justify-between gap-2">
							<span class="flex items-center gap-1.5"><FeatherIcon name="dollar-sign" class="h-3.5 w-3.5" />Cost</span>
							<span class="font-semibold text-[color:var(--portal-text)]">{{ fmtMoney(p.estimated_costing) }}</span>
						</p>
					</div>
				</div>
				<div
					v-if="!visibleProjects.length"
					class="sm:col-span-2 xl:col-span-3 rounded-2xl border border-dashed border-[color:var(--portal-border-strong)] p-10 text-center text-[color:var(--portal-muted)]" style="background:var(--portal-surface)"
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
								style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
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
								<p v-if="isManager" class="flex justify-between gap-2"><span>Lead Architecture</span><span class="truncate font-medium text-[color:var(--portal-text)]">{{ p.portal_project_manager || "—" }}</span></p>
								<p class="flex justify-between gap-2"><span>Stage</span><span class="font-medium text-[color:var(--portal-text)]">{{ p.portal_kanban_stage || "—" }}</span></p>
								<p class="flex justify-between gap-2"><span>Timeline</span><span class="font-medium text-[color:var(--portal-text)]">{{ p.expected_start_date || "—" }} → {{ p.expected_end_date || "—" }}</span></p>
								<p v-if="isManager" class="flex justify-between gap-2"><span>Est. cost</span><span class="font-semibold text-[color:var(--portal-text)]">{{ fmtMoney(p.estimated_costing) }}</span></p>
							</div>
						</div>
					</div>
				</div>
				<div
					v-if="!visibleProjects.length"
					class="rounded-2xl border border-dashed border-[color:var(--portal-border-strong)] p-10 text-center text-[color:var(--portal-muted)]" style="background:var(--portal-surface)"
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
				<div class="relative z-10 w-full max-w-lg rounded-2xl border border-[color:var(--portal-border)] p-6 shadow-2xl portal-anim-in" style="background:var(--portal-surface)">
					<div class="mb-4 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<div
								class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
								style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%);"
							>
								<FeatherIcon name="plus" class="h-4 w-4" />
							</div>
							<h2 class="text-lg font-semibold text-[color:var(--portal-text)]">New project</h2>
						</div>
						<button
							type="button"
							class="rounded-lg p-2 transition"
							style="color:var(--portal-muted)"
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
						<div class="grid gap-3 sm:grid-cols-2">
							<div>
								<label class="portal-section-title mb-1 block">Phase</label>
								<select v-model="newForm.portal_phase" class="portal-input">
									<option value="">— Select —</option>
									<option>Schematic Design</option>
									<option>CD</option>
									<option>CD+</option>
									<option>DD</option>
									<option>TD</option>
									<option>FC</option>
									<option>Construction</option>
								</select>
							</div>
							<div>
								<label class="portal-section-title mb-1 block">Lead Architect</label>
								<select v-model="newForm.portal_project_manager" class="portal-input">
									<option value="">— Select —</option>
									<option v-for="u in portalUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
								</select>
							</div>
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Customer</label>
							<div ref="newCustomerPickerRef" class="space-y-2">
								<TextInput
									v-model="newCustomerSearchQ"
									class="w-full rounded-xl"
									placeholder="Click to see existing customers, or type to filter…"
									@focus="onNewCustomerFocus"
								/>
								<div
									v-if="newCustomerHits.length"
									class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
								>
									<button
										v-for="c in newCustomerHits"
										:key="c.name"
										type="button"
										class="flex w-full flex-col gap-0.5 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white"
										@click="linkNewCustomer(c.name)"
									>
										<span class="font-medium text-gray-900">{{ c.customer_name || c.name }}</span>
										<span class="text-xs text-gray-500">{{ c.name }}</span>
									</button>
								</div>
								<p v-if="newForm.customer" class="text-xs text-[color:var(--portal-muted)]">
									Selected: <strong class="text-[color:var(--portal-text)]">{{ newForm.customer }}</strong>
								</p>
							</div>
						</div>
						<p v-if="createError" class="text-sm text-red-600">{{ createError }}</p>
						<div class="flex justify-end gap-2 pt-2">
							<button class="portal-btn portal-btn-ghost" @click="closeNew">Cancel</button>
							<Button
								variant="solid"
								class="rounded-xl"
								style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%); color: #fff;"
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

		<!-- ── Assign Architect Modal ────────────────────────────────────── -->
		<Teleport to="body">
			<div v-if="showMembers" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.45);" @click.self="closeMembers">
				<div class="w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden" style="background:#ffffff;">
					<!-- Header -->
					<div class="flex items-center justify-between px-6 py-5">
						<h2 class="text-lg font-bold text-gray-900">Assign Architect</h2>
						<button class="h-8 w-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 transition" @click="closeMembers">
							<FeatherIcon name="x" class="h-4 w-4"/>
						</button>
					</div>

					<!-- Body -->
					<div class="px-6 pb-6 space-y-4">
						<p class="text-sm text-gray-500">
							Project: <strong class="text-gray-900">{{ membersProject?.project_name }}</strong>
						</p>

						<div>
							<label class="block text-sm text-gray-500 mb-2">Select Architect</label>
							<select
								v-model="membersList[0]"
								class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-400"
							>
								<option value="">— Select —</option>
								<option v-for="u in portalUsers" :key="u.name" :value="u.name">
									{{ u.full_name || u.name }}
								</option>
							</select>
						</div>

						<p v-if="membersProject?.portal_project_manager" class="text-sm text-gray-400">
							Currently assigned to: <strong class="text-gray-700">{{ portalUsers.find(u => u.name === membersProject.portal_project_manager)?.full_name || membersProject.portal_project_manager }}</strong>
						</p>

						<div class="flex gap-3 pt-2">
							<button
								class="flex-1 rounded-xl py-2.5 text-sm font-bold text-white transition"
								style="background:#FF6B00;"
								:disabled="savingMembers || !membersList[0]"
								@click="saveMembers"
							>{{ savingMembers ? "Assigning…" : "Assign" }}</button>
							<button class="rounded-xl px-5 py-2.5 text-sm font-medium text-gray-600 border border-gray-200 hover:bg-gray-50 transition" @click="closeMembers">Cancel</button>
						</div>
					</div>
				</div>
			</div>
		</Teleport>

		<!-- ── Edit Project Modal ────────────────────────────────────────── -->
		<Teleport to="body">
			<div v-if="showEdit" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeEdit">
				<div class="w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden" style="background:#ffffff;">
					<!-- Header -->
					<div class="flex items-center justify-between px-6 py-5 border-b border-gray-100">
						<div>
							<div class="flex items-center gap-2">
								<FeatherIcon name="edit-2" class="h-4 w-4" style="color:#f59e0b;"/>
								<h2 class="text-lg font-bold text-gray-900">Edit Project</h2>
							</div>
							<p class="text-xs text-gray-400 mt-0.5">{{ editForm.name }}</p>
						</div>
						<button class="h-8 w-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 transition" @click="closeEdit">
							<FeatherIcon name="x" class="h-4 w-4"/>
						</button>
					</div>

					<!-- Body -->
					<div class="px-6 py-5 space-y-4 max-h-[70vh] overflow-y-auto">
						<!-- Project Name -->
						<div>
							<label class="block text-xs font-semibold text-gray-600 mb-1.5">Project Name</label>
							<input
								v-model="editForm.project_name"
								type="text"
								class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
							/>
						</div>

						<!-- Office + Phase -->
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label class="block text-xs font-semibold text-gray-600 mb-1.5">Office</label>
								<select v-model="editForm.portal_office" class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400">
									<option value="">— Select —</option>
									<option v-for="o in officeOptions" :key="o" :value="o">{{ o }}</option>
								</select>
							</div>
							<div>
								<label class="block text-xs font-semibold text-gray-600 mb-1.5">Phase</label>
								<select v-model="editForm.portal_phase" class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400">
									<option value="">— Select —</option>
									<option>Schematic Design</option>
									<option>CD</option>
									<option>CD+</option>
									<option>DD</option>
									<option>TD</option>
									<option>FC</option>
									<option>Construction</option>
								</select>
							</div>
						</div>

						<!-- Status + Lead Architect -->
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label class="block text-xs font-semibold text-gray-600 mb-1.5">Status</label>
								<select v-model="editForm.status" class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400">
									<option>Open</option>
									<option>In Progress</option>
									<option>Completed</option>
									<option>On Hold</option>
									<option>Cancelled</option>
								</select>
							</div>
							<div>
								<label class="block text-xs font-semibold text-gray-600 mb-1.5">Lead Architect</label>
								<select v-model="editForm.portal_project_manager" class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400">
									<option value="">— Select —</option>
									<option v-for="u in portalUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
								</select>
							</div>
						</div>

						<!-- Start Date + End Date -->
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label class="block text-xs font-semibold text-gray-600 mb-1.5">Start Date</label>
								<input v-model="editForm.expected_start_date" type="date" class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"/>
							</div>
							<div>
								<label class="block text-xs font-semibold text-gray-600 mb-1.5">End Date</label>
								<input v-model="editForm.expected_end_date" type="date" class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"/>
							</div>
						</div>

						<!-- Progress -->
						<div>
							<label class="block text-xs font-semibold text-gray-600 mb-1.5">Progress: {{ editForm.percent_complete }}%</label>
							<input
								v-model.number="editForm.percent_complete"
								type="range" min="0" max="100" step="5"
								class="w-full h-2 rounded-full appearance-none cursor-pointer"
								style="accent-color:#f59e0b;"
							/>
						</div>

						<!-- Estimated Cost (managers only) -->
						<div v-if="isManager">
							<label class="block text-xs font-semibold text-gray-600 mb-1.5">Estimated Cost (SAR)</label>
							<input v-model="editForm.estimated_costing" type="number" min="0" step="1" placeholder="e.g. 500000" class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"/>
						</div>

						<!-- Servers -->
						<div>
							<label class="block text-xs font-semibold text-gray-600 mb-1.5">Servers (links)</label>
							<div class="space-y-2">
								<input v-model="editForm.portal_server_t" type="url" placeholder="T-Server — Google Drive link" class="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"/>
								<input v-model="editForm.portal_server_a" type="url" placeholder="A-Server — Autodesk link" class="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"/>
								<input v-model="editForm.portal_server_c" type="url" placeholder="ERP Server — Client server link" class="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"/>
							</div>
						</div>

						<!-- Remarks -->
						<div>
							<label class="block text-xs font-semibold text-gray-600 mb-1.5">Remarks</label>
							<textarea
								v-model="editForm.notes"
								rows="3"
								class="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400 resize-none"
							></textarea>
						</div>

						<p v-if="editError" class="text-xs text-red-600">{{ editError }}</p>
					</div>

					<!-- Footer -->
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
						<button class="rounded-xl px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 transition" @click="closeEdit">Cancel</button>
						<button
							class="rounded-xl px-5 py-2 text-sm font-semibold text-white transition"
							style="background:#f59e0b;"
							:disabled="saving"
							@click="submitEdit"
						>
							{{ saving ? "Saving…" : "Save Changes" }}
						</button>
					</div>
				</div>
			</div>
		</Teleport>

		<!-- ERP Server popup — same centered-modal pattern as "New project" above, so it can never be clipped -->
		<Teleport to="body">
			<div
				v-if="erpDropdownProject"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="closeErpDropdown"></div>
				<div class="relative z-10 w-full max-w-xs rounded-2xl shadow-2xl overflow-hidden portal-anim-in" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
					<div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--portal-border);">
						<h2 class="text-sm font-semibold" style="color:var(--portal-text);">ERP Server</h2>
						<button class="h-7 w-7 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeErpDropdown">
							<FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
						</button>
					</div>
					<div class="p-2">
						<a
							:href="erpDropdownProject.portal_server_c || undefined"
							:target="erpDropdownProject.portal_server_c ? '_blank' : undefined"
							rel="noopener noreferrer"
							class="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition"
							:style="erpDropdownProject.portal_server_c ? 'color:var(--portal-text);cursor:pointer;' : 'color:var(--portal-subtle);cursor:default;'"
							@click="!erpDropdownProject.portal_server_c && $event.preventDefault()"
							@mouseenter="$event.currentTarget.style.background='var(--portal-surface-alt)'"
							@mouseleave="$event.currentTarget.style.background=''"
						>
							<FeatherIcon name="link" class="h-4 w-4 shrink-0" />
							Client Server{{ erpDropdownProject.portal_server_c ? "" : " (not set)" }}
						</a>
						<a
							href="#"
							class="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition"
							style="color:var(--portal-text);cursor:pointer;"
							@click.prevent="goToProjectFiles(erpDropdownProject)"
							@mouseenter="$event.currentTarget.style.background='var(--portal-surface-alt)'"
							@mouseleave="$event.currentTarget.style.background=''"
						>
							<FeatherIcon name="folder" class="h-4 w-4 shrink-0" />
							Project Files
						</a>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>

<style>
@media print {
	* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

	/* Hide sidebar/nav (layout shell) */
	nav, aside, header, footer { display: none !important; }

	/* Hide page hero (title + view-mode buttons) */
	.portal-hero { display: none !important; }

	/* Hide filter card (the p-4 one) */
	.portal-card-strong:not(.overflow-x-auto) { display: none !important; }

	/* Hide loading/empty state */
	.text-\[color\:var\(--portal-muted\)\] { display: none !important; }

	/* Page setup */
	body, html { margin: 0 !important; padding: 0 !important; background: #fff !important; }
	.h-full { height: auto !important; overflow: visible !important; }
	.overflow-auto { overflow: visible !important; }
	.p-6 { padding: 16px !important; }
	.mx-auto, .max-w-7xl { max-width: 100% !important; }
	.space-y-5 > * + * { margin-top: 0 !important; }

	/* Print header injected via pseudo-elements */
	.portal-card-strong.overflow-x-auto {
		display: block !important;
		padding: 0 !important;
		box-shadow: none !important;
		border: none !important;
	}
	.portal-card-strong.overflow-x-auto::before {
		content: "Project Register";
		display: block !important;
		font-size: 22px;
		font-weight: 700;
		color: #111827;
		padding: 16px 16px 2px;
		font-family: system-ui, sans-serif;
	}
	.portal-card-strong.overflow-x-auto::after {
		content: "";
		display: block !important;
		padding: 0 16px 14px;
		border-bottom: 1px solid #e5e7eb;
	}

	/* Table */
	table { width: 100% !important; font-size: 11px !important; border-collapse: collapse !important; }
	thead tr { background: #0F172A !important; color: #fff !important; }
	th { padding: 8px 12px !important; text-align: left !important; font-size: 10px !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; }
	td { padding: 7px 12px !important; border-bottom: 1px solid #e5e7eb !important; vertical-align: middle !important; }

	/* Alternate row background for readability */
	tbody tr:nth-child(even) td { background: #f9fafb !important; }

	/* Hide Actions column (last column) */
	th:last-child, td:last-child { display: none !important; }

	/* Progress bar visible */
	.h-2 { height: 6px !important; border-radius: 3px !important; }

	/* Keep office/status badges */
	span[class*="inline-flex"] { display: inline-flex !important; }
}
</style>
