<template>
	<Teleport to="body">
		<Transition name="desc-modal">
			<div v-if="show" class="fixed inset-0 z-[60] flex items-center justify-center px-4">
				<div
					class="absolute inset-0 bg-black/50 backdrop-blur-sm"
					@click="handleClose"
				></div>
				<div
					class="relative bg-white w-full max-w-2xl rounded-2xl shadow-2xl z-10 flex flex-col max-h-[80vh]"
				>
					<div
						class="flex justify-between items-center px-6 py-4 border-b border-gray-100 shrink-0"
					>
						<div class="flex items-center gap-2">
							<div class="w-1 h-5 bg-blue-500 rounded-full"></div>
							<h2 class="text-medium font-semibold text-gray-800">
								{{ allowEdit ? "Edit Description" : "Description" }}
							</h2>
							<span
								v-if="itemCode"
								class="text-xs text-gray-800 font-medium bg-gray-200 px-2 py-0.5 rounded-full"
							>
								{{ itemCode }}
							</span>
						</div>
						<button
							@click="handleClose"
							class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-50 transition"
						>
							<FeatherIcon
								name="x"
								class="w-4 h-4 text-gray-700 hover:text-red-500"
							/>
						</button>
					</div>
					<div
						v-if="allowEdit"
						class="flex-1 overflow-y-auto px-6 py-5 desc-scroll flex flex-col gap-3"
					>
						<p class="text-xs text-gray-400 font-medium">
							Use the toolbar to format your description. HTML output will be saved.
						</p>
						<div
							class="border border-gray-200 rounded-xl overflow-hidden bg-white editor-wrapper"
						>
							<TextEditor
								:content="editValue"
								:editable="true"
								placeholder="Enter description..."
								editor-class="min-h-[220px] px-4 py-3 text-sm text-gray-700 leading-relaxed focus:outline-none"
								@change="editValue = $event"
							>
								<template #top>
									<TextEditorFixedMenu
										:buttons="editorButtons"
										class="border-b border-gray-200 bg-gray-50 px-2 py-1 flex flex-wrap gap-0.5"
									/>
								</template>
							</TextEditor>
						</div>
					</div>
					<div v-else class="flex-1 overflow-y-auto px-6 py-5 desc-scroll">
						<div
							v-if="isHtml"
							class="prose prose-sm max-w-none text-gray-700 leading-relaxed"
							v-html="description"
						></div>
						<p
							v-else
							class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap"
						>
							{{ description || "No description available." }}
						</p>
					</div>
					<div
						class="px-6 py-3 border-t border-gray-100 flex justify-end gap-2 shrink-0"
					>
						<template v-if="allowEdit">
							<button
								@click="handleClose"
								class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-semibold transition bg-gray-100 hover:bg-gray-200 text-gray-700"
							>
								Cancel
							</button>
							<button
								@click="saveEdit"
								:disabled="saving"
								class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-semibold transition bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
							>
								<FeatherIcon
									:name="saving ? 'loader' : 'check'"
									class="w-3.5 h-3.5"
									:class="{ 'animate-spin': saving }"
								/>
								{{ saving ? "Saving..." : "Save" }}
							</button>
						</template>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { FeatherIcon, TextEditor, TextEditorFixedMenu } from "frappe-ui";

const props = defineProps({
	show: { type: Boolean, default: false },
	description: { type: String, default: "" },
	itemCode: { type: String, default: null },
	allowEdit: { type: Boolean, default: false },
});

const emit = defineEmits(["close", "save"]);

const editValue = ref("");
const saving = ref(false);

const isHtml = computed(() => /<[a-z][\s\S]*>/i.test(props.description || ""));

const editorButtons = [
	"Paragraph",
	"Heading 1",
	"Heading 2",
	"Heading 3",
	"Separator",

	"Bold",
	"Italic",
	"Underline",
	"Strikethrough",
	"Highlight",
	"Separator",

	"Bullet List",
	"Numbered List",
	"Separator",

	"Blockquote",
	"Code",
	"Horizontal Rule",
	"Separator",

	"Link",
	"Image",
	"Separator",

	"Align Left",
	"Align Center",
	"Align Right",
	"Align Justify",
	"Separator",

	"Table",
	"Separator",

	"Undo",
	"Redo",
];

watch(
	() => props.show,
	(val) => {
		if (val && props.allowEdit) {
			editValue.value = props.description || "";
		}
		if (!val) {
			editValue.value = "";
			saving.value = false;
		}
	},
);

watch(
	() => props.description,
	(val) => {
		if (props.show && props.allowEdit) {
			editValue.value = val || "";
		}
	},
);

const saveEdit = async () => {
	saving.value = true;
	try {
		await emit("save", { itemCode: props.itemCode, description: editValue.value });
	} finally {
		saving.value = false;
	}
};

const handleClose = () => {
	emit("close");
};
</script>

