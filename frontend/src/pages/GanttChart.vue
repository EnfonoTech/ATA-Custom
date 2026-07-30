<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { FeatherIcon } from "frappe-ui";
import { call } from "@/api";

const loading      = ref(true);
const teams        = ref([]);
const unassigned   = ref([]);
const officeList   = ref(["ALL"]);
const officeFilter = ref("ALL");
const teamOptions  = ref([]);
const teamFilter   = ref("");
const viewMode     = ref("year"); // "year" | "quarter" | "month"

const PALETTE_SOLID = ["#C9A84C", "#185FA5", "#276749", "#9b5de5", "#f15bb5", "#00bbf9", "#e63946"];

function officeIndex(office) {
	const idx = officeList.value.indexOf(office);
	return idx > 0 ? (idx - 1) % PALETTE_SOLID.length : PALETTE_SOLID.length - 1;
}
function teamColor(office) {
	return PALETTE_SOLID[officeIndex(office)] ?? "#6b7280";
}

async function load() {
	loading.value = true;
	try {
		const args = {};
		if (officeFilter.value !== "ALL") args.office = officeFilter.value;
		if (teamFilter.value) args.team = teamFilter.value;

		const [data, offices] = await Promise.all([
			call({ method: "portal_app.api.gantt.get_gantt_data", args }),
			officeList.value.length > 1 ? Promise.resolve(null) : call({ method: "portal_app.api.teams.get_offices" }),
		]);
		teams.value = data?.teams || [];
		unassigned.value = data?.unassigned || [];
		if (Array.isArray(offices) && offices.length) {
			officeList.value = ["ALL", ...offices];
		}
		if (!teamOptions.value.length) {
			teamOptions.value = teams.value.map((t) => ({ name: t.name, label: t.department_name }));
		}
	} catch (e) {
		console.error("gantt data error", e);
	} finally {
		loading.value = false;
	}
}

onMounted(load);
watch([officeFilter, teamFilter], load);

const totalProjects = computed(() => teams.value.reduce((s, t) => s + t.projects.length, 0) + unassigned.value.length);
const totalMilestones = computed(() =>
	teams.value.reduce((s, t) => s + t.projects.filter((p) => p.portal_upcoming_milestone).length, 0) +
	unassigned.value.filter((p) => p.portal_upcoming_milestone).length,
);

// ── Timeline window (Full Year / Quarterly / Monthly) ──────────────────────
const today = new Date();
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const visibleMonths = computed(() => {
	const year = today.getFullYear();
	if (viewMode.value === "month") {
		return [{ year, month: today.getMonth() }];
	}
	if (viewMode.value === "quarter") {
		const qStart = Math.floor(today.getMonth() / 3) * 3;
		return [0, 1, 2].map((i) => ({ year, month: qStart + i }));
	}
	return Array.from({ length: 12 }, (_, i) => ({ year, month: i }));
});

const windowStart = computed(() => {
	const m = visibleMonths.value[0];
	return new Date(m.year, m.month, 1);
});
const windowEnd = computed(() => {
	const m = visibleMonths.value[visibleMonths.value.length - 1];
	return new Date(m.year, m.month + 1, 0, 23, 59, 59);
});
const windowSpanMs = computed(() => windowEnd.value.getTime() - windowStart.value.getTime());

function pct(date) {
	return ((date.getTime() - windowStart.value.getTime()) / windowSpanMs.value) * 100;
}

const todayPct = computed(() => {
	const p = pct(today);
	return p >= 0 && p <= 100 ? p : null;
});

function parseDate(s) {
	if (!s) return null;
	const d = new Date(String(s).replace(" ", "T"));
	return Number.isNaN(d.getTime()) ? null : d;
}

