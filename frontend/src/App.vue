<template>
	<router-view />
	<Teleport to="body">
		<transition name="slide-toast">
			<div v-if="toastMessage.text" class="fixed bottom-6 right-6 z-[9999]">
				<div
					class="max-w-xs w-full p-4 bg-white border rounded-xl shadow-lg"
					:class="
						toastMessage.type === 'success' ? 'border-green-100' : 'border-red-100'
					"
					role="alert"
				>
					<div class="flex gap-x-3 items-start">
						<svg
							v-if="toastMessage.type === 'success'"
							class="shrink-0 size-4 text-green-500 mt-0.5"
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							fill="currentColor"
							viewBox="0 0 16 16"
						>
							<path
								d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"
							/>
						</svg>
						<svg
							v-else
							class="shrink-0 size-4 text-red-500 mt-0.5"
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							fill="currentColor"
							viewBox="0 0 16 16"
						>
							<path
								d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
							/>
						</svg>
						<div class="grow">
							<p
								class="text-sm font-medium"
								:class="
									toastMessage.type === 'success'
										? 'text-green-700'
										: 'text-red-700'
								"
							>
								{{ toastMessage.text }}
							</p>
						</div>
						<button
							@click="hideToast"
							class="ml-2 flex items-center justify-center w-5 h-5 text-[10px] text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100 transition"
						>
							✕
						</button>
					</div>
				</div>
			</div>
		</transition>
	</Teleport>
</template>

<script setup>
import { useToast } from "@/composables/useToast";

const { toastMessage, hideToast } = useToast();
</script>

<style>
.slide-toast-enter-active,
.slide-toast-leave-active {
	transition: all 0.35s ease;
}
.slide-toast-enter-from {
	opacity: 0;
	transform: translateX(100%);
}
.slide-toast-enter-to {
	opacity: 1;
	transform: translateX(0);
}
.slide-toast-leave-from {
	opacity: 1;
	transform: translateX(0);
}
.slide-toast-leave-to {
	opacity: 0;
	transform: translateX(100%);
}
</style>
