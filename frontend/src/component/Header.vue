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
				<div class="relative" @click.stop>
					<button
						type="button"
						class="relative flex h-9 w-9 items-center justify-center rounded-xl border border-[color:var(--portal-border)] bg-white text-[color:var(--portal-muted)] transition hover:bg-gray-50 hover:text-[color:var(--portal-text)]"
						aria-label="Notifications"
						@click="toggleBell"
					>
						<FeatherIcon name="bell" class="h-4 w-4" />
						<span
							v-if="unreadCount > 0"
							class="absolute -right-1 -top-1 flex min-w-[18px] items-center justify-center rounded-full px-1 text-[10px] font-bold text-white"
							style="background: linear-gradient(135deg, #ef4444, #f97316);"
						>
							{{ unreadCount > 99 ? "99+" : unreadCount }}
						</span>
					</button>
					<div
						v-if="bellOpen"
						class="absolute right-0 top-full z-50 mt-2 w-80 origin-top-right overflow-hidden rounded-2xl border border-[color:var(--portal-border)] bg-white shadow-2xl"
					>
						<div class="flex items-center justify-between border-b border-[color:var(--portal-border)] px-4 py-2.5">
							<p class="text-sm font-semibold text-[color:var(--portal-text)]">Notifications</p>
							<button
								v-if="notifications.length"
								class="text-xs font-medium text-[color:var(--portal-accent)] hover:underline"
								@click="markAllRead"
							>
								Mark all read
							</button>
						</div>
						<div class="max-h-96 overflow-auto">
							<p v-if="notificationsLoading" class="p-4 text-center text-xs text-[color:var(--portal-muted)]">Loading…</p>
							<div
								v-else-if="!notifications.length"
								class="flex flex-col items-center gap-2 p-6 text-center text-xs text-[color:var(--portal-muted)]"
							>
								<FeatherIcon name="inbox" class="h-5 w-5" />
								You're all caught up.
							</div>
							<button
								v-for="n in notifications"
								:key="n.name"
								type="button"
								class="flex w-full items-start gap-3 border-b border-[color:var(--portal-border)] px-4 py-2.5 text-left transition last:border-b-0 hover:bg-[color:var(--portal-bg)]"
								@click="onNotificationClick(n)"
							>
								<span
									class="mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full"
									:class="n.read ? 'bg-transparent' : 'bg-[color:var(--portal-accent)]'"
								></span>
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium text-[color:var(--portal-text)]">
										{{ n.subject || "Notification" }}
									</p>
									<p class="text-[11px] text-[color:var(--portal-muted)]">
										<span v-if="n.document_type">{{ n.document_type }} · </span>
										{{ fmtRelative(n.creation) }}
									</p>
								</div>
							</button>
						</div>
					</div>
				</div>
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
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
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

// Notification bell — backed by Frappe's Notification Log (same source as the desk bell).
const bellOpen = ref(false);
const notifications = ref([]);
const notificationsLoading = ref(false);
const unreadCount = ref(0);
let notifPollHandle;

async function loadNotifications() {
	notificationsLoading.value = true;
	try {
		const res = await call({ method: "portal_app.api.profile.list_notifications" });
		notifications.value = res?.items || [];
		unreadCount.value = res?.unread || 0;
	} catch (e) {
		// Silent — Notification Log may not be installed.
		notifications.value = [];
		unreadCount.value = 0;
	} finally {
		notificationsLoading.value = false;
	}
}

async function toggleBell() {
	bellOpen.value = !bellOpen.value;
	if (bellOpen.value) await loadNotifications();
}

async function markAllRead() {
	try {
		await call({
			method: "portal_app.api.profile.mark_notifications_read",
			type: "POST",
			args: {},
		});
		unreadCount.value = 0;
		notifications.value = notifications.value.map((n) => ({ ...n, read: 1 }));
	} catch (e) {
		/* ignore */
	}
}

async function onNotificationClick(n) {
	if (!n.read) {
		try {
			await call({
				method: "portal_app.api.profile.mark_notifications_read",
				type: "POST",
				args: { names: JSON.stringify([n.name]) },
			});
			n.read = 1;
			unreadCount.value = Math.max(0, unreadCount.value - 1);
		} catch {
			/* ignore */
		}
	}
	bellOpen.value = false;
	// Best-effort deep-link.
	if (n.document_type === "Project" && n.document_name) {
		router.push("/projects/" + encodeURIComponent(n.document_name));
	} else if (n.document_type === "Task" && n.document_name) {
		router.push("/tasks");
	}
}

function fmtRelative(s) {
	if (!s) return "";
	const dt = new Date(String(s).replace(" ", "T"));
	if (Number.isNaN(dt.getTime())) return s;
	const diff = (Date.now() - dt.getTime()) / 1000;
	if (diff < 60) return "just now";
	if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
	if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
	if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
	return dt.toLocaleDateString();
}

function onDocClick(e) {
	if (!bellOpen.value) return;
	const target = e.target;
	if (target instanceof Element && target.closest(".relative")) return; // bell wrapper has class relative
	bellOpen.value = false;
}

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
	// Initial fetch + light polling (every 60s) so the bell badge stays current.
	loadNotifications();
	notifPollHandle = setInterval(loadNotifications, 60000);
});

onBeforeUnmount(() => {
	if (notifPollHandle) clearInterval(notifPollHandle);
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
