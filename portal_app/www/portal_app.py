"""Serves the portal single-page app at /portal-app.

Why this file does more than `context.no_cache = 1`:

The built bundle uses FIXED filenames — `frontend.js` and `assets/index.css` —
because this page and the desk page hardcode those paths. Nginx sends no
`Cache-Control` for them, so browsers fall back to heuristic caching and happily
serve yesterday's JavaScript after a deploy. That is not theoretical: a copy
rewrite shipped, the server served the new file with a fresh ETag, and the
browser kept showing the old text.

So we stamp `?v=<build>` on both, derived from the bundle's modification time.
A rebuild changes the mtime, which changes the URL, which forces a refetch —
while unchanged builds keep their URL and stay cached.

Lazy-loaded chunks are handled differently: vite content-hashes them
(`chunks/[name]-[hash].js`) and rewrites the imports inside the entry bundle on
every build, so they bust themselves.
"""

import os

import frappe

# Path of the built entry bundle, relative to the app's public/ directory.
_BUNDLE = "frontend/frontend.js"


def _build_version() -> str:
	"""Short, stable token that changes whenever the bundle is rebuilt."""
	try:
		path = frappe.get_app_path("portal_app", "public", *_BUNDLE.split("/"))
		return str(int(os.path.getmtime(path)))
	except Exception:
		# Never break the page over a cache-busting nicety.
		return frappe.utils.get_build_version()


def get_context(context):
	# context.no_cache governs FRAPPE's server-side website cache (the X-From-Cache
	# header). It says nothing to the browser — verified: this page came back with no
	# Cache-Control header at all, so browsers applied heuristic caching to the HTML,
	# kept requesting the OLD ?v=, and the asset cache-busting below never got a
	# chance. A deploy then looked like it had not happened.
	# Browser cache headers are NOT set here. frappe.local.response is the API
	# response dict and writing headers onto it from a website page silently does
	# nothing — verified: the response still came back with no Cache-Control. The
	# real hook is after_request (see portal_app.utils.set_spa_no_cache), which is
	# handed the actual response object by frappe/app.py.
	context.no_cache = 1
	context.build_version = _build_version()
	return context
