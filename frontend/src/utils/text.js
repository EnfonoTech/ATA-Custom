export const stripHtml = (str) => {
	if (!str) return "—";
	return str
		.replace(/<[^>]*>/g, " ")
		.replace(/\s+/g, " ")
		.trim();
};
