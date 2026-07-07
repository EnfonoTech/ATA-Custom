<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { FeatherIcon } from "frappe-ui";
import { call } from "@/api";

const loading      = ref(true);
const milestones   = ref([]);
const officeList   = ref(["ALL"]);
const officeFilter = ref("ALL");
const projects     = ref([]);
const weekOffset   = ref(0);
const dayIndex     = ref(0);

const HOURS = Array.from({ length: 13 }, (_, i) => i + 7); // 7:00 .. 19:00

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

function fmt(d) {
	return d.toISOString().slice(0, 10);
}
function startOfWeek(d) {
	const date = new Date(d);
	const day = date.getDay();
	const diff = (day === 0 ? -6 : 1) - day; // shift to Monday
	date.setDate(date.getDate() + diff);
	date.setHours(0, 0, 0, 0);
	return date;
}

const today = new Date();
const todayStr = fmt(today);

// 4 weeks (28 days), starting from the Monday of the current week + weekOffset*7.
const days = computed(() => {
	const base = startOfWeek(today);
	base.setDate(base.getDate() + weekOffset.value * 28);
	return Array.from({ length: 28 }, (_, i) => {
		const d = new Date(base);
		d.setDate(base.getDate() + i);
		return {
			dateStr: fmt(d),
			dayName: d.toLocaleDateString(undefined, { weekday: "short" }),
			dayNum: d.getDate(),
			month: d.toLocaleDateString(undefined, { month: "short" }),
		};
	});
});
const weeks = computed(() => [days.value.slice(0, 7), days.value.slice(7, 14), days.value.slice(14, 21), days.value.slice(21, 28)]);
const selectedDay = computed(() => days.value[dayIndex.value]);

async function loadMilestones() {
	loading.value = true;
	try {
		milestones.value = await call({
			method: "portal_app.api.daily_gantt.get_milestones",
			args: { start_date: days.value[0].dateStr, end_date: days.value[27].dateStr },
		});
	} catch (e) {
		console.error(e);
		milestones.value = [];
	} finally {
		loading.value = false;
	}
}

async function loadProjects() {
	try {
		const res = await call({ method: "portal_app.api.projects.list_projects" });
		projects.value = res?.projects || [];
	} catch (e) {
		console.error(e);
	}
}

onMounted(async () => {
	dayIndex.value = days.value.findIndex((d) => d.dateStr === todayStr);
	if (dayIndex.value < 0) dayIndex.value = 0;
	await Promise.all([
		loadMilestones(),
		loadProjects(),
		call({ method: "portal_app.api.teams.get_offices" }).then((o) => {
			if (Array.isArray(o) && o.length) officeList.value = ["ALL", ...o];
		}),
	]);
});

watch(weekOffset, () => {
	dayIndex.value = 0;
	loadMilestones();
});

function milestonesFor(dateStr) {
	return milestones.value.filter((m) => m.starts_on?.slice(0, 10) === dateStr);
}
const dayMilestones = computed(() => milestonesFor(selectedDay.value?.dateStr));
const completedCount = computed(() => dayMilestones.value.filter((m) => m.completed).length);

function timePct(startsOn) {
	const t = startsOn?.slice(11, 16) || "07:00";
	const [h, m] = t.split(":").map(Number);
	const hourFrac = h + m / 60;
	return Math.min(100, Math.max(0, ((hourFrac - 7) / 12) * 100));
}
function projectName(id) {
	return projects.value.find((p) => p.name === id)?.project_name || "";
}
const filteredProjects = computed(() => {
	if (officeFilter.value === "ALL") return projects.value;
	return projects.value.filter((p) => p.portal_office === officeFilter.value);
});

// ── Add / Edit / Toggle / Delete ────────────────────────────────────────────
const showAdd   = ref(false);
const saving    = ref(false);
const addError  = ref("");
const form      = ref({ title: "", time: "09:00", color: "#185FA5", project: "" });

function openAdd() {
	addError.value = "";
	form.value = { title: "", time: "09:00", color: "#185FA5", project: "" };
	showAdd.value = true;
}
function closeAdd() { showAdd.value = false; }

async function submitAdd() {
	if (!form.value.title.trim()) { addError.value = "Title is required."; return; }
	saving.value = true;
	addError.value = "";
	try {
		await call({
			method: "portal_app.api.daily_gantt.create_milestone",
			type: "POST",
			args: {
				title: form.value.title.trim(),
				date: selectedDay.value.dateStr,
				time: form.value.time,
				project: form.value.project || undefined,
				color: form.value.color,
			},
		});
		closeAdd();
		await loadMilestones();
	} catch (e) {
		addError.value = apiErr(e);
	} finally {
		saving.value = false;
	}
}

async function toggleMilestone(m) {
	try {
		await call({ method: "portal_app.api.daily_gantt.toggle_milestone", type: "POST", args: { name: m.name } });
		m.completed = !m.completed;
	} catch (e) {
		console.error(e);
	}
}

const editingId = ref(null);
const editForm  = ref({ title: "", time: "" });