function fmtMilestoneDate(s) {
	const d = parseDate(s);
	if (!d) return "";
	return d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function barStyle(p) {
	let start = parseDate(p.expected_start_date);
	let end = parseDate(p.expected_end_date);
	if (!start && !end) return null;
	if (!start) start = new Date(end);
	if (!end) end = new Date(start);
	if (end < start) end = start;

	const clampedStart = start < windowStart.value ? windowStart.value : start;
	const clampedEnd = end > windowEnd.value ? windowEnd.value : end;
	if (clampedEnd < windowStart.value || clampedStart > windowEnd.value) return null;

	const left = Math.max(0, pct(clampedStart));
	const right = Math.min(100, pct(clampedEnd));
	const width = Math.max(right - left, 1.2);
	return { left: `${left}%`, width: `${width}%` };
}

function progressColor(pct_) {
	const n = Number(pct_ || 0);
	if (n >= 80) return "#10B981";
	if (n >= 40) return "#185FA5";
	return "#F59E0B";
}

function statusPillClass(s) {
	const t = String(s || "").toLowerCase();
	if (t === "completed") return "portal-pill-success";
	if (t === "cancelled") return "portal-pill-danger";
	if (t === "open") return "portal-pill-accent";
	return "portal-pill-muted";
}

function printGantt() {
	window.print();
}

// ── Add / Edit Milestone — a text label (portal_upcoming_milestone) plus the
// actual date it falls on (portal_milestone_date), both saved on the Project.
// The date is what positions the flag on the timeline below — without it the
// flag has nowhere real to sit, so it's required. ──────────────────────────
const milestoneProject = ref(null);
const milestoneText    = ref("");
const milestoneDate    = ref("");
const milestoneSaving  = ref(false);
const milestoneError   = ref("");

function openMilestone(p) {
	milestoneProject.value = p;
	milestoneText.value = p.portal_upcoming_milestone || "";
	milestoneDate.value = p.portal_milestone_date || "";
	milestoneError.value = "";
}
function closeMilestone() { milestoneProject.value = null; }

async function saveMilestone() {
	if (!milestoneProject.value) return;
	if (milestoneText.value.trim() && !milestoneDate.value) {
		milestoneError.value = "Pick the date this milestone falls on.";
		return;
	}
	milestoneSaving.value = true;
	milestoneError.value = "";
	try {
		await call({
			method: "portal_app.api.projects.update_project",
			type: "POST",
			args: {
				project: milestoneProject.value.name,
				portal_upcoming_milestone: milestoneText.value.trim(),
				portal_milestone_date: milestoneText.value.trim() ? milestoneDate.value : "",
			},
		});
		milestoneProject.value.portal_upcoming_milestone = milestoneText.value.trim();
		milestoneProject.value.portal_milestone_date = milestoneText.value.trim() ? milestoneDate.value : "";
		closeMilestone();
	} catch (e) {
		const body = e?.responseBody;
		milestoneError.value = body?.message || body?.exc || "Could not save milestone.";
	} finally {
		milestoneSaving.value = false;
	}
}

// Real position on the timeline for a project's milestone flag — falls back to
// the bar's end (old behaviour) only for rows saved before a date existed.
function milestoneFlagStyle(p) {
	const d = parseDate(p.portal_milestone_date);
	if (d) {
		const p_ = pct(d);
		if (p_ < 0 || p_ > 100) return null;
		return { left: `calc(${p_}% - 6px)` };
	}
	const bar = barStyle(p);
	if (!bar) return null;
	return { left: `calc(${bar.left} + ${bar.width} - 6px)` };
}

// All projects across every team + unassigned, for the header "+ Milestone" project picker.
const allProjectsFlat = computed(() => [
	...teams.value.flatMap((t) => t.projects),
	...unassigned.value,
]);
const milestonePickerOpen = ref(false);
function openMilestonePicker() {
	if (!allProjectsFlat.value.length) return;
	milestonePickerOpen.value = true;
}
function pickProjectForMilestone(p) {
	milestonePickerOpen.value = false;
	openMilestone(p);
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-7xl space-y-5">

			<div class="print-title">Gantt Chart &amp; Milestones</div>

			<!-- Header -->
			<div class="portal-hero portal-anim-in">
				<div class="flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="bar-chart-2" class="h-3 w-3" />
							Timeline
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							Gantt Chart &amp; Milestones
						</h1>
						<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
							Project timeline by team · {{ totalProjects }} projects · {{ totalMilestones }} milestones
						</p>
					</div>

					<div class="flex flex-wrap items-center gap-2">
						<div class="inline-flex rounded-xl border border-[color:var(--portal-border)] p-0.5 shadow-sm" style="background:var(--portal-surface)">
							<button
								v-for="v in [['year','Full Year'],['quarter','Quarterly'],['month','Monthly']]" :key="v[0]"
								type="button"
								class="rounded-lg px-3 py-1.5 text-xs font-semibold transition"
								:style="viewMode === v[0] ? 'background:var(--portal-accent);color:#fff;' : 'color:var(--portal-muted);'"
								@click="viewMode = v[0]"
							>{{ v[1] }}</button>
						</div>
						<select v-model="teamFilter" class="portal-input text-sm">
							<option value="">All Teams</option>
							<option v-for="t in teamOptions" :key="t.name" :value="t.name">{{ t.label }}</option>
						</select>
						<button class="portal-btn portal-btn-ghost" @click="printGantt">
							<FeatherIcon name="printer" class="h-4 w-4" />
							Print
						</button>
						<button class="portal-btn portal-btn-primary" @click="openMilestonePicker">
							<FeatherIcon name="flag" class="h-4 w-4" />
							Milestone
						</button>
					</div>
				</div>

				<div class="mt-3 inline-flex rounded-xl border border-[color:var(--portal-border)] p-0.5 shadow-sm" style="background:var(--portal-surface)">
					<button
						v-for="o in officeList" :key="o"
						type="button"
						class="rounded-lg px-3 py-1.5 text-xs font-semibold transition"
						:style="officeFilter === o ? 'background:var(--portal-accent);color:#fff;' : 'color:var(--portal-muted);'"
						@click="officeFilter = o"
					>{{ o }}</button>
				</div>
			</div>

			<!-- Loading -->
			<div v-if="loading" class="flex items-center gap-2 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading timeline…
			</div>

			<!-- Teams -->
			<div v-else class="space-y-5">
				<div v-for="t in teams" :key="t.name" class="portal-card-strong overflow-hidden">
					<!-- Team header -->
					<div class="flex items-center justify-between gap-3 px-4 py-3" :style="{ background: teamColor(t.office) + '22', borderLeft: '4px solid ' + teamColor(t.office) }">
						<div class="flex items-center gap-2 min-w-0">
							<div class="h-7 w-7 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0" :style="{ background: teamColor(t.office) }">
								<FeatherIcon name="users" class="h-3.5 w-3.5" />
							</div>
							<span class="font-semibold text-sm truncate" style="color:var(--portal-text);">{{ t.department_name }}</span>
							<span class="portal-pill portal-pill-muted flex-shrink-0">{{ t.projects.length }} projects</span>
						</div>
					</div>

					<!-- Month grid header -->
					<div class="grid text-[10px] font-semibold uppercase tracking-wider border-b border-[color:var(--portal-border)]" style="grid-template-columns: 220px 1fr;">
						<div></div>
						<div class="relative grid" :style="{ gridTemplateColumns: `repeat(${visibleMonths.length}, 1fr)` }">
							<div v-for="m in visibleMonths" :key="m.year + '-' + m.month" class="px-2 py-2 text-center border-l border-[color:var(--portal-border)]" style="color:var(--portal-muted);">
								{{ MONTH_NAMES[m.month] }} {{ m.year }}
							</div>
						</div>
					</div>

					<!-- Rows -->
					<div class="divide-y divide-[color:var(--portal-border)]">
						<div v-for="p in t.projects" :key="p.name" class="grid items-center" style="grid-template-columns: 220px 1fr;">
							<div class="px-3 py-2.5 min-w-0 flex items-center gap-2">
								<div class="min-w-0 flex-1">
									<div class="text-xs font-semibold truncate" style="color:var(--portal-text);">{{ p.project_name }}</div>
									<span class="portal-pill text-[10px] mt-0.5" :class="statusPillClass(p.status)">{{ p.status }}</span>
									<span v-if="p.portal_phase" class="portal-pill portal-pill-accent text-[10px] mt-0.5 ml-1">{{ p.portal_phase }}</span>
								</div>
								<button
									type="button"
									class="h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 transition hover:bg-black/5"
									:title="p.portal_upcoming_milestone ? 'Edit milestone' : 'Add milestone'"
									@click="openMilestone(p)"
								>
									<FeatherIcon name="flag" class="h-3.5 w-3.5" :style="{ color: p.portal_upcoming_milestone ? '#ef4444' : 'var(--portal-subtle)' }" />
								</button>
							</div>
							<div class="relative h-9 border-l border-[color:var(--portal-border)]" style="background-image: linear-gradient(to right, var(--portal-border) 1px, transparent 1px);" :style="{ backgroundSize: `${100/visibleMonths.length}% 100%` }">
								<!-- today line -->
								<div v-if="todayPct !== null" class="absolute top-0 bottom-0 w-px bg-red-500 z-10" :style="{ left: todayPct + '%' }"></div>
								<!-- bar -->
								<div
									v-if="barStyle(p)"
									class="absolute top-1.5 h-6 rounded-md overflow-hidden"
									:style="{ ...barStyle(p), background: 'rgba(128,128,128,0.18)' }"
									:title="p.project_name + ' — ' + Math.round(p.percent_complete || 0) + '%'"
								>
									<div class="h-full rounded-md" :style="{ width: (p.percent_complete || 0) + '%', background: progressColor(p.percent_complete) }"></div>
									<span class="absolute inset-0 flex items-center px-2 text-[10px] font-semibold text-white truncate" style="mix-blend-mode: difference;">
										{{ Math.round(p.percent_complete || 0) }}%
									</span>
								</div>
								<FeatherIcon
									v-if="p.portal_upcoming_milestone && milestoneFlagStyle(p)"
									name="flag"
									class="absolute top-1 h-3.5 w-3.5 text-red-500"
									:style="milestoneFlagStyle(p)"
									:title="'Milestone: ' + p.portal_upcoming_milestone + (p.portal_milestone_date ? ' — ' + fmtMilestoneDate(p.portal_milestone_date) : '')"
								/>
								<span v-if="!barStyle(p)" class="absolute inset-0 flex items-center px-2 text-[10px]" style="color:var(--portal-subtle);">No dates set</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Unassigned -->
				<div v-if="unassigned.length" class="portal-card-strong overflow-hidden">
					<div class="px-4 py-3 border-l-4 border-gray-400" style="background:rgba(128,128,128,0.1);">
						<span class="font-semibold text-sm" style="color:var(--portal-text);">Unassigned to a team</span>
						<span class="portal-pill portal-pill-muted ml-2">{{ unassigned.length }} projects</span>
					</div>
					<div class="divide-y divide-[color:var(--portal-border)]">
						<div v-for="p in unassigned" :key="p.name" class="grid items-center" style="grid-template-columns: 220px 1fr;">
							<div class="px-3 py-2.5 min-w-0 flex items-center gap-2">
								<div class="min-w-0 flex-1">
									<div class="text-xs font-semibold truncate" style="color:var(--portal-text);">{{ p.project_name }}</div>
									<span class="portal-pill text-[10px] mt-0.5" :class="statusPillClass(p.status)">{{ p.status }}</span>
									<span v-if="p.portal_phase" class="portal-pill portal-pill-accent text-[10px] mt-0.5 ml-1">{{ p.portal_phase }}</span>
								</div>
								<button
									type="button"
									class="h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0 transition hover:bg-black/5"
									:title="p.portal_upcoming_milestone ? 'Edit milestone' : 'Add milestone'"
									@click="openMilestone(p)"
								>
									<FeatherIcon name="flag" class="h-3.5 w-3.5" :style="{ color: p.portal_upcoming_milestone ? '#ef4444' : 'var(--portal-subtle)' }" />
								</button>
							</div>
							<div class="relative h-9 border-l border-[color:var(--portal-border)]">
								<div v-if="todayPct !== null" class="absolute top-0 bottom-0 w-px bg-red-500 z-10" :style="{ left: todayPct + '%' }"></div>
								<div
									v-if="barStyle(p)"
									class="absolute top-1.5 h-6 rounded-md overflow-hidden"
									:style="{ ...barStyle(p), background: 'rgba(128,128,128,0.18)' }"
								>
									<div class="h-full rounded-md" :style="{ width: (p.percent_complete || 0) + '%', background: progressColor(p.percent_complete) }"></div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div v-if="!teams.length && !unassigned.length" class="portal-card-strong p-10 text-center" style="color:var(--portal-muted);">
					No projects to show for this filter.
				</div>
			</div>

		</div>
	</div>

	<!-- Pick a project to add a milestone to (from the header "+ Milestone" button) -->
	<Teleport to="body">
		<div
			v-if="milestonePickerOpen"
			class="fixed inset-0 z-[60] flex items-center justify-center px-4"
			role="dialog"
			aria-modal="true"
		>
			<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="milestonePickerOpen = false"></div>
			<div class="relative z-10 w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden portal-anim-in" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
				<div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--portal-border);">
					<h2 class="text-sm font-semibold" style="color:var(--portal-text);">Pick a project</h2>
					<button class="h-7 w-7 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="milestonePickerOpen = false">
						<FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
					</button>
				</div>
				<div class="max-h-[50vh] overflow-y-auto p-2">
					<button
						v-for="p in allProjectsFlat" :key="p.name"
						type="button"
						class="w-full flex items-center justify-between gap-2 rounded-xl px-3 py-2.5 text-left text-sm transition hover:bg-[color:var(--portal-surface-alt)]"
						style="color:var(--portal-text);"
						@click="pickProjectForMilestone(p)"
					>
						<span class="truncate">{{ p.project_name }}</span>
						<FeatherIcon name="flag" class="h-3.5 w-3.5 shrink-0" :style="{ color: p.portal_upcoming_milestone ? '#ef4444' : 'var(--portal-subtle)' }" />
					</button>
				</div>
			</div>
		</div>
	</Teleport>

	<!-- Add / Edit Milestone Modal -->
	<Teleport to="body">
		<div
			v-if="milestoneProject"
			class="fixed inset-0 z-[60] flex items-center justify-center px-4"
			role="dialog"
			aria-modal="true"
		>
			<div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" @click="closeMilestone"></div>
			<div class="relative z-10 w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden portal-anim-in" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
				<div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--portal-border);">
					<div class="min-w-0">
						<h2 class="text-sm font-semibold" style="color:var(--portal-text);">Milestone</h2>
						<p class="text-xs mt-0.5 truncate" style="color:var(--portal-muted);">{{ milestoneProject.project_name }}</p>
					</div>
					<button class="h-7 w-7 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeMilestone">
						<FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
					</button>
				</div>

				<div class="px-5 py-4 space-y-3">
					<input
						v-model="milestoneText"
						type="text"
						placeholder="e.g. Client presentation"
						class="portal-input w-full"
						maxlength="140"
						@keyup.enter="saveMilestone"
					/>
					<div>
						<label class="block text-xs font-medium mb-1" style="color:var(--portal-muted);">Milestone date</label>
						<input v-model="milestoneDate" type="date" class="portal-input w-full" @keyup.enter="saveMilestone"/>
						<p class="text-[11px] mt-1" style="color:var(--portal-subtle);">This is where the flag lands on the Gantt timeline.</p>
					</div>
					<p v-if="milestoneError" class="text-xs text-red-600">{{ milestoneError }}</p>
				</div>
				<div class="flex items-center justify-end gap-3 px-5 py-4 border-t" style="border-color:var(--portal-border);">
					<button class="portal-btn portal-btn-ghost" @click="closeMilestone">Cancel</button>
					<button class="portal-btn portal-btn-primary" :disabled="milestoneSaving" @click="saveMilestone">
						{{ milestoneSaving ? "Saving…" : "Save" }}
					</button>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<style>
.print-title { display: none; }

@media print {
	* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

	/* Hide sidebar/nav/header (layout shell) */
	nav, aside, header, footer { display: none !important; }

	/* Hide filters/view-toggle/print button — replaced by a plain print title */
	.portal-hero { display: none !important; }
	.print-title {
		display: block !important;
		font-size: 20px;
		font-weight: 700;
		color: #111827;
		padding: 4px 0 14px;
		font-family: system-ui, sans-serif;
	}

	body, html { margin: 0 !important; padding: 0 !important; background: #fff !important; }
	.h-full { height: auto !important; overflow: visible !important; }
	.overflow-auto { overflow: visible !important; }
	.p-6 { padding: 16px !important; }
	.mx-auto, .max-w-7xl { max-width: 100% !important; }
	.space-y-5 > * + * { margin-top: 10px !important; }

	.portal-card-strong {
		break-inside: avoid;
		box-shadow: none !important;
		border: 1px solid #e5e7eb !important;
	}
}
</style>
