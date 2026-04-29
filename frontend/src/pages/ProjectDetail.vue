<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, inject } from "vue";
import { call } from "@/api";
import { useRouter } from "vue-router";
import { Button, TextInput, Password, FeatherIcon } from "frappe-ui";
import FileUploadPanel from "@/component/FileUploadPanel.vue";

const props = defineProps({
	name: { type: String, required: true },
});

const router = useRouter();
const loading = ref(true);
const payload = ref(null);

const portalCapabilities = inject("portalCapabilities", ref({}));
const canManage = computed(() => (portalCapabilities.value?.manageable_project_names || []).includes(props.name));
const canShareFolder = computed(
	() =>
		!isCustomerPortalUser.value &&
		(portalCapabilities.value?.allowed_project_names || []).includes(props.name),
);
const canLinkCustomer = computed(() => canManage.value && !!portalCapabilities.value?.can_manage_customers);
const isCustomerPortalUser = computed(() => !!portalCapabilities.value?.is_customer_portal_user);
const sessionUser = computed(() => portalCapabilities.value?.portal_user || "");

function canDeleteFileOnDetail(f) {
	if (!f || f.is_folder || isCustomerPortalUser.value) return false;
	if (canManage.value) return true;
	return !!sessionUser.value && f.owner === sessionUser.value;
}

const teamList = ref([]);
/** Linked customer portal users from API: { name, full_name, email } */
const customerPortalUsers = ref([]);
const cpSearchQ = ref("");
const cpHits = ref([]);
let cpSearchTimer;
const cpSaving = ref(false);
const cpMessage = ref("");
const cpError = ref("");
const showInviteCustomerUser = ref(false);
const inviteEmail = ref("");
const inviteFullName = ref("");
const invitePassword = ref("");
const inviteBusy = ref(false);
const customerDisplayName = ref("");
const customerSearchQ = ref("");
const customerHits = ref([]);
let customerSearchTimer;
const manualCustomerId = ref("");
const customerBusy = ref(false);
const customerMsg = ref("");
const customerErr = ref("");
const showNewCustomer = ref(false);
const newCustomerName = ref("");
const newCustomerBusy = ref(false);
const teamSaving = ref(false);
const teamMessage = ref("");
const teamError = ref("");

const projectTitleDraft = ref("");
const titleSaving = ref(false);
const titleError = ref("");
const titleOk = ref("");

const searchQ = ref("");
const searchHits = ref([]);
let searchTimer;

const files = ref([]);
const folders = ref([]);
const projectRootPath = ref("");
const filesLoading = ref(false);
const fileDeleteError = ref("");
const deleteBusyName = ref("");

// Share button on the upload panel just hops over to the Files hub for that folder,
// where the full Drive-style Share modal lives. Keeps ProjectDetail focused.
function onOpenShareFromPanel(folderPath) {
	router.push({
		path: "/files",
		query: { project: props.name, folder: folderPath, share: "1" },
	});
}

const project = computed(() => payload.value?.project);
const tasks = computed(() => payload.value?.tasks || []);
const kanbanStage = computed(() => payload.value?.kanban_stage || "—");
const hasProjectCustomer = computed(() => !!(project.value?.customer));
const customerPortalUserIds = computed(() => new Set(customerPortalUsers.value.map((u) => u.name)));

function rememberProject(p) {
	try {
		const key = "portal_recent_projects";
		const list = JSON.parse(localStorage.getItem(key) || "[]");
		const entry = { name: p.name, project_name: p.project_name || p.name };
		const next = [entry, ...list.filter((x) => x.name !== p.name)].slice(0, 8);
		localStorage.setItem(key, JSON.stringify(next));
	} catch {
		/* ignore */
	}
}

async function loadDashboard() {
	loading.value = true;
	try {
		payload.value = await call({
			method: "portal_app.api.projects.project_dashboard",
			args: { name: props.name },
		});
		const p = payload.value?.project;
		customerDisplayName.value = payload.value?.customer_display_name || "";
		if (p) {
			rememberProject(p);
			teamList.value = (p.users || []).map((row) => row.user).filter(Boolean);
		}
		await loadCustomerPortalUsers();
	} catch (e) {
		console.error(e);
	} finally {
		loading.value = false;
	}
}

