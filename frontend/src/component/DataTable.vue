<template>
	<div class="flex-1 border border-gray-100 rounded-xl bg-white overflow-x-auto">
		<table class="min-w-full border-collapse text-sm text-left">
			<thead
				class="bg-gray-50 text-[11px] uppercase text-gray-500 font-bold tracking-widest"
			>
				<tr>
					<th
						v-for="col in columns"
						:key="col.key"
						:class="[
							'px-6 py-2 bg-gray-50 whitespace-nowrap',
							col.align === 'right'
								? 'text-right'
								: col.align === 'center'
									? 'text-center'
									: '',
						]"
					>
						<button
							class="inline-flex items-center gap-1 group"
							@click="handleSort(col.key)"
						>
							<span>{{ col.label }}</span>
							<span class="flex flex-col gap-[1px] ml-0.5">
								<svg
									class="w-2 h-2 transition-colors"
									:class="
										sortKey === col.key && sortOrder === 'asc'
											? 'text-gray-900'
											: 'text-gray-300 group-hover:text-gray-400'
									"
									viewBox="0 0 10 6"
									fill="currentColor"
								>
									<path d="M5 0L10 6H0L5 0Z" />
								</svg>
								<svg
									class="w-2 h-2 transition-colors"
									:class="
										sortKey === col.key && sortOrder === 'desc'
											? 'text-gray-900'
											: 'text-gray-300 group-hover:text-gray-400'
									"
									viewBox="0 0 10 6"
									fill="currentColor"
								>
									<path d="M5 6L0 0H10L5 6Z" />
								</svg>
							</span>
						</button>
					</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-gray-100 bg-white">
				<tr
					v-for="(row, index) in rows"
					:key="index"
					class="hover:bg-gray-50 transition-colors"
					:class="{ 'cursor-pointer': clickable }"
					@click="clickable ? $emit('row-click', row) : null"
				>
					<td
						v-for="col in columns"
						:key="col.key"
						:class="[
							'px-6 py-3 whitespace-nowrap text-ellipsis',
							col.align === 'right'
								? 'text-right'
								: col.align === 'center'
									? 'text-center'
									: '',
						]"
					>
						<slot :name="col.key" :row="row">
							<span class="text-gray-600 font-medium">
								{{ row[col.key] ?? "--" }}
							</span>
						</slot>
					</td>
				</tr>
				<tr v-if="rows.length === 0">
					<td
						:colspan="columns.length"
						class="px-6 py-12 text-center text-gray-400 font-medium italic"
					>
						{{ emptyText }}
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script>
export default {
	name: "DataTable",
	props: {
		columns: {
			type: Array,
			required: true,
		},
		rows: {
			type: Array,
			required: true,
		},
		emptyText: {
			type: String,
			default: "No records found.",
		},
		clickable: {
			type: Boolean,
			default: true,
		},
	},
	emits: ["row-click", "sort"],

	data() {
		return {
			sortKey: null,
			sortOrder: null,
		};
	},

	methods: {
		handleSort(key) {
			if (this.sortKey !== key) {
				this.sortKey = key;
				this.sortOrder = "asc";
			} else if (this.sortOrder === "asc") {
				this.sortOrder = "desc";
			} else if (this.sortOrder === "desc") {
				this.sortKey = null;
				this.sortOrder = null;
			}

			this.$emit("sort", { key: this.sortKey, order: this.sortOrder });
		},
	},
};
</script>
