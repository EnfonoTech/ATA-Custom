<script setup>
import { ref, onMounted, inject, computed } from "vue";
import { useRouter } from "vue-router";
import { Button, TextInput, FeatherIcon } from "frappe-ui";
import { call } from "@/api";

const router = useRouter();
const portalCapabilities = inject("portalCapabilities", ref({}));
const refreshPortalCapabilities = inject("refreshPortalCapabilities", () => Promise.resolve());
const manageCount = computed(() => (portalCapabilities.value?.manageable_project_names || []).length);
const canEditTemplate = computed(() => !!portalCapabilities.value?.can_edit_portal_folder_template);

const loading = ref(true);
const saving = ref(false);
const profile = ref(null);
const form = ref({
	full_name: "",
	mobile_no: "",
	language: "",
	time_zone: "",
});
const message = ref("");
const error = ref("");

onMounted(async () => {
	try {
		await refreshPortalCapabilities();
	} catch (e) {
		console.error(e);
	}
	try {
		profile.value = await call({ method: "portal_app.api.profile.get_my_profile" });
		form.value = {
			full_name: profile.value.full_name || "",
			mobile_no: profile.value.mobile_no || "",
			language: profile.value.language || "",
			time_zone: profile.value.time_zone || "",
		};
	} catch (e) {
		console.error(e);
		error.value = "Could not load profile.";
	} finally {
		loading.value = false;
	}
});

async function save() {
	saving.value = true;
	message.value = "";
	error.value = "";
	try {
		profile.value = await call({
			method: "portal_app.api.profile.update_my_profile",
			type: "POST",
			args: { ...form.value },
		});
		localStorage.setItem("full_name", profile.value.full_name || profile.value.name || "");
		if (profile.value.user_image != null) {
			localStorage.setItem("profile_image", profile.value.user_image || "");
		}
		message.value = "Saved.";
	} catch (e) {
		console.error(e);
		error.value = extractErr(e);
	} finally {
		saving.value = false;
	}
}