async function loadCustomerPortalUsers() {
	if (!canManage.value || !project.value?.customer) {
		customerPortalUsers.value = [];
		return;
	}
	try {
		const res = await call({
			method: "portal_app.api.projects.get_customer_portal_users",
			args: { project: props.name },
		});
		customerPortalUsers.value = res.users || [];
	} catch (e) {
		console.error(e);
		customerPortalUsers.value = [];
	}
}

async function loadFiles() {
	filesLoading.value = true;
	fileDeleteError.value = "";
	try {
		const res = await call({
			method: "portal_app.api.files.list_project_files",
			args: { project: props.name },
		});
		files.value = res.files || [];
		folders.value = res.folders?.subfolders || [];
		projectRootPath.value = res.folders?.project_root || "";
	} catch (e) {
		console.error(e);
	} finally {
		filesLoading.value = false;
	}
}

async function deleteProjectFile(f) {
	if (!f?.name || f.is_folder || !canDeleteFileOnDetail(f)) return;
	fileDeleteError.value = "";
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
		fileDeleteError.value = apiErr(e);
	} finally {
		deleteBusyName.value = "";
	}
}

onMounted(async () => {
	await loadDashboard();
	await loadFiles();
});

watch(
	() => props.name,
	async () => {
		await loadDashboard();
		await loadFiles();
	},
);

watch(
	() => project.value?.project_name,
	(n) => {
		if (typeof n === "string") projectTitleDraft.value = n;
	},
	{ immediate: true },
);

async function runCustomerSearch(q) {
	if (!canLinkCustomer.value) {
		customerHits.value = [];
		return;
	}
	try {
		customerHits.value = await call({
			method: "portal_app.api.projects.search_customers",
			args: { txt: (q || "").trim() },
		});
	} catch (e) {
		console.error(e);
		customerHits.value = [];
	}
}
watch(customerSearchQ, (q) => {
	clearTimeout(customerSearchTimer);
	customerSearchTimer = setTimeout(() => runCustomerSearch(q), 200);
});
function onCustomerFocus() {
	if (!customerHits.value.length) runCustomerSearch(customerSearchQ.value);
}

async function runCpSearch(q) {
	if (!canManage.value || !project.value?.customer) {
		cpHits.value = [];
		return;
	}
	try {
		cpHits.value = await call({
			method: "portal_app.api.projects.search_portal_users",
			args: { txt: (q || "").trim() },
		});
	} catch (e) {
		console.error(e);
		cpHits.value = [];
	}
}
watch(cpSearchQ, (q) => {
	clearTimeout(cpSearchTimer);
	cpSearchTimer = setTimeout(() => runCpSearch(q), 200);
});
function onCpFocus() {
	if (!cpHits.value.length) runCpSearch(cpSearchQ.value);
}

watch(searchQ, (q) => {
	clearTimeout(searchTimer);
	searchTimer = setTimeout(() => runUserSearch(q), 200);
});

function addTeamUser(u) {
	if (!u || teamList.value.includes(u)) return;
	teamList.value = [...teamList.value, u];
	searchQ.value = "";
	searchHits.value = [];
}

function removeTeamUser(u) {
	teamList.value = teamList.value.filter((x) => x !== u);
}

// Refs on each picker wrapper so we can detect clicks outside and close the dropdown.
const teamPickerRef = ref(null);
const customerPickerRef = ref(null);
const cpPickerRef = ref(null);

function onSearchFocus() {
	const q = (searchQ.value || "").trim();
	if (!searchHits.value.length) {
		// Mirror customer/cp behaviour — pop existing matches on focus, even with empty q.
		runUserSearch(q);
	}
}

async function runUserSearch(q) {
	try {
		searchHits.value = await call({
			method: "portal_app.api.projects.search_portal_users",
			args: { txt: (q || "").trim() },
		});
	} catch (e) {
		console.error(e);
		searchHits.value = [];
	}
}