<style scoped>
.desc-scroll::-webkit-scrollbar {
	width: 4px;
}
.desc-scroll::-webkit-scrollbar-thumb {
	background: #e2e8f0;
	border-radius: 999px;
}

.desc-modal-enter-active,
.desc-modal-leave-active {
	transition: opacity 0.2s ease;
}
.desc-modal-enter-from,
.desc-modal-leave-to {
	opacity: 0;
}
.desc-modal-enter-active .relative,
.desc-modal-leave-active .relative {
	transition: transform 0.2s ease;
}
.desc-modal-enter-from .relative,
.desc-modal-leave-to .relative {
	transform: scale(0.97) translateY(8px);
}

.editor-wrapper :deep(.ProseMirror) {
	min-height: 220px;
	padding: 0.75rem 1rem;
	font-size: 0.875rem;
	color: #374151;
	line-height: 1.6;
	outline: none;
}

.editor-wrapper :deep(.ProseMirror p.is-editor-empty:first-child::before) {
	content: attr(data-placeholder);
	color: #9ca3af;
	pointer-events: none;
	float: left;
	height: 0;
}

.editor-wrapper :deep(.ProseMirror p) {
	margin-bottom: 0.5rem;
}

.editor-wrapper :deep(.ProseMirror strong) {
	font-weight: 700;
	color: #1f2937;
}

.editor-wrapper :deep(.ProseMirror em) {
	font-style: italic;
}

.editor-wrapper :deep(.ProseMirror u) {
	text-decoration: underline;
}

.editor-wrapper :deep(.ProseMirror s) {
	text-decoration: line-through;
}

.editor-wrapper :deep(.ProseMirror h1) {
	font-size: 1.5rem;
	font-weight: 700;
	color: #111827;
	margin-bottom: 0.5rem;
}

.editor-wrapper :deep(.ProseMirror h2) {
	font-size: 1.25rem;
	font-weight: 600;
	color: #1f2937;
	margin-bottom: 0.4rem;
}

.editor-wrapper :deep(.ProseMirror h3) {
	font-size: 1.1rem;
	font-weight: 600;
	color: #374151;
	margin-bottom: 0.4rem;
}

.editor-wrapper :deep(.ProseMirror ul) {
	padding-left: 1.25rem;
	list-style-type: disc;
	margin-bottom: 0.5rem;
}

.editor-wrapper :deep(.ProseMirror ol) {
	padding-left: 1.25rem;
	list-style-type: decimal;
	margin-bottom: 0.5rem;
}

.editor-wrapper :deep(.ProseMirror li) {
	margin-bottom: 0.2rem;
}

.editor-wrapper :deep(.ProseMirror blockquote) {
	border-left: 3px solid #e5e7eb;
	padding-left: 1rem;
	color: #6b7280;
	font-style: italic;
	margin: 0.5rem 0;
}

.editor-wrapper :deep(.ProseMirror code) {
	background: #f3f4f6;
	border-radius: 4px;
	padding: 2px 6px;
	font-size: 0.8rem;
	color: #ef4444;
	font-family: monospace;
}

.editor-wrapper :deep(.ProseMirror pre) {
	background: #1f2937;
	color: #f9fafb;
	border-radius: 0.5rem;
	padding: 1rem;
	overflow-x: auto;
	font-size: 0.8rem;
	margin-bottom: 0.5rem;
}

.editor-wrapper :deep(.ProseMirror img) {
	max-width: 100%;
	border-radius: 0.5rem;
	margin: 0.5rem 0;
}

.editor-wrapper :deep(.ProseMirror a) {
	color: #3b82f6;
	text-decoration: underline;
}

.editor-wrapper :deep(.ProseMirror table) {
	width: 100%;
	border-collapse: collapse;
	font-size: 0.8rem;
	margin-bottom: 0.5rem;
}

.editor-wrapper :deep(.ProseMirror th),
.editor-wrapper :deep(.ProseMirror td) {
	border: 1px solid #e5e7eb;
	padding: 6px 10px;
	text-align: left;
}

.editor-wrapper :deep(.ProseMirror th) {
	background: #f9fafb;
	font-weight: 600;
	color: #6b7280;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	font-size: 0.7rem;
}
:deep(.prose p) {
	margin-bottom: 0.6rem;
}
:deep(.prose ul) {
	padding-left: 1.2rem;
}
:deep(.prose li) {
	margin-bottom: 0.25rem;
}
:deep(.prose strong) {
	color: #374151;
}
:deep(.prose a) {
	color: #3b82f6;
	text-decoration: underline;
}
:deep(.prose table) {
	width: 100%;
	border-collapse: collapse;
	font-size: 0.8rem;
}
:deep(.prose th),
:deep(.prose td) {
	border: 1px solid #e5e7eb;
	padding: 6px 10px;
	text-align: left;
}
:deep(.prose th) {
	background: #f9fafb;
	font-weight: 600;
	color: #6b7280;
	text-transform: uppercase;
	letter-spacing: 0.04em;
	font-size: 0.7rem;
}
</style>
