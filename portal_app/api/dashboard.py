import frappe
from frappe.utils import add_days, nowdate

from portal_app.api import helper
from portal_app.api.projects import portfolio_dashboard


@frappe.whitelist()
def get_dashboard_data():
	"""Portfolio overview + portal file settings (FR-PM-002)."""
	if frappe.session.user == "Guest":
		frappe.throw("Not allowed", frappe.PermissionError)

	allowed = helper.get_allowed_project_names()
	if not allowed:
		return {
			**portfolio_dashboard(),
			"portal_settings": helper.get_portal_settings_dict(),
			"my_tasks": [],
			"upcoming_projects": [],
			"budget_health": {"under_80": 0, "at_risk": 0, "over_100": 0},
			"user_projects_preview": [],
		}

	portfolio = portfolio_dashboard()
	settings = helper.get_portal_settings_dict()
	user = frappe.session.user

	my_tasks = frappe.get_all(
		"Task",
		filters={
			"project": ["in", allowed],
			"_assign": ["like", f'%"{user}"%'],
			"status": ["not in", ["Completed", "Cancelled"]],
		},
		fields=["name", "subject", "project", "status", "priority", "progress", "exp_end_date"],
		order_by="exp_end_date asc, modified desc",
		limit_page_length=8,
	)

	upcoming_projects = frappe.get_all(
		"Project",
		filters={
			"name": ["in", allowed],
			"expected_end_date": ["between", [nowdate(), add_days(nowdate(), 14)]],
			"status": ["not in", ["Completed", "Cancelled"]],
		},
		fields=["name", "project_name", "status", "expected_end_date", "percent_complete"],
		order_by="expected_end_date asc",
		limit_page_length=8,
	)

	project_meta = frappe.get_meta("Project")
	has_purchase = project_meta.has_field("total_purchase_cost")
	has_expense = project_meta.has_field("total_expense_claim")

	cost_fields = ["name", "estimated_costing"]
	if has_purchase:
		cost_fields.append("total_purchase_cost")
	if has_expense:
		cost_fields.append("total_expense_claim")

	budget_health = {"under_80": 0, "at_risk": 0, "over_100": 0}
	for p in frappe.get_all(
		"Project",
		filters={"name": ["in", allowed]},
		fields=cost_fields,
		limit_page_length=200,
	):
		budget = float(p.get("estimated_costing") or 0)
		spent = 0.0
		if has_purchase:
			spent += float(p.get("total_purchase_cost") or 0)
		if has_expense:
			spent += float(p.get("total_expense_claim") or 0)
		if budget <= 0:
			continue
		ratio = (spent / budget) * 100.0
		if ratio >= 100:
			budget_health["over_100"] += 1
		elif ratio >= 80:
			budget_health["at_risk"] += 1
		else:
			budget_health["under_80"] += 1

	return {
		**portfolio,
		"portal_settings": settings,
		"my_tasks": my_tasks,
		"upcoming_projects": upcoming_projects,
		"budget_health": budget_health,
		"user_projects_preview": frappe.get_all(
			"Project",
			filters={"name": ["in", allowed[:8]]},
			fields=["name", "project_name", "status", "customer", "expected_end_date"],
			order_by="modified desc",
			limit_page_length=8,
		),
	}
