<script setup>
import { ref, provide, onErrorCaptured, onMounted, onUnmounted } from "vue";
import Sidebar from "@/component/Sidebar.vue";
import Header from "@/component/Header.vue";
import Toaster from "@/component/Toaster.vue";
import { call } from "@/api";
import { setCurrencyLocale } from "@/utils/currency";

const error = ref(null);

const sidebarCollapsed = ref(typeof localStorage !== "undefined" && localStorage.getItem("portal_sidebar_collapsed") === "1");

function toggleSidebar() {
	sidebarCollapsed.value = !sidebarCollapsed.value;
	localStorage.setItem("portal_sidebar_collapsed", sidebarCollapsed.value ? "1" : "0");
}

const portalCapabilities = ref({
	can_create_project: false,
	manageable_project_names: [],
	allowed_project_names: [],
	team_member_project_names: [],
	can_edit_portal_folder_template: false,
	portal_user: "",
});

async function loadPortalCapabilities() {
	try {
		portalCapabilities.value = await call({
			method: "portal_app.api.projects.get_capabilities",
		});
	} catch (e) {
		console.error(e);
	}
}

const portalAdmin = ref({
	can_create_users: false,
	can_run_demo_seed: false,
});

async function loadPortalAdmin() {
	try {
		portalAdmin.value = await call({
			method: "portal_app.api.portal_admin.get_portal_admin_capabilities",
		});
	} catch (e) {
		console.error(e);
	}
}

provide("sidebarCollapsed", sidebarCollapsed);
provide("toggleSidebar", toggleSidebar);
provide("portalCapabilities", portalCapabilities);
provide("refreshPortalCapabilities", loadPortalCapabilities);
provide("portalAdmin", portalAdmin);

onErrorCaptured((err) => {
	console.error("Layout caught error:", err);
	error.value = err;
	return false;
});

onMounted(async () => {
	try {
		await call({
			method: "portal_app.api.helper.get_portal_workspace_settings",
		});
		setCurrencyLocale(navigator.language || "en-US");
	} catch (err) {
		console.error("Failed to load portal settings:", err);
	}
	await loadPortalCapabilities();
	await loadPortalAdmin();

	const onKey = (e) => {
		if (!(e.ctrlKey || e.metaKey) || e.key !== "b") return;
		const t = e.target;
		if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
		e.preventDefault();
		toggleSidebar();
	};
	window.addEventListener("keydown", onKey);
	onUnmounted(() => window.removeEventListener("keydown", onKey));
});
</script>

<template>
	<div class="flex h-screen w-full overflow-hidden" style="background: var(--portal-bg)">
		<Sidebar />

		<div class="flex min-w-0 flex-1 flex-col overflow-hidden" style="background: transparent">
			<Header />
			<div class="min-h-0 flex-1 overflow-hidden">
				<div v-if="error" class="m-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 shadow-sm">
					<div class="font-semibold">Something went wrong</div>
					<div class="mt-1 text-red-700/90">{{ error.message }}</div>
				</div>

				<Suspense v-else>
					<router-view class="h-full" />
					<template #fallback>
						<div class="flex h-full items-center justify-center">
							<div class="flex items-center gap-3 rounded-xl border border-[color:var(--portal-border)] bg-white px-4 py-3 text-sm text-[color:var(--portal-muted)] shadow-sm">
								<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
								Loading…
							</div>
						</div>
					</template>
				</Suspense>
			</div>
		</div>
		<Toaster />
	</div>
</template>
