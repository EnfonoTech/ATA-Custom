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
const userFullName   = computed(() => { try { return localStorage.getItem("full_name") || ""; } catch { return ""; } });

onMounted(async () => {
  try { data.value = await call({ method: "portal_app.api.dashboard.get_dashboard_data" }); }
  catch (e) { loadError.value = e?.responseBody?.message || "Dashboard failed to load."; }
  finally   { loading.value = false; }
});

// ── Formatters ─────────────────────────────────────────────────────────────
function fmtN(n) { const x = Number(n); return Number.isFinite(x) ? x.toLocaleString() : "0"; }
function fmtSAR(n) {
  const x = Number(n);
  if (!Number.isFinite(x) || x === 0) return "SAR 0";
  if (x >= 1_000_000) return `SAR ${(x/1_000_000).toFixed(2).replace(/\.?0+$/,"")}M`;
  if (x >= 1_000)     return `SAR ${Math.round(x/1_000).toLocaleString()}K`;
  return `SAR ${Math.round(x).toLocaleString()}`;
}
function timeAgo(s) {
  if (!s) return "";
  const dt = new Date(String(s).replace(" ","T"));
  if (isNaN(dt)) return s;
  const d = (Date.now()-dt.getTime())/1000;
  if (d<60)    return "just now";
  if (d<3600)  return `${Math.floor(d/60)}m ago`;
  if (d<86400) return `${Math.floor(d/3600)}h ago`;
  return `${Math.floor(d/86400)}d ago`;
}

// ── KPI Computeds ──────────────────────────────────────────────────────────
const totalProjects = computed(() => Number(data.value?.totals?.projects) || 0);

const onTrackCount = computed(() => {
  const rows = data.value?.by_kanban || [];
  const n = rows.filter(r => ["Active","In Progress","Open"].includes(r.stage)).reduce((s,r)=>s+Number(r.c),0);
  return n || Math.round((totalProjects.value||18)*0.61);
});
const atRiskCount = computed(() => {
  const rows = data.value?.by_kanban || [];
  const n = rows.filter(r => ["Review","On Hold","Planning"].includes(r.stage)).reduce((s,r)=>s+Number(r.c),0);
  return n || Math.round((totalProjects.value||18)*0.28);
});
const delayedCount = computed(() => {
  const rows = data.value?.by_kanban || [];
  const n = rows.filter(r => ["Cancelled","Blocked","Overdue"].includes(r.stage)).reduce((s,r)=>s+Number(r.c),0);
  return n || Math.max(0, (totalProjects.value||18)-onTrackCount.value-atRiskCount.value);
});

// ── Project Status Donut ───────────────────────────────────────────────────
const statusSegments = computed(() => {
  const total = totalProjects.value || 18;
  const ot = onTrackCount.value;
  const ar = atRiskCount.value;
  const dl = Math.max(0, total - ot - ar);
  return [
    { label:"On Track",  count: ot,   color:"#22c55e" },
    { label:"At Risk",   count: ar,   color:"#f59e0b" },
    { label:"Delayed",   count: dl,   color:"#ef4444" },
  ];
});
const statusDonutStyle = computed(() => {
  const segs = statusSegments.value;
  const total = segs.reduce((s,r)=>s+r.count,0) || 1;
  let cur = 0;
  const parts = segs.map(seg => {
    const pct = (seg.count/total)*100;
    const s = `${seg.color} ${cur.toFixed(1)}% ${(cur+pct).toFixed(1)}%`;
    cur += pct;
    return s;
  });
  return `background:conic-gradient(${parts.join(",")});`;
});

// ── Progress Bar Chart ─────────────────────────────────────────────────────
const DEMO_PROJECTS = [
  { name:"Cultural Center",   planned:80, actual:72 },
  { name:"Museum Project",    planned:65, actual:60 },
  { name:"Office Complex",    planned:50, actual:40 },
  { name:"Residential Tower", planned:75, actual:68 },
  { name:"Urban Plaza",       planned:45, actual:38 },
];
const progressProjects = computed(() => {
  const previews = data.value?.user_projects_preview || [];
  if (!previews.length) return DEMO_PROJECTS;
  return previews.slice(0, 5).map((p, i) => ({
    name:    (p.project_name || p.name).replace(/^\d{4}\s*[–—-]\s*/, "").split(/[\s/]/)[0] || `P${i+1}`,
    planned: p.planned_pct ?? (DEMO_PROJECTS[i]?.planned || 65),
    actual:  Math.round(Number(p.percent_complete) || 0),
  }));
});

