<script setup>
// The client contact's landing page: for one project, only Incoming (what ATA sent) and
// Outgoing (what the client sent), each as numbered submissions 1, 2, 3 … (oldest = 1).
// Arabic first (RTL), switchable to English. `dir` / `lang` live on this page's root
// element only, never on <html>, so leaving the page cannot leave the portal in RTL.
// Access is the server's: list_client_projects / list_client_transmittals are scoped by
// get_allowed_project_names, downloads go through download_project_file, uploads through
// upload_project_file into the client Outgoing folder.
import { ref, computed, onMounted } from "vue";
import { call, uploadFile } from "@/api";
import { FeatherIcon } from "frappe-ui";
import { useClientLang } from "@/i18n/clientPortal";

const { lang, dir, t, setLang, formatDate } = useClientLang();

const PROJECT_KEY = "portal_client_project";

const branding = ref({});
const projects = ref([]);
const projectsLoading = ref(true);
const project = ref("");
const data = ref(null);
const loading = ref(false);
const loadError = ref(false);
const direction = ref(""); // "" = the two folder tiles, else "incoming" | "outgoing"
const openKeys = ref(new Set());
const uploadBusy = ref(false);
const uploadMsg = ref("");
const uploadErr = ref("");
const fileInput = ref(null);

const currentProject = computed(() => projects.value.find((p) => p.name === project.value) || null);
const submissions = computed(() => (direction.value && data.value ? data.value[direction.value] || [] : []));
const canUpload = computed(() => !!data.value?.can_upload && direction.value === "outgoing");

function apiErr(e) {
	const body = e?.responseBody;
	if (body?._server_messages) {
		try {
			const arr = JSON.parse(body._server_messages);
			if (arr.length) return JSON.parse(arr[0]).message || arr[0];
		} catch {
			return String(body._server_messages[0]);
		}
	}
	// Never body.exc: a client must not see a server traceback.
	return body?.message || t("error");
}

function rememberProject(name) {
	try {
		if (name) window.sessionStorage.setItem(PROJECT_KEY, name);
		else window.sessionStorage.removeItem(PROJECT_KEY);
	} catch {
		/* storage blocked */
	}
}

function recalledProject() {
	try {
		return window.sessionStorage.getItem(PROJECT_KEY) || "";
	} catch {
		return "";
	}
}

function downloadUrl(f) {
	return `/api/method/portal_app.api.files.download_project_file?file_name=${encodeURIComponent(f.name)}`;
}

