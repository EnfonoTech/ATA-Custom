import frappe

from portal_app.api import helper


@frappe.whitelist()
def global_search(query):
	query = (query or "").strip()
	if len(query) < 2:
		return {"projects": [], "tasks": [], "teams": []}

	like = f"%{query}%"
	allowed_names = helper.get_allowed_project_names()

	projects = []
	if allowed_names:
		projects = frappe.get_all(
			"Project",
			filters={
				"name": ["in", allowed_names],
				"project_name": ["like", like],
			},
			fields=["name", "project_name", "status"],
			order_by="modified desc",
			limit_page_length=5,
		)
		if len(projects) < 5:
			by_code = frappe.get_all(
				"Project",
				filters={
					"name": ["in", allowed_names],
					"portal_project_code": ["like", like],
				},
				fields=["name", "project_name", "status"],
				order_by="modified desc",
				limit_page_length=5 - len(projects),
			)
			seen = {p.name for p in projects}
			projects += [p for p in by_code if p.name not in seen]

	tasks = []
	if allowed_names:
		tasks = frappe.get_all(
			"Task",
			filters={"project": ["in", allowed_names], "subject": ["like", like]},
			fields=["name", "subject", "project", "status"],
			order_by="modified desc",
			limit_page_length=5,
		)

	teams = []
	if not helper.user_is_customer_portal_user():
		teams = frappe.get_all(
			"Department",
			filters={"portal_office": ["!=", ""], "department_name": ["like", like]},
			fields=["name", "department_name", "portal_office"],
			limit_page_length=5,
		)

	return {"projects": projects, "tasks": tasks, "teams": teams}
