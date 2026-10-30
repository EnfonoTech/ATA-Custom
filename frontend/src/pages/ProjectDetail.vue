<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, inject } from "vue";
import { call } from "@/api";
import { useRouter } from "vue-router";
import { Button, TextInput, Password, FeatherIcon } from "frappe-ui";
import FileUploadPanel from "@/component/FileUploadPanel.vue";
import { LINK_TYPES, LINK_LABELS } from "@/config/roles";

const props = defineProps({
	name: { type: String, required: true },
});

const router = useRouter();
const loading = ref(true);
const payload = ref(null);

const portalCapabilities = inject("portalCapabilities", ref({}));
const canManage = computed(() => (portalCapabilities.value?.manageable_project_names || []).includes(props.name));
const canShareFolder = computed(
	() =>
		!isCustomerPortalUser.value &&
		(portalCapabilities.value?.allowed_project_names || []).includes(props.name),
);
const canLinkCustomer = computed(() => canManage.value && !!portalCapabilities.value?.can_manage_customers);
const isManager = computed(() => !!portalCapabilities.value?.is_manager);
// What this person may do to the project's team: a Team Manager / Department Coordinator /
// Department Admin / Super Admin (or the project's Project Lead) can add people; only a
// Super Admin, Department Admin or Department Coordinator can take them off. The server
// decides, project_dashboard returns the answer.
const teamRights = computed(() => payload.value?.team_rights || { can_add: false, can_remove: false });
const canAddMembers = computed(() => !!teamRights.value.can_add);
const canRemoveMembers = computed(() => !!teamRights.value.can_remove);
const canPickFromOrgChart = computed(() => canAddMembers.value && !!portalCapabilities.value?.can_view_org_chart);
const isCustomerPortalUser = computed(() => !!portalCapabilities.value?.is_customer_portal_user);
const sessionUser = computed(() => portalCapabilities.value?.portal_user || "");

function canDeleteFileOnDetail(f) {
	if (!f || f.is_folder || isCustomerPortalUser.value) return false;
	if (canManage.value) return true;
	return !!sessionUser.value && f.owner === sessionUser.value;
}

const teamList = ref([]);
const userGroups = ref([]);
const addingGroup = ref(false);
const selectedGroup = ref("");
/** Linked customer portal users from API: { name, full_name, email } */
const customerPortalUsers = ref([]);
const cpSearchQ = ref("");
const cpHits = ref([]);
let cpSearchTimer;
const cpSaving = ref(false);
const cpMessage = ref("");
const cpError = ref("");
const showInviteCustomerUser = ref(false);
const inviteEmail = ref("");
const inviteFullName = ref("");
const invitePassword = ref("");
const inviteSendWelcome = ref(true);
const inviteBusy = ref(false);
const cpCanReset = ref(false);
const cpCanInvite = ref(false);
const cpCanLinkExisting = ref(false);
const cpWarn = ref("");
const showResetUser = ref(false);
const resetTarget = ref(null);
const resetMode = ref("email");
const resetPassword = ref("");
const resetBusy = ref(false);
const resetErr = ref("");
const customerDisplayName = ref("");
const customerSearchQ = ref("");
const customerHits = ref([]);
let customerSearchTimer;

// ── Portal Team (Department) — groups this project under a team on the Gantt
// Chart. Distinct from the "Team" section below, which manages individual
// project MEMBERS, not the department/office grouping. ─────────────────────
const deptOptions = ref([]);
const deptSearchQ = ref("");
const deptBusy = ref(false);
const deptMsg = ref("");
const deptErr = ref("");
const manualCustomerId = ref("");
const customerBusy = ref(false);
const customerMsg = ref("");
const customerErr = ref("");
const showNewCustomer = ref(false);
const newCustomerName = ref("");
const newCustomerBusy = ref(false);

const showNewTeam = ref(false);
const newTeamName = ref("");
const newTeamOffice = ref("");
const newTeamBusy = ref(false);
const teamSaving = ref(false);
const teamMessage = ref("");
const teamError = ref("");

// "Add from org chart" picker
const showOrgPicker = ref(false);
const orgChartData = ref({ teams: [], unassigned: [], super_admins: [] });
const orgLoading = ref(false);
const orgErr = ref("");
const orgSearch = ref("");
const orgPicked = ref(new Set());

const projectTitleDraft = ref("");
const titleSaving = ref(false);
const titleError = ref("");
const titleOk = ref("");

const searchQ = ref("");
const searchHits = ref([]);
let searchTimer;

const files = ref([]);
const folders = ref([]);
const projectRootPath = ref("");
const filesLoading = ref(false);
const fileDeleteError = ref("");
const deleteBusyName = ref("");

// Share button on the upload panel just hops over to the Files hub for that folder,
// where the full Drive-style Share modal lives. Keeps ProjectDetail focused.
function onOpenShareFromPanel(folderPath) {
	router.push({
		path: "/files",
		query: { project: props.name, folder: folderPath, share: "1" },
	});
}

const project = computed(() => payload.value?.project);
const teamRows = computed(() => (project.value?.users || []).filter((r) => r.user));
const tasks = computed(() => payload.value?.tasks || []);
const kanbanStage = computed(() => payload.value?.kanban_stage || "—");
const hasProjectCustomer = computed(() => !!(project.value?.customer));
const customerPortalUserIds = computed(() => new Set(customerPortalUsers.value.map((u) => u.name)));

function rememberProject(p) {
	try {
		const key = "portal_recent_projects";
		const list = JSON.parse(localStorage.getItem(key) || "[]");
		const entry = { name: p.name, project_name: p.project_name || p.name };
		const next = [entry, ...list.filter((x) => x.name !== p.name)].slice(0, 8);
		localStorage.setItem(key, JSON.stringify(next));
	} catch {
		/* ignore */
	}
}

async function loadDashboard() {
	loading.value = true;
	try {
		payload.value = await call({
			method: "portal_app.api.projects.project_dashboard",
			args: { name: props.name },
		});
		const p = payload.value?.project;
		customerDisplayName.value = payload.value?.customer_display_name || "";
		if (p) {
			rememberProject(p);
			teamList.value = (p.users || []).map((row) => row.user).filter(Boolean);
		}
		await loadCustomerPortalUsers();
	} catch (e) {
		console.error(e);
	} finally {
		loading.value = false;
	}
}

async function loadCustomerPortalUsers() {
	if (!canManage.value || !project.value?.customer) {
		customerPortalUsers.value = [];
		cpCanReset.value = false;
		cpCanInvite.value = false;
		cpCanLinkExisting.value = false;
		return;
	}
	try {
		const res = await call({
			method: "portal_app.api.projects.get_customer_portal_users",
			args: { project: props.name },
		});
		customerPortalUsers.value = res.users || [];
		cpCanReset.value = !!res.can_reset_password;
		cpCanInvite.value = !!res.can_invite;
		cpCanLinkExisting.value = !!res.can_link_existing;
	} catch (e) {
		console.error(e);
		customerPortalUsers.value = [];
		cpCanReset.value = false;
		cpCanInvite.value = false;
		cpCanLinkExisting.value = false;
	}
}

// Capabilities load in Layout after this page mounts; on a hard load the first
// loadCustomerPortalUsers() runs with canManage still false, so retry once it flips.
watch(canManage, (manage) => {
	if (manage) loadCustomerPortalUsers();
});

function formatLastLogin(value) {
	if (!value) return "";
	const d = new Date(String(value).replace(" ", "T"));
	return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
}

function openInviteCustomerUser() {
	cpError.value = "";
	cpMessage.value = "";
	cpWarn.value = "";
	inviteEmail.value = "";
	inviteFullName.value = "";
	invitePassword.value = "";
	inviteSendWelcome.value = true;
	showInviteCustomerUser.value = true;
}

function openResetUser(u) {
	resetTarget.value = u;
	resetMode.value = "email";
	resetPassword.value = "";
	resetErr.value = "";
	showResetUser.value = true;
}

async function submitResetUser() {
	if (!resetTarget.value) return;
	if (resetMode.value === "set" && resetPassword.value.length < 8) {
		resetErr.value = "The new password must be at least 8 characters.";
		return;
	}
	resetBusy.value = true;
	resetErr.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.reset_customer_portal_user_password",
			type: "POST",
			args: {
				project: props.name,
				user: resetTarget.value.name,
				mode: resetMode.value,
				new_password: resetMode.value === "set" ? resetPassword.value : undefined,
			},
		});
		const who = res?.email || resetTarget.value.email || resetTarget.value.name;
		cpMessage.value =
			resetMode.value === "email"
				? `A password reset link is on its way to ${who}.`
				: `New password set for ${who}. Their other sessions were signed out.`;
		showResetUser.value = false;
		resetPassword.value = "";
	} catch (e) {
		resetErr.value = apiErr(e);
	} finally {
		resetBusy.value = false;
	}
}

