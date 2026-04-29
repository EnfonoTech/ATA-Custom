<script setup>
import { ref, inject, computed } from "vue";
import { FeatherIcon } from "frappe-ui";
import { useRoute } from "vue-router";

const route = useRoute();
const sidebarCollapsed = inject("sidebarCollapsed", ref(false));
const toggleSidebar = inject("toggleSidebar", () => {});

const collapsed = computed(() => !!sidebarCollapsed.value);

const portalAdmin = inject(
	"portalAdmin",
	ref({ can_create_users: false, can_run_demo_seed: false }),
);

const portalCapabilities = inject("portalCapabilities", ref({}));

const groups = computed(() => {
	const a = portalAdmin.value;
	const isCust = !!portalCapabilities.value?.is_customer_portal_user;

	const main = {
		title: "Workspace",
		items: [
			{ name: "Dashboard", path: "/dashboard", icon: "layout" },
			{ name: "Projects", path: "/projects", icon: "folder" },
			{ name: "Tasks", path: "/tasks", icon: "check-square" },
			{ name: "Kanban", path: "/kanban", icon: "columns" },
			{ name: "Calendar", path: "/calendar", icon: "calendar" },
		],
	};

	const work = {
		title: "Files",
		items: [
			{ name: "Files", path: "/files", icon: "paperclip" },
			{ name: "Shared with me", path: "/shared-with-me", icon: "share-2" },
		],
	};
	// "Manage shares" is the project admin's audit + revoke console — only visible
	// to users who can manage at least one project (not regular members).
	if (!isCust && (portalCapabilities.value?.manageable_project_names || []).length) {
		work.items.push({
			name: "Manage shares",
			path: "/manage-shares",
			icon: "shield",
		});
	}
	if (!isCust && portalCapabilities.value?.can_edit_portal_folder_template) {
		work.items.push({
			name: "File tools",
			path: "/file-tools",
			icon: "sliders",
		});
	}

	const account = {
		title: "Account",
		items: [{ name: "Profile", path: "/profile", icon: "user" }],
	};
	if (a?.can_create_users || a?.can_run_demo_seed) {
		account.items.push({ name: "Admin", path: "/admin", icon: "settings" });
	}

	return [main, work, account];
});

function isActiveItem(item) {
	const target = item.path.split("?")[0];
	if (route.path === target) return true;
	if (target !== "/" && route.path.startsWith(target + "/")) return true;
	return false;
}
</script>

<template>
	<aside
		class="relative flex h-screen shrink-0 flex-col border-r border-[color:var(--portal-border)] transition-[width] duration-200 ease-out"
		:class="collapsed ? 'w-[4.5rem]' : 'w-64'"
		style="background: linear-gradient(180deg, #ffffff 0%, #f7f8fb 100%);"
	>
		<!-- Brand -->
		<div
			class="flex items-center gap-3 border-b border-[color:var(--portal-border)] px-4 py-4"
			:class="collapsed ? 'justify-center px-2' : 'justify-between'"
		>
			<div class="flex min-w-0 items-center gap-3" :class="collapsed ? 'flex-col' : ''">
				<div
					class="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl text-white shadow-md"
					style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%);"
				>
					<FeatherIcon name="briefcase" class="h-5 w-5" />
				</div>
				<div v-if="!collapsed" class="min-w-0">
					<h2 class="truncate text-base font-semibold text-[color:var(--portal-text)]">Portal</h2>
					<p class="text-[11px] uppercase tracking-wider text-[color:var(--portal-muted)]">
						Projects · Files
					</p>
				</div>
			</div>
			<button
				v-if="!collapsed"
				type="button"
				class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[color:var(--portal-muted)] transition hover:bg-gray-100 hover:text-[color:var(--portal-text)]"
				title="Collapse sidebar"
				@click="toggleSidebar"
			>
				<FeatherIcon name="chevron-left" class="h-4 w-4" />
			</button>
		</div>

		<!-- Collapse arrow when collapsed -->
		<button
			v-if="collapsed"
			type="button"
			class="mx-auto mt-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[color:var(--portal-muted)] transition hover:bg-gray-100 hover:text-[color:var(--portal-text)]"
			title="Expand sidebar"
			@click="toggleSidebar"
		>
			<FeatherIcon name="chevron-right" class="h-4 w-4" />
		</button>

		<!-- Nav -->
		<nav class="flex-1 space-y-5 overflow-y-auto px-3 py-4" :class="collapsed ? 'px-1.5' : 'px-3'">
			<div v-for="group in groups" :key="group.title" class="space-y-1">
				<p
					v-if="!collapsed"
					class="px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[color:var(--portal-subtle)]"
				>
					{{ group.title }}
				</p>
				<router-link
					v-for="item in group.items"
					:key="item.path"
					:to="item.path"
					custom
					v-slot="{ navigate }"
				>
					<div
						role="link"
						tabindex="0"
						class="group relative flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
						:class="[
							isActiveItem(item)
								? 'text-[color:var(--portal-accent-strong)]'
								: 'text-[color:var(--portal-text)] hover:bg-white',
							collapsed ? 'justify-center px-2' : '',
						]"
						:style="
							isActiveItem(item)
								? 'background: linear-gradient(135deg, rgba(79,70,229,0.10) 0%, rgba(99,102,241,0.06) 100%); box-shadow: inset 0 0 0 1px rgba(79,70,229,0.2);'
								: ''
						"
						:title="collapsed ? item.name : undefined"
						@click="navigate"
						@keydown.enter="navigate"
					>
						<span
							v-if="isActiveItem(item) && !collapsed"
							class="absolute -left-3 top-1.5 bottom-1.5 w-1 rounded-r-full"
							style="background: linear-gradient(180deg, #4f46e5, #38bdf8);"
						></span>
						<FeatherIcon
							:name="item.icon"
							class="h-[18px] w-[18px] shrink-0 transition"
							:class="isActiveItem(item) ? 'text-[color:var(--portal-accent-strong)]' : 'text-[color:var(--portal-muted)] group-hover:text-[color:var(--portal-text)]'"
						/>
						<span v-if="!collapsed" class="truncate">{{ item.name }}</span>
					</div>
				</router-link>
			</div>
		</nav>

		<div
			v-if="!collapsed"
			class="m-3 rounded-xl border border-[color:var(--portal-border)] bg-white/70 px-3 py-3 text-[11px] leading-relaxed text-[color:var(--portal-muted)] backdrop-blur"
		>
			<div class="mb-1 flex items-center gap-1.5 text-[color:var(--portal-text)]">
				<FeatherIcon name="zap" class="h-3.5 w-3.5 text-[color:var(--portal-accent)]" />
				<span class="text-xs font-semibold">Quick tip</span>
			</div>
			Press
			<kbd class="rounded border border-gray-200 bg-gray-50 px-1 text-[10px]">Ctrl</kbd>
			+
			<kbd class="rounded border border-gray-200 bg-gray-50 px-1 text-[10px]">B</kbd>
			to toggle this sidebar.
		</div>
	</aside>
</template>
