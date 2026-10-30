<script setup>
import { ref, computed, onMounted, watch, inject } from "vue";
import { FeatherIcon } from "frappe-ui";
import { call } from "@/api";
import { ROLE_LABELS } from "@/config/roles";

const loading    = ref(true);
const loadError  = ref("");
const chart      = ref({ me: {}, super_admins: [], departments: [], teams: [], unassigned: [] });
const me         = computed(() => chart.value.me || {});

const portalCapabilities = inject("portalCapabilities", ref({}));
const refreshPortalCapabilities = inject("refreshPortalCapabilities", async () => {});

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

// ── Roles ─────────────────────────────────────────────────────────────────────
const ROLE_STYLE = {
  super_admin:            { label: ROLE_LABELS.super_admin,            color: "#7c3aed", bg: "rgba(124,58,237,0.12)", border: "rgba(124,58,237,0.32)" },
  department_admin:       { label: ROLE_LABELS.department_admin,       color: "#b45309", bg: "rgba(180,83,9,0.12)",   border: "rgba(180,83,9,0.32)" },
  department_coordinator: { label: ROLE_LABELS.department_coordinator, color: "#0f766e", bg: "rgba(15,118,110,0.12)", border: "rgba(15,118,110,0.32)" },
  team_lead:              { label: ROLE_LABELS.team_lead,              color: "#185FA5", bg: "rgba(24,95,165,0.12)",  border: "rgba(24,95,165,0.32)" },
  project_lead:           { label: ROLE_LABELS.project_lead,           color: "#9B2335", bg: "rgba(155,35,53,0.10)",  border: "rgba(155,35,53,0.28)" },
  team_member:            { label: ROLE_LABELS.team_member,            color: "#6b7280", bg: "rgba(128,128,128,0.10)", border: "rgba(128,128,128,0.25)" },
};
function roleStyle(role) {
  const r = ROLE_STYLE[role] || ROLE_STYLE.team_member;
  return { background: r.bg, color: r.color, border: `1px solid ${r.border}` };
}
function roleLabel(role) { return (ROLE_STYLE[role] || ROLE_STYLE.team_member).label; }

const OFFICE_COLOR  = { RIYADH: "#C9A84C", LISBON: "#185FA5", MANILA: "#276749", CAIRO: "#9b5de5", OTHER: "#6b7280" };
const OFFICE_BG     = { RIYADH: "rgba(201,168,76,0.12)", LISBON: "rgba(24,95,165,0.12)", MANILA: "rgba(39,103,73,0.12)", CAIRO: "rgba(155,93,229,0.12)", OTHER: "rgba(128,128,128,0.1)" };
const OFFICE_BORDER = { RIYADH: "rgba(201,168,76,0.30)", LISBON: "rgba(24,95,165,0.30)", MANILA: "rgba(39,103,73,0.30)", CAIRO: "rgba(155,93,229,0.30)", OTHER: "rgba(128,128,128,0.2)" };
function officeColor(o) { return OFFICE_COLOR[o] || "#6b7280"; }

