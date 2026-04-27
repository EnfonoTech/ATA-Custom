<script setup>
const props = defineProps({
	modelValue: {
		type: Number,
		default: 10,
	},
	options: {
		type: Array,
		default: () => [10, 20, 50, 100],
	},
});

const emit = defineEmits(["update:modelValue"]);

const isActive = (value) => props.modelValue === value;

const updateValue = (value) => {
	emit("update:modelValue", value);
};
</script>

<template>
	<div class="flex items-center gap-3">
		<div class="flex items-center rounded-xl border border-gray-200 bg-gray-50 p-1 shadow-sm">
			<button
				v-for="(option, index) in options"
				:key="option"
				@click="updateValue(option)"
				class="px-4 py-1.5 text-sm font-medium rounded-lg transition-all duration-200"
				:class="[
					isActive(option)
						? 'bg-white text-blue-600 shadow-md'
						: 'text-gray-600 hover:text-gray-900 hover:bg-white/70',
				]"
			>
				{{ option }}
			</button>
		</div>
	</div>
</template>
