"""Request-level helpers wired up from hooks.py."""

import frappe

# Only the SPA's HTML entry points. Everything under /assets/ must stay cacheable —
# the chunks are content-hashed and the entry carries a ?v= build stamp, so caching
# them is the whole point.
_NO_STORE_PATHS = ("/portal-app",)


def set_spa_no_cache(response=None, request=None, **kwargs):
	"""Tell browsers never to cache the SPA's HTML document.

	`context.no_cache = 1` only governs Frappe's own server-side website cache (the
	`X-From-Cache` header). It emits no browser directive at all, which was the bug:
	/portal-app came back with no `Cache-Control`, browsers cached the HTML under
	heuristic freshness, and kept requesting the previous `?v=` build stamp. The
	asset cache-busting then never fired and deploys looked like they had not landed.

	`after_request` is the documented place to reach the real response object —
	frappe/app.py `run_after_request_hooks` calls each hook with
	`response=` and `request=`.

	Deliberately defensive: a hook that raises here would break every request on the
	site, and a missing cache header is never worth that.
	"""
	try:
		if response is None or request is None:
			return
		path = request.path or ""
		if not any(path == p or path.startswith(p + "/") for p in _NO_STORE_PATHS):
			return
		# Only the HTML document, never a static file served under the same prefix.
		ctype = response.headers.get("Content-Type", "")
		if "text/html" not in ctype:
			return
		response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
		response.headers["Pragma"] = "no-cache"
		response.headers["Expires"] = "0"
	except Exception:
		frappe.logger().debug("portal_app: could not set SPA cache headers", exc_info=True)
