<script setup>
import { ref, computed, onMounted, inject } from "vue";
import { FeatherIcon } from "frappe-ui";
import { call } from "@/api";

const officeFilter  = ref("ALL");
const selectedTeam  = ref(null);
const loading       = ref(true);
const teams         = ref([]);
const officeList    = ref(["ALL"]);

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

// Predefined palette — cycles for any number of offices
const PALETTE_SOLID  = ["#C9A84C","#185FA5","#276749","#9b5de5","#f15bb5","#00bbf9","#e63946"];
const PALETTE_BG     = ["rgba(201,168,76,0.15)","rgba(24,95,165,0.15)","rgba(39,103,73,0.15)","rgba(155,93,229,0.15)","rgba(241,91,181,0.15)","rgba(0,187,249,0.15)","rgba(230,57,70,0.15)"];
const PALETTE_BORDER = ["rgba(201,168,76,0.4)","rgba(24,95,165,0.4)","rgba(39,103,73,0.4)","rgba(155,93,229,0.4)","rgba(241,91,181,0.4)","rgba(0,187,249,0.4)","rgba(230,57,70,0.4)"];

function officeIndex(office) {
  const idx = officeList.value.indexOf(office);
  return idx > 0 ? (idx - 1) % PALETTE_SOLID.length : PALETTE_SOLID.length - 1;
}
function officeBadgeStyle(office) {
  const i = officeIndex(office);
  return {
    background: PALETTE_BG[i]     ?? "rgba(128,128,128,0.1)",
    color:      PALETTE_SOLID[i]  ?? "#6b7280",
    border:     `1px solid ${PALETTE_BORDER[i] ?? "rgba(128,128,128,0.2)"}`,
  };
}
function avatarBg(office) {
  const i = officeIndex(office);
  return PALETTE_SOLID[i] ?? "#6b7280";
}
function initials(name) {
  if (!name) return "?";
  return name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

async function loadTeams() {
  try {
    const [data, offices] = await Promise.all([
      call({ method: "portal_app.api.teams.get_teams" }),
      call({ method: "portal_app.api.teams.get_offices" }),
    ]);
    if (Array.isArray(offices) && offices.length) {
      officeList.value = ["ALL", ...offices];
    }
    if (Array.isArray(data) && data) {
      teams.value = data.map(dept => ({
        id:          dept.name,
        name:        dept.department_name,
        office:      dept.office || "OTHER",
        memberCount: dept.member_count,
        memberList:     (dept.members || []).map(m => ({
          id:          m.name,
          name:        m.employee_name,
          designation: m.designation || "",
          email:       m.company_email || "",
        })),
        lead:           (dept.members && dept.members[0]) ? dept.members[0].employee_name : dept.department_name,
        projectCount:   dept.project_count || 0,
        activeProjects: dept.active_project_count || 0,
      }));
    }
  } catch (e) {
    console.error("get_teams error", e);
  } finally {
    loading.value = false;
  }
}

function refreshSelectedTeam() {
  if (!selectedTeam.value) return;
  selectedTeam.value = teams.value.find(t => t.id === selectedTeam.value.id) || null;
}

onMounted(loadTeams);

const filtered      = computed(() => {
  if (officeFilter.value === "ALL") return teams.value;
  return teams.value.filter(t => t.office === officeFilter.value);
});
const totalMembers  = computed(() => teams.value.reduce((s, t) => s + t.memberCount, 0));

function openTeam(team)  { selectedTeam.value = team; }
function closeTeam()     { selectedTeam.value = null; }

// ── Edit Team ─────────────────────────────────────────────────────────────
const showEditTeam  = ref(false);
const savingTeam    = ref(false);
const teamEditError = ref("");
const teamEditForm  = ref({ id: "", department_name: "", office: "" });
const editableOffices = computed(() => officeList.value.filter(o => o !== "ALL"));

function openEditTeam() {
  if (!selectedTeam.value) return;
  teamEditError.value = "";
  teamEditForm.value = {
    id:              selectedTeam.value.id,
    department_name: selectedTeam.value.name,
    office:          selectedTeam.value.office,
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
    await loadTeams();
    refreshSelectedTeam();
  } catch (e) {
    teamEditError.value = apiErr(e);
  } finally {
    savingTeam.value = false;
  }
}

// ── Add / Remove Member ──────────────────────────────────────────────────
// Team membership = Frappe's standard "Assign To" on the Department doc, so
// members here are Users (portal logins), not Employees. Mirrors Frappe's
// native assign dialog: pick an individual User, or a whole User Group at once.
const showAddMember     = ref(false);
const assignableUsers   = ref([]);
const userGroups        = ref([]);
const addMemberSearch   = ref("");
const addMemberError    = ref("");
const addingMemberName  = ref(null);
const removingMemberId  = ref(null);

async function openAddMember() {
  if (!selectedTeam.value) return;
  addMemberError.value = "";
  addMemberSearch.value = "";
  try {
    const [users, groups] = await Promise.all([
      call({ method: "portal_app.api.teams.get_assignable_users", args: { team: selectedTeam.value.id } }),
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
  if (!selectedTeam.value) return;
  addingMemberName.value = user.name;
  addMemberError.value = "";
  try {
    await call({
      method: "portal_app.api.teams.add_team_member",
      type: "POST",
      args: { team: selectedTeam.value.id, user: user.name },
    });
    closeAddMember();
    await loadTeams();
    refreshSelectedTeam();
  } catch (e) {
    addMemberError.value = apiErr(e);
  } finally {
    addingMemberName.value = null;
  }
}

async function addMemberGroup(group) {
  if (!selectedTeam.value) return;
  addingMemberName.value = `group:${group.name}`;
  addMemberError.value = "";
  try {
    await call({
      method: "portal_app.api.teams.add_team_member",
      type: "POST",
      args: { team: selectedTeam.value.id, user_group: group.name },
    });
    closeAddMember();
    await loadTeams();
    refreshSelectedTeam();
  } catch (e) {
    addMemberError.value = apiErr(e);
  } finally {
    addingMemberName.value = null;
  }
}

async function removeMember(m) {
  if (!selectedTeam.value) return;
  removingMemberId.value = m.id;
  try {
    await call({
      method: "portal_app.api.teams.remove_team_member",
      type: "POST",
      args: { team: selectedTeam.value.id, user: m.id },
    });
    await loadTeams();
    refreshSelectedTeam();
  } catch (e) {
    console.error(e);
  } finally {
    removingMemberId.value = null;
  }
}
</script>

<template>
  <div class="h-full overflow-auto p-6" style="background: var(--portal-bg)">
    <div class="mx-auto max-w-7xl space-y-5">

      <!-- Header -->
      <div class="portal-hero portal-anim-in">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <span class="portal-pill portal-pill-accent">
              <FeatherIcon name="users" class="h-3 w-3" />
              Workload
            </span>
            <h1 class="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--portal-text)]">
              Teams &amp; Members
            </h1>
            <p class="mt-1 text-sm text-[color:var(--portal-muted)]">
              {{ filtered.length }} departments · {{ totalMembers }} members
            </p>
          </div>

          <!-- Office filter -->
          <div class="inline-flex rounded-xl border border-[color:var(--portal-border)] p-0.5 shadow-sm" style="background:var(--portal-surface)">
            <button
              v-for="o in officeList" :key="o"
              type="button"
              class="rounded-lg px-3 py-1.5 text-xs font-semibold transition"
              :style="officeFilter === o
                ? 'background:' + (o === 'ALL' ? 'var(--portal-accent)' : avatarBg(o)) + ';color:#fff;'
                : 'color:var(--portal-muted);'"
              @click="officeFilter = o"
            >{{ o }}</button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center gap-2 text-[color:var(--portal-muted)]">
        <span class="h-3 w-3 animate-spin rounded-full border-2 border-[color:var(--portal-accent)] border-t-transparent"></span>
        Loading teams…
      </div>

      <!-- Team Cards Grid -->
      <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <div
          v-for="team in filtered"
          :key="team.id"
          class="portal-card p-5 flex flex-col gap-3 transition hover:-translate-y-0.5 cursor-pointer"
          :style="{ borderTop: '3px solid ' + avatarBg(team.office) }"
          @click="openTeam(team)"
        >
          <!-- Team header -->
          <div class="flex items-center gap-3">
            <div
              class="h-10 w-10 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
              :style="{ background: avatarBg(team.office) }"
            >
              {{ initials(team.lead) }}
            </div>
            <div class="min-w-0">
              <div class="font-semibold text-sm truncate" style="color:var(--portal-text);">{{ team.name }}</div>
              <div class="text-xs truncate" style="color:var(--portal-muted);">{{ team.memberCount }} members</div>
            </div>
          </div>

          <!-- Office badge + project count -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full" :style="officeBadgeStyle(team.office)">
              {{ team.office }}
            </span>
            <span v-if="team.projectCount > 0" class="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border);color:var(--portal-muted);">
              <FeatherIcon name="folder" class="h-3 w-3" />
              {{ team.activeProjects }}/{{ team.projectCount }} projects
            </span>
          </div>

          <!-- Member avatars preview -->
          <div class="flex items-center gap-1 flex-wrap">
            <div
              v-for="m in team.memberList.slice(0, 6)" :key="m.name"
              class="h-7 w-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold border-2 -ml-1 first:ml-0"
              :style="{ background: avatarBg(team.office), borderColor: 'var(--portal-surface)' }"
              :title="m.name"
            >{{ initials(m.name) }}</div>
            <span v-if="team.memberList.length > 6" class="text-[10px] ml-1" style="color:var(--portal-muted);">
              +{{ team.memberList.length - 6 }} more
            </span>
          </div>

          <!-- Footer -->
          <div class="flex items-center gap-2 pt-2 border-t border-[color:var(--portal-border)]">
            <FeatherIcon name="users" class="h-3.5 w-3.5" style="color:var(--portal-subtle);"/>
            <span class="text-xs" style="color:var(--portal-muted);">Click to view members</span>
          </div>
        </div>

        <div v-if="!filtered.length && !loading" class="sm:col-span-2 xl:col-span-3 p-10 text-center text-[color:var(--portal-muted)]">
          No teams for this office.
        </div>
      </div>

    </div>
  </div>

  <!-- Team Detail Modal -->
  <Teleport to="body">
    <div
      v-if="selectedTeam"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background:rgba(0,0,0,0.6);"
      @click.self="closeTeam"
    >
      <div class="w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden" style="background:var(--portal-surface);">

        <!-- Modal Header -->
        <div class="flex items-center justify-between px-6 py-5 border-b border-[color:var(--portal-border)]"
          :style="{ borderTop: '4px solid ' + avatarBg(selectedTeam.office) }">
          <div class="flex items-center gap-3">
            <div class="h-11 w-11 rounded-xl flex items-center justify-center text-white font-bold"
              :style="{ background: avatarBg(selectedTeam.office) }">
              {{ initials(selectedTeam.lead) }}
            </div>
            <div>
              <h2 class="text-lg font-bold" style="color:var(--portal-text);">{{ selectedTeam.name }}</h2>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full" :style="officeBadgeStyle(selectedTeam.office)">
                  {{ selectedTeam.office }}
                </span>
                <span class="text-xs" style="color:var(--portal-muted);">{{ selectedTeam.memberCount }} members</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button
              v-if="canManageTeams"
              class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-accent-soft)]"
              title="Edit team"
              @click="openEditTeam"
            >
              <FeatherIcon name="edit-2" class="h-4 w-4" style="color:var(--portal-accent);"/>
            </button>
            <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeTeam">
              <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
            </button>
          </div>
        </div>

        <!-- Members List -->
        <div class="px-6 py-4 max-h-[60vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-3">
            <div class="text-xs font-semibold uppercase tracking-wider" style="color:var(--portal-muted);">Team Members</div>
            <button
              v-if="canManageTeams"
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
              v-for="m in selectedTeam.memberList"
              :key="m.id"
              class="flex items-center gap-3 rounded-xl p-3"
              style="background:var(--portal-surface-alt);border:1px solid var(--portal-border);"
            >
              <div class="h-8 w-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                :style="{ background: avatarBg(selectedTeam.office) }">
                {{ initials(m.name) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold" style="color:var(--portal-text);">{{ m.name }}</div>
                <div v-if="m.designation" class="text-xs mt-0.5" style="color:var(--portal-muted);">{{ m.designation }}</div>
                <div v-if="m.email" class="text-[10px] mt-0.5" style="color:var(--portal-subtle);">{{ m.email }}</div>
              </div>
              <button
                v-if="canManageTeams"
                class="h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0 transition hover:bg-red-50"
                title="Remove from team"
                :disabled="removingMemberId === m.id"
                @click="removeMember(m)"
              >
                <FeatherIcon name="x" class="h-3.5 w-3.5" :style="{ color: removingMemberId === m.id ? '#d1d5db' : '#dc2626' }"/>
              </button>
            </div>
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