async function loadFiles() {
	filesLoading.value = true;
	fileDeleteError.value = "";
	try {
		const res = await call({
			method: "portal_app.api.files.list_project_files",
			args: { project: props.name },
		});
		files.value = res.files || [];
		folders.value = res.folders?.subfolders || [];
		projectRootPath.value = res.folders?.project_root || "";
	} catch (e) {
		console.error(e);
	} finally {
		filesLoading.value = false;
	}
}

async function deleteProjectFile(f) {
	if (!f?.name || f.is_folder || !canDeleteFileOnDetail(f)) return;
	fileDeleteError.value = "";
	if (!window.confirm(`Delete “${f.file_name}”? This removes the ERPNext File record and its attachment.`)) return;
	deleteBusyName.value = f.name;
	try {
		await call({
			method: "portal_app.api.files.delete_project_file",
			type: "POST",
			args: { file_name: f.name },
		});
		await loadFiles();
	} catch (e) {
		fileDeleteError.value = apiErr(e);
	} finally {
		deleteBusyName.value = "";
	}
}

onMounted(async () => {
	await loadDashboard();
	await loadFiles();
	loadUserGroups();
});

watch(
	() => props.name,
	async () => {
		await loadDashboard();
		await loadFiles();
	},
);

watch(
	() => project.value?.project_name,
	(n) => {
		if (typeof n === "string") projectTitleDraft.value = n;
	},
	{ immediate: true },
);

async function runCustomerSearch(q) {
	if (!canLinkCustomer.value) {
		customerHits.value = [];
		return;
	}
	try {
		customerHits.value = await call({
			method: "portal_app.api.projects.search_customers",
			args: { txt: (q || "").trim() },
		});
	} catch (e) {
		console.error(e);
		customerHits.value = [];
	}
}
watch(customerSearchQ, (q) => {
	clearTimeout(customerSearchTimer);
	customerSearchTimer = setTimeout(() => runCustomerSearch(q), 200);
});
function onCustomerFocus() {
	if (!customerHits.value.length) runCustomerSearch(customerSearchQ.value);
}

async function runCpSearch(q) {
	if (!canManage.value || !project.value?.customer) {
		cpHits.value = [];
		return;
	}
	try {
		cpHits.value = await call({
			method: "portal_app.api.projects.search_portal_users",
			args: { txt: (q || "").trim(), customer_portal: 1 },
		});
	} catch (e) {
		console.error(e);
		cpHits.value = [];
	}
}
watch(cpSearchQ, (q) => {
	clearTimeout(cpSearchTimer);
	cpSearchTimer = setTimeout(() => runCpSearch(q), 200);
});
function onCpFocus() {
	if (!cpHits.value.length) runCpSearch(cpSearchQ.value);
}

watch(searchQ, (q) => {
	clearTimeout(searchTimer);
	searchTimer = setTimeout(() => runUserSearch(q), 200);
});

/** Add people to the team right away (the server checks the caller may add to THIS project). */
async function addTeamUsers(users) {
	const fresh = [...new Set((users || []).filter((u) => u && !teamList.value.includes(u)))];
	if (!fresh.length) return false;
	teamSaving.value = true;
	teamMessage.value = "";
	teamError.value = "";
	try {
		await call({
			method: "portal_app.api.projects.add_project_members",
			type: "POST",
			args: { project: props.name, users: JSON.stringify(fresh) },
		});
		teamMessage.value = fresh.length === 1 ? "Added to the team." : `${fresh.length} people added to the team.`;
		await loadDashboard();
		return true;
	} catch (e) {
		teamError.value = apiErr(e);
		return false;
	} finally {
		teamSaving.value = false;
	}
}

async function addTeamUser(u) {
	searchQ.value = "";
	searchHits.value = [];
	await addTeamUsers([u]);
}

/** Take someone off the team (Super Admin / Department Admin only). */
async function removeTeamUser(row) {
	if (!row?.user || !canRemoveMembers.value) return;
	if (!window.confirm(`Remove ${row.full_name || row.user} from this project's team?`)) return;
	teamSaving.value = true;
	teamMessage.value = "";
	teamError.value = "";
	try {
		await call({
			method: "portal_app.api.projects.remove_project_members",
			type: "POST",
			args: { project: props.name, users: JSON.stringify([row.user]) },
		});
		teamMessage.value = "Removed from the team.";
		await loadDashboard();
	} catch (e) {
		teamError.value = apiErr(e);
	} finally {
		teamSaving.value = false;
	}
}

async function openOrgPicker() {
	orgSearch.value = "";
	orgPicked.value = new Set();
	orgErr.value = "";
	showOrgPicker.value = true;
	orgLoading.value = true;
	try {
		orgChartData.value = await call({ method: "portal_app.api.teams.get_org_chart" });
	} catch (e) {
		orgErr.value = apiErr(e);
	} finally {
		orgLoading.value = false;
	}
}

function toggleOrgPick(user) {
	const s = new Set(orgPicked.value);
	s.has(user) ? s.delete(user) : s.add(user);
	orgPicked.value = s;
}

/** The org chart as pick lists: one group per team, people already on the project are greyed. */
const orgGroups = computed(() => {
	const q = orgSearch.value.trim().toLowerCase();
	const hit = (m) => !q || (m.full_name || "").toLowerCase().includes(q) || (m.user || "").toLowerCase().includes(q);
	const groups = (orgChartData.value.teams || []).map((t) => ({
		key: t.name,
		label: t.department_name,
		office: t.office,
		people: (t.members || []).filter(hit),
	}));
	const loose = (orgChartData.value.unassigned || []).filter(hit);
	if (loose.length) groups.push({ key: "__none__", label: "Not in a team yet", office: "", people: loose });
	return groups.filter((g) => g.people.length);
});

async function submitOrgPicker() {
	if (!orgPicked.value.size) return;
	const ok = await addTeamUsers([...orgPicked.value]);
	if (ok) showOrgPicker.value = false;
	else orgErr.value = teamError.value;
}

async function loadUserGroups() {
	try {
		userGroups.value = await call({ method: "portal_app.api.teams.get_user_groups" });
	} catch (e) {
		console.error(e);
		userGroups.value = [];
	}
}

/** Add every member of the selected User Group to the team at once. */
async function addTeamUserGroup() {
	if (!selectedGroup.value) return;
	addingGroup.value = true;
	teamError.value = "";
	try {
		const members = await call({
			method: "portal_app.api.teams.get_user_group_members",
			args: { user_group: selectedGroup.value },
		});
		selectedGroup.value = "";
		await addTeamUsers(members || []);
	} catch (e) {
		teamError.value = apiErr(e);
	} finally {
		addingGroup.value = false;
	}
}

// Refs on each picker wrapper so we can detect clicks outside and close the dropdown.
const teamPickerRef = ref(null);
const customerPickerRef = ref(null);
const cpPickerRef = ref(null);

function onSearchFocus() {
	const q = (searchQ.value || "").trim();
	if (!searchHits.value.length) {
		// Mirror customer/cp behaviour — pop existing matches on focus, even with empty q.
		runUserSearch(q);
	}
}

async function runUserSearch(q) {
	try {
		searchHits.value = await call({
			method: "portal_app.api.projects.search_portal_users",
			args: { txt: (q || "").trim(), staff_only: 1 },
		});
	} catch (e) {
		console.error(e);
		searchHits.value = [];
	}
}

/** Enter key on the team-search input: add the top hit straight away. */
async function onTeamSearchEnter() {
	const top = (searchHits.value || []).find((h) => !teamList.value.includes(h.name));
	if (top) await addTeamUser(top.name);
}

function onDocClickClosePickers(e) {
	const t = e.target;
	if (teamPickerRef.value && !teamPickerRef.value.contains(t)) {
		searchHits.value = [];
	}
	if (customerPickerRef.value && !customerPickerRef.value.contains(t)) {
		customerHits.value = [];
	}
	if (cpPickerRef.value && !cpPickerRef.value.contains(t)) {
		cpHits.value = [];
	}
}

