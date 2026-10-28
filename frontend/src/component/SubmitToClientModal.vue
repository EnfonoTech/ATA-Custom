<script setup>
// "Submit to client": one numbered submission folder in the client folder's Incoming,
// named NN_YYYY-MM-DD_<Type>[ - <description>]. Used by the Files page (selected files,
// or a folder) and the File Browser (one file). The server numbers and cleans the name;
// the preview here only mirrors it.
import { ref, computed, watch } from "vue";
import { call } from "@/api";
import { FeatherIcon } from "frappe-ui";

const props = defineProps({
	project: { type: String, default: "" },
	files: { type: Array, default: () => [] }, // [{ name, file_name }]
	folder: { type: Object, default: null }, // { name, label } or null
	open: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "submitted"]);

const types = ref([]);
const typesLoading = ref(false);
const submissionType = ref("");
const description = ref("");
const busy = ref(false);
const error = ref("");
const ok = ref("");

function apiErr(e, fallback) {
	const body = e?.responseBody;
	if (body?._server_messages) {
		try {
			return JSON.parse(JSON.parse(body._server_messages)[0]).message;
		} catch {
			/* fall through */
		}
	}
	return body?.message || fallback;
}

function todayIso() {
	const d = new Date();
	const mm = String(d.getMonth() + 1).padStart(2, "0");
	const dd = String(d.getDate()).padStart(2, "0");
	return `${d.getFullYear()}-${mm}-${dd}`;
}

