<template>
	<Teleport to="body">
		<Transition name="modal">
			<div v-if="show" class="fixed inset-0 z-[70] flex items-center justify-center px-4">
				<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('cancel')"></div>
				<div class="relative bg-white w-full max-w-sm rounded-2xl shadow-2xl z-10 overflow-hidden">
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
						<div class="flex items-center gap-2">
							<div class="w-1 h-5 bg-gray-900 rounded-full"></div>
							<h2 class="text-medium font-semibold text-gray-800">Confirm Logout</h2>
						</div>
						<button
							@click="$emit('cancel')"
							class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition"
						>
							<FeatherIcon name="x" class="w-4 h-4 text-gray-500 hover:text-gray-800" />
						</button>
					</div>
					<div class="px-6 py-8 flex flex-col items-center gap-4">
						<div class="w-16 h-16 flex items-center justify-center rounded-full bg-gray-100 ring-4 ring-gray-200">
							<FeatherIcon name="log-out" class="w-7 h-7 text-gray-900" />
						</div>
						<div class="text-center space-y-1">
							<p class="text-sm font-semibold text-gray-800">Are you sure you want to logout?</p>
						</div>
					</div>
					<div class="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-2">
						<button
							@click="$emit('cancel')"
							:disabled="loggingOut"
							class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition bg-gray-100 hover:bg-gray-200 text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							Cancel
						</button>
						<button
							@click="$emit('confirm')"
							:disabled="loggingOut"
							class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition bg-gray-900 hover:bg-black text-white disabled:opacity-50 disabled:cursor-not-allowed"
						>
							<FeatherIcon
								:name="loggingOut ? 'loader' : 'log-out'"
								class="w-3.5 h-3.5"
								:class="{ 'animate-spin': loggingOut }"
							/>
							{{ loggingOut ? "Logging out..." : "Logout" }}
						</button>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui";

defineProps({
	show: { type: Boolean, default: false },
	loggingOut: { type: Boolean, default: false },
});

defineEmits(["cancel", "confirm"]);
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
	transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
	opacity: 0;
}
.modal-enter-active .relative,
.modal-leave-active .relative {
	transition: transform 0.2s ease;
}
.modal-enter-from .relative,
.modal-leave-to .relative {
	transform: scale(0.97) translateY(8px);
}
</style>