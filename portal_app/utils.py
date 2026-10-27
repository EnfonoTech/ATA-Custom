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


def assign_add_unchecked(args):
	"""`frappe.desk.form.assign_to.add` without its document permission check.

	Callers run their own portal gate first. Frappe 15.104 takes the flag as
	`add(args, ignore_permissions=True)`; newer v15 releases dropped the keyword from
	the whitelisted `add()` and moved it to the internal `_add()`. Passing the keyword
	there raises TypeError, so pick whichever this bench has.
	"""
	from frappe.desk.form import assign_to

	if hasattr(assign_to, "_add"):
		return assign_to._add(args, ignore_permissions=True)
	return assign_to.add(args, ignore_permissions=True)


def assign_remove_unchecked(doctype, name, user):
	"""`assign_to.remove` without its permission check, on every v15 release.

	`remove()` lost its `ignore_permissions` keyword in the same change as `add()`.
	Both old and new `remove()` are a thin wrapper over `set_status`, whose signature
	did not change, so call that directly.
	"""
	from frappe.desk.form.assign_to import set_status

	return set_status(doctype, name, "", user, status="Cancelled", ignore_permissions=True)
