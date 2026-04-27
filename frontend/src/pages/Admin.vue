<script setup>
import { ref, onMounted, computed } from "vue";
import { call } from "@/api";
import { Button, TextInput, Password, FeatherIcon } from "frappe-ui";

const caps = ref({ can_create_users: false, can_run_demo_seed: false });
const loadingCaps = ref(true);

const email = ref("");
const fullName = ref("");
const password = ref("");
const roleProjectsUser = ref(true);
const roleProjectsManager = ref(false);
const rolePortalCustomer = ref(false);
const portalLinkedCustomer = ref("");
const sendWelcome = ref(false);
const userBusy = ref(false);
const userMsg = ref("");
const userErr = ref("");

// New tracked seed runs
const seedRuns = ref([]);
const seedRunsLoading = ref(false);
const seedRunBusy = ref(false);
const seedRunErr = ref("");
const seedRunMsg = ref("");
const newRunLabel = ref("Portal demo run");
const newRunOpts = ref({
	include_users: true,
	include_customers: true,
	include_projects: true,
	include_tasks: true,
	include_files: true,
});
const cleanupBusyName = ref("");

const canShow = computed(() => caps.value.can_create_users || caps.value.can_run_demo_seed);

onMounted(async () => {
	try {
		caps.value = await call({
			method: "portal_app.api.portal_admin.get_portal_admin_capabilities",
		});
	} catch (e) {
		console.error(e);
	} finally {
		loadingCaps.value = false;
	}
	if (caps.value.can_run_demo_seed) {
		await loadSeedRuns();
	}
});

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

async function createUser() {
	userMsg.value = "";
	userErr.value = "";
	const roles = [];
	if (roleProjectsUser.value) roles.push("Projects User");
	if (roleProjectsManager.value) roles.push("Projects Manager");
	if (rolePortalCustomer.value) roles.push("Portal Customer");
	if (!roles.length) {
		userErr.value = "Select at least one role.";
		return;
	}
	if (rolePortalCustomer.value && !portalLinkedCustomer.value.trim()) {
		userErr.value = "Portal Customer requires the Customer ID (link field).";
		return;
	}
	userBusy.value = true;
	try {
		await call({
			method: "portal_app.api.portal_admin.create_portal_user",
			type: "POST",
			args: {
				email: email.value.trim(),
				full_name: fullName.value.trim(),
				password: password.value,
				roles_json: JSON.stringify(roles),
				send_welcome_email: sendWelcome.value ? 1 : 0,
				portal_linked_customer: portalLinkedCustomer.value.trim() || undefined,
			},
		});
		userMsg.value = "User created.";
		email.value = "";
		fullName.value = "";
		password.value = "";
		portalLinkedCustomer.value = "";
		rolePortalCustomer.value = false;
	} catch (e) {
		userErr.value = apiErr(e);
	} finally {
		userBusy.value = false;
	}
}

async function loadSeedRuns() {
	seedRunsLoading.value = true;
	seedRunErr.value = "";
	try {
		const res = await call({ method: "portal_app.api.portal_admin.list_demo_seed_runs" });
		seedRuns.value = res?.runs || [];
	} catch (e) {
		seedRunErr.value = apiErr(e);
		seedRuns.value = [];
	} finally {
		seedRunsLoading.value = false;
	}
}

