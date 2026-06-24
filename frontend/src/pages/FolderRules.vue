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

const RULE_TYPES = [
	{ value: "Cross-route", label: "Cross-route", icon: "git-merge",
	  hint: "Re-post files of a specific type from a source folder to a secondary folder." },
	{ value: "Mirror",      label: "Mirror",      icon: "copy",
	  hint: "Duplicate ALL uploads from source folder into target folder, preserving subfolder structure." },
];

function addRule(type = "Cross-route") {
	rules.value.unshift({
		name: "",
		rule_name: "",
		rule_type: type,
		file_classification: type === "Cross-route" ? "Presentation Files" : "",
		source_folder_pattern: "",
		source_match_mode: "contains",
		target_folder_pattern: "",
		target_match_mode: "contains",
		enabled: 1,
		_dirty: true,
		_new: true,
	});
}

function addMirrorRule() {
	rules.value.unshift({
		name: "",
		rule_name: "01-DOCUMENTS → 03-BALADIYA/01-DOCUMENTS",
		rule_type: "Mirror",
		file_classification: "",
		source_folder_pattern: "01-DOCUMENTS",
		source_match_mode: "starts_with",
		target_folder_pattern: "03-BALADIYA/01-DOCUMENTS",
		target_match_mode: "starts_with",
		enabled: 1,
		_dirty: true,
		_new: true,
	});
}

function markDirty(rule) {
	rule._dirty = true;
}

