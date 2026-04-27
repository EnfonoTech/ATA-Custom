import { ref, nextTick } from "vue";

export const useTooltip = () => {
	const tooltipEl = ref(null);
	const tooltip = ref({ visible: false, content: "", isHtml: false, x: 0, y: 0 });

	const showTooltip = (event, value) => {
		const rect = event.currentTarget.getBoundingClientRect();
		const TOOLTIP_WIDTH = 288;
		const GAP = 8;

		let x = rect.left;
		if (x + TOOLTIP_WIDTH > window.innerWidth) {
			x = window.innerWidth - TOOLTIP_WIDTH - 8;
		}

		tooltip.value = {
			visible: true,
			content: value,
			isHtml: /<[a-z][\s\S]*>/i.test(value || ""),
			x,
			y: rect.bottom + GAP,
		};

		nextTick(() => {
			if (!tooltipEl.value) return;
			const tooltipHeight = tooltipEl.value.offsetHeight;
			const spaceBelow = window.innerHeight - rect.bottom;
			const spaceAbove = rect.top;

			if (tooltipHeight > spaceBelow && tooltipHeight <= spaceAbove) {
				tooltip.value.y = rect.top - tooltipHeight - GAP;
			}
		});
	};

	const hideTooltip = () => {
		tooltip.value.visible = false;
	};

	return { tooltipEl, tooltip, showTooltip, hideTooltip };
};
