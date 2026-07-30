<script setup>
import { ref, computed, onMounted, watch, inject } from "vue";
import { FeatherIcon } from "frappe-ui";
import { call } from "@/api";

const portalCapabilities = inject("portalCapabilities", ref({}));
const isManager = computed(() => !!portalCapabilities.value?.is_manager);

const loading    = ref(true);
const tasks      = ref([]);
const weekOffset = ref(0);
const dayIndex   = ref(0);

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

async function loadTasks() {
	loading.value = true;
	try {
		tasks.value = await call({
			method: "portal_app.api.daily_task.get_tasks",
			args: { start_date: days.value[0].dateStr, end_date: days.value[27].dateStr },
		});
	} catch (e) {
		console.error(e);
		tasks.value = [];
	} finally {
		loading.value = false;
	}
}

onMounted(async () => {
	dayIndex.value = days.value.findIndex((d) => d.dateStr === todayStr);
	if (dayIndex.value < 0) dayIndex.value = 0;
	await loadTasks();
});

watch(weekOffset, () => {
	dayIndex.value = 0;
	loadTasks();
});

function tasksFor(dateStr) {
	return tasks.value.filter((t) => t.starts_on?.slice(0, 10) === dateStr);
}
const dayTasks = computed(() => tasksFor(selectedDay.value?.dateStr));
const completedCount = computed(() => dayTasks.value.filter((t) => t.completed).length);

function timePct(startsOn) {
	const t = startsOn?.slice(11, 16) || "07:00";
	const [h, m] = t.split(":").map(Number);
	const hourFrac = h + m / 60;
	return Math.min(100, Math.max(0, ((hourFrac - 7) / 12) * 100));
}

// ── Assignee search combobox (managers only — pick who the task is for) ────
const userQuery    = ref("");
const userResults  = ref([]);
const userSelected = ref(null); // { email, full_name }
const userOpen     = ref(false);
let userDebounce;
async function onUserInput() {
	userSelected.value = null;
	clearTimeout(userDebounce);
	userDebounce = setTimeout(async () => {
		if (!userQuery.value.trim()) { userResults.value = []; userOpen.value = false; return; }
		try {
			userResults.value = await call({ method: "portal_app.api.projects.search_assignable_users", args: { query: userQuery.value } });
			userOpen.value = !!userResults.value.length;
		} catch { userResults.value = []; }
	}, 250);
}
function selectUser(u) {
	userSelected.value = u;
	userQuery.value = u.full_name || u.email;
	userOpen.value = false;
}
function clearUser() { userQuery.value = ""; userSelected.value = null; userResults.value = []; userOpen.value = false; }
function blurUser() { setTimeout(() => { userOpen.value = false; }, 180); }
function initials(name) {
	return (name || "?").split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}

// ── Add / Edit / Toggle / Delete ────────────────────────────────────────────
const showAdd  = ref(false);
const saving   = ref(false);
const addError = ref("");
const form     = ref({ title: "", time: "09:00", color: "#185FA5" });

function openAdd() {
	addError.value = "";
	form.value = { title: "", time: "09:00", color: "#185FA5" };
	clearUser();
	showAdd.value = true;
}
function closeAdd() { showAdd.value = false; }

async function submitAdd() {
	if (!form.value.title.trim()) { addError.value = "Title is required."; return; }
	saving.value = true;
	addError.value = "";
	try {
		await call({
			method: "portal_app.api.daily_task.create_task",
			type: "POST",
			args: {
				title: form.value.title.trim(),
				date: selectedDay.value.dateStr,
				time: form.value.time,
				assigned_to: userSelected.value?.email || undefined,
				color: form.value.color,
			},
		});
		closeAdd();
		await loadTasks();
	} catch (e) {
		addError.value = apiErr(e);
	} finally {
		saving.value = false;
	}
}

async function toggleTask(t) {
	try {
		await call({ method: "portal_app.api.daily_task.toggle_task", type: "POST", args: { name: t.name } });
		t.completed = !t.completed;
	} catch (e) {
		console.error(e);
	}
}

const editingId = ref(null);
const editForm  = ref({ title: "", time: "" });

function startEdit(t) {
	editingId.value = t.name;
	editForm.value = { title: t.subject, time: t.starts_on?.slice(11, 16) || "09:00" };
}
function cancelEdit() { editingId.value = null; }

async function saveEdit(t) {
	try {
		await call({
			method: "portal_app.api.daily_task.update_task",
			type: "POST",
			args: { name: t.name, title: editForm.value.title, time: editForm.value.time },
		});
		editingId.value = null;
		await loadTasks();
	} catch (e) {
		console.error(e);
	}
}

