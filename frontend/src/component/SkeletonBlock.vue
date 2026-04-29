<script setup>
defineProps({
	w: { type: String, default: "100%" },
	h: { type: String, default: "1rem" },
	rounded: { type: String, default: "0.5rem" },
});
</script>

<template>
	<div
		class="portal-skeleton"
		:style="{ width: w, height: h, borderRadius: rounded }"
		aria-hidden="true"
	></div>
</template>

<style>
.portal-skeleton {
	display: block;
	position: relative;
	overflow: hidden;
	background: linear-gradient(90deg, rgba(99, 102, 241, 0.08) 0%, rgba(99, 102, 241, 0.16) 50%, rgba(99, 102, 241, 0.08) 100%);
	background-size: 200% 100%;
	animation: portal-skeleton-shimmer 1.4s ease-in-out infinite;
}
@keyframes portal-skeleton-shimmer {
	0% { background-position: 200% 0; }
	100% { background-position: -200% 0; }
}
</style>