function extractErr(e) {
	const body = e?.responseBody;
	if (body?._server_messages) {
		try {
			const arr = JSON.parse(body._server_messages);
			if (arr.length) return JSON.parse(arr[0]).message || arr[0];
		} catch {
			return body._server_messages[0];
		}
	}
	return body?.message || body?.exc || "Save failed.";
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-2xl space-y-5">
			<div class="portal-hero portal-anim-in">
				<div class="relative">
					<span class="portal-pill portal-pill-accent">
						<FeatherIcon name="user" class="h-3 w-3" />
						Profile
					</span>
					<h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
						Your account
					</h1>
					<p class="mt-1 max-w-2xl text-sm text-[color:var(--portal-muted)]">
						Portal identity, roles, linked customer, and preferences.
					</p>
				</div>
			</div>

			<div v-if="loading" class="portal-card-strong flex items-center justify-center gap-2 p-10 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading…
			</div>

			<template v-else>
				<!-- Identity card -->
				<div class="portal-card-strong overflow-hidden p-0">
					<div
						class="relative h-24"
						style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #38bdf8 100%);"
					>
						<div
							aria-hidden="true"
							class="pointer-events-none absolute inset-0 opacity-30"
							style="background-image: radial-gradient(circle at 20% 50%, rgba(255,255,255,0.4), transparent 40%);"
						></div>
					</div>
					<div class="-mt-10 flex items-end gap-4 px-5 pb-5">
						<img
							v-if="profile?.user_image"
							:src="profile.user_image"
							alt=""
							class="h-20 w-20 rounded-2xl object-cover ring-4 ring-white shadow-md"
						/>
						<div
							v-else
							class="flex h-20 w-20 items-center justify-center rounded-2xl text-2xl font-semibold text-white shadow-md ring-4 ring-white"
							style="background: linear-gradient(135deg, #6366f1 0%, #38bdf8 100%);"
						>
							{{ (form.full_name || profile?.name || "?").slice(0, 1).toUpperCase() }}
						</div>
						<div class="min-w-0 flex-1 pb-1">
							<p class="text-base font-semibold text-[color:var(--portal-text)]">{{ form.full_name || profile?.name }}</p>
							<p class="truncate text-xs text-[color:var(--portal-muted)]">{{ profile?.name }}</p>
						</div>
					</div>

					<div v-if="profile?.roles?.length" class="flex flex-wrap gap-1.5 px-5 pb-5">
						<span v-for="r in profile.roles" :key="r" class="portal-pill portal-pill-muted">{{ r }}</span>
					</div>
				</div>

				<!-- Permissions -->
				<div
					v-if="manageCount > 0 || canEditTemplate"
					class="portal-callout"
				>
					<p class="portal-section-title flex items-center gap-1.5">
						<FeatherIcon name="shield" class="h-3 w-3" />
						Portal permissions
					</p>
					<ul class="mt-2 space-y-1.5 text-sm text-[color:var(--portal-text)]">
						<li v-if="manageCount > 0" class="flex items-start gap-2">
							<FeatherIcon name="check-circle" class="mt-0.5 h-3.5 w-3.5 shrink-0 text-[color:var(--portal-success)]" />
							<span>You can manage <strong>{{ manageCount }}</strong> project(s), including delete/share/rename on Files where applicable.</span>
						</li>
						<li v-if="canEditTemplate" class="flex items-start gap-2">
							<FeatherIcon name="check-circle" class="mt-0.5 h-3.5 w-3.5 shrink-0 text-[color:var(--portal-success)]" />
							<span>You can edit the <strong>company-wide subfolder template</strong> on the File tools page.</span>
						</li>
					</ul>
					<div class="mt-3 flex flex-wrap gap-2">
						<button
							class="portal-btn portal-btn-ghost text-xs"
							@click="router.push('/files')"
						>
							<FeatherIcon name="paperclip" class="h-3.5 w-3.5" />
							Open Files
						</button>
						<button
							v-if="canEditTemplate"
							class="portal-btn portal-btn-ghost text-xs"
							@click="router.push('/file-tools')"
						>
							<FeatherIcon name="sliders" class="h-3.5 w-3.5" />
							File tools
						</button>
					</div>
				</div>

				<!-- Linked customer -->
				<div
					v-if="profile?.portal_linked_customer"
					class="portal-card-strong p-4"
				>
					<div class="flex items-start gap-3">
						<div class="portal-kpi-icon shrink-0">
							<FeatherIcon name="briefcase" class="h-4 w-4" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="portal-section-title">Linked customer (portal)</p>
							<p class="mt-1 truncate font-semibold text-[color:var(--portal-text)]">
								{{ profile.portal_linked_customer_name || profile.portal_linked_customer }}
							</p>
							<p class="truncate font-mono text-xs text-[color:var(--portal-subtle)]">{{ profile.portal_linked_customer }}</p>
							<p v-if="profile.is_customer_portal_user" class="mt-2 text-xs text-[color:var(--portal-muted)]">
								You only see projects where this customer is linked.
							</p>
						</div>
					</div>
				</div>

				<!-- Preferences form -->
				<div class="portal-card-strong p-5">
					<h2 class="mb-3 flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
						<FeatherIcon name="settings" class="h-4 w-4 text-[color:var(--portal-accent)]" />
						Preferences
					</h2>
					<div class="grid gap-3 sm:grid-cols-2">
						<div class="sm:col-span-2">
							<label class="portal-section-title mb-1 block">Full name</label>
							<TextInput v-model="form.full_name" class="w-full rounded-xl" />
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Mobile</label>
							<TextInput v-model="form.mobile_no" class="w-full rounded-xl" />
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Language</label>
							<TextInput v-model="form.language" placeholder="e.g. en" class="w-full rounded-xl" />
						</div>
						<div class="sm:col-span-2">
							<label class="portal-section-title mb-1 block">Time zone</label>
							<TextInput v-model="form.time_zone" placeholder="e.g. Asia/Riyadh" class="w-full rounded-xl" />
						</div>
					</div>

					<p v-if="message" class="mt-3 text-sm text-green-700">{{ message }}</p>
					<p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>

					<div class="mt-4 flex items-center gap-2">
						<Button
							variant="solid"
							class="rounded-xl"
							style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); color: #fff;"
							:loading="saving"
							@click="save"
						>
							Save changes
						</Button>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>