/** Enter key on the team-search input: pick the top hit, add to team, save immediately. */
async function onTeamSearchEnter() {
	const top = (searchHits.value || []).find((h) => !teamList.value.includes(h.name));
	if (top) {
		addTeamUser(top.name);
		await saveTeam();
		return;
	}
	// No usable suggestion — if there's at least one user typed, just save current list.
	if (teamList.value.length) {
		await saveTeam();
	}
}

function onDocClickClosePickers(e) {
	const t = e.target;
	if (teamPickerRef.value && !teamPickerRef.value.contains(t)) {
		searchHits.value = [];
	}
	if (customerPickerRef.value && !customerPickerRef.value.contains(t)) {
		customerHits.value = [];
	}
	if (cpPickerRef.value && !cpPickerRef.value.contains(t)) {
		cpHits.value = [];
	}
}

onMounted(() => document.addEventListener("click", onDocClickClosePickers));
onBeforeUnmount(() => document.removeEventListener("click", onDocClickClosePickers));

async function syncCustomerPortalUserIds(userIds) {
	cpSaving.value = true;
	cpMessage.value = "";
	cpError.value = "";
	try {
		await call({
			method: "portal_app.api.projects.sync_customer_portal_users",
			type: "POST",
			args: { project: props.name, users: JSON.stringify(userIds) },
		});
		cpMessage.value = "Saved.";
		await loadCustomerPortalUsers();
		window.setTimeout(() => {
			cpMessage.value = "";
		}, 2500);
	} catch (e) {
		cpError.value = apiErr(e);
	} finally {
		cpSaving.value = false;
	}
}

async function addCustomerPortalUserImmediate(userId) {
	if (!userId || customerPortalUserIds.value.has(userId) || cpSaving.value) return;
	const next = [...customerPortalUsers.value.map((u) => u.name), userId];
	cpSearchQ.value = "";
	cpHits.value = [];
	await syncCustomerPortalUserIds(next);
}

async function removeCustomerPortalUserImmediate(userId) {
	if (!userId || cpSaving.value) return;
	const next = customerPortalUsers.value.map((u) => u.name).filter((x) => x !== userId);
	await syncCustomerPortalUserIds(next);
}

async function submitInviteCustomerUser() {
	if (!inviteEmail.value.trim() || !inviteFullName.value.trim() || invitePassword.value.length < 6) {
		cpError.value = "Email, name, and password (min 6) are required.";
		return;
	}
	inviteBusy.value = true;
	cpError.value = "";
	try {
		await call({
			method: "portal_app.api.projects.create_customer_portal_user_from_project",
			type: "POST",
			args: {
				project: props.name,
				email: inviteEmail.value.trim(),
				full_name: inviteFullName.value.trim(),
				password: invitePassword.value,
			},
		});
		showInviteCustomerUser.value = false;
		inviteEmail.value = "";
		inviteFullName.value = "";
		invitePassword.value = "";
		cpMessage.value = "User created and linked to this project’s customer.";
		await loadCustomerPortalUsers();
	} catch (e) {
		cpError.value = apiErr(e);
	} finally {
		inviteBusy.value = false;
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

async function saveTeam() {
	teamSaving.value = true;
	teamMessage.value = "";
	teamError.value = "";
	try {
		await call({
			method: "portal_app.api.projects.sync_project_team",
			type: "POST",
			args: { project: props.name, users: JSON.stringify(teamList.value) },
		});
		teamMessage.value = "Team updated.";
		await loadDashboard();
	} catch (e) {
		teamError.value = apiErr(e);
	} finally {
		teamSaving.value = false;
	}
}

async function saveProjectTitle() {
	const t = projectTitleDraft.value.trim();
	if (t.length < 2) {
		titleError.value = "Enter a title of at least 2 characters.";
		return;
	}
	titleSaving.value = true;
	titleError.value = "";
	titleOk.value = "";
	try {
		await call({
			method: "portal_app.api.projects.rename_project",
			type: "POST",
			args: { project: props.name, project_name: t },
		});
		titleOk.value = "Title saved.";
		await loadDashboard();
		window.setTimeout(() => {
			titleOk.value = "";
		}, 2500);
	} catch (e) {
		titleError.value = apiErr(e);
	} finally {
		titleSaving.value = false;
	}
}

async function linkCustomer(customerId) {
	if (!customerId) return;
	customerBusy.value = true;
	customerMsg.value = "";
	customerErr.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.set_project_customer",
			type: "POST",
			args: { project: props.name, customer: customerId },
		});
		customerDisplayName.value = res.customer_display_name || "";
		customerSearchQ.value = "";
		customerHits.value = [];
		customerMsg.value = "Customer linked.";
		await loadDashboard();
		await loadCustomerPortalUsers();
	} catch (e) {
		customerErr.value = apiErr(e);
	} finally {
		customerBusy.value = false;
	}
}

