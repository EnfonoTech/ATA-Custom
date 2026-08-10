<template>
	<header
		class="sticky top-0 z-40 w-full border-b"
		style="background:var(--portal-header-bg);border-color:var(--portal-border);position:sticky;overflow:visible;"
	>
		<div class="flex items-center gap-3 px-5 py-3">

			<!-- Search bar (center-ish) -->
			<div class="flex-1 max-w-lg relative">
				<div class="relative flex items-center">
					<FeatherIcon name="search" class="absolute left-3 h-4 w-4 pointer-events-none" style="color:var(--portal-subtle);"/>
					<input
						ref="searchInput"
						v-model="searchQuery"
						type="text"
						placeholder="Search projects, teams, tasks, documents..."
						class="w-full rounded-xl pl-9 pr-16 py-2 text-sm outline-none transition"
						style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);color:var(--portal-text);"
						@input="onSearchInput"
						@focus="$event.target.style.borderColor='var(--portal-accent)'; if (hasSearchResults) searchOpen = true"
						@blur="$event.target.style.borderColor='var(--portal-border-strong)'; closeSearch()"
					/>
					<div class="absolute right-2.5 flex items-center gap-0.5">
						<kbd class="rounded px-1 py-0.5 text-[10px] font-medium" style="background:var(--portal-border-strong);color:var(--portal-subtle);border:1px solid var(--portal-border-strong);">Ctrl</kbd>
						<span class="text-[10px]" style="color:var(--portal-subtle);">+</span>
						<kbd class="rounded px-1 py-0.5 text-[10px] font-medium" style="background:var(--portal-border-strong);color:var(--portal-subtle);border:1px solid var(--portal-border-strong);">K</kbd>
					</div>
				</div>

				<!-- Results dropdown -->
				<div
					v-if="searchOpen && searchQuery.trim().length >= 2"
					class="absolute left-0 right-0 top-[calc(100%+6px)] z-50 max-h-96 overflow-y-auto rounded-xl shadow-lg"
					style="background:var(--portal-surface);border:1px solid var(--portal-border);"
				>
					<div v-if="searching" class="px-4 py-3 text-xs" style="color:var(--portal-muted);">Searching…</div>
					<template v-else-if="hasSearchResults">
						<div v-if="searchResults.projects.length" class="py-1">
							<p class="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider" style="color:var(--portal-subtle);">Projects</p>
							<div
								v-for="p in searchResults.projects" :key="p.name"
								class="flex items-center gap-2 px-3 py-2 text-sm cursor-pointer transition"
								style="color:var(--portal-text);"
								@mousedown.prevent="goToProject(p)"
								@mouseenter="$event.currentTarget.style.background='var(--portal-surface-alt)'"
								@mouseleave="$event.currentTarget.style.background=''"
							>
								<FeatherIcon name="folder" class="h-3.5 w-3.5 shrink-0" style="color:var(--portal-subtle);"/>
								<span class="truncate">{{ p.project_name }}</span>
								<span class="ml-auto text-[10px]" style="color:var(--portal-subtle);">{{ p.status }}</span>
							</div>
						</div>
						<div v-if="searchResults.tasks.length" class="py-1" style="border-top:1px solid var(--portal-border);">
							<p class="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider" style="color:var(--portal-subtle);">Tasks</p>
							<div
								v-for="t in searchResults.tasks" :key="t.name"
								class="flex items-center gap-2 px-3 py-2 text-sm cursor-pointer transition"
								style="color:var(--portal-text);"
								@mousedown.prevent="goToTask(t)"
								@mouseenter="$event.currentTarget.style.background='var(--portal-surface-alt)'"
								@mouseleave="$event.currentTarget.style.background=''"
							>
								<FeatherIcon name="check-square" class="h-3.5 w-3.5 shrink-0" style="color:var(--portal-subtle);"/>
								<span class="truncate">{{ t.subject }}</span>
								<span class="ml-auto text-[10px]" style="color:var(--portal-subtle);">{{ t.status }}</span>
							</div>
						</div>
						<div v-if="searchResults.teams.length" class="py-1" style="border-top:1px solid var(--portal-border);">
							<p class="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider" style="color:var(--portal-subtle);">Teams</p>
							<div
								v-for="team in searchResults.teams" :key="team.name"
								class="flex items-center gap-2 px-3 py-2 text-sm cursor-pointer transition"
								style="color:var(--portal-text);"
								@mousedown.prevent="goToTeam(team)"
								@mouseenter="$event.currentTarget.style.background='var(--portal-surface-alt)'"
								@mouseleave="$event.currentTarget.style.background=''"
							>
								<FeatherIcon name="users" class="h-3.5 w-3.5 shrink-0" style="color:var(--portal-subtle);"/>
								<span class="truncate">{{ team.department_name }}</span>
							</div>
						</div>
					</template>
					<div v-else class="px-4 py-3 text-xs" style="color:var(--portal-muted);">No results for "{{ searchQuery }}"</div>
				</div>
			</div>

			<div class="flex items-center gap-2 ml-auto">
				<!-- Date display -->
				<div class="hidden lg:flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium"
				     style="background:var(--portal-surface-alt);color:var(--portal-muted);border:1px solid var(--portal-border-strong);">
					<FeatherIcon name="calendar" class="h-3.5 w-3.5" style="color:#f59e0b;"/>
					{{ currentDate }}
				</div>

				<!-- Dark / Light mode toggle -->
				<button
					type="button"
					class="flex h-9 w-9 items-center justify-center rounded-xl transition"
					:title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
					style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);"
					@click="toggleMode"
				>
					<FeatherIcon :name="isDark ? 'sun' : 'moon'" class="h-4 w-4" style="color:var(--portal-muted);"/>
				</button>

				<!-- Color theme picker -->
				<div class="relative" @click.stop>
					<button
						type="button"
						class="relative flex h-9 w-9 items-center justify-center rounded-xl transition"
						style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);"
						:title="'Theme: ' + activeTheme.label"
						@click="themeOpen = !themeOpen"
					>
						<span class="h-4 w-4 rounded-full border-2 border-white shadow" :style="{ background: activeTheme.color }"></span>
					</button>
					<div
						v-if="themeOpen"
						class="absolute left-0 top-full z-50 mt-2 w-52 origin-top-left overflow-hidden rounded-2xl shadow-2xl"
						style="background:var(--portal-surface-dropdown);border:1px solid var(--portal-border);"
					>
						<div class="px-3 py-2" style="border-bottom:1px solid var(--portal-border);">
							<p class="text-xs font-semibold" style="color:var(--portal-text);">Color Theme</p>
						</div>
						<div class="grid grid-cols-3 gap-1.5 p-2">
							<button
								v-for="t in THEMES"
								:key="t.key"
								type="button"
								class="flex flex-col items-center gap-1.5 rounded-xl px-2 py-2 text-[11px] font-medium transition"
								:style="currentTheme === t.key ? 'background:rgba(255,255,255,0.08);' : ''"
								@mouseenter="$event.currentTarget.style.background='rgba(255,255,255,0.05)'"
								@mouseleave="$event.currentTarget.style.background=currentTheme===t.key?'rgba(255,255,255,0.08)':''"
								@click="applyTheme(t.key)"
							>
								<span
									class="h-7 w-7 rounded-full flex items-center justify-center"
									:style="{ background: t.color, border:'2px solid rgba(255,255,255,0.15)', boxShadow:'0 2px 6px rgba(0,0,0,0.4)' }"
								>
									<svg v-if="currentTheme === t.key" viewBox="0 0 16 16" class="h-3 w-3 fill-white"><path d="M13 4L6.5 11 3 7.5"/><path fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M13 4l-6.5 7L3 7.5"/></svg>
								</span>
								<span class="text-center leading-tight" style="color:var(--portal-muted);">{{ t.label }}</span>
							</button>
						</div>
					</div>
				</div>

				<!-- Notification bell -->
				<div class="relative" @click.stop>
					<button
						type="button"
						class="relative flex h-9 w-9 items-center justify-center rounded-xl transition"
						style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);color:var(--portal-muted);"
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
						class="absolute right-0 top-full z-50 mt-2 w-80 origin-top-right overflow-hidden rounded-2xl shadow-2xl"
						style="background:var(--portal-surface-dropdown);border:1px solid var(--portal-border);"
					>
						<div class="flex items-center justify-between px-4 py-2.5" style="border-bottom:1px solid var(--portal-border);">
							<p class="text-sm font-semibold" style="color:var(--portal-text);">Notifications</p>
							<button
								v-if="notifications.length"
								class="text-xs font-medium hover:underline"
								style="color:#f59e0b;"
								@click="markAllRead"
							>
								Mark all read
							</button>
						</div>
						<div class="max-h-96 overflow-auto">
							<p v-if="notificationsLoading" class="p-4 text-center text-xs" style="color:var(--portal-muted);">Loading…</p>
							<div
								v-else-if="!notifications.length"
								class="flex flex-col items-center gap-2 p-6 text-center text-xs"
								style="color:var(--portal-muted);"
							>
								<FeatherIcon name="inbox" class="h-5 w-5" />
								You're all caught up.
							</div>
							<button
								v-for="n in notifications"
								:key="n.name"
								type="button"
								class="flex w-full items-start gap-3 px-4 py-2.5 text-left transition last:border-b-0"
								style="border-bottom:1px solid var(--portal-border);"
								@mouseenter="$event.currentTarget.style.background='rgba(255,255,255,0.03)'"
								@mouseleave="$event.currentTarget.style.background=''"
								@click="onNotificationClick(n)"
							>
								<span
									class="mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full"
									:style="n.read ? 'background:transparent;' : 'background:#f59e0b;'"
								></span>
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium" style="color:var(--portal-text);">
										{{ n.subject || "Notification" }}
									</p>
									<p class="text-[11px]" style="color:var(--portal-muted);">
										<span v-if="n.document_type">{{ n.document_type }} · </span>
										{{ fmtRelative(n.creation) }}
									</p>
								</div>
							</button>
						</div>
					</div>
				</div>
				<!-- New Project button -->
				<button
					type="button"
					class="hidden sm:inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition"
					style="background:#f59e0b;color:#0d1117;box-shadow:0 4px 12px rgba(245,158,11,0.3);"
					@mouseenter="$event.currentTarget.style.background='#fbbf24'"
					@mouseleave="$event.currentTarget.style.background='#f59e0b'"
					@click="router.push('/projects?create=1')"
				>
					<FeatherIcon name="plus" class="h-3.5 w-3.5"/>
					New Project
				</button>

				<div class="hidden text-right md:block">
					<p class="text-sm font-semibold" style="color:var(--portal-text);">{{ fullName }}</p>
					<p v-if="userEmail" class="text-[11px]" style="color:var(--portal-subtle);">{{ userEmail }}</p>
				</div>
				<div class="profile-dropdown-wrapper">
					<Dropdown :options="dropdownOptions" placement="bottom-end">
						<template #default>
							<img
								v-if="profileImage"
								:src="profileImage"
								class="h-10 w-10 cursor-pointer rounded-full object-cover transition hover:opacity-90"
								style="box-shadow:0 0 0 2px var(--portal-border-strong);"
							/>
							<div
								v-else
								class="flex h-10 w-10 cursor-pointer select-none items-center justify-center rounded-full font-semibold transition hover:opacity-90"
								style="background:linear-gradient(135deg,#f59e0b 0%,#d97706 60%,#b45309 100%);color:#0d1117;box-shadow:0 0 0 2px var(--portal-border-strong);"
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

