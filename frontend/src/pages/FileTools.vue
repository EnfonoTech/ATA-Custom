<script setup>
import { ref, inject, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { call, uploadFile } from "@/api";
import { FeatherIcon } from "frappe-ui";

const router = useRouter();
const portalCapabilities = inject("portalCapabilities", ref({}));
const refreshPortalCapabilities = inject("refreshPortalCapabilities", () => Promise.resolve());

const canEditTemplate = computed(() => !!portalCapabilities.value?.can_edit_portal_folder_template);

const templateRows = ref([]);
const templateLoading = ref(false);
const templateSaveBusy = ref(false);
const templateSaveErr = ref("");
const templateSaveOk = ref("");
const templateZipBusy = ref(false);
const templateZipInput = ref(null);

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
	return e?.message || "Something went wrong.";
}

async function loadTemplate() {
	if (!canEditTemplate.value) return;
	templateLoading.value = true;
	templateSaveErr.value = "";
	try {
		const res = await call({ method: "portal_app.api.projects.get_portal_folder_template" });
		const rows = (res.rows || []).map((r) => ({ folder_name: String(r.folder_name || "") }));
		templateRows.value = rows.length ? rows : [{ folder_name: "" }];
	} catch (e) {
		console.error(e);
		templateSaveErr.value = apiErr(e);
		templateRows.value = [{ folder_name: "" }];
	} finally {
		templateLoading.value = false;
	}
}

function addTemplateRow() {
	templateRows.value = [...templateRows.value, { folder_name: "" }];
}

function removeTemplateRow(index) {
	const next = templateRows.value.filter((_, i) => i !== index);
	templateRows.value = next.length ? next : [{ folder_name: "" }];
}

function moveTemplateRow(index, delta) {
	const j = index + delta;
	if (j < 0 || j >= templateRows.value.length) return;
	const next = [...templateRows.value];
	[next[index], next[j]] = [next[j], next[index]];
	templateRows.value = next;
}

async function saveTemplate() {
	const cleaned = templateRows.value.map((r) => String(r.folder_name || "").trim()).filter(Boolean);
	templateSaveBusy.value = true;
	templateSaveErr.value = "";
	templateSaveOk.value = "";
	try {
		await call({
			method: "portal_app.api.projects.save_portal_folder_template",
			type: "POST",
			args: { rows: cleaned },
		});
		templateSaveOk.value = cleaned.length
			? "Template saved. New projects will use this layout. Existing folders are unchanged."
			: "Template cleared. Built-in defaults apply until you add rows again.";
		await loadTemplate();
		window.setTimeout(() => (templateSaveOk.value = ""), 4500);
	} catch (e) {
		templateSaveErr.value = apiErr(e);
	} finally {
		templateSaveBusy.value = false;
	}
}

function openTemplateZipPicker() {
	templateZipInput.value?.click();
}

async function onTemplateZipChange(e) {
	const input = e?.target;
	const file = input?.files?.[0];
	if (!file) return;
	templateZipBusy.value = true;
	templateSaveErr.value = "";
	templateSaveOk.value = "";
	try {
		const res = await uploadFile("portal_app.api.projects.import_portal_folder_template_zip", file);
		const rows = (res?.rows || []).map((r) => ({ folder_name: String(r.folder_name || "") }));
		templateRows.value = rows.length ? rows : [{ folder_name: "" }];
		templateSaveOk.value = `Imported ${res?.count ?? rows.length} folder path(s) from ZIP.`;
		window.setTimeout(() => (templateSaveOk.value = ""), 4500);
	} catch (err) {
		templateSaveErr.value = apiErr(err);
	} finally {
		templateZipBusy.value = false;
		if (input) input.value = "";
	}
}