async function removeTask(t) {
	try {
		await call({ method: "portal_app.api.daily_task.delete_task", type: "POST", args: { name: t.name } });
		await loadTasks();
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
							Daily Task
						</h1>
						<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
							Your personal reminders · {{ dayTasks.length }} tasks today · {{ completedCount }} completed
						</p>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						<button class="portal-btn portal-btn-primary" @click="openAdd">
							<FeatherIcon name="plus" class="h-4 w-4" />
							Task
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
						<div v-if="tasksFor(d.dateStr).length" class="flex justify-center gap-0.5 mt-1">
							<span
								v-for="t in tasksFor(d.dateStr).slice(0, 3)" :key="t.name"
								class="h-1.5 w-1.5 rounded-full"
								:style="{ background: t.completed ? '#4ade80' : '#fbbf24' }"
							></span>
							<span v-if="tasksFor(d.dateStr).length > 3" class="text-[8px] ml-0.5" :style="dayIndex === wi*7+di ? 'color:rgba(255,255,255,0.7)' : 'color:var(--portal-subtle)'">
								+{{ tasksFor(d.dateStr).length - 3 }}
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
					<span class="text-xs" style="color:var(--portal-muted);">{{ dayTasks.length }} tasks</span>
				</div>

				<div v-if="loading" class="p-6 text-center text-sm" style="color:var(--portal-muted);">Loading…</div>
				<div v-else class="relative" style="height:500px;">
					<div v-for="h in HOURS" :key="h" class="absolute left-0 right-0 border-b" style="border-color:var(--portal-border);" :style="{ top: `${((h-7)/12)*100}%` }">
						<span class="inline-block w-14 text-[10px] text-right pr-3 -mt-2" style="color:var(--portal-subtle);">{{ h }}:00</span>
					</div>
					<div
						v-for="t in dayTasks" :key="t.name"
						class="absolute left-16 right-4 cursor-pointer"
						:style="{ top: timePct(t.starts_on) + '%', transform: 'translateY(-50%)' }"
					>
						<div v-if="editingId === t.name" class="bg-white rounded-lg p-2 shadow-lg border border-amber-200 relative z-20">
							<input v-model="editForm.title" class="w-full text-xs px-2 py-1 border rounded mb-1" />
							<div class="flex gap-1">
								<input v-model="editForm.time" type="time" class="text-xs px-1 py-0.5 border rounded" />
								<button class="text-[10px] px-2 py-0.5 bg-green-500 text-white rounded" @click="saveEdit(t)">Save</button>
								<button class="text-[10px] px-2 py-0.5 bg-gray-200 rounded" @click="cancelEdit">Cancel</button>
							</div>
						</div>
						<div
							v-else
							class="flex items-center gap-3 p-3 rounded-xl border transition hover:shadow-md"
							:class="t.completed ? 'bg-green-50 border-green-200' : 'border-[color:var(--portal-border)]'"
							style="background:var(--portal-surface);"
						>
							<button class="flex-shrink-0" @click="toggleTask(t)">
								<FeatherIcon :name="t.completed ? 'check-circle' : 'circle'" class="h-5 w-5" :style="{ color: t.completed ? '#22c55e' : t.color }" />
							</button>
							<div class="flex-1 min-w-0 cursor-pointer" @click="startEdit(t)">
								<div class="text-sm font-semibold truncate" :class="t.completed ? 'line-through text-gray-400' : ''" style="color:var(--portal-text);">{{ t.subject }}</div>
								<div class="text-[11px]" style="color:var(--portal-muted);">{{ t.starts_on?.slice(11,16) }}</div>
							</div>
							<button class="flex-shrink-0 text-gray-300 hover:text-red-500" @click="removeTask(t)">
								<FeatherIcon name="x" class="h-4 w-4" />
							</button>
						</div>
					</div>
					<div v-if="!dayTasks.length" class="absolute left-16 right-4 top-1/2 -translate-y-1/2 text-center text-sm" style="color:var(--portal-muted);">
						No tasks for this day.
					</div>
				</div>
			</div>

		</div>

		<!-- Add Task Modal -->
		<Teleport to="body">
			<div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeAdd">
				<div class="w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
					<div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
						<h2 class="text-lg font-bold" style="color:var(--portal-text);">Add Task</h2>
						<button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeAdd">
							<FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
						</button>
					</div>
					<div class="px-6 py-5 space-y-4">
						<p class="text-xs" style="color:var(--portal-muted);">For {{ selectedDay?.dayName }}, {{ selectedDay?.month }} {{ selectedDay?.dayNum }}</p>
						<div>
							<label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Title</label>
							<input v-model="form.title" type="text" class="portal-input w-full" placeholder="e.g. Submit drawings to client" />
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

						<!-- Assign to (managers only) -->
						<div v-if="isManager" class="relative">
							<label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Assign to (optional — defaults to you)</label>
							<div class="relative">
								<FeatherIcon name="user" class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[color:var(--portal-subtle)]" />
								<input
									v-model="userQuery"
									class="portal-input w-full pl-8 pr-8"
									placeholder="Search by name or email…"
									autocomplete="off"
									@input="onUserInput"
									@focus="onUserInput"
									@blur="blurUser"
								/>
								<button v-if="userQuery" type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" @click="clearUser">
									<FeatherIcon name="x" class="h-3.5 w-3.5" />
								</button>
							</div>
							<ul v-if="userOpen && userResults.length"
								class="absolute z-30 mt-1 w-full overflow-hidden rounded-xl border border-[color:var(--portal-border)] bg-white shadow-lg"
							>
								<li
									v-for="u in userResults" :key="u.email"
									class="flex cursor-pointer items-center gap-2.5 px-3 py-2 hover:bg-[color:var(--portal-accent-soft)]"
									@mousedown.prevent="selectUser(u)"
								>
									<div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
										 style="background:linear-gradient(135deg,var(--portal-accent),var(--portal-accent-strong))">
										{{ initials(u.full_name) }}
									</div>
									<div class="min-w-0">
										<div class="truncate text-xs font-semibold" style="color:var(--portal-text);">{{ u.full_name }}</div>
										<div class="truncate text-[10px]" style="color:var(--portal-muted);">{{ u.email }}</div>
									</div>
								</li>
							</ul>
						</div>

						<p v-if="addError" class="text-xs text-red-600">{{ addError }}</p>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-[color:var(--portal-border)]">
						<button class="portal-btn portal-btn-ghost" @click="closeAdd">Cancel</button>
						<button class="portal-btn portal-btn-primary" :disabled="saving" @click="submitAdd">{{ saving ? "Saving…" : "Add Task" }}</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
