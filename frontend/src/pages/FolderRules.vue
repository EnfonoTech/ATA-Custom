<script setup>
import { ref, onMounted, computed } from "vue";
import { call } from "@/api";
import { FeatherIcon } from "frappe-ui";

const rules        = ref([]);
const folderPaths  = ref([]);
const loading      = ref(true);
const savingIds    = ref(new Set());
const deletingIds  = ref(new Set());
const globalError  = ref("");

const FILE_CLASSIFICATIONS = [
	"Presentation Files",
	"Drawing / Layout Files",
	"3D Model Files",
	"Feasibility / Area Calculation Files",
	"Editable Design Source Files",
	"Rendering / Image Files",
	"Submission Files",
	"Uncategorized",
];

const MATCH_MODES = [
	{ value: "contains",    label: "contains" },
	{ value: "starts_with", label: "starts with" },
	{ value: "exact",       label: "exact" },
];

// Derive a deduplicated list of path segments useful as autocomplete hints
const pathSuggestions = computed(() => {
	const seen = new Set();
	const out  = [];
	for (const p of folderPaths.value) {
		const parts = String(p).split("/");
		for (const seg of parts) {
			const s = seg.trim();
			if (s && !seen.has(s)) { seen.add(s); out.push(s); }
		}
		if (!seen.has(p)) { seen.add(p); out.push(p); }
	}
	return out.sort();
});

const classificationColor = (cls) => {
	const map = {
		"Presentation Files": "bg-purple-100 text-purple-800 border-purple-200",
		"Drawing / Layout Files": "bg-blue-100 text-blue-800 border-blue-200",
		"3D Model Files": "bg-cyan-100 text-cyan-800 border-cyan-200",
		"Feasibility / Area Calculation Files": "bg-amber-100 text-amber-800 border-amber-200",
		"Editable Design Source Files": "bg-pink-100 text-pink-800 border-pink-200",
		"Rendering / Image Files": "bg-orange-100 text-orange-800 border-orange-200",
		"Submission Files": "bg-teal-100 text-teal-800 border-teal-200",
		"Uncategorized": "bg-gray-100 text-gray-700 border-gray-200",
	};
	return map[cls] || "bg-gray-100 text-gray-700 border-gray-200";
};

async function loadAll() {
	loading.value = true;
	try {
		const [rulesRes, pathsRes] = await Promise.all([
			call({ method: "portal_app.api.files.list_folder_route_rules" }),
			call({ method: "portal_app.api.files.list_folder_template_paths" }),
		]);
		rules.value = (rulesRes?.rules || []).map((r) => ({ ...r, _dirty: false }));
		folderPaths.value = pathsRes?.paths || [];
	} catch (e) {
		globalError.value = "Failed to load rules. " + (e?.message || "");
	} finally {
		loading.value = false;
	}
}
onMounted(loadAll);

function addRule() {
	rules.value.unshift({
		name: "",
		rule_name: "",
		file_classification: "Presentation Files",
		source_folder_pattern: "",
		source_match_mode: "contains",
		target_folder_pattern: "",
		target_match_mode: "contains",
		enabled: 1,
		_dirty: true,
		_new: true,
	});
}

function markDirty(rule) {
	rule._dirty = true;
}

async function saveRule(rule) {
	if (!rule.source_folder_pattern.trim()) { rule._err = "Source pattern is required."; return; }
	if (!rule.target_folder_pattern.trim()) { rule._err = "Target pattern is required."; return; }
	if (!rule.file_classification)          { rule._err = "File classification is required."; return; }
	rule._err = "";

	const id = rule.name || rule._tmpId || Math.random().toString(36).slice(2);
	if (!rule._tmpId && !rule.name) rule._tmpId = id;

	const nextSaving = new Set(savingIds.value);
	nextSaving.add(id);
	savingIds.value = nextSaving;

	try {
		const payload = {
			name: rule.name || "",
			rule_name: rule.rule_name || (rule.source_folder_pattern + " → " + rule.file_classification + " → " + rule.target_folder_pattern),
			file_classification: rule.file_classification,
			source_folder_pattern: rule.source_folder_pattern.trim(),
			source_match_mode: rule.source_match_mode || "contains",
			target_folder_pattern: rule.target_folder_pattern.trim(),
			target_match_mode: rule.target_match_mode || "contains",
			enabled: rule.enabled ? 1 : 0,
		};
		const res = await call({
			method: "portal_app.api.files.save_folder_route_rule",
			type: "POST",
			args: payload,
		});
		rule.name    = res.name || rule.name;
		rule._dirty  = false;
		rule._new    = false;
		if (!rule.rule_name) rule.rule_name = res.rule_name || "";
	} catch (e) {
		rule._err = (e?.responseBody?.message || e?.message || "Save failed.");
	} finally {
		const next = new Set(savingIds.value);
		next.delete(id);
		savingIds.value = next;
	}
}

