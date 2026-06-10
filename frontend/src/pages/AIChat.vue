<script setup>
import { ref, computed, nextTick, onMounted } from "vue";
import { call } from "@/api";
import { FeatherIcon } from "frappe-ui";

// ── State ────────────────────────────────────────────────────────────────────
const messages  = ref([]);
const input     = ref("");
const busy      = ref(false);
const scrollEl  = ref(null);
const inputEl   = ref(null);
const showSugg  = ref(true);

const SUGGESTIONS = [
  { icon: "layers",      text: "How many active projects are there?" },
  { icon: "upload-cloud",text: "Show files uploaded this week" },
  { icon: "check-square",text: "How many tasks are open?" },
  { icon: "bar-chart-2", text: "Give me a summary of all projects" },
  { icon: "search",      text: "Find projects with Tower in the name" },
  { icon: "file-text",   text: "How many files are in the system?" },
];

// ── Boot message ─────────────────────────────────────────────────────────────
onMounted(() => {
  messages.value.push({
    role: "ai",
    text: "Hello! I'm **ATA AI**, your intelligent project assistant. I can answer questions about your projects, files, tasks, and team activity.\n\nWhat would you like to know?",
    type: "text",
    ts: now(),
  });
  nextTick(() => focusInput());
});

// ── Helpers ──────────────────────────────────────────────────────────────────
function now() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function focusInput() {
  inputEl.value?.focus();
}

async function scrollBottom() {
  await nextTick();
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight;
}

// ── Send ─────────────────────────────────────────────────────────────────────
async function send(text) {
  const q = (text || input.value || "").trim();
  if (!q || busy.value) return;
  input.value = "";
  showSugg.value = false;

  messages.value.push({ role: "user", text: q, ts: now() });
  scrollBottom();

  busy.value = true;
  messages.value.push({ role: "ai", text: null, ts: now(), typing: true });
  scrollBottom();

  try {
    const res = await call({ method: "portal_app.api.ai_chat.ask", args: { question: q } });
    messages.value.pop(); // remove typing indicator
    messages.value.push({ role: "ai", ...res, ts: now(), typing: false });
  } catch (e) {
    messages.value.pop();
    messages.value.push({
      role: "ai",
      type: "error",
      text: "Sorry, I couldn't process that request. Please try again.",
      ts: now(),
    });
  } finally {
    busy.value = false;
    scrollBottom();
    focusInput();
  }
}

function onKey(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
}

// ── Render helpers ───────────────────────────────────────────────────────────
function parseMarkdown(s) {
  if (!s) return "";
  return s
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, '<code class="bg-indigo-50 text-indigo-700 px-1 rounded text-xs">$1</code>')
    .replace(/\n/g, "<br>");
}

const BAR_COLORS = [
  "#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b","#ef4444","#ec4899","#64748b",
];
function barColor(i) { return BAR_COLORS[i % BAR_COLORS.length]; }
</script>