function startEdit(m) {
	editingId.value = m.name;
	editForm.value = { title: m.subject, time: m.starts_on?.slice(11, 16) || "09:00" };
}
function cancelEdit() { editingId.value = null; }

async function saveEdit(m) {
	try {
		await call({
			method: "portal_app.api.daily_gantt.update_milestone",
			type: "POST",
			args: { name: m.name, title: editForm.value.title, time: editForm.value.time },
		});
		editingId.value = null;
		await loadMilestones();
	} catch (e) {
		console.error(e);
	}
}

async function removeMilestone(m) {
	try {
		await call({ method: "portal_app.api.daily_gantt.delete_milestone", type: "POST", args: { name: m.name } });
		await loadMilestones();
	} catch (e) {
		console.error(e);
	}
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-5xl space-y-5">

			<!-- Header -->
			<div class="portal-hero portal-anim-in">
				<div class="flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="clock" class="h-3 w-3" />
							Daily Planning
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							Gantt Chart Daily
						</h1>
						<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
							4-week timeline · {{ dayMilestones.length }} milestones today · {{ completedCount }} completed
						</p>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] p-0.5 shadow-sm" style="background:var(--portal-surface)">
							<button
								v-for="o in officeList" :key="o"
								type="button"
								class="rounded-lg px-3 py-1.5 text-xs font-semibold transition"
								:style="officeFilter === o ? 'background:var(--portal-accent);color:#fff;' : 'color:var(--portal-muted);'"
								@click="officeFilter = o"
							>{{ o }}</button>
						</div>
						<button class="portal-btn portal-btn-primary" @click="openAdd">
							<FeatherIcon name="plus" class="h-4 w-4" />
							Milestone
						</button>
					</div>
				</div>
			</div>

			<!-- Week navigation -->
			<div class="flex items-center gap-3">
				<button class="portal-btn" @click="weekOffset--">
					<FeatherIcon name="chevron-left" class="h-3.5 w-3.5" />
					Prev 4 Weeks
				</button>
				<span class="text-sm font-semibold" style="color:var(--portal-text);">
					{{ days[0]?.month }} {{ days[0]?.dayNum }} – {{ days[27]?.month }} {{ days[27]?.dayNum }}
					<span v-if="weekOffset === 0" class="ml-2 text-xs" style="color:var(--portal-accent);">(Current)</span>
				</span>
				<button class="portal-btn" @click="weekOffset++">
					Next 4 Weeks
					<FeatherIcon name="chevron-right" class="h-3.5 w-3.5" />
				</button>
			</div>

			<!-- 4-week mini calendar -->
			<div class="portal-card-strong p-4 space-y-2">
				<div v-for="(week, wi) in weeks" :key="wi" class="grid grid-cols-7 gap-2">
					<button
						v-for="(d, di) in week" :key="d.dateStr"
						type="button"
						class="rounded-xl p-2.5 text-center border transition"
						:class="dayIndex === wi * 7 + di
							? 'border-transparent'
							: d.dateStr === todayStr
								? 'border-[color:var(--portal-accent)]/40'
								: 'border-transparent hover:bg-[color:var(--portal-surface-alt)]'"
						:style="dayIndex === wi * 7 + di
							? 'background:#0F172A;color:#fff;'
							: d.dateStr === todayStr ? 'background:var(--portal-accent-soft);' : ''"
						@click="dayIndex = wi * 7 + di"
					>
						<p class="text-[10px] font-medium" :style="dayIndex === wi*7+di ? 'color:rgba(255,255,255,0.7)' : 'color:var(--portal-muted)'">{{ d.dayName }}</p>
						<p class="text-base font-bold" :style="dayIndex === wi*7+di ? 'color:#fff' : (d.dateStr === todayStr ? 'color:var(--portal-accent)' : 'color:var(--portal-text)')">{{ d.dayNum }}</p>
						<p class="text-[9px]" :style="dayIndex === wi*7+di ? 'color:rgba(255,255,255,0.5)' : 'color:var(--portal-subtle)'">{{ d.month }}</p>
						<div v-if="milestonesFor(d.dateStr).length" class="flex justify-center gap-0.5 mt-1">
							<span
								v-for="m in milestonesFor(d.dateStr).slice(0, 3)" :key="m.name"
								class="h-1.5 w-1.5 rounded-full"
								:style="{ background: m.completed ? '#4ade80' : '#fbbf24' }"
							></span>
							<span v-if="milestonesFor(d.dateStr).length > 3" class="text-[8px] ml-0.5" :style="dayIndex === wi*7+di ? 'color:rgba(255,255,255,0.7)' : 'color:var(--portal-subtle)'">
								+{{ milestonesFor(d.dateStr).length - 3 }}
							</span>
						</div>
					</button>
				</div>
			</div>

			<!-- Selected day timeline -->
			<div class="portal-card-strong overflow-hidden">
				<div class="px-4 py-3 border-b border-[color:var(--portal-border)] flex items-center justify-between">
					<h3 class="text-sm font-semibold flex items-center gap-2" style="color:var(--portal-text);">
						<FeatherIcon name="clock" class="h-4 w-4" style="color:var(--portal-accent);"/>
						{{ selectedDay?.dayName }}, {{ selectedDay?.month }} {{ selectedDay?.dayNum }}
						<span v-if="selectedDay?.dateStr === todayStr" class="text-[10px] font-bold px-2 py-0.5 rounded-full" style="background:var(--portal-accent);color:#fff;">TODAY</span>
					</h3>
					<span class="text-xs" style="color:var(--portal-muted);">{{ dayMilestones.length }} milestones</span>
				</div>

				<div v-if="loading" class="p-6 text-center text-sm" style="color:var(--portal-muted);">Loading…</div>
				<div v-else class="relative" style="height:500px;">
					<div v-for="h in HOURS" :key="h" class="absolute left-0 right-0 border-b" style="border-color:var(--portal-border);" :style="{ top: `${((h-7)/12)*100}%` }">
						<span class="inline-block w-14 text-[10px] text-right pr-3 -mt-2" style="color:var(--portal-subtle);">{{ h }}:00</span>
					</div>
					<div
						v-for="m in dayMilestones" :key="m.name"
						class="absolute left-16 right-4 cursor-pointer"
						:style="{ top: timePct(m.starts_on) + '%', transform: 'translateY(-50%)' }"
					>
						<div v-if="editingId === m.name" class="bg-white rounded-lg p-2 shadow-lg border border-amber-200 relative z-20">
							<input v-model="editForm.title" class="w-full text-xs px-2 py-1 border rounded mb-1" />
							<div class="flex gap-1">
								<input v-model="editForm.time" type="time" class="text-xs px-1 py-0.5 border rounded" />
								<button class="text-[10px] px-2 py-0.5 bg-green-500 text-white rounded" @click="saveEdit(m)">Save</button>
								<button class="text-[10px] px-2 py-0.5 bg-gray-200 rounded" @click="cancelEdit">Cancel</button>
							</div>
						</div>
						<div
							v-else
							class="flex items-center gap-3 p-3 rounded-xl border transition hover:shadow-md"
							:class="m.completed ? 'bg-green-50 border-green-200' : 'border-[color:var(--portal-border)]'"
							style="background:var(--portal-surface);"
						>
							<button class="flex-shrink-0" @click="toggleMilestone(m)">
								<FeatherIcon :name="m.completed ? 'check-circle' : 'circle'" class="h-5 w-5" :style="{ color: m.completed ? '#22c55e' : m.color }" />
							</button>
							<div class="flex-1 min-w-0 cursor-pointer" @click="startEdit(m)">
								<div class="text-sm font-semibold truncate" :class="m.completed ? 'line-through text-gray-400' : ''" style="color:var(--portal-text);">{{ m.subject }}</div>
								<div class="text-[11px]" style="color:var(--portal-muted);">
									{{ m.starts_on?.slice(11,16) }}
									<span v-if="projectName(m.project)"> · {{ projectName(m.project) }}</span>
								</div>
							</div>
							<button class="flex-shrink-0 text-gray-300 hover:text-red-500" @click="removeMilestone(m)">
								<FeatherIcon name="x" class="h-4 w-4" />
							</button>
						</div>
					</div>
					<div v-if="!dayMilestones.length" class="absolute left-16 right-4 top-1/2 -translate-y-1/2 text-center text-sm" style="color:var(--portal-muted);">
						No milestones for this day.
					</div>
				</div>
			</div>

		</div>

		<!-- Add Milestone Modal -->
		<Teleport to="body">
			<div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeAdd">
				<div class="w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
					<div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
						<h2 class="text-lg font-bold" style="color:var(--portal-text);">Add Milestone</h2>
						<button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeAdd">
							<FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
						</button>
					</div>
					<div class="px-6 py-5 space-y-4">
						<p class="text-xs" style="color:var(--portal-muted);">For {{ selectedDay?.dayName }}, {{ selectedDay?.month }} {{ selectedDay?.dayNum }}</p>
						<div>
							<label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Title</label>
							<input v-model="form.title" type="text" class="portal-input w-full" placeholder="e.g. Client site visit" />
						</div>
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Time</label>
								<input v-model="form.time" type="time" class="portal-input w-full" />
							</div>
							<div>
								<label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Color</label>
								<input v-model="form.color" type="color" class="portal-input w-full h-[38px]" />
							</div>
						</div>
						<div>
							<label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Project (optional)</label>
							<select v-model="form.project" class="portal-input w-full">
								<option value="">— None —</option>
								<option v-for="p in filteredProjects" :key="p.name" :value="p.name">{{ p.project_name }}</option>
							</select>
						</div>
						<p v-if="addError" class="text-xs text-red-600">{{ addError }}</p>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-[color:var(--portal-border)]">
						<button class="portal-btn portal-btn-ghost" @click="closeAdd">Cancel</button>
						<button class="portal-btn portal-btn-primary" :disabled="saving" @click="submitAdd">{{ saving ? "Saving…" : "Add Milestone" }}</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