function fmtSize(bytes) {
	const n = Number(bytes) || 0;
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
	return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function toggle(key) {
	const next = new Set(openKeys.value);
	if (next.has(key)) next.delete(key);
	else next.add(key);
	openKeys.value = next;
}

async function loadTransmittals() {
	if (!project.value) return;
	loading.value = true;
	loadError.value = false;
	try {
		data.value = await call({
			method: "portal_app.api.submissions.list_client_transmittals",
			args: { project: project.value },
		});
	} catch {
		data.value = null;
		loadError.value = true;
	} finally {
		loading.value = false;
	}
}

async function pickProject(name) {
	project.value = name;
	direction.value = "";
	openKeys.value = new Set();
	rememberProject(name);
	await loadTransmittals();
}

function backToProjects() {
	project.value = "";
	data.value = null;
	direction.value = "";
	rememberProject("");
}

function openDirection(d) {
	direction.value = d;
	openKeys.value = new Set();
	uploadMsg.value = "";
	uploadErr.value = "";
}

async function onFilesPicked(ev) {
	const input = ev?.target;
	const picked = Array.from(input?.files || []);
	if (!picked.length || !project.value) return;
	uploadBusy.value = true;
	uploadMsg.value = "";
	uploadErr.value = "";
	let done = 0;
	try {
		for (const file of picked) {
			uploadMsg.value = t("uploading", { done: done + 1, total: picked.length });
			await uploadFile("portal_app.api.files.upload_project_file", file, {
				project: project.value,
				target_folder: "__client_outgoing__",
				destination: "erpnext",
				is_private: "1",
			});
			done++;
		}
		uploadMsg.value = t("uploaded", { n: done });
	} catch (e) {
		uploadMsg.value = "";
		uploadErr.value = `${t("uploadFailed")}: ${apiErr(e)}`;
	} finally {
		uploadBusy.value = false;
		if (input) input.value = "";
		if (done) await loadTransmittals();
	}
}

async function signOut() {
	try {
		await call({ method: "logout", type: "GET" });
	} catch (err) {
		console.error("Logout failed:", err);
	} finally {
		try {
			localStorage.removeItem("full_name");
			localStorage.removeItem("profile_image");
			localStorage.removeItem("user_email");
		} catch {
			/* storage blocked */
		}
		window.location.href = "/portal-app/login";
	}
}

onMounted(async () => {
	call({ method: "portal_app.api.public.get_branding" })
		.then((b) => (branding.value = b || {}))
		.catch(() => {});
	try {
		projects.value = (await call({ method: "portal_app.api.submissions.list_client_projects" })) || [];
	} catch {
		projects.value = [];
	} finally {
		projectsLoading.value = false;
	}
	const recalled = recalledProject();
	if (projects.value.length === 1) await pickProject(projects.value[0].name);
	else if (recalled && projects.value.some((p) => p.name === recalled)) await pickProject(recalled);
});
</script>

<template>
	<div :dir="dir" :lang="lang" class="client-page min-h-screen" style="background:var(--portal-bg)">
		<!-- Header -->
		<header class="border-b" style="border-color:var(--portal-border);background:var(--portal-surface)">
			<div class="mx-auto flex max-w-4xl items-center justify-between gap-3 px-4 py-3">
				<div class="flex min-w-0 items-center gap-3">
					<img
						v-if="branding.company_logo"
						:src="branding.company_logo"
						alt=""
						class="h-9 w-auto shrink-0 object-contain"
					/>
					<div class="min-w-0">
						<p class="truncate text-sm font-bold" style="color:var(--portal-text)">{{ branding.company_name || "ATA" }}</p>
						<p class="truncate text-xs" style="color:var(--portal-muted)">{{ t("title") }}</p>
					</div>
				</div>
				<div class="flex shrink-0 items-center gap-2">
					<button
						type="button"
						class="rounded-lg border px-3 py-1.5 text-xs font-semibold"
						style="border-color:var(--portal-border);color:var(--portal-text)"
						@click="setLang(lang === 'ar' ? 'en' : 'ar')"
					>{{ t("language") }}</button>
					<button
						type="button"
						class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold text-white"
						style="background:#111827"
						@click="signOut"
					>
						<FeatherIcon name="log-out" class="h-3.5 w-3.5 rtl:rotate-180" />
						{{ t("signOut") }}
					</button>
				</div>
			</div>
		</header>

		<main class="mx-auto max-w-4xl px-4 py-6">
			<!-- Loading projects -->
			<p v-if="projectsLoading" class="py-10 text-center text-sm" style="color:var(--portal-muted)">{{ t("loading") }}</p>

			<!-- No projects -->
			<div v-else-if="!projects.length" class="rounded-2xl border px-6 py-12 text-center" style="border-color:var(--portal-border);background:var(--portal-surface)">
				<FeatherIcon name="folder" class="mx-auto mb-3 h-8 w-8" style="color:var(--portal-subtle)" />
				<p class="text-sm" style="color:var(--portal-muted)">{{ t("noProjects") }}</p>
			</div>

			<!-- Project picker -->
			<section v-else-if="!project">
				<h1 class="mb-4 text-lg font-bold" style="color:var(--portal-text)">{{ t("chooseProject") }}</h1>
				<div class="grid gap-3 sm:grid-cols-2">
					<button
						v-for="p in projects"
						:key="p.name"
						type="button"
						class="flex items-center justify-between gap-3 rounded-2xl border px-4 py-4 text-start transition hover:shadow-md"
						style="border-color:var(--portal-border);background:var(--portal-surface)"
						@click="pickProject(p.name)"
					>
						<span class="min-w-0">
							<bdi class="block truncate text-sm font-semibold" style="color:var(--portal-text)">{{ p.project_name || p.name }}</bdi>
							<bdi v-if="p.portal_project_code" class="block truncate text-xs" style="color:var(--portal-muted)">{{ p.portal_project_code }}</bdi>
						</span>
						<FeatherIcon name="chevron-right" class="h-4 w-4 shrink-0 rtl:rotate-180" style="color:var(--portal-subtle)" />
					</button>
				</div>
			</section>

			<!-- A project -->
			<section v-else>
				<div class="mb-4 flex flex-wrap items-center justify-between gap-2">
					<div class="min-w-0">
						<h1 class="truncate text-lg font-bold" style="color:var(--portal-text)">
							<bdi>{{ currentProject?.project_name || data?.project_name || project }}</bdi>
						</h1>
						<p v-if="direction" class="text-xs" style="color:var(--portal-muted)">
							{{ t(direction) }} · {{ t(direction === "incoming" ? "incomingHint" : "outgoingHint") }}
						</p>
					</div>
					<div class="flex items-center gap-2">
						<button
							v-if="direction"
							type="button"
							class="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-semibold"
							style="border-color:var(--portal-border);color:var(--portal-text)"
							@click="direction = ''"
						>
							<FeatherIcon name="chevron-left" class="h-3.5 w-3.5 rtl:rotate-180" />
							{{ t("back") }}
						</button>
						<button
							v-else-if="projects.length > 1"
							type="button"
							class="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-semibold"
							style="border-color:var(--portal-border);color:var(--portal-text)"
							@click="backToProjects"
						>
							<FeatherIcon name="chevron-left" class="h-3.5 w-3.5 rtl:rotate-180" />
							{{ t("backToProjects") }}
						</button>
					</div>
				</div>

				<p v-if="loading" class="py-10 text-center text-sm" style="color:var(--portal-muted)">{{ t("loading") }}</p>
				<div v-else-if="loadError" class="rounded-2xl border px-6 py-8 text-center text-sm" style="border-color:var(--portal-border);background:var(--portal-surface);color:var(--portal-danger)">
					{{ t("error") }}
					<button type="button" class="ms-2 underline" @click="loadTransmittals">{{ t("open") }}</button>
				</div>

				<!-- The two folders -->
				<div v-else-if="!direction" class="grid gap-4 sm:grid-cols-2">
					<button
						v-for="d in ['incoming', 'outgoing']"
						:key="d"
						type="button"
						class="flex flex-col items-start gap-3 rounded-2xl border px-5 py-6 text-start transition hover:shadow-md"
						style="border-color:var(--portal-border);background:var(--portal-surface)"
						@click="openDirection(d)"
					>
						<span
							class="flex h-12 w-12 items-center justify-center rounded-2xl text-white"
							:style="d === 'incoming' ? 'background:linear-gradient(135deg,#0ea5e9 0%,#6366f1 100%)' : 'background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%)'"
						>
							<FeatherIcon :name="d === 'incoming' ? 'download' : 'upload'" class="h-6 w-6" />
						</span>
						<span class="text-xl font-bold" style="color:var(--portal-text)">{{ t(d) }}</span>
						<span class="text-sm" style="color:var(--portal-muted)">{{ t(d === "incoming" ? "incomingHint" : "outgoingHint") }}</span>
						<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold" style="background:var(--portal-surface-alt);color:var(--portal-text)">
							{{ (data?.[d] || []).length }} · {{ t("submission") }}
						</span>
					</button>
				</div>

				<!-- Submissions of one folder -->
				<div v-else class="space-y-3">
					<div v-if="canUpload" class="rounded-2xl border px-4 py-4" style="border-color:var(--portal-border);background:var(--portal-surface)">
						<input ref="fileInput" type="file" multiple class="hidden" @change="onFilesPicked" />
						<button
							type="button"
							class="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
							style="background:linear-gradient(135deg,#f59e0b 0%,#d97706 100%)"
							:disabled="uploadBusy"
							@click="fileInput?.click()"
						>
							<FeatherIcon name="upload" class="h-4 w-4" />
							{{ t("upload") }}
						</button>
						<p v-if="uploadMsg" class="mt-2 text-sm" style="color:var(--portal-success)">{{ uploadMsg }}</p>
						<p v-if="uploadErr" class="mt-2 text-sm" style="color:var(--portal-danger)">{{ uploadErr }}</p>
					</div>

					<p v-if="!submissions.length" class="rounded-2xl border px-6 py-10 text-center text-sm" style="border-color:var(--portal-border);background:var(--portal-surface);color:var(--portal-muted)">
						{{ t("empty") }}
					</p>

					<article
						v-for="s in submissions"
						:key="s.key"
						class="overflow-hidden rounded-2xl border"
						:style="`border-color:${s.is_latest ? 'rgba(34,197,94,0.45)' : 'var(--portal-border)'};background:var(--portal-surface)`"
					>
						<button
							type="button"
							class="flex w-full items-center justify-between gap-3 px-4 py-3 text-start"
							:aria-expanded="openKeys.has(s.key)"
							@click="toggle(s.key)"
						>
							<span class="min-w-0">
								<span class="flex flex-wrap items-center gap-2">
									<span class="text-sm font-bold" style="color:var(--portal-text)">{{ t("submissionN", { n: s.number }) }}</span>
									<span v-if="s.is_latest" class="rounded-full px-2 py-0.5 text-[11px] font-semibold" style="background:var(--portal-success-soft);color:var(--portal-success)">{{ t("latest") }}</span>
								</span>
								<bdi class="mt-0.5 block truncate text-xs font-mono" style="color:var(--portal-muted)">{{ s.title }}</bdi>
								<span class="mt-0.5 block text-[11px]" style="color:var(--portal-subtle)">
									{{ t("sentOn", { date: formatDate(s.created) }) }} · {{ t("fileCount", { n: s.file_count }) }}
								</span>
							</span>
							<span class="flex shrink-0 items-center gap-1 text-xs font-semibold" style="color:var(--portal-accent)">
								{{ openKeys.has(s.key) ? t("close") : t("open") }}
								<FeatherIcon :name="openKeys.has(s.key) ? 'chevron-down' : 'chevron-right'" class="h-4 w-4 rtl:rotate-180" />
							</span>
						</button>
						<ul v-if="openKeys.has(s.key)" class="divide-y border-t" style="border-color:var(--portal-border)">
							<li v-for="f in s.files" :key="f.name" class="flex items-center justify-between gap-3 px-4 py-2.5">
								<span class="min-w-0">
									<bdi class="block truncate text-sm" style="color:var(--portal-text)">{{ f.file_name }}</bdi>
									<span class="block text-[11px]" style="color:var(--portal-muted)">
										<bdi v-if="f.relative_path">{{ f.relative_path }} · </bdi>{{ fmtSize(f.file_size) }}
									</span>
								</span>
								<a
									:href="downloadUrl(f)"
									target="_blank"
									rel="noopener"
									class="flex shrink-0 items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-semibold"
									style="border-color:var(--portal-border);color:var(--portal-text)"
								>
									<FeatherIcon name="download" class="h-3.5 w-3.5" />
									{{ t("download") }}
								</a>
							</li>
						</ul>
					</article>
				</div>
			</section>
		</main>
	</div>
</template>

<style scoped>
.client-page[lang="ar"] {
	font-family: "Noto Naskh Arabic", "Segoe UI", Tahoma, sans-serif;
}
</style>
