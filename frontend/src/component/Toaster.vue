<script setup>
import { useToast } from "@/composables/useToast";
import { FeatherIcon } from "frappe-ui";

const { state, dismiss } = useToast();

function iconFor(kind) {
	if (kind === "success") return "check-circle";
	if (kind === "error") return "alert-circle";
	return "info";
}
function classFor(kind) {
	if (kind === "success") return "border-emerald-200 bg-emerald-50/95 text-emerald-900";
	if (kind === "error") return "border-red-200 bg-red-50/95 text-red-900";
	return "border-[color:var(--portal-border)] bg-white/95 text-[color:var(--portal-text)]";
}
function iconClassFor(kind) {
	if (kind === "success") return "text-emerald-600";
	if (kind === "error") return "text-red-600";
	return "text-[color:var(--portal-accent)]";
}
</script>

<template>
	<Teleport to="body">
		<div class="pointer-events-none fixed bottom-6 right-6 z-[100] flex w-full max-w-sm flex-col gap-2">
			<TransitionGroup name="portal-toast" tag="div" class="flex flex-col gap-2">
				<div
					v-for="t in state.items"
					:key="t.id"
					class="pointer-events-auto flex items-start gap-3 rounded-2xl border px-4 py-3 shadow-lg backdrop-blur"
					:class="classFor(t.kind)"
					role="status"
				>
					<FeatherIcon :name="iconFor(t.kind)" class="mt-0.5 h-4 w-4 shrink-0" :class="iconClassFor(t.kind)" />
					<div class="min-w-0 flex-1 text-sm">
						<p v-if="t.title" class="font-semibold">{{ t.title }}</p>
						<p :class="t.title ? 'mt-0.5 opacity-90' : ''">{{ t.message }}</p>
					</div>
					<button
						type="button"
						class="rounded-md p-0.5 opacity-50 transition hover:bg-black/10 hover:opacity-100"
						aria-label="Dismiss"
						@click="dismiss(t.id)"
					>
						<FeatherIcon name="x" class="h-3.5 w-3.5" />
					</button>
				</div>
			</TransitionGroup>
		</div>
	</Teleport>
</template>

<style scoped>
.portal-toast-enter-active,
.portal-toast-leave-active {
	transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.portal-toast-enter-from {
	opacity: 0;
	transform: translateX(20px) scale(0.97);
}
.portal-toast-leave-to {
	opacity: 0;
	transform: translateX(20px) scale(0.97);
}
.portal-toast-move {
	transition: transform 0.25s ease;
}
</style>
