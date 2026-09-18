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

// ── Roles ────────────────────────────────────────────────────────────────────
// frappe.get_roles() returns EVERY role the user holds — for Administrator that
// is ~60, which rendered as a wall of identical grey pills and buried the ones
// that actually mean something here. Portal roles first, the rest behind a
// toggle.
const PORTAL_ROLES = [
	"System Manager",
	"Projects Manager",
	"Projects User",
	"Portal Customer",
	"Administrator",
];
const showAllRoles = ref(false);
const keyRoles = computed(() => (profile.value?.roles || []).filter((r) => PORTAL_ROLES.includes(r)));
const otherRoles = computed(() => (profile.value?.roles || []).filter((r) => !PORTAL_ROLES.includes(r)));

// ── Password ─────────────────────────────────────────────────────────────────
const pw = ref({ current_password: "", new_password: "", confirm: "" });
const pwSaving = ref(false);
const pwMessage = ref("");
const pwError = ref("");
const showPw = ref(false);

async function changePassword() {
	pwMessage.value = "";
	pwError.value = "";
	if (!pw.value.current_password || !pw.value.new_password) {
		pwError.value = "Enter your current password and the new one.";
		return;
	}
	if (pw.value.new_password !== pw.value.confirm) {
		pwError.value = "The two new passwords do not match.";
		return;
	}
	if (pw.value.new_password.length < 8) {
		pwError.value = "Your new password must be at least 8 characters long.";
		return;
	}
	pwSaving.value = true;
	try {
		await call({
			method: "portal_app.api.profile.change_my_password",
			type: "POST",
			args: {
				current_password: pw.value.current_password,
				new_password: pw.value.new_password,
				logout_other_sessions: 1,
			},
		});
		pw.value = { current_password: "", new_password: "", confirm: "" };
		pwMessage.value = "Password changed. Any other devices you were signed in on have been signed out.";
	} catch (e) {
		console.error(e);
		pwError.value = extractErr(e) || "Could not change the password.";
	} finally {
		pwSaving.value = false;
	}
}

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
					<!-- Cover. Was a flat 96px block of accent gradient and nothing else.
					     Now layered: a blueprint grid (this is an architecture practice),
					     two soft light pools, and a fade into the card so the avatar has
					     something to sit against instead of a hard colour band. -->
					<div
						class="relative h-32 overflow-hidden"
						style="background: linear-gradient(135deg, var(--portal-accent-strong) 0%, var(--portal-accent) 55%, var(--portal-accent-strong) 100%);"
					>
						<div
							aria-hidden="true"
							class="pointer-events-none absolute inset-0 opacity-[0.18]"
							style="
								background-image:
									linear-gradient(to right, rgba(255,255,255,0.9) 1px, transparent 1px),
									linear-gradient(to bottom, rgba(255,255,255,0.9) 1px, transparent 1px);
								background-size: 26px 26px;
							"
						></div>
						<div
							aria-hidden="true"
							class="pointer-events-none absolute inset-0"
							style="
								background-image:
									radial-gradient(circle at 12% 15%, rgba(255,255,255,0.55), transparent 45%),
									radial-gradient(circle at 88% 90%, rgba(0,0,0,0.28), transparent 55%);
							"
						></div>
						<!-- soft arc, echoes the drafting-compass mark in the logo -->
						<svg
							aria-hidden="true"
							class="pointer-events-none absolute -right-6 -top-10 h-48 w-48 opacity-25"
							viewBox="0 0 200 200"
							fill="none"
						>
							<circle cx="100" cy="100" r="86" stroke="#fff" stroke-width="1.5" />
							<circle cx="100" cy="100" r="60" stroke="#fff" stroke-width="1.5" />
							<circle cx="100" cy="100" r="34" stroke="#fff" stroke-width="1.5" />
							<path d="M100 0 L100 200 M0 100 L200 100" stroke="#fff" stroke-width="1" />
						</svg>
						<div
							aria-hidden="true"
							class="pointer-events-none absolute inset-x-0 bottom-0 h-12"
							style="background: linear-gradient(to bottom, transparent, var(--portal-surface));"
						></div>
					</div>
					<div class="-mt-10 flex items-end gap-4 px-5 pb-5">
						<img
							v-if="profile?.user_image"
							:src="profile.user_image"
							alt=""
							class="h-20 w-20 rounded-2xl object-cover"
					style="box-shadow: 0 0 0 4px var(--portal-surface), 0 4px 12px rgba(0,0,0,0.3);"
						/>
						<div
							v-else
							class="flex h-20 w-20 items-center justify-center rounded-2xl text-2xl font-semibold text-white"
							style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%); box-shadow: 0 0 0 4px var(--portal-surface), 0 4px 12px rgba(0,0,0,0.3);"
						>
							{{ (form.full_name || profile?.name || "?").slice(0, 1).toUpperCase() }}
						</div>
						<div class="min-w-0 flex-1 pb-1">
							<p class="text-base font-semibold text-[color:var(--portal-text)]">{{ form.full_name || profile?.name }}</p>
							<p class="truncate text-xs text-[color:var(--portal-muted)]">{{ profile?.name }}</p>
						</div>
					</div>

					<div v-if="profile?.roles?.length" class="px-5 pb-5">
						<p class="portal-section-title mb-2">Roles</p>
						<div class="flex flex-wrap items-center gap-1.5">
							<span v-for="r in keyRoles" :key="r" class="portal-pill portal-pill-accent">{{ r }}</span>
							<template v-if="showAllRoles">
								<span v-for="r in otherRoles" :key="r" class="portal-pill portal-pill-muted">{{ r }}</span>
							</template>
							<button
								v-if="otherRoles.length"
								type="button"
								class="portal-pill portal-pill-muted cursor-pointer"
								style="border-style: dashed;"
								@click="showAllRoles = !showAllRoles"
							>
								{{ showAllRoles ? "Show fewer" : `+${otherRoles.length} more` }}
							</button>
						</div>
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
							style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%); color: #fff;"
							:loading="saving"
							@click="save"
						>
							Save changes
						</Button>
					</div>
				</div>

				<!-- Password -->
				<div class="portal-card-strong p-5">
					<h2 class="mb-1 flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
						<FeatherIcon name="lock" class="h-4 w-4 text-[color:var(--portal-accent)]" />
						Password
					</h2>
					<p class="mb-3 text-sm text-[color:var(--portal-muted)]">
						Change the password you sign in with. You need your current one to do it.
					</p>

					<div class="grid gap-3 sm:grid-cols-2">
						<div class="sm:col-span-2">
							<label class="portal-section-title mb-1 block">Current password</label>
							<TextInput
								v-model="pw.current_password"
								:type="showPw ? 'text' : 'password'"
								autocomplete="current-password"
								class="w-full rounded-xl"
							/>
						</div>
						<div>
							<label class="portal-section-title mb-1 block">New password</label>
							<TextInput
								v-model="pw.new_password"
								:type="showPw ? 'text' : 'password'"
								autocomplete="new-password"
								class="w-full rounded-xl"
							/>
						</div>
						<div>
							<label class="portal-section-title mb-1 block">Confirm new password</label>
							<TextInput
								v-model="pw.confirm"
								:type="showPw ? 'text' : 'password'"
								autocomplete="new-password"
								class="w-full rounded-xl"
							/>
						</div>
					</div>

					<label class="mt-3 flex cursor-pointer items-center gap-2 text-xs text-[color:var(--portal-muted)]">
						<input v-model="showPw" type="checkbox" class="rounded" />
						Show passwords
					</label>

					<p class="mt-2 text-xs text-[color:var(--portal-subtle)]">
						At least 8 characters. Changing it signs you out everywhere else.
					</p>

					<p v-if="pwMessage" class="mt-3 text-sm text-green-700">{{ pwMessage }}</p>
					<p v-if="pwError" class="mt-3 text-sm text-red-600">{{ pwError }}</p>

					<div class="mt-4">
						<Button
							variant="solid"
							class="rounded-xl"
							style="background: linear-gradient(135deg, var(--portal-accent) 0%, var(--portal-accent-strong) 100%); color: #fff;"
							:loading="pwSaving"
							@click="changePassword"
						>
							Change password
						</Button>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>
