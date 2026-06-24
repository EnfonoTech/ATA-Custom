<script setup>
import { ref, inject, computed } from "vue";
import { FeatherIcon } from "frappe-ui";
import { useRoute, useRouter } from "vue-router";

const route  = useRoute();
const router = useRouter();

const sidebarCollapsed = inject("sidebarCollapsed", ref(false));
const toggleSidebar    = inject("toggleSidebar", () => {});
const collapsed        = computed(() => !!sidebarCollapsed.value);

const portalAdmin        = inject("portalAdmin", ref({ can_create_users: false, can_run_demo_seed: false }));
const portalCapabilities = inject("portalCapabilities", ref({}));
const portalSettings     = inject("portalSettings", ref({ company_logo: "", company_name: "", company_tagline: "", logo_width: 0, logo_height: 0 }));

const CS = (m) => `/coming-soon?m=${m}`;

// ── Team Structure (collapsible) ─────────────────────────────────────────
const TEAMS = [
	{ key:"cd", name:"CD Team", count:46, subTeams:[{ name:"ID Team", count:23 },{ name:"LA Team", count:23 }] },
	{ key:"dd", name:"DD Team", count:42, subTeams:[{ name:"ID Team", count:21 },{ name:"LA Team", count:21 }] },
	{ key:"td", name:"TD Team", count:40, subTeams:[{ name:"ID Team", count:20 },{ name:"LA Team", count:20 }] },
];
const ataExpanded  = ref(true);
const teamExpanded = ref({ cd:false, dd:false, td:false });
function toggleAta()     { ataExpanded.value = !ataExpanded.value; }
function toggleTeam(key) { teamExpanded.value[key] = !teamExpanded.value[key]; }

const groups = computed(() => {
	const a      = portalAdmin.value;
	const isCust = !!portalCapabilities.value?.is_customer_portal_user;

	const workspace = {
		title: "Project Management",
		items: [
			{ name: "Dashboard", path: "/dashboard", icon: "layout"       },
			{ name: "Projects",  path: "/projects",  icon: "folder"       },
			{ name: "Tasks",     path: "/tasks",      icon: "check-square" },
			{ name: "Kanban",    path: "/kanban",     icon: "columns"      },
			{ name: "Calendar",  path: "/calendar",   icon: "calendar"     },
		],
	};

	const modules = {
		title: "Modules",
		items: [
			{ name: "HR",       path: CS("HR"),       icon: "user",       comingSoon: true },
			{ name: "Accounts", path: CS("Accounts"), icon: "book-open",  comingSoon: true },
			{ name: "Stock",    path: CS("Stock"),    icon: "package",    comingSoon: true },
			{ name: "Assets",   path: CS("Assets"),   icon: "server",     comingSoon: true },
			{ name: "Helpdesk", path: CS("Helpdesk"), icon: "headphones", comingSoon: true },
		],
	};

	const filesItems = [
		{ name: "Files",        path: "/files",           icon: "paperclip" },
		{ name: "File Browser", path: "/file-browser",    icon: "database"  },
		{ name: "Shared",       path: "/shared-with-me",  icon: "share-2"   },
	];
	if (!isCust && (portalCapabilities.value?.manageable_project_names || []).length) {
		filesItems.push({ name: "Shares", path: "/manage-shares", icon: "shield" });
	}
	if (!isCust && portalCapabilities.value?.can_edit_portal_folder_template) {
		filesItems.push({ name: "File tools",    path: "/file-tools",   icon: "sliders"   });
		filesItems.push({ name: "Routing rules", path: "/folder-rules", icon: "git-merge" });
	}
	const files = { title: "Files", items: filesItems };

	const accountItems = [{ name: "Profile", path: "/profile", icon: "user" }];
	if (a?.can_create_users || a?.can_run_demo_seed) {
		accountItems.push({ name: "Admin", path: "/admin", icon: "settings" });
	}
	const account = { title: "Account", items: accountItems };

	const ai = {
		title: "AI",
		items: [{ name: "ATA AI CHAT", path: "/ai-chat", icon: "zap", ai: true }],
	};

	const analytics = {
		title: "Analytics",
		items: [
			{ name: "Reports",        path: CS("Reports"),    icon: "bar-chart-2",    comingSoon: true },
			{ name: "Resources",      path: CS("Resources"),  icon: "package",        comingSoon: true },
			{ name: "Risks & Issues", path: CS("Risks"),      icon: "alert-triangle", comingSoon: true },
			{ name: "Settings",       path: "/profile",       icon: "settings"        },
		],
	};

	return [workspace, ai, modules, files, analytics, account];
});

