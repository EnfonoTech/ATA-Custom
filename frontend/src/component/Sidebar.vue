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

// Items in "Modules" group — link to Coming Soon
const CS = (m) => `/coming-soon?m=${m}`;

const groups = computed(() => {
	const a     = portalAdmin.value;
	const isCust = !!portalCapabilities.value?.is_customer_portal_user;

	const workspace = {
		title: "Workspace",
		items: [
			{ name: "Dashboard", path: "/dashboard",  icon: "layout"       },
			{ name: "Projects",  path: "/projects",   icon: "folder"       },
			{ name: "Tasks",     path: "/tasks",       icon: "check-square" },
			{ name: "Kanban",    path: "/kanban",      icon: "columns"      },
			{ name: "Calendar",  path: "/calendar",    icon: "calendar"     },
		],
	};

	const modules = {
		title: "Modules",
		items: [
			{ name: "CRM",           path: CS("CRM"),           icon: "users",         comingSoon: true },
			{ name: "HR",            path: CS("HR"),            icon: "user",           comingSoon: true },
			{ name: "Finance",       path: CS("Finance"),       icon: "dollar-sign",    comingSoon: true },
			{ name: "Accounts",      path: CS("Accounts"),      icon: "book-open",      comingSoon: true },
			{ name: "Purchases",     path: CS("Purchases"),     icon: "shopping-cart",  comingSoon: true },
			{ name: "Stock",         path: CS("Stock"),         icon: "package",        comingSoon: true },
			{ name: "Manufacturing", path: CS("Manufacturing"), icon: "tool",           comingSoon: true },
			{ name: "Assets",        path: CS("Assets"),        icon: "server",         comingSoon: true },
			{ name: "Helpdesk",      path: CS("Helpdesk"),      icon: "headphones",     comingSoon: true },
			{ name: "Reports",       path: CS("Reports"),       icon: "bar-chart-2",    comingSoon: true },
		],
	};

	const filesItems = [
		{ name: "Files",        path: "/files",        icon: "paperclip" },
		{ name: "File Browser", path: "/file-browser", icon: "database"  },
		{ name: "Shared",       path: "/shared-with-me", icon: "share-2" },
	];
	if (!isCust && (portalCapabilities.value?.manageable_project_names || []).length) {
		filesItems.push({ name: "Shares",     path: "/manage-shares", icon: "shield" });
	}
	if (!isCust && portalCapabilities.value?.can_edit_portal_folder_template) {
		filesItems.push({ name: "File tools",     path: "/file-tools",    icon: "sliders"   });
		filesItems.push({ name: "Routing rules",  path: "/folder-rules",  icon: "git-merge" });
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

	return [workspace, modules, files, ai, account];
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
		style="background: linear-gradient(180deg, #ffffff 0%, #f7f8fb 100%);"
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
				class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[color:var(--portal-muted)] transition hover:bg-gray-100"
				title="Collapse sidebar"
				@click="toggleSidebar"
			>
				<FeatherIcon name="chevron-left" class="h-4 w-4" />
			</button>
		</div>

		<!-- Expand arrow when collapsed -->
		<button
			v-if="collapsed"
			type="button"
			class="mx-auto mt-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[color:var(--portal-muted)] transition hover:bg-gray-100"
			title="Expand sidebar"
			@click="toggleSidebar"
		>
			<FeatherIcon name="chevron-right" class="h-4 w-4" />
		</button>

		<!-- Nav -->
		<nav class="flex-1 space-y-4 overflow-y-auto py-3" :class="collapsed ? 'px-1.5' : 'px-2'">
			<div v-for="group in groups" :key="group.title" class="space-y-0.5">
				<p
					v-if="!collapsed"
					class="mb-1 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-[color:var(--portal-subtle)]"
				>
					{{ group.title }}
				</p>
				<template v-for="item in group.items" :key="item.path">
				<!-- AI item: special gradient treatment -->
				<div
					v-if="item.ai"
					role="link"
					tabindex="0"
					class="group relative flex cursor-pointer items-center gap-2.5 rounded-xl py-2 text-[13px] font-bold transition"
					:class="collapsed ? 'justify-center px-2' : 'px-3'"
					:style="isActive(item)
						? 'background:linear-gradient(135deg,#4f46e5,#7c3aed);box-shadow:0 4px 14px rgba(79,70,229,0.45);color:white'
						: 'background:linear-gradient(135deg,rgba(79,70,229,0.12),rgba(124,58,237,0.12));border:1px solid rgba(99,102,241,0.25);color:#6366f1'"
					:title="collapsed ? item.name : undefined"
					@click="navigate(item)"
					@keydown.enter="navigate(item)"
				>
					<!-- Animated pulse ring when active -->
					<span v-if="isActive(item)" class="absolute -inset-0.5 rounded-xl opacity-30"
						  style="background:linear-gradient(135deg,#6366f1,#8b5cf6);animation:pulse 2s cubic-bezier(0.4,0,0.6,1) infinite"></span>
					<FeatherIcon :name="item.icon" class="relative h-[17px] w-[17px] shrink-0" />
					<span v-if="!collapsed" class="relative truncate tracking-wide">{{ item.name }}</span>
					<span v-if="!collapsed" class="relative ml-auto flex h-1.5 w-1.5 shrink-0">
						<span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
							  :style="isActive(item) ? 'background:#a5b4fc' : 'background:#6366f1'"></span>
						<span class="relative inline-flex h-1.5 w-1.5 rounded-full"
							  :style="isActive(item) ? 'background:#e0e7ff' : 'background:#6366f1'"></span>
					</span>
				</div>

				<!-- Regular item -->
				<div
					v-else
					role="link"
					tabindex="0"
					class="group relative flex cursor-pointer items-center gap-2.5 rounded-xl py-2 text-[13px] font-medium transition"
					:class="[
						isActive(item)
							? 'text-[color:var(--portal-accent-strong)]'
							: 'text-[color:var(--portal-text)] hover:bg-gray-50',
						collapsed ? 'justify-center px-2' : 'px-3',
					]"
					:style="
						isActive(item)
							? 'background: var(--portal-accent-soft); box-shadow: inset 0 0 0 1px rgba(79,70,229,0.15);'
							: ''
					"
					:title="collapsed ? item.name : undefined"
					@click="navigate(item)"
					@keydown.enter="navigate(item)"
				>
					<!-- Active indicator bar -->
					<span
						v-if="isActive(item) && !collapsed"
						class="absolute -left-2 top-1.5 bottom-1.5 w-1 rounded-r-full"
						style="background: linear-gradient(180deg, var(--portal-accent), var(--portal-accent-strong));"
					></span>

					<FeatherIcon
						:name="item.icon"
						class="h-[17px] w-[17px] shrink-0"
						:class="isActive(item) ? 'text-[color:var(--portal-accent-strong)]' : 'text-[color:var(--portal-muted)] group-hover:text-[color:var(--portal-text)]'"
					/>
					<span v-if="!collapsed" class="truncate">{{ item.name }}</span>

					<!-- Coming soon dot -->
					<span
						v-if="!collapsed && item.comingSoon"
						class="ml-auto h-1.5 w-1.5 shrink-0 rounded-full opacity-50"
						style="background: var(--portal-accent);"
					></span>
				</div>
				</template>
			</div>
		</nav>

		<!-- Bottom hint -->
		<div
			v-if="!collapsed"
			class="m-2 rounded-xl border border-[color:var(--portal-border)] bg-white/70 px-3 py-2.5 text-[11px] leading-relaxed text-[color:var(--portal-muted)]"
		>
			<kbd class="rounded border border-gray-200 bg-gray-50 px-1 text-[10px]">Ctrl</kbd>
			+
			<kbd class="rounded border border-gray-200 bg-gray-50 px-1 text-[10px]">B</kbd>
			to toggle sidebar
		</div>
	</aside>
</template>
