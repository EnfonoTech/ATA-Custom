<script setup>
import { ref, computed, onMounted, inject } from "vue";
import { FeatherIcon } from "frappe-ui";
import OrgNode from "@/components/OrgNode.vue";
import { call } from "@/api";

const loading    = ref(true);
const orgTree    = ref([]);
const headcount  = ref([]);
const officeList = ref(["ALL"]);
const teamsRaw   = ref([]); // full get_teams() rows, kept for the manage-team modal

const portalCapabilities = inject("portalCapabilities", ref({}));
const canManageTeams = computed(() => !!portalCapabilities.value?.can_manage_teams);

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

async function loadTeams() {
  try {
    const teams = await call({ method: "portal_app.api.teams.get_teams" });
    if (!Array.isArray(teams)) return;
    teamsRaw.value = teams;

    // Build office list
    const offices = [...new Set(teams.map(d => d.office).filter(Boolean))];
    officeList.value = ["ALL", ...offices];

    // Build org tree — each team is a top-level node, members are children
    orgTree.value = teams.map(dept => ({
      id:       dept.name,
      name:     dept.members?.[0]?.employee_name || dept.department_name,
      role:     dept.department_name + " Lead",
      office:   dept.office || "OTHER",
      children: (dept.members || []).slice(1).map(m => ({
        id:     dept.name + "-" + m.name,
        name:   m.employee_name,
        role:   m.designation || dept.department_name,
        office: dept.office || "OTHER",
      })),
    }));

    // Build headcount per office
    const byOffice = {};
    for (const dept of teams) {
      const off = dept.office || "OTHER";
      byOffice[off] = (byOffice[off] || 0) + (dept.member_count || 0);
    }
    headcount.value = Object.entries(byOffice).map(([office, count]) => ({
      office,
      label: office,
      count,
    }));
  } catch (e) {
    console.error("org chart load error", e);
  } finally {
    loading.value = false;
  }
}

onMounted(loadTeams);

// ── Manage Team (edit name/office + add/remove members) ─────────────────────
// Mirrors TeamsPage.vue's team-management modal, triggered from a tree row here.
const managingTeamId = ref(null);
const managingTeam = computed(() => teamsRaw.value.find(t => t.name === managingTeamId.value) || null);

function openManageTeam(teamId) { managingTeamId.value = teamId; }
function closeManageTeam() { managingTeamId.value = null; }
async function refreshManagingTeam() {
  await loadTeams();
}

const showEditTeam    = ref(false);
const savingTeam      = ref(false);
const teamEditError   = ref("");
const teamEditForm    = ref({ id: "", department_name: "", office: "" });
const editableOffices = computed(() => officeList.value.filter(o => o !== "ALL"));

function openEditTeam() {
  if (!managingTeam.value) return;
  teamEditError.value = "";
  teamEditForm.value = {
    id:              managingTeam.value.name,
    department_name: managingTeam.value.department_name,
    office:          managingTeam.value.office,
  };
  showEditTeam.value = true;
}
function closeEditTeam() { showEditTeam.value = false; }

async function submitEditTeam() {
  if (!teamEditForm.value.department_name?.trim()) {
    teamEditError.value = "Team name required.";
    return;
  }
  savingTeam.value = true;
  teamEditError.value = "";
  try {
    await call({
      method: "portal_app.api.teams.update_team",
      type: "POST",
      args: {
        team:            teamEditForm.value.id,
        department_name: teamEditForm.value.department_name,
        office:          teamEditForm.value.office,
      },
    });
    showEditTeam.value = false;
    await refreshManagingTeam();
  } catch (e) {
    teamEditError.value = apiErr(e);
  } finally {
    savingTeam.value = false;
  }
}

// ── Add / Remove Member ──────────────────────────────────────────────────
const showAddMember    = ref(false);
const assignableUsers  = ref([]);
const userGroups       = ref([]);
const addMemberSearch  = ref("");
const addMemberError   = ref("");
const addingMemberName = ref(null);
const removingMemberId = ref(null);

async function openAddMember() {
  if (!managingTeam.value) return;
  addMemberError.value = "";
  addMemberSearch.value = "";
  try {
    const [users, groups] = await Promise.all([
      call({ method: "portal_app.api.teams.get_assignable_users", args: { team: managingTeam.value.name } }),
      call({ method: "portal_app.api.teams.get_user_groups" }),
    ]);
    assignableUsers.value = users || [];
    userGroups.value = groups || [];
  } catch (e) {
    assignableUsers.value = [];
    userGroups.value = [];
    addMemberError.value = apiErr(e);
  }
  showAddMember.value = true;
}
function closeAddMember() { showAddMember.value = false; }