// ── Color Themes ────────────────────────────────────────────────────────────
const THEMES = [
	{ key: "indigo", label: "Indigo",   color: "#4f46e5" },
	{ key: "sky",    label: "Sky",      color: "#0ea5e9" },
	{ key: "emerald",label: "Emerald",  color: "#059669" },
	{ key: "rose",   label: "Rose",     color: "#e11d48" },
	{ key: "amber",  label: "Amber",    color: "#d97706" },
	{ key: "brown",  label: "Brown",    color: "#92400e" },
];

// ── Dark / Light mode ───────────────────────────────────────────────────────
const isDark = ref(
	(() => { try { return localStorage.getItem("portal_mode") === "dark"; } catch { return false; } })()
);

function toggleMode() {
	isDark.value = !isDark.value;
	try { localStorage.setItem("portal_mode", isDark.value ? "dark" : "light"); } catch { /**/ }
	if (isDark.value) {
		document.documentElement.removeAttribute("data-mode");
	} else {
		document.documentElement.setAttribute("data-mode", "light");
	}
}

const currentTheme = ref(
	(() => { try { return localStorage.getItem("portal_theme") || "indigo"; } catch { return "indigo"; } })()
);
const themeOpen = ref(false);
const activeTheme = computed(() => THEMES.find(t => t.key === currentTheme.value) || THEMES[0]);

