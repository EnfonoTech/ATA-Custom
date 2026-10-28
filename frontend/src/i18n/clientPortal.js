// Strings for the client landing page (/portal-app/client) only — the rest of the portal
// is English. Arabic is the default; the choice is remembered per browser.
import { ref, computed } from "vue";

const STORAGE_KEY = "portal_client_lang";

export const MESSAGES = {
	ar: {
		title: "بوابة العميل",
		chooseProject: "اختر المشروع",
		noProjects: "لا توجد مشاريع مرتبطة بحسابك",
		incoming: "الوارد",
		outgoing: "الصادر",
		incomingHint: "ما أرسلته ATA إليكم",
		outgoingHint: "ما أرسلتموه إلى ATA",
		submission: "تسليم",
		submissionN: "التسليم رقم {n}",
		latest: "الأحدث (النهائي)",
		files: "الملفات",
		fileCount: "{n} ملف",
		open: "فتح",
		close: "إغلاق",
		download: "تنزيل",
		back: "رجوع",
		backToProjects: "العودة إلى المشاريع",
		empty: "لا توجد تسليمات بعد",
		upload: "رفع ملفات إلى الصادر",
		uploading: "جارٍ الرفع {done} من {total}…",
		uploaded: "تم رفع {n} ملف",
		uploadFailed: "تعذّر الرفع",
		loading: "جارٍ التحميل…",
		error: "حدث خطأ، حاول مرة أخرى",
		signOut: "تسجيل الخروج",
		language: "English",
		sentOn: "أُرسل في {date}",
	},
	en: {
		title: "Client portal",
		chooseProject: "Choose a project",
		noProjects: "No projects are linked to your account",
		incoming: "Incoming",
		outgoing: "Outgoing",
		incomingHint: "What ATA sent to you",
		outgoingHint: "What you sent to ATA",
		submission: "Submission",
		submissionN: "Submission {n}",
		latest: "Latest (final)",
		files: "Files",
		fileCount: "{n} file(s)",
		open: "Open",
		close: "Close",
		download: "Download",
		back: "Back",
		backToProjects: "Back to projects",
		empty: "No submissions yet",
		upload: "Upload files to Outgoing",
		uploading: "Uploading {done} of {total}…",
		uploaded: "Uploaded {n} file(s)",
		uploadFailed: "Upload failed",
		loading: "Loading…",
		error: "Something went wrong, try again",
		signOut: "Sign out",
		language: "العربية",
		sentOn: "Sent on {date}",
	},
};

function readLang() {
	try {
		const v = window.localStorage.getItem(STORAGE_KEY);
		return v === "en" || v === "ar" ? v : "ar";
	} catch {
		return "ar";
	}
}

export function useClientLang() {
	const lang = ref(readLang());
	const dir = computed(() => (lang.value === "ar" ? "rtl" : "ltr"));

	function setLang(l) {
		lang.value = l === "en" ? "en" : "ar";
		try {
			window.localStorage.setItem(STORAGE_KEY, lang.value);
		} catch {
			/* storage blocked: the choice lasts for this page view only */
		}
	}

	function t(key, params = {}) {
		const text = MESSAGES[lang.value]?.[key] ?? MESSAGES.en[key] ?? key;
		return text.replace(/\{(\w+)\}/g, (m, k) => (k in params ? String(params[k]) : m));
	}

	// ar-SA would default to the Umm al-Qura calendar; the file names carry Gregorian
	// YYYY-MM-DD dates with Latin digits, so the page uses the same.
	function formatDate(value) {
		if (!value) return "";
		const d = new Date(String(value).replace(" ", "T"));
		if (Number.isNaN(d.getTime())) return String(value);
		const locale = lang.value === "ar" ? "ar-u-ca-gregory-nu-latn" : "en-GB";
		try {
			return d.toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
		} catch {
			return String(value).slice(0, 10);
		}
	}

	return { lang, dir, t, setLang, formatDate };
}