const filteredAssignable = computed(() => {
  const q = addMemberSearch.value.trim().toLowerCase();
  return (assignableUsers.value || []).filter(
    u => !q || (u.full_name || u.name || "").toLowerCase().includes(q)
  );
});
const filteredUserGroups = computed(() => {
  const q = addMemberSearch.value.trim().toLowerCase();
  return (userGroups.value || []).filter(g => !q || g.name.toLowerCase().includes(q));
});

async function addMember(user) {
  if (!managingTeam.value) return;
  addingMemberName.value = user.name;
  addMemberError.value = "";
  try {
    await call({
      method: "portal_app.api.teams.add_team_member",
      type: "POST",
      args: { team: managingTeam.value.name, user: user.name },
    });
    closeAddMember();
    await refreshManagingTeam();
  } catch (e) {
    addMemberError.value = apiErr(e);
  } finally {
    addingMemberName.value = null;
  }
}

async function addMemberGroup(group) {
  if (!managingTeam.value) return;
  addingMemberName.value = `group:${group.name}`;
  addMemberError.value = "";
  try {
    await call({
      method: "portal_app.api.teams.add_team_member",
      type: "POST",
      args: { team: managingTeam.value.name, user_group: group.name },
    });
    closeAddMember();
    await refreshManagingTeam();
  } catch (e) {
    addMemberError.value = apiErr(e);
  } finally {
    addingMemberName.value = null;
  }
}

async function removeMember(m) {
  if (!managingTeam.value) return;
  removingMemberId.value = m.name;
  try {
    await call({
      method: "portal_app.api.teams.remove_team_member",
      type: "POST",
      args: { team: managingTeam.value.name, user: m.name },
    });
    await refreshManagingTeam();
  } catch (e) {
    console.error(e);
  } finally {
    removingMemberId.value = null;
  }
}

const officeFilter = ref("ALL");
const expanded     = ref(new Set());
const selected     = ref(null);

const totalMembers = computed(() => headcount.value.reduce((s, r) => s + r.count, 0));

function hasOffice(node, office) {
  if (node.office === office) return true;
  return (node.children || []).some(c => hasOffice(c, office));
}
const visibleTree = computed(() =>
  officeFilter.value === "ALL"
    ? orgTree.value
    : orgTree.value.filter(n => hasOffice(n, officeFilter.value))
);

function toggleExpand(id) {
  const s = new Set(expanded.value);
  s.has(id) ? s.delete(id) : s.add(id);
  expanded.value = s;
}
function selectMember(node) {
  selected.value = selected.value?.id === node.id ? null : node;
}
function setFilter(off) {
  officeFilter.value = off;
  expanded.value = new Set();
}
function initials(name) {
  const parts = (name || "").trim().split(" ");
  return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : (name || "?").slice(0, 2).toUpperCase();
}

const OFFICE_COLOR = { RIYADH: "#C9A84C", LISBON: "#185FA5", MANILA: "#276749", OTHER: "#6b7280" };
const OFFICE_BG    = { RIYADH: "rgba(201,168,76,0.12)", LISBON: "rgba(24,95,165,0.12)", MANILA: "rgba(39,103,73,0.12)", OTHER: "rgba(128,128,128,0.1)" };
const OFFICE_BORDER= { RIYADH: "rgba(201,168,76,0.30)", LISBON: "rgba(24,95,165,0.30)", MANILA: "rgba(39,103,73,0.30)", OTHER: "rgba(128,128,128,0.2)" };
</script>

