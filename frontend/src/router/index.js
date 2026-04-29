import { createRouter, createWebHistory } from "vue-router";
import { call } from "@/api";

// Layout + Login eager-load (Layout wraps every authed page; Login is the first paint
// for unauth visitors). Everything else is lazy-loaded so the initial bundle stays small.
import Layout from "@/pages/Layout.vue";
import Login from "@/pages/Login.vue";
const Dashboard     = () => import("@/pages/Dashboard.vue");
const Projects      = () => import("@/pages/Projects.vue");
const ProjectDetail = () => import("@/pages/ProjectDetail.vue");
const Kanban        = () => import("@/pages/Kanban.vue");
const Calendar      = () => import("@/pages/Calendar.vue");
const Tasks         = () => import("@/pages/Tasks.vue");
const Files         = () => import("@/pages/Files.vue");
const FileTools     = () => import("@/pages/FileTools.vue");
const SharedFolder  = () => import("@/pages/SharedFolder.vue");
const SharedWithMe  = () => import("@/pages/SharedWithMe.vue");
const ManageShares  = () => import("@/pages/ManageShares.vue");
const Profile       = () => import("@/pages/Profile.vue");
const Admin         = () => import("@/pages/Admin.vue");

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
				path: "manage-shares",
				name: "ManageShares",
				component: ManageShares,
				meta: { requiresProjectAdmin: true },
			},
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

	if (to.meta.requiresProjectAdmin && isAuthenticated) {
		try {
			const caps = await call({
				method: "portal_app.api.projects.get_capabilities",
			});
			if (!(caps?.manageable_project_names || []).length) {
				return "/dashboard";
			}
		} catch {
			return "/dashboard";
		}
	}

	return true;
});

export default router;
