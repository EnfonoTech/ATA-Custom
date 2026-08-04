import frappe
from frappe.utils import add_days, date_diff, flt, get_first_day, nowdate

from portal_app.api import helper
from portal_app.api.projects import portfolio_dashboard


def _pct_change(curr, prev):
	"""Percent change vs `prev`. None when there's no prior baseline to compare against
	(can't express a meaningful percent change from zero)."""
	if not prev:
		return None
	return round(((curr - prev) / prev) * 100, 1)


def _planned_pct(start, end):
	"""Elapsed timeline as percent (0-100). Returns None when dates are missing."""
	if not start or not end:
		return None
	try:
		total = date_diff(str(end), str(start))
		if total <= 0:
			return None
		elapsed = date_diff(nowdate(), str(start))
		return max(0, min(100, round((elapsed / total) * 100)))
	except Exception:
		return None


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
			"team_member_count": 0,
			"recent_activity": [],
			"trends": {"projects": None, "team_members": None, "sales": None},
			"sales_this_month": 0,
			"top_projects_by_revenue": [],
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

	budget_health = {"under_80": 0, "at_risk": 0, "over_100": 0, "avg_pct": 0.0, "max_pct": 0.0}
	pct_samples = []
	# Budget health is derived from estimated_costing, so it must obey the same
	# value-visibility rule the rest of this function applies — otherwise a user who
	# is not allowed to see project values still learns them in aggregate.
	budget_visible = helper.get_value_visible_project_names()
	for p in frappe.get_all(
		"Project",
		filters={"name": ["in", budget_visible]} if budget_visible else {"name": ["in", []]},
		fields=cost_fields,
		limit_page_length=200,
	):
		budget = flt(p.get("estimated_costing"))
		spent = 0.0
		if has_purchase:
			spent += flt(p.get("total_purchase_cost"))
		if has_expense:
			spent += flt(p.get("total_expense_claim"))
		if budget <= 0:
			continue
		ratio = (spent / budget) * 100.0
		pct_samples.append(ratio)
		if ratio >= 100:
			budget_health["over_100"] += 1
		elif ratio >= 80:
			budget_health["at_risk"] += 1
		else:
			budget_health["under_80"] += 1
	if pct_samples:
		budget_health["avg_pct"] = round(sum(pct_samples) / len(pct_samples), 1)
		budget_health["max_pct"] = round(max(pct_samples), 1)

	project_fields = [
		"name", "project_name", "status", "customer",
		"expected_start_date", "expected_end_date",
		"estimated_costing", "percent_complete", "modified",
	]
	meta_proj = frappe.get_meta("Project")
	for fn in ("portal_kanban_stage", "portal_project_code", "portal_project_manager"):
		if meta_proj.has_field(fn):
			project_fields.append(fn)

	user_projects_preview = frappe.get_all(
		"Project",
		filters={"name": ["in", allowed[:10]]},
		fields=project_fields,
		order_by="modified desc",
		limit_page_length=10,
	)
	for p in user_projects_preview:
		p["planned_pct"] = _planned_pct(p.get("expected_start_date"), p.get("expected_end_date"))
		if not helper.can_view_project_value(p["name"]):
			p["estimated_costing"] = None

	team_member_count = frappe.db.count(
		"User",
		filters={
			"enabled": 1,
			"user_type": "System User",
			"name": ["not in", ["Guest", "Administrator"]],
		},
	)

	# "vs last month" trends — the only two metrics with a real historical baseline
	# (creation date). Project/task *status* isn't snapshotted anywhere, so a trend
	# for On Track / At Risk / Delayed can't be computed truthfully; those cards show
	# a share-of-total instead (see get_teams-style ratios computed on the frontend).
	cutoff = add_days(nowdate(), -30)
	projects_prev = frappe.db.count("Project", {"name": ["in", allowed], "creation": ["<=", cutoff]})
	team_prev = frappe.db.count(
		"User",
		filters={
			"enabled": 1,
			"user_type": "System User",
			"name": ["not in", ["Guest", "Administrator"]],
			"creation": ["<=", cutoff],
		},
	)
	# Sales this month / Top projects by revenue — scoped to whichever projects this
	# user may see the *value* of (System Manager: all; Projects Manager: only their
	# own assigned projects) — same rule as everywhere else cost data is shown.
	value_names = helper.get_value_visible_project_names()
	month_start = get_first_day(nowdate())
	prev_month_end = add_days(month_start, -1)
	prev_month_start = get_first_day(prev_month_end)

	sales_this_month = 0.0
	sales_last_month = 0.0
	top_projects_by_revenue = []
	if value_names:
		placeholders = ",".join(["%s"] * len(value_names))
		sales_this_month = flt(
			frappe.db.sql(
				f"SELECT SUM(estimated_costing) FROM `tabProject` WHERE name IN ({placeholders}) AND creation >= %s",
				value_names + [month_start],
			)[0][0]
			or 0
		)
		sales_last_month = flt(
			frappe.db.sql(
				# Half-open interval: `creation` is a DATETIME, so BETWEEN with a date-only
				# upper bound silently drops everything created after 00:00:00 on that day.
				f"SELECT SUM(estimated_costing) FROM `tabProject` WHERE name IN ({placeholders}) AND creation >= %s AND creation < %s",
				value_names + [prev_month_start, month_start],
			)[0][0]
			or 0
		)
		top_projects_by_revenue = frappe.get_all(
			"Project",
			filters={"name": ["in", value_names], "estimated_costing": [">", 0]},
			fields=["name", "project_name", "estimated_costing"],
			order_by="estimated_costing desc",
			limit_page_length=5,
		)
		if top_projects_by_revenue:
			max_val = max(flt(p.estimated_costing) for p in top_projects_by_revenue) or 1
			for p in top_projects_by_revenue:
				p["share_pct"] = round((flt(p.estimated_costing) / max_val) * 100)

	trends = {
		"projects": _pct_change(len(allowed), projects_prev),
		"team_members": _pct_change(team_member_count, team_prev),
		"sales": _pct_change(sales_this_month, sales_last_month),
	}

	recent_activity = []

	for f in frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Project",
			"attached_to_name": ["in", allowed],
			"is_folder": 0,
		},
		fields=["file_name", "attached_to_name", "owner", "creation"],
		order_by="creation desc",
		limit_page_length=8,
	):
		recent_activity.append({
			"type": "file",
			"title": f"Uploaded: {f.file_name}",
			"detail": f.attached_to_name,
			"user": f.owner,
			"time": str(f.creation),
		})

	for t in frappe.get_all(
		"Task",
		filters={
			"project": ["in", allowed],
			"modified": [">=", add_days(nowdate(), -14)],
		},
		fields=["name", "subject", "project", "status", "modified", "owner"],
		order_by="modified desc",
		limit_page_length=8,
	):
		recent_activity.append({
			"type": "task",
			"title": t.subject or t.name,
			"detail": t.project,
			"status": t.status,
			"user": t.owner,
			"time": str(t.modified),
		})

	recent_activity.sort(key=lambda x: x["time"], reverse=True)
	recent_activity = recent_activity[:8]

	return {
		**portfolio,
		"portal_settings": settings,
		"my_tasks": my_tasks,
		"upcoming_projects": upcoming_projects,
		"budget_health": budget_health,
		"user_projects_preview": user_projects_preview,
		"team_member_count": team_member_count,
		"recent_activity": recent_activity,
		"trends": trends,
		"sales_this_month": sales_this_month,
		"top_projects_by_revenue": top_projects_by_revenue,
	}
