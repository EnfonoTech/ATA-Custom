<script setup>
import { ref, onMounted, inject, computed } from "vue";
import { call } from "@/api";
import { useRouter } from "vue-router";
import { FeatherIcon } from "frappe-ui";
import SkeletonBlock from "@/component/SkeletonBlock.vue";
import BudgetMeter from "@/component/BudgetMeter.vue";

const router = useRouter();
const loading = ref(true);
const data = ref(null);
const pinned = ref([]);
const loadError = ref("");

const portalCapabilities = inject("portalCapabilities", ref({}));
const canCreate = computed(() => !!portalCapabilities.value?.can_create_project);
const userFullName = computed(() => {
	if (typeof localStorage === "undefined") return "";
	return localStorage.getItem("full_name") || "";
});

const greeting = computed(() => {
	const h = new Date().getHours();
	if (h < 12) return "Good morning";
	if (h < 18) return "Good afternoon";
	return "Good evening";
});

onMounted(async () => {
	try {
		loadError.value = "";
		data.value = await call({ method: "portal_app.api.dashboard.get_dashboard_data" });
		try {
			pinned.value = JSON.parse(localStorage.getItem("portal_recent_projects") || "[]");
		} catch {
			pinned.value = [];
		}
	} catch (e) {
		console.error(e);
		loadError.value =
			e?.responseBody?.message ||
			"Dashboard failed to load. Try reloading after bench build / clear-cache.";
	} finally {
		loading.value = false;
	}
});

function fmt(n) {
	return n == null ? "—" : Number(n).toLocaleString();
}

function startNewProject() {
	router.push({ path: "/projects", query: { create: "1" } });
}

function openProject(name) {
	router.push("/projects/" + encodeURIComponent(name));
}

function priorityPillClass(p) {
	const t = String(p || "").toLowerCase();
	if (t === "urgent") return "portal-pill-danger";
	if (t === "high") return "portal-pill-warning";
	if (t === "medium") return "portal-pill-accent";
	return "portal-pill-muted";
}