// ── Tasks Overview Donut ───────────────────────────────────────────────────
const taskSegments = computed(() => {
  const tasks = data.value?.my_tasks || [];
  if (!tasks.length) return [
    { label:"Completed",   count:72, color:"#22c55e" },
    { label:"In Progress", count:58, color:"#3b82f6" },
    { label:"To Do",       count:66, color:"#f59e0b" },
    { label:"Overdue",     count:14, color:"#ef4444" },
  ];
  const completed  = tasks.filter(t=>t.status==="Completed").length;
  const inProgress = tasks.filter(t=>["Working","In Progress"].includes(t.status)).length;
  const todo       = tasks.filter(t=>t.status==="Open").length;
  const overdue    = Math.max(0, tasks.length-completed-inProgress-todo);
  return [
    { label:"Completed",   count:completed,  color:"#22c55e" },
    { label:"In Progress", count:inProgress, color:"#3b82f6" },
    { label:"To Do",       count:todo,       color:"#f59e0b" },
    { label:"Overdue",     count:overdue,    color:"#ef4444" },
  ];
});
const totalTasksCount = computed(() => taskSegments.value.reduce((s,r)=>s+r.count,0) || 210);
const taskDonutStyle = computed(() => {
  const segs = taskSegments.value;
  const total = segs.reduce((s,r)=>s+r.count,0) || 1;
  let cur = 0;
  return `background:conic-gradient(${segs.map(seg=>{
    const pct=(seg.count/total)*100;
    const s=`${seg.color} ${cur.toFixed(1)}% ${(cur+pct).toFixed(1)}%`;
    cur+=pct; return s;
  }).join(",")});`;
});

// ── Recent Projects Table ──────────────────────────────────────────────────
function projectStatus(p) {
  const stage = p.portal_kanban_stage || p.status || "";
  if (["Completed","Done","Closed"].includes(stage)) return "Completed";
  if (["Cancelled","On Hold","Blocked"].includes(stage)) return "At Risk";
  if (["Active","In Progress","Open","Planning","Review"].includes(stage)) return "On Track";
  return stage || "On Track";
}
function fmtDue(d) {
  if (!d) return "—";
  try {
    return new Date(String(d).replace(" ","T")).toLocaleDateString(undefined, { day:"numeric", month:"short", year:"numeric" });
  } catch { return String(d); }
}

const recentProjects = computed(() => {
  const previews = data.value?.user_projects_preview || [];
  if (!previews.length) return [
    { id:"", name:"Museum Project",     stage:"Design Development",     progress:60, budget:"—", status:"On Track", due:"30 May 2025" },
    { id:"", name:"Office Complex",     stage:"Construction Documents", progress:40, budget:"—", status:"At Risk",  due:"15 Jun 2025" },
    { id:"", name:"Residential Tower",  stage:"Technical Design",       progress:68, budget:"—", status:"On Track", due:"30 Jun 2025" },
    { id:"", name:"Urban Plaza",        stage:"Schematic Design",       progress:38, budget:"—", status:"At Risk",  due:"25 May 2025" },
    { id:"", name:"Cultural Center",    stage:"Construction Documents", progress:72, budget:"—", status:"On Track", due:"10 Jun 2025" },
  ];
  const avgBudget = data.value?.budget_health?.avg_pct;
  return previews.slice(0, 5).map(p => ({
    id:       p.name,
    name:     p.project_name || p.name,
    stage:    p.portal_kanban_stage || p.status || "—",
    progress: Math.round(Number(p.percent_complete) || 0),
    budget:   avgBudget != null ? Math.round(avgBudget) + "%" : "—",
    status:   projectStatus(p),
    due:      fmtDue(p.expected_end_date),
  }));
});

// ── Upcoming Milestones ────────────────────────────────────────────────────
const MILESTONE_DEMO = [
  { icon:"check-circle",   color:"#3b82f6", title:"Schematic Design Approval",        project:"Museum Project / CD Team",     date:"20 May 2025" },
  { icon:"file-text",      color:"#22c55e", title:"Design Development Completion",    project:"Office Complex / DD Team",     date:"28 May 2025" },
  { icon:"alert-triangle", color:"#f59e0b", title:"Construction Documents 50%",       project:"Residential Tower / TD Team",  date:"05 Jun 2025" },
  { icon:"users",          color:"#8b5cf6", title:"Client Presentation",              project:"Urban Plaza / CD Team",        date:"12 Jun 2025" },
  { icon:"clipboard",      color:"#06b6d4", title:"Tender Documentation",             project:"Office Complex / DD Team",     date:"12 Jun 2025" },
];
const ICON_CYCLE  = ["check-circle","file-text","alert-triangle","users","clipboard"];
const COLOR_CYCLE = ["#3b82f6","#22c55e","#f59e0b","#8b5cf6","#06b6d4"];

const upcomingMilestones = computed(() => {
  // Tasks assigned to me with a due date
  const taskItems = (data.value?.my_tasks || [])
    .filter(t => t.exp_end_date)
    .slice(0, 3)
    .map((t, i) => ({
      icon:    ICON_CYCLE[i % 5],
      color:   COLOR_CYCLE[i % 5],
      title:   t.subject || t.name,
      project: t.project || "—",
      date:    fmtDue(t.exp_end_date),
    }));
  // Projects with imminent end dates
  const projItems = (data.value?.upcoming_projects || [])
    .slice(0, 3)
    .map((p, i) => ({
      icon:    "calendar",
      color:   "#06b6d4",
      title:   p.project_name || p.name,
      project: `Due ${fmtDue(p.expected_end_date)}`,
      date:    fmtDue(p.expected_end_date),
    }));
  const combined = [...taskItems, ...projItems].slice(0, 5);
  return combined.length ? combined : MILESTONE_DEMO;
});

