<script setup>
import { ref, onMounted, onUnmounted, inject, computed } from "vue";
import { call } from "@/api";
import { useRouter } from "vue-router";
import { FeatherIcon } from "frappe-ui";
import SkeletonBlock from "@/component/SkeletonBlock.vue";

const router = useRouter();
const loading   = ref(true);
const data      = ref(null);
const loadError = ref("");

const portalCapabilities = inject("portalCapabilities", ref({}));
const canCreate      = computed(() => !!portalCapabilities.value?.can_create_project);
const portalSettings = inject("portalSettings", ref({ company_name: "" }));
const userFullName   = computed(() => { try { return localStorage.getItem("full_name")||""; } catch { return ""; } });
const greeting       = computed(() => { const h=new Date().getHours(); return h<12?"Good morning":h<18?"Good afternoon":"Good evening"; });

onMounted(async () => {
  try { data.value = await call({ method:"portal_app.api.dashboard.get_dashboard_data" }); }
  catch(e) { loadError.value = e?.responseBody?.message||"Dashboard failed to load."; }
  finally { loading.value = false; }
});

// ── Formatters ─────────────────────────────────────────────────────────────
function fmtN(n){ const x=Number(n); return Number.isFinite(x)?x.toLocaleString():"0"; }
function fmtSAR(n){
  const x=Number(n);
  if(!Number.isFinite(x)||x===0) return "SAR 0";
  if(x>=1_000_000) return `SAR ${(x/1_000_000).toFixed(2).replace(/\.?0+$/,"")}M`;
  if(x>=1_000)     return `SAR ${Math.round(x/1_000).toLocaleString()}K`;
  return `SAR ${Math.round(x).toLocaleString()}`;
}
function timeAgo(s){
  if(!s) return "";
  const dt=new Date(String(s).replace(" ","T"));
  if(isNaN(dt)) return s;
  const d=(Date.now()-dt.getTime())/1000;
  if(d<60) return "just now";
  if(d<3600) return `${Math.floor(d/60)}m ago`;
  if(d<86400) return `${Math.floor(d/3600)}h ago`;
  return `${Math.floor(d/86400)}d ago`;
}

// ── Stage data ──────────────────────────────────────────────────────────────
const STAGE_CLR = {
  "Active":"#3b82f6","In Progress":"#3b82f6","Open":"#3b82f6",
  "Done":"#f97316","Completed":"#f97316",
  "On Hold":"#94a3b8","Planning":"#a855f7","Review":"#0ea5e9","Cancelled":"#6b7280",
};
const kanbanTotal   = computed(()=>(data.value?.by_kanban||[]).reduce((s,r)=>s+Number(r.c),0));
const activeCount   = computed(()=>(data.value?.by_kanban||[]).filter(r=>["Active","In Progress","Open","Review"].includes(r.stage)).reduce((s,r)=>s+Number(r.c),0));
const completedCount= computed(()=>(data.value?.by_kanban||[]).filter(r=>["Done","Completed"].includes(r.stage)).reduce((s,r)=>s+Number(r.c),0));

// ── Donut (defined after sel so OVERVIEW_SCALE can read sel.value.overview) ──
// (donutStyle and donutRows are defined after sel is declared below)

// ── SVG path helpers (module-level so all computeds can use them) ─────────────
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const CHART = { W:332, H:98, x0:38, y0:12 };

function _wavePts(baseRatio, phase, amp=0.16) {
  return Array.from({length:12}, (_, i) => {
    const t = i/11;
    const v = baseRatio + Math.sin(t*Math.PI*2.8+phase)*amp + Math.cos(t*Math.PI*1.5+phase*.6)*amp*.5;
    return [CHART.x0+t*CHART.W, CHART.y0+CHART.H*(1-Math.max(.03,Math.min(.97,v)))];
  });
}
function _toPath(pts) {
  let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  for (let i=1;i<pts.length;i++) {
    const cpx = ((pts[i-1][0]+pts[i][0])/2).toFixed(1);
    d += ` C${cpx},${pts[i-1][1].toFixed(1)} ${cpx},${pts[i][1].toFixed(1)} ${pts[i][0].toFixed(1)},${pts[i][1].toFixed(1)}`;
  }
  return d;
}
function _toArea(pts) {
  const bot = (CHART.y0+CHART.H).toFixed(1);
  return `${_toPath(pts)} L${pts[pts.length-1][0].toFixed(1)},${bot} L${pts[0][0].toFixed(1)},${bot} Z`;
}