function applyTheme(key) {
	currentTheme.value = key;
	try { localStorage.setItem("portal_theme", key); } catch { /**/ }
	if (key === "indigo") {
		document.documentElement.removeAttribute("data-theme");
	} else {
		document.documentElement.setAttribute("data-theme", key);
	}
	themeOpen.value = false;
}

function onDocClickTheme(e) {
	if (!themeOpen.value) return;
	if (e.target instanceof Element && e.target.closest(".relative")) return;
	themeOpen.value = false;
}

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

const currentDate = computed(() => {
  const d = new Date();
  return d.toLocaleDateString("en-US", { weekday:"long", day:"numeric", month:"long", year:"numeric" });
});

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
	const target = e.target;
	if (bellOpen.value) {
		if (!(target instanceof Element && target.closest(".relative"))) {
			bellOpen.value = false;
		}
	}
	if (themeOpen.value) {
		if (!(target instanceof Element && target.closest(".relative"))) {
			themeOpen.value = false;
		}
	}
}

onMounted(async () => {
	// Apply saved dark/light mode
	if (!isDark.value) {
		document.documentElement.setAttribute("data-mode", "light");
	} else {
		document.documentElement.removeAttribute("data-mode");
	}
	// Apply saved accent theme
	const savedTheme = currentTheme.value;
	if (savedTheme && savedTheme !== "indigo") {
		document.documentElement.setAttribute("data-theme", savedTheme);
	}

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
	window.removeEventListener("keydown", handleGlobalKeydown);
});

