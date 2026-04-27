<template>
	<header
		class="sticky top-0 z-40 w-full border-b border-[color:var(--portal-border)] bg-white/80 backdrop-blur"
		style="position: sticky; overflow: visible"
	>
		<div class="flex items-center justify-between gap-4 px-6 py-3">
			<div class="min-w-0">
				<p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--portal-subtle)]">
					Portal
				</p>
				<h1 class="truncate text-lg font-semibold text-[color:var(--portal-text)]">
					{{ pageTitle }}
				</h1>
			</div>

			<div class="flex items-center gap-3">
				<a
					href="/app"
					class="hidden rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-1.5 text-xs font-medium text-[color:var(--portal-muted)] transition hover:bg-gray-50 hover:text-[color:var(--portal-text)] sm:inline-flex sm:items-center sm:gap-1.5"
					title="Open ERPNext desk"
				>
					<FeatherIcon name="external-link" class="h-3.5 w-3.5" />
					Desk
				</a>
				<div class="hidden text-right md:block">
					<p class="text-sm font-semibold text-[color:var(--portal-text)]">
						{{ fullName }}
					</p>
					<p v-if="userEmail" class="text-[11px] text-[color:var(--portal-muted)]">{{ userEmail }}</p>
				</div>
				<div class="profile-dropdown-wrapper">
					<Dropdown :options="dropdownOptions" placement="bottom-end">
						<template #default>
							<img
								v-if="profileImage"
								:src="profileImage"
								class="h-10 w-10 cursor-pointer rounded-full object-cover ring-2 ring-white shadow-sm transition hover:opacity-90"
							/>
							<div
								v-else
								class="flex h-10 w-10 cursor-pointer select-none items-center justify-center rounded-full font-semibold text-white shadow-sm ring-2 ring-white transition hover:opacity-90"
								style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
							>
								{{ initials }}
							</div>
						</template>
					</Dropdown>
				</div>
			</div>
		</div>
	</header>

	<LogoutModal
		:show="logoutModal"
		:logging-out="loggingOut"
		@cancel="logoutModal = false"
		@confirm="handleLogout"
	/>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { Dropdown, FeatherIcon } from "frappe-ui";
import LogoutModal from "@/component/LogoutModal.vue";
import { call } from "@/api";

const router = useRouter();
const route = useRoute();

const fullName = ref(localStorage.getItem("full_name") || "User");
const profileImage = ref(localStorage.getItem("profile_image") || "");
const userEmail = ref(localStorage.getItem("user_email") || "");

const logoutModal = ref(false);
const loggingOut = ref(false);

const initials = computed(() =>
	fullName.value
		.split(" ")
		.map((n) => n[0])
		.join("")
		.toUpperCase()
		.slice(0, 2),
);

const pageTitle = computed(() => route.name || "Dashboard");

onMounted(async () => {
	try {
		const u = await call({ method: "portal_app.api.profile.get_my_profile" });
		if (u?.full_name) fullName.value = u.full_name;
		if (u?.user_image != null) profileImage.value = u.user_image || "";
		if (u?.email) userEmail.value = u.email;
		localStorage.setItem("full_name", fullName.value);
		localStorage.setItem("profile_image", profileImage.value);
		localStorage.setItem("user_email", userEmail.value);
	} catch (e) {
		console.error(e);
	}
});

const openLogoutModal = () => {
	logoutModal.value = true;
};

const handleLogout = async () => {
	loggingOut.value = true;
	try {
		const csrfMatch = document.cookie.match(/csrf_token=([^;]+)/);
		const csrf = csrfMatch ? decodeURIComponent(csrfMatch[1]) : "";
		await fetch("/api/method/logout", {
			method: "POST",
			credentials: "include",
			headers: {
				"Content-Type": "application/json",
				...(csrf ? { "X-Frappe-CSRF-Token": csrf } : {}),
			},
			body: "{}",
		});
	} catch (err) {
		console.error("Logout failed:", err);
	} finally {
		localStorage.removeItem("full_name");
		localStorage.removeItem("profile_image");
		localStorage.removeItem("user_email");

		logoutModal.value = false;
		loggingOut.value = false;

		window.location.href = `${window.location.origin}/portal-app/login`;
	}
};

const goProfile = () => router.push("/profile");

const dropdownOptions = computed(() => [
	{ label: "Profile", icon: "user", onClick: goProfile },
	{
		label: "Switch to Desk",
		icon: "external-link",
		onClick: () => (window.location.href = "/app"),
	},
	{ label: "Logout", icon: "log-out", onClick: openLogoutModal },
]);
</script>

<style>
.dropdown-list {
	z-index: 9999 !important;
	margin-top: 8px !important;
}

[data-radix-popper-content-wrapper],
[data-floating-ui-portal] {
	z-index: 9999 !important;
}
</style>