async function saveRule(rule) {
	if (!rule.source_folder_pattern?.trim()) { rule._err = "Source pattern is required."; return; }
	if (!rule.target_folder_pattern?.trim()) { rule._err = "Target pattern is required."; return; }
	// Cross-route requires a file classification; Mirror does not.
	if ((!rule.rule_type || rule.rule_type === "Cross-route") && !rule.file_classification) {
		rule._err = "File classification is required for Cross-route rules."; return;
	}
	rule._err = "";

	const id = rule.name || rule._tmpId || Math.random().toString(36).slice(2);
	if (!rule._tmpId && !rule.name) rule._tmpId = id;

	const nextSaving = new Set(savingIds.value);
	nextSaving.add(id);
	savingIds.value = nextSaving;

	try {
		const ruleType = rule.rule_type || "Cross-route";
		const autoName = ruleType === "Mirror"
			? `${rule.source_folder_pattern} → ${rule.target_folder_pattern} (Mirror)`
			: `${rule.source_folder_pattern} → ${rule.file_classification} → ${rule.target_folder_pattern}`;
		const payload = {
			name:                  rule.name || "",
			rule_name:             rule.rule_name || autoName,
			rule_type:             ruleType,
			file_classification:   rule.file_classification || "",
			source_folder_pattern: rule.source_folder_pattern.trim(),
			source_match_mode:     rule.source_match_mode || "contains",
			target_folder_pattern: rule.target_folder_pattern.trim(),
			target_match_mode:     rule.target_match_mode || "contains",
			enabled:               rule.enabled ? 1 : 0,
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
					Automatically post files to additional folders during upload — without any extra steps for the user.
					Two rule types: <strong>Mirror</strong> (replicate all files with folder structure) and <strong>Cross-route</strong> (route specific file types to a secondary destination).
				</p>
			</div>

			<p v-if="globalError" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ globalError }}</p>

			<!-- ── Rule type cards (explanation) ── -->
			<div class="grid gap-3 sm:grid-cols-2">
				<div
					v-for="rt in RULE_TYPES" :key="rt.value"
					class="portal-card flex items-start gap-3 p-4 cursor-pointer hover:border-[color:var(--portal-accent)]"
					@click="addRule(rt.value)"
					:title="`Click to add a ${rt.label} rule`"
				>
					<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
						:style="rt.value === 'Mirror'
							? 'background:rgba(59,130,246,0.12);color:#3b82f6'
							: 'background:var(--portal-accent-soft);color:var(--portal-accent)'">
						<FeatherIcon :name="rt.icon" class="h-4 w-4" />
					</div>
					<div>
						<p class="text-sm font-semibold" style="color:var(--portal-text)">{{ rt.label }}</p>
						<p class="mt-0.5 text-xs" style="color:var(--portal-muted)">{{ rt.hint }}</p>
					</div>
					<div class="ml-auto shrink-0">
						<span class="portal-btn portal-btn-ghost text-xs pointer-events-none px-2 py-1">+ Add</span>
					</div>
				</div>
			</div>

			<!-- ── Toolbar ── -->
			<div class="flex flex-wrap items-center justify-between gap-2">
				<p class="text-sm" style="color:var(--portal-muted)">
					{{ rules.length }} rule{{ rules.length === 1 ? "" : "s" }} configured
				</p>
				<div class="flex gap-2">
					<!-- Quick-add the standard ATA mirror rule -->
					<button class="portal-btn portal-btn-ghost text-xs" @click="addMirrorRule"
						title="Pre-fills the 01-DOCUMENTS → 03-BALADIYA/01-DOCUMENTS mirror rule">
						<FeatherIcon name="copy" class="h-3.5 w-3.5" style="color:#3b82f6" />
						Add documents mirror
					</button>
					<button class="portal-btn portal-btn-primary" @click="addRule('Cross-route')">
						<FeatherIcon name="plus" class="h-4 w-4" />
						New rule
					</button>
				</div>
			</div>

			<div v-if="loading" class="flex items-center gap-2" style="color:var(--portal-muted)">
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
					<!-- Top bar -->
					<div class="flex items-center justify-between gap-3 border-b px-4 py-2.5"
						style="border-color:var(--portal-border);background:var(--portal-bg)">

						<!-- Enable toggle -->
						<button type="button"
							class="flex items-center gap-2 rounded-lg px-2 py-1 text-xs font-semibold transition"
							:style="rule.enabled ? 'color:#059669' : 'color:var(--portal-muted)'"
							@click="toggleEnabled(rule)">
							<span class="inline-flex h-4 w-7 items-center rounded-full transition-colors"
								:class="rule.enabled ? 'bg-emerald-500' : 'bg-gray-300'">
								<span class="h-3 w-3 rounded-full bg-white shadow transition-transform"
									:class="rule.enabled ? 'translate-x-3.5' : 'translate-x-0.5'"></span>
							</span>
							{{ rule.enabled ? "Enabled" : "Disabled" }}
						</button>

						<!-- Rule type badge -->
						<span class="shrink-0 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold"
							:style="(rule.rule_type || 'Cross-route') === 'Mirror'
								? 'background:rgba(59,130,246,0.1);color:#3b82f6;border-color:rgba(59,130,246,0.25)'
								: 'background:var(--portal-accent-soft);color:var(--portal-accent);border-color:rgba(245,158,11,0.25)'">
							<FeatherIcon :name="(rule.rule_type || 'Cross-route') === 'Mirror' ? 'copy' : 'git-merge'" class="h-2.5 w-2.5" />
							{{ rule.rule_type || "Cross-route" }}
						</span>

						<!-- Rule name -->
						<input v-model="rule.rule_name" type="text"
							class="min-w-0 flex-1 rounded-lg border-0 bg-transparent px-2 py-1 text-xs font-medium placeholder:text-[color:var(--portal-subtle)] focus:ring-1 focus:ring-[color:var(--portal-accent)]"
							style="color:var(--portal-text)"
							placeholder="Rule description (auto-generated if blank)"
							@input="markDirty(rule)" />

						<!-- Save -->
						<button v-if="rule._dirty" type="button"
							class="portal-btn portal-btn-primary shrink-0 text-xs"
							:disabled="savingIds.has(rule.name || rule._tmpId)"
							@click="saveRule(rule)">
							<span v-if="savingIds.has(rule.name || rule._tmpId)" class="flex items-center gap-1">
								<span class="h-3 w-3 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
								Saving…
							</span>
							<span v-else class="flex items-center gap-1">
								<FeatherIcon name="save" class="h-3.5 w-3.5" />Save
							</span>
						</button>

						<!-- Delete -->
						<button type="button"
							class="rounded-lg p-1.5 transition"
							style="color:var(--portal-muted)"
							:disabled="deletingIds.has(rule.name)"
							title="Delete rule"
							@click="deleteRule(rule, idx)">
							<FeatherIcon name="trash-2" class="h-4 w-4" />
						</button>
					</div>

					<!-- ── Pipeline ── -->
					<div class="flex flex-wrap items-stretch gap-0 sm:flex-nowrap">

						<!-- NODE 1: Source -->
						<div class="flex min-w-[170px] flex-1 flex-col gap-2 border-r p-4" style="border-color:var(--portal-border)">
							<div class="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest" style="color:var(--portal-muted)">
								<span class="flex h-5 w-5 items-center justify-center rounded-md text-white text-[10px] font-black"
									style="background:var(--portal-accent)">1</span>
								IF uploaded inside
							</div>
							<input v-model="rule.source_folder_pattern" type="text" :list="`src-dl-${idx}`"
								class="w-full rounded-xl border px-3 py-2 text-sm font-medium placeholder:text-[color:var(--portal-subtle)] focus:outline-none focus:ring-1 focus:ring-[color:var(--portal-accent)]"
								style="border-color:var(--portal-border);background:var(--portal-surface);color:var(--portal-text)"
								:placeholder="(rule.rule_type||'Cross-route')==='Mirror' ? 'e.g. 01-DOCUMENTS' : 'e.g. 01-CONCEPT STUDIES'"
								@input="markDirty(rule)" />
							<datalist :id="`src-dl-${idx}`">
								<option v-for="s in pathSuggestions" :key="s" :value="s" />
							</datalist>
							<select v-model="rule.source_match_mode"
								class="w-full rounded-xl border px-3 py-1.5 text-xs focus:outline-none"
								style="border-color:var(--portal-border);background:var(--portal-surface);color:var(--portal-muted)"
								@change="markDirty(rule)">
								<option v-for="m in MATCH_MODES" :key="m.value" :value="m.value">Folder label {{ m.label }} pattern</option>
							</select>
							<p v-if="(rule.rule_type||'Cross-route')==='Mirror'" class="text-[10px]" style="color:var(--portal-subtle)">
								Mirror matches: exact path <em>or</em> any subfolder under it.
							</p>
						</div>

						<!-- Arrow -->
						<div class="hidden items-center justify-center px-1 sm:flex">
							<div class="flex flex-col items-center gap-0.5">
								<div class="h-px w-6" style="background:var(--portal-border)"></div>
								<FeatherIcon name="chevron-right" class="h-4 w-4" style="color:var(--portal-accent)" />
								<div class="h-px w-6" style="background:var(--portal-border)"></div>
							</div>
						</div>

						<!-- NODE 2: Classification filter (Cross-route only) -->
						<div v-if="(rule.rule_type||'Cross-route')==='Cross-route'"
							class="flex min-w-[170px] flex-1 flex-col gap-2 border-r p-4" style="border-color:var(--portal-border)">
							<div class="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest" style="color:var(--portal-muted)">
								<span class="flex h-5 w-5 items-center justify-center rounded-md bg-indigo-500 text-white text-[10px] font-black">2</span>
								AND file type is
							</div>
							<select v-model="rule.file_classification"
								class="w-full rounded-xl border px-3 py-2 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-[color:var(--portal-accent)]"
								style="border-color:var(--portal-border);background:var(--portal-surface);color:var(--portal-text)"
								@change="markDirty(rule)">
								<option value="">— Any classification —</option>
								<option v-for="cls in FILE_CLASSIFICATIONS" :key="cls" :value="cls">{{ cls }}</option>
							</select>
							<span v-if="rule.file_classification"
								class="inline-flex w-fit items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold"
								:class="classificationColor(rule.file_classification)">
								<FeatherIcon name="tag" class="h-2.5 w-2.5" />
								{{ rule.file_classification }}
							</span>
						</div>

						<!-- NODE 2 placeholder for Mirror (no classification needed) -->
						<div v-else
							class="flex min-w-[120px] flex-1 flex-col items-center justify-center gap-1 border-r p-4 opacity-50"
							style="border-color:var(--portal-border)">
							<FeatherIcon name="copy" class="h-6 w-6" style="color:#3b82f6" />
							<p class="text-[10px] font-semibold text-center" style="color:var(--portal-muted)">All file types</p>
							<p class="text-[9px] text-center" style="color:var(--portal-subtle)">Mirror copies everything</p>
						</div>

						<!-- Arrow -->
						<div class="hidden items-center justify-center px-1 sm:flex">
							<div class="flex flex-col items-center gap-0.5">
								<div class="h-px w-6" style="background:var(--portal-border)"></div>
								<FeatherIcon name="chevron-right" class="h-4 w-4" style="color:var(--portal-accent)" />
								<div class="h-px w-6" style="background:var(--portal-border)"></div>
							</div>
						</div>

						<!-- NODE 3: Target -->
						<div class="flex min-w-[170px] flex-1 flex-col gap-2 p-4">
							<div class="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest" style="color:var(--portal-muted)">
								<span class="flex h-5 w-5 items-center justify-center rounded-md bg-emerald-500 text-white text-[10px] font-black">3</span>
								{{ (rule.rule_type||'Cross-route')==='Mirror' ? 'MIRROR into' : 'THEN also copy to' }}
							</div>
							<input v-model="rule.target_folder_pattern" type="text" :list="`tgt-dl-${idx}`"
								class="w-full rounded-xl border px-3 py-2 text-sm font-medium placeholder:text-[color:var(--portal-subtle)] focus:outline-none focus:ring-1 focus:ring-[color:var(--portal-accent)]"
								style="border-color:var(--portal-border);background:var(--portal-surface);color:var(--portal-text)"
								:placeholder="(rule.rule_type||'Cross-route')==='Mirror' ? 'e.g. 03-BALADIYA/01-DOCUMENTS' : 'e.g. 05-PRESENTATION'"
								@input="markDirty(rule)" />
							<datalist :id="`tgt-dl-${idx}`">
								<option v-for="s in pathSuggestions" :key="s" :value="s" />
							</datalist>
							<select v-if="(rule.rule_type||'Cross-route')!=='Mirror'"
								v-model="rule.target_match_mode"
								class="w-full rounded-xl border px-3 py-1.5 text-xs focus:outline-none"
								style="border-color:var(--portal-border);background:var(--portal-surface);color:var(--portal-muted)"
								@change="markDirty(rule)">
								<option v-for="m in MATCH_MODES" :key="m.value" :value="m.value">Folder label {{ m.label }} pattern</option>
							</select>
							<p v-else class="text-[10px]" style="color:var(--portal-subtle)">
								Subfolder structure is replicated. e.g. uploading to <code>01-DOCUMENTS/04-DRAWINGS</code>
								also saves to <code>03-BALADIYA/01-DOCUMENTS/04-DRAWINGS</code>.
							</p>
						</div>
					</div>

					<p v-if="rule._err" class="border-t px-4 py-2 text-xs text-red-700"
						style="background:rgba(239,68,68,0.08);border-color:rgba(239,68,68,0.15)">{{ rule._err }}</p>
				</div>

				<!-- Empty state -->
				<div v-if="!rules.length"
					class="rounded-2xl border border-dashed p-12 text-center"
					style="border-color:var(--portal-border-strong);background:var(--portal-surface)">
					<div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl"
						style="background:var(--portal-accent-soft)">
						<FeatherIcon name="git-merge" class="h-6 w-6" style="color:var(--portal-accent)" />
					</div>
					<p class="font-semibold" style="color:var(--portal-text)">No routing rules yet</p>
					<p class="mt-1 text-sm" style="color:var(--portal-muted)">
						Add a <strong>Mirror</strong> rule to auto-copy documents to Baladiya, or a <strong>Cross-route</strong> rule to send specific file types to a secondary folder.
					</p>
					<div class="mt-4 flex flex-wrap items-center justify-center gap-2">
						<button class="portal-btn portal-btn-ghost text-xs" @click="addMirrorRule">
							<FeatherIcon name="copy" class="h-3.5 w-3.5" style="color:#3b82f6" />
							Add documents mirror rule
						</button>
						<button class="portal-btn portal-btn-primary text-xs" @click="addRule('Cross-route')">
							<FeatherIcon name="plus" class="h-3.5 w-3.5" />
							New cross-route rule
						</button>
					</div>
				</div>
			</div>

			<!-- ── Documentation ── -->
			<div class="portal-card-strong p-5 space-y-4">
				<p class="font-semibold flex items-center gap-2" style="color:var(--portal-text)">
					<FeatherIcon name="book-open" class="h-4 w-4" style="color:var(--portal-accent)" />
					How routing works
				</p>

				<div class="grid gap-3 sm:grid-cols-2">
					<!-- Mirror -->
					<div class="rounded-xl border p-4" style="border-color:rgba(59,130,246,0.2);background:rgba(59,130,246,0.06)">
						<p class="flex items-center gap-1.5 text-sm font-semibold mb-2" style="color:#3b82f6">
							<FeatherIcon name="copy" class="h-3.5 w-3.5" />Mirror rule
						</p>
						<ul class="space-y-1 text-xs" style="color:var(--portal-muted)">
							<li>• Applies to <strong>all</strong> file types — no classification filter needed.</li>
							<li>• Source pattern uses <em>prefix</em> matching — any folder whose path starts with the source prefix is included.</li>
							<li>• Target is a folder prefix. Subfolder structure is replicated automatically.</li>
							<li>• Example: <code style="color:var(--portal-text)">01-DOCUMENTS/04-DRAWINGS</code> → <code style="color:var(--portal-text)">03-BALADIYA/01-DOCUMENTS/04-DRAWINGS</code></li>
						</ul>
					</div>
					<!-- Cross-route -->
					<div class="rounded-xl border p-4" style="border-color:rgba(245,158,11,0.2);background:var(--portal-accent-soft)">
						<p class="flex items-center gap-1.5 text-sm font-semibold mb-2" style="color:var(--portal-accent)">
							<FeatherIcon name="git-merge" class="h-3.5 w-3.5" />Cross-route rule
						</p>
						<ul class="space-y-1 text-xs" style="color:var(--portal-muted)">
							<li>• Triggers only for a specific <strong>file classification</strong> (e.g. Drawing / Layout Files).</li>
							<li>• Target is found by matching the target pattern against existing folder labels.</li>
							<li>• The first matching folder wins; subfolder structure is <em>not</em> replicated.</li>
							<li>• Example: DWG in Concept Studies → also save to Presentation folder.</li>
						</ul>
					</div>
				</div>

				<div class="rounded-xl border p-4 text-xs" style="border-color:var(--portal-border);color:var(--portal-muted)">
					<p class="font-semibold mb-2" style="color:var(--portal-text)">Match modes</p>
					<div class="grid gap-1 sm:grid-cols-3">
						<div><strong style="color:var(--portal-text)">contains</strong> — pattern appears anywhere in the folder label path.</div>
						<div><strong style="color:var(--portal-text)">starts_with</strong> — path begins with the pattern (recommended for Mirror).</div>
						<div><strong style="color:var(--portal-text)">exact</strong> — full path must match exactly.</div>
					</div>
				</div>

				<div class="rounded-xl border p-4 text-xs" style="border-color:rgba(245,158,11,0.2);background:rgba(245,158,11,0.05)">
					<p class="font-semibold mb-1" style="color:var(--portal-accent)">ATA standard: 01-DOCUMENTS → 03-BALADIYA</p>
					<p style="color:var(--portal-muted)">
						All files uploaded to <code>01-DOCUMENTS</code> (or any subfolder like <code>01-DOCUMENTS/04-DRAWINGS</code>)
						should also appear in the corresponding Baladiya folder (<code>03-BALADIYA/01-DOCUMENTS/04-DRAWINGS</code>).
						Use the <strong>Add documents mirror</strong> button above to set this up.
					</p>
				</div>
			</div>

		</div>
	</div>
</template>
