"""Serves the portal single-page app at /portal-app.

The built entry bundle and its CSS are content-hashed (`frontend-<hash>.js`,
`assets/index-<hash>.css`), so every build has new URLs and nothing can be served
stale. Lazy chunks import the entry by that same hashed URL, so the browser loads
exactly one copy of the app. The current names are read from the index.html vite
writes next to the bundle.
"""

import os
import re

import frappe

_BUILT_INDEX = ("frontend", "index.html")
_FALLBACK = {"js": ["/assets/portal_app/frontend/frontend.js"], "css": ["/assets/portal_app/frontend/assets/index.css"]}
_cache = {"mtime": None, "bundle": None}


def get_bundle() -> dict:
	"""{"js": [...], "css": [...]} for the current build, re-read only when it changes."""
	try:
		path = frappe.get_app_path("portal_app", "public", *_BUILT_INDEX)
		mtime = os.path.getmtime(path)
		if _cache["mtime"] == mtime and _cache["bundle"]:
			return _cache["bundle"]
		with open(path, encoding="utf-8") as f:
			html = f.read()
		bundle = {
			"js": re.findall(r'<script[^>]+src="(/assets/portal_app/frontend/[^"]+\.js)"', html),
			"css": re.findall(r'<link[^>]+href="(/assets/portal_app/frontend/[^"]+\.css)"', html),
		}
		if not bundle["js"]:
			return _FALLBACK
		_cache.update(mtime=mtime, bundle=bundle)
		return bundle
	except Exception:
		# Never break the page over bundle discovery.
		return _FALLBACK


def get_context(context):
	# context.no_cache governs FRAPPE's server-side website cache only. Browser
	# no-store for this HTML is set in portal_app.utils.set_spa_no_cache
	# (after_request), which is what keeps the hashed bundle names fresh.
	context.no_cache = 1
	bundle = get_bundle()
	context.bundle_js = bundle["js"]
	context.bundle_css = bundle["css"]
	# The SPA reads window.csrf_token for its POSTs (frontend/src/api/index.js).
	context.csrf_token = frappe.sessions.get_csrf_token() if frappe.session.user != "Guest" else ""
	return context