onMounted(() => document.addEventListener("click", onDocClickClosePickers));
onBeforeUnmount(() => document.removeEventListener("click", onDocClickClosePickers));

async function syncCustomerPortalUserIds(userIds) {
	cpSaving.value = true;
	cpMessage.value = "";
	cpError.value = "";
	cpWarn.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.sync_customer_portal_users",
			type: "POST",
			args: { project: props.name, users: JSON.stringify(userIds) },
		});
		// notified maps user -> false when the mail could not be queued (no outgoing
		// email account); say so instead of promising an email that never goes out.
		const entries = Object.entries(res?.notified || {});
		const sent = entries.filter(([, ok]) => ok).map(([u]) => u);
		const failed = entries.filter(([, ok]) => !ok).map(([u]) => u);
		cpWarn.value = failed.length
			? `Added ${failed.join(", ")}, but the access email could not be sent. Check the outgoing email account.`
			: "";
		cpMessage.value = sent.length
			? `Added ${sent.join(", ")}. An access email is on its way.`
			: failed.length
				? ""
				: "Saved.";
		await loadCustomerPortalUsers();
		window.setTimeout(() => {
			if (cpMessage.value === "Saved.") cpMessage.value = "";
		}, 2500);
	} catch (e) {
		cpError.value = apiErr(e);
	} finally {
		cpSaving.value = false;
	}
}

async function addCustomerPortalUserImmediate(userId) {
	if (!userId || customerPortalUserIds.value.has(userId) || cpSaving.value) return;
	const next = [...customerPortalUsers.value.map((u) => u.name), userId];
	cpSearchQ.value = "";
	cpHits.value = [];
	await syncCustomerPortalUserIds(next);
}

async function removeCustomerPortalUserImmediate(userId) {
	if (!userId || cpSaving.value) return;
	const next = customerPortalUsers.value.map((u) => u.name).filter((x) => x !== userId);
	await syncCustomerPortalUserIds(next);
}

async function submitInviteCustomerUser() {
	if (!inviteEmail.value.trim() || !inviteFullName.value.trim()) {
		cpError.value = "Email and full name are required.";
		return;
	}
	if (invitePassword.value && invitePassword.value.length < 8) {
		cpError.value = "A password set here must be at least 8 characters (or leave it blank).";
		return;
	}
	inviteBusy.value = true;
	cpError.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.create_customer_portal_user_from_project",
			type: "POST",
			args: {
				project: props.name,
				email: inviteEmail.value.trim(),
				full_name: inviteFullName.value.trim(),
				password: invitePassword.value || undefined,
				send_welcome_email: inviteSendWelcome.value ? 1 : 0,
			},
		});
		const who = res?.email || inviteEmail.value.trim();
		const linked = res?.created
			? `Created ${who} and linked them to this customer.`
			: `Linked the existing user ${who} to this customer — they keep their current password.`;
		cpWarn.value = "";
		if (inviteSendWelcome.value && res?.email_sent) {
			cpMessage.value = `${linked} An invite email is on its way.`;
		} else if (inviteSendWelcome.value) {
			cpMessage.value = linked;
			cpWarn.value = "The invite email could not be sent — check the outgoing email account.";
		} else {
			cpMessage.value = res?.created ? `${linked} No email was sent; share the password with them yourself.` : linked;
		}
		showInviteCustomerUser.value = false;
		inviteEmail.value = "";
		inviteFullName.value = "";
		invitePassword.value = "";
		await loadCustomerPortalUsers();
	} catch (e) {
		cpError.value = apiErr(e);
	} finally {
		inviteBusy.value = false;
	}
}

// ── Project links (T Server / Autodesk Server / ERP) ─────────────────────────
// project_dashboard sends portal_links; the path / URL is only there when can_open.
// A locked link is a disabled button: nothing to open, nothing in the page to leak.
const LOCKED_HINT = "Ask your Department Coordinator for access";
const LINK_ICONS = { "T Server": "hard-drive", "Autodesk Server": "box", ERP: "server" };
const projectLinks = computed(() => {
	const by = Object.fromEntries((payload.value?.portal_links || []).map((e) => [e.link_type, e]));
	return LINK_TYPES.map((t) => by[t] || { link_type: t, has_path: 0, has_url: 0, can_open: 0 });
});
const showLinksCard = computed(() => !isCustomerPortalUser.value && !!payload.value?.portal_links);
const canManageLinks = computed(() => !!payload.value?.can_manage_links);
const linkMsg = ref("");
function linkState(e) {
	if (!e || (!e.has_path && !e.has_url)) return "unset";
	return e.can_open ? "open" : "locked";
}
async function copyText(text) {
	try {
		await navigator.clipboard.writeText(text);
	} catch {
		const ta = document.createElement("textarea");
		ta.value = text;
		ta.setAttribute("readonly", "");
		ta.style.position = "fixed";
		ta.style.opacity = "0";
		document.body.appendChild(ta);
		ta.select();
		try { document.execCommand("copy"); } finally { document.body.removeChild(ta); }
	}
}
async function copyLinkPath(e) {
	if (linkState(e) !== "open" || !e.copy_path) return;
	await copyText(e.copy_path);
	linkMsg.value = `${LINK_LABELS[e.link_type] || e.link_type} path copied.`;
	setTimeout(() => (linkMsg.value = ""), 3000);
}

// "Manage links" (the project's Department Coordinator / Department Admin / Super Admin)
const showLinks = ref(false);
const linksBusy = ref(false);
const linksErr = ref("");
const linksForm = ref({}); // link_type -> { copy_path, open_url, allowed_users: [{ user, full_name }] }
let linksOriginal = {};
const linkUserQ = ref({});
const linkUserHits = ref({});
let linkUserTimer;

function linkSnapshot(f) {
	return JSON.stringify([f.copy_path || "", f.open_url || "", (f.allowed_users || []).map((u) => u.user)]);
}
async function openManageLinks() {
	linksErr.value = "";
	try {
		const res = await call({ method: "portal_app.api.links.get_project_links", args: { project: props.name } });
		const form = {};
		for (const e of res?.links || []) {
			form[e.link_type] = {
				copy_path: e.copy_path || "",
				open_url: e.open_url || "",
				allowed_users: (e.allowed_users || []).map((u) => ({ user: u.user, full_name: u.full_name })),
			};
		}
		linksForm.value = form;
		linksOriginal = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, linkSnapshot(v)]));
		linkUserQ.value = {};
		linkUserHits.value = {};
		showLinks.value = true;
	} catch (e) {
		linkMsg.value = apiErr(e);
	}
}
function searchLinkUsers(type) {
	clearTimeout(linkUserTimer);
	const q = (linkUserQ.value[type] || "").trim();
	if (q.length < 2) {
		linkUserHits.value = { ...linkUserHits.value, [type]: [] };
		return;
	}
	linkUserTimer = setTimeout(async () => {
		try {
			const hits = await call({
				method: "portal_app.api.projects.search_portal_users",
				args: { txt: q, staff_only: 1 },
			});
			linkUserHits.value = { ...linkUserHits.value, [type]: hits || [] };
		} catch {
			linkUserHits.value = { ...linkUserHits.value, [type]: [] };
		}
	}, 250);
}
function addLinkUser(type, u) {
	const f = linksForm.value[type];
	if (!f.allowed_users.some((x) => x.user === u.name)) f.allowed_users.push({ user: u.name, full_name: u.full_name || u.name });
	linkUserQ.value = { ...linkUserQ.value, [type]: "" };
	linkUserHits.value = { ...linkUserHits.value, [type]: [] };
}
function removeLinkUser(type, user) {
	const f = linksForm.value[type];
	f.allowed_users = f.allowed_users.filter((x) => x.user !== user);
}
async function saveLinks() {
	linksBusy.value = true;
	linksErr.value = "";
	try {
		let latest = null;
		for (const type of LINK_TYPES) {
			const f = linksForm.value[type];
			if (!f || linkSnapshot(f) === linksOriginal[type]) continue;
			latest = await call({
				method: "portal_app.api.links.save_project_link",
				type: "POST",
				args: {
					project: props.name,
					link_type: type,
					copy_path: f.copy_path || "",
					open_url: (f.open_url || "").trim(),
					allowed_users: JSON.stringify(f.allowed_users.map((u) => u.user)),
				},
			});
			linksOriginal[type] = linkSnapshot(f);
		}
		if (latest?.links && payload.value) payload.value = { ...payload.value, portal_links: latest.links };
		showLinks.value = false;
	} catch (e) {
		linksErr.value = apiErr(e);
	} finally {
		linksBusy.value = false;
	}
}

