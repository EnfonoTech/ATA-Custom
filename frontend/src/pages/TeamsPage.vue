<script setup>
import { ref, computed, onMounted } from "vue";
import { FeatherIcon } from "frappe-ui";
import { call } from "@/api";

const officeFilter  = ref("ALL");
const selectedTeam  = ref(null);
const loading       = ref(true);
const teams         = ref([]);
const officeList    = ref(["ALL"]);

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

onMounted(async () => {
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
          name:        m.employee_name,
          designation: m.designation || "—",
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
});

const filtered      = computed(() => {
  if (officeFilter.value === "ALL") return teams.value;
  return teams.value.filter(t => t.office === officeFilter.value);
});
const totalMembers  = computed(() => teams.value.reduce((s, t) => s + t.memberCount, 0));

function openTeam(team)  { selectedTeam.value = team; }
function closeTeam()     { selectedTeam.value = null; }
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
          <button class="h-8 w-8 rounded-full flex items-center justify-center transition hover:bg-[color:var(--portal-surface-alt)]" @click="closeTeam">
            <FeatherIcon name="x" class="h-4 w-4" style="color:var(--portal-muted);"/>
          </button>
        </div>

        <!-- Members List -->
        <div class="px-6 py-4 max-h-[60vh] overflow-y-auto">
          <div class="text-xs font-semibold uppercase tracking-wider mb-3" style="color:var(--portal-muted);">Team Members</div>
          <div class="space-y-2">
            <div
              v-for="m in selectedTeam.memberList"
              :key="m.name"
              class="flex items-center gap-3 rounded-xl p-3"
              style="background:var(--portal-surface-alt);border:1px solid var(--portal-border);"
            >
              <div class="h-8 w-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                :style="{ background: avatarBg(selectedTeam.office) }">
                {{ initials(m.name) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold" style="color:var(--portal-text);">{{ m.name }}</div>
                <div class="text-xs mt-0.5" style="color:var(--portal-muted);">{{ m.designation }}</div>
                <div v-if="m.email" class="text-[10px] mt-0.5" style="color:var(--portal-subtle);">{{ m.email }}</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>