<template>
  <div class="h-full overflow-y-auto p-6" style="background:var(--portal-bg);">

    <!-- Header -->
    <div class="mb-5">
      <h1 class="text-xl font-bold mb-1" style="color:var(--portal-text);">Organization Chart</h1>
      <p class="text-sm" style="color:var(--portal-muted);">
        {{ totalMembers }} employees · {{ orgTree.length }} teams · Click to expand/collapse
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center gap-2 text-sm" style="color:var(--portal-muted);">
      <span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
      Loading…
    </div>

    <template v-else>
      <!-- Office filter buttons -->
      <div class="flex items-center gap-2 mb-5 flex-wrap">
        <button
          v-for="off in officeList" :key="off"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
          :style="officeFilter === off
            ? 'background:var(--portal-text);color:var(--portal-bg);'
            : 'background:var(--portal-surface);color:var(--portal-muted);border:1px solid var(--portal-border);'"
          @click="setFilter(off)"
        >
          {{ off === 'ALL' ? 'All Offices' : off }}
        </button>
      </div>

      <!-- Main grid -->
      <div class="grid gap-5 lg:grid-cols-3">

        <!-- Hierarchy tree (2/3) -->
        <div class="lg:col-span-2 rounded-2xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
          <div class="flex items-center gap-2 mb-4">
            <FeatherIcon name="users" class="h-4 w-4" style="color:var(--portal-accent);"/>
            <span class="text-sm font-semibold" style="color:var(--portal-text);">Hierarchy</span>
            <span class="text-xs ml-auto" style="color:var(--portal-muted);">
              {{ officeFilter !== 'ALL' ? `Showing: ${officeFilter}` : 'All offices' }}
            </span>
          </div>

          <div v-if="visibleTree.length">
            <OrgNode
              v-for="node in visibleTree"
              :key="node.id"
              :node="node"
              :depth="0"
              :expanded="expanded"
              :selected-id="selected?.id || null"
              :can-manage-teams="canManageTeams"
              @toggle="toggleExpand"
              @select="selectMember"
              @manage="openManageTeam"
            />
          </div>
          <p v-else class="text-sm text-center py-8" style="color:var(--portal-muted);">
            No team members found for {{ officeFilter }}.
          </p>
        </div>

        <!-- Right panel (1/3) -->
        <div class="space-y-4">

          <!-- Selected member -->
          <div class="rounded-2xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div v-if="selected" class="text-center">
              <div
                class="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-bold text-xl mx-auto mb-3"
                :style="{ background: OFFICE_COLOR[selected.office] || '#6b7280' }"
              >
                {{ initials(selected.name) }}
              </div>
              <p class="font-semibold text-sm mb-0.5" style="color:var(--portal-text);">{{ selected.name }}</p>
              <p class="text-xs mb-3" style="color:var(--portal-muted);">{{ selected.role }}</p>
              <span
                class="text-[10px] font-semibold px-2.5 py-1 rounded-full"
                :style="{ background: OFFICE_BG[selected.office] || 'rgba(128,128,128,0.1)', color: OFFICE_COLOR[selected.office] || '#6b7280', border: `1px solid ${OFFICE_BORDER[selected.office] || 'rgba(128,128,128,0.2)'}` }"
              >
                {{ selected.office }}
              </span>
              <div v-if="selected.children?.length" class="mt-4 pt-3" style="border-top:1px solid var(--portal-border);">
                <p class="text-xs" style="color:var(--portal-muted);">
                  Direct reports: <strong style="color:var(--portal-text);">{{ selected.children.length }}</strong>
                </p>
              </div>
            </div>
            <div v-else class="text-center py-6">
              <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3" style="background:var(--portal-surface-alt);">
                <FeatherIcon name="user" class="h-5 w-5" style="color:var(--portal-muted);"/>
              </div>
              <p class="text-xs font-medium mb-1" style="color:var(--portal-text);">Select a Member</p>
              <p class="text-[11px]" style="color:var(--portal-muted);">Click on any team member to view their details.</p>
            </div>
          </div>

          <!-- Headcount summary -->
          <div class="rounded-2xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <p class="text-[10px] font-semibold uppercase tracking-wider mb-4" style="color:var(--portal-muted);">Headcount Summary</p>
            <div class="space-y-3">
              <div v-for="row in headcount" :key="row.office" class="flex items-center gap-2.5">
                <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ background: OFFICE_COLOR[row.office] || '#6b7280' }"></div>
                <span class="flex-1 text-xs" style="color:var(--portal-text);">{{ row.label }}</span>
                <span class="text-xs font-semibold" style="color:var(--portal-text);">{{ row.count }}</span>
              </div>
            </div>
            <div class="mt-4 pt-3" style="border-top:1px solid var(--portal-border);color:var(--portal-muted);">
              <p class="text-[10px]">Total: {{ totalMembers }} active employees</p>
            </div>
          </div>

        </div>
      </div>
    </template>
  </div>

  <!-- Manage Team Modal (members list + edit + add/remove) -->
  <Teleport to="body">
    <div
      v-if="managingTeam"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background:rgba(0,0,0,0.6);"
      @click.self="closeManageTeam"
    >
      <div class="w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <div>
            <h2 class="text-lg font-bold" style="color:var(--portal-text);">{{ managingTeam.department_name }}</h2>
            <div class="flex items-center gap-2 mt-0.5">
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full"
                :style="{ background: OFFICE_BG[managingTeam.office] || 'rgba(128,128,128,0.1)', color: OFFICE_COLOR[managingTeam.office] || '#6b7280' }">
                {{ managingTeam.office || "—" }}
              </span>
              <span class="text-xs" style="color:var(--portal-muted);">{{ managingTeam.member_count }} members</span>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button
              class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-accent-soft)]"
              title="Edit team"
              @click="openEditTeam"
            >
              <FeatherIcon name="edit-2" class="h-4 w-4" style="color:var(--portal-accent);"/>
            </button>
            <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeManageTeam">
              <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
            </button>
          </div>
        </div>

        <div class="px-6 py-4 max-h-[60vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-3">
            <div class="text-xs font-semibold uppercase tracking-wider" style="color:var(--portal-muted);">Team Members</div>
            <button
              class="flex items-center gap-1 text-xs font-semibold rounded-lg px-2 py-1 transition hover:bg-[color:var(--portal-accent-soft)]"
              style="color:var(--portal-accent);"
              @click="openAddMember"
            >
              <FeatherIcon name="user-plus" class="h-3.5 w-3.5" />
              Add member
            </button>
          </div>
          <div class="space-y-2">
            <div
              v-for="m in (managingTeam.members || [])"
              :key="m.name"
              class="flex items-center gap-3 rounded-xl p-3"
              style="background:var(--portal-surface-alt);border:1px solid var(--portal-border);"
            >
              <div class="h-8 w-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                :style="{ background: OFFICE_COLOR[managingTeam.office] || '#6b7280' }">
                {{ initials(m.employee_name) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold" style="color:var(--portal-text);">{{ m.employee_name }}</div>
                <div v-if="m.designation" class="text-xs mt-0.5" style="color:var(--portal-muted);">{{ m.designation }}</div>
              </div>
              <button
                class="h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0 transition hover:bg-red-50"
                title="Remove from team"
                :disabled="removingMemberId === m.name"
                @click="removeMember(m)"
              >
                <FeatherIcon name="x" class="h-3.5 w-3.5" :style="{ color: removingMemberId === m.name ? '#d1d5db' : '#dc2626' }"/>
              </button>
            </div>
            <p v-if="!(managingTeam.members || []).length" class="text-xs text-center py-6" style="color:var(--portal-muted);">
              No members yet.
            </p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Edit Team Modal -->
  <Teleport to="body">
    <div
      v-if="showEditTeam"
      class="fixed inset-0 z-[60] flex items-center justify-center p-4"
      style="background:rgba(0,0,0,0.55);"
      @click.self="closeEditTeam"
    >
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
          <button
            class="portal-btn portal-btn-primary"
            :disabled="savingTeam"
            @click="submitEditTeam"
          >{{ savingTeam ? "Saving…" : "Save Changes" }}</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Add Member Modal -->
  <Teleport to="body">
    <div
      v-if="showAddMember"
      class="fixed inset-0 z-[60] flex items-center justify-center p-4"
      style="background:rgba(0,0,0,0.55);"
      @click.self="closeAddMember"
    >
      <div class="w-full max-w-md rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]">
          <h2 class="text-lg font-bold" style="color:var(--portal-text);">Add Member</h2>
          <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeAddMember">
            <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
          </button>
        </div>
        <div class="px-6 py-4">
          <input
            v-model="addMemberSearch"
            type="search"
            placeholder="Search users or user groups"
            class="portal-input w-full mb-3"
          />
          <p v-if="addMemberError" class="text-xs text-red-600 mb-2">{{ addMemberError }}</p>
          <div class="max-h-[50vh] overflow-y-auto">
            <template v-if="filteredUserGroups.length">
              <div class="text-[10px] font-semibold uppercase tracking-wider mb-1.5 px-0.5" style="color:var(--portal-muted);">User Groups</div>
              <div class="space-y-1.5 mb-3">
                <button
                  v-for="g in filteredUserGroups"
                  :key="'group:' + g.name"
                  type="button"
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
                v-for="u in filteredAssignable"
                :key="u.name"
                type="button"
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
              <div v-if="!filteredAssignable.length && !filteredUserGroups.length" class="text-center text-xs py-6" style="color:var(--portal-muted);">
                No matching users or groups.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
