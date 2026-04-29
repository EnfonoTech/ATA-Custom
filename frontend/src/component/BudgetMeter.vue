<script setup>
import { computed } from "vue";

const props = defineProps({
	pct: { type: Number, required: true }, // 0..100+
	label: { type: String, default: "" },
});

const clamped = computed(() => Math.max(0, Math.min(120, Number(props.pct) || 0)));
const tone = computed(() => {
	const v = clamped.value;
	if (v >= 100) return { fg: "linear-gradient(90deg, #ef4444, #f97316)", text: "text-red-700", state: "Over budget" };
	if (v >= 80) return { fg: "linear-gradient(90deg, #f59e0b, #fbbf24)", text: "text-amber-700", state: "At risk" };
	return { fg: "linear-gradient(90deg, #10b981, #34d399)", text: "text-emerald-700", state: "Healthy" };
});
</script>

<template>
	<div class="space-y-1">
		<div class="flex items-center justify-between text-[11px] font-medium">
			<span :class="tone.text">{{ label || tone.state }}</span>
			<span class="font-mono text-[color:var(--portal-text)]">{{ Math.round(clamped) }}%</span>
		</div>
		<div class="relative h-2 overflow-hidden rounded-full bg-[color:var(--portal-bg-dim)]">
			<div
				class="absolute left-0 top-0 h-full rounded-full transition-all duration-500"
				:style="{ width: Math.min(100, clamped) + '%', background: tone.fg }"
			></div>
			<!-- 100% threshold tick -->
			<div class="absolute top-0 h-full w-px bg-[color:var(--portal-border-strong)]" style="left: calc(100% - 1px);"></div>
		</div>
	</div>
</template>
