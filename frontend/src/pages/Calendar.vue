<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { call } from "@/api";
import { Button, TextInput, FeatherIcon } from "frappe-ui";
import EmptyState from "@/component/EmptyState.vue";
import SkeletonBlock from "@/component/SkeletonBlock.vue";

const router = useRouter();

const loading = ref(true);
const events = ref([]);
const projectOptions = ref([]);

const viewMode = ref("month");
const anchorDate = ref(new Date());
const searchQuery = ref("");
const typeFilter = ref("all");
const projectFilter = ref("");

const selectedDay = ref(null);
let searchDebounce;

const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function parseLocalDate(str) {
	if (str == null || str === "") return null;
	const raw = typeof str === "string" ? str : String(str);
	const m = raw.match(/^(\d{4}-\d{2}-\d{2})/);
	if (m) {
		const [y, mo, d] = m[1].split("-").map(Number);
		return new Date(y, mo - 1, d);
	}
	const d = new Date(raw);
	return Number.isNaN(d.getTime()) ? null : d;
}

function dateOnly(d) {
	return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function isSameDay(a, b) {
	return (
		a.getFullYear() === b.getFullYear() &&
		a.getMonth() === b.getMonth() &&
		a.getDate() === b.getDate()
	);
}

function isToday(d) {
	return isSameDay(d, new Date());
}

function eventSpansDay(ev, day) {
	const s = parseLocalDate(ev.start);
	const e = parseLocalDate(ev.end || ev.start);
	if (!s || !e) return false;
	const a = dateOnly(s).getTime();
	const b = dateOnly(e).getTime();
	const t = dateOnly(day).getTime();
	return t >= a && t <= b;
}

function eventsForDay(dayDate) {
	return events.value.filter((ev) => eventSpansDay(ev, dayDate));
}

function isTask(ev) {
	return ev.extendedProps?.type === "task";
}

function eventPillClass(ev) {
	return isTask(ev)
		? "bg-violet-50 text-violet-900 ring-1 ring-violet-200 hover:bg-violet-100"
		: "bg-sky-50 text-sky-900 ring-1 ring-sky-200 hover:bg-sky-100";
}

function eventDotClass(ev) {
	return isTask(ev) ? "bg-violet-500" : "bg-sky-500";
}

const rangeTitle = computed(() => {
	const d = anchorDate.value;
	if (viewMode.value === "month" || viewMode.value === "list") {
		return d.toLocaleDateString(undefined, { month: "long", year: "numeric" });
	}
	const ws = weekStart(d);
	const we = new Date(ws);
	we.setDate(we.getDate() + 6);
	if (ws.getMonth() === we.getMonth() && ws.getFullYear() === we.getFullYear()) {
		return `${ws.toLocaleDateString(undefined, { month: "short", day: "numeric" })} – ${we.toLocaleDateString(undefined, { day: "numeric", year: "numeric" })}`;
	}
	return `${ws.toLocaleDateString(undefined, { month: "short", day: "numeric" })} – ${we.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}`;
});

function weekStart(d) {
	const x = new Date(d);
	const pad = (x.getDay() + 6) % 7;
	x.setDate(x.getDate() - pad);
	return dateOnly(x);
}

function startOfCalendarGrid(d) {
	const y = d.getFullYear();
	const m = d.getMonth();
	const first = new Date(y, m, 1);
	const pad = (first.getDay() + 6) % 7;
	return new Date(y, m, 1 - pad);
}

const monthCells = computed(() => {
	const start = startOfCalendarGrid(anchorDate.value);
	const cur = new Date(start);
	const cells = [];
	const targetMonth = anchorDate.value.getMonth();
	for (let i = 0; i < 42; i++) {
		const inMonth = cur.getMonth() === targetMonth;
		cells.push({
			date: new Date(cur),
			inMonth,
			dayNum: cur.getDate(),
			key: `${cur.getFullYear()}-${cur.getMonth()}-${cur.getDate()}`,
			events: eventsForDay(cur),
			today: isToday(cur),
		});
		cur.setDate(cur.getDate() + 1);
	}
	return cells;
});

const weekDays = computed(() => {
	const ws = weekStart(anchorDate.value);
	const days = [];
	for (let i = 0; i < 7; i++) {
		const d = new Date(ws);
		d.setDate(ws.getDate() + i);
		days.push({
			date: d,
			key: `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`,
			label: d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" }),
			events: eventsForDay(d),
			today: isToday(d),
		});
	}
	return days;
});

function overlapsAnchorMonth(ev) {
	const y = anchorDate.value.getFullYear();
	const m = anchorDate.value.getMonth();
	const ms = new Date(y, m, 1);
	const me = new Date(y, m + 1, 0);
	const s = parseLocalDate(ev.start);
	const e = parseLocalDate(ev.end || ev.start);
	if (!s || !e) return false;
	const a = dateOnly(s).getTime();
	const b = dateOnly(e).getTime();
	const x = dateOnly(ms).getTime();
	const z = dateOnly(me).getTime();
	return a <= z && b >= x;
}

const listRows = computed(() => {
	const rows = events.value
		.filter((ev) => overlapsAnchorMonth(ev))
		.map((ev) => ({
			...ev,
			_sort: parseLocalDate(ev.start)?.getTime() ?? 0,
		}))
		.sort((a, b) => a._sort - b._sort);
	return rows;
});

async function loadEvents() {
	loading.value = true;
	try {
		const res = await call({
			method: "portal_app.api.projects.calendar_events",
			args: {
				search: searchQuery.value.trim() || undefined,
				type_filter: typeFilter.value,
				project: projectFilter.value || undefined,
			},
		});
		events.value = res.events || [];
		projectOptions.value = res.projects || [];
	} catch (e) {
		console.error(e);
		events.value = [];
	} finally {
		loading.value = false;
	}
}

function shiftPeriod(dir) {
	const d = new Date(anchorDate.value);
	if (viewMode.value === "month" || viewMode.value === "list") {
		d.setMonth(d.getMonth() + dir);
	} else {
		d.setDate(d.getDate() + dir * 7);
	}
	anchorDate.value = d;
}

function goToday() {
	anchorDate.value = new Date();
}

function openEvent(ev) {
	selectedDay.value = null;
	const proj = ev.extendedProps?.project;
	if (proj) {
		router.push({ name: "ProjectDetail", params: { name: proj } });
	}
}

function openDayModal(cell) {
	if (!cell.events.length) return;
	if (cell.events.length <= 3) return;
	selectedDay.value = {
		label: cell.date.toLocaleDateString(undefined, {
			weekday: "long",
			day: "numeric",
			month: "long",
			year: "numeric",
		}),
		events: cell.events,
	};
}

function formatRange(ev) {
	const s = ev.start || "—";
	const e = ev.end && ev.end !== ev.start ? ev.end : null;
	return e ? `${s} → ${e}` : s;
}

watch([typeFilter, projectFilter], () => {
	loadEvents();
});

watch(searchQuery, () => {
	clearTimeout(searchDebounce);
	searchDebounce = setTimeout(() => loadEvents(), 350);
});

onMounted(() => loadEvents());
</script>

<template>
	<div class="h-full overflow-auto p-4 sm:p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-6xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="calendar" class="h-3 w-3" />
							Calendar
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							Project & task timeline
						</h1>
						<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Each entry is a <strong>project</strong> or <strong>task</strong>, drawn on every day from its start through its end. Click any entry to open that project.
						</p>
					</div>
					<div class="flex shrink-0 flex-wrap gap-2">
						<span class="portal-pill" style="background: rgba(56, 189, 248, 0.12); color: rgb(7, 89, 133); border-color: rgba(56, 189, 248, 0.3);">
							<span class="h-2 w-2 rounded-full bg-sky-500"></span>
							Project
						</span>
						<span class="portal-pill" style="background: rgba(167, 139, 250, 0.12); color: rgb(76, 29, 149); border-color: rgba(167, 139, 250, 0.3);">
							<span class="h-2 w-2 rounded-full bg-violet-500"></span>
							Task
						</span>
					</div>
				</div>
			</div>

			<div class="portal-card-strong flex flex-col gap-3 p-4">
				<div class="flex flex-wrap items-center gap-2">
					<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] p-0.5">
						<button
							v-for="mode in [
								{ id: 'month', label: 'Month' },
								{ id: 'week', label: 'Week' },
								{ id: 'list', label: 'Agenda' },
							]"
							:key="mode.id"
							type="button"
							class="rounded-lg px-3 py-1.5 text-sm font-medium transition"
							:class="
								viewMode === mode.id
									? 'bg-white text-[color:var(--portal-text)] shadow-sm'
									: 'text-[color:var(--portal-muted)] hover:text-[color:var(--portal-text)]'
							"
							@click="viewMode = mode.id"
						>
							{{ mode.label }}
						</button>
					</div>
					<div class="mx-2 hidden h-6 w-px bg-[color:var(--portal-border)] sm:block" />
					<button class="portal-btn" @click="goToday">
						<FeatherIcon name="target" class="h-3.5 w-3.5" />
						Today
					</button>
					<div class="flex items-center gap-1">
						<button
							type="button"
							class="rounded-lg border border-[color:var(--portal-border)] bg-white px-2 py-1.5 text-[color:var(--portal-text)] transition hover:bg-[color:var(--portal-bg)]"
							aria-label="Previous"
							@click="shiftPeriod(-1)"
						>
							<FeatherIcon name="chevron-left" class="h-4 w-4" />
						</button>
						<span class="min-w-[10rem] text-center text-sm font-semibold text-[color:var(--portal-text)]">{{ rangeTitle }}</span>
						<button
							type="button"
							class="rounded-lg border border-[color:var(--portal-border)] bg-white px-2 py-1.5 text-[color:var(--portal-text)] transition hover:bg-[color:var(--portal-bg)]"
							aria-label="Next"
							@click="shiftPeriod(1)"
						>
							<FeatherIcon name="chevron-right" class="h-4 w-4" />
						</button>
					</div>
				</div>

				<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					<div class="lg:col-span-2">
						<label class="portal-section-title mb-1 block">Search</label>
						<TextInput
							v-model="searchQuery"
							class="w-full rounded-xl"
							placeholder="Title, project or task id…"
						/>
					</div>
					<div>
						<label class="portal-section-title mb-1 block">Type</label>
						<select v-model="typeFilter" class="portal-input">
							<option value="all">Projects &amp; tasks</option>
							<option value="project">Projects only</option>
							<option value="task">Tasks only</option>
						</select>
					</div>
					<div>
						<label class="portal-section-title mb-1 block">Project</label>
						<select v-model="projectFilter" class="portal-input">
							<option value="">All accessible projects</option>
							<option v-for="p in projectOptions" :key="p.name" :value="p.name">
								{{ p.project_name || p.name }}
							</option>
						</select>
					</div>
				</div>
			</div>

			<div v-if="loading" class="portal-card-strong space-y-3 p-5">
				<div class="grid grid-cols-7 gap-2">
					<SkeletonBlock v-for="i in 7" :key="`day-h-${i}`" h="1.25rem" />
				</div>
				<div class="grid grid-cols-7 gap-2">
					<SkeletonBlock v-for="i in 35" :key="`day-${i}`" h="5rem" rounded="0.75rem" />
				</div>
			</div>

			<EmptyState
				v-else-if="!events.length"
				icon="calendar"
				title="No dated projects or tasks in this view"
				message="Set Expected Start / End on the Project (or actual dates from timesheets), and dates on Tasks. Then pick a month that overlaps, or clear the search / project filter above."
				gradient="linear-gradient(135deg, #f59e0b 0%, #fb923c 100%)"
			/>

			<!-- Month grid -->
			<div
				v-else-if="viewMode === 'month' && events.length"
				class="overflow-hidden rounded-2xl border border-[color:var(--portal-border)] bg-white shadow-sm"
			>
				<div class="grid grid-cols-7 border-b border-[color:var(--portal-border)] bg-[color:var(--portal-bg)]">
					<div
						v-for="w in weekdayLabels"
						:key="w"
						class="py-2 text-center text-xs font-semibold uppercase tracking-wide text-gray-500"
					>
						{{ w }}
					</div>
				</div>
				<div class="grid grid-cols-7 gap-px bg-gray-200">
					<div
						v-for="cell in monthCells"
						:key="cell.key"
						class="min-h-[6.5rem] bg-white p-1 sm:min-h-[7.5rem] sm:p-1.5"
						:class="{
							'bg-gray-50/80': !cell.inMonth,
							'ring-1 ring-inset ring-sky-300': cell.today,
						}"
					>
						<div
							class="mb-1 flex items-center justify-between"
							:class="cell.inMonth ? 'text-gray-900' : 'text-gray-400'"
						>
							<span class="text-sm font-medium">{{ cell.dayNum }}</span>
							<button
								v-if="cell.events.length > 3"
								type="button"
								class="text-[10px] font-medium text-sky-700 hover:underline sm:text-xs"
								@click="openDayModal(cell)"
							>
								+{{ cell.events.length - 3 }} more
							</button>
						</div>
						<div class="flex flex-col gap-0.5">
							<button
								v-for="ev in cell.events.slice(0, 3)"
								:key="ev.id + cell.key"
								type="button"
								class="w-full truncate rounded px-1 py-0.5 text-left text-[10px] font-medium leading-tight sm:text-xs"
								:class="eventPillClass(ev)"
								:title="ev.title + ' — ' + formatRange(ev)"
								@click.stop="openEvent(ev)"
							>
								{{ ev.title }}
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Week columns -->
			<div
				v-else-if="viewMode === 'week' && events.length"
				class="grid grid-cols-1 gap-3 sm:grid-cols-7"
			>
				<div
					v-for="day in weekDays"
					:key="day.key"
					class="flex min-h-[12rem] flex-col rounded-2xl border border-gray-200 bg-white p-2 shadow-sm"
					:class="{ 'ring-1 ring-sky-300': day.today }"
				>
					<p class="border-b border-gray-100 pb-2 text-xs font-semibold text-gray-700">{{ day.label }}</p>
					<div class="mt-2 flex flex-1 flex-col gap-1 overflow-y-auto">
						<button
							v-for="ev in day.events"
							:key="ev.id + day.key"
							type="button"
							class="w-full rounded-lg px-2 py-1.5 text-left text-xs font-medium"
							:class="eventPillClass(ev)"
							@click="openEvent(ev)"
						>
							<span class="line-clamp-2">{{ ev.title }}</span>
							<span class="mt-0.5 block text-[10px] font-normal opacity-80">{{ formatRange(ev) }}</span>
						</button>
						<p v-if="!day.events.length" class="py-4 text-center text-xs text-gray-400">No items</p>
					</div>
				</div>
			</div>

			<!-- Agenda list -->
			<div v-else-if="viewMode === 'list' && events.length" class="overflow-hidden rounded-2xl border border-[color:var(--portal-border)] bg-white shadow-sm">
				<div class="border-b border-gray-100 bg-gray-50 px-4 py-2 text-xs font-semibold uppercase text-gray-500">
					All matching items ({{ listRows.length }})
				</div>
				<ul class="divide-y divide-gray-100">
					<li
						v-for="ev in listRows"
						:key="ev.id"
						class="flex cursor-pointer flex-wrap items-start justify-between gap-3 px-4 py-3 transition hover:bg-gray-50"
						role="button"
						tabindex="0"
						@click="openEvent(ev)"
						@keydown.enter="openEvent(ev)"
					>
						<div class="min-w-0 flex-1">
							<p class="font-medium text-gray-900">{{ ev.title }}</p>
							<p class="mt-0.5 text-xs text-gray-500">
								<span
									class="mr-2 inline-block rounded px-1.5 py-0.5 font-medium"
									:class="isTask(ev) ? 'bg-violet-100 text-violet-800' : 'bg-sky-100 text-sky-800'"
								>
									{{ isTask(ev) ? "Task" : "Project" }}
								</span>
								<span v-if="ev.extendedProps?.project">Project: {{ ev.extendedProps.project }}</span>
								<span v-if="ev.extendedProps?.status" class="text-gray-400"> · {{ ev.extendedProps.status }}</span>
							</p>
						</div>
						<div class="shrink-0 text-right text-sm text-gray-600">
							{{ formatRange(ev) }}
						</div>
					</li>
					<li v-if="!listRows.length" class="px-4 py-10 text-center text-sm text-gray-500">
						No dated projects or tasks match your filters.
					</li>
				</ul>
			</div>
		</div>

		<Teleport to="body">
			<div
				v-if="selectedDay"
				class="fixed inset-0 z-[70] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-black/40" @click="selectedDay = null"></div>
				<div class="relative z-10 max-h-[80vh] w-full max-w-md overflow-hidden rounded-2xl border bg-white shadow-2xl">
					<div class="border-b border-gray-100 px-4 py-3">
						<h3 class="font-semibold text-gray-900">{{ selectedDay.label }}</h3>
						<p class="text-xs text-gray-500">{{ selectedDay.events.length }} items</p>
					</div>
					<ul class="max-h-[55vh] overflow-y-auto divide-y divide-gray-100">
						<li
							v-for="ev in selectedDay.events"
							:key="ev.id"
							class="cursor-pointer px-4 py-3 hover:bg-gray-50"
							@click="openEvent(ev)"
						>
							<p class="font-medium text-gray-900">{{ ev.title }}</p>
							<p class="text-xs text-gray-500">{{ formatRange(ev) }}</p>
						</li>
					</ul>
					<div class="border-t border-gray-100 px-4 py-3 text-right">
						<button
							type="button"
							class="rounded-lg px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
							@click="selectedDay = null"
						>
							Close
						</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
