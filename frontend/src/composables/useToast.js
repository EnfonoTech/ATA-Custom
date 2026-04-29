import { reactive } from "vue";

/** Global toast queue. Use the helpers (success / error / info) to push messages. */
let counter = 0;
const state = reactive({ items: [] });

function push(payload) {
	const id = ++counter;
	const item = {
		id,
		kind: payload.kind || "info", // info | success | error
		title: payload.title || "",
		message: payload.message || "",
		ttl: payload.ttl ?? 4000,
	};
	state.items = [...state.items, item];
	if (item.ttl > 0) {
		setTimeout(() => dismiss(id), item.ttl);
	}
	return id;
}

function dismiss(id) {
	state.items = state.items.filter((t) => t.id !== id);
}

export function useToast() {
	return {
		state,
		toast: push,
		dismiss,
		success: (message, opts = {}) => push({ kind: "success", message, ...opts }),
		error: (message, opts = {}) => push({ kind: "error", message, ttl: 6000, ...opts }),
		info: (message, opts = {}) => push({ kind: "info", message, ...opts }),
	};
}

// Backwards-compat for older callers that imported showToast/toastMessage directly.
export const toastMessage = { value: { text: "", type: "" } };
export const showToast = (text, type = "info") => push({ kind: type, message: text });
export const hideToast = () => (state.items = []);
