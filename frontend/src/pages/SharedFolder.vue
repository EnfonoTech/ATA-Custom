<script setup>
import { ref, onMounted, computed } from "vue";
import { call } from "@/api";
import { useRoute } from "vue-router";

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
	<div class="min-h-screen bg-gray-50 p-6">
		<div class="mx-auto max-w-4xl space-y-4">
			<div>
				<h1 class="text-2xl font-bold text-gray-900">Shared folder</h1>
				<p class="text-sm text-gray-600">Read-only access via secure portal share link.</p>
			</div>

			<div v-if="loading" class="rounded-2xl border bg-white p-4 text-gray-500">Loading…</div>
			<div v-else-if="error" class="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
				{{ error }}
			</div>
			<template v-else-if="data">
				<div class="rounded-2xl border bg-white p-4 shadow-sm">
					<div class="grid gap-2 text-sm text-gray-700 sm:grid-cols-3">
						<p><strong>Project:</strong> {{ data.project_name }} ({{ data.project }})</p>
						<p><strong>Folder:</strong> {{ data.folder_label }}</p>
						<p><strong>Expires:</strong> {{ fmtTs(data.expires_at) }}</p>
					</div>
				</div>
				<div class="overflow-x-auto rounded-2xl border bg-white shadow-sm">
					<table class="w-full text-left text-sm">
						<thead>
							<tr class="border-b bg-gray-50 text-gray-600">
								<th class="px-4 py-3">File</th>
								<th class="px-4 py-3">Size</th>
								<th class="px-4 py-3">Created</th>
								<th class="px-4 py-3">Link</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="f in data.files || []" :key="f.name" class="border-b border-gray-100">
								<td class="px-4 py-3">{{ f.file_name }}</td>
								<td class="px-4 py-3">{{ f.file_size ?? "—" }}</td>
								<td class="px-4 py-3">{{ f.creation }}</td>
								<td class="px-4 py-3">
									<a v-if="f.file_url" :href="f.file_url" target="_blank" rel="noopener" class="text-blue-600 underline">
										Open
									</a>
								</td>
							</tr>
						</tbody>
					</table>
					<p v-if="!(data.files || []).length" class="p-4 text-center text-gray-500">
						No files available in this shared folder.
					</p>
				</div>
			</template>
		</div>
	</div>
</template>