function apiErr(e) {
	const body = e?.responseBody;
	if (body?._server_messages) {
		try {
			const arr = JSON.parse(body._server_messages);
			if (arr.length) return JSON.parse(arr[0]).message || arr[0];
		} catch {
			return String(body._server_messages[0]);
		}
	}
	return body?.message || body?.exc || "Request failed.";
}

async function saveProjectTitle() {
	const t = projectTitleDraft.value.trim();
	if (t.length < 2) {
		titleError.value = "Enter a title of at least 2 characters.";
		return;
	}
	titleSaving.value = true;
	titleError.value = "";
	titleOk.value = "";
	try {
		await call({
			method: "portal_app.api.projects.rename_project",
			type: "POST",
			args: { project: props.name, project_name: t },
		});
		titleOk.value = "Title saved.";
		await loadDashboard();
		window.setTimeout(() => {
			titleOk.value = "";
		}, 2500);
	} catch (e) {
		titleError.value = apiErr(e);
	} finally {
		titleSaving.value = false;
	}
}

async function linkCustomer(customerId) {
	if (!customerId) return;
	customerBusy.value = true;
	customerMsg.value = "";
	customerErr.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.set_project_customer",
			type: "POST",
			args: { project: props.name, customer: customerId },
		});
		customerDisplayName.value = res.customer_display_name || "";
		customerSearchQ.value = "";
		customerHits.value = [];
		customerMsg.value = "Customer linked.";
		await loadDashboard();
		await loadCustomerPortalUsers();
	} catch (e) {
		customerErr.value = apiErr(e);
	} finally {
		customerBusy.value = false;
	}
}

async function clearCustomer() {
	customerBusy.value = true;
	customerMsg.value = "";
	customerErr.value = "";
	try {
		await call({
			method: "portal_app.api.projects.set_project_customer",
			type: "POST",
			args: { project: props.name, customer: "" },
		});
		customerDisplayName.value = "";
		customerMsg.value = "Customer cleared.";
		await loadDashboard();
	} catch (e) {
		customerErr.value = apiErr(e);
	} finally {
		customerBusy.value = false;
	}
}

async function loadDeptOptions() {
	if (deptOptions.value.length) return;
	try {
		deptOptions.value = await call({ method: "portal_app.api.teams.get_teams" });
	} catch (e) {
		console.error(e);
		deptOptions.value = [];
	}
}
const deptHits = computed(() => {
	const q = deptSearchQ.value.trim().toLowerCase();
	const list = q
		? deptOptions.value.filter((d) => d.department_name.toLowerCase().includes(q))
		: deptOptions.value;
	return list.slice(0, 25);
});

async function setProjectTeam(deptName) {
	deptBusy.value = true;
	deptMsg.value = "";
	deptErr.value = "";
	try {
		await call({
			method: "portal_app.api.projects.update_project",
			type: "POST",
			args: { project: props.name, portal_team: deptName },
		});
		deptSearchQ.value = "";
		deptMsg.value = deptName ? "Team set." : "Team cleared.";
		await loadDashboard();
		window.setTimeout(() => (deptMsg.value = ""), 2500);
	} catch (e) {
		deptErr.value = apiErr(e);
	} finally {
		deptBusy.value = false;
	}
}

async function submitNewTeam() {
	const n = newTeamName.value.trim();
	if (n.length < 2) {
		deptErr.value = "Enter a team name.";
		return;
	}
	newTeamBusy.value = true;
	deptErr.value = "";
	try {
		const res = await call({
			method: "portal_app.api.teams.create_or_get_team",
			type: "POST",
			args: { department_name: n, office: newTeamOffice.value.trim() },
		});
		showNewTeam.value = false;
		newTeamName.value = "";
		newTeamOffice.value = "";
		deptOptions.value = []; // force a fresh fetch so the new team shows up in the picker
		await setProjectTeam(res.name);
	} catch (e) {
		deptErr.value = apiErr(e);
	} finally {
		newTeamBusy.value = false;
	}
}

async function applyManualCustomer() {
	const id = manualCustomerId.value.trim();
	if (!id) return;
	await linkCustomer(id);
	manualCustomerId.value = "";
}

async function submitNewCustomer() {
	const n = newCustomerName.value.trim();
	if (n.length < 2) {
		customerErr.value = "Enter a customer name.";
		return;
	}
	newCustomerBusy.value = true;
	customerErr.value = "";
	try {
		const res = await call({
			method: "portal_app.api.projects.create_or_get_customer",
			type: "POST",
			args: { customer_name: n },
		});
		showNewCustomer.value = false;
		newCustomerName.value = "";
		await linkCustomer(res.name);
	} catch (e) {
		customerErr.value = apiErr(e);
	} finally {
		newCustomerBusy.value = false;
	}
}
</script>

