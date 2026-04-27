<script setup>
import { ref, onMounted, inject, computed } from "vue";
import { call } from "@/api";
import { useRouter } from "vue-router";
import { FeatherIcon } from "frappe-ui";

const router = useRouter();
const loading = ref(true);
const board = ref({ columns: [], field: "" });
const stageSaving = ref("");
const err = ref("");

const portalCapabilities = inject("portalCapabilities", ref({}));
const manageable = computed(() => new Set(portalCapabilities.value?.manageable_project_names || []));

onMounted(async () => {
	try {
		board.value = await call({ method: "portal_app.api.projects.kanban_board" });
	} catch (e) {
		console.error(e);
	} finally {
		loading.value = false;
	}
});

function canEditProject(name) {
	return manageable.value.has(name);
}

function stagePillClass(stage) {
	const s = String(stage || "").toLowerCase();
	if (s.includes("done") || s.includes("completed")) return "portal-pill-success";
	if (s.includes("review")) return "portal-pill-warning";
	if (s.includes("hold")) return "portal-pill-warning";
	if (s.includes("active") || s.includes("working") || s.includes("open")) return "portal-pill-accent";
	if (s.includes("cancel")) return "portal-pill-danger";
	return "portal-pill-muted";
}

function stageRailColor(stage) {
	const s = String(stage || "").toLowerCase();
	if (s.includes("done") || s.includes("completed")) return "linear-gradient(180deg, #10b981, #059669)";
	if (s.includes("review")) return "linear-gradient(180deg, #f59e0b, #d97706)";
	if (s.includes("hold")) return "linear-gradient(180deg, #fb923c, #ea580c)";
	if (s.includes("active") || s.includes("working") || s.includes("open")) return "linear-gradient(180deg, #4f46e5, #38bdf8)";
	if (s.includes("cancel")) return "linear-gradient(180deg, #ef4444, #dc2626)";
	return "linear-gradient(180deg, #94a3b8, #64748b)";
}

async function updateStage(projectName, stage) {
	if (!canEditProject(projectName)) return;
	stageSaving.value = projectName;
	err.value = "";
	try {
		await call({
			method: "portal_app.api.projects.set_project_stage",
			type: "POST",
			args: { project: projectName, stage },
		});
		board.value = await call({ method: "portal_app.api.projects.kanban_board" });
	} catch (e) {
		console.error(e);
		err.value = e?.responseBody?.message || "Could not update stage.";
	} finally {
		stageSaving.value = "";
	}
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative">
					<span class="portal-pill portal-pill-accent">
						<FeatherIcon name="trello" class="h-3 w-3" />
						Kanban
					</span>
					<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">Project board</h1>
					<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
						Visual lifecycle tracking. Managers can update a project's stage right from each card.
					</p>
				</div>
			</div>

			<div v-if="loading" class="portal-card-strong flex items-center justify-center gap-2 p-10 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading board…
			</div>

			<div v-else class="flex gap-4 overflow-x-auto pb-4">
				<div
					v-for="col in board.columns"
					:key="col.stage"
					class="portal-card-strong w-80 shrink-0 overflow-hidden p-0"
				>
					<div
						class="relative flex items-center justify-between gap-2 px-3 py-3"
						style="background: var(--portal-bg-dim);"
					>
						<span
							class="absolute left-0 top-0 bottom-0 w-1"
							:style="{ background: stageRailColor(col.stage) }"
						></span>
						<span class="ml-2 portal-pill" :class="stagePillClass(col.stage)">
							{{ col.stage }}
						</span>
						<span class="text-xs font-semibold text-[color:var(--portal-muted)]">{{ col.projects.length }}</span>
					</div>
					<div class="space-y-2 p-3">
						<div
							v-for="p in col.projects"
							:key="p.name"
							class="cursor-pointer rounded-xl border border-[color:var(--portal-border)] bg-white p-3 text-sm transition hover:border-[color:var(--portal-accent)] hover:shadow-md"
							@click="router.push('/projects/' + encodeURIComponent(p.name))"
						>
							<div class="flex items-start justify-between gap-2">
								<div class="min-w-0">
									<div class="text-[10px] font-semibold uppercase tracking-wider text-[color:var(--portal-subtle)]">
										{{ p.portal_project_code || p.name }}
									</div>
									<p class="mt-0.5 truncate font-medium text-[color:var(--portal-text)]">
										{{ p.project_name }}
									</p>
									<p class="mt-0.5 truncate text-xs text-[color:var(--portal-muted)]">
										<FeatherIcon name="user" class="mr-1 inline h-3 w-3" />{{ p.customer || "No client" }}
									</p>
								</div>
								<FeatherIcon
									name="arrow-up-right"
									class="h-4 w-4 shrink-0 text-[color:var(--portal-muted)]"
								/>
							</div>
							<div v-if="canEditProject(p.name)" class="mt-3 border-t border-[color:var(--portal-border)] pt-2.5" @click.stop>
								<label class="portal-section-title mb-1 block">Update stage</label>
								<select
									class="portal-input py-1.5 text-xs"
									:value="col.stage"
									:disabled="stageSaving === p.name"
									@change="updateStage(p.name, $event.target.value)"
								>
									<option
										v-for="x in board.columns.map((c) => c.stage)"
										:key="x"
										:value="x"
									>
										{{ x }}
									</option>
								</select>
							</div>
						</div>
						<div
							v-if="!col.projects.length"
							class="rounded-xl border border-dashed border-[color:var(--portal-border-strong)] py-6 text-center text-xs text-[color:var(--portal-muted)]"
						>
							Empty
						</div>
					</div>
				</div>
				<div
					v-if="!board.columns.length"
					class="portal-card-strong w-full p-10 text-center text-[color:var(--portal-muted)]"
				>
					No projects yet.
				</div>
			</div>
			<div v-if="err" class="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
				{{ err }}
			</div>
		</div>
	</div>
</template>