async function createSeedRun() {
	if (
		!confirm(
			"Create a new demo seed run?\n\nThis adds the demo users, customers, projects, tasks, and sample file. " +
				"They are tracked under this run and can be wiped with one click later.",
		)
	) {
		return;
	}
	seedRunBusy.value = true;
	seedRunErr.value = "";
	seedRunMsg.value = "";
	try {
		const res = await call({
			method: "portal_app.api.portal_admin.create_demo_seed_run",
			type: "POST",
			args: {
				run_label: newRunLabel.value || "Portal demo run",
				include_users: newRunOpts.value.include_users ? 1 : 0,
				include_customers: newRunOpts.value.include_customers ? 1 : 0,
				include_projects: newRunOpts.value.include_projects ? 1 : 0,
				include_tasks: newRunOpts.value.include_tasks ? 1 : 0,
				include_files: newRunOpts.value.include_files ? 1 : 0,
			},
		});
		const c = res?.counts || {};
		seedRunMsg.value = `Run ${res?.name || ""} created — ${c.projects || 0} projects · ${c.users || 0} users · ${c.tasks || 0} tasks.`;
		await loadSeedRuns();
		setTimeout(() => (seedRunMsg.value = ""), 5000);
	} catch (e) {
		seedRunErr.value = apiErr(e);
	} finally {
		seedRunBusy.value = false;
	}
}

async function deleteSeedRun(name) {
	if (
		!confirm(
			`Delete seed run “${name}”?\n\nThis will permanently remove every record this run created (users, customers, projects, tasks, files).` +
				" Records that pre-existed before the run are preserved.",
		)
	) {
		return;
	}
	cleanupBusyName.value = name;
	seedRunErr.value = "";
	seedRunMsg.value = "";
	try {
		await call({
			method: "portal_app.api.portal_admin.delete_demo_seed_run",
			type: "POST",
			args: { name },
		});
		seedRunMsg.value = `Run ${name} cleaned up.`;
		await loadSeedRuns();
		setTimeout(() => (seedRunMsg.value = ""), 4000);
	} catch (e) {
		seedRunErr.value = apiErr(e);
	} finally {
		cleanupBusyName.value = "";
	}
}

function fmtDate(s) {
	if (!s) return "—";
	const d = new Date(String(s).replace(" ", "T"));
	if (Number.isNaN(d.getTime())) return s;
	return d.toLocaleString();
}

function statusPillClass(s) {
	const t = String(s || "").toLowerCase();
	if (t === "active") return "portal-pill-success";
	if (t === "cleaned") return "portal-pill-muted";
	if (t === "failed") return "portal-pill-danger";
	return "portal-pill-muted";
}