function initials(name) {
  const parts = (name || "").trim().split(" ").filter(Boolean);
  return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : (name || "?").slice(0, 2).toUpperCase();
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadChart(keepSelection = true) {
  try {
    loadError.value = "";
    chart.value = await call({ method: "portal_app.api.teams.get_org_chart" });
    if (!keepSelection) selected.value = null;
    else if (selected.value && !selectedPerson.value) selected.value = null;
    if (!expanded.value.size) {
      // Open the teams that are "mine" (or the first one) so the page is not a wall of closed rows.
      const mine = (chart.value.teams || []).filter(t => t.is_mine).map(t => t.name);
      expanded.value = new Set(mine.length ? mine : (chart.value.teams || []).slice(0, 1).map(t => t.name));
    }
  } catch (e) {
    loadError.value = apiErr(e);
  } finally {
    loading.value = false;
  }
}
onMounted(() => loadChart(false));

// ── Filters / tree state ──────────────────────────────────────────────────────
const officeFilter = ref("ALL");
const search       = ref("");
const expanded     = ref(new Set());
const selected     = ref(null); // { team, user }

const officeList = computed(() => {
  const offices = [...new Set((chart.value.teams || []).map(t => t.office).filter(Boolean))];
  return ["ALL", ...offices];
});

const matches = (p) => {
  const q = search.value.trim().toLowerCase();
  return !q || (p.full_name || "").toLowerCase().includes(q) || (p.user || "").toLowerCase().includes(q);
};

const visibleTeams = computed(() =>
  (chart.value.teams || [])
    .filter(t => officeFilter.value === "ALL" || t.office === officeFilter.value)
    .map(t => ({ ...t, shown: (t.members || []).filter(matches) }))
    .filter(t => !search.value.trim() || t.shown.length)
);
const visibleSuperAdmins = computed(() => (chart.value.super_admins || []).filter(matches));
const visibleUnassigned  = computed(() => (chart.value.unassigned || []).filter(matches));

function toggleTeam(name) {
  const s = new Set(expanded.value);
  s.has(name) ? s.delete(name) : s.add(name);
  expanded.value = s;
}
function isOpen(name) { return !!search.value.trim() || expanded.value.has(name); }
function expandAll()   { expanded.value = new Set((chart.value.teams || []).map(t => t.name)); }
function collapseAll() { expanded.value = new Set(); }

const totalPeople = computed(() => {
  const ids = new Set();
  for (const t of chart.value.teams || []) for (const m of t.members || []) ids.add(m.user);
  return ids.size;
});

const headcount = computed(() => {
  const by = {};
  for (const t of chart.value.teams || []) {
    const o = t.office || "OTHER";
    by[o] = (by[o] || 0) + (t.member_count || 0);
  }
  return Object.entries(by).map(([office, count]) => ({ office, count }));
});

// ── Selected person ───────────────────────────────────────────────────────────
const SUPER = "__super__";
const NONE = "__none__";
const DEPT = "__dept__:"; // + department name: a person on the department itself

// Departments above the teams (get_org_chart.departments). Each keeps its teams, filtered
// like the flat list; an older server without the block shows one group of every team.
const visibleDepartments = computed(() => {
  const shownTeams = new Map(visibleTeams.value.map(t => [t.name, t]));
  const groups = chart.value.departments?.length
    ? chart.value.departments
    : [{ name: "", label: "Teams", pending: false, admins: [], coordinators: [], members: [], teams: chart.value.teams || [], can_edit: false }];
  return groups
    .map(d => {
      const people = [...(d.admins || []), ...(d.coordinators || []), ...(d.members || [])].filter(matches);
      const teams = (d.teams || []).map(t => shownTeams.get(t.name)).filter(Boolean);
      return { ...d, people, shownTeams: teams };
    })
    .filter(d => {
      if (officeFilter.value !== "ALL") return d.shownTeams.length > 0;
      if (search.value.trim()) return d.shownTeams.length > 0 || d.people.length > 0;
      return true;
    });
});
function deptOf(name) { return (chart.value.departments || []).find(d => d.name === name) || null; }

const selectedTeam = computed(() => (chart.value.teams || []).find(t => t.name === selected.value?.team) || null);
const selectedPerson = computed(() => {
  const sel = selected.value;
  if (!sel) return null;
  if (sel.team === SUPER) {
    const p = (chart.value.super_admins || []).find(x => x.user === sel.user);
    return p ? { ...p, role: "super_admin", team_role: null, is_super_admin: true, can_change_role: false, can_remove: false } : null;
  }
  if (sel.team === NONE) {
    const p = (chart.value.unassigned || []).find(x => x.user === sel.user);
    return p ? { ...p, role: p.is_super_admin ? "super_admin" : "team_member", team_role: null, can_change_role: false, can_remove: false } : null;
  }
  if (sel.team.startsWith(DEPT)) {
    const d = deptOf(sel.team.slice(DEPT.length));
    const p = d && [...(d.admins || []), ...(d.coordinators || []), ...(d.members || [])].find(x => x.user === sel.user);
    return p ? { ...p, role: p.is_super_admin ? "super_admin" : p.unit_role, team_role: null, can_change_role: false, can_remove: false } : null;
  }
  return (selectedTeam.value?.members || []).find(m => m.user === sel.user) || null;
});
const selectedOffice = computed(() => selectedTeam.value?.office || "");

function selectPerson(team, user) {
  if (selected.value?.team === team && selected.value?.user === user) { selected.value = null; return; }
  selected.value = { team, user };
}

// role editor draft follows the selection
const roleDraft = ref("team_member");
const addToTeam = ref("");
const panelBusy = ref(false);
const panelMsg  = ref("");
const panelErr  = ref("");
watch(selectedPerson, (p) => {
  panelMsg.value = "";
  panelErr.value = "";
  addToTeam.value = "";
  if (p && p.team_role) roleDraft.value = p.team_role;
}, { immediate: true });

const roleOptions = computed(() => {
  const opts = [
    { value: "team_member", label: ROLE_LABELS.team_member },
    { value: "team_lead", label: ROLE_LABELS.team_lead },
  ];
  if (me.value.can_grant_admin) opts.push({ value: "department_admin", label: "Department Admin" });
  return opts;
});

async function saveRole() {
  const p = selectedPerson.value;
  if (!p || !selectedTeam.value || roleDraft.value === p.team_role) return;
  panelBusy.value = true; panelMsg.value = ""; panelErr.value = "";
  try {
    await call({
      method: "portal_app.api.teams.set_member_role",
      type: "POST",
      args: { team: selectedTeam.value.name, user: p.user, role: roleDraft.value },
    });
    panelMsg.value = `${p.full_name} is now ${roleLabel(roleDraft.value)} of ${selectedTeam.value.department_name}.`;
    await loadChart();
  } catch (e) {
    panelErr.value = apiErr(e);
  } finally {
    panelBusy.value = false;
  }
}

async function removeFromTeam() {
  const p = selectedPerson.value, t = selectedTeam.value;
  if (!p || !t) return;
  if (!window.confirm(`Remove ${p.full_name} from ${t.department_name}?`)) return;
  panelBusy.value = true; panelMsg.value = ""; panelErr.value = "";
  try {
    await call({ method: "portal_app.api.teams.remove_team_member", type: "POST", args: { team: t.name, user: p.user } });
    selected.value = null;
    await loadChart();
  } catch (e) {
    panelErr.value = apiErr(e);
  } finally {
    panelBusy.value = false;
  }
}

async function removeAsLead() {
  const p = selectedPerson.value, t = selectedTeam.value;
  if (!p || !t) return;
  if (!window.confirm(`Remove ${p.full_name} as ${ROLE_LABELS.team_lead} of ${t.department_name}? They stay on the team as a ${ROLE_LABELS.team_member}.`)) return;
  panelBusy.value = true; panelMsg.value = ""; panelErr.value = "";
  try {
    await call({ method: "portal_app.api.teams.remove_team_lead", type: "POST", args: { team: t.name } });
    await loadChart();
    panelMsg.value = `${p.full_name} is now a ${ROLE_LABELS.team_member}.`;
  } catch (e) {
    panelErr.value = apiErr(e);
  } finally {
    panelBusy.value = false;
  }
}

async function toggleSuperAdmin() {
  const p = selectedPerson.value;
  if (!p) return;
  const on = !p.is_super_admin;
  const msg = on
    ? `Make ${p.full_name} a Super Admin? A Super Admin can see and change everything in the portal.`
    : `Remove Super Admin access from ${p.full_name}?`;
  if (!window.confirm(msg)) return;
  panelBusy.value = true; panelMsg.value = ""; panelErr.value = "";
  try {
    await call({ method: "portal_app.api.portal_admin.set_super_admin", type: "POST", args: { user: p.user, enabled: on ? 1 : 0 } });
    await loadChart();
    panelMsg.value = on ? `${p.full_name} is now a Super Admin.` : `${p.full_name} is no longer a Super Admin.`;
  } catch (e) {
    panelErr.value = apiErr(e);
  } finally {
    panelBusy.value = false;
  }
}

// people who are in no team yet: add them to one
const editableTeams = computed(() => (chart.value.teams || []).filter(t => t.can_edit));
async function addUnassignedToTeam() {
  const p = selectedPerson.value;
  if (!p || !addToTeam.value) return;
  panelBusy.value = true; panelMsg.value = ""; panelErr.value = "";
  try {
    await call({ method: "portal_app.api.teams.add_team_member", type: "POST", args: { team: addToTeam.value, user: p.user } });
    const t = (chart.value.teams || []).find(x => x.name === addToTeam.value);
    selected.value = null;
    await loadChart();
    if (t) expanded.value = new Set([...expanded.value, t.name]);
  } catch (e) {
    panelErr.value = apiErr(e);
  } finally {
    panelBusy.value = false;
  }
}

// ── Assign to project ─────────────────────────────────────────────────────────
const showAssign     = ref(false);
const assignProjects = ref([]);
const assignSearch   = ref("");
const assignPicked   = ref(new Set());
const assignBusy     = ref(false);
const assignMsg      = ref("");
const assignErr      = ref("");
const assignLoading  = ref(false);

async function openAssign() {
  const p = selectedPerson.value;
  if (!p) return;
  assignSearch.value = ""; assignPicked.value = new Set(); assignMsg.value = ""; assignErr.value = "";
  showAssign.value = true;
  assignLoading.value = true;
  try {
    assignProjects.value = await call({ method: "portal_app.api.projects.get_assignable_projects", args: { for_user: p.user } }) || [];
  } catch (e) {
    assignProjects.value = [];
    assignErr.value = apiErr(e);
  } finally {
    assignLoading.value = false;
  }
}
function closeAssign() { showAssign.value = false; }
const filteredAssign = computed(() => {
  const q = assignSearch.value.trim().toLowerCase();
  return (assignProjects.value || []).filter(pr =>
    !q || (pr.project_name || "").toLowerCase().includes(q) || (pr.name || "").toLowerCase().includes(q)
      || (pr.portal_project_code || "").toLowerCase().includes(q)
  );
});
function toggleAssignPick(name) {
  const s = new Set(assignPicked.value);
  s.has(name) ? s.delete(name) : s.add(name);
  assignPicked.value = s;
}
async function submitAssign() {
  const p = selectedPerson.value;
  if (!p || !assignPicked.value.size) return;
  assignBusy.value = true; assignMsg.value = ""; assignErr.value = "";
  const done = [], failed = [];
  for (const project of assignPicked.value) {
    try {
      await call({
        method: "portal_app.api.projects.add_project_members",
        type: "POST",
        args: { project, users: JSON.stringify([p.user]) },
      });
      done.push(project);
    } catch (e) {
      failed.push(`${project}: ${apiErr(e)}`);
    }
  }
  assignBusy.value = false;
  if (done.length) assignMsg.value = `${p.full_name} was added to ${done.length} project${done.length === 1 ? "" : "s"}.`;
  if (failed.length) assignErr.value = failed.join(" · ");
  try {
    assignProjects.value = await call({ method: "portal_app.api.projects.get_assignable_projects", args: { for_user: p.user } }) || [];
  } catch { /* keep the list */ }
  assignPicked.value = new Set();
  await loadChart();
}

// ── Reset password ────────────────────────────────────────────────────────────
const showReset  = ref(false);
const resetMode  = ref("email");
const resetPw    = ref("");
const resetBusy  = ref(false);
const resetMsg   = ref("");
const resetErr   = ref("");
function openReset() {
  resetMode.value = "email"; resetPw.value = ""; resetMsg.value = ""; resetErr.value = "";
  showReset.value = true;
}
function closeReset() { showReset.value = false; }
async function submitReset() {
  const p = selectedPerson.value;
  if (!p) return;
  if (resetMode.value === "set" && resetPw.value.length < 8) { resetErr.value = "Use at least 8 characters."; return; }
  resetBusy.value = true; resetMsg.value = ""; resetErr.value = "";
  try {
    await call({
      method: "portal_app.api.portal_admin.reset_user_password",
      type: "POST",
      args: { user: p.user, mode: resetMode.value, new_password: resetMode.value === "set" ? resetPw.value : undefined },
    });
    resetMsg.value = resetMode.value === "email"
      ? `A reset link is on its way to ${p.user}.`
      : "The password was changed and they were signed out everywhere.";
    resetPw.value = "";
  } catch (e) {
    resetErr.value = apiErr(e);
  } finally {
    resetBusy.value = false;
  }
}

// ── Manage Team (edit name/office + add members) ──────────────────────────────
const managingTeamId = ref(null);
const managingTeam = computed(() => (chart.value.teams || []).find(t => t.name === managingTeamId.value) || null);
function openManageTeam(teamId) { managingTeamId.value = teamId; }
function closeManageTeam() { managingTeamId.value = null; }

const showEditTeam    = ref(false);
const savingTeam      = ref(false);
const teamEditError   = ref("");
const teamEditForm    = ref({ id: "", department_name: "", office: "" });
const editableOffices = computed(() => officeList.value.filter(o => o !== "ALL"));

function openEditTeam() {
  if (!managingTeam.value) return;
  teamEditError.value = "";
  teamEditForm.value = { id: managingTeam.value.name, department_name: managingTeam.value.department_name, office: managingTeam.value.office };
  showEditTeam.value = true;
}
function closeEditTeam() { showEditTeam.value = false; }
async function submitEditTeam() {
  if (!teamEditForm.value.department_name?.trim()) { teamEditError.value = "Team name required."; return; }
  savingTeam.value = true; teamEditError.value = "";
  try {
    await call({
      method: "portal_app.api.teams.update_team",
      type: "POST",
      args: { team: teamEditForm.value.id, department_name: teamEditForm.value.department_name, office: teamEditForm.value.office },
    });
    showEditTeam.value = false;
    await loadChart();
  } catch (e) {
    teamEditError.value = apiErr(e);
  } finally {
    savingTeam.value = false;
  }
}

const showAddMember    = ref(false);
const assignableUsers  = ref([]);
const userGroups       = ref([]);
const addMemberSearch  = ref("");
const addMemberError   = ref("");
const addingMemberName = ref(null);

async function openAddMember() {
  if (!managingTeam.value) return;
  addMemberError.value = ""; addMemberSearch.value = "";
  try {
    const [users, groups] = await Promise.all([
      call({ method: "portal_app.api.teams.get_assignable_users", args: { team: managingTeam.value.name } }),
      call({ method: "portal_app.api.teams.get_user_groups" }),
    ]);
    assignableUsers.value = users || [];
    userGroups.value = groups || [];
  } catch (e) {
    assignableUsers.value = []; userGroups.value = [];
    addMemberError.value = apiErr(e);
  }
  showAddMember.value = true;
}
function closeAddMember() { showAddMember.value = false; }
const filteredAssignable = computed(() => {
  const q = addMemberSearch.value.trim().toLowerCase();
  return (assignableUsers.value || []).filter(u => !q || (u.full_name || u.name || "").toLowerCase().includes(q));
});
const filteredUserGroups = computed(() => {
  const q = addMemberSearch.value.trim().toLowerCase();
  return (userGroups.value || []).filter(g => !q || g.name.toLowerCase().includes(q));
});
async function addMember(user) {
  if (!managingTeam.value) return;
  addingMemberName.value = user.name; addMemberError.value = "";
  try {
    await call({ method: "portal_app.api.teams.add_team_member", type: "POST", args: { team: managingTeam.value.name, user: user.name } });
    closeAddMember();
    await loadChart();
  } catch (e) {
    addMemberError.value = apiErr(e);
  } finally {
    addingMemberName.value = null;
  }
}
// ── Change role (R4) ──────────────────────────────────────────────────────────
// The server decides who may change whom (portal_admin.change_user_role): this dialog
// only offers what get_user_designations says is assignable.
const ROLE_ORDER = ["super_admin", "department_admin", "department_coordinator", "team_lead", "team_member"];
const UNIT_ROLES = ["department_admin", "department_coordinator", "team_lead"];
const showRoleDialog = ref(false);
const roleData       = ref(null);
const roleLoading    = ref(false);
const roleBusy       = ref(false);
const roleErr        = ref("");
const roleMsg        = ref("");
const roleKey        = ref("");
const roleUnit       = ref("");
const keepOthers     = ref(false);
const assignableRoleKeys = computed(() => ROLE_ORDER.filter(k => roleData.value?.assignable && k in roleData.value.assignable));
const roleNeedsUnit  = computed(() => UNIT_ROLES.includes(roleKey.value));
const unitOptions    = computed(() =>
  (roleData.value?.assignable?.[roleKey.value] || []).map(u => ({
    value: u,
    label: roleData.value?.unit_labels?.[u] || u,
    pending: (roleData.value?.pending_units || []).includes(u),
  }))
);
watch(roleKey, () => { roleUnit.value = unitOptions.value.length === 1 ? unitOptions.value[0].value : ""; });

async function openRoleDialog() {
  const p = selectedPerson.value;
  if (!p) return;
  roleErr.value = ""; roleMsg.value = ""; roleData.value = null; roleKey.value = ""; roleUnit.value = ""; keepOthers.value = false;
  showRoleDialog.value = true;
  roleLoading.value = true;
  try {
    roleData.value = await call({ method: "portal_app.api.portal_admin.get_user_designations", args: { user: p.user } });
  } catch (e) {
    roleErr.value = apiErr(e);
  } finally {
    roleLoading.value = false;
  }
}
function closeRoleDialog() { showRoleDialog.value = false; }
function canRemoveDesignation(d) {
  const a = roleData.value?.assignable || {};
  if (!["super_admin", ...UNIT_ROLES].includes(d.role) || !(d.role in a)) return false;
  return d.role === "super_admin" || (a[d.role] || []).includes(d.unit);
}
async function afterRoleChange(res, message) {
  if (roleData.value && res?.designations) roleData.value = { ...roleData.value, designations: res.designations };
  roleMsg.value = message;
  await loadChart();
  if (roleData.value?.user === me.value.user) await refreshPortalCapabilities();
}
async function submitRoleChange() {
  const user = roleData.value?.user;
  if (!user || !roleKey.value || (roleNeedsUnit.value && !roleUnit.value)) return;
  roleBusy.value = true; roleErr.value = ""; roleMsg.value = "";
  try {
    const res = await call({
      method: "portal_app.api.portal_admin.change_user_role",
      type: "POST",
      args: { user, role: roleKey.value, unit: roleNeedsUnit.value ? roleUnit.value : undefined, keep_other_roles: keepOthers.value ? 1 : 0 },
    });
    await afterRoleChange(res, `${roleData.value.full_name || user} is now ${ROLE_LABELS[roleKey.value] || roleKey.value}.`);
  } catch (e) {
    roleErr.value = apiErr(e);
  } finally {
    roleBusy.value = false;
  }
}
async function removeDesignation(d) {
  const user = roleData.value?.user;
  if (!user) return;
  if (!window.confirm(`Remove ${d.label}${d.unit_label ? " of " + d.unit_label : ""} from ${roleData.value.full_name || user}?`)) return;
  roleBusy.value = true; roleErr.value = ""; roleMsg.value = "";
  try {
    const res = await call({
      method: "portal_app.api.portal_admin.remove_user_designation",
      type: "POST",
      args: { user, role: d.role, unit: d.unit || undefined },
    });
    await afterRoleChange(res, `${d.label} removed.`);
  } catch (e) {
    roleErr.value = apiErr(e);
  } finally {
    roleBusy.value = false;
  }
}

// ── Pending departments (Super Admin): activate ───────────────────────────────
async function activateDepartment(dept) {
  if (!window.confirm(`Activate ${dept.label}? Its Department Admins, Coordinators and Team Managers get their roles now.`)) return;
  try {
    await call({ method: "portal_app.api.teams.set_department_pending", type: "POST", args: { department: dept.name, pending: 0 } });
    await loadChart();
  } catch (e) {
    loadError.value = apiErr(e);
  }
}

async function addMemberGroup(group) {
  if (!managingTeam.value) return;
  addingMemberName.value = `group:${group.name}`; addMemberError.value = "";
  try {
    await call({ method: "portal_app.api.teams.add_team_member", type: "POST", args: { team: managingTeam.value.name, user_group: group.name } });
    closeAddMember();
    await loadChart();
  } catch (e) {
    addMemberError.value = apiErr(e);
  } finally {
    addingMemberName.value = null;
  }
}
</script>

<template>
  <div class="h-full overflow-y-auto p-6" style="background:var(--portal-bg);">

    <!-- Header -->
    <div class="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold mb-1" style="color:var(--portal-text);">Organization Chart</h1>
        <p class="text-sm" style="color:var(--portal-muted);">
          {{ totalPeople }} people · {{ (chart.departments || []).filter(d => d.name).length }} departments · {{ (chart.teams || []).length }} teams · You are
          <strong style="color:var(--portal-text);">{{ me.role_label || "—" }}</strong>
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-1.5">
        <span v-for="(r, key) in ROLE_STYLE" :key="key" class="text-[10px] font-semibold px-2.5 py-1 rounded-full" :style="roleStyle(key)">{{ r.label }}</span>
      </div>
    </div>

    <p v-if="me.can_edit_any_team || me.can_grant_admin" class="mb-4 text-xs rounded-xl px-4 py-3"
       style="background:var(--portal-surface);border:1px solid var(--portal-border);color:var(--portal-muted);">
      Click a person to change their role, remove them from the team, assign them to projects or reset their password.
      <template v-if="!me.can_grant_admin"> You can manage the teams of the department you are a Department Admin of.</template>
    </p>
    <p v-else class="mb-4 text-xs rounded-xl px-4 py-3"
       style="background:var(--portal-surface);border:1px solid var(--portal-border);color:var(--portal-muted);">
      As a {{ me.role === "department_coordinator" ? "Department Coordinator" : "Team Manager" }} you can click anyone to assign them to your projects.
    </p>

    <div v-if="loading" class="flex items-center gap-2 text-sm" style="color:var(--portal-muted);">
      <span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
      Loading…
    </div>
    <p v-else-if="loadError" class="text-sm text-red-600">{{ loadError }}</p>

    <template v-else>
      <!-- Filters -->
      <div class="flex flex-wrap items-center gap-2 mb-5">
        <button
          v-for="off in officeList" :key="off"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
          :style="officeFilter === off
            ? 'background:var(--portal-text);color:var(--portal-bg);'
            : 'background:var(--portal-surface);color:var(--portal-muted);border:1px solid var(--portal-border);'"
          @click="officeFilter = off"
        >{{ off === 'ALL' ? 'All Offices' : off }}</button>
        <input v-model="search" type="search" placeholder="Find a person…" class="portal-input ml-auto w-56" />
        <button class="text-xs font-semibold" style="color:var(--portal-accent);" @click="expandAll">Expand all</button>
        <button class="text-xs font-semibold" style="color:var(--portal-muted);" @click="collapseAll">Collapse all</button>
      </div>

      <div class="grid gap-5 lg:grid-cols-3">
        <!-- Hierarchy (2/3) -->
        <div class="lg:col-span-2 space-y-3">

          <!-- Super Admins -->
          <div v-if="visibleSuperAdmins.length" class="rounded-2xl p-4" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center gap-2 mb-2">
              <FeatherIcon name="shield" class="h-4 w-4" style="color:#7c3aed;" />
              <span class="text-sm font-semibold" style="color:var(--portal-text);">Super Admins</span>
              <span class="text-xs" style="color:var(--portal-muted);">{{ visibleSuperAdmins.length }}</span>
            </div>
            <div class="space-y-1.5">
              <div
                v-for="p in visibleSuperAdmins" :key="p.user"
                class="flex items-center gap-3 rounded-xl p-2.5 cursor-pointer transition"
                :style="selected && selected.team === SUPER && selected.user === p.user
                  ? 'background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.4);'
                  : 'background:rgba(124,58,237,0.06);border:1px solid rgba(124,58,237,0.18);'"
                @click="selectPerson(SUPER, p.user)"
              >
                <div class="h-9 w-9 rounded-xl flex items-center justify-center text-white text-xs font-bold flex-shrink-0" style="background:#7c3aed;">{{ initials(p.full_name) }}</div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-semibold truncate" style="color:var(--portal-text);">{{ p.full_name }}</p>
                  <p class="text-[10px] truncate" style="color:var(--portal-muted);">{{ p.user }}</p>
                </div>
                <span class="text-[9px] font-semibold px-2 py-0.5 rounded-full" :style="roleStyle('super_admin')">Super Admin</span>
              </div>
            </div>
          </div>

          <!-- Departments, each with its people and its teams -->
          <div
            v-for="dept in visibleDepartments" :key="'dept::' + dept.name"
            class="rounded-2xl p-3 space-y-3"
            :class="dept.pending ? 'opacity-60' : ''"
            style="background:var(--portal-surface-alt);border:1px solid var(--portal-border);"
          >
            <div class="flex flex-wrap items-center gap-2 px-1">
              <FeatherIcon name="layers" class="h-4 w-4" style="color:var(--portal-accent);" />
              <span class="text-sm font-bold" style="color:var(--portal-text);">{{ dept.label }}</span>
              <span v-if="dept.pending" class="text-[9px] font-semibold px-2 py-0.5 rounded-full" style="background:rgba(128,128,128,0.15);color:var(--portal-muted);">Not active yet</span>
              <span class="text-xs" style="color:var(--portal-muted);">{{ (dept.teams || []).length }} team{{ (dept.teams || []).length === 1 ? "" : "s" }}</span>
              <button
                v-if="dept.pending && me.is_super_admin"
                class="ml-auto portal-btn portal-btn-primary text-xs"
                @click.stop="activateDepartment(dept)"
              >Activate</button>
            </div>
            <div v-if="dept.people.length" class="space-y-1.5">
              <div
                v-for="p in dept.people" :key="dept.name + '::' + p.unit_role + '::' + p.user"
                class="flex items-center gap-3 rounded-xl p-2.5 cursor-pointer transition"
                :style="selected && selected.team === DEPT + dept.name && selected.user === p.user
                  ? 'background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.4);'
                  : 'background:var(--portal-surface);border:1px solid var(--portal-border);'"
                @click="selectPerson(DEPT + dept.name, p.user)"
              >
                <div class="h-9 w-9 rounded-xl flex items-center justify-center text-white text-xs font-bold flex-shrink-0" :style="{ background: (ROLE_STYLE[p.unit_role] || ROLE_STYLE.team_member).color }">{{ initials(p.full_name) }}</div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-semibold truncate" style="color:var(--portal-text);">{{ p.full_name }}</p>
                  <p class="text-[10px] truncate" style="color:var(--portal-muted);">{{ p.user }} · {{ p.project_count }} project{{ p.project_count === 1 ? "" : "s" }}</p>
                </div>
                <span v-if="p.is_super_admin" class="text-[9px] font-semibold px-2 py-0.5 rounded-full" :style="roleStyle('super_admin')">{{ roleLabel('super_admin') }}</span>
                <span class="text-[9px] font-semibold px-2 py-0.5 rounded-full" :style="roleStyle(p.unit_role)">{{ roleLabel(p.unit_role) }}</span>
              </div>
            </div>
          <!-- Teams -->
          <div
            v-for="team in dept.shownTeams" :key="team.name"
            class="rounded-2xl p-4"
            style="background:var(--portal-surface);border:1px solid var(--portal-border);"
          >
            <div class="flex items-center gap-2 cursor-pointer" @click="toggleTeam(team.name)">
              <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                :style="{ background: OFFICE_BG[team.office] || OFFICE_BG.OTHER, color: officeColor(team.office), border: `1px solid ${OFFICE_BORDER[team.office] || OFFICE_BORDER.OTHER}` }">
                {{ isOpen(team.name) ? '−' : '+' }}
              </span>
              <span class="text-sm font-semibold" style="color:var(--portal-text);">{{ team.department_name }}</span>
              <span class="text-[9px] font-semibold px-2 py-0.5 rounded-full"
                :style="{ background: OFFICE_BG[team.office] || OFFICE_BG.OTHER, color: officeColor(team.office), border: `1px solid ${OFFICE_BORDER[team.office] || OFFICE_BORDER.OTHER}` }">
                {{ team.office || "—" }}
              </span>
              <span class="text-xs" style="color:var(--portal-muted);">{{ team.member_count }} {{ team.member_count === 1 ? "person" : "people" }}</span>
              <span v-if="team.is_mine" class="text-[9px] font-semibold px-2 py-0.5 rounded-full" style="background:rgba(245,158,11,0.15);color:#b45309;">Your team</span>
              <button
                v-if="team.can_edit"
                class="ml-auto w-7 h-7 rounded-full flex items-center justify-center transition hover:bg-black/5"
                title="Manage team"
                @click.stop="openManageTeam(team.name)"
              >
                <FeatherIcon name="edit-2" class="h-3.5 w-3.5" :style="{ color: officeColor(team.office) }" />
              </button>
            </div>

            <div v-if="isOpen(team.name)" class="mt-3 space-y-1.5 pl-3 ml-3 border-l" style="border-color:var(--portal-border);">
              <div
                v-for="m in team.shown" :key="team.name + '::' + m.user"
                class="flex items-center gap-3 rounded-xl p-2.5 cursor-pointer transition"
                :style="selected && selected.team === team.name && selected.user === m.user
                  ? 'background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.4);'
                  : `background:${OFFICE_BG[team.office] || OFFICE_BG.OTHER};border:1px solid ${OFFICE_BORDER[team.office] || OFFICE_BORDER.OTHER};`"
                @click="selectPerson(team.name, m.user)"
              >
                <div class="h-9 w-9 rounded-xl flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                  :style="{ background: officeColor(team.office) }">{{ initials(m.full_name) }}</div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-semibold truncate" style="color:var(--portal-text);">{{ m.full_name }}</p>
                  <p class="text-[10px] truncate" style="color:var(--portal-muted);">{{ m.user }} · {{ m.project_count }} project{{ m.project_count === 1 ? "" : "s" }}</p>
                </div>
                <span v-if="m.is_super_admin" class="text-[9px] font-semibold px-2 py-0.5 rounded-full" :style="roleStyle('super_admin')">Super Admin</span>
                <span v-if="!m.is_super_admin || m.team_role !== 'team_member'" class="text-[9px] font-semibold px-2 py-0.5 rounded-full" :style="roleStyle(m.team_role)">{{ roleLabel(m.team_role) }}</span>
              </div>
              <p v-if="!team.shown.length" class="text-xs py-2" style="color:var(--portal-muted);">No people in this team yet.</p>
            </div>
          </div>
          </div>
          <p v-if="!visibleDepartments.length" class="text-sm text-center py-8" style="color:var(--portal-muted);">No teams or people match.</p>

          <!-- Not in a team (admins only) -->
          <div v-if="visibleUnassigned.length" class="rounded-2xl p-4" style="background:var(--portal-surface);border:1px dashed var(--portal-border);">
            <div class="flex items-center gap-2 mb-2">
              <FeatherIcon name="user-plus" class="h-4 w-4" style="color:var(--portal-muted);" />
              <span class="text-sm font-semibold" style="color:var(--portal-text);">Not in a team yet</span>
              <span class="text-xs" style="color:var(--portal-muted);">{{ visibleUnassigned.length }} · click someone to add them to a team</span>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="u in visibleUnassigned" :key="u.user"
                class="text-xs rounded-full px-3 py-1.5 transition"
                :style="selected && selected.team === NONE && selected.user === u.user
                  ? 'background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.45);color:var(--portal-text);'
                  : 'background:var(--portal-surface-alt);border:1px solid var(--portal-border);color:var(--portal-text);'"
                @click="selectPerson(NONE, u.user)"
              >{{ u.full_name }}</button>
            </div>
          </div>
        </div>

        <!-- Right panel (1/3) -->
        <div class="space-y-4">
          <div class="rounded-2xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div v-if="selectedPerson">
              <div class="text-center">
                <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-bold text-xl mx-auto mb-3"
                  :style="{ background: selectedPerson.is_super_admin ? '#7c3aed' : officeColor(selectedOffice) }">
                  {{ initials(selectedPerson.full_name) }}
                </div>
                <p class="font-semibold text-sm mb-0.5" style="color:var(--portal-text);">{{ selectedPerson.full_name }}</p>
                <p class="text-xs mb-2 break-all" style="color:var(--portal-muted);">{{ selectedPerson.user }}</p>
                <div class="flex flex-wrap items-center justify-center gap-1.5">
                  <span class="text-[10px] font-semibold px-2.5 py-1 rounded-full" :style="roleStyle(selectedPerson.role)">{{ roleLabel(selectedPerson.role) }}</span>
                  <span v-if="selectedPerson.is_super_admin && selectedPerson.team_role" class="text-[10px] font-semibold px-2.5 py-1 rounded-full" :style="roleStyle(selectedPerson.team_role)">{{ roleLabel(selectedPerson.team_role) }} here</span>
                  <span v-if="selectedTeam" class="text-[10px] font-semibold px-2.5 py-1 rounded-full"
                    :style="{ background: OFFICE_BG[selectedOffice] || OFFICE_BG.OTHER, color: officeColor(selectedOffice), border: `1px solid ${OFFICE_BORDER[selectedOffice] || OFFICE_BORDER.OTHER}` }">
                    {{ selectedTeam.department_name }}
                  </span>
                </div>
                <p v-if="selectedPerson.project_count !== undefined" class="text-xs mt-3" style="color:var(--portal-muted);">
                  On <strong style="color:var(--portal-text);">{{ selectedPerson.project_count }}</strong> project{{ selectedPerson.project_count === 1 ? "" : "s" }}
                </p>
              </div>

              <!-- Change role -->
              <div v-if="selectedPerson.can_change_role && selectedTeam" class="mt-5 pt-4" style="border-top:1px solid var(--portal-border);">
                <p class="text-[10px] font-semibold uppercase tracking-wider mb-2" style="color:var(--portal-muted);">Role in {{ selectedTeam.department_name }}</p>
                <div class="flex items-center gap-2">
                  <select v-model="roleDraft" class="portal-input flex-1" :disabled="panelBusy">
                    <option v-for="o in roleOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
                  </select>
                  <button class="portal-btn portal-btn-primary" :disabled="panelBusy || roleDraft === selectedPerson.team_role" @click="saveRole">
                    {{ panelBusy ? "Saving…" : "Save" }}
                  </button>
                </div>
                <p class="text-[11px] mt-1.5" style="color:var(--portal-muted);">A team has one {{ ROLE_LABELS.team_lead }}; choosing a new one makes the previous one a {{ ROLE_LABELS.team_member }}.</p>
              </div>
              <p v-else-if="selectedTeam && selectedPerson.team_role === 'department_admin'" class="mt-4 text-[11px]" style="color:var(--portal-muted);">
                Only a Super Admin can change a Department Admin.
              </p>

              <!-- Add an unassigned person to a team -->
              <div v-if="selected && selected.team === NONE && editableTeams.length" class="mt-5 pt-4" style="border-top:1px solid var(--portal-border);">
                <p class="text-[10px] font-semibold uppercase tracking-wider mb-2" style="color:var(--portal-muted);">Add to a team</p>
                <div class="flex items-center gap-2">
                  <select v-model="addToTeam" class="portal-input flex-1" :disabled="panelBusy">
                    <option value="">— Select team —</option>
                    <option v-for="t in editableTeams" :key="t.name" :value="t.name">{{ t.department_name }}</option>
                  </select>
                  <button class="portal-btn portal-btn-primary" :disabled="panelBusy || !addToTeam" @click="addUnassignedToTeam">Add</button>
                </div>
              </div>

              <!-- Actions -->
              <div class="mt-5 pt-4 space-y-2" style="border-top:1px solid var(--portal-border);">
                <button v-if="me.can_change_roles" class="portal-btn portal-btn-ghost w-full flex items-center justify-center gap-2" @click="openRoleDialog">
                  <FeatherIcon name="award" class="h-4 w-4" /> Change role…
                </button>
                <button v-if="me.can_assign_to_projects" class="portal-btn portal-btn-ghost w-full flex items-center justify-center gap-2" @click="openAssign">
                  <FeatherIcon name="briefcase" class="h-4 w-4" /> Assign to project…
                </button>
                <button v-if="selectedPerson.can_reset_password" class="portal-btn portal-btn-ghost w-full flex items-center justify-center gap-2" @click="openReset">
                  <FeatherIcon name="key" class="h-4 w-4" /> Reset password…
                </button>
                <button v-if="selectedTeam && selectedPerson.team_role === 'team_lead' && selectedPerson.can_remove" class="portal-btn portal-btn-ghost w-full flex items-center justify-center gap-2" :disabled="panelBusy" @click="removeAsLead">
                  <FeatherIcon name="user-minus" class="h-4 w-4" /> Remove as {{ ROLE_LABELS.team_lead }}
                </button>
                <button v-if="selectedTeam && selectedPerson.can_remove" class="w-full flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition hover:bg-red-50" style="color:#dc2626;border:1px solid rgba(220,38,38,0.35);" :disabled="panelBusy" @click="removeFromTeam">
                  <FeatherIcon name="user-x" class="h-4 w-4" /> Remove from team
                </button>
                <button v-if="me.is_super_admin && selectedPerson.user !== me.user" class="portal-btn portal-btn-ghost w-full flex items-center justify-center gap-2" :disabled="panelBusy" @click="toggleSuperAdmin">
                  <FeatherIcon name="shield" class="h-4 w-4" /> {{ selectedPerson.is_super_admin ? "Remove Super Admin access" : "Make Super Admin" }}
                </button>
              </div>
              <p v-if="panelMsg" class="text-xs text-green-700 mt-3">{{ panelMsg }}</p>
              <p v-if="panelErr" class="text-xs text-red-600 mt-3">{{ panelErr }}</p>
            </div>
            <div v-else class="text-center py-6">
              <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3" style="background:var(--portal-surface-alt);">
                <FeatherIcon name="user" class="h-5 w-5" style="color:var(--portal-muted);"/>
              </div>
              <p class="text-xs font-medium mb-1" style="color:var(--portal-text);">Select a person</p>
              <p class="text-[11px]" style="color:var(--portal-muted);">Click anyone in the chart to see their role and what you can do.</p>
            </div>
          </div>

          <!-- Headcount summary -->
          <div class="rounded-2xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <p class="text-[10px] font-semibold uppercase tracking-wider mb-4" style="color:var(--portal-muted);">Headcount Summary</p>
            <div class="space-y-3">
              <div v-for="row in headcount" :key="row.office" class="flex items-center gap-2.5">
                <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ background: officeColor(row.office) }"></div>
                <span class="flex-1 text-xs" style="color:var(--portal-text);">{{ row.office }}</span>
                <span class="text-xs font-semibold" style="color:var(--portal-text);">{{ row.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>

  <!-- Change role -->
  <Teleport to="body">
    <div v-if="showRoleDialog" class="fixed inset-0 z-[60] flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeRoleDialog">
      <div class="w-full max-w-md rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <div>
            <h2 class="text-lg font-bold" style="color:var(--portal-text);">Change role</h2>
            <p class="text-xs mt-0.5" style="color:var(--portal-muted);">{{ roleData?.full_name || selectedPerson?.full_name }} · project teams and Project Leads are not changed.</p>
          </div>
          <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeRoleDialog">
            <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
          </button>
        </div>
        <div class="px-6 py-5 space-y-4">
          <p v-if="roleLoading" class="text-xs text-center py-4" style="color:var(--portal-muted);">Loading…</p>
          <template v-else-if="roleData">
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-wider mb-2" style="color:var(--portal-muted);">Current roles</p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="d in roleData.designations || []" :key="d.role + '::' + (d.unit || '')"
                  class="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full"
                  :class="d.pending ? 'opacity-60' : ''"
                  :style="roleStyle(d.role)"
                >
                  {{ d.label }}<template v-if="d.unit_label"> · {{ d.unit_label }}</template><template v-if="d.count"> ({{ d.count }})</template><template v-if="d.pending"> · not active yet</template>
                  <button v-if="canRemoveDesignation(d)" type="button" class="ml-0.5" :title="'Remove ' + d.label" :disabled="roleBusy" @click="removeDesignation(d)">
                    <FeatherIcon name="x" class="h-3 w-3" />
                  </button>
                </span>
                <span v-if="!(roleData.designations || []).length" class="text-xs" style="color:var(--portal-muted);">No portal role.</span>
              </div>
            </div>
            <template v-if="assignableRoleKeys.length">
              <div>
                <label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">New role</label>
                <select v-model="roleKey" class="portal-input w-full" :disabled="roleBusy">
                  <option value="">— Select —</option>
                  <option v-for="k in assignableRoleKeys" :key="k" :value="k">{{ ROLE_LABELS[k] || k }}</option>
                </select>
              </div>
              <div v-if="roleNeedsUnit">
                <label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">{{ roleKey === "team_lead" ? "Team" : "Department" }}</label>
                <select v-model="roleUnit" class="portal-input w-full" :disabled="roleBusy">
                  <option value="">— Select —</option>
                  <option v-for="u in unitOptions" :key="u.value" :value="u.value">{{ u.label }}{{ u.pending ? " (not active yet)" : "" }}</option>
                </select>
              </div>
              <label class="flex items-center gap-2 text-sm cursor-pointer" style="color:var(--portal-text);">
                <input v-model="keepOthers" type="checkbox" />
                Keep their other roles
              </label>
              <p class="text-[11px]" style="color:var(--portal-muted);">Project Lead is set on each project (Project page → Project Lead).</p>
            </template>
            <p v-else class="text-xs" style="color:var(--portal-muted);">You cannot change this person's role.</p>
          </template>
          <p v-if="roleMsg" class="text-xs text-green-700">{{ roleMsg }}</p>
          <p v-if="roleErr" class="text-xs text-red-600">{{ roleErr }}</p>
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-[color:var(--portal-border)]">
          <button class="portal-btn portal-btn-ghost" @click="closeRoleDialog">Close</button>
          <button
            v-if="assignableRoleKeys.length"
            class="portal-btn portal-btn-primary"
            :disabled="roleBusy || !roleKey || (roleNeedsUnit && !roleUnit)"
            @click="submitRoleChange"
          >{{ roleBusy ? "Saving…" : keepOthers ? "Add role" : "Change role" }}</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Assign to project -->
  <Teleport to="body">
    <div v-if="showAssign" class="fixed inset-0 z-[60] flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeAssign">
      <div class="w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <div>
            <h2 class="text-lg font-bold" style="color:var(--portal-text);">Assign to project</h2>
            <p class="text-xs mt-0.5" style="color:var(--portal-muted);">{{ selectedPerson?.full_name }} joins the team of each project you tick.</p>
          </div>
          <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeAssign">
            <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
          </button>
        </div>
        <div class="px-6 py-4">
          <input v-model="assignSearch" type="search" placeholder="Search projects" class="portal-input w-full mb-3" />
          <div class="max-h-[45vh] overflow-y-auto space-y-1.5">
            <p v-if="assignLoading" class="text-xs text-center py-6" style="color:var(--portal-muted);">Loading…</p>
            <label
              v-for="pr in filteredAssign" :key="pr.name"
              class="flex items-center gap-3 rounded-xl p-2.5 cursor-pointer"
              :style="pr.already_on_team ? 'opacity:.55;' : ''"
              style="background:var(--portal-surface-alt);border:1px solid var(--portal-border);"
            >
              <input type="checkbox" :disabled="!!pr.already_on_team" :checked="assignPicked.has(pr.name)" @change="toggleAssignPick(pr.name)" />
              <div class="min-w-0 flex-1">
                <div class="text-sm font-medium truncate" style="color:var(--portal-text);">{{ pr.project_name || pr.name }}</div>
                <div class="text-[11px] truncate" style="color:var(--portal-muted);">{{ pr.portal_project_code || pr.name }}<span v-if="pr.status"> · {{ pr.status }}</span></div>
              </div>
              <span v-if="pr.already_on_team" class="text-[10px] font-semibold" style="color:var(--portal-muted);">On team</span>
            </label>
            <p v-if="!assignLoading && !filteredAssign.length" class="text-xs text-center py-6" style="color:var(--portal-muted);">
              No projects you can assign people to{{ assignSearch ? " match." : "." }}
            </p>
          </div>
          <p v-if="assignMsg" class="text-xs text-green-700 mt-3">{{ assignMsg }}</p>
          <p v-if="assignErr" class="text-xs text-red-600 mt-3">{{ assignErr }}</p>
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-[color:var(--portal-border)]">
          <button class="portal-btn portal-btn-ghost" @click="closeAssign">Close</button>
          <button class="portal-btn portal-btn-primary" :disabled="assignBusy || !assignPicked.size" @click="submitAssign">
            {{ assignBusy ? "Adding…" : `Add to ${assignPicked.size || ""} project${assignPicked.size === 1 ? "" : "s"}` }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Reset password -->
  <Teleport to="body">
    <div v-if="showReset" class="fixed inset-0 z-[60] flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeReset">
      <div class="w-full max-w-md rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <h2 class="text-lg font-bold" style="color:var(--portal-text);">Reset password</h2>
          <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeReset">
            <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
          </button>
        </div>
        <div class="px-6 py-5 space-y-3">
          <p class="text-sm" style="color:var(--portal-text);">{{ selectedPerson?.full_name }} <span class="text-xs" style="color:var(--portal-muted);">({{ selectedPerson?.user }})</span></p>
          <label class="flex items-start gap-2 text-sm cursor-pointer" style="color:var(--portal-text);">
            <input v-model="resetMode" type="radio" value="email" class="mt-1" />
            <span><strong>Email them a reset link</strong><br /><span class="text-xs" style="color:var(--portal-muted);">They choose their own new password. The link expires after a few days.</span></span>
          </label>
          <label v-if="me.is_super_admin" class="flex items-start gap-2 text-sm cursor-pointer" style="color:var(--portal-text);">
            <input v-model="resetMode" type="radio" value="set" class="mt-1" />
            <span><strong>Set a password now</strong><br /><span class="text-xs" style="color:var(--portal-muted);">They are signed out everywhere and must use the new password.</span></span>
          </label>
          <input v-if="resetMode === 'set'" v-model="resetPw" type="password" autocomplete="new-password" placeholder="New password (8+ characters)" class="portal-input w-full" />
          <p v-if="resetMsg" class="text-xs text-green-700">{{ resetMsg }}</p>
          <p v-if="resetErr" class="text-xs text-red-600">{{ resetErr }}</p>
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-[color:var(--portal-border)]">
          <button class="portal-btn portal-btn-ghost" @click="closeReset">Close</button>
          <button class="portal-btn portal-btn-primary" :disabled="resetBusy" @click="submitReset">
            {{ resetBusy ? "Working…" : resetMode === "email" ? "Send reset link" : "Set password" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Manage Team Modal -->
  <Teleport to="body">
    <div v-if="managingTeam" class="fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,0.6);" @click.self="closeManageTeam">
      <div class="w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <div>
            <h2 class="text-lg font-bold" style="color:var(--portal-text);">{{ managingTeam.department_name }}</h2>
            <div class="flex items-center gap-2 mt-0.5">
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full"
                :style="{ background: OFFICE_BG[managingTeam.office] || OFFICE_BG.OTHER, color: officeColor(managingTeam.office) }">{{ managingTeam.office || "—" }}</span>
              <span class="text-xs" style="color:var(--portal-muted);">{{ managingTeam.member_count }} people</span>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-accent-soft)]" title="Edit team" @click="openEditTeam">
              <FeatherIcon name="edit-2" class="h-4 w-4" style="color:var(--portal-accent);"/>
            </button>
            <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeManageTeam">
              <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
            </button>
          </div>
        </div>
        <div class="px-6 py-4">
          <p class="text-xs mb-3" style="color:var(--portal-muted);">Rename the team or change its office, and add people to it. Change someone's role, or remove them, by clicking them in the chart.</p>
          <button class="portal-btn portal-btn-primary flex items-center gap-1.5" @click="openAddMember">
            <FeatherIcon name="user-plus" class="h-4 w-4" /> Add member
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Edit Team Modal -->
  <Teleport to="body">
    <div v-if="showEditTeam" class="fixed inset-0 z-[60] flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeEditTeam">
      <div class="w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <h2 class="text-lg font-bold" style="color:var(--portal-text);">Edit Team</h2>
          <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeEditTeam">
            <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
          </button>
        </div>
        <div class="px-6 py-5 space-y-4">
          <div>
            <label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Team Name</label>
            <input v-model="teamEditForm.department_name" type="text" class="portal-input w-full" />
          </div>
          <div>
            <label class="text-xs font-semibold mb-1.5 block" style="color:var(--portal-muted);">Office</label>
            <select v-model="teamEditForm.office" class="portal-input w-full">
              <option value="">— Select —</option>
              <option v-for="o in editableOffices" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <p v-if="teamEditError" class="text-xs text-red-600">{{ teamEditError }}</p>
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-[color:var(--portal-border)]">
          <button class="portal-btn portal-btn-ghost" @click="closeEditTeam">Cancel</button>
          <button class="portal-btn portal-btn-primary" :disabled="savingTeam" @click="submitEditTeam">{{ savingTeam ? "Saving…" : "Save Changes" }}</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Add Member Modal -->
  <Teleport to="body">
    <div v-if="showAddMember" class="fixed inset-0 z-[60] flex items-center justify-center p-4" style="background:rgba(0,0,0,0.55);" @click.self="closeAddMember">
      <div class="w-full max-w-md rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <h2 class="text-lg font-bold" style="color:var(--portal-text);">Add Member</h2>
          <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeAddMember">
            <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
          </button>
        </div>
        <div class="px-6 py-4">
          <input v-model="addMemberSearch" type="search" placeholder="Search users or user groups" class="portal-input w-full mb-3" />
          <p v-if="addMemberError" class="text-xs text-red-600 mb-2">{{ addMemberError }}</p>
          <div class="max-h-[50vh] overflow-y-auto">
            <template v-if="filteredUserGroups.length">
              <div class="text-[10px] font-semibold uppercase tracking-wider mb-1.5 px-0.5" style="color:var(--portal-muted);">User Groups</div>
              <div class="space-y-1.5 mb-3">
                <button
                  v-for="g in filteredUserGroups" :key="'group:' + g.name" type="button"
                  class="w-full flex items-center justify-between gap-3 rounded-xl p-2.5 text-left transition hover:bg-[color:var(--portal-surface-alt)]"
                  :disabled="addingMemberName === ('group:' + g.name)"
                  @click="addMemberGroup(g)"
                >
                  <div class="flex items-center gap-2 min-w-0">
                    <FeatherIcon name="users" class="h-4 w-4 flex-shrink-0" style="color:var(--portal-accent);"/>
                    <div class="min-w-0">
                      <div class="text-sm font-medium truncate" style="color:var(--portal-text);">{{ g.name }}</div>
                      <div class="text-xs truncate" style="color:var(--portal-muted);">{{ g.member_count }} member{{ g.member_count === 1 ? "" : "s" }}</div>
                    </div>
                  </div>
                  <FeatherIcon name="plus-circle" class="h-4 w-4 flex-shrink-0" style="color:var(--portal-accent);"/>
                </button>
              </div>
            </template>
            <div class="text-[10px] font-semibold uppercase tracking-wider mb-1.5 px-0.5" style="color:var(--portal-muted);">Users</div>
            <div class="space-y-1.5">
              <button
                v-for="u in filteredAssignable" :key="u.name" type="button"
                class="w-full flex items-center justify-between gap-3 rounded-xl p-2.5 text-left transition hover:bg-[color:var(--portal-surface-alt)]"
                :disabled="addingMemberName === u.name"
                @click="addMember(u)"
              >
                <div class="min-w-0">
                  <div class="text-sm font-medium truncate" style="color:var(--portal-text);">{{ u.full_name || u.name }}</div>
                  <div class="text-xs truncate" style="color:var(--portal-muted);">{{ u.name }}</div>
                </div>
                <FeatherIcon name="plus-circle" class="h-4 w-4 flex-shrink-0" style="color:var(--portal-accent);"/>
              </button>
              <div v-if="!filteredAssignable.length && !filteredUserGroups.length" class="text-center text-xs py-6" style="color:var(--portal-muted);">No matching users or groups.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