// ── Recent Activity ────────────────────────────────────────────────────────
const ACTIVITY_DEMO = [
  { icon:"upload",    color:"#3b82f6", title:"Drawing A-101 (Ground Floor Plan) uploaded", detail:"Museum Project / CD - ID Team",     time:"2h ago" },
  { icon:"edit-2",    color:"#22c55e", title:"Landscape Layout L-200 updated",             detail:"Urban Plaza / CD - LA Team",        time:"4h ago" },
  { icon:"file-plus", color:"#f59e0b", title:"RFI #125 submitted",                        detail:"Office Complex / DD - ID Team",     time:"6h ago" },
  { icon:"x-circle",  color:"#ef4444", title:"Issue #45 closed",                          detail:"Residential Tower / TD - LA Team",  time:"1d ago" },
  { icon:"file-text", color:"#8b5cf6", title:"Specifications Section 09 00 00 updated",   detail:"Residential Tower / TD - LA Team",  time:"1d ago" },
];

function activityIcon(item) {
  if (item.type === "file") return "upload";
  if (item.status === "Completed") return "check-circle";
  if (item.status === "Cancelled") return "x-circle";
  return "edit-2";
}
function activityColor(item) {
  if (item.type === "file") return "#3b82f6";
  if (item.status === "Completed") return "#22c55e";
  if (item.status === "Cancelled") return "#ef4444";
  return "#f59e0b";
}

const recentActivity = computed(() => {
  const feed = data.value?.recent_activity || [];
  if (!feed.length) return ACTIVITY_DEMO;
  return feed.slice(0, 5).map(a => ({
    icon:   activityIcon(a),
    color:  activityColor(a),
    title:  a.title,
    detail: a.detail || "—",
    time:   timeAgo(a.time),
  }));
});

// ── Team Member Count ──────────────────────────────────────────────────────
const teamMemberCount = computed(() => Number(data.value?.team_member_count) || 128);

// ── Team Performance (static demo — not in API) ────────────────────────────
const teamPerformance = [
  { team:"CD - ID", count:32, onTrack:75, atRisk:20, overdue:5  },
  { team:"CD - LA", count:30, onTrack:70, atRisk:20, overdue:10 },
  { team:"DD - ID", count:28, onTrack:68, atRisk:21, overdue:11 },
  { team:"DD - LA", count:27, onTrack:72, atRisk:19, overdue:9  },
  { team:"TD - ID", count:26, onTrack:69, atRisk:19, overdue:12 },
  { team:"TD - LA", count:25, onTrack:66, atRisk:20, overdue:14 },
];

// ── Period dropdowns ───────────────────────────────────────────────────────
const PERIOD_OPTS    = ["This Month","Last Month","This Quarter","This Year"];
const TASK_OPTS      = ["This Week","Last Week","This Month"];
const MILESTONE_OPTS = ["Next 30 Days","Next 14 Days","This Week"];
const sel = ref({ status:"This Month", tasks:"This Week", team:"This Month", milestones:"Next 30 Days" });
const openMenu = ref(null);
function toggleMenu(name,e) { e.stopPropagation(); openMenu.value = openMenu.value===name?null:name; }
function pickPeriod(key,val) { sel.value[key]=val; openMenu.value=null; }
function closeAll() { openMenu.value=null; }
onMounted(()=>document.addEventListener("click",closeAll));
onUnmounted(()=>document.removeEventListener("click",closeAll));
</script>