<template>
	<div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
		<div class="mx-auto max-w-6xl space-y-6">
			<button
				type="button"
				class="inline-flex items-center gap-1.5 text-sm font-medium text-[color:var(--portal-muted)] transition hover:text-[color:var(--portal-text)]"
				@click="router.push('/projects')"
			>
				<FeatherIcon name="arrow-left" class="h-4 w-4" />
				Back to projects
			</button>

			<div v-if="loading" class="flex items-center gap-2 text-[color:var(--portal-muted)]">
				<span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
				Loading…
			</div>

			<template v-else-if="project">
				<!-- Hero -->
				<div class="portal-hero portal-anim-in">
					<div class="relative flex flex-wrap items-start justify-between gap-4">
						<div class="min-w-0 flex-1">
							<div class="flex flex-wrap items-center gap-2">
								<span class="portal-pill portal-pill-accent">
									<FeatherIcon name="folder" class="h-3 w-3" />
									Project
								</span>
								<span v-if="project.status" class="portal-pill portal-pill-muted">{{ project.status }}</span>
								<span v-if="kanbanStage && kanbanStage !== '—'" class="portal-pill portal-pill-muted">
									<FeatherIcon name="trello" class="h-3 w-3" />
									{{ kanbanStage }}
								</span>
							</div>
							<h1 class="mt-2 truncate text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
								{{ project.project_name }}
							</h1>
							<p class="mt-1 text-sm text-[color:var(--portal-muted)]">
								<span class="font-mono">{{ project.name }}</span>
							</p>
						</div>
						<div class="flex shrink-0 flex-wrap items-center gap-2">
							<button
								type="button"
								class="portal-btn"
								@click="router.push({ path: '/files', query: { project: project.name } })"
							>
								<FeatherIcon name="paperclip" class="h-4 w-4" />
								Files
							</button>
							<button
								v-if="!isCustomerPortalUser"
								type="button"
								class="portal-btn"
								@click="router.push({ path: '/tasks', query: { project: project.name } })"
							>
								<FeatherIcon name="check-square" class="h-4 w-4" />
								Tasks
							</button>
						</div>
					</div>

					<div v-if="canManage" class="mt-5 rounded-xl border border-[color:var(--portal-border)] bg-white/70 p-3 backdrop-blur">
						<p class="portal-section-title">Rename project</p>
						<div class="mt-2 flex flex-wrap items-center gap-2">
							<TextInput v-model="projectTitleDraft" class="max-w-xl flex-1 rounded-xl" />
							<Button
								variant="solid"
								class="rounded-xl bg-black text-white"
								:loading="titleSaving"
								@click="saveProjectTitle"
							>
								Save title
							</Button>
						</div>
						<p v-if="titleError" class="mt-2 text-sm text-red-600">{{ titleError }}</p>
						<p v-if="titleOk" class="mt-2 text-sm text-green-700">{{ titleOk }}</p>
					</div>
				</div>

				<!-- KPI grid -->
				<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="activity" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Status</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">{{ project.status || "—" }}</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="trello" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Kanban stage</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">{{ kanbanStage }}</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="user" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Client</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">
								{{ customerDisplayName || project.customer || "—" }}
							</p>
							<p v-if="project.customer" class="truncate text-xs text-[color:var(--portal-subtle)]">{{ project.customer }}</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="calendar" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Timeline</p>
							<p class="mt-1 text-sm text-[color:var(--portal-text)]">
								{{ project.expected_start_date || "—" }}
								<span class="mx-1 text-[color:var(--portal-subtle)]">→</span>
								{{ project.expected_end_date || "—" }}
							</p>
						</div>
					</div>
					<div v-if="isManager" class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="credit-card" class="h-4 w-4" /></div>
						<div class="min-w-0">
							<p class="portal-section-title">Estimated cost</p>
							<p class="mt-1 truncate text-base font-semibold text-[color:var(--portal-text)]">
								{{ project.estimated_costing ? `SAR ${Number(project.estimated_costing).toLocaleString()}` : "—" }}
							</p>
						</div>
					</div>
					<div class="portal-kpi">
						<div class="portal-kpi-icon"><FeatherIcon name="bar-chart-2" class="h-4 w-4" /></div>
						<div class="min-w-0 flex-1">
							<p class="portal-section-title">Progress</p>
							<div class="mt-1 flex items-center gap-2">
								<p class="text-base font-semibold text-[color:var(--portal-text)]">{{ project.percent_complete ?? 0 }}%</p>
							</div>
							<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--portal-bg-dim)]">
								<div
									class="h-full rounded-full transition-all"
									:style="{
										width: Math.min(100, Math.max(0, Number(project.percent_complete) || 0)) + '%',
										background: 'linear-gradient(90deg, var(--portal-accent), var(--portal-accent-strong))',
									}"
								></div>
							</div>
						</div>
					</div>
				</div>

				<!-- Project links (T Server / Autodesk Server / ERP) -->
				<div v-if="showLinksCard" class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="link" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Project links
						</h2>
						<button v-if="canManageLinks" type="button" class="portal-btn" @click="openManageLinks">
							<FeatherIcon name="settings" class="h-4 w-4" />
							Manage links
						</button>
					</div>
					<div class="space-y-2">
						<div
							v-for="e in projectLinks"
							:key="e.link_type"
							class="flex flex-wrap items-center gap-3 rounded-xl border border-[color:var(--portal-border)] px-3 py-2.5"
						>
							<FeatherIcon :name="LINK_ICONS[e.link_type] || 'link'" class="h-4 w-4 shrink-0 text-[color:var(--portal-muted)]" />
							<div class="min-w-0 flex-1">
								<p class="text-sm font-semibold text-[color:var(--portal-text)]">{{ LINK_LABELS[e.link_type] || e.link_type }}</p>
								<p v-if="linkState(e) === 'open' && e.copy_path" class="truncate font-mono text-xs text-[color:var(--portal-muted)]" :title="e.copy_path">{{ e.copy_path }}</p>
								<p v-else-if="linkState(e) === 'locked'" class="text-xs text-[color:var(--portal-subtle)]">{{ LOCKED_HINT }}</p>
								<p v-else-if="linkState(e) === 'unset'" class="text-xs text-[color:var(--portal-subtle)]">Not set</p>
							</div>
							<template v-if="linkState(e) === 'open'">
								<button v-if="e.copy_path" type="button" class="portal-btn" @click="copyLinkPath(e)">
									<FeatherIcon name="copy" class="h-4 w-4" />
									Copy
								</button>
								<a
									v-if="e.open_url"
									:href="e.open_url"
									target="_blank"
									rel="noopener noreferrer"
									class="portal-btn"
								>
									<FeatherIcon name="external-link" class="h-4 w-4" />
									Open
								</a>
							</template>
							<template v-else-if="linkState(e) === 'locked'">
								<button
									v-if="e.has_path"
									type="button"
									class="portal-btn cursor-not-allowed opacity-50"
									disabled
									aria-disabled="true"
									:title="LOCKED_HINT"
								>
									<FeatherIcon name="lock" class="h-4 w-4" />
									Copy
								</button>
								<button
									v-if="e.has_url"
									type="button"
									class="portal-btn cursor-not-allowed opacity-50"
									disabled
									aria-disabled="true"
									:title="LOCKED_HINT"
								>
									<FeatherIcon name="lock" class="h-4 w-4" />
									Open
								</button>
							</template>
							<button
								v-if="e.link_type === 'ERP'"
								type="button"
								class="portal-btn"
								@click="router.push({ path: '/files', query: { project: project.name } })"
							>
								<FeatherIcon name="folder" class="h-4 w-4" />
								Project files
							</button>
						</div>
					</div>
					<p v-if="linkMsg" class="mt-2 text-sm text-[color:var(--portal-muted)]">{{ linkMsg }}</p>
				</div>

				<div class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="user" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Customer
						</h2>
					</div>
					<p class="mb-3 text-sm text-gray-600">
						Links this project to a <strong>Customer</strong> record. Client Customer logins only see projects for their linked customer.
					</p>
					<div v-if="canManage" class="space-y-3">
						<template v-if="canLinkCustomer">
							<label class="text-xs font-medium text-gray-600">Search customers</label>
							<div ref="customerPickerRef" class="space-y-2" @focusin="onCustomerFocus">
								<TextInput
									v-model="customerSearchQ"
									class="w-full rounded-xl"
									placeholder="Click to see existing customers, or type to filter…"
								/>
								<div
									v-if="customerHits.length"
									class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
								>
									<button
										v-for="c in customerHits"
										:key="c.name"
										type="button"
										class="flex w-full flex-col gap-0.5 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white"
										@click="linkCustomer(c.name)"
									>
										<span class="font-medium text-gray-900">{{ c.customer_name || c.name }}</span>
										<span class="text-xs text-gray-500">{{ c.name }}</span>
									</button>
								</div>
							</div>
							<div class="flex flex-wrap gap-2">
								<button
									type="button"
									class="rounded-xl border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-50"
									@click="showNewCustomer = true"
								>
									Create customer (no duplicate name)
								</button>
								<button
									v-if="project.customer"
									type="button"
									class="rounded-xl border border-red-200 px-3 py-2 text-sm text-red-700 hover:bg-red-50"
									:disabled="customerBusy"
									@click="clearCustomer"
								>
									Clear customer
								</button>
							</div>
						</template>
						<template v-else>
							<label class="text-xs font-medium text-gray-600">Customer ID (from Desk)</label>
							<div class="flex flex-wrap gap-2">
								<TextInput v-model="manualCustomerId" class="min-w-[200px] flex-1 rounded-xl" placeholder="e.g. CUST-00001" />
								<Button
									variant="solid"
									class="rounded-xl bg-black text-white"
									:loading="customerBusy"
									@click="applyManualCustomer"
								>
									Link
								</Button>
								<button
									v-if="project.customer"
									type="button"
									class="rounded-xl border border-red-200 px-3 py-2 text-sm text-red-700"
									:disabled="customerBusy"
									@click="clearCustomer"
								>
									Clear
								</button>
							</div>
						</template>
						<p v-if="customerMsg" class="text-sm text-green-700">{{ customerMsg }}</p>
						<p v-if="customerErr" class="text-sm text-red-600">{{ customerErr }}</p>
						<div
							v-if="hasProjectCustomer && cpCanInvite"
							class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-3"
						>
							<p class="min-w-0 flex-1 text-sm text-gray-700">
								Give someone at <strong>{{ customerDisplayName || project.customer }}</strong> a portal login. They get
								a welcome email, set their own password, and see this customer’s projects.
							</p>
							<Button variant="solid" class="rounded-xl bg-black text-white" @click="openInviteCustomerUser">
								Invite customer user
							</Button>
						</div>
					</div>
					<p v-else class="text-sm text-gray-500">You can view the customer link; only a Super Admin, a Department Admin or the Project Lead can change it.</p>
				</div>

				<div
					v-if="canManage && hasProjectCustomer"
					class="portal-card-strong p-5"
				>
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="user-plus" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Client Customer logins
						</h2>
						<Button v-if="cpCanInvite" type="button" variant="outline" size="sm" @click="openInviteCustomerUser">
							Invite new user
						</Button>
					</div>
					<p class="mb-3 text-sm text-gray-600">
						Everyone here can sign in to the portal and see this customer’s projects. One login can belong to
						<strong>several</strong> customers and sees all of their projects. <strong>Remove from portal</strong>
						takes away this customer only; their other customers stay.
					</p>

					<p class="mb-2 text-xs font-medium uppercase text-gray-500">People with access</p>
					<ul class="mb-4 divide-y rounded-xl border border-gray-200 bg-white text-sm">
						<li
							v-for="u in customerPortalUsers"
							:key="u.name"
							class="flex flex-wrap items-center justify-between gap-3 py-3 px-4"
						>
							<div class="min-w-0 flex-1">
								<p class="font-medium text-gray-900">{{ u.full_name || u.name }}</p>
								<p class="truncate text-xs text-gray-500">{{ u.email || u.name }}</p>
								<p class="mt-0.5 text-xs" :class="u.last_login ? 'text-gray-500' : 'text-amber-700'">
									{{ u.last_login ? `Last signed in ${formatLastLogin(u.last_login)}` : "Invited — hasn’t signed in yet" }}
								</p>
							</div>
							<div class="flex shrink-0 flex-wrap gap-2">
								<button
									v-if="cpCanReset && u.can_reset"
									type="button"
									class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
									:disabled="cpSaving"
									@click="openResetUser(u)"
								>
									Reset password
								</button>
								<button
									type="button"
									class="rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
									:disabled="cpSaving"
									@click="removeCustomerPortalUserImmediate(u.name)"
								>
									Remove from portal
								</button>
							</div>
						</li>
						<li
							v-if="!customerPortalUsers.length"
							class="py-8 px-4 text-center text-sm text-gray-500"
						>
							No Client Customer logins yet. Search below to add someone, or use Invite new user.
						</li>
					</ul>

					<template v-if="cpCanLinkExisting">
					<p class="mb-2 text-xs font-medium uppercase text-gray-500">Add existing user</p>
					<label class="mb-2 block text-xs text-gray-600">Search by email, username, or full name — they are added as soon as you choose one.</label>
					<div ref="cpPickerRef" class="mb-3 space-y-2" @focusin="onCpFocus">
						<TextInput
							v-model="cpSearchQ"
							class="w-full rounded-xl"
							placeholder="Click to see existing portal users, or type to filter…"
							:disabled="cpSaving"
						/>
						<div
							v-if="cpHits.length"
							class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
						>
							<button
								v-for="u in cpHits"
								:key="u.name"
								type="button"
								class="flex w-full items-center justify-between gap-2 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
								:disabled="cpSaving || customerPortalUserIds.has(u.name)"
								@click="addCustomerPortalUserImmediate(u.name)"
							>
								<span class="min-w-0">
									<span class="font-medium text-gray-900">{{ u.full_name || u.name }}</span>
									<span class="mt-0.5 block truncate text-xs text-gray-500">{{ u.email || u.name }}</span>
								</span>
								<span v-if="customerPortalUserIds.has(u.name)" class="shrink-0 text-xs text-gray-400">Added</span>
								<span v-else class="shrink-0 text-xs font-medium text-blue-600">Add</span>
							</button>
						</div>
					</div>
					</template>
					<p v-else class="mb-3 text-xs text-gray-500">Only a Super Admin or a Department Admin can add Client Customer logins.</p>
					<p v-if="cpSaving" class="mb-2 text-sm text-gray-600">Updating…</p>
					<p v-if="cpMessage" class="text-sm text-green-700">{{ cpMessage }}</p>
					<p v-if="cpWarn" class="text-sm font-medium text-amber-700">{{ cpWarn }}</p>
					<p v-if="cpError" class="text-sm text-red-600">{{ cpError }}</p>
				</div>

				<div v-if="!isCustomerPortalUser" class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="grid" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Portal Team (Gantt grouping)
						</h2>
					</div>
					<p class="mb-3 text-sm text-gray-600">
						Groups this project under a team on the Gantt Chart page. A Super Admin can set any team; a Department Admin or Department Coordinator can only use a team of their own department; the project's Project Lead can set it on their own project.
					</p>
					<div v-if="canManage" class="space-y-3">
						<p class="text-sm" style="color:var(--portal-text);">
							Current: <strong>{{ project.portal_team || "None" }}</strong>
						</p>
						<label class="text-xs font-medium text-gray-600">Search teams</label>
						<div class="space-y-2" @focusin="loadDeptOptions">
							<TextInput
								v-model="deptSearchQ"
								class="w-full rounded-xl"
								placeholder="Click to see teams, or type to filter…"
							/>
							<div
								v-if="deptHits.length"
								class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
							>
								<button
									v-for="d in deptHits"
									:key="d.name"
									type="button"
									class="flex w-full flex-col gap-0.5 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white"
									:disabled="deptBusy"
									@click="setProjectTeam(d.name)"
								>
									<span class="font-medium text-gray-900">{{ d.department_name }}</span>
									<span class="text-xs text-gray-500">{{ d.office }}</span>
								</button>
							</div>
						</div>
						<div class="flex flex-wrap gap-2">
							<button
								type="button"
								class="rounded-xl border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-50"
								@click="showNewTeam = true"
							>
								Create team (no duplicate name)
							</button>
							<button
								v-if="project.portal_team"
								type="button"
								class="rounded-xl border border-red-200 px-3 py-2 text-sm text-red-700 hover:bg-red-50"
								:disabled="deptBusy"
								@click="setProjectTeam('')"
							>
								Clear team
							</button>
						</div>
						<p v-if="deptMsg" class="text-sm text-green-700">{{ deptMsg }}</p>
						<p v-if="deptErr" class="text-sm text-red-600">{{ deptErr }}</p>
					</div>
					<p v-else class="text-sm text-gray-500">You can view the team; only a Super Admin, a Department Admin, a Department Coordinator or the Project Lead can change it.</p>
				</div>

				<div v-if="!isCustomerPortalUser" class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="users" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Team
							<span class="text-xs font-normal text-[color:var(--portal-muted)]">{{ teamRows.length }}</span>
						</h2>
						<button v-if="canPickFromOrgChart" type="button" class="portal-btn portal-btn-ghost" @click="openOrgPicker">
							<FeatherIcon name="git-branch" class="h-3.5 w-3.5" />
							Add from org chart
						</button>
					</div>
					<p v-if="!canAddMembers" class="mb-3 text-xs text-[color:var(--portal-muted)]">
						View only. A Team Manager, Department Coordinator, Department Admin or Super Admin adds people to a project.
					</p>
					<p v-else-if="!canRemoveMembers" class="mb-3 text-xs text-[color:var(--portal-muted)]">
						You can add people to this project. Only a Super Admin or a Department Admin can remove them.
					</p>
					<div v-if="canAddMembers" ref="teamPickerRef" class="mb-4 space-y-2">
						<label class="text-xs font-medium text-gray-600">Add user (search by email, username, or full name)</label>
						<div @focusin="onSearchFocus">
							<TextInput
								v-model="searchQ"
								class="w-full rounded-xl"
								placeholder="Click to see existing users, type to filter, press Enter to add"
								:disabled="teamSaving"
								@keyup.enter="onTeamSearchEnter"
							/>
						</div>
						<div
							v-if="searchHits.length"
							class="max-h-48 overflow-auto rounded-xl border border-gray-200 bg-gray-50 text-sm"
						>
							<button
								v-for="h in searchHits"
								:key="h.name"
								type="button"
								class="flex w-full items-center justify-between gap-2 border-b border-gray-100 px-3 py-2 text-left last:border-0 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
								:disabled="teamSaving || teamList.includes(h.name)"
								@click="addTeamUser(h.name)"
							>
								<span class="min-w-0 flex-1 truncate">
									<span class="font-medium text-gray-900">{{ h.full_name || h.name }}</span>
									<span class="ml-2 text-xs text-gray-500">{{ h.email || h.name }}</span>
								</span>
								<span v-if="teamList.includes(h.name)" class="text-xs text-gray-400">on team</span>
								<span v-else class="text-xs font-medium text-blue-600">Add</span>
							</button>
						</div>

						<div v-if="userGroups.length" class="mt-3 flex flex-wrap items-center gap-2">
							<label class="text-xs font-medium text-gray-600">Or add a whole User Group</label>
							<div class="flex items-center gap-2">
								<select v-model="selectedGroup" class="portal-input text-sm">
									<option value="">— Select —</option>
									<option v-for="g in userGroups" :key="g.name" :value="g.name">
										{{ g.name }} ({{ g.member_count }})
									</option>
								</select>
								<Button
									variant="subtle"
									class="rounded-xl"
									:disabled="!selectedGroup || teamSaving"
									:loading="addingGroup"
									@click="addTeamUserGroup"
								>
									Add group
								</Button>
							</div>
						</div>
					</div>
					<ul class="divide-y rounded-xl border border-gray-100 text-sm">
						<li v-for="row in teamRows" :key="row.user" class="flex items-center justify-between gap-2 py-2 px-3">
							<span class="min-w-0">
								<span class="font-medium text-[color:var(--portal-text)]">{{ row.full_name || row.user }}</span>
								<span
									v-if="project.portal_project_manager && project.portal_project_manager === row.user"
									class="portal-pill portal-pill-muted ml-1.5"
								>Project Lead</span>
								<span class="block truncate text-xs text-gray-500">{{ row.user }}</span>
							</span>
							<button
								v-if="canRemoveMembers"
								type="button"
								class="shrink-0 text-xs text-red-600 hover:underline disabled:opacity-50"
								:disabled="teamSaving"
								@click="removeTeamUser(row)"
							>
								Remove
							</button>
						</li>
						<li v-if="!teamRows.length" class="py-4 px-3 text-gray-500">No users on this project yet.</li>
					</ul>
					<div class="mt-3 space-y-1">
						<p v-if="teamSaving" class="text-sm text-gray-600">Updating…</p>
						<p v-if="teamMessage" class="text-sm text-green-700">{{ teamMessage }}</p>
						<p v-if="teamError" class="text-sm text-red-600">{{ teamError }}</p>
					</div>
				</div>

				<div class="portal-card-strong p-5">
					<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="paperclip" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Files
						</h2>
						<button
							type="button"
							class="portal-btn portal-btn-ghost"
							@click="router.push({ path: '/files', query: { project: project.name } })"
						>
							Open in Files hub
							<FeatherIcon name="arrow-up-right" class="h-3.5 w-3.5" />
						</button>
					</div>
					<FileUploadPanel
						v-if="!isCustomerPortalUser"
						:project="project?.name || props.name"
						:folders="folders"
						:project-root-path="projectRootPath"
						:allow-share="canShareFolder"
						class="mb-4"
						@uploaded="loadFiles"
						@open-share="onOpenShareFromPanel"
					/>
					<p v-else class="mb-4 text-sm text-[color:var(--portal-muted)]">
						You can upload into 06-CLIENT SUBMITTAL / Outgoing from
						<button type="button" class="font-medium underline" @click="router.push({ path: '/files', query: { project: project.name } })">the Files hub</button>.
					</p>
					<p v-if="fileDeleteError" class="mb-2 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-800">
						{{ fileDeleteError }}
					</p>
					<div v-if="filesLoading" class="text-sm text-[color:var(--portal-muted)]">Loading files…</div>
					<ul v-else class="divide-y divide-[color:var(--portal-border)] text-sm">
						<li v-for="f in files" :key="f.name" class="flex flex-wrap items-center justify-between gap-2 py-2.5">
							<span class="min-w-0 break-words text-[color:var(--portal-text)]">
								<FeatherIcon name="file" class="mr-1.5 inline h-3.5 w-3.5 text-[color:var(--portal-muted)]" />
								{{ f.file_name }}
								<span v-if="f.is_private" class="portal-pill portal-pill-muted ml-1.5">private</span>
								<span v-if="f.client_direction" class="portal-pill ml-1.5" :class="f.client_direction === 'incoming' ? 'portal-pill-accent' : 'portal-pill-success'">{{ f.client_direction === "incoming" ? "Sent to client" : "From client" }}</span>
								<span v-else-if="f.uploaded_by_client" class="ml-1.5 inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-800" :title="`Uploaded by the client: ${f.uploaded_by_name || f.owner || ''}`">Client upload</span>
							</span>
							<div class="flex shrink-0 flex-wrap items-center gap-2">
								<a
									v-if="f.file_url"
									:href="`/api/method/portal_app.api.files.download_project_file?file_name=${encodeURIComponent(f.name)}`"
									target="_blank"
									rel="noopener"
									class="text-[color:var(--portal-accent)] hover:underline"
								>
									Open
								</a>
								<button
									v-if="canDeleteFileOnDetail(f)"
									type="button"
									class="text-xs font-medium text-red-700 hover:underline disabled:opacity-50"
									:disabled="!!deleteBusyName"
									@click="deleteProjectFile(f)"
								>
									{{ deleteBusyName === f.name ? "Deleting…" : "Delete" }}
								</button>
							</div>
						</li>
						<li v-if="!files.length" class="py-4 text-center text-[color:var(--portal-muted)]">No files yet.</li>
					</ul>
				</div>

				<div v-if="!isCustomerPortalUser" class="portal-card-strong p-5">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="flex items-center gap-2 font-semibold text-[color:var(--portal-text)]">
							<FeatherIcon name="check-square" class="h-4 w-4 text-[color:var(--portal-accent)]" />
							Tasks
						</h2>
						<button
							type="button"
							class="portal-btn portal-btn-ghost"
							@click="router.push({ path: '/tasks', query: { project: project.name } })"
						>
							Open task workspace
							<FeatherIcon name="arrow-up-right" class="h-3.5 w-3.5" />
						</button>
					</div>
					<div class="space-y-2">
						<div
							v-for="t in tasks"
							:key="t.name"
							class="rounded-xl border border-[color:var(--portal-border)] bg-white px-3 py-2.5 shadow-sm transition hover:border-[color:var(--portal-border-strong)] hover:shadow-md"
						>
							<div class="flex flex-wrap items-center justify-between gap-2">
								<p class="font-medium text-[color:var(--portal-text)]">{{ t.subject }}</p>
								<span class="portal-pill portal-pill-muted">{{ t.status }}</span>
							</div>
							<p class="mt-1 text-xs font-mono text-[color:var(--portal-subtle)]">{{ t.name }}</p>
						</div>
						<div v-if="!tasks.length" class="rounded-xl border border-dashed border-gray-300 bg-white py-6 text-center text-gray-500">
							No tasks linked.
						</div>
					</div>
				</div>
			</template>
		</div>

		<Teleport to="body">
			<div
				v-if="showLinks"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showLinks = false"></div>
				<div class="relative z-10 flex max-h-[88vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl border bg-white shadow-2xl">
					<div class="border-b border-gray-100 px-6 py-4">
						<h3 class="text-lg font-semibold text-gray-900">Manage project links</h3>
						<p class="mt-0.5 text-sm text-gray-600">
							Only the people you allow (and the department's coordinators and admins) can open a link.
							A link with no path, no URL and nobody allowed is removed.
						</p>
					</div>
					<div class="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-4">
						<div v-for="type in LINK_TYPES" :key="type" class="space-y-2">
							<p class="text-sm font-semibold text-gray-900">{{ LINK_LABELS[type] || type }}</p>
							<template v-if="linksForm[type]">
								<input
									v-model="linksForm[type].copy_path"
									type="text"
									class="w-full rounded-xl border border-gray-200 px-3 py-2 font-mono text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
									:placeholder="type === 'T Server' ? 'Mapped-drive path, e.g. T:\\My Drive\\Project' : 'Path (optional)'"
								/>
								<input
									v-model="linksForm[type].open_url"
									type="url"
									class="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
									:placeholder="type === 'T Server' ? 'Google Drive link (https://…)' : 'Link (https://…)'"
								/>
								<div class="flex flex-wrap gap-1.5">
									<span
										v-for="u in linksForm[type].allowed_users"
										:key="type + ':' + u.user"
										class="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700"
									>
										{{ u.full_name || u.user }}
										<button type="button" class="text-gray-400 hover:text-red-600" :title="'Remove ' + (u.full_name || u.user)" @click="removeLinkUser(type, u.user)">
											<FeatherIcon name="x" class="h-3 w-3" />
										</button>
									</span>
									<span v-if="!linksForm[type].allowed_users.length" class="text-xs text-gray-500">Nobody else allowed yet.</span>
								</div>
								<div class="relative">
									<input
										v-model="linkUserQ[type]"
										type="text"
										class="w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
										placeholder="Allow someone: type a name"
										@input="searchLinkUsers(type)"
									/>
									<div v-if="(linkUserHits[type] || []).length" class="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-lg">
										<button
											v-for="u in linkUserHits[type]"
											:key="type + '::' + u.name"
											type="button"
											class="block w-full px-3 py-2 text-left text-sm hover:bg-gray-50"
											@click="addLinkUser(type, u)"
										>
											{{ u.full_name || u.name }} <span class="text-xs text-gray-500">{{ u.name }}</span>
										</button>
									</div>
								</div>
							</template>
						</div>
						<p v-if="linksErr" class="text-sm text-red-600">{{ linksErr }}</p>
					</div>
					<div class="flex items-center justify-end gap-2 border-t border-gray-100 px-6 py-4">
						<button type="button" class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" @click="showLinks = false">
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="linksBusy" @click="saveLinks">
							Save links
						</Button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="showOrgPicker"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showOrgPicker = false"></div>
				<div class="relative z-10 flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border bg-white shadow-2xl">
					<div class="border-b border-gray-100 px-6 py-4">
						<h3 class="text-lg font-semibold text-gray-900">Add from the org chart</h3>
						<p class="mt-0.5 text-sm text-gray-600">Tick the people to put on <strong>{{ project?.project_name || props.name }}</strong>.</p>
					</div>
					<div class="px-6 pt-4">
						<TextInput v-model="orgSearch" class="w-full rounded-xl" placeholder="Search people" />
					</div>
					<div class="min-h-0 flex-1 overflow-y-auto px-6 py-4">
						<p v-if="orgLoading" class="py-6 text-center text-sm text-gray-500">Loading…</p>
						<template v-else>
							<div v-for="g in orgGroups" :key="g.key" class="mb-4">
								<p class="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-gray-500">
									{{ g.label }}<span v-if="g.office" class="font-normal normal-case"> · {{ g.office }}</span>
								</p>
								<label
									v-for="m in g.people"
									:key="g.key + '::' + m.user"
									class="mb-1.5 flex cursor-pointer items-center gap-3 rounded-xl border border-gray-100 bg-gray-50 px-3 py-2"
									:class="teamList.includes(m.user) ? 'opacity-55' : ''"
								>
									<input
										type="checkbox"
										:disabled="teamList.includes(m.user)"
										:checked="orgPicked.has(m.user)"
										@change="toggleOrgPick(m.user)"
									/>
									<span class="min-w-0 flex-1">
										<span class="block truncate text-sm font-medium text-gray-900">{{ m.full_name || m.user }}</span>
										<span class="block truncate text-xs text-gray-500">{{ m.user }}<span v-if="m.role_label"> · {{ m.role_label }}</span></span>
									</span>
									<span v-if="teamList.includes(m.user)" class="shrink-0 text-xs text-gray-400">On team</span>
								</label>
							</div>
							<p v-if="!orgGroups.length && !orgErr" class="py-6 text-center text-sm text-gray-500">No people to show.</p>
						</template>
						<p v-if="orgErr" class="text-sm text-red-600">{{ orgErr }}</p>
					</div>
					<div class="flex items-center justify-end gap-2 border-t border-gray-100 px-6 py-4">
						<button type="button" class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" @click="showOrgPicker = false">
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :disabled="!orgPicked.size" :loading="teamSaving" @click="submitOrgPicker">
							{{ orgPicked.size ? `Add ${orgPicked.size} to the team` : "Add to the team" }}
						</Button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="showNewCustomer"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showNewCustomer = false"></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border bg-white p-6 shadow-2xl">
					<h3 class="text-lg font-semibold text-gray-900">New customer</h3>
					<p class="mt-1 text-sm text-gray-600">
						If the name already exists (same spelling), the existing customer is linked—nothing is duplicated.
					</p>
					<label class="mt-4 block text-xs font-medium text-gray-600">Customer name</label>
					<TextInput v-model="newCustomerName" class="mt-1 w-full rounded-xl" placeholder="Legal or trading name" />
					<div class="mt-4 flex justify-end gap-2">
						<button type="button" class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" @click="showNewCustomer = false">
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="newCustomerBusy" @click="submitNewCustomer">
							Create or link
						</Button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="showNewTeam"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showNewTeam = false"></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border bg-white p-6 shadow-2xl">
					<h3 class="text-lg font-semibold text-gray-900">New team</h3>
					<p class="mt-1 text-sm text-gray-600">
						If the name already exists (same spelling), the existing team is used — nothing is duplicated.
					</p>
					<label class="mt-4 block text-xs font-medium text-gray-600">Team name</label>
					<TextInput v-model="newTeamName" class="mt-1 w-full rounded-xl" placeholder="e.g. CD Team 07" />
					<label class="mt-3 block text-xs font-medium text-gray-600">Office (optional)</label>
					<TextInput v-model="newTeamOffice" class="mt-1 w-full rounded-xl" placeholder="e.g. RIYADH" />
					<div class="mt-4 flex justify-end gap-2">
						<button type="button" class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" @click="showNewTeam = false">
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="newTeamBusy" @click="submitNewTeam">
							Create and assign
						</Button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="showInviteCustomerUser"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div
					class="absolute inset-0 bg-black/40 backdrop-blur-sm"
					@click="showInviteCustomerUser = false"
				></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border bg-white p-6 shadow-2xl">
					<h3 class="text-lg font-semibold text-gray-900">Invite a Client Customer</h3>
					<p class="mt-1 text-sm text-gray-600">
						Gives this person a portal login linked to
						<strong>{{ customerDisplayName || project?.customer }}</strong>. They will see every project of that
						customer, and only its client-submittal files. If the email already has a login, that user is linked
						instead.
					</p>
					<div class="mt-4 space-y-3">
						<div>
							<label class="mb-1 block text-xs font-medium text-gray-600">Email (username)</label>
							<TextInput
								v-model="inviteEmail"
								type="email"
								class="w-full rounded-xl"
								placeholder="name@company.com"
								autocomplete="off"
							/>
						</div>
						<div>
							<label class="mb-1 block text-xs font-medium text-gray-600">Full name</label>
							<TextInput v-model="inviteFullName" class="w-full rounded-xl" placeholder="Their name" autocomplete="off" />
						</div>
						<label class="flex items-start gap-2 text-sm text-gray-800">
							<input v-model="inviteSendWelcome" type="checkbox" class="mt-0.5 rounded border-gray-300" />
							<span>
								Send a welcome email
								<span class="block text-xs text-gray-500">
									It contains a link to set their own password, then opens the portal.
								</span>
							</span>
						</label>
						<div>
							<label class="mb-1 block text-xs font-medium text-gray-600">
								{{ inviteSendWelcome ? "Password (optional — leave blank to let them choose)" : "Password (min 8)" }}
							</label>
							<Password v-model="invitePassword" class="w-full rounded-xl" autocomplete="new-password" />
						</div>
					</div>
					<p v-if="cpError" class="mt-3 text-sm text-red-600">{{ cpError }}</p>
					<div class="mt-4 flex justify-end gap-2">
						<button
							type="button"
							class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
							@click="showInviteCustomerUser = false"
						>
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="inviteBusy" @click="submitInviteCustomerUser">
							{{ inviteSendWelcome ? "Create & send invite" : "Create & link" }}
						</Button>
					</div>
				</div>
			</div>
		</Teleport>

		<Teleport to="body">
			<div
				v-if="showResetUser && resetTarget"
				class="fixed inset-0 z-[60] flex items-center justify-center px-4"
				role="dialog"
				aria-modal="true"
			>
				<div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="!resetBusy && (showResetUser = false)"></div>
				<div class="relative z-10 w-full max-w-md rounded-2xl border bg-white p-6 shadow-2xl">
					<h3 class="text-lg font-semibold text-gray-900">Reset password</h3>
					<p class="mt-1 text-sm text-gray-600">
						For <strong>{{ resetTarget.full_name || resetTarget.name }}</strong>
						<span class="text-gray-500">({{ resetTarget.email || resetTarget.name }})</span>
					</p>
					<div class="mt-4 space-y-3">
						<label class="flex items-start gap-2 text-sm text-gray-800">
							<input v-model="resetMode" type="radio" value="email" class="mt-1" />
							<span>
								Email them a reset link
								<span class="block text-xs text-gray-500">They choose a new password themselves. Recommended.</span>
							</span>
						</label>
						<label class="flex items-start gap-2 text-sm text-gray-800">
							<input v-model="resetMode" type="radio" value="set" class="mt-1" />
							<span>
								Set a new password now
								<span class="block text-xs text-gray-500">
									Signs them out everywhere. You must pass the new password on to them.
								</span>
							</span>
						</label>
						<div v-if="resetMode === 'set'">
							<label class="mb-1 block text-xs font-medium text-gray-600">New password (min 8)</label>
							<Password v-model="resetPassword" class="w-full rounded-xl" autocomplete="new-password" />
						</div>
					</div>
					<p v-if="resetErr" class="mt-3 text-sm text-red-600">{{ resetErr }}</p>
					<div class="mt-4 flex justify-end gap-2">
						<button
							type="button"
							class="rounded-xl px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
							:disabled="resetBusy"
							@click="showResetUser = false"
						>
							Cancel
						</button>
						<Button variant="solid" class="rounded-xl bg-black text-white" :loading="resetBusy" @click="submitResetUser">
							{{ resetMode === "email" ? "Send reset link" : "Set password" }}
						</Button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
