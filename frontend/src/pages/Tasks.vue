<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { call } from "@/api";
import { useRoute, useRouter } from "vue-router";
import { Button, TextInput, FeatherIcon } from "frappe-ui";

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const savingTask = ref("");
const tasks = ref([]);
const mineOpen = ref([]);
const summary = ref({ total: 0, open: 0, overdue: 0 });
const err = ref("");

const search = ref("");
const status = ref("");
const priority = ref("");
const project = ref("");
const onlyMine = ref(false);

const statusOptions = ["Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled"];
const priorityOptions = ["Low", "Medium", "High", "Urgent"];

let debounce;

function applyRoutePreset() {
	if (route.query.project) project.value = String(route.query.project);
}

async function loadTasks() {
	loading.value = true;
	err.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.list_tasks",
			args: {
				status: status.value || undefined,
				priority: priority.value || undefined,
				project: project.value || undefined,
				search: search.value.trim() || undefined,
				only_mine: onlyMine.value ? 1 : 0,
			},
		});
		tasks.value = res.tasks || [];
		mineOpen.value = res.mine_open || [];
		summary.value = res.summary || { total: 0, open: 0, overdue: 0 };
	} catch (e) {
		console.error(e);
		err.value = e?.responseBody?.message || "Could not load tasks.";
	} finally {
		loading.value = false;
	}
}

function clearFilters() {
	search.value = "";
	status.value = "";
	priority.value = "";
	project.value = "";
	onlyMine.value = false;
}

async function saveTask(t) {
	savingTask.value = t.name;
	err.value = "";
	try {
		await call({
			method: "portal_app.api.projects.update_task",
			type: "POST",
			args: {
				task: t.name,
				status: t.status,
				priority: t.priority,
				progress: t.progress,
				exp_start_date: t.exp_start_date || undefined,
				exp_end_date: t.exp_end_date || undefined,
			},
		});
	} catch (e) {
		console.error(e);
		err.value = e?.responseBody?.message || "Could not update task.";
	} finally {
		savingTask.value = "";
	}
}

const hasFilters = computed(
	() => !!(search.value.trim() || status.value || priority.value || project.value || !onlyMine.value),
);

function statusPillClass(v) {
	const x = String(v || "").toLowerCase();
	if (x === "completed") return "portal-pill-success";
	if (x === "cancelled" || x === "overdue") return "portal-pill-danger";
	if (x === "pending review") return "portal-pill-warning";
	if (x === "working" || x === "open") return "portal-pill-accent";
	return "portal-pill-muted";
}

function priorityPillClass(v) {
	const x = String(v || "").toLowerCase();
	if (x === "urgent") return "portal-pill-danger";
	if (x === "high") return "portal-pill-warning";
	if (x === "medium") return "portal-pill-accent";
	return "portal-pill-muted";
}

watch([status, priority, project, onlyMine], loadTasks);
watch(search, () => {
	clearTimeout(debounce);
	debounce = setTimeout(loadTasks, 300);
});