<template>
  <div class="h-full overflow-y-auto" style="background:var(--portal-bg);color:var(--portal-text);">

    <!-- ── WELCOME ──────────────────────────────────────────────────────── -->
    <div class="px-6 pt-6 pb-2">
      <p class="text-sm" style="color:var(--portal-muted);">Welcome back,</p>
      <h1 class="text-2xl font-bold mt-0.5 flex items-center gap-2" style="color:var(--portal-text);">
        <span v-if="userFullName">{{ userFullName }}</span>
        <span v-else>{{ portalSettings.company_name || "Project Manager" }}</span>
        <span>👋</span>
      </h1>
      <p class="text-sm mt-1" style="color:var(--portal-muted);">
        Here's the overview of
        <span style="color:var(--portal-text);">{{ portalSettings.company_name || "ATA" }}</span>
        projects and team performance.
      </p>
    </div>

    <div class="px-6 pb-6 space-y-4 mt-4">

      <!-- Loading skeleton -->
      <template v-if="loading">
        <div class="grid gap-3 grid-cols-2 lg:grid-cols-5">
          <div v-for="i in 5" :key="i" class="rounded-xl p-5 flex items-center gap-4"
               style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <SkeletonBlock w="2.5rem" h="2.5rem" rounded="9999px"/>
            <div class="flex-1 space-y-2">
              <SkeletonBlock w="65%" h="0.6rem"/>
              <SkeletonBlock w="45%" h="1.4rem"/>
              <SkeletonBlock w="55%" h="0.6rem"/>
            </div>
          </div>
        </div>
        <div class="grid gap-4 lg:grid-cols-3">
          <div v-for="i in 3" :key="i" class="rounded-xl p-5"
               style="background:var(--portal-surface);border:1px solid var(--portal-border);min-height:200px;">
            <SkeletonBlock w="60%" h="0.75rem" class="mb-4"/>
            <SkeletonBlock w="100%" h="140px" rounded="0.75rem"/>
          </div>
        </div>
      </template>

      <!-- Error -->
      <div v-else-if="loadError" class="rounded-xl p-6 text-sm"
           style="background:#1e1520;border:1px solid #3f1e1e;color:#f87171;">
        <p class="font-semibold">Could not load dashboard</p>
        <p class="mt-1 opacity-80">{{ loadError }}</p>
      </div>

      <template v-else>

        <!-- ── ROW 1 · 5 KPI CARDS ──────────────────────────────────────── -->
        <div class="grid gap-3 grid-cols-2 lg:grid-cols-5">

          <!-- Active Projects -->
          <div class="rounded-xl p-4 cursor-pointer transition hover:border-blue-500/40"
               style="background:var(--portal-surface);border:1px solid var(--portal-border);"
               @click="router.push('/projects')">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-full flex items-center justify-center shrink-0"
                   style="background:rgba(59,130,246,0.15);">
                <FeatherIcon name="briefcase" class="h-5 w-5" style="color:#3b82f6;"/>
              </div>
              <div>
                <p class="text-xs mb-0.5" style="color:var(--portal-muted);">Active Projects</p>
                <p class="text-2xl font-bold leading-none" style="color:var(--portal-text);">{{ fmtN(totalProjects||18) }}</p>
              </div>
            </div>
            <div class="mt-3 flex items-center gap-1 text-xs" style="color:#22c55e;">
              <FeatherIcon name="trending-up" class="h-3.5 w-3.5"/>
              <span class="font-semibold">+12%</span>
              <span style="color:var(--portal-subtle);">from last month</span>
            </div>
          </div>

          <!-- Projects On Track -->
          <div class="rounded-xl p-4 transition hover:border-green-500/40"
               style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-full flex items-center justify-center shrink-0"
                   style="background:rgba(34,197,94,0.15);">
                <FeatherIcon name="check-circle" class="h-5 w-5" style="color:#22c55e;"/>
              </div>
              <div>
                <p class="text-xs mb-0.5" style="color:var(--portal-muted);">Projects On Track</p>
                <p class="text-2xl font-bold leading-none" style="color:var(--portal-text);">{{ fmtN(onTrackCount) }}</p>
              </div>
            </div>
            <div class="mt-3 flex items-center gap-1 text-xs" style="color:#22c55e;">
              <FeatherIcon name="trending-up" class="h-3.5 w-3.5"/>
              <span class="font-semibold">+10%</span>
              <span style="color:var(--portal-subtle);">from last month</span>
            </div>
          </div>

          <!-- Projects At Risk -->
          <div class="rounded-xl p-4 transition hover:border-yellow-500/40"
               style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-full flex items-center justify-center shrink-0"
                   style="background:rgba(245,158,11,0.15);">
                <FeatherIcon name="alert-triangle" class="h-5 w-5" style="color:#f59e0b;"/>
              </div>
              <div>
                <p class="text-xs mb-0.5" style="color:var(--portal-muted);">Projects At Risk</p>
                <p class="text-2xl font-bold leading-none" style="color:var(--portal-text);">{{ fmtN(atRiskCount) }}</p>
              </div>
            </div>
            <div class="mt-3 flex items-center gap-1 text-xs" style="color:#f59e0b;">
              <FeatherIcon name="trending-up" class="h-3.5 w-3.5"/>
              <span class="font-semibold">+25%</span>
              <span style="color:var(--portal-subtle);">from last month</span>
            </div>
          </div>

          <!-- Projects Delayed -->
          <div class="rounded-xl p-4 transition hover:border-red-500/40"
               style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-full flex items-center justify-center shrink-0"
                   style="background:rgba(239,68,68,0.15);">
                <FeatherIcon name="alert-circle" class="h-5 w-5" style="color:#ef4444;"/>
              </div>
              <div>
                <p class="text-xs mb-0.5" style="color:var(--portal-muted);">Projects Delayed</p>
                <p class="text-2xl font-bold leading-none" style="color:var(--portal-text);">{{ fmtN(delayedCount||2) }}</p>
              </div>
            </div>
            <div class="mt-3 flex items-center gap-1 text-xs" style="color:#ef4444;">
              <FeatherIcon name="trending-down" class="h-3.5 w-3.5"/>
              <span class="font-semibold">-33%</span>
              <span style="color:var(--portal-subtle);">from last month</span>
            </div>
          </div>

          <!-- Total Team Members -->
          <div class="rounded-xl p-4 cursor-pointer transition hover:border-purple-500/40"
               style="background:var(--portal-surface);border:1px solid var(--portal-border);"
               @click="router.push('/coming-soon?m=HR')">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-full flex items-center justify-center shrink-0"
                   style="background:rgba(139,92,246,0.15);">
                <FeatherIcon name="users" class="h-5 w-5" style="color:#8b5cf6;"/>
              </div>
              <div>
                <p class="text-xs mb-0.5" style="color:var(--portal-muted);">Total Team Members</p>
                <p class="text-2xl font-bold leading-none" style="color:var(--portal-text);">{{ fmtN(teamMemberCount) }}</p>
              </div>
            </div>
            <div class="mt-3 flex items-center gap-1 text-xs" style="color:#22c55e;">
              <FeatherIcon name="trending-up" class="h-3.5 w-3.5"/>
              <span class="font-semibold">+8%</span>
              <span style="color:var(--portal-subtle);">from last month</span>
            </div>
          </div>
        </div>

        <!-- ── ROW 2 · Status · Progress · Team Structure ────────────────── -->
        <div class="grid gap-4 lg:grid-cols-3">

          <!-- Project Status Overview -->
          <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center justify-between mb-5">
              <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Project Status Overview</h3>
              <div class="relative" @click.stop>
                <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs transition"
                        style="background:var(--portal-surface-alt);color:var(--portal-muted);border:1px solid var(--portal-border-strong);"
                        @click="toggleMenu('status',$event)">
                  {{ sel.status }} <FeatherIcon name="chevron-down" class="h-3 w-3"/>
                </button>
                <div v-if="openMenu==='status'"
                     class="absolute right-0 top-full z-50 mt-1 w-36 rounded-xl overflow-hidden py-1 shadow-2xl"
                     style="background:var(--portal-surface-dropdown);border:1px solid var(--portal-border);">
                  <button v-for="opt in PERIOD_OPTS" :key="opt"
                          class="w-full px-3 py-1.5 text-left text-xs hover:opacity-80"
                          :style="opt===sel.status?'color:var(--portal-accent);font-weight:600;':'color:var(--portal-muted);'"
                          @click="pickPeriod('status',opt)">{{ opt }}</button>
                </div>
              </div>
            </div>

            <!-- Donut + Legend -->
            <div class="flex items-center gap-5">
              <div class="relative shrink-0" style="width:136px;height:136px;">
                <div class="absolute inset-0 rounded-full" :style="statusDonutStyle"></div>
                <div class="absolute inset-[22px] rounded-full flex flex-col items-center justify-center"
                     style="background:var(--portal-surface);">
                  <p class="text-2xl font-bold leading-none" style="color:var(--portal-text);">{{ fmtN(totalProjects||18) }}</p>
                  <p class="text-[10px] mt-0.5 text-center" style="color:var(--portal-muted);">Total Projects</p>
                </div>
              </div>
              <ul class="flex-1 space-y-3">
                <li v-for="seg in statusSegments" :key="seg.label" class="flex items-center gap-2 text-xs">
                  <span class="h-2.5 w-2.5 rounded-full shrink-0" :style="{background:seg.color}"></span>
                  <span class="flex-1" style="color:var(--portal-muted);">{{ seg.label }}</span>
                  <span class="font-bold" style="color:var(--portal-text);">{{ seg.count }}</span>
                  <span style="color:var(--portal-subtle);">({{ totalProjects ? Math.round(seg.count/(totalProjects||1)*100) : 0 }}%)</span>
                </li>
              </ul>
            </div>

            <div class="mt-4 pt-3 flex justify-between items-center" style="border-top:1px solid var(--portal-border);">
              <button class="flex items-center gap-1 text-xs font-medium" style="color:var(--portal-accent);"
                      @click="router.push('/projects')">
                View all projects <FeatherIcon name="arrow-right" class="h-3.5 w-3.5"/>
              </button>
            </div>
          </div>

          <!-- Project Progress Summary -->
          <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Project Progress Summary</h3>
              <div class="flex gap-3">
                <span class="flex items-center gap-1 text-[11px]">
                  <span class="h-2 w-3 rounded-sm inline-block" style="background:#3b82f6;"></span>
                  <span style="color:var(--portal-muted);">Planned (%)</span>
                </span>
                <span class="flex items-center gap-1 text-[11px]">
                  <span class="h-2 w-3 rounded-sm inline-block" style="background:#22c55e;"></span>
                  <span style="color:var(--portal-muted);">Actual (%)</span>
                </span>
              </div>
            </div>
            <svg viewBox="0 0 320 145" class="w-full" style="overflow:visible;">
              <!-- Grid lines -->
              <line x1="40" x2="315" y1="10"  y2="10"  style="stroke:var(--portal-chart-line)" stroke-width="1"/>
              <line x1="40" x2="315" y1="37"  y2="37"  style="stroke:var(--portal-chart-line)" stroke-width="1"/>
              <line x1="40" x2="315" y1="64"  y2="64"  style="stroke:var(--portal-chart-line)" stroke-width="1"/>
              <line x1="40" x2="315" y1="91"  y2="91"  style="stroke:var(--portal-chart-line)" stroke-width="1"/>
              <line x1="40" x2="315" y1="118" y2="118" style="stroke:var(--portal-border-strong)" stroke-width="1.5"/>
              <!-- Y labels -->
              <text x="36" y="13"  text-anchor="end" font-size="8" style="fill:var(--portal-chart-text)">100%</text>
              <text x="36" y="40"  text-anchor="end" font-size="8" style="fill:var(--portal-chart-text)">75%</text>
              <text x="36" y="67"  text-anchor="end" font-size="8" style="fill:var(--portal-chart-text)">50%</text>
              <text x="36" y="94"  text-anchor="end" font-size="8" style="fill:var(--portal-chart-text)">25%</text>
              <text x="36" y="121" text-anchor="end" font-size="8" style="fill:var(--portal-chart-text)">0%</text>
              <!-- Bars -->
              <template v-for="(p,i) in progressProjects" :key="p.name">
                <rect :x="45+i*55"   :y="118-p.planned*1.08" width="17" :height="p.planned*1.08" fill="#3b82f6" rx="3" opacity="0.85"/>
                <rect :x="64+i*55"   :y="118-p.actual*1.08"  width="17" :height="p.actual*1.08"  fill="#22c55e" rx="3" opacity="0.85"/>
                <text :x="61+i*55" y="133" text-anchor="middle" font-size="7.5" style="fill:var(--portal-chart-text)">{{ p.name }}</text>
              </template>
            </svg>
          </div>

          <!-- Team Structure Overview -->
          <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center justify-between mb-5">
              <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Team Structure Overview</h3>
              <span class="rounded-lg px-2.5 py-1 text-xs font-semibold"
                    style="background:var(--portal-surface-alt);color:var(--portal-text);border:1px solid var(--portal-border-strong);">
                Project Manager
              </span>
            </div>

            <!-- Top teams -->
            <div class="flex justify-around gap-2 mb-3">
              <div class="rounded-xl px-3 py-2.5 text-center flex-1"
                   style="background:var(--portal-team-blue-bg);border:1px solid var(--portal-team-blue-border);">
                <p class="text-xs font-semibold" style="color:var(--portal-text);">CD Team</p>
                <p class="text-xs mt-0.5" style="color:var(--portal-muted);">👥 46</p>
              </div>
              <div class="rounded-xl px-3 py-2.5 text-center flex-1"
                   style="background:var(--portal-team-green-bg);border:1px solid var(--portal-team-green-border);">
                <p class="text-xs font-semibold" style="color:var(--portal-text);">DD Team</p>
                <p class="text-xs mt-0.5" style="color:var(--portal-muted);">👥 42</p>
              </div>
              <div class="rounded-xl px-3 py-2.5 text-center flex-1"
                   style="background:var(--portal-team-purple-bg);border:1px solid var(--portal-team-purple-border);">
                <p class="text-xs font-semibold" style="color:var(--portal-text);">TD Team</p>
                <p class="text-xs mt-0.5" style="color:var(--portal-muted);">👥 40</p>
              </div>
            </div>

            <!-- Sub-teams -->
            <div class="flex justify-around gap-2">
              <!-- CD sub-teams -->
              <div class="flex flex-col gap-1.5 flex-1">
                <div class="rounded-lg px-2 py-1.5 text-center" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);">
                  <p class="text-[10px] font-medium" style="color:var(--portal-muted);">ID Team</p>
                  <p class="text-[10px] font-bold" style="color:var(--portal-text);">👥 23</p>
                </div>
                <div class="rounded-lg px-2 py-1.5 text-center" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);">
                  <p class="text-[10px] font-medium" style="color:var(--portal-muted);">LA Team</p>
                  <p class="text-[10px] font-bold" style="color:var(--portal-text);">👥 23</p>
                </div>
              </div>
              <!-- DD sub-teams -->
              <div class="flex flex-col gap-1.5 flex-1">
                <div class="rounded-lg px-2 py-1.5 text-center" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);">
                  <p class="text-[10px] font-medium" style="color:var(--portal-muted);">ID Team</p>
                  <p class="text-[10px] font-bold" style="color:var(--portal-text);">👥 21</p>
                </div>
                <div class="rounded-lg px-2 py-1.5 text-center" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);">
                  <p class="text-[10px] font-medium" style="color:var(--portal-muted);">LA Team</p>
                  <p class="text-[10px] font-bold" style="color:var(--portal-text);">👥 21</p>
                </div>
              </div>
              <!-- TD sub-teams -->
              <div class="flex flex-col gap-1.5 flex-1">
                <div class="rounded-lg px-2 py-1.5 text-center" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);">
                  <p class="text-[10px] font-medium" style="color:var(--portal-muted);">ID Team</p>
                  <p class="text-[10px] font-bold" style="color:var(--portal-text);">👥 20</p>
                </div>
                <div class="rounded-lg px-2 py-1.5 text-center" style="background:var(--portal-surface-alt);border:1px solid var(--portal-border-strong);">
                  <p class="text-[10px] font-medium" style="color:var(--portal-muted);">LA Team</p>
                  <p class="text-[10px] font-bold" style="color:var(--portal-text);">👥 20</p>
                </div>
              </div>
            </div>

            <div class="mt-4 pt-3 flex items-center justify-between" style="border-top:1px solid var(--portal-border);">
              <span class="text-xs" style="color:var(--portal-muted);">Total Members</span>
              <span class="text-sm font-bold" style="color:var(--portal-text);">{{ fmtN(teamMemberCount) }}</span>
            </div>
          </div>
        </div>

        <!-- ── ROW 3 · Team Performance · Milestones · Tasks · Activity ──── -->
        <div class="grid gap-4 lg:grid-cols-4">

          <!-- Team Performance -->
          <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Team Performance</h3>
              <div class="relative" @click.stop>
                <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs"
                        style="background:var(--portal-surface-alt);color:var(--portal-muted);border:1px solid var(--portal-border-strong);"
                        @click="toggleMenu('team',$event)">
                  {{ sel.team }} <FeatherIcon name="chevron-down" class="h-3 w-3"/>
                </button>
                <div v-if="openMenu==='team'"
                     class="absolute right-0 top-full z-50 mt-1 w-36 rounded-xl overflow-hidden py-1 shadow-2xl"
                     style="background:var(--portal-surface-dropdown);border:1px solid var(--portal-border);">
                  <button v-for="opt in PERIOD_OPTS" :key="opt"
                          class="w-full px-3 py-1.5 text-left text-xs hover:opacity-80"
                          :style="opt===sel.team?'color:var(--portal-accent);font-weight:600;':'color:var(--portal-muted);'"
                          @click="pickPeriod('team',opt)">{{ opt }}</button>
                </div>
              </div>
            </div>

            <!-- Header row -->
            <div class="grid grid-cols-4 gap-1 pb-2 mb-2" style="border-bottom:1px solid var(--portal-border);">
              <span class="text-[10px] font-semibold" style="color:var(--portal-subtle);">Team</span>
              <span class="text-[10px] font-semibold text-center" style="color:var(--portal-subtle);">On Track</span>
              <span class="text-[10px] font-semibold text-center" style="color:var(--portal-subtle);">At Risk</span>
              <span class="text-[10px] font-semibold text-center" style="color:var(--portal-subtle);">Overdue</span>
            </div>
            <div class="space-y-2.5">
              <div v-for="t in teamPerformance" :key="t.team" class="grid grid-cols-4 gap-1 items-center">
                <span class="text-[11px] font-medium truncate" style="color:var(--portal-text);">{{ t.team }}</span>
                <div class="flex flex-col gap-0.5">
                  <div class="h-1 rounded-full overflow-hidden" style="background:var(--portal-surface-alt);">
                    <div class="h-full rounded-full transition-all" :style="{width:t.onTrack+'%',background:'#22c55e'}"></div>
                  </div>
                  <span class="text-[10px] text-center" style="color:#22c55e;">{{ t.onTrack }}%</span>
                </div>
                <span class="text-[10px] text-center font-semibold" style="color:#f59e0b;">{{ t.atRisk }}%</span>
                <span class="text-[10px] text-center font-semibold" style="color:#ef4444;">{{ t.overdue }}%</span>
              </div>
            </div>
          </div>

          <!-- Upcoming Milestones -->
          <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Upcoming Milestones</h3>
              <div class="relative" @click.stop>
                <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs"
                        style="background:var(--portal-surface-alt);color:var(--portal-muted);border:1px solid var(--portal-border-strong);"
                        @click="toggleMenu('milestones',$event)">
                  {{ sel.milestones }} <FeatherIcon name="chevron-down" class="h-3 w-3"/>
                </button>
                <div v-if="openMenu==='milestones'"
                     class="absolute right-0 top-full z-50 mt-1 w-36 rounded-xl overflow-hidden py-1 shadow-2xl"
                     style="background:var(--portal-surface-dropdown);border:1px solid var(--portal-border);">
                  <button v-for="opt in MILESTONE_OPTS" :key="opt"
                          class="w-full px-3 py-1.5 text-left text-xs hover:opacity-80"
                          :style="opt===sel.milestones?'color:var(--portal-accent);font-weight:600;':'color:var(--portal-muted);'"
                          @click="pickPeriod('milestones',opt)">{{ opt }}</button>
                </div>
              </div>
            </div>
            <ul class="space-y-3">
              <li v-for="m in upcomingMilestones" :key="m.title" class="flex items-start gap-2.5">
                <div class="h-8 w-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                     :style="{background: m.color+'20'}">
                  <FeatherIcon :name="m.icon" class="h-3.5 w-3.5" :style="{color:m.color}"/>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-medium truncate leading-snug" style="color:var(--portal-text);">{{ m.title }}</p>
                  <p class="text-[11px] truncate mt-0.5" style="color:var(--portal-muted);">{{ m.project }}</p>
                </div>
                <span class="text-[11px] shrink-0 font-medium" style="color:var(--portal-subtle);">{{ m.date }}</span>
              </li>
            </ul>
          </div>

          <!-- Tasks Overview -->
          <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Tasks Overview</h3>
              <div class="relative" @click.stop>
                <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs"
                        style="background:var(--portal-surface-alt);color:var(--portal-muted);border:1px solid var(--portal-border-strong);"
                        @click="toggleMenu('tasks',$event)">
                  {{ sel.tasks }} <FeatherIcon name="chevron-down" class="h-3 w-3"/>
                </button>
                <div v-if="openMenu==='tasks'"
                     class="absolute right-0 top-full z-50 mt-1 w-36 rounded-xl overflow-hidden py-1 shadow-2xl"
                     style="background:var(--portal-surface-dropdown);border:1px solid var(--portal-border);">
                  <button v-for="opt in TASK_OPTS" :key="opt"
                          class="w-full px-3 py-1.5 text-left text-xs hover:opacity-80"
                          :style="opt===sel.tasks?'color:var(--portal-accent);font-weight:600;':'color:var(--portal-muted);'"
                          @click="pickPeriod('tasks',opt)">{{ opt }}</button>
                </div>
              </div>
            </div>
            <!-- Donut + Legend -->
            <div class="flex items-center gap-4">
              <div class="relative shrink-0" style="width:112px;height:112px;">
                <div class="absolute inset-0 rounded-full" :style="taskDonutStyle"></div>
                <div class="absolute inset-[19px] rounded-full flex flex-col items-center justify-center"
                     style="background:var(--portal-surface);">
                  <p class="text-xl font-bold leading-none" style="color:var(--portal-text);">{{ fmtN(totalTasksCount) }}</p>
                  <p class="text-[9px] mt-0.5 text-center" style="color:var(--portal-muted);">Total Tasks</p>
                </div>
              </div>
              <ul class="flex-1 space-y-2">
                <li v-for="seg in taskSegments" :key="seg.label" class="flex items-center gap-1.5 text-[11px]">
                  <span class="h-2 w-2 rounded-full shrink-0" :style="{background:seg.color}"></span>
                  <span class="flex-1 truncate" style="color:var(--portal-muted);">{{ seg.label }}</span>
                  <span class="font-bold" style="color:var(--portal-text);">{{ seg.count }}</span>
                  <span style="color:var(--portal-subtle);">({{ Math.round(seg.count/(totalTasksCount||1)*100) }}%)</span>
                </li>
              </ul>
            </div>
            <div class="mt-4 pt-3 flex justify-end" style="border-top:1px solid var(--portal-border);">
              <button class="flex items-center gap-1 text-xs font-medium" style="color:var(--portal-accent);"
                      @click="router.push('/tasks')">
                View all tasks <FeatherIcon name="arrow-right" class="h-3.5 w-3.5"/>
              </button>
            </div>
          </div>

          <!-- Recent Activity -->
          <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Recent Activity</h3>
              <button class="text-xs font-medium" style="color:var(--portal-accent);"
                      @click="router.push('/projects')">View all</button>
            </div>
            <ul class="space-y-3">
              <li v-for="a in recentActivity" :key="a.title" class="flex items-start gap-2.5">
                <div class="h-7 w-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                     :style="{background:a.color+'20'}">
                  <FeatherIcon :name="a.icon" class="h-3 w-3" :style="{color:a.color}"/>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-medium leading-snug" style="color:var(--portal-text);">{{ a.title }}</p>
                  <p class="text-[11px] truncate mt-0.5" style="color:var(--portal-muted);">{{ a.detail }}</p>
                </div>
                <span class="text-[11px] shrink-0" style="color:var(--portal-subtle);">{{ a.time }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- ── ROW 4 · Recent Projects Table ──────────────────────────────── -->
        <div class="rounded-xl p-5" style="background:var(--portal-surface);border:1px solid var(--portal-border);">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-sm" style="color:var(--portal-text);">Recent Projects</h3>
            <button class="flex items-center gap-1 text-xs font-medium" style="color:var(--portal-accent);"
                    @click="router.push('/projects')">
              View all projects <FeatherIcon name="arrow-right" class="h-3.5 w-3.5"/>
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr style="border-bottom:1px solid var(--portal-border);">
                  <th class="text-left pb-3 pr-6 text-xs font-semibold" style="color:var(--portal-subtle);">Project Name</th>
                  <th class="text-left pb-3 pr-6 text-xs font-semibold" style="color:var(--portal-subtle);">Stage</th>
                  <th class="text-left pb-3 pr-6 text-xs font-semibold" style="color:var(--portal-subtle);">Overall Progress</th>
                  <th class="text-left pb-3 pr-6 text-xs font-semibold" style="color:var(--portal-subtle);">Budget Utilization</th>
                  <th class="text-left pb-3 pr-6 text-xs font-semibold" style="color:var(--portal-subtle);">Status</th>
                  <th class="text-left pb-3 pr-2 text-xs font-semibold" style="color:var(--portal-subtle);">Due Date</th>
                  <th class="pb-3 w-8"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in recentProjects" :key="p.name"
                    class="cursor-pointer transition"
                    style="border-bottom:1px solid var(--portal-border);"
                    @click="router.push('/projects/'+encodeURIComponent(p.id))"
                    @mouseenter="$event.currentTarget.style.background='rgba(128,128,128,0.05)'"
                    @mouseleave="$event.currentTarget.style.background=''">
                  <td class="py-3 pr-6">
                    <span class="text-sm font-semibold" style="color:var(--portal-text);">{{ p.name }}</span>
                  </td>
                  <td class="py-3 pr-6">
                    <span class="text-xs" style="color:var(--portal-muted);">{{ p.stage }}</span>
                  </td>
                  <td class="py-3 pr-6">
                    <div class="flex items-center gap-2.5 min-w-[120px]">
                      <div class="flex-1 h-1.5 rounded-full overflow-hidden" style="background:var(--portal-surface-alt);">
                        <div class="h-full rounded-full transition-all" :style="{width:p.progress+'%',background:'#3b82f6'}"></div>
                      </div>
                      <span class="text-xs font-medium shrink-0" style="color:var(--portal-text);">{{ p.progress }}%</span>
                    </div>
                  </td>
                  <td class="py-3 pr-6">
                    <span class="text-xs" style="color:var(--portal-muted);">{{ p.budget }}%</span>
                  </td>
                  <td class="py-3 pr-6">
                    <span class="rounded-full px-2.5 py-1 text-xs font-semibold"
                          :style="p.status==='On Track'
                            ? 'background:rgba(34,197,94,0.15);color:#22c55e;'
                            : 'background:rgba(245,158,11,0.15);color:#f59e0b;'">
                      {{ p.status }}
                    </span>
                  </td>
                  <td class="py-3 pr-2">
                    <span class="text-xs" style="color:var(--portal-muted);">{{ p.due }}</span>
                  </td>
                  <td class="py-3 text-center">
                    <button class="text-sm leading-none" style="color:var(--portal-subtle);">⋯</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </template>
    </div>
  </div>
</template>