// Client-side mirror of files._clean_name_part (the server has the last word).
function cleanPart(text) {
	let s = String(text || "").replace(/[/\\:*?"<>|\x00-\x1f]/g, " ");
	while (s.includes("..")) s = s.replace(/\.\./g, "");
	return s.replace(/\s+/g, " ").replace(/^[ .]+|[ .]+$/g, "");
}

const stem = computed(() => {
	const desc = cleanPart(description.value);
	const type = submissionType.value || "<Type>";
	return `NN_${todayIso()}_${type}${desc ? " - " + desc : ""}`;
});

function extOf(name) {
	const n = String(name || "");
	const i = n.lastIndexOf(".");
	return i > 0 ? n.slice(i) : "";
}

const resultingNames = computed(() =>
	props.folder ? [] : props.files.map((f, i) => `${stem.value}${i === 0 ? "" : "-" + (i + 1)}${extOf(f.file_name)}`)
);

async function loadTypes() {
	typesLoading.value = true;
	try {
		const rows = await call({ method: "portal_app.api.submissions.list_submission_types" });
		types.value = (rows || []).filter((r) => r.enabled);
		if (!types.value.some((t) => t.name === submissionType.value)) {
			submissionType.value = types.value.length === 1 ? types.value[0].name : "";
		}
	} catch (e) {
		error.value = apiErr(e, "Could not load the submission types.");
	} finally {
		typesLoading.value = false;
	}
}

watch(
	() => props.open,
	(isOpen) => {
		if (!isOpen) return;
		error.value = "";
		ok.value = "";
		description.value = "";
		loadTypes();
	},
	{ immediate: true }
);

function close() {
	if (busy.value) return;
	emit("close");
}

async function confirm() {
	if (!props.project || !submissionType.value) return;
	busy.value = true;
	error.value = "";
	ok.value = "";
	const args = { project: props.project, submission_type: submissionType.value, description: description.value };
	if (props.folder) args.folder_path = props.folder.name;
	else args.file_names = JSON.stringify(props.files.map((f) => f.name));
	try {
		const res = await call({ method: "portal_app.api.submissions.submit_to_client", type: "POST", args });
		ok.value = `Submitted as "${res.folder_name}" — the client sees it in their Incoming (your Outgoing).`;
		emit("submitted", res);
		setTimeout(() => {
			ok.value = "";
			emit("close");
		}, 3000);
	} catch (e) {
		error.value = apiErr(e, "Submission failed.");
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<Teleport to="body">
		<div
			v-if="open"
			class="fixed inset-0 z-[70] flex items-center justify-center px-4"
			role="dialog"
			aria-modal="true"
			@click.self="close"
		>
			<div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"></div>
			<div class="relative z-10 w-full max-w-lg rounded-2xl shadow-2xl" style="background:var(--portal-surface);border:1px solid var(--portal-border)" @click.stop>
				<!-- Header -->
				<div class="flex items-center justify-between gap-3 border-b px-5 py-4" style="border-color:var(--portal-border)">
					<div class="flex items-center gap-3">
						<div class="flex h-10 w-10 items-center justify-center rounded-2xl text-white shadow-md"
							style="background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);">
							<FeatherIcon name="send" class="h-5 w-5" />
						</div>
						<div>
							<h2 class="text-base font-bold" style="color:var(--portal-text)">Submit to Client</h2>
							<p class="text-xs" style="color:var(--portal-muted)">Creates one numbered submission folder in <strong>06-CLIENT SUBMITTAL / Outgoing</strong> (the client sees it in Incoming)</p>
						</div>
					</div>
					<button type="button" class="rounded-lg p-1.5 transition" style="color:var(--portal-subtle)" :disabled="busy" @click="close">
						<FeatherIcon name="x" class="h-4 w-4" />
					</button>
				</div>

				<!-- Body -->
				<div class="space-y-4 px-5 py-5">
					<!-- What is submitted -->
					<div class="rounded-xl px-4 py-3" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border)">
						<p v-if="folder" class="flex items-center gap-2 text-sm font-semibold" style="color:var(--portal-text)">
							<FeatherIcon name="folder" class="h-4 w-4 shrink-0" style="color:var(--portal-accent)" />
							<span class="truncate">{{ folder.label }}</span>
							<span class="text-[11px] font-normal" style="color:var(--portal-muted)">(whole folder, original file names)</span>
						</p>
						<template v-else>
							<p class="mb-1 text-[11px] font-semibold" style="color:var(--portal-muted)">{{ files.length }} file(s)</p>
							<p v-for="f in files" :key="f.name" class="flex items-center gap-2 truncate text-sm" style="color:var(--portal-text)">
								<FeatherIcon name="file" class="h-3.5 w-3.5 shrink-0" style="color:var(--portal-accent)" />
								<span class="truncate">{{ f.file_name }}</span>
							</p>
						</template>
					</div>

					<!-- Type -->
					<label class="block">
						<span class="mb-1 block text-xs font-semibold" style="color:var(--portal-text)">Submission type <span style="color:var(--portal-danger)">*</span></span>
						<select v-model="submissionType" class="portal-input w-full rounded-xl px-3 py-2 text-sm" :disabled="busy || typesLoading" required>
							<option value="" disabled>{{ typesLoading ? "Loading…" : "Choose a type" }}</option>
							<option v-for="t in types" :key="t.name" :value="t.name">{{ t.type_name }}</option>
						</select>
					</label>

					<!-- Description -->
					<label class="block">
						<span class="mb-1 flex items-center justify-between text-xs font-semibold" style="color:var(--portal-text)">
							<span>Description <span class="font-normal" style="color:var(--portal-muted)">(optional)</span></span>
							<span class="font-normal" style="color:var(--portal-muted)">{{ description.length }}/100</span>
						</span>
						<input v-model="description" type="text" maxlength="100" class="portal-input w-full rounded-xl px-3 py-2 text-sm" placeholder="e.g. Layout plan rev01" :disabled="busy" />
					</label>

					<!-- Generated name preview -->
					<div class="rounded-xl border px-4 py-3" style="border-color:rgba(245,158,11,0.25);background:rgba(245,158,11,0.06)">
						<p class="mb-1.5 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider" style="color:var(--portal-accent)">
							<FeatherIcon name="tag" class="h-3 w-3" />
							Submission folder
						</p>
						<p class="font-mono text-sm font-bold break-all" style="color:var(--portal-text)">{{ stem }}</p>
						<ul v-if="resultingNames.length" class="mt-2 space-y-0.5 text-[11px] font-mono" style="color:var(--portal-muted)">
							<li v-for="n in resultingNames" :key="n" class="break-all">{{ n }}</li>
						</ul>
						<div class="mt-2 flex flex-wrap gap-3 text-[11px]" style="color:var(--portal-muted)">
							<span class="flex items-center gap-1"><span class="font-bold" style="color:var(--portal-accent)">NN</span> = next number in the client's Incoming</span>
							<span class="flex items-center gap-1"><span class="font-bold" style="color:var(--portal-accent)">Date</span> = today ({{ todayIso() }})</span>
						</div>
					</div>

					<p v-if="error" class="rounded-xl px-3 py-2 text-sm" style="background:var(--portal-danger-soft);color:var(--portal-danger);border:1px solid rgba(239,68,68,0.2)">{{ error }}</p>
					<p v-if="ok" class="rounded-xl px-3 py-2 text-sm font-medium" style="background:var(--portal-success-soft);color:var(--portal-success);border:1px solid rgba(34,197,94,0.2)">
						<FeatherIcon name="check-circle" class="mr-1 inline h-4 w-4" />{{ ok }}
					</p>
				</div>

				<!-- Footer -->
				<div class="flex items-center justify-end gap-2 border-t px-5 py-4" style="border-color:var(--portal-border);background:rgba(0,0,0,0.15)">
					<button type="button" class="portal-btn rounded-xl px-4 py-2 text-sm font-medium" :disabled="busy" @click="close">Cancel</button>
					<button
						type="button"
						class="flex items-center gap-2 rounded-xl px-5 py-2 text-sm font-bold text-white shadow-md transition hover:opacity-90 disabled:opacity-50"
						style="background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%);"
						:disabled="busy || !!ok || !submissionType || (!folder && !files.length)"
						@click="confirm"
					>
						<span v-if="busy" class="flex items-center gap-2">
							<span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
							Submitting…
						</span>
						<span v-else class="flex items-center gap-2">
							<FeatherIcon name="send" class="h-4 w-4" />
							Confirm &amp; Submit to Client
						</span>
					</button>
				</div>
			</div>
		</div>
	</Teleport>
</template>
