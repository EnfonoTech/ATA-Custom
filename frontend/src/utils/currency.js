const CURRENCY_LOCALE_MAP = {
	AED: "en-AE",
};

const CURRENCY_SYMBOL_FALLBACK_MAP = {
	AED: "د.إ",
};

let ERP_DEFAULT_LOCALE = null;

export function setCurrencyLocale(locale) {
	if (!locale || typeof locale !== "string") return;
	ERP_DEFAULT_LOCALE = locale;
}

export function formatCurrency(value, currency = "INR", locale = null) {
	if (value === null || value === undefined || value === "") return "";
	if (typeof value === "string" && /[A-Za-z₹$€£¥]/.test(value)) return value;

	const currencyCode = String(currency || "INR").toUpperCase();
	const resolvedLocale =
		locale || CURRENCY_LOCALE_MAP[currencyCode] || ERP_DEFAULT_LOCALE || "en-IN";
	const amount = Number(value);
	if (!Number.isFinite(amount)) return String(value);

	try {
		let formatted = new Intl.NumberFormat(resolvedLocale, {
			style: "currency",
			currency: currencyCode,
			currencyDisplay: "narrowSymbol",
			maximumFractionDigits: 2,
		}).format(amount);

		const fallbackSymbol = CURRENCY_SYMBOL_FALLBACK_MAP[currencyCode];
		if (fallbackSymbol && formatted.includes(currencyCode)) {
			formatted = formatted.replace(currencyCode, fallbackSymbol).replace(/\s{2,}/g, " ");
		}

		return formatted;
	} catch {
		return `${currencyCode} ${amount.toLocaleString(resolvedLocale)}`.trim();
	}
}
