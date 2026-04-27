function readCookie(name) {
	const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
	return match ? decodeURIComponent(match[2]) : "";
}

let cachedCsrfToken = null;

function getCsrfToken() {
	if (cachedCsrfToken) return cachedCsrfToken;
	const fromBoot = (typeof window !== "undefined" && (window.csrf_token || window?.frappe?.boot?.csrf_token)) || "";
	if (fromBoot && fromBoot !== "None") {
		cachedCsrfToken = fromBoot;
		return cachedCsrfToken;
	}
	const fromCookie = readCookie("csrf_token");
	if (fromCookie) {
		cachedCsrfToken = fromCookie;
	}
	return cachedCsrfToken || "";
}

async function refreshCsrfToken() {
	cachedCsrfToken = null;
	try {
		const res = await fetch("/api/method/frappe.sessions.get_csrf_token", {
			method: "GET",
			credentials: "include",
		});
		if (!res.ok) return "";
		const data = await res.json().catch(() => ({}));
		const token = data?.message?.csrf_token || data?.message || "";
		if (token && typeof token === "string") {
			cachedCsrfToken = token;
			if (typeof window !== "undefined") {
				window.csrf_token = token;
			}
			return token;
		}
	} catch {
		/* ignore — fall back to whatever we had */
	}
	return "";
}

function isCsrfError(errorBody) {
	if (!errorBody) return false;
	const exc = String(errorBody.exc_type || errorBody.exception || "");
	if (exc.includes("CSRFTokenError")) return true;
	const msg = String(errorBody.exc || errorBody._error_message || errorBody.message || "");
	return /CSRFTokenError|Invalid Request/i.test(msg);
}

export async function call({ method, args = {}, type = "GET", responseType = "json" }) {
	const url = `/api/method/${method}`;
	const isPost = type === "POST";

	const buildOptions = (csrfToken) => {
		const opts = {
			method: type,
			credentials: "include",
			headers: {},
		};
		if (csrfToken) opts.headers["X-Frappe-CSRF-Token"] = csrfToken;
		if (type === "POST") {
			opts.headers["Content-Type"] = "application/json";
			opts.body = JSON.stringify(args);
		}
		return opts;
	};

	let getUrl = url;
	if (type === "GET") {
		const query = new URLSearchParams(args).toString();
		if (query) getUrl = `${url}?${query}`;
	}

	const send = async (csrfToken) => {
		return await fetch(type === "GET" ? getUrl : url, buildOptions(csrfToken));
	};

	let res = await send(getCsrfToken());

	if (!res.ok && isPost && res.status === 403) {
		// Try one CSRF refresh + retry. Frappe re-issues the token after server restart / migrate.
		const errPeek = await res.clone().json().catch(() => ({}));
		if (isCsrfError(errPeek)) {
			const fresh = await refreshCsrfToken();
			if (fresh) {
				res = await send(fresh);
			}
		}
	}

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		const error = new Error("API Error");
		error.responseBody = errorData;
		throw error;
	}

	if (responseType === "blob") {
		return await res.blob();
	}

	const data = await res.json();
	return data.message;
}

/**
 * Multipart upload for whitelisted file handlers (project field + file).
 */
export async function uploadFile(method, file, extraFields = {}) {
	const fd = new FormData();
	fd.append("file", file);
	for (const [k, v] of Object.entries(extraFields)) {
		if (v != null && v !== "") fd.append(k, String(v));
	}
	const sendOnce = async (csrfToken) => {
		const headers = {};
		if (csrfToken) headers["X-Frappe-CSRF-Token"] = csrfToken;
		return await fetch(`/api/method/${method}`, {
			method: "POST",
			body: fd,
			credentials: "include",
			headers,
		});
	};

	let res = await sendOnce(getCsrfToken());
	if (!res.ok && res.status === 403) {
		const errPeek = await res.clone().json().catch(() => ({}));
		if (isCsrfError(errPeek)) {
			const fresh = await refreshCsrfToken();
			if (fresh) res = await sendOnce(fresh);
		}
	}

	if (!res.ok) {
		const errorData = await res.json().catch(() => ({}));
		const error = new Error("API Error");
		error.responseBody = errorData;
		throw error;
	}
	const data = await res.json();
	return data.message;
}

// Public helper so app entry can prime the CSRF cache (e.g. after login).
export async function ensureCsrfReady() {
	if (getCsrfToken()) return;
	await refreshCsrfToken();
}
