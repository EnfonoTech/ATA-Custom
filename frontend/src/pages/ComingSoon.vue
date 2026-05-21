<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { FeatherIcon } from "frappe-ui";

const route = useRoute();
const router = useRouter();

const moduleName = computed(() => route.query.m || route.query.module || "This module");

const MODULE_META = {
  CRM:           { icon: "users",          desc: "Customer relationship management, leads, opportunities, and sales pipeline." },
  HR:            { icon: "user",           desc: "Human resources, employee management, attendance, leaves, and payroll." },
  Finance:       { icon: "dollar-sign",    desc: "Financial accounting, ledgers, journal entries, and financial reports." },
  Accounts:      { icon: "book-open",      desc: "Accounts payable, receivable, invoices, and payment management." },
  Purchases:     { icon: "shopping-cart",  desc: "Purchase orders, supplier management, and procurement workflows." },
  Stock:         { icon: "package",        desc: "Inventory management, warehouses, stock movements, and valuations." },
  Manufacturing: { icon: "tool",           desc: "Bill of materials, work orders, production planning, and quality control." },
  Assets:        { icon: "server",         desc: "Fixed asset management, depreciation schedules, and asset tracking." },
  Helpdesk:      { icon: "headphones",     desc: "Customer support tickets, SLA management, and issue tracking." },
  Reports:       { icon: "bar-chart-2",    desc: "Analytics, custom reports, dashboards, and data exports." },
  Settings:      { icon: "settings",       desc: "System configuration, user roles, and portal preferences." },
};

const meta = computed(() => MODULE_META[moduleName.value] || { icon: "zap", desc: "This module is currently under development." });
</script>

<template>
  <div class="flex h-full items-center justify-center p-8" style="background: var(--portal-bg)">
    <div class="w-full max-w-md text-center portal-anim-in">
      <!-- Icon circle -->
      <div
        class="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-3xl shadow-lg"
        style="background: linear-gradient(135deg, var(--portal-accent-soft) 0%, var(--portal-surface) 100%); border: 2px solid var(--portal-border);"
      >
        <FeatherIcon
          :name="meta.icon"
          class="h-10 w-10"
          style="color: var(--portal-accent);"
        />
      </div>

      <!-- Badge -->
      <span
        class="inline-block rounded-full px-3 py-1 text-xs font-bold uppercase tracking-widest mb-4"
        style="background: var(--portal-accent-soft); color: var(--portal-accent-strong);"
      >
        Coming Soon
      </span>

      <!-- Title -->
      <h1 class="text-3xl font-bold mb-3" style="color: var(--portal-text);">
        {{ moduleName }}
      </h1>

      <!-- Description -->
      <p class="text-base leading-relaxed mb-8" style="color: var(--portal-muted);">
        {{ meta.desc }}
        <br class="hidden sm:block" />
        We're building this for you — stay tuned.
      </p>

      <!-- Progress bar decoration -->
      <div class="mx-auto mb-8 h-1.5 w-48 rounded-full overflow-hidden" style="background: var(--portal-border);">
        <div
          class="h-full rounded-full"
          style="width: 45%; background: linear-gradient(90deg, var(--portal-accent), var(--portal-accent-strong));"
        ></div>
      </div>

      <!-- Action -->
      <button
        class="portal-btn"
        @click="router.back()"
      >
        <FeatherIcon name="arrow-left" class="h-4 w-4" />
        Go back
      </button>

      <!-- Subtle grid decoration -->
      <div
        class="absolute inset-0 -z-10 opacity-30 pointer-events-none"
        style="background-image: radial-gradient(var(--portal-border) 1px, transparent 1px); background-size: 28px 28px;"
      ></div>
    </div>
  </div>
</template>
