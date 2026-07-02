<script setup>
import { ref, computed, onMounted } from "vue";
import { FeatherIcon } from "frappe-ui";
import OrgNode from "@/components/OrgNode.vue";
import { call } from "@/api";

const loading    = ref(true);
const orgTree    = ref([]);
const headcount  = ref([]);
const officeList = ref(["ALL"]);

onMounted(async () => {
  try {
    const teams = await call({ method: "portal_app.api.teams.get_teams" });
    if (!Array.isArray(teams)) return;

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
});

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
              @toggle="toggleExpand"
              @select="selectMember"
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
</template>