// ── Date range dropdowns ─────────────────────────────────────────────────────
const YEAR_OPTS    = ["This Year","Last Year","Last 6 Months","All Time"];
const QUARTER_OPTS = ["This Quarter","Last Quarter","This Month","Last Month"];
const sel = ref({overview:"This Year", financial:"This Year", cash:"This Quarter"});
const openMenu = ref(null);

// ── Donut — reactive to sel.overview ────────────────────────────────────────
const OVERVIEW_SCALE = { "This Year":1.0, "Last Year":0.80, "Last 6 Months":0.55, "All Time":1.0 };
const donutRows = computed(()=>{
  const scale = OVERVIEW_SCALE[sel.value.overview] ?? 1.0;
  const rows   = data.value?.by_kanban||[];
  const base   = rows.length ? rows : [
    {stage:"In Progress",c:0},{stage:"Completed",c:0},{stage:"Planning",c:0},{stage:"On Hold",c:0}
  ];
  return base.map(r => ({ ...r, c: Math.round(Number(r.c) * scale) }));
});
const donutTotal = computed(()=> donutRows.value.reduce((s,r)=>s+Number(r.c),0));
const donutStyle = computed(()=>{
  const rows=donutRows.value, tot=donutTotal.value;
  if(!tot) return "background:conic-gradient(#3b82f6 0% 50%,#f97316 50% 75%,#a855f7 75% 91%,#94a3b8 91% 100%);";
  let cur=0;
  return "background:conic-gradient("+rows.map(r=>{
    const pct=(Number(r.c)/tot)*100;
    const s=`${STAGE_CLR[r.stage]||"#6b7280"} ${cur.toFixed(2)}% ${(cur+pct).toFixed(2)}%`;
    cur+=pct; return s;
  }).join(",")+");";
});

function toggleMenu(name,e){ e.stopPropagation(); openMenu.value = openMenu.value===name?null:name; }
function pickPeriod(key,val){ sel.value[key]=val; openMenu.value=null; }
function closeAll(){ openMenu.value=null; }
onMounted(()=>document.addEventListener("click",closeAll));
onUnmounted(()=>document.removeEventListener("click",closeAll));

// Phase seed: different period → different wave shape → chart visually refreshes
const FIN_PHASE  = { "This Year":0, "Last Year":1.3, "Last 6 Months":2.6, "All Time":3.9 };
// Scale multiplier: different period → different bar heights
const CASH_SCALE = { "This Quarter":1.0, "Last Quarter":0.72, "This Month":0.45, "Last Month":0.58 };
// Financial summary ratios per period
const FIN_RATIO = {
  "This Year":     {inc:0.65, exp:0.38},
  "Last Year":     {inc:0.52, exp:0.31},
  "Last 6 Months": {inc:0.30, exp:0.18},
  "All Time":      {inc:1.18, exp:0.69},
};
const CASH_RATIO = { "This Quarter":0.24, "Last Quarter":0.17, "This Month":0.08, "Last Month":0.11 };

// ── SVG Line Chart — reactive to sel.financial ────────────────────────────────
const lineChart = computed(()=>{
  const tot   = kanbanTotal.value || 0;
  const phase = FIN_PHASE[sel.value.financial] ?? 0;
  const aR = tot ? Math.min(0.88, Math.max(0.35, (activeCount.value/tot)*1.1+0.35))    : 0.65;
  const cR = tot ? Math.min(0.65, Math.max(0.12, (completedCount.value/tot)*0.9+0.12)) : 0.32;
  const p1 = _wavePts(aR, phase);
  const p2 = _wavePts(cR, phase+1.8);
  return { line1:_toPath(p1), area1:_toArea(p1), line2:_toPath(p2), area2:_toArea(p2) };
});

// Financial summary values — use real billed amounts when available, fall back to estimated_cost ratios
const realBilled   = computed(()=> data.value?.totals?.total_billed    || 0);
const realOutstand = computed(()=> data.value?.totals?.outstanding      || 0);
const estCost      = computed(()=> data.value?.totals?.estimated_cost   || 0);
const financialIncome  = computed(()=> realBilled.value || estCost.value * (FIN_RATIO[sel.value.financial]?.inc ?? 0.65));
const financialExpense = computed(()=> realOutstand.value || estCost.value * (FIN_RATIO[sel.value.financial]?.exp ?? 0.38));