function statusPillClass(s) {
	const t = String(s || "").toLowerCase();
	if (t === "completed") return "portal-pill-success";
	if (t === "cancelled") return "portal-pill-danger";
	if (t === "open") return "portal-pill-accent";
	return "portal-pill-muted";
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-7xl space-y-5">
			<!-- Hero -->
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-start justify-between gap-4">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="layout" class="h-3 w-3" />
							Dashboard
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							{{ greeting }}<span v-if="userFullName">, {{ userFullName.split(" ")[0] }}</span>
						</h1>
						<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Portfolio at a glance — health, deadlines, your assigned tasks, and quick access to recent projects.
						</p>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						<button
							class="portal-btn"
							@click="router.push('/projects')"
						>
							<FeatherIcon name="folder" class="h-4 w-4" />
							All projects
						</button>
						<button
							v-if="canCreate"
							class="portal-btn portal-btn-primary"
							@click="startNewProject"
						>
							<FeatherIcon name="plus" class="h-4 w-4" />
							New project
						</button>
					</div>
				</div>
			</div>

			<template v-if="loading">
				<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					<div v-for="i in 4" :key="`kpi-${i}`" class="portal-kpi">
						<SkeletonBlock w="2.25rem" h="2.25rem" rounded="0.75rem" />
						<div class="min-w-0 flex-1 space-y-2">
							<SkeletonBlock w="60%" h="0.7rem" />
							<SkeletonBlock w="40%" h="1.4rem" />
						</div>
					</div>
				</div>
				<div class="grid gap-4 lg:grid-cols-2">
					<div v-for="i in 2" :key="`row-${i}`" class="portal-card-strong space-y-3 p-5">
						<SkeletonBlock w="40%" h="1rem" />
						<SkeletonBlock h="2.25rem" />
						<SkeletonBlock h="2.25rem" />
						<SkeletonBlock h="2.25rem" />
					</div>
				</div>
			</template>
			<div
				v-else-if="loadError"
				class="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 shadow-sm"
			>
				<p class="font-semibold">Could not load dashboard</p>
				<p class="mt-1">{{ loadError }}</p>
			</div>

			<template v-else-if="data">
				<!-- KPI cards -->
				<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					<div class="portal-kpi" style="background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, transparent 60%), var(--portal-surface);">
						<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #4f46e5, #6366f1); color: #fff;">
							<FeatherIcon name="folder" class="h-4 w-4" />
						</div>
						<div class="min-w-0">
							<p class="portal-section-title">Projects</p>
							<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ data.totals?.projects ?? 0 }}</p>
						</div>
					</div>
					<div class="portal-kpi" style="background: linear-gradient(135deg, rgba(56,189,248,0.06) 0%, transparent 60%), var(--portal-surface);">
						<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: #fff;">
							<FeatherIcon name="check-square" class="h-4 w-4" />
						</div>
						<div class="min-w-0">
							<p class="portal-section-title">Open tasks</p>
							<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ data.totals?.open_tasks ?? 0 }}</p>
						</div>
					</div>
					<div class="portal-kpi" style="background: linear-gradient(135deg, rgba(16,185,129,0.06) 0%, transparent 60%), var(--portal-surface);">
						<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #059669, #10b981); color: #fff;">
							<FeatherIcon name="dollar-sign" class="h-4 w-4" />
						</div>
						<div class="min-w-0">
							<p class="portal-section-title">Estimated cost</p>
							<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ fmt(data.totals?.estimated_cost) }}</p>
						</div>
					</div>
					<div class="portal-kpi" style="background: linear-gradient(135deg, rgba(244,114,182,0.06) 0%, transparent 60%), var(--portal-surface);">
						<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #db2777, #f472b6); color: #fff;">
							<FeatherIcon name="alert-triangle" class="h-4 w-4" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="portal-section-title">Budget risk</p>
							<p class="mt-1 text-sm font-semibold text-[color:var(--portal-text)]">
								<span class="text-[color:var(--portal-warning)]">{{ data.budget_health?.at_risk || 0 }}</span>
								<span class="text-[color:var(--portal-muted)]"> at risk · </span>
								<span class="text-[color:var(--portal-danger)]">{{ data.budget_health?.over_100 || 0 }}</span>
								<span class="text-[color:var(--portal-muted)]"> over</span>
							</p>
							<BudgetMeter
								class="mt-2"
								:pct="data.budget_health?.max_pct || 0"
								label="Highest spend"
							/>
						</div>
					</div>
				</div>

				<!-- Pinned recents -->
				<div v-if="pinned.length" class="portal-card-strong p-5">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="bookmark" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Recently visited
						</h2>
						<span class="text-xs text-[color:var(--portal-subtle)]">Stored locally in this browser</span>
					</div>
					<div class="flex flex-wrap gap-2">
						<button
							v-for="p in pinned"
							:key="p.name"
							type="button"
							class="group flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-sm font-medium text-[color:var(--portal-text)] transition hover:border-[color:var(--portal-accent)] hover:bg-[color:var(--portal-accent-soft)]"
							@click="openProject(p.name)"
						>
							<FeatherIcon name="folder" class="h-3.5 w-3.5 text-[color:var(--portal-muted)] group-hover:text-[color:var(--portal-accent)]" />
							{{ p.project_name || p.name }}
						</button>
					</div>
				</div>

				<!-- Status / Kanban distribution -->
				<div class="grid gap-4 lg:grid-cols-2">
					<div class="portal-card-strong p-5">
						<h2 class="mb-3 flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="activity" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							By ERP status
						</h2>
						<ul class="space-y-1.5">
							<li
								v-for="row in data.by_status || []"
								:key="row.status"
								class="flex items-center justify-between rounded-lg px-3 py-2 text-sm transition hover:bg-[color:var(--portal-bg)]"
							>
								<span class="flex items-center gap-2">
									<span class="portal-pill" :class="statusPillClass(row.status)">{{ row.status }}</span>
								</span>
								<span class="font-semibold text-[color:var(--portal-text)]">{{ row.c }}</span>
							</li>
							<li v-if="!(data.by_status || []).length" class="py-4 text-center text-xs text-[color:var(--portal-muted)]">
								No data yet.
							</li>
						</ul>
					</div>
					<div class="portal-card-strong p-5">
						<h2 class="mb-3 flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="trello" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							By Kanban stage
						</h2>
						<ul class="space-y-1.5">
							<li
								v-for="row in data.by_kanban || []"
								:key="String(row.stage)"
								class="flex items-center justify-between rounded-lg px-3 py-2 text-sm transition hover:bg-[color:var(--portal-bg)]"
							>
								<span class="font-medium text-[color:var(--portal-text)]">{{ row.stage }}</span>
								<span class="font-semibold text-[color:var(--portal-text)]">{{ row.c }}</span>
							</li>
							<li v-if="!(data.by_kanban || []).length" class="py-4 text-center text-xs text-[color:var(--portal-muted)]">
								No Kanban data yet.
							</li>
						</ul>
					</div>
				</div>

				<!-- My tasks + Upcoming -->
				<div class="grid gap-4 lg:grid-cols-2">
					<div class="portal-card-strong p-5">
						<div class="mb-3 flex items-center justify-between">
							<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
								<FeatherIcon name="check-square" class="h-4 w-4 text-[color:var(--portal-accent)]" />
								My open tasks
							</h2>
							<button
								class="portal-btn portal-btn-ghost text-xs"
								@click="router.push('/tasks')"
							>
								View all
								<FeatherIcon name="arrow-up-right" class="h-3.5 w-3.5" />
							</button>
						</div>
						<ul class="space-y-2">
							<li
								v-for="t in data.my_tasks || []"
								:key="t.name"
								class="rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2.5 transition hover:border-[color:var(--portal-border-strong)] hover:shadow-sm"
							>
								<div class="flex items-start justify-between gap-2">
									<div class="min-w-0">
										<p class="truncate text-sm font-medium text-[color:var(--portal-text)]">{{ t.subject || t.name }}</p>
										<p class="truncate text-xs text-[color:var(--portal-muted)]">
											<FeatherIcon name="folder" class="mr-1 inline h-3 w-3" />
											{{ t.project }}
										</p>
									</div>
									<span class="portal-pill shrink-0" :class="priorityPillClass(t.priority)">
										{{ t.priority || "—" }}
									</span>
								</div>
								<div class="mt-2 flex items-center justify-between text-xs text-[color:var(--portal-muted)]">
									<span class="flex items-center gap-1">
										<FeatherIcon name="circle" class="h-3 w-3" />
										{{ t.status }}
									</span>
									<span class="flex items-center gap-1">
										<FeatherIcon name="calendar" class="h-3 w-3" />
										{{ t.exp_end_date || "—" }}
									</span>
								</div>
							</li>
							<li v-if="!(data.my_tasks || []).length" class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] py-6 text-center text-sm text-[color:var(--portal-muted)]">
								No open assigned tasks.
							</li>
						</ul>
					</div>

					<div class="portal-card-strong p-5">
						<div class="mb-3 flex items-center justify-between">
							<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
								<FeatherIcon name="calendar" class="h-4 w-4 text-[color:var(--portal-accent)]" />
								Upcoming deadlines
							</h2>
							<span class="text-xs text-[color:var(--portal-subtle)]">Next 14 days</span>
						</div>
						<ul class="space-y-2">
							<li
								v-for="p in data.upcoming_projects || []"
								:key="p.name"
								class="cursor-pointer rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2.5 transition hover:border-[color:var(--portal-accent)] hover:bg-[color:var(--portal-accent-soft)]"
								@click="openProject(p.name)"
							>
								<p class="truncate text-sm font-medium text-[color:var(--portal-text)]">{{ p.project_name || p.name }}</p>
								<div class="mt-1 flex items-center justify-between text-xs text-[color:var(--portal-muted)]">
									<span class="portal-pill" :class="statusPillClass(p.status)">{{ p.status }}</span>
									<span class="flex items-center gap-1">
										<FeatherIcon name="calendar" class="h-3 w-3" />
										{{ p.expected_end_date || "—" }}
									</span>
								</div>
							</li>
							<li v-if="!(data.upcoming_projects || []).length" class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] py-6 text-center text-sm text-[color:var(--portal-muted)]">
								No upcoming deadlines.
							</li>
						</ul>
					</div>
				</div>

				<!-- Recent table -->
				<div class="portal-card-strong p-5">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="layers" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Recent projects
						</h2>
						<button
							class="portal-btn portal-btn-ghost text-xs"
							@click="router.push('/projects')"
						>
							View all
							<FeatherIcon name="arrow-up-right" class="h-3.5 w-3.5" />
						</button>
					</div>
					<div class="overflow-x-auto rounded-xl border border-[color:var(--portal-border)]">
						<table class="w-full text-left text-sm">
							<thead style="background: var(--portal-bg-dim);">
								<tr class="text-[color:var(--portal-muted)]">
									<th class="px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider">Name</th>
									<th class="px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider">Status</th>
									<th class="px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider">Client</th>
									<th class="px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider">End</th>
								</tr>
							</thead>
							<tbody>
								<tr
									v-for="p in data.user_projects_preview || []"
									:key="p.name"
									class="cursor-pointer border-t border-[color:var(--portal-border)] transition hover:bg-[color:var(--portal-accent-soft)]"
									@click="openProject(p.name)"
								>
									<td class="px-4 py-2.5 font-medium text-[color:var(--portal-text)]">{{ p.project_name || p.name }}</td>
									<td class="px-4 py-2.5">
										<span class="portal-pill" :class="statusPillClass(p.status)">{{ p.status }}</span>
									</td>
									<td class="px-4 py-2.5 text-[color:var(--portal-muted)]">{{ p.customer || "—" }}</td>
									<td class="px-4 py-2.5 text-[color:var(--portal-muted)]">{{ p.expected_end_date || "—" }}</td>
								</tr>
								<tr v-if="!(data.user_projects_preview || []).length">
									<td colspan="4" class="p-6 text-center text-[color:var(--portal-muted)]">
										No projects yet.
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>

				<div
					v-if="data.portal_settings?.file_access_note"
					class="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 shadow-sm"
				>
					<strong>File policy:</strong> {{ data.portal_settings.file_access_note }}
				</div>
			</template>
		</div>
	</div>
</template>