const totalCreated = computed(() =>
	seedRuns.value.reduce((sum, r) => {
		const c = r.counts || {};
		return sum + (c.users || 0) + (c.customers || 0) + (c.projects || 0) + (c.tasks || 0) + (c.files || 0);
	}, 0),
);
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-4xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative">
					<span class="portal-pill portal-pill-accent">
						<FeatherIcon name="shield" class="h-3 w-3" />
						Admin
					</span>
					<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
						Portal administration
					</h1>
					<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
						Onboard new portal users and manage the demo dataset (Auditor / System Manager only).
					</p>
				</div>
			</div>

			<div v-if="loadingCaps" class="portal-card-strong flex items-center justify-center gap-2 p-10 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading…
			</div>

			<div
				v-else-if="!canShow"
				class="portal-card-strong p-6 text-center"
			>
				<div
					class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl text-white"
					style="background: linear-gradient(135deg, #f87171 0%, #fb923c 100%);"
				>
					<FeatherIcon name="lock" class="h-5 w-5" />
				</div>
				<h2 class="text-base font-semibold text-[color:var(--portal-text)]">Restricted page</h2>
				<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
					Available to users who can create Users in ERPNext, or System Managers who may run the demo seed (when enabled).
				</p>
			</div>

			<template v-else>
				<!-- Create user -->
				<div v-if="caps.can_create_users" class="portal-card-strong space-y-4 p-5">
					<div class="flex items-center gap-2">
						<div
							class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
							style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
						>
							<FeatherIcon name="user-plus" class="h-4 w-4" />
						</div>
						<div>
							<h2 class="text-base font-semibold text-[color:var(--portal-text)]">Create portal user</h2>
							<p class="text-xs text-[color:var(--portal-muted)]">
								Creates a System User with portal roles. For full HR setup, use Desk → User.
							</p>
						</div>
					</div>
					<div class="grid gap-3 sm:grid-cols-2">
						<div class="sm:col-span-2">
							<label class="portal-section-title mb-1 block">Email (username)</label>
							<TextInput v-model="email" type="email" class="w-full rounded-xl" placeholder="name@company.com" />
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Full name</label>
							<TextInput v-model="fullName" class="w-full rounded-xl" />
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Password (min 6)</label>
							<Password v-model="password" class="w-full rounded-xl" />
						</div>
					</div>
					<div class="flex flex-wrap gap-2">
						<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-3 py-1.5 text-sm">
							<input v-model="roleProjectsUser" type="checkbox" class="rounded border-gray-300" />
							Projects User
						</label>
						<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-3 py-1.5 text-sm">
							<input v-model="roleProjectsManager" type="checkbox" class="rounded border-gray-300" />
							Projects Manager
						</label>
						<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-3 py-1.5 text-sm">
							<input v-model="rolePortalCustomer" type="checkbox" class="rounded border-gray-300" />
							Portal Customer
						</label>
					</div>
					<div v-if="rolePortalCustomer">
						<label class="portal-section-title mb-1 block">Linked Customer ID</label>
						<TextInput v-model="portalLinkedCustomer" class="w-full rounded-xl" placeholder="e.g. CUST-00001" />
					</div>
					<label class="flex items-center gap-2 text-sm text-[color:var(--portal-text)]">
						<input v-model="sendWelcome" type="checkbox" class="rounded border-gray-300" />
						Send welcome email (if outgoing email is configured)
					</label>
					<p v-if="userMsg" class="text-sm text-green-700">{{ userMsg }}</p>
					<p v-if="userErr" class="text-sm text-red-600">{{ userErr }}</p>
					<Button
						variant="solid"
						class="rounded-xl"
						style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); color: #fff;"
						:loading="userBusy"
						@click="createUser"
					>
						Create user
					</Button>
				</div>

				<!-- Demo seed runs -->
				<div v-if="caps.can_run_demo_seed" class="portal-card-strong space-y-4 p-5">
					<div class="flex flex-wrap items-start justify-between gap-3">
						<div class="flex items-center gap-2">
							<div
								class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
								style="background: linear-gradient(135deg, #db2777 0%, #f472b6 60%, #fde68a 100%);"
							>
								<FeatherIcon name="database" class="h-4 w-4" />
							</div>
							<div>
								<h2 class="text-base font-semibold text-[color:var(--portal-text)]">Demo dataset</h2>
								<p class="text-xs text-[color:var(--portal-muted)]">
									Each <strong>seed run</strong> creates demo users, customers, projects, tasks, and a sample file —
									tracked so you can wipe exactly what it created.
								</p>
							</div>
						</div>
						<button class="portal-btn portal-btn-ghost" :disabled="seedRunsLoading" @click="loadSeedRuns">
							<FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" :class="seedRunsLoading ? 'animate-spin' : ''" />
							Refresh
						</button>
					</div>

					<!-- Create new run -->
					<div class="rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-4">
						<p class="portal-section-title mb-2">Create a new run</p>
						<div class="grid gap-3 sm:grid-cols-2">
							<div class="sm:col-span-2">
								<label class="portal-section-title mb-1 block">Label</label>
								<TextInput v-model="newRunLabel" class="w-full rounded-xl" placeholder="e.g. Demo for Acme review" />
							</div>
						</div>
						<div class="mt-3 flex flex-wrap gap-2">
							<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-sm">
								<input v-model="newRunOpts.include_users" type="checkbox" class="rounded border-gray-300" />
								Users
							</label>
							<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-sm">
								<input v-model="newRunOpts.include_customers" type="checkbox" class="rounded border-gray-300" />
								Customers
							</label>
							<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-sm">
								<input v-model="newRunOpts.include_projects" type="checkbox" class="rounded border-gray-300" />
								Projects
							</label>
							<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-sm">
								<input v-model="newRunOpts.include_tasks" type="checkbox" class="rounded border-gray-300" />
								Tasks
							</label>
							<label class="flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-sm">
								<input v-model="newRunOpts.include_files" type="checkbox" class="rounded border-gray-300" />
								Sample file
							</label>
						</div>
						<div class="mt-4 flex flex-wrap items-center gap-3">
							<button
								class="portal-btn portal-btn-primary"
								:disabled="seedRunBusy"
								@click="createSeedRun"
							>
								<FeatherIcon name="play" class="h-4 w-4" />
								{{ seedRunBusy ? "Running…" : "Run seed" }}
							</button>
							<p v-if="seedRunMsg" class="text-sm text-green-700">{{ seedRunMsg }}</p>
							<p v-if="seedRunErr" class="text-sm text-red-600">{{ seedRunErr }}</p>
						</div>
					</div>

					<!-- Existing runs -->
					<div>
						<div class="mb-2 flex items-center justify-between">
							<p class="portal-section-title">Past runs</p>
							<span class="text-xs text-[color:var(--portal-subtle)]">
								{{ seedRuns.length }} run{{ seedRuns.length === 1 ? "" : "s" }} · {{ totalCreated }} tracked records
							</span>
						</div>
						<div v-if="seedRunsLoading" class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] py-6 text-center text-xs text-[color:var(--portal-muted)]">
							Loading…
						</div>
						<div
							v-else-if="!seedRuns.length"
							class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] py-6 text-center text-sm text-[color:var(--portal-muted)]"
						>
							No seed runs yet. Click <strong>Run seed</strong> above to create one.
						</div>
						<ul v-else class="space-y-2">
							<li
								v-for="r in seedRuns"
								:key="r.name"
								class="flex flex-wrap items-center gap-3 rounded-xl border border-[color:var(--portal-border)] bg-white p-3 transition hover:border-[color:var(--portal-border-strong)]"
							>
								<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white"
									:style="
										r.status === 'Active'
											? 'background: linear-gradient(135deg, #10b981, #38bdf8);'
											: r.status === 'Failed'
												? 'background: linear-gradient(135deg, #ef4444, #f97316);'
												: 'background: linear-gradient(135deg, #6b7280, #9ca3af);'
									"
								>
									<FeatherIcon
										:name="r.status === 'Active' ? 'database' : r.status === 'Failed' ? 'alert-triangle' : 'archive'"
										class="h-4 w-4"
									/>
								</div>
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-semibold text-[color:var(--portal-text)]">
										{{ r.run_label || r.name }}
									</p>
									<p class="truncate text-xs text-[color:var(--portal-muted)]">
										<span class="font-mono">{{ r.name }}</span> · {{ fmtDate(r.run_at) }} · {{ r.run_by || "—" }}
									</p>
									<p class="mt-1 text-[11px] text-[color:var(--portal-muted)]">
										<span class="mr-2">{{ r.counts?.users || 0 }} users</span>
										<span class="mr-2">{{ r.counts?.customers || 0 }} customers</span>
										<span class="mr-2">{{ r.counts?.projects || 0 }} projects</span>
										<span class="mr-2">{{ r.counts?.tasks || 0 }} tasks</span>
										<span>{{ r.counts?.files || 0 }} files</span>
									</p>
								</div>
								<span class="portal-pill" :class="statusPillClass(r.status)">{{ r.status }}</span>
								<button
									class="portal-btn portal-btn-danger text-xs"
									:disabled="!!cleanupBusyName"
									@click="deleteSeedRun(r.name)"
								>
									<FeatherIcon name="trash-2" class="h-3.5 w-3.5" />
									{{ cleanupBusyName === r.name ? "Cleaning…" : "Delete & clean up" }}
								</button>
							</li>
						</ul>
					</div>

					<p class="text-[11px] text-[color:var(--portal-subtle)]">
						Demo password: <code class="rounded bg-[color:var(--portal-bg-dim)] px-1 py-0.5 font-mono">ChangeMe-Demo#1</code>
					</p>
				</div>
			</template>
		</div>
	</div>
</template>