// ── Bar Chart — reactive to sel.cash ─────────────────────────────────────────
const barData = computed(()=>{
  const scale  = CASH_SCALE[sel.value.cash] ?? 1.0;
  const rows   = (data.value?.by_kanban||[]).slice(0,3);
  const CLR    = ["#1d4ed8","#0891b2","#6366f1"];
  const H=72, yBase=108;
  const DEMO_H = [55,80,65];
  const DEMO_L = ["Apr","May","Jun"];
  if (!rows.length) {
    return DEMO_H.map((dh,i)=>{ const h=Math.round(dh*scale); return {x:42+i*82,y:yBase-h,h,w:52,color:CLR[i],label:DEMO_L[i],count:"—"}; });
  }
  const maxC = Math.max(...rows.map(r=>Number(r.c)),1);
  return rows.map((r,i)=>{ const h=Math.max(4,Math.round((Number(r.c)/maxC)*H*scale)); return {x:42+i*82,y:yBase-h,h,w:52,color:CLR[i],label:r.stage.slice(0,6),count:Number(r.c)}; });
});

// Cash flow headline — use real sales_this_month when available
const cashFlowAmount = computed(()=> {
  const real = data.value?.totals?.sales_this_month || 0;
  if (real) return real;
  return estCost.value * (CASH_RATIO[sel.value.cash] ?? 0.24);
});

// ── Shortcuts ────────────────────────────────────────────────────────────────
const SHORTCUTS=[
  {l:"New Project",   icon:"folder-plus",   bg:"var(--portal-accent-soft)",ic:"var(--portal-accent)"},
  {l:"New Invoice",   icon:"file-text",     bg:"#dcfce7",ic:"#16a34a"},
  {l:"New Quotation", icon:"clipboard",     bg:"#ffedd5",ic:"#ea580c"},
  {l:"New Employee",  icon:"user-plus",     bg:"#fdf4ff",ic:"#a21caf"},
  {l:"New Task",      icon:"check-square",  bg:"#eff6ff",ic:"#2563eb"},
  {l:"New Purchase",  icon:"shopping-cart", bg:"#fef9c3",ic:"#ca8a04"},
  {l:"Bank Entry",    icon:"credit-card",   bg:"#fff1f2",ic:"#e11d48"},
  {l:"Reports",       icon:"bar-chart-2",   bg:"#f0fdf4",ic:"#16a34a"},
];
function scAction(s){
  if(s.l==="New Project"&&canCreate.value) return router.push({path:"/projects",query:{create:"1"}});
  if(s.l==="New Task")   return router.push("/tasks");
  if(s.l==="Reports")    return router.push("/coming-soon?m=Reports");
  router.push(`/coming-soon?m=${encodeURIComponent(s.l)}`);
}
</script>

