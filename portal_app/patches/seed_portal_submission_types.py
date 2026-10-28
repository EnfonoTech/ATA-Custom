def execute():
	"""Seed the default Portal Submission Types on existing sites (fresh sites get them
	from after_install). Insert-only, safe to run twice."""
	from portal_app.install import seed_default_submission_types

	seed_default_submission_types()