async function clearCustomer() {
	customerBusy.value = true;
	customerMsg.value = "";
	customerErr.value = "";
	try {
		await call({
			method: "portal_app.api.projects.set_project_customer",
			type: "POST",
			args: { project: props.name, customer: "" },
		});
		customerDisplayName.value = "";
		customerMsg.value = "Customer cleared.";
		await loadDashboard();
	} catch (e) {
		customerErr.value = apiErr(e);
	} finally {
		customerBusy.value = false;
	}
}

async function applyManualCustomer() {
	const id = manualCustomerId.value.trim();
	if (!id) return;
	await linkCustomer(id);
	manualCustomerId.value = "";
}

async function submitNewCustomer() {
	const n = newCustomerName.value.trim();
	if (n.length < 2) {
		customerErr.value = "Enter a customer name.";
		return;
	}
	newCustomerBusy.value = true;
	customerErr.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.create_or_get_customer",
			type: "POST",
			args: { customer_name: n },
		});
		showNewCustomer.value = false;
		newCustomerName.value = "";
		await linkCustomer(res.name);
	} catch (e) {
		customerErr.value = apiErr(e);
	} finally {
		newCustomerBusy.value = false;
	}
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-6xl space-y-6">
			<button
				type="button"
				class="inline-flex items-center gap-1.5 text-sm font-medium text-[color:var(--portal-muted)] transition hover:text-[color:var(--portal-text)]"
				@click="router.push('/projects')"
			>
				<FeatherIcon name="arrow-left" class="h-4 w-4" />
				Back to projects
			</button>

			<div v-if="loading" class="flex items-center gap-2 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading…
			</div>

			<template v-else-if="project">
				<!-- Hero -->
				<div class="portal-hero portal-anim-in">
					<div class="relative flex flex-wrap items-start justify-between gap-4">
						<div class="min-w-0 flex-1">
							<div class="flex flex-wrap items-center gap-2">
								<span class="portal-pill portal-pill-accent">
									<FeatherIcon name="folder" class="h-3 w-3" />
									Project
								</span>
								<span v-if="project.status" class="portal-pill portal-pill-muted">{{ project.status }}</span>
								<span v-if="kanbanStage && kanbanStage !== '—'" class="portal-pill portal-pill-muted">
									<FeatherIcon name="trello" class="h-3 w-3" />
									{{ kanbanStage }}
								</span>
							</div>
							<h1 class="mt-2 truncate text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
								{{ project.project_name }}
							</h1>
							<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
								<span class="font-mono">{{ project.name }}</span>
							</p>
						</div>
						<div class="flex shrink-0 flex-wrap items-center gap-2">
							<button
								type="button"
								class="portal-btn"
								@click="router.push({ path: '/files', query: { project: project.name } })"
							>
								<FeatherIcon name="paperclip" class="h-4 w-4" />
								Files
							</button>
							<button
								type="button"
								class="portal-btn"
								@click="router.push({ path: '/tasks', query: { project: project.name } })"
							>
								<FeatherIcon name="check-square" class="h-4 w-4" />
								Tasks
							</button>
						</div>
					</div>

					<div v-if="canManage" class="mt-5 rounded-xl border border-[color:var(--portal-border)] bg-white/70 p-3 backdrop-blur">
						<p class="portal-section-title">Rename project</p>
						<div class="mt-2 flex flex-wrap items-center gap-2">
							<TextInput v-model="projectTitleDraft" class="max-w-xl flex-1 rounded-xl" />
							<Button
								variant="solid"
								class="rounded-xl bg-black text-white"
								:loading="titleSaving"
								@click="saveProjectTitle"
							>
								Save title
							</Button>
						</div>
						<p v-if="titleError" class="mt-2 text-sm text-red-600">{{ titleError }}</p>
						<p v-if="titleOk" class="mt-2 text-sm text-green-700">{{ titleOk }}</p>
					</div>
				</div>

				<!-- KPI grid -->
				<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="activity" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Status</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">{{ project.status || "—" }}</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="trello" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Kanban stage</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">{{ kanbanStage }}</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="user" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Client</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">
								{{ customerDisplayName || project.customer || "—" }}
							</p>
							<p v-if="project.customer" class="truncate text-xs text-[color:var(--portal-subtle)]">{{ project.customer }}</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="calendar" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Timeline</p>
							<p class="mt-1 text-sm text-[color:var(--portal-text)]">
								{{ project.expected_start_date || "—" }}
								<span class="mx-1 text-[color:var(--portal-subtle)]">→</span>
								{{ project.expected_end_date || "—" }}
							</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="dollar-sign" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Estimated cost</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">
								{{ project.estimated_costing ?? "—" }}
							</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="bar-chart-2" class="h-4 w-4" /></div>
						<div class="min-w-0 flex-1">
							<p class="portal-section-title">Progress</p>
							<div class="mt-1 flex items-center gap-2">
								<p class="text-base font-semibold text-[color:var(--portal-text)]">{{ project.percent_complete ?? 0 }}%</p>
							</div>
							<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--portal-bg-dim)]">
								<div
									class="h-full rounded-full transition-all"
									:style="{
										width: Math.min(100, Math.max(0, Number(project.percent_complete) || 0)) + '%',
										background: 'linear-gradient(90deg, #4f46e5, #38bdf8)',
									}"
								></div>
							</div>
						</div>
					</div>
				</div>

				<div class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="user" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Customer (ERPNext)
						</h2>
					</div>
					<p class="mb-3 text-sm text-gray-600">
						Links this project to a <strong>Customer</strong> record. Customer portal users only see projects for their linked customer.
					</p>
					<div v-if="canManage" class="space-y-3">
						<template v-if="canLinkCustomer">
							<label class="text-xs font-medium text-gray-600">Search customers</label>
							<div ref="customerPickerRef" class="space-y-2" @focusin="onCustomerFocus">
								<TextInput
									v-model="customerSearchQ"
									class="w-full rounded-xl"
									placeholder="Click to see existing customers, or type to filter…"
								/>
								<div
									v-if="customerHits.length"
									class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
								>
									<button
										v-for="c in customerHits"
										:key="c.name"
										type="button"
										class="flex w-full flex-col gap-0.5 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white"
										@click="linkCustomer(c.name)"
									>
										<span class="font-medium text-gray-900">{{ c.customer_name || c.name }}</span>
										<span class="text-xs text-gray-500">{{ c.name }}</span>
									</button>
								</div>
							</div>
							<div class="flex flex-wrap gap-2">
								<button
									type="button"
									class="rounded-xl border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-50"
									@click="showNewCustomer = true"
								>
									Create customer (no duplicate name)
								</button>
								<button
									v-if="project.customer"
									type="button"
									class="rounded-xl border border-red-200 px-3 py-2 text-sm text-red-700 hover:bg-red-50"
									:disabled="customerBusy"
									@click="clearCustomer"
								>
									Clear customer
								</button>
							</div>
						</template>
						<template v-else>
							<label class="text-xs font-medium text-gray-600">Customer ID (from Desk)</label>
							<div class="flex flex-wrap gap-2">
								<TextInput v-model="manualCustomerId" class="min-w-[200px] flex-1 rounded-xl" placeholder="e.g. CUST-00001" />
								<Button
									variant="solid"
									class="rounded-xl bg-black text-white"
									:loading="customerBusy"
									@click="applyManualCustomer"
								>
									Link
								</Button>
								<button
									v-if="project.customer"
									type="button"
									class="rounded-xl border border-red-200 px-3 py-2 text-sm text-red-700"
									:disabled="customerBusy"
									@click="clearCustomer"
								>
									Clear
								</button>
							</div>
						</template>
						<p v-if="customerMsg" class="text-sm text-green-700">{{ customerMsg }}</p>
						<p v-if="customerErr" class="text-sm text-red-600">{{ customerErr }}</p>
					</div>
					<p v-else class="text-sm text-gray-500">You can view the customer link; only project managers can change it.</p>
				</div>

				<div class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="users" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Team
						</h2>
						<span v-if="!canManage" class="text-xs text-[color:var(--portal-muted)]">View only — ask a project manager to change membership.</span>
					</div>
					<div v-if="canManage" ref="teamPickerRef" class="mb-4 space-y-2">
						<label class="text-xs font-medium text-gray-600">Add user (search by email, username, or full name)</label>
						<div @focusin="onSearchFocus">
							<TextInput
								v-model="searchQ"
								class="w-full rounded-xl"
								placeholder="Click to see existing users, type to filter, press Enter to add + save"
								@keyup.enter="onTeamSearchEnter"
							/>
						</div>
						<div
							v-if="searchHits.length"
							class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
						>
							<button
								v-for="h in searchHits"
								:key="h.name"
								type="button"
								class="flex w-full items-center justify-between gap-2 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
								:disabled="teamList.includes(h.name)"
								@click="addTeamUser(h.name)"
							>
								<span class="min-w-0 flex-1 truncate">
									<span class="font-medium text-gray-900">{{ h.full_name || h.name }}</span>
									<span class="ml-2 text-xs text-gray-500">{{ h.email || h.name }}</span>
								</span>
								<span v-if="teamList.includes(h.name)" class="text-xs text-gray-400">on team</span>
							</button>
						</div>
					</div>
					<ul class="divide-y rounded-xl border border-gray-100 text-sm">
						<li v-for="u in teamList" :key="u" class="flex items-center justify-between gap-2 py-2 px-3">
							<span>{{ u }}</span>
							<button
								v-if="canManage"
								type="button"
								class="text-xs text-red-600 hover:underline"
								@click="removeTeamUser(u)"
							>
								Remove
							</button>
						</li>
						<li v-if="!teamList.length" class="py-4 px-3 text-gray-500">No users on this project yet.</li>
					</ul>
					<div v-if="canManage" class="mt-3 flex flex-wrap items-center gap-3">
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="teamSaving" @click="saveTeam">
							Save team
						</Button>
						<p v-if="teamMessage" class="text-sm text-green-700">{{ teamMessage }}</p>
						<p v-if="teamError" class="text-sm text-red-600">{{ teamError }}</p>
					</div>
				</div>

				<div
					v-if="canManage && hasProjectCustomer"
					class="portal-card-strong p-5"
				>
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="user-plus" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Customer portal users
						</h2>
						<Button
							type="button"
							variant="outline"
							size="sm"
							@click="
								cpError = '';
								showInviteCustomerUser = true
							"
						>
							Invite new user
						</Button>
					</div>
					<p class="mb-3 text-sm text-gray-600">
						One ERPNext <strong>Customer</strong> can have <strong>many</strong> portal logins. Everyone here shares
						that customer link, gets the Portal Customer role, and sees the same customer’s projects. Use
						<strong>Remove from portal</strong> to unlink them from this customer (they lose customer portal access
						for that customer).
					</p>

					<p class="mb-2 text-xs font-medium uppercase text-gray-500">People with access</p>
					<ul class="mb-4 divide-y rounded-xl border border-gray-200 bg-white text-sm">
						<li
							v-for="u in customerPortalUsers"
							:key="u.name"
							class="flex flex-wrap items-center justify-between gap-3 py-3 px-4"
						>
							<div class="min-w-0 flex-1">
								<p class="font-medium text-gray-900">{{ u.full_name || u.name }}</p>
								<p class="truncate text-xs text-gray-500">{{ u.email || u.name }}</p>
							</div>
							<button
								type="button"
								class="shrink-0 rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
								:disabled="cpSaving"
								@click="removeCustomerPortalUserImmediate(u.name)"
							>
								Remove from portal
							</button>
						</li>
						<li
							v-if="!customerPortalUsers.length"
							class="py-8 px-4 text-center text-sm text-gray-500"
						>
							No customer portal users yet. Search below to add someone, or use Invite new user.
						</li>
					</ul>

					<p class="mb-2 text-xs font-medium uppercase text-gray-500">Add existing user</p>
					<label class="mb-2 block text-xs text-gray-600">Search by email, username, or full name — they are added as soon as you choose one.</label>
					<div ref="cpPickerRef" class="mb-3 space-y-2" @focusin="onCpFocus">
						<TextInput
							v-model="cpSearchQ"
							class="w-full rounded-xl"
							placeholder="Click to see existing portal users, or type to filter…"
							:disabled="cpSaving"
						/>
						<div
							v-if="cpHits.length"
							class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
						>
							<button
								v-for="u in cpHits"
								:key="u.name"
								type="button"
								class="flex w-full items-center justify-between gap-2 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
								:disabled="cpSaving || customerPortalUserIds.has(u.name)"
								@click="addCustomerPortalUserImmediate(u.name)"
							>
								<span class="min-w-0">
									<span class="font-medium text-gray-900">{{ u.full_name || u.name }}</span>
									<span class="mt-0.5 block truncate text-xs text-gray-500">{{ u.email || u.name }}</span>
								</span>
								<span v-if="customerPortalUserIds.has(u.name)" class="shrink-0 text-xs text-gray-400">Added</span>
								<span v-else class="shrink-0 text-xs font-medium text-blue-600">Add</span>
							</button>
						</div>
					</div>
					<p v-if="cpSaving" class="mb-2 text-sm text-gray-600">Updating…</p>
					<p v-if="cpMessage" class="text-sm text-green-700">{{ cpMessage }}</p>
					<p v-if="cpError" class="text-sm text-red-600">{{ cpError }}</p>
				</div>

				<div class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="paperclip" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Files
						</h2>
						<button
							type="button"
							class="portal-btn portal-btn-ghost"
							@click="router.push({ path: '/files', query: { project: project.name } })"
						>
							Open in Files hub
							<FeatherIcon name="arrow-up-right" class="h-3.5 w-3.5" />
						</button>
					</div>
					<FileUploadPanel
						v-if="!isCustomerPortalUser"
						:project="project?.name || props.name"
						:folders="folders"
						:project-root-path="projectRootPath"
						:allow-share="canShareFolder"
						class="mb-4"
						@uploaded="loadFiles"
						@open-share="onOpenShareFromPanel"
					/>
					<p v-else class="mb-4 text-sm text-[color:var(--portal-muted)]">Customer portal access is view-only for files.</p>
					<p v-if="fileDeleteError" class="mb-2 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-800">
						{{ fileDeleteError }}
					</p>
					<div v-if="filesLoading" class="text-sm text-[color:var(--portal-muted)]">Loading files…</div>
					<ul v-else class="divide-y divide-[color:var(--portal-border)] text-sm">
						<li v-for="f in files" :key="f.name" class="flex flex-wrap items-center justify-between gap-2 py-2.5">
							<span class="min-w-0 break-words text-[color:var(--portal-text)]">
								<FeatherIcon name="file" class="mr-1.5 inline h-3.5 w-3.5 text-[color:var(--portal-muted)]" />
								{{ f.file_name }}
								<span v-if="f.is_private" class="portal-pill portal-pill-muted ml-1.5">private</span>
							</span>
							<div class="flex shrink-0 flex-wrap items-center gap-2">
								<a
									v-if="f.file_url"
									:href="f.file_url"
									target="_blank"
									rel="noopener"
									class="text-[color:var(--portal-accent)] hover:underline"
								>
									Open
								</a>
								<button
									v-if="canDeleteFileOnDetail(f)"
									type="button"
									class="text-xs font-medium text-red-700 hover:underline disabled:opacity-50"
									:disabled="!!deleteBusyName"
									@click="deleteProjectFile(f)"
								>
									{{ deleteBusyName === f.name ? "Deleting…" : "Delete" }}
								</button>
							</div>
						</li>
						<li v-if="!files.length" class="py-4 text-center text-[color:var(--portal-muted)]">No files yet.</li>
					</ul>
				</div>

				<div class="portal-card-strong p-5">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="check-square" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Tasks
						</h2>
						<button
							type="button"
							class="portal-btn portal-btn-ghost"
							@click="router.push({ path: '/tasks', query: { project: project.name } })"
						>
							Open task workspace
							<FeatherIcon name="arrow-up-right" class="h-3.5 w-3.5" />
						</button>
					</div>
					<div class="space-y-2">
						<div
							v-for="t in tasks"
							:key="t.name"
							class="rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2.5 shadow-sm transition hover:border-[color:var(--portal-border-strong)] hover:shadow-md"
						>
							<div class="flex flex-wrap items-center justify-between gap-2">
								<p class="font-medium text-[color:var(--portal-text)]">{{ t.subject }}</p>
								<span class="portal-pill portal-pill-muted">{{ t.status }}</span>
							</div>
							<p class="mt-1 text-xs font-mono text-[color:var(--portal-subtle)]">{{ t.name }}</p>
						</div>
						<div v-if="!tasks.length" class="rounded-xl border border-dashed border-gray-300 bg-white py-6 text-center text-gray-500">
							No tasks linked.
						</div>
					</div>
				</div>
			</template>
		</div>

		<Teleport to="body">
			<div
				v-if="showNewCustomer"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showNewCustomer = false"></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border bg-white p-6 shadow-2xl">
					<h3 class="text-lg font-semibold text-gray-900">New customer</h3>
					<p class="mt-1 text-sm text-gray-600">
						If the name already exists (same spelling), the existing customer is linked—nothing is duplicated.
					</p>
					<label class="mt-4 block text-xs font-medium text-gray-600">Customer name</label>
					<TextInput v-model="newCustomerName" class="mt-1 w-full rounded-xl" placeholder="Legal or trading name" />
					<div class="mt-4 flex justify-end gap-2">
						<button type="button" class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" @click="showNewCustomer = false">
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="newCustomerBusy" @click="submitNewCustomer">
							Create or link
						</Button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="showInviteCustomerUser"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div
					class="absolute inset-0 bg-black/40 backdrop-blur-sm"
					@click="showInviteCustomerUser = false"
				></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border bg-white p-6 shadow-2xl">
					<h3 class="text-lg font-semibold text-gray-900">Invite customer portal user</h3>
					<p class="mt-1 text-sm text-gray-600">
						Creates a user with the Portal Customer role linked to this project’s customer. If the email already
						exists, that user is linked when allowed.
					</p>
					<div class="mt-4 space-y-3">
						<div>
							<label class="mb-1 block text-xs font-medium text-gray-600">Email (username)</label>
							<TextInput v-model="inviteEmail" type="email" class="w-full rounded-xl" placeholder="name@company.com" />
						</div>
						<div>
							<label class="mb-1 block text-xs font-medium text-gray-600">Full name</label>
							<TextInput v-model="inviteFullName" class="w-full rounded-xl" />
						</div>
						<div>
							<label class="mb-1 block text-xs font-medium text-gray-600">Password (min 6)</label>
							<Password v-model="invitePassword" class="w-full rounded-xl" />
						</div>
					</div>
					<p v-if="cpError" class="mt-3 text-sm text-red-600">{{ cpError }}</p>
					<div class="mt-4 flex justify-end gap-2">
						<button
							type="button"
							class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
							@click="showInviteCustomerUser = false"
						>
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="inviteBusy" @click="submitInviteCustomerUser">
							Create &amp; link
						</Button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
