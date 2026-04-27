import { h } from "vue";
import { FeatherIcon } from "frappe-ui";

export const useTabIcon = () => {
	const tabIcon = (name) => ({ render: () => h(FeatherIcon, { name, class: "w-3.5 h-3.5" }) });
	return { tabIcon };
};
