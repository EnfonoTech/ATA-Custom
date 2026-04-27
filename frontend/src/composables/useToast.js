import { ref } from "vue";

const toastMessage = ref({ text: "", type: "" });
let toastTimer = null;

export function useToast() {
	const showToast = (text, type = "success") => {
		if (toastTimer) clearTimeout(toastTimer);
		toastMessage.value = { text, type };
		toastTimer = setTimeout(() => {
			toastMessage.value = { text: "", type: "" };
		}, 4000);
	};

	const hideToast = () => {
		toastMessage.value = { text: "", type: "" };
	};

	return { toastMessage, showToast, hideToast };
}
