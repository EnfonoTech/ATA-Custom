<template>
  <div>
    <!-- Node row -->
    <div
      class="flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 mb-1.5"
      :style="nodeStyle"
      @click="selectMember"
    >
      <!-- expand/collapse -->
      <button
        v-if="hasChildren"
        class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold transition-colors"
        :style="btnStyle"
        @click.stop="$emit('toggle', node.id)"
      >
        {{ isExpanded ? '−' : '+' }}
      </button>
      <div v-else class="w-6 h-6 flex-shrink-0" />

      <!-- avatar -->
      <div
        class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
        :style="{ background: officeColor }"
      >
        {{ initials }}
      </div>

      <!-- name + role -->
      <div class="min-w-0 flex-1">
        <p class="text-xs font-semibold truncate" style="color:var(--portal-text);">{{ node.name }}</p>
        <p class="text-[10px] truncate mt-0.5" style="color:var(--portal-muted);">{{ node.role }}</p>
      </div>

      <!-- office badge -->
      <span class="text-[9px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0 hidden sm:block" :style="badgeStyle">
        {{ node.office }}
      </span>

      <!-- manage team (edit / add-remove members) — team-level nodes only -->
      <button
        v-if="depth === 0 && canManageTeams"
        class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition hover:bg-black/5"
        title="Manage team"
        @click.stop="$emit('manage', node.id)"
      >
        <FeatherIcon name="edit-2" class="h-3.5 w-3.5" :style="{ color: officeColor }" />
      </button>
    </div>

    <!-- children -->
    <div v-if="isExpanded && hasChildren" class="pl-5 border-l ml-4 mb-1" style="border-color:var(--portal-border);">
      <OrgNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :expanded="expanded"
        :selected-id="selectedId"
        :can-manage-teams="canManageTeams"
        @toggle="$emit('toggle', $event)"
        @select="$emit('select', $event)"
        @manage="$emit('manage', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { FeatherIcon } from "frappe-ui";

const props = defineProps({
  node:            { type: Object, required: true },
  depth:           { type: Number, default: 0 },
  expanded:        { type: Object, required: true },
  selectedId:      { type: String, default: null },
  canManageTeams:  { type: Boolean, default: false },
});

const emit = defineEmits(["toggle", "select", "manage"]);

const OFFICE_COLOR  = { RIYADH: "#C9A84C", LISBON: "#185FA5", MANILA: "#276749" };
const OFFICE_BG     = { RIYADH: "rgba(201,168,76,0.12)",  LISBON: "rgba(24,95,165,0.12)",  MANILA: "rgba(39,103,73,0.12)"  };
const OFFICE_BORDER = { RIYADH: "rgba(201,168,76,0.30)",  LISBON: "rgba(24,95,165,0.30)",  MANILA: "rgba(39,103,73,0.30)"  };

const hasChildren  = computed(() => (props.node.children || []).length > 0);
const isExpanded   = computed(() => props.expanded.has(props.node.id));
const isSelected   = computed(() => props.selectedId === props.node.id);
const officeColor  = computed(() => OFFICE_COLOR[props.node.office]  || "#6b7280");

const nodeStyle = computed(() => ({
  background: isSelected.value
    ? "rgba(245,158,11,0.12)"
    : (OFFICE_BG[props.node.office] || "var(--portal-surface-alt)"),
  border: isSelected.value
    ? "1px solid rgba(245,158,11,0.4)"
    : `1px solid ${OFFICE_BORDER[props.node.office] || "var(--portal-border)"}`,
}));

const badgeStyle = computed(() => ({
  background: OFFICE_BG[props.node.office]     || "var(--portal-surface-alt)",
  color:      OFFICE_COLOR[props.node.office]  || "#6b7280",
  border:     `1px solid ${OFFICE_BORDER[props.node.office] || "var(--portal-border)"}`,
}));

const btnStyle = computed(() => ({
  background: OFFICE_BG[props.node.office]    || "var(--portal-surface-alt)",
  color:      OFFICE_COLOR[props.node.office] || "#6b7280",
  border:     `1px solid ${OFFICE_BORDER[props.node.office] || "var(--portal-border)"}`,
}));

const initials = computed(() => {
  const parts = props.node.name.trim().split(" ");
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : props.node.name.slice(0, 2).toUpperCase();
});

function selectMember() {
  emit("select", props.node);
}
</script>