<template>
  <div class="flex h-full flex-col overflow-hidden bg-[#0f0f1a]">

    <!-- ══ HEADER ══════════════════════════════════════════════════════════ -->
    <header class="relative shrink-0 overflow-hidden border-b border-white/10">
      <!-- Grid bg -->
      <div class="pointer-events-none absolute inset-0"
           style="background-image: linear-gradient(rgba(99,102,241,0.08) 1px, transparent 1px),
                                    linear-gradient(90deg, rgba(99,102,241,0.08) 1px, transparent 1px);
                  background-size: 32px 32px;">
      </div>
      <!-- Glow blobs -->
      <div class="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full opacity-20 blur-3xl"
           style="background:radial-gradient(circle,#6366f1,transparent 70%)"></div>
      <div class="pointer-events-none absolute -right-16 -bottom-10 h-56 w-56 rounded-full opacity-15 blur-3xl"
           style="background:radial-gradient(circle,#8b5cf6,transparent 70%)"></div>

      <div class="relative flex items-center gap-4 px-6 py-4">
        <!-- Icon -->
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl"
             style="background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    box-shadow:0 0 20px rgba(99,102,241,0.5)">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.6"
               stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
          </svg>
        </div>

        <!-- Title -->
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl font-black tracking-tight text-white">ATA <span style="background:linear-gradient(90deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent">AI</span> CHAT</h1>
            <span class="flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                  style="background:rgba(99,102,241,0.2);color:#a5b4fc;border:1px solid rgba(99,102,241,0.3)">
              <span class="relative flex h-1.5 w-1.5">
                <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75"></span>
                <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-indigo-400"></span>
              </span>
              Live
            </span>
          </div>
          <p class="text-xs text-indigo-300/70">Intelligent assistant — ask questions about your projects &amp; data</p>
        </div>

        <!-- Right: clear btn -->
        <div class="ml-auto">
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/60 transition hover:bg-white/10 hover:text-white"
            @click="messages = [{ role:'ai', text:'Session cleared. How can I help you?', type:'text', ts:now() }]; showSugg=true"
          >
            <FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" />
            Clear
          </button>
        </div>
      </div>
    </header>

    <!-- ══ BODY ════════════════════════════════════════════════════════════ -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Left panel: quick actions / context (only on wider screens) -->
      <aside class="hidden w-56 shrink-0 flex-col gap-3 border-r border-white/10 bg-white/[0.02] p-4 xl:flex">
        <p class="text-[10px] font-semibold uppercase tracking-[0.15em] text-indigo-400/70">Quick Ask</p>
        <div class="flex flex-col gap-1.5">
          <button
            v-for="s in SUGGESTIONS"
            :key="s.text"
            type="button"
            class="flex items-start gap-2 rounded-xl px-3 py-2.5 text-left text-[11px] font-medium text-white/60 transition hover:bg-white/8 hover:text-white"
            style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06)"
            @click="send(s.text)"
          >
            <FeatherIcon :name="s.icon" class="mt-0.5 h-3.5 w-3.5 shrink-0 text-indigo-400" />
            <span>{{ s.text }}</span>
          </button>
        </div>

        <div class="mt-auto rounded-xl p-3" style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2)">
          <p class="text-[10px] font-semibold text-indigo-300">Powered by</p>
          <p class="text-[11px] font-bold text-white">ATA Intelligence</p>
          <p class="mt-1 text-[9px] text-indigo-400/60">Connected to ERPNext live data</p>
        </div>
      </aside>

      <!-- Chat area -->
      <div class="flex flex-1 flex-col overflow-hidden">

        <!-- Messages scroll area -->
        <div ref="scrollEl" class="flex-1 overflow-y-auto px-4 py-5 space-y-4" style="scroll-behavior:smooth">

          <!-- Suggested chips (shown initially) -->
          <div v-if="showSugg && messages.length <= 1" class="flex flex-wrap gap-2 pb-2">
            <button
              v-for="s in SUGGESTIONS"
              :key="s.text"
              type="button"
              class="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium text-white/70 transition hover:text-white"
              style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25)"
              @click="send(s.text)"
            >
              <FeatherIcon :name="s.icon" class="h-3 w-3 text-indigo-400" />
              {{ s.text }}
            </button>
          </div>

          <!-- Each message -->
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="flex items-end gap-3"
            :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <!-- AI avatar -->
            <div v-if="msg.role === 'ai'" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl"
                 style="background:linear-gradient(135deg,#6366f1,#8b5cf6);box-shadow:0 0 12px rgba(99,102,241,0.4)">
              <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8"
                   stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/>
              </svg>
            </div>

            <!-- Bubble -->
            <div class="max-w-[75%] space-y-2">

              <!-- Typing indicator -->
              <div v-if="msg.typing" class="flex items-center gap-1.5 rounded-2xl rounded-bl-sm px-4 py-3"
                   style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1)">
                <span v-for="d in 3" :key="d" class="h-2 w-2 rounded-full bg-indigo-400"
                      :style="`animation:bounce 1.2s ease-in-out ${(d-1)*0.2}s infinite`"></span>
              </div>

              <!-- User bubble -->
              <div v-else-if="msg.role === 'user'"
                   class="rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed text-white"
                   style="background:linear-gradient(135deg,#4f46e5,#7c3aed);box-shadow:0 4px 15px rgba(79,70,229,0.3)">
                {{ msg.text }}
              </div>

              <!-- AI text bubble -->
              <div v-else-if="msg.type === 'text' || msg.type === 'error' || !msg.type"
                   class="rounded-2xl rounded-bl-sm px-4 py-3 text-sm leading-relaxed text-white/90"
                   :style="msg.type==='error'
                     ? 'background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3)'
                     : 'background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1)'"
                   v-html="parseMarkdown(msg.text)">
              </div>

              <!-- AI stat bubble -->
              <template v-else-if="msg.type === 'stat' || msg.type === 'summary'">
                <div class="rounded-2xl rounded-bl-sm px-4 py-3"
                     style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1)">
                  <p class="text-sm leading-relaxed text-white/90" v-html="parseMarkdown(msg.answer || msg.text)"></p>
                  <p v-if="msg.subtitle" class="mt-1 text-xs text-white/40" v-html="parseMarkdown(msg.subtitle)"></p>
                  <p v-if="msg.hint" class="mt-2 text-xs italic text-indigo-400/70">{{ msg.hint }}</p>
                </div>
                <!-- Bar chart -->
                <div v-if="msg.data && msg.data.length" class="space-y-1.5 rounded-xl p-3"
                     style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08)">
                  <div v-for="(row, ri) in msg.data" :key="ri" class="flex items-center gap-2">
                    <span class="w-28 shrink-0 truncate text-right text-[11px] text-white/50">{{ row.label }}</span>
                    <div class="flex-1 overflow-hidden rounded-full" style="background:rgba(255,255,255,0.08);height:7px">
                      <div class="h-full rounded-full transition-all duration-700"
                           :style="{
                             width: Math.max(4, (row.value / Math.max(...msg.data.map(r=>r.value))) * 100) + '%',
                             background: barColor(ri),
                           }"></div>
                    </div>
                    <span class="w-8 text-right text-[11px] font-bold text-white/70">{{ row.value }}</span>
                  </div>
                </div>
              </template>

              <!-- AI list bubble -->
              <template v-else-if="msg.type === 'list'">
                <div class="rounded-2xl rounded-bl-sm px-4 py-3"
                     style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1)">
                  <p class="text-sm text-white/90" v-html="parseMarkdown(msg.answer || msg.text)"></p>
                </div>
                <div v-if="msg.data && msg.data.length"
                     class="max-h-52 space-y-1 overflow-y-auto rounded-xl p-2"
                     style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08)">
                  <div v-for="(item, ii) in msg.data" :key="ii"
                       class="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-white/70"
                       style="background:rgba(255,255,255,0.04)">
                    <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-md text-[9px] font-bold"
                          :style="`background:${barColor(ii)};color:white;opacity:0.9`">{{ ii+1 }}</span>
                    {{ item }}
                  </div>
                </div>
              </template>

              <!-- Timestamp -->
              <p class="text-[10px] text-white/25" :class="msg.role==='user' ? 'text-right' : ''">{{ msg.ts }}</p>
            </div>

            <!-- User avatar -->
            <div v-if="msg.role === 'user'" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-gray-600 to-gray-700">
              <FeatherIcon name="user" class="h-4 w-4 text-white/80" />
            </div>
          </div>

        </div>

        <!-- ── Input bar ───────────────────────────────────────────────── -->
        <div class="shrink-0 border-t border-white/10 bg-white/[0.02] px-4 py-4">

          <!-- Mobile suggestion chips -->
          <div v-if="showSugg && messages.length <= 1" class="mb-3 flex flex-wrap gap-2 xl:hidden">
            <button
              v-for="s in SUGGESTIONS.slice(0,3)"
              :key="s.text"
              type="button"
              class="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium text-white/60 transition hover:text-white"
              style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25)"
              @click="send(s.text)"
            >
              <FeatherIcon :name="s.icon" class="h-3 w-3 text-indigo-400" />
              {{ s.text }}
            </button>
          </div>

          <div class="flex items-end gap-3">
            <div class="flex-1 overflow-hidden rounded-2xl"
                 style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);box-shadow:0 0 0 0 transparent;transition:box-shadow 0.2s"
                 :style="input ? 'box-shadow:0 0 0 2px rgba(99,102,241,0.4)' : ''">
              <textarea
                ref="inputEl"
                v-model="input"
                rows="1"
                placeholder="Ask anything about your projects, files, or tasks…"
                class="w-full resize-none bg-transparent px-4 py-3 text-sm leading-relaxed text-white placeholder-white/30 outline-none"
                style="max-height:120px"
                :disabled="busy"
                @keydown="onKey"
                @input="e => { e.target.style.height='auto'; e.target.style.height=Math.min(e.target.scrollHeight,120)+'px' }"
              ></textarea>
            </div>

            <button
              type="button"
              class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl transition-all"
              :class="busy || !input.trim() ? 'opacity-40 cursor-not-allowed' : 'hover:scale-105 active:scale-95'"
              style="background:linear-gradient(135deg,#6366f1,#8b5cf6);box-shadow:0 4px 15px rgba(99,102,241,0.4)"
              :disabled="busy || !input.trim()"
              @click="send()"
            >
              <FeatherIcon name="send" class="h-4 w-4 text-white" />
            </button>
          </div>

          <p class="mt-2 text-center text-[10px] text-white/20">
            ATA AI reads live ERPNext data · Press Enter to send
          </p>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30%            { transform: translateY(-6px); }
}

/* Slim scrollbar for dark bg */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 9999px; }
</style>
