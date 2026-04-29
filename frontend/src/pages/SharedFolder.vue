<script setup>
import { ref, onMounted, computed } from "vue";
import { call } from "@/api";
import { useRoute } from "vue-router";
import { FeatherIcon } from "frappe-ui";

const route = useRoute();
const loading = ref(true);
const error = ref("");
const data = ref(null);

const token = computed(() => String(route.query.token || "").trim());

function fmtTs(epochSec) {
	const n = Number(epochSec || 0);
	if (!n) return "—";
	return new Date(n * 1000).toLocaleString();
}

function fmtDate(s) {
	if (!s) return "—";
	const d = new Date(String(s).replace(" ", "T"));
	return Number.isNaN(d.getTime()) ? s : d.toLocaleDateString();
}

function fileSize(bytes) {
	if (bytes == null) return "—";
	const n = Number(bytes);
	if (Number.isNaN(n) || !n) return "—";
	if (n < 1024) return `${n} B`;
	if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
	if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
	return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

async function loadSharedFolder() {
	loading.value = true;
	error.value = "";
	try {
		if (!token.value) {
			error.value = "Missing share token.";
			return;
		}
		data.value = await call({
			method: "portal_app.api.files.get_shared_folder_files",
			args: { token: token.value },
		});
	} catch (e) {
		const body = e?.responseBody;
		error.value = body?.message || body?.exc || "Failed to open shared folder.";
	} finally {
		loading.value = false;
	}
}

onMounted(loadSharedFolder);
</script>

<template>
	<div class="shared-shell">
		<!-- Cinematic backdrop -->
		<div class="shared-bg" aria-hidden="true">
			<div class="shared-orb orb-1"></div>
			<div class="shared-orb orb-2"></div>
			<div class="shared-grid"></div>
			<div class="shared-vignette"></div>
		</div>

		<div class="relative z-10 flex min-h-screen items-start justify-center p-6 sm:p-12">
			<div class="w-full max-w-4xl space-y-5">
				<!-- Hero -->
				<div class="rounded-3xl border border-white/10 bg-white/5 p-6 text-white backdrop-blur-md shadow-2xl">
					<div class="flex flex-wrap items-start justify-between gap-3">
						<div class="min-w-0">
							<div class="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-white/80">
								<FeatherIcon name="link" class="h-3 w-3" />
								Secure portal share
							</div>
							<h1 class="mt-3 text-2xl font-semibold tracking-tight">Shared folder</h1>
							<p class="mt-1 text-sm text-white/70">
								Read-only access via secure portal share link. The link expires automatically.
							</p>
						</div>
						<div v-if="data" class="flex shrink-0 items-center gap-2">
							<span class="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-xs text-white/70">
								Expires {{ fmtTs(data.expires_at) }}
							</span>
						</div>
					</div>

					<div v-if="data" class="mt-5 grid gap-3 sm:grid-cols-3">
						<div class="rounded-2xl border border-white/10 bg-black/15 p-3">
							<p class="text-[10px] font-semibold uppercase tracking-wider text-white/50">Project</p>
							<p class="mt-1 truncate text-sm font-semibold">{{ data.project_name }}</p>
							<p class="truncate font-mono text-[11px] text-white/60">{{ data.project }}</p>
						</div>
						<div class="rounded-2xl border border-white/10 bg-black/15 p-3 sm:col-span-2">
							<p class="text-[10px] font-semibold uppercase tracking-wider text-white/50">Folder</p>
							<p class="mt-1 truncate text-sm font-semibold">{{ data.folder_label }}</p>
							<p class="truncate text-[11px] text-white/60">
								{{ (data.files || []).length }} file{{ (data.files || []).length === 1 ? "" : "s" }}
							</p>
						</div>
					</div>
				</div>

				<!-- Loading -->
				<div v-if="loading" class="rounded-3xl border border-white/10 bg-white/5 p-8 text-center text-sm text-white/70 backdrop-blur-md">
					<div class="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
					Loading shared folder…
				</div>

				<!-- Error -->
				<div v-else-if="error" class="rounded-3xl border border-red-300/30 bg-red-500/10 p-6 text-sm text-red-100 backdrop-blur-md">
					<div class="flex items-start gap-3">
						<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-red-500/30 text-red-100">
							<FeatherIcon name="alert-octagon" class="h-4 w-4" />
						</div>
						<div>
							<p class="font-semibold text-white">Cannot open this share</p>
							<p class="mt-1 text-red-100/90">{{ error }}</p>
							<p class="mt-2 text-xs text-red-100/60">
								If the link has expired, ask the person who sent it to issue a new one.
							</p>
						</div>
					</div>
				</div>

				<!-- File list -->
				<template v-else-if="data">
					<div class="overflow-hidden rounded-3xl border border-white/10 bg-white/5 backdrop-blur-md shadow-xl">
						<div class="border-b border-white/10 bg-black/20 px-5 py-3 text-[10px] font-semibold uppercase tracking-wider text-white/60">
							Files ({{ (data.files || []).length }})
						</div>
						<div v-if="(data.files || []).length" class="divide-y divide-white/5">
							<div
								v-for="f in data.files || []"
								:key="f.name"
								class="flex items-center gap-3 px-5 py-3 transition hover:bg-white/5"
							>
								<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-white/80">
									<FeatherIcon name="file" class="h-4 w-4" />
								</div>
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium text-white">{{ f.file_name }}</p>
									<p class="truncate text-xs text-white/60">
										{{ fileSize(f.file_size) }} · {{ fmtDate(f.creation) }}
									</p>
								</div>
								<a
									v-if="f.file_url"
									:href="f.file_url"
									target="_blank"
									rel="noopener"
									class="flex shrink-0 items-center gap-1.5 rounded-xl border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-white/15"
								>
									<FeatherIcon name="download" class="h-3.5 w-3.5" />
									Download
								</a>
							</div>
						</div>
						<p v-else class="p-6 text-center text-sm text-white/60">
							No files available in this shared folder.
						</p>
					</div>

					<p class="text-center text-[11px] text-white/40">
						Powered by Portal · Read-only access · Authorised personnel only
					</p>
				</template>
			</div>
		</div>
	</div>
</template>

<style scoped>
.shared-shell {
	position: relative;
	min-height: 100vh;
	background: #050610;
	color: #fff;
	overflow: hidden;
	isolation: isolate;
}
.shared-bg {
	position: absolute;
	inset: 0;
	z-index: 0;
	overflow: hidden;
}
.shared-orb {
	position: absolute;
	border-radius: 9999px;
	filter: blur(90px);
	opacity: 0.55;
	animation: shared-float 26s ease-in-out infinite;
	will-change: transform;
}
.orb-1 {
	width: 700px;
	height: 700px;
	left: -200px;
	top: -180px;
	background: radial-gradient(circle, #6366f1 0%, transparent 70%);
}
.orb-2 {
	width: 600px;
	height: 600px;
	right: -160px;
	bottom: -200px;
	background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
	animation-delay: -10s;
}
@keyframes shared-float {
	0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
	50% { transform: translate3d(30px, -20px, 0) scale(1.05); }
}
.shared-grid {
	position: absolute;
	inset: 0;
	background-image:
		linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
		linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
	background-size: 56px 56px;
	mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
	-webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
.shared-vignette {
	position: absolute;
	inset: 0;
	background: radial-gradient(ellipse at center, transparent 50%, rgba(0, 0, 0, 0.55) 100%);
	pointer-events: none;
}
@media (prefers-reduced-motion: reduce) {
	.shared-orb { animation: none; }
}
</style>