function isActive(item) {
	if (item.comingSoon) {
		return route.path === "/coming-soon" && route.query.m === item.path.split("=")[1];
	}
	const target = item.path.split("?")[0];
	if (route.path === target) return true;
	if (target !== "/" && route.path.startsWith(target + "/")) return true;
	return false;
}

function navigate(item) {
	router.push(item.path);
}
</script>

<template>
	<aside
		class="relative flex h-screen shrink-0 flex-col border-r border-[color:var(--portal-border)] transition-[width] duration-200 ease-out"
		:class="collapsed ? 'w-[4.5rem]' : 'w-56'"
		style="background: linear-gradient(180deg, var(--portal-sidebar-start) 0%, var(--portal-bg) 100%);"
	>
		<!-- Brand / Logo -->
		<div
			class="flex items-center gap-3 border-b border-[color:var(--portal-border)] px-4 py-3"
			:class="collapsed ? 'justify-center px-2' : 'justify-between'"
		>
			<div class="flex min-w-0 items-center gap-2.5" :class="collapsed ? 'flex-col' : ''">
				<img
					v-if="portalSettings.company_logo"
					:src="portalSettings.company_logo"
					class="shrink-0 rounded-xl object-contain"
					:class="collapsed ? 'h-9 w-9' : ''"
					:style="!collapsed ? {
						maxHeight: portalSettings.logo_height ? portalSettings.logo_height + 'px' : '44px',
						maxWidth:  portalSettings.logo_width  ? portalSettings.logo_width  + 'px' : '120px',
						width: 'auto', height: 'auto',
					} : {}"
					:title="portalSettings.company_name || 'Portal'"
				/>
				<!-- AMA lettermark fallback -->
				<svg
					v-else
					viewBox="0 0 74 62"
					fill="currentColor"
					class="shrink-0 text-[color:var(--portal-text)]"
					:class="collapsed ? 'h-8 w-auto' : 'h-10 w-auto'"
					aria-hidden="true"
				>
					<polygon points="0,4 11,4 19,58 8,58"/>
					<polygon points="23,27 30,27 35,58 28,58"/>
					<polygon points="36,30 41,30 45,58 40,58"/>
					<polygon points="46,22 54,22 59,58 51,58"/>
					<circle cx="65" cy="9" r="4.8" fill="none" stroke="currentColor" stroke-width="1"/>
					<text x="65" y="11.8" font-size="4.6" text-anchor="middle" font-weight="700" font-family="sans-serif">TM</text>
				</svg>
				<div v-if="!collapsed" class="min-w-0">
					<h2 class="truncate text-xs font-bold leading-tight tracking-wide text-[color:var(--portal-text)]" style="letter-spacing:0.06em;">
						{{ portalSettings.company_name || "ABDULMOHSIN ALTHEYAB" }}
					</h2>
					<p class="truncate text-[9px] uppercase tracking-wider text-[color:var(--portal-muted)]">
						{{ portalSettings.company_tagline || "ARCHITECTS | معماريون" }}
					</p>
				</div>
			</div>
			<button
				v-if="!collapsed"
				type="button"
				class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition"
				style="color:var(--portal-subtle);"
				title="Collapse sidebar"
				@click="toggleSidebar"
				@mouseenter="$event.currentTarget.style.background='rgba(128,128,128,0.1)'"
				@mouseleave="$event.currentTarget.style.background=''"
			>
				<FeatherIcon name="chevron-left" class="h-4 w-4" />
			</button>
		</div>

		<!-- Expand arrow when collapsed -->
		<button
			v-if="collapsed"
			type="button"
			class="mx-auto mt-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[color:var(--portal-muted)] transition"
			title="Expand sidebar"
			@click="toggleSidebar"
			@mouseenter="$event.currentTarget.style.background='rgba(128,128,128,0.1)'"
			@mouseleave="$event.currentTarget.style.background=''"
		>
			<FeatherIcon name="chevron-right" class="h-4 w-4" />
		</button>

		<!-- Nav -->
		<nav class="flex-1 space-y-4 overflow-y-auto py-3" :class="collapsed ? 'px-1.5' : 'px-2'">

			<!-- ── Project Management group ── -->
			<div class="space-y-0.5">
				<p v-if="!collapsed" class="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.14em]" style="color:var(--portal-section-label);">
					{{ groups[0].title }}
				</p>
				<template v-for="item in groups[0].items" :key="item.path">
					<div
						role="link" tabindex="0"
						class="group relative flex cursor-pointer items-center gap-2.5 rounded-xl py-2 text-[13px] font-medium transition"
						:class="collapsed ? 'justify-center px-2' : 'px-3'"
						:style="isActive(item) ? 'background:rgba(245,158,11,0.12);color:var(--portal-accent);' : 'color:var(--portal-muted);'"
						:title="collapsed ? item.name : undefined"
						@click="navigate(item)"
						@keydown.enter="navigate(item)"
						@mouseenter="!isActive(item) && ($event.currentTarget.style.background='rgba(128,128,128,0.07)')"
						@mouseleave="!isActive(item) && ($event.currentTarget.style.background='')"
					>
						<span v-if="isActive(item) && !collapsed" class="absolute -left-2 top-1.5 bottom-1.5 w-1 rounded-r-full" style="background:linear-gradient(180deg,var(--portal-accent),var(--portal-accent-strong));"></span>
						<FeatherIcon :name="item.icon" class="h-[17px] w-[17px] shrink-0" :style="isActive(item) ? 'color:var(--portal-accent);' : 'color:var(--portal-subtle);'"/>
						<span v-if="!collapsed" class="truncate">{{ item.name }}</span>
					</div>
				</template>
			</div>

			<!-- ── AI GROUP (before Team Structure) ── -->
			<div v-if="groups[1]" class="space-y-0.5">
				<p v-if="!collapsed" class="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.14em]" style="color:var(--portal-section-label);">
					{{ groups[1].title }}
				</p>
				<template v-for="item in groups[1].items" :key="item.path">
					<div
						v-if="item.ai"
						role="link" tabindex="0"
						class="group relative flex cursor-pointer items-center gap-2.5 rounded-xl py-2 text-[13px] font-bold transition"
						:class="collapsed ? 'justify-center px-2' : 'px-3'"
						:style="isActive(item)
							? 'background:linear-gradient(135deg,var(--portal-accent),var(--portal-accent-strong));box-shadow:0 4px 14px rgba(245,158,11,0.35);color:#0d1117;'
							: 'background:linear-gradient(135deg,rgba(245,158,11,0.12),rgba(217,119,6,0.12));border:1px solid rgba(245,158,11,0.25);color:var(--portal-accent);'"
						:title="collapsed ? item.name : undefined"
						@click="navigate(item)"
						@keydown.enter="navigate(item)"
					>
						<FeatherIcon :name="item.icon" class="relative h-[17px] w-[17px] shrink-0"/>
						<span v-if="!collapsed" class="relative truncate tracking-wide">{{ item.name }}</span>
						<span v-if="!collapsed" class="relative ml-auto flex h-1.5 w-1.5 shrink-0">
							<span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
							      :style="isActive(item) ? 'background:#fcd34d' : 'background:var(--portal-accent)'"></span>
							<span class="relative inline-flex h-1.5 w-1.5 rounded-full"
							      :style="isActive(item) ? 'background:#fde68a' : 'background:var(--portal-accent)'"></span>
						</span>
					</div>
				</template>
			</div>

			<!-- ── TEAM STRUCTURE ── -->
			<div class="space-y-0.5">
				<p v-if="!collapsed" class="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.14em]" style="color:var(--portal-section-label);">
					Team Structure
				</p>

				<!-- ATA Teams root -->
				<div v-if="!collapsed"
				     class="flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 text-[13px] font-medium transition"
				     style="color:var(--portal-muted);"
				     @click="toggleAta"
				     @mouseenter="$event.currentTarget.style.background='rgba(128,128,128,0.07)'"
				     @mouseleave="$event.currentTarget.style.background=''">
					<FeatherIcon name="users" class="h-[17px] w-[17px] shrink-0" style="color:var(--portal-subtle);"/>
					<span class="flex-1 truncate">ATA Teams</span>
					<span class="rounded-full px-1.5 py-0.5 text-[10px] font-bold mr-1" style="background:var(--portal-surface-alt);color:var(--portal-muted);">128</span>
					<FeatherIcon :name="ataExpanded ? 'chevron-down' : 'chevron-right'" class="h-3.5 w-3.5 shrink-0" style="color:var(--portal-subtle);"/>
				</div>
				<!-- Collapsed: icon only -->
				<div v-else class="flex justify-center py-2">
					<FeatherIcon name="users" class="h-[17px] w-[17px]" style="color:var(--portal-subtle);" title="ATA Teams"/>
				</div>

				<!-- Expanded team list -->
				<template v-if="ataExpanded && !collapsed">
					<div v-for="team in TEAMS" :key="team.key" class="ml-3">
						<!-- Team row -->
						<div class="flex cursor-pointer items-center gap-2 rounded-xl px-2.5 py-1.5 text-[12px] font-medium transition"
						     style="color:var(--portal-muted);"
						     @click="toggleTeam(team.key)"
						     @mouseenter="$event.currentTarget.style.background='rgba(128,128,128,0.06)'"
						     @mouseleave="$event.currentTarget.style.background=''">
							<span class="h-3.5 w-3.5 shrink-0 flex items-center justify-center">
								<span class="h-full w-px" style="background:var(--portal-border);"></span>
							</span>
							<span class="flex-1 truncate">{{ team.name }}</span>
							<span class="rounded-full px-1.5 py-0.5 text-[10px] font-bold" style="background:var(--portal-surface-alt);color:var(--portal-muted);">{{ team.count }}</span>
							<FeatherIcon :name="teamExpanded[team.key] ? 'chevron-down' : 'chevron-right'" class="h-3 w-3 shrink-0 ml-0.5" style="color:var(--portal-subtle);"/>
						</div>

						<!-- Sub-teams -->
						<template v-if="teamExpanded[team.key]">
							<div v-for="sub in team.subTeams" :key="sub.name"
							     class="portal-sub-team flex items-center gap-2 rounded-xl px-2.5 py-1.5 text-[11px] ml-3 cursor-default transition"
							     style="color:var(--portal-subtle);">
								<span class="h-3.5 w-3.5 shrink-0 flex items-center justify-center">
									<span class="h-full w-px" style="background:var(--portal-border);"></span>
								</span>
								<FeatherIcon name="user" class="h-3 w-3 shrink-0" style="color:var(--portal-subtle);"/>
								<span class="flex-1 truncate">{{ sub.name }}</span>
								<span class="rounded-full px-1.5 py-0.5 text-[10px] font-bold" style="background:var(--portal-surface-alt);color:var(--portal-subtle);">{{ sub.count }}</span>
							</div>
						</template>
					</div>
				</template>
			</div>

			<!-- ── Remaining groups (Modules, Files, Analytics, Account) ── -->
			<div v-for="group in groups.slice(2)" :key="group.title" class="space-y-0.5">
				<p v-if="!collapsed" class="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.14em]" style="color:var(--portal-section-label);">
					{{ group.title }}
				</p>
				<template v-for="item in group.items" :key="item.path">

					<!-- AI item -->
					<div
						v-if="item.ai"
						role="link" tabindex="0"
						class="group relative flex cursor-pointer items-center gap-2.5 rounded-xl py-2 text-[13px] font-bold transition"
						:class="collapsed ? 'justify-center px-2' : 'px-3'"
						:style="isActive(item)
							? 'background:linear-gradient(135deg,var(--portal-accent),var(--portal-accent-strong));box-shadow:0 4px 14px rgba(245,158,11,0.35);color:#0d1117;'
							: 'background:linear-gradient(135deg,rgba(245,158,11,0.12),rgba(217,119,6,0.12));border:1px solid rgba(245,158,11,0.25);color:var(--portal-accent);'"
						:title="collapsed ? item.name : undefined"
						@click="navigate(item)"
						@keydown.enter="navigate(item)"
					>
						<span v-if="isActive(item)" class="absolute -inset-0.5 rounded-xl opacity-30"
						      style="background:linear-gradient(135deg,var(--portal-accent),var(--portal-accent-strong));animation:pulse 2s cubic-bezier(0.4,0,0.6,1) infinite"></span>
						<FeatherIcon :name="item.icon" class="relative h-[17px] w-[17px] shrink-0"/>
						<span v-if="!collapsed" class="relative truncate tracking-wide">{{ item.name }}</span>
						<span v-if="!collapsed" class="relative ml-auto flex h-1.5 w-1.5 shrink-0">
							<span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
							      :style="isActive(item) ? 'background:#fcd34d' : 'background:var(--portal-accent)'"></span>
							<span class="relative inline-flex h-1.5 w-1.5 rounded-full"
							      :style="isActive(item) ? 'background:#fde68a' : 'background:var(--portal-accent)'"></span>
						</span>
					</div>

					<!-- Regular item -->
					<div
						v-else
						role="link" tabindex="0"
						class="group relative flex cursor-pointer items-center gap-2.5 rounded-xl py-2 text-[13px] font-medium transition"
						:class="collapsed ? 'justify-center px-2' : 'px-3'"
						:style="isActive(item) ? 'background:rgba(245,158,11,0.12);color:var(--portal-accent);' : 'color:var(--portal-muted);'"
						:title="collapsed ? item.name : undefined"
						@click="navigate(item)"
						@keydown.enter="navigate(item)"
						@mouseenter="!isActive(item) && ($event.currentTarget.style.background='rgba(128,128,128,0.07)')"
						@mouseleave="!isActive(item) && ($event.currentTarget.style.background='')"
					>
						<span v-if="isActive(item) && !collapsed" class="absolute -left-2 top-1.5 bottom-1.5 w-1 rounded-r-full"
						      style="background:linear-gradient(180deg,var(--portal-accent),var(--portal-accent-strong));"></span>
						<FeatherIcon :name="item.icon" class="h-[17px] w-[17px] shrink-0"
						             :style="isActive(item) ? 'color:var(--portal-accent);' : 'color:var(--portal-subtle);'"/>
						<span v-if="!collapsed" class="truncate">{{ item.name }}</span>
						<span v-if="!collapsed && item.comingSoon"
						      class="ml-auto h-1.5 w-1.5 shrink-0 rounded-full opacity-40"
						      style="background:var(--portal-subtle);"></span>
					</div>
				</template>
			</div>
		</nav>

		<!-- Bottom support card -->
		<div v-if="!collapsed" class="m-2 rounded-xl px-3 py-3" style="background:var(--portal-surface-raised);border:1px solid var(--portal-border);">
			<div class="flex items-center gap-2 mb-2">
				<div class="h-7 w-7 rounded-full flex items-center justify-center shrink-0" style="background:rgba(245,158,11,0.15);">
					<FeatherIcon name="headphones" class="h-3.5 w-3.5" style="color:var(--portal-accent);"/>
				</div>
				<div>
					<p class="text-[11px] font-semibold" style="color:var(--portal-text);">Need Help?</p>
					<p class="text-[10px]" style="color:var(--portal-subtle);">Contact support team for assistance.</p>
				</div>
			</div>
			<div class="text-[10px]" style="color:var(--portal-subtle);">
				<kbd class="rounded px-1 py-0.5" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);color:var(--portal-muted);">Ctrl</kbd>
				+
				<kbd class="rounded px-1 py-0.5" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);color:var(--portal-muted);">B</kbd>
				to toggle sidebar
			</div>
		</div>
	</aside>
</template>