async function toggleEnabled(rule) {
	rule.enabled = rule.enabled ? 0 : 1;
	if (rule.name) {
		await saveRule(rule);
	}
}

async function deleteRule(rule, idx) {
	if (!window.confirm(`Delete rule "${rule.rule_name || "this rule"}"?`)) return;

	if (rule.name) {
		const next = new Set(deletingIds.value);
		next.add(rule.name);
		deletingIds.value = next;
		try {
			await call({
				method: "portal_app.api.files.delete_folder_route_rule",
				type: "POST",
				args: { rule_name: rule.name },
			});
		} catch (e) {
			rule._err = e?.message || "Delete failed.";
			const n = new Set(deletingIds.value); n.delete(rule.name); deletingIds.value = n;
			return;
		}
		const n = new Set(deletingIds.value); n.delete(rule.name); deletingIds.value = n;
	}
	rules.value.splice(idx, 1);
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-4xl space-y-5">

			<!-- ── Header ── -->
			<div class="portal-hero portal-anim-in">
				<span class="portal-pill portal-pill-accent">
					<FeatherIcon name="git-merge" class="h-3 w-3" />
					Automation
				</span>
				<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
					Folder Routing Rules
				</h1>
				<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
					Define when files uploaded to a folder should be <strong>automatically mirrored</strong> to another folder based on file classification. Each rule is a pipeline: source → filter → target.
				</p>
			</div>

			<p v-if="globalError" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ globalError }}</p>

			<!-- ── Toolbar ── -->
			<div class="flex items-center justify-between">
				<p class="text-sm text-[color:var(--portal-muted)]">
					{{ rules.length }} rule{{ rules.length === 1 ? "" : "s" }} configured
				</p>
				<button class="portal-btn portal-btn-primary" @click="addRule">
					<FeatherIcon name="plus" class="h-4 w-4" />
					New rule
				</button>
			</div>

			<div v-if="loading" class="flex items-center gap-2 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading…
			</div>

			<!-- ── Rule cards ── -->
			<div v-else class="space-y-4">
				<div
					v-for="(rule, idx) in rules"
					:key="rule.name || rule._tmpId || idx"
					class="portal-card-strong overflow-hidden transition-all duration-200"
					:class="rule._new ? 'ring-2 ring-[color:var(--portal-accent)] ring-offset-1' : ''"
				>
					<!-- Top bar: enable toggle + rule name + delete -->
					<div class="flex items-center justify-between gap-3 border-b border-[color:var(--portal-border)] bg-[color:var(--portal-bg)] px-4 py-2.5">
						<!-- Enable toggle -->
						<button
							type="button"
							class="flex items-center gap-2 rounded-lg px-2 py-1 text-xs font-semibold transition"
							:class="rule.enabled ? 'text-emerald-700 hover:bg-emerald-50' : 'text-[color:var(--portal-muted)] hover:bg-gray-100'"
							@click="toggleEnabled(rule)"
						>
							<span
								class="inline-flex h-4 w-7 items-center rounded-full transition-colors"
								:class="rule.enabled ? 'bg-emerald-500' : 'bg-gray-300'"
							>
								<span
									class="h-3 w-3 rounded-full bg-white shadow transition-transform"
									:class="rule.enabled ? 'translate-x-3.5' : 'translate-x-0.5'"
								></span>
							</span>
							{{ rule.enabled ? "Enabled" : "Disabled" }}
						</button>

						<!-- Rule name (editable inline) -->
						<input
							v-model="rule.rule_name"
							type="text"
							class="min-w-0 flex-1 rounded-lg border-0 bg-transparent px-2 py-1 text-xs font-medium text-[color:var(--portal-text)] placeholder:text-[color:var(--portal-subtle)] focus:ring-1 focus:ring-[color:var(--portal-accent)]"
							placeholder="Rule description (auto-generated if blank)"
							@input="markDirty(rule)"
						/>

						<!-- Save button (shown when dirty) -->
						<button
							v-if="rule._dirty"
							type="button"
							class="portal-btn portal-btn-primary shrink-0 text-xs"
							:disabled="savingIds.has(rule.name || rule._tmpId)"
							@click="saveRule(rule)"
						>
							<span v-if="savingIds.has(rule.name || rule._tmpId)" class="flex items-center gap-1">
								<span class="h-3 w-3 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
								Saving…
							</span>
							<span v-else class="flex items-center gap-1">
								<FeatherIcon name="save" class="h-3.5 w-3.5" />
								Save
							</span>
						</button>

						<!-- Delete -->
						<button
							type="button"
							class="rounded-lg p-1.5 text-[color:var(--portal-muted)] transition hover:bg-red-50 hover:text-red-600"
							:disabled="deletingIds.has(rule.name)"
							title="Delete rule"
							@click="deleteRule(rule, idx)"
						>
							<FeatherIcon name="trash-2" class="h-4 w-4" />
						</button>
					</div>

					<!-- ── Pipeline flow ── -->
					<div class="flex flex-wrap items-stretch gap-0 sm:flex-nowrap">

						<!-- NODE 1: Source folder -->
						<div class="flex min-w-[170px] flex-1 flex-col gap-2 border-r border-[color:var(--portal-border)] p-4">
							<div class="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest text-[color:var(--portal-muted)]">
								<span class="flex h-5 w-5 items-center justify-center rounded-md bg-[color:var(--portal-accent)] text-white text-[10px] font-black">1</span>
								IF uploaded inside
							</div>
							<input
								v-model="rule.source_folder_pattern"
								type="text"
								:list="`src-dl-${idx}`"
								class="w-full rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2 text-sm font-medium text-[color:var(--portal-text)] placeholder:text-[color:var(--portal-subtle)] focus:border-[color:var(--portal-accent)] focus:outline-none focus:ring-1 focus:ring-[color:var(--portal-accent)]"
								placeholder="e.g. 01-CONCEPT STUDIES"
								@input="markDirty(rule)"
							/>
							<datalist :id="`src-dl-${idx}`">
								<option v-for="s in pathSuggestions" :key="s" :value="s" />
							</datalist>
							<select
								v-model="rule.source_match_mode"
								class="w-full rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-xs text-[color:var(--portal-muted)] focus:border-[color:var(--portal-accent)] focus:outline-none"
								@change="markDirty(rule)"
							>
								<option v-for="m in MATCH_MODES" :key="m.value" :value="m.value">Folder label {{ m.label }} pattern</option>
							</select>
						</div>

						<!-- Arrow -->
						<div class="hidden items-center justify-center px-1 sm:flex">
							<div class="flex flex-col items-center gap-0.5">
								<div class="h-px w-6 bg-[color:var(--portal-border)]"></div>
								<FeatherIcon name="chevron-right" class="h-4 w-4 text-[color:var(--portal-accent)]" />
								<div class="h-px w-6 bg-[color:var(--portal-border)]"></div>
							</div>
						</div>

						<!-- NODE 2: Classification filter -->
						<div class="flex min-w-[170px] flex-1 flex-col gap-2 border-r border-[color:var(--portal-border)] p-4">
							<div class="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest text-[color:var(--portal-muted)]">
								<span class="flex h-5 w-5 items-center justify-center rounded-md bg-indigo-500 text-white text-[10px] font-black">2</span>
								AND file type is
							</div>
							<select
								v-model="rule.file_classification"
								class="w-full rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2 text-sm font-medium text-[color:var(--portal-text)] focus:border-[color:var(--portal-accent)] focus:outline-none focus:ring-1 focus:ring-[color:var(--portal-accent)]"
								@change="markDirty(rule)"
							>
								<option value="">— Any classification —</option>
								<option v-for="cls in FILE_CLASSIFICATIONS" :key="cls" :value="cls">{{ cls }}</option>
							</select>
							<!-- Classification colour badge preview -->
							<span
								v-if="rule.file_classification"
								class="inline-flex w-fit items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold"
								:class="classificationColor(rule.file_classification)"
							>
								<FeatherIcon name="tag" class="h-2.5 w-2.5" />
								{{ rule.file_classification }}
							</span>
						</div>

						<!-- Arrow -->
						<div class="hidden items-center justify-center px-1 sm:flex">
							<div class="flex flex-col items-center gap-0.5">
								<div class="h-px w-6 bg-[color:var(--portal-border)]"></div>
								<FeatherIcon name="chevron-right" class="h-4 w-4 text-[color:var(--portal-accent)]" />
								<div class="h-px w-6 bg-[color:var(--portal-border)]"></div>
							</div>
						</div>

						<!-- NODE 3: Target folder -->
						<div class="flex min-w-[170px] flex-1 flex-col gap-2 p-4">
							<div class="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest text-[color:var(--portal-muted)]">
								<span class="flex h-5 w-5 items-center justify-center rounded-md bg-emerald-500 text-white text-[10px] font-black">3</span>
								THEN also copy to
							</div>
							<input
								v-model="rule.target_folder_pattern"
								type="text"
								:list="`tgt-dl-${idx}`"
								class="w-full rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2 text-sm font-medium text-[color:var(--portal-text)] placeholder:text-[color:var(--portal-subtle)] focus:border-[color:var(--portal-accent)] focus:outline-none focus:ring-1 focus:ring-[color:var(--portal-accent)]"
								placeholder="e.g. 05-PRESENTATION"
								@input="markDirty(rule)"
							/>
							<datalist :id="`tgt-dl-${idx}`">
								<option v-for="s in pathSuggestions" :key="s" :value="s" />
							</datalist>
							<select
								v-model="rule.target_match_mode"
								class="w-full rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-xs text-[color:var(--portal-muted)] focus:border-[color:var(--portal-accent)] focus:outline-none"
								@change="markDirty(rule)"
							>
								<option v-for="m in MATCH_MODES" :key="m.value" :value="m.value">Folder label {{ m.label }} pattern</option>
							</select>
						</div>
					</div>

					<p v-if="rule._err" class="border-t border-red-100 bg-red-50 px-4 py-2 text-xs text-red-700">{{ rule._err }}</p>
				</div>

				<!-- Empty state -->
				<div
					v-if="!rules.length"
					class="rounded-2xl border border-dashed border-[color:var(--portal-border-strong)] bg-white p-12 text-center"
				>
					<div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[color:var(--portal-accent-soft)]">
						<FeatherIcon name="git-merge" class="h-6 w-6 text-[color:var(--portal-accent)]" />
					</div>
					<p class="font-semibold text-[color:var(--portal-text)]">No routing rules yet</p>
					<p class="mt-1 text-sm text-[color:var(--portal-muted)]">Click <strong>New rule</strong> to define your first folder routing pipeline.</p>
				</div>
			</div>

			<!-- Legend -->
			<div class="rounded-2xl border border-[color:var(--portal-border)] bg-white p-4 text-xs text-[color:var(--portal-muted)]">
				<p class="mb-2 font-semibold uppercase tracking-wide text-[color:var(--portal-text)]">How it works</p>
				<div class="space-y-1">
					<p><strong class="text-[color:var(--portal-text)]">Source pattern:</strong> text matched against the upload destination folder's full label path (case-insensitive).</p>
					<p><strong class="text-[color:var(--portal-text)]">File classification:</strong> auto-detected from the file's extension or PDF keyword. Users can override it in the upload confirm dialog.</p>
					<p><strong class="text-[color:var(--portal-text)]">Target pattern:</strong> the first folder whose label matches is used as the auto-copy destination.</p>
					<p><strong class="text-[color:var(--portal-text)]">Match modes:</strong> <em>contains</em> matches anywhere in the path, <em>starts_with</em> from the beginning, <em>exact</em> requires a full match.</p>
				</div>
			</div>

		</div>
	</div>
</template>
