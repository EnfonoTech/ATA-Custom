import { computed } from "vue";
import { formatCurrency } from "@/utils/currency";

export const useDocCurrencyFormat = (
	docRef,
	{
		docCurrencyKey = "currency",
		companyCurrencyKey = "company_currency",
		outstandingCurrencyKey = "outstanding_currency",
	} = {},
) => {
	const formatDocAmount = (value) =>
		formatCurrency(value, docRef.value?.[docCurrencyKey] || "INR");

	const formatCompanyAmount = (value) =>
		formatCurrency(value, docRef.value?.[companyCurrencyKey] || "INR");

	const formatOutstandingAmount = (value) =>
		formatCurrency(
			value,
			docRef.value?.[outstandingCurrencyKey] || docRef.value?.[docCurrencyKey] || "INR",
		);

	const showCompanyCurrency = computed(() => {
		const doc = docRef.value || {};
		return (
			doc[companyCurrencyKey] &&
			doc[docCurrencyKey] &&
			doc[companyCurrencyKey] !== doc[docCurrencyKey]
		);
	});

	return { formatDocAmount, formatCompanyAmount, formatOutstandingAmount, showCompanyCurrency };
};