onMounted(async () => {
	applyRoutePreset();
	await loadTasks();
});
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-7xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="check-square" class="h-3 w-3" />
							Tasks
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">Tasks workspace</h1>
						<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Search and filter tasks, track progress, and update status — all from one place.
						</p>
					</div>
					<button class="portal-btn" @click="router.push('/projects')">
						<FeatherIcon name="arrow-left" class="h-4 w-4" />
						Back to projects
					</button>
				</div>
			</div>

			<div class="grid gap-3 sm:grid-cols-3">
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #4f46e5, #6366f1); color: #fff;">
						<FeatherIcon name="layers" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Total</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-text)]">{{ summary.total }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: #fff;">
						<FeatherIcon name="circle" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Open</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-accent-strong)]">{{ summary.open }}</p>
					</div>
				</div>
				<div class="portal-kpi">
					<div class="portal-kpi-icon" style="background: linear-gradient(135deg, #dc2626, #f87171); color: #fff;">
						<FeatherIcon name="alert-octagon" class="h-4 w-4" />
					</div>
					<div class="min-w-0">
						<p class="portal-section-title">Overdue</p>
						<p class="mt-1 text-2xl font-semibold text-[color:var(--portal-danger)]">{{ summary.overdue }}</p>
					</div>
				</div>
			</div>

			<div class="portal-card-strong p-5">
				<div class="mb-3 flex items-center justify-between">
					<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
						<FeatherIcon name="user-check" class="h-4 w-4 text-[color:var(--portal-accent)]" />
						Assigned to you (open)
					</h2>
					<span class="portal-pill portal-pill-muted">{{ mineOpen.length }} items</span>
				</div>
				<div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
					<div
						v-for="t in mineOpen"
						:key="t.name"
						class="cursor-pointer rounded-xl border border-[color:var(--portal-border)] bg-white p-3 transition hover:border-[color:var(--portal-accent)] hover:shadow-md"
						@click="router.push('/projects/' + encodeURIComponent(t.project))"
					>
						<p class="truncate text-sm font-medium text-[color:var(--portal-text)]">{{ t.subject || t.name }}</p>
						<p class="mt-0.5 truncate text-xs text-[color:var(--portal-muted)]">
							<FeatherIcon name="folder" class="mr-1 inline h-3 w-3" />{{ t.project }}
						</p>
						<div class="mt-2 flex items-center justify-between gap-2">
							<span class="portal-pill" :class="statusPillClass(t.status)">{{ t.status }}</span>
							<span class="portal-pill" :class="priorityPillClass(t.priority)">{{ t.priority || "Low" }}</span>
						</div>
					</div>
					<div
						v-if="!mineOpen.length"
						class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] bg-white p-6 text-center text-sm text-[color:var(--portal-muted)] md:col-span-2 xl:col-span-3"
					>
						No open tasks assigned to you.
					</div>
				</div>
			</div>

			<div class="portal-card-strong p-5">
				<div class="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
					<div class="relative w-full lg:col-span-2">
						<FeatherIcon
							name="search"
							class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--portal-subtle)]"
						/>
						<TextInput v-model="search" class="w-full rounded-xl pl-9" placeholder="Search by task name or title" />
					</div>
					<select v-model="status" class="portal-input">
						<option value="">All status</option>
						<option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
					</select>
					<select v-model="priority" class="portal-input">
						<option value="">All priority</option>
						<option v-for="p in priorityOptions" :key="p" :value="p">{{ p }}</option>
					</select>
					<TextInput v-model="project" class="w-full rounded-xl" placeholder="Filter by project ID" />
				</div>
				<div class="mt-3 flex flex-wrap items-center gap-3">
					<label class="inline-flex items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-3 py-1.5 text-sm text-[color:var(--portal-text)]">
						<input v-model="onlyMine" type="checkbox" class="rounded border-gray-300" />
						<FeatherIcon name="user" class="h-3.5 w-3.5 text-[color:var(--portal-muted)]" />
						Only my tasks
					</label>
					<button
						v-if="hasFilters"
						class="portal-btn portal-btn-ghost text-xs"
						@click="clearFilters"
					>
						<FeatherIcon name="x" class="h-3.5 w-3.5" />
						Clear filters
					</button>
				</div>
			</div>

			<div v-if="loading" class="portal-card-strong flex items-center justify-center gap-2 p-10 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading tasks…
			</div>
			<div v-else class="portal-card-strong overflow-x-auto p-0">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-[color:var(--portal-border)] text-[color:var(--portal-muted)]" style="background: var(--portal-bg-dim);">
							<th class="px-3 py-3 text-xs font-semibold uppercase tracking-wider">Task</th>
							<th class="px-3 py-3 text-xs font-semibold uppercase tracking-wider">Project</th>
							<th class="px-3 py-3 text-xs font-semibold uppercase tracking-wider">Status</th>
							<th class="px-3 py-3 text-xs font-semibold uppercase tracking-wider">Priority</th>
							<th class="px-3 py-3 text-xs font-semibold uppercase tracking-wider">Progress</th>
							<th class="px-3 py-3 text-xs font-semibold uppercase tracking-wider">Start</th>
							<th class="px-3 py-3 text-xs font-semibold uppercase tracking-wider">End</th>
							<th class="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider">Action</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="t in tasks"
							:key="t.name"
							class="border-b border-[color:var(--portal-border)] align-top transition"
							:class="{
								'bg-rose-50/30': t.status === 'Overdue',
								'bg-emerald-50/30': t.status === 'Completed',
							}"
						>
							<td class="px-3 py-3">
								<p class="font-medium text-[color:var(--portal-text)]">{{ t.subject || t.name }}</p>
								<p class="font-mono text-xs text-[color:var(--portal-subtle)]">{{ t.name }}</p>
								<div class="mt-2 flex flex-wrap gap-1">
									<span class="portal-pill" :class="statusPillClass(t.status)">{{ t.status || "Open" }}</span>
									<span class="portal-pill" :class="priorityPillClass(t.priority)">{{ t.priority || "Low" }}</span>
								</div>
							</td>
							<td class="px-3 py-3">
								<button
									type="button"
									class="text-left text-[color:var(--portal-accent)] hover:underline"
									@click="router.push('/projects/' + encodeURIComponent(t.project))"
								>
									{{ t.project }}
								</button>
							</td>
							<td class="px-3 py-3">
								<select v-model="t.status" class="portal-input py-1.5">
									<option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
								</select>
							</td>
							<td class="px-3 py-3">
								<select v-model="t.priority" class="portal-input py-1.5">
									<option v-for="p in priorityOptions" :key="p" :value="p">{{ p }}</option>
								</select>
							</td>
							<td class="px-3 py-3">
								<div class="flex items-center gap-2">
									<input
										v-model.number="t.progress"
										type="number"
										min="0"
										max="100"
										class="portal-input w-20 px-2 py-1.5"
									/>
									<span class="text-xs text-[color:var(--portal-muted)]">%</span>
								</div>
							</td>
							<td class="px-3 py-3">
								<input v-model="t.exp_start_date" type="date" class="portal-input py-1.5" />
							</td>
							<td class="px-3 py-3">
								<input v-model="t.exp_end_date" type="date" class="portal-input py-1.5" />
							</td>
							<td class="px-3 py-3 text-right">
								<Button
									type="button"
									size="sm"
									variant="solid"
									class="rounded-lg"
									style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); color: #fff;"
									:loading="savingTask === t.name"
									@click="saveTask(t)"
								>
									Save
								</Button>
							</td>
						</tr>
						<tr v-if="!tasks.length">
							<td colspan="8" class="px-3 py-12 text-center text-[color:var(--portal-muted)]">
								No tasks found. Try clearing filters or disabling “Only my tasks”.
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<div v-if="err" class="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
				{{ err }}
			</div>
		</div>
	</div>
</template>
