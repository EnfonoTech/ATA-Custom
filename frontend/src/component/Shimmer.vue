<template>
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2 pb-4">
		<div
			v-for="i in 5"
			:key="'stat-' + i"
			class="bg-white rounded-lg shadow-sm px-3 py-2 flex items-center justify-between"
		>
			<div class="space-y-2">
				<div class="h-2.5 w-20 bg-gray-200 rounded animate-pulse"></div>
				<div class="h-5 w-14 bg-gray-200 rounded animate-pulse"></div>
			</div>
			<div class="w-10 h-10 bg-gray-200 rounded-full animate-pulse"></div>
		</div>
	</div>
	<div class="bg-white pt-3 rounded-xl shadow-sm flex flex-col flex-1 min-h-0 overflow-hidden">
		<div class="px-3 py-4 border-b border-gray-100 flex items-center gap-2 flex-wrap">
			<div class="h-8 w-36 bg-gray-200 rounded animate-pulse"></div>
			<div class="h-8 w-36 bg-gray-200 rounded animate-pulse"></div>
			<div class="h-8 w-36 bg-gray-200 rounded animate-pulse"></div>
			<div class="h-8 w-40 bg-gray-200 rounded animate-pulse"></div>
			<div class="h-4 w-24 bg-gray-200 rounded animate-pulse ml-auto"></div>
		</div>
		<div class="p-3 space-y-0">
			<div class="grid grid-cols-6 gap-4 px-2 py-3 border-b border-gray-100">
				<div
					v-for="k in 6"
					:key="'th-' + k"
					class="h-3 bg-gray-200 rounded animate-pulse"
				></div>
			</div>
			<div
				v-for="r in 8"
				:key="'tr-' + r"
				class="grid grid-cols-6 gap-4 px-2 py-4 border-b border-gray-100"
			>
				<div class="h-4 bg-gray-200 rounded animate-pulse"></div>
				<div class="h-5 w-16 bg-gray-200 rounded-full animate-pulse"></div>
				<div class="h-4 bg-gray-200 rounded animate-pulse"></div>
				<div class="h-4 bg-gray-200 rounded animate-pulse"></div>
				<div class="h-4 bg-gray-200 rounded animate-pulse ml-auto w-20"></div>
				<div class="h-4 bg-gray-200 rounded animate-pulse ml-auto w-20"></div>
			</div>
		</div>
	</div>
	<div class="flex items-center justify-between px-1 mb-16 mt-1">
		<div class="h-8 w-32 bg-gray-200 rounded animate-pulse"></div>
	</div>
</template>
