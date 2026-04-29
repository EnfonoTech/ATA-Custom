<script setup>
import { FeatherIcon } from "frappe-ui";

defineProps({
	icon: { type: String, default: "inbox" },
	title: { type: String, required: true },
	message: { type: String, default: "" },
	gradient: {
		type: String,
		default: "linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #38bdf8 100%)",
	},
});
</script>

<template>
	<div class="portal-card-strong flex flex-col items-center justify-center gap-3 p-10 text-center">
		<div
			class="flex h-12 w-12 items-center justify-center rounded-2xl text-white"
			:style="{ background: gradient }"
		>
			<FeatherIcon :name="icon" class="h-5 w-5" />
		</div>
		<p class="text-base font-semibold text-[color:var(--portal-text)]">{{ title }}</p>
		<p v-if="message" class="max-w-md text-sm text-[color:var(--portal-muted)]">{{ message }}</p>
		<div v-if="$slots.action" class="mt-1 flex flex-wrap items-center justify-center gap-2">
			<slot name="action" />
		</div>
	</div>
</template>