onMounted(async () => {
	try {
		await refreshPortalCapabilities();
	} catch (e) {
		console.error(e);
	}
	if (canEditTemplate.value) {
		await loadTemplate();
	}
});
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-4xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative flex flex-wrap items-start justify-between gap-3">
					<div class="min-w-0">
						<span class="portal-pill portal-pill-accent">
							<FeatherIcon name="sliders" class="h-3 w-3" />
							Auditor tools
						</span>
						<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
							File tools
						</h1>
						<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Manage the company-wide project folder structure. Available only to users with the
							<strong class="text-[color:var(--portal-text)]">Auditor</strong> role — this is the source of truth for the project standard.
						</p>
					</div>
					<button
						type="button"
						class="portal-btn portal-btn-ghost"
						@click="router.push('/files')"
					>
						<FeatherIcon name="arrow-left" class="h-4 w-4" />
						Back to Files
					</button>
				</div>
			</div>

			<div
				v-if="!canEditTemplate"
				class="portal-card-strong p-6 text-center"
			>
				<div
					class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl text-white"
					style="background: linear-gradient(135deg, #f87171 0%, #fb923c 100%);"
				>
					<FeatherIcon name="lock" class="h-5 w-5" />
				</div>
				<h2 class="text-base font-semibold text-[color:var(--portal-text)]">Auditor role required</h2>
				<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
					You need the <strong class="text-[color:var(--portal-text)]">Auditor</strong> role to edit the company-wide folder template.
					Ask a System Manager to assign it from <strong>Desk → User → your user → Roles</strong>.
				</p>
			</div>

			<div v-else class="portal-card-strong relative overflow-hidden p-5">
				<div
					aria-hidden="true"
					class="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-60"
					style="background: radial-gradient(closest-side, rgba(99, 102, 241, 0.18), transparent 70%);"
				></div>
				<div class="relative mb-4 flex flex-wrap items-start justify-between gap-3">
					<div>
						<div class="flex items-center gap-2">
							<div
								class="flex h-9 w-9 items-center justify-center rounded-xl text-white"
								style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
							>
								<FeatherIcon name="layers" class="h-4 w-4" />
							</div>
							<h2 class="text-base font-semibold text-[color:var(--portal-text)]">
								Default file subfolders
							</h2>
							<span class="portal-pill portal-pill-muted">company-wide</span>
						</div>
						<p class="mt-2 max-w-2xl text-sm text-[color:var(--portal-muted)]">
							Use one path per row. For nested folders use
							<code class="rounded bg-[color:var(--portal-bg-dim)] px-1 py-0.5 text-[11px]">Parent/Child</code>.
							Mirrors <strong class="text-[color:var(--portal-text)]">Portal Project Settings → Subfolder template</strong>.
							Existing project folders are not renamed.
						</p>
					</div>
					<div class="hidden items-center gap-2 sm:flex">
						<span class="portal-pill portal-pill-muted">{{ templateRows.length }} rows</span>
					</div>
				</div>

				<div v-if="templateLoading" class="text-sm text-[color:var(--portal-muted)]">Loading template…</div>
				<div v-else class="space-y-2">
					<div
						v-for="(row, idx) in templateRows"
						:key="`tpl-${idx}`"
						class="group flex flex-wrap items-center gap-2 rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2 transition hover:border-[color:var(--portal-border-strong)] hover:shadow-sm"
					>
						<span
							class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[11px] font-semibold text-[color:var(--portal-muted)]"
							style="background: var(--portal-bg-dim);"
						>
							{{ idx + 1 }}
						</span>
						<div class="relative min-w-0 flex-1">
							<FeatherIcon
								name="folder"
								class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[color:var(--portal-subtle)]"
							/>
							<input
								v-model="row.folder_name"
								type="text"
								class="portal-input pl-9"
								placeholder="e.g. 01-DOCUMENTS/01-CLIENT DATA/01-BUSINESS CARD"
							/>
						</div>
						<div class="flex shrink-0 gap-1">
							<button
								type="button"
								class="flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--portal-border)] text-[color:var(--portal-muted)] transition hover:bg-gray-50 disabled:opacity-30"
								:disabled="idx === 0"
								title="Move up"
								@click="moveTemplateRow(idx, -1)"
							>
								<FeatherIcon name="arrow-up" class="h-3.5 w-3.5" />
							</button>
							<button
								type="button"
								class="flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--portal-border)] text-[color:var(--portal-muted)] transition hover:bg-gray-50 disabled:opacity-30"
								:disabled="idx >= templateRows.length - 1"
								title="Move down"
								@click="moveTemplateRow(idx, 1)"
							>
								<FeatherIcon name="arrow-down" class="h-3.5 w-3.5" />
							</button>
							<button
								type="button"
								class="flex h-8 w-8 items-center justify-center rounded-lg border border-red-100 text-red-700 transition hover:bg-red-50"
								title="Remove row"
								@click="removeTemplateRow(idx)"
							>
								<FeatherIcon name="trash-2" class="h-3.5 w-3.5" />
							</button>
						</div>
					</div>

					<div class="flex flex-wrap gap-2 pt-1">
						<button class="portal-btn" @click="addTemplateRow">
							<FeatherIcon name="plus" class="h-3.5 w-3.5" />
							Add row
						</button>
						<button class="portal-btn portal-btn-primary" :disabled="templateSaveBusy" @click="saveTemplate">
							<FeatherIcon name="save" class="h-3.5 w-3.5" />
							{{ templateSaveBusy ? "Saving…" : "Save template" }}
						</button>
						<button class="portal-btn" :disabled="templateZipBusy" @click="openTemplateZipPicker">
							<FeatherIcon name="upload" class="h-3.5 w-3.5" />
							{{ templateZipBusy ? "Importing ZIP…" : "Import ZIP structure" }}
						</button>
						<input
							ref="templateZipInput"
							type="file"
							accept=".zip,application/zip"
							class="hidden"
							@change="onTemplateZipChange"
						/>
					</div>
					<p class="flex items-start gap-1.5 text-xs text-[color:var(--portal-muted)]">
						<FeatherIcon name="info" class="mt-0.5 h-3 w-3 shrink-0" />
						ZIP import reads folder paths from directories inside the archive (only leaf folders are kept; intermediate parents are auto-created), and replaces the current template.
					</p>
					<p v-if="templateSaveErr" class="text-sm text-red-700">{{ templateSaveErr }}</p>
					<p v-if="templateSaveOk" class="text-sm text-green-700">{{ templateSaveOk }}</p>
				</div>
			</div>
		</div>
	</div>
</template>
