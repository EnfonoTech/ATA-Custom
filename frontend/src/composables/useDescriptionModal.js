import { ref } from "vue";

export const useDescriptionModal = () => {
	const descriptionModal = ref({ show: false, description: "", itemCode: null });

	const openDescription = (item) => {
		descriptionModal.value = {
			show: true,
			description: item?.description || "",
			itemCode: item?.item_code || null,
		};
	};

	const closeDescription = () => {
		descriptionModal.value.show = false;
	};

	const resetDescription = () => {
		descriptionModal.value = { show: false, description: "", itemCode: null };
	};

	return { descriptionModal, openDescription, closeDescription, resetDescription };
};
