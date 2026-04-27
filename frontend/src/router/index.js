import { createRouter, createWebHistory } from "vue-router";
import Login from "@/pages/Login.vue";
import Layout from "@/pages/Layout.vue";
import Dashboard from "@/pages/Dashboard.vue";
import Projects from "@/pages/Projects.vue";
import ProjectDetail from "@/pages/ProjectDetail.vue";
import Kanban from "@/pages/Kanban.vue";
import Calendar from "@/pages/Calendar.vue";
import Tasks from "@/pages/Tasks.vue";
import Files from "@/pages/Files.vue";
import FileTools from "@/pages/FileTools.vue";
import SharedFolder from "@/pages/SharedFolder.vue";
import SharedWithMe from "@/pages/SharedWithMe.vue";
import Profile from "@/pages/Profile.vue";
import Admin from "@/pages/Admin.vue";
import { call } from "@/api";

const routes = [
	{
		path: "/login",
		name: "Login",
		component: Login,
	},
	{
		path: "/shared-folder",
		name: "SharedFolder",
		component: SharedFolder,
	},
	{
		path: "/",
		component: Layout,
		children: [
			{ path: "", redirect: "/dashboard" },
			{ path: "dashboard", name: "Dashboard", component: Dashboard },
			{ path: "projects", name: "Projects", component: Projects },
			{ path: "projects/:name", name: "ProjectDetail", component: ProjectDetail, props: true },
			{ path: "kanban", name: "Kanban", component: Kanban },
			{ path: "tasks", name: "Tasks", component: Tasks },
			{ path: "calendar", name: "Calendar", component: Calendar },
			{ path: "files", name: "Files", component: Files },
			{ path: "shared-with-me", name: "SharedWithMe", component: SharedWithMe },
			{
				path: "file-tools",
				name: "FileTools",
				component: FileTools,
				meta: { requiresAuditor: true },
			},
			{ path: "profile", name: "Profile", component: Profile },
			{
				path: "admin",
				name: "Admin",
				component: Admin,
				meta: { requiresPortalAdmin: true },
			},
		],
	},
];

const router = createRouter({
	history: createWebHistory("/portal-app/"),
	routes,
});

async function checkAuth() {
	try {
		const data = await call({
			method: "portal_app.api.auth.get_logged_user",
		});
		if (data?.profile_image !== undefined) {
			localStorage.setItem("profile_image", data.profile_image || "");
		}
		if (data?.full_name !== undefined) {
			localStorage.setItem("full_name", data.full_name || "");
		}
		return !!(data && data.user);
	} catch (error) {
		console.error("Auth check failed:", error);
		return false;
	}
}

router.beforeEach(async (to) => {
	const publicPaths = new Set(["/login", "/shared-folder"]);
	const isAuthenticated = await checkAuth();

	if (!publicPaths.has(to.path) && !isAuthenticated) {
		return "/login";
	}

	if (to.path === "/login" && isAuthenticated) {
		return "/dashboard";
	}

	if (to.meta.requiresPortalAdmin && isAuthenticated) {
		try {
			const caps = await call({
				method: "portal_app.api.portal_admin.get_portal_admin_capabilities",
			});
			if (!caps?.can_create_users && !caps?.can_run_demo_seed) {
				return "/dashboard";
			}
		} catch {
			return "/dashboard";
		}
	}

	if (to.meta.requiresAuditor && isAuthenticated) {
		try {
			const caps = await call({
				method: "portal_app.api.projects.get_capabilities",
			});
			if (!caps?.can_edit_portal_folder_template) {
				return "/dashboard";
			}
		} catch {
			return "/dashboard";
		}
	}

	return true;
});

export default router;