// ── Global search ───────────────────────────────────────────────────────────
const searchInput   = ref(null);
const searchQuery   = ref("");
const searchOpen    = ref(false);
const searching     = ref(false);
const searchResults = ref({ projects: [], tasks: [], teams: [] });
let searchDebounce  = null;

const hasSearchResults = computed(() =>
	searchResults.value.projects.length || searchResults.value.tasks.length || searchResults.value.teams.length
);

function onSearchInput() {
	clearTimeout(searchDebounce);
	const q = searchQuery.value.trim();
	if (q.length < 2) {
		searchResults.value = { projects: [], tasks: [], teams: [] };
		searchOpen.value = false;
		return;
	}
	searchDebounce = setTimeout(async () => {
		searching.value = true;
		try {
			searchResults.value = await call({ method: "portal_app.api.search.global_search", args: { query: q } });
			searchOpen.value = true;
		} catch (e) {
			console.error("search error", e);
		} finally {
			searching.value = false;
		}
	}, 250);
}

function goToProject(p) {
	searchOpen.value = false;
	searchQuery.value = "";
	router.push({ name: "ProjectDetail", params: { name: p.name } });
}
function goToTask() {
	searchOpen.value = false;
	searchQuery.value = "";
	router.push({ name: "Tasks" });
}
function goToTeam() {
	searchOpen.value = false;
	searchQuery.value = "";
	router.push({ name: "Teams" });
}
function closeSearch() {
	setTimeout(() => { searchOpen.value = false; }, 150);
}

function handleGlobalKeydown(e) {
	if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
		e.preventDefault();
		searchInput.value?.focus();
	}
	if (e.key === "Escape") {
		searchOpen.value = false;
		searchInput.value?.blur();
	}
}
window.addEventListener("keydown", handleGlobalKeydown);

const openLogoutModal = () => {
	logoutModal.value = true;
};

const handleLogout = async () => {
	loggingOut.value = true;
	try {
		// GET, not POST: Frappe only enforces CSRF on POST/PUT/DELETE/PATCH, and the
		// cached client-side CSRF token can go stale relative to the session's actual
		// token (frappe.sessions.get_csrf_token, which call()'s stale-token retry path
		// calls, isn't even a whitelisted endpoint — that retry always 403s). A CSRF
		// failure here threw before frappe.local.login_manager.logout() ever ran, so
		// the error was caught and swallowed below, but the server session was never
		// actually terminated even though the browser moved on to the login page.
		// logout's whitelist has no explicit `methods=`, so GET is allowed, and GET
		// skips CSRF entirely — sidestepping the broken refresh path altogether.
		await call({ method: "logout", type: "GET" });
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