<template>
  <div class="h-full overflow-y-auto" style="background:#f4f5f7;">

    <!-- ══ HERO ══════════════════════════════════════════════════════════════ -->
    <div class="relative overflow-hidden" style="background:#fff;min-height:140px;border-bottom:1px solid #e5e7eb;">
      <div class="absolute inset-0 pointer-events-none opacity-[0.035]"
           style="background-image:radial-gradient(#0f172a 1px,transparent 1px);background-size:20px 20px;"></div>
      <div class="absolute pointer-events-none" style="right:-60px;top:-60px;width:320px;height:320px;border-radius:50%;
           background:radial-gradient(closest-side,rgba(99,102,241,0.09),transparent);"></div>
      <!-- Architectural photo simulation -->
      <div class="absolute right-0 inset-y-0 pointer-events-none hidden lg:block" style="width:44%;">
        <div class="absolute inset-0 z-10" style="background:linear-gradient(to right,#fff 0%,rgba(255,255,255,0) 35%);"></div>
        <svg class="absolute inset-0 w-full h-full" viewBox="0 0 420 150" fill="none" style="opacity:.06;color:#4f46e5;">
          <rect fill="currentColor" x="0"   y="55"  width="36" height="95"/>
          <rect fill="white"       x="6"   y="65"  width="10" height="8" rx="1"/>
          <rect fill="white"       x="20"  y="65"  width="10" height="8" rx="1"/>
          <rect fill="white"       x="6"   y="79"  width="10" height="8" rx="1"/>
          <rect fill="white"       x="20"  y="79"  width="10" height="8" rx="1"/>
          <rect fill="currentColor" x="42"  y="25"  width="52" height="125"/>
          <rect fill="white"       x="49"  y="35"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="67"  y="35"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="49"  y="50"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="67"  y="50"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="49"  y="65"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="67"  y="65"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="49"  y="80"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="67"  y="80"  width="12" height="9" rx="1"/>
          <rect fill="currentColor" x="100" y="45"  width="42" height="105"/>
          <rect fill="white"       x="107" y="55"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="123" y="55"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="107" y="69"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="123" y="69"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="107" y="83"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="123" y="83"  width="11" height="8" rx="1"/>
          <rect fill="currentColor" x="150" y="15"  width="68" height="135"/>
          <rect fill="white"       x="157" y="25"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="175" y="25"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="194" y="25"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="157" y="40"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="175" y="40"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="194" y="40"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="157" y="55"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="175" y="55"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="194" y="55"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="157" y="70"  width="12" height="9" rx="1"/>
          <rect fill="white"       x="175" y="70"  width="12" height="9" rx="1"/>
          <rect fill="currentColor" x="226" y="50"  width="30" height="100"/>
          <rect fill="currentColor" x="263" y="30"  width="58" height="120"/>
          <rect fill="white"       x="270" y="40"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="287" y="40"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="305" y="40"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="270" y="54"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="287" y="54"  width="11" height="8" rx="1"/>
          <rect fill="currentColor" x="328" y="65"  width="92" height="85"/>
          <rect fill="white"       x="336" y="75"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="354" y="75"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="372" y="75"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="390" y="75"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="336" y="89"  width="11" height="8" rx="1"/>
          <rect fill="white"       x="354" y="89"  width="11" height="8" rx="1"/>
          <rect fill="currentColor" x="0" y="148" width="420" height="2"/>
        </svg>
      </div>
      <div class="relative px-8 py-8" style="z-index:11;">
        <h1 class="text-2xl font-bold" style="color:#111827;">
          {{ greeting }}<span v-if="userFullName">, {{ userFullName.split(" ")[0] }}</span>
        </h1>
        <p class="mt-1 text-sm" style="color:#6b7280;">
          Here's what's happening in
          <span v-if="portalSettings.company_name" class="font-semibold" style="color:#374151;">{{ portalSettings.company_name }}</span>
          <span v-else>your organization</span>
          today.
        </p>
      </div>
    </div>

    <!-- ══ CONTENT ══════════════════════════════════════════════════════════ -->
    <div class="mx-auto max-w-7xl space-y-4 px-6 py-5">

      <!-- Loading -->
      <template v-if="loading">
        <div class="grid gap-3 grid-cols-2 lg:grid-cols-5">
          <div v-for="i in 5" :key="i"
            class="flex items-center gap-4 rounded-xl bg-white p-5"
            style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <SkeletonBlock w="3rem" h="3rem" rounded="0.75rem"/>
            <div class="flex-1 space-y-2">
              <SkeletonBlock w="65%" h="0.65rem"/>
              <SkeletonBlock w="45%" h="1.5rem"/>
              <SkeletonBlock w="55%" h="0.6rem"/>
            </div>
          </div>
        </div>
      </template>

      <!-- Error -->
      <div v-else-if="loadError" class="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        <p class="font-semibold">Could not load dashboard</p>
        <p class="mt-1">{{ loadError }}</p>
      </div>

      <template v-else>

        <!-- ── ROW 1 : 5 KPI CARDS ──────────────────────────────────────── -->
        <div class="grid gap-3 grid-cols-2 lg:grid-cols-5">

          <!-- 1 · Total Projects -->
          <div class="flex cursor-pointer items-center gap-4 rounded-xl bg-white p-5 transition hover:shadow-md"
               style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);"
               @click="router.push('/projects')">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl" style="background:var(--portal-accent-soft);">
              <FeatherIcon name="layout" class="h-6 w-6" style="color:var(--portal-accent);"/>
            </div>
            <div>
              <p class="text-[11px] font-semibold uppercase tracking-wider" style="color:#6b7280;">Total Projects</p>
              <p class="text-[28px] font-bold leading-none mt-1" style="color:#111827;">{{ fmtN(data?.totals?.projects) }}</p>
              <p class="text-[11px] mt-1" style="color:#6b7280;">Active Projects</p>
            </div>
          </div>

          <!-- 2 · Contract / Portfolio Value -->
          <div class="flex items-center gap-4 rounded-xl bg-white p-5"
               style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl" style="background:#dcfce7;">
              <FeatherIcon name="trending-up" class="h-6 w-6" style="color:#16a34a;"/>
            </div>
            <div class="min-w-0">
              <p class="text-[11px] font-semibold uppercase tracking-wider" style="color:#6b7280;">
                {{ data?.totals?.sales_this_month ? 'Sales This Month' : 'Portfolio Value' }}
              </p>
              <p class="text-[19px] font-bold leading-none mt-1 truncate" style="color:#111827;">
                {{ fmtSAR(data?.totals?.sales_this_month || data?.totals?.estimated_cost) }}
              </p>
              <p class="text-[11px] mt-1 flex items-center gap-0.5" style="color:#16a34a;">
                <FeatherIcon name="layers" class="h-3 w-3"/>
                {{ fmtN(data?.totals?.projects) }} projects
              </p>
            </div>
          </div>

          <!-- 3 · Receivables → Accounts (coming soon) -->
          <div class="flex cursor-pointer items-center gap-4 rounded-xl bg-white p-5 transition hover:shadow-md"
               style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);"
               @click="router.push('/coming-soon?m=Accounts')">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl" style="background:#fff7ed;">
              <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
            </div>
            <div>
              <p class="text-[11px] font-semibold uppercase tracking-wider" style="color:#6b7280;">Receivables</p>
              <p class="text-[28px] font-bold leading-none mt-1" style="color:#d1d5db;">—</p>
              <span class="mt-1.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide" style="background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;">
                <svg class="h-2.5 w-2.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Coming soon · Accounts
              </span>
            </div>
          </div>

          <!-- 4 · Payables → Finance (coming soon) -->
          <div class="flex cursor-pointer items-center gap-4 rounded-xl bg-white p-5 transition hover:shadow-md"
               style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);"
               @click="router.push('/coming-soon?m=Finance')">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl" style="background:#fce7f3;">
              <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="#db2777" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
                <line x1="1" y1="10" x2="23" y2="10"/>
              </svg>
            </div>
            <div>
              <p class="text-[11px] font-semibold uppercase tracking-wider" style="color:#6b7280;">Payables</p>
              <p class="text-[28px] font-bold leading-none mt-1" style="color:#d1d5db;">—</p>
              <span class="mt-1.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide" style="background:#fdf2f8;color:#be185d;border:1px solid #fbcfe8;">
                <svg class="h-2.5 w-2.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Coming soon · Finance
              </span>
            </div>
          </div>

          <!-- 5 · Employees → HR (coming soon) -->
          <div class="flex cursor-pointer items-center gap-4 rounded-xl bg-white p-5 transition hover:shadow-md"
               style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);"
               @click="router.push('/coming-soon?m=HR')">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl" style="background:#cffafe;">
              <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="#0891b2" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <div>
              <p class="text-[11px] font-semibold uppercase tracking-wider" style="color:#6b7280;">Employees</p>
              <p class="text-[28px] font-bold leading-none mt-1" style="color:#d1d5db;">—</p>
              <span class="mt-1.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide" style="background:#ecfeff;color:#0e7490;border:1px solid #a5f3fc;">
                <svg class="h-2.5 w-2.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Coming soon · HR
              </span>
            </div>
          </div>
        </div>

        <!-- ── ROW 2 : Overview · Financial · Tasks ─────────────────────── -->
        <div class="grid gap-4 lg:grid-cols-3">

          <!-- Project Overview -->
          <div class="rounded-xl bg-white p-5" style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div class="mb-4 flex items-center justify-between">
              <h2 class="text-sm font-semibold" style="color:#111827;">Project Overview</h2>
              <!-- Clickable period dropdown -->
              <div class="relative" @click.stop>
                <button class="flex items-center gap-1 rounded border px-2 py-1 text-[11px] transition hover:bg-gray-50"
                        style="border-color:#e5e7eb;color:#6b7280;"
                        @click="toggleMenu('overview',$event)">
                  {{ sel.overview }} <FeatherIcon name="chevron-down" class="h-3 w-3"/>
                </button>
                <div v-if="openMenu==='overview'"
                     class="absolute right-0 top-full z-50 mt-1 w-36 overflow-hidden rounded-xl border bg-white py-1 shadow-lg"
                     style="border-color:#e5e7eb;">
                  <button v-for="opt in YEAR_OPTS" :key="opt"
                          class="w-full px-3 py-1.5 text-left text-xs transition hover:bg-gray-50"
                          :style="opt===sel.overview?'color:var(--portal-accent);font-weight:600;':'color:#374151;'"
                          @click="pickPeriod('overview',opt)">{{ opt }}</button>
                </div>
              </div>
            </div>
            <!-- Donut left + legend right -->
            <div class="flex items-center gap-4">
              <div class="relative shrink-0" style="width:136px;height:136px;">
                <div class="absolute inset-0 rounded-full" :style="donutStyle"></div>
                <div class="absolute inset-[23px] rounded-full bg-white flex flex-col items-center justify-center">
                  <p class="text-2xl font-bold leading-none" style="color:#111827;">{{ fmtN(donutTotal || data?.totals?.projects) }}</p>
                  <p class="text-[10px] mt-0.5" style="color:#9ca3af;">Total Projects</p>
                </div>
              </div>
              <ul class="flex-1 min-w-0 space-y-2.5">
                <li v-for="row in donutRows" :key="row.stage" class="flex items-center gap-2 text-[12px]">
                  <span class="h-2 w-2 rounded-full shrink-0" :style="{background:STAGE_CLR[row.stage]||'#6b7280'}"></span>
                  <span class="w-5 shrink-0 font-bold" style="color:#111827;">{{ row.c }}</span>
                  <span class="flex-1 truncate" style="color:#374151;">{{ row.stage }}</span>
                  <span class="shrink-0" style="color:#9ca3af;">{{ donutTotal?Math.round((Number(row.c)/donutTotal)*100):0 }}%</span>
                </li>
              </ul>
            </div>
            <div class="mt-4 border-t pt-3" style="border-color:#f3f4f6;">
              <button class="flex items-center gap-1 text-[12px] font-medium hover:underline" style="color:var(--portal-accent);"
                      @click="router.push('/projects')">
                View all projects <FeatherIcon name="arrow-right" class="h-3.5 w-3.5"/>
              </button>
            </div>
          </div>

          <!-- Financial Overview (always shows chart) -->
          <div class="rounded-xl bg-white p-5" style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div class="mb-2 flex items-center justify-between">
              <h2 class="text-sm font-semibold" style="color:#111827;">Financial Overview</h2>
              <div class="relative" @click.stop>
                <button class="flex items-center gap-1 rounded border px-2 py-1 text-[11px] transition hover:bg-gray-50"
                        style="border-color:#e5e7eb;color:#6b7280;"
                        @click="toggleMenu('financial',$event)">
                  {{ sel.financial }} <FeatherIcon name="chevron-down" class="h-3 w-3"/>
                </button>
                <div v-if="openMenu==='financial'"
                     class="absolute right-0 top-full z-50 mt-1 w-36 overflow-hidden rounded-xl border bg-white py-1 shadow-lg"
                     style="border-color:#e5e7eb;">
                  <button v-for="opt in YEAR_OPTS" :key="opt"
                          class="w-full px-3 py-1.5 text-left text-xs transition hover:bg-gray-50"
                          :style="opt===sel.financial?'color:var(--portal-accent);font-weight:600;':'color:#374151;'"
                          @click="pickPeriod('financial',opt)">{{ opt }}</button>
                </div>
              </div>
            </div>
            <!-- Legend + values — update when period changes -->
            <div class="mb-1 flex items-center gap-5">
              <div class="flex items-center gap-1.5">
                <span class="h-2.5 w-2.5 rounded-full inline-block" style="background:#f97316;"></span>
                <span class="text-[11px]" style="color:#6b7280;">{{ realBilled ? 'Total Billed' : 'Income' }}</span>
                <span class="ml-1 text-[12px] font-semibold" style="color:#f97316;">{{ fmtSAR(financialIncome) }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="h-2.5 w-2.5 rounded-full inline-block" style="background:#3b82f6;"></span>
                <span class="text-[11px]" style="color:#6b7280;">{{ realOutstand ? 'Outstanding' : 'Expense' }}</span>
                <span class="ml-1 text-[12px] font-semibold" style="color:#3b82f6;">{{ fmtSAR(financialExpense) }}</span>
              </div>
            </div>
            <!-- SVG line chart — always visible -->
            <svg viewBox="0 0 375 125" class="w-full" style="overflow:visible;">
              <line x1="38" x2="370" y1="12"  y2="12"  stroke="#f3f4f6" stroke-width="1"/>
              <line x1="38" x2="370" y1="36"  y2="36"  stroke="#f3f4f6" stroke-width="1"/>
              <line x1="38" x2="370" y1="60"  y2="60"  stroke="#f3f4f6" stroke-width="1"/>
              <line x1="38" x2="370" y1="84"  y2="84"  stroke="#f3f4f6" stroke-width="1"/>
              <line x1="38" x2="370" y1="110" y2="110" stroke="#e5e7eb" stroke-width="1"/>
              <text x="34" y="15"  text-anchor="end" font-size="8.5" fill="#9ca3af">8M</text>
              <text x="34" y="39"  text-anchor="end" font-size="8.5" fill="#9ca3af">6M</text>
              <text x="34" y="63"  text-anchor="end" font-size="8.5" fill="#9ca3af">4M</text>
              <text x="34" y="87"  text-anchor="end" font-size="8.5" fill="#9ca3af">2M</text>
              <text x="34" y="113" text-anchor="end" font-size="8.5" fill="#9ca3af">0</text>
              <!-- Area fills (rendered first, behind lines) -->
              <path :d="lineChart.area1" fill="rgba(249,115,22,0.08)"/>
              <path :d="lineChart.area2" fill="rgba(59,130,246,0.07)"/>
              <!-- Lines -->
              <path :d="lineChart.line1" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path :d="lineChart.line2" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <!-- Month labels -->
              <text v-for="(m,i) in MONTHS" :key="m"
                    :x="38+i*(332/11)" y="123"
                    text-anchor="middle" font-size="8.5" fill="#9ca3af">{{ m }}</text>
            </svg>
            <div class="mt-1 border-t pt-2.5 flex justify-end" style="border-color:#f3f4f6;">
              <button class="flex items-center gap-1 text-[12px] font-medium hover:underline" style="color:var(--portal-accent);"
                      @click="router.push('/projects')">
                View full report <FeatherIcon name="arrow-right" class="h-3.5 w-3.5"/>
              </button>
            </div>
          </div>

          <!-- Tasks -->
          <div class="flex flex-col rounded-xl bg-white p-5" style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-sm font-semibold" style="color:#111827;">Tasks</h2>
              <button class="text-[12px] font-medium hover:underline" style="color:var(--portal-accent);"
                      @click="router.push('/tasks')">View all</button>
            </div>
            <ul class="flex-1 divide-y" style="border-color:#f9fafb;">
              <li v-for="t in (data?.my_tasks||[])" :key="t.name"
                  class="flex items-start gap-2.5 py-2.5">
                <span class="mt-0.5 h-[17px] w-[17px] shrink-0 rounded flex items-center justify-center border-2"
                      :style="t.status==='Completed'?'background:var(--portal-accent);border-color:var(--portal-accent);':'border-color:#d1d5db;background:#fff;'">
                  <FeatherIcon v-if="t.status==='Completed'" name="check" class="h-2.5 w-2.5 text-white"/>
                </span>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-[13px] font-medium leading-tight" style="color:#111827;">{{ t.subject||t.name }}</p>
                  <p class="truncate text-[11px] mt-0.5" style="color:#9ca3af;">{{ t.project }}</p>
                </div>
                <span class="shrink-0 text-[11px] font-medium" style="color:#6b7280;">{{ t.exp_end_date||"—" }}</span>
              </li>
              <li v-if="!(data?.my_tasks||[]).length"
                  class="py-6 text-center text-xs" style="color:#9ca3af;">
                No open tasks assigned to you.
              </li>
            </ul>
            <div class="mt-3 border-t pt-3" style="border-color:#f3f4f6;">
              <button class="flex items-center gap-1 text-[12px] font-medium hover:underline" style="color:var(--portal-accent);"
                      @click="router.push('/tasks')">
                <FeatherIcon name="plus-circle" class="h-3.5 w-3.5"/> Add New Task
              </button>
            </div>
          </div>
        </div>

        <!-- ── ROW 3 : Recent Docs · Cash Flow · Shortcuts ──────────────── -->
        <div class="grid gap-4 lg:grid-cols-3">

          <!-- Recent Documents -->
          <div class="rounded-xl bg-white p-5" style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-sm font-semibold" style="color:#111827;">Recent Documents</h2>
              <button class="text-[12px] font-medium hover:underline" style="color:var(--portal-accent);"
                      @click="router.push('/projects')">View all</button>
            </div>
            <ul class="divide-y" style="border-color:#f9fafb;">
              <li v-for="p in (data?.user_projects_preview||[])" :key="p.name"
                  class="flex cursor-pointer items-center gap-3 py-2.5 -mx-1 px-1 rounded-lg transition hover:bg-gray-50"
                  @click="router.push('/projects/'+encodeURIComponent(p.name))">
                <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
                     style="background:#f8fafc;border:1px solid #e5e7eb;">
                  <FeatherIcon name="file-text" class="h-3.5 w-3.5" style="color:#9ca3af;"/>
                </div>
                <p class="flex-1 min-w-0 truncate text-[13px] font-medium" style="color:#111827;">{{ p.project_name||p.name }}</p>
                <div class="flex shrink-0 flex-col items-end gap-0.5">
                  <span class="rounded px-1.5 py-0.5 text-[10px] font-medium" style="background:#f3f4f6;color:#4b5563;">Project</span>
                  <span class="text-[11px]" style="color:#9ca3af;">{{ timeAgo(p.modified) }}</span>
                </div>
              </li>
              <li v-if="!(data?.user_projects_preview||[]).length" class="py-6 text-center text-xs" style="color:#9ca3af;">
                No recent documents.
              </li>
            </ul>
          </div>

          <!-- Cash Flow (always shows chart) -->
          <div class="rounded-xl bg-white p-5" style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <div class="mb-2 flex items-center justify-between">
              <h2 class="text-sm font-semibold" style="color:#111827;">Cash Flow</h2>
              <div class="relative" @click.stop>
                <button class="flex items-center gap-1 rounded border px-2 py-1 text-[11px] transition hover:bg-gray-50"
                        style="border-color:#e5e7eb;color:#6b7280;"
                        @click="toggleMenu('cash',$event)">
                  {{ sel.cash }} <FeatherIcon name="chevron-down" class="h-3 w-3"/>
                </button>
                <div v-if="openMenu==='cash'"
                     class="absolute right-0 top-full z-50 mt-1 w-36 overflow-hidden rounded-xl border bg-white py-1 shadow-lg"
                     style="border-color:#e5e7eb;">
                  <button v-for="opt in QUARTER_OPTS" :key="opt"
                          class="w-full px-3 py-1.5 text-left text-xs transition hover:bg-gray-50"
                          :style="opt===sel.cash?'color:var(--portal-accent);font-weight:600;':'color:#374151;'"
                          @click="pickPeriod('cash',opt)">{{ opt }}</button>
                </div>
              </div>
            </div>
            <p class="text-[11px]" style="color:#6b7280;">Net Cash Flow</p>
            <p class="text-[24px] font-bold leading-tight" style="color:#111827;">{{ fmtSAR(cashFlowAmount) }}</p>
            <p class="mt-0.5 mb-2 flex items-center gap-1 text-[11px]" style="color:#16a34a;">
              <FeatherIcon name="trending-up" class="h-3.5 w-3.5"/>
              vs {{ sel.cash === "This Quarter" ? "last quarter" : sel.cash === "This Month" ? "last month" : "prior period" }}
            </p>
            <!-- SVG bar chart — always visible -->
            <svg viewBox="0 0 270 140" class="w-full" style="overflow:visible;">
              <line x1="30" x2="258" y1="18"  y2="18"  stroke="#f3f4f6" stroke-width="1"/>
              <line x1="30" x2="258" y1="44"  y2="44"  stroke="#f3f4f6" stroke-width="1"/>
              <line x1="30" x2="258" y1="70"  y2="70"  stroke="#f3f4f6" stroke-width="1"/>
              <line x1="30" x2="258" y1="108" y2="108" stroke="#e5e7eb" stroke-width="1.5"/>
              <text x="26" y="21"  text-anchor="end" font-size="8.5" fill="#9ca3af">2M</text>
              <text x="26" y="47"  text-anchor="end" font-size="8.5" fill="#9ca3af">1M</text>
              <text x="26" y="73"  text-anchor="end" font-size="8.5" fill="#9ca3af">0</text>
              <text x="26" y="113" text-anchor="end" font-size="8.5" fill="#9ca3af">-1M</text>
              <!-- Bars -->
              <template v-for="b in barData" :key="b.label">
                <rect :x="b.x" :y="b.y" :width="b.w" :height="b.h" :fill="b.color" rx="4"/>
                <text :x="b.x+b.w/2" :y="b.y-3" text-anchor="middle" font-size="8.5" font-weight="600" :fill="b.color">
                  {{ b.count }}
                </text>
                <text :x="b.x+b.w/2" y="122" text-anchor="middle" font-size="8.5" fill="#9ca3af">{{ b.label }}</text>
              </template>
            </svg>
            <div class="mt-1 border-t pt-2.5 flex justify-end" style="border-color:#f3f4f6;">
              <button class="flex items-center gap-1 text-[12px] font-medium hover:underline" style="color:var(--portal-accent);"
                      @click="router.push('/kanban')">
                View full report <FeatherIcon name="arrow-right" class="h-3.5 w-3.5"/>
              </button>
            </div>
          </div>

          <!-- Shortcuts (4×2 grid) -->
          <div class="rounded-xl bg-white p-5" style="border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <h2 class="mb-4 text-sm font-semibold" style="color:#111827;">Shortcuts</h2>
            <div class="grid grid-cols-4 gap-2">
              <button v-for="s in SHORTCUTS" :key="s.l" type="button"
                      class="group flex flex-col items-center gap-1.5 rounded-xl py-3 px-1 transition"
                      style="border:1px solid #f3f4f6;"
                      @mouseover="$event.currentTarget.style.background='var(--portal-accent-soft)';$event.currentTarget.style.borderColor='var(--portal-accent-soft)'"
                      @mouseleave="$event.currentTarget.style.background='';$event.currentTarget.style.borderColor='#f3f4f6'"
                      @click="scAction(s)">
                <span class="flex h-10 w-10 items-center justify-center rounded-xl" :style="{background:s.bg}">
                  <FeatherIcon :name="s.icon" class="h-4 w-4" :style="{color:s.ic}"/>
                </span>
                <span class="text-center text-[10px] font-medium leading-tight" style="color:#374151;">{{ s.l }}</span>
              </button>
            </div>
          </div>
        </div>

      </template>
    </div>
  </div>
</template>
