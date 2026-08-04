import re

import frappe
from frappe import _
from frappe.utils import add_days, cint, cstr, flt, nowdate

from portal_app.api import helper


def _scoped_file_rows(allowed, since=None, limit=20):
    """Recent files, restricted to projects the caller may see.

    Never query `tabFile` unscoped — a portal user must not learn the filenames of
    projects (or of HR/accounting attachments) they have no access to.
    """
    if not allowed:
        return []
    placeholders = ",".join(["%s"] * len(allowed))
    params = list(allowed)
    date_clause = ""
    if since:
        date_clause = " AND creation >= %s"
        params.append(since)
    return frappe.db.sql(
        f"""SELECT file_name, file_size, creation FROM `tabFile`
           WHERE is_folder = 0 AND attached_to_doctype = 'Project'
             AND attached_to_name IN ({placeholders}){date_clause}
           ORDER BY creation DESC LIMIT {cint(limit)}""",
        params,
        as_dict=True,
    )


def _scoped_file_count(allowed):
    if not allowed:
        return 0
    return frappe.db.count(
        "File",
        {"is_folder": 0, "attached_to_doctype": "Project", "attached_to_name": ["in", allowed]},
    )


@frappe.whitelist()
def ask(question):
    """Query project database with natural language and return a structured answer."""
    if not helper.user_can_use_portal():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    q = cstr(question).strip()
    if not q:
        return {"answer": "Please ask me a question about your projects or files.", "data": [], "type": "text"}

    ql = q.lower()
    allowed = helper.get_allowed_project_names() or []

    # ── Project stats ─────────────────────────────────────────────────────────
    if any(k in ql for k in ["how many project", "total project", "project count", "number of project",
                               "summary of all project", "summary", "overview"]):
        if not allowed:
            return {"type": "text", "answer": "You don't have access to any projects yet."}
        placeholders = ",".join(["%s"] * len(allowed))
        rows = frappe.db.sql(
            f"SELECT status, COUNT(*) as c FROM `tabProject` WHERE name IN ({placeholders}) GROUP BY status ORDER BY c DESC",
            allowed,
            as_dict=True,
        )
        total = sum(r.c for r in rows)
        breakdown = ", ".join(f"{r.status}: {r.c}" for r in rows)
        return {
            "type": "stat",
            "answer": f"There are **{total} projects** you have access to.",
            "subtitle": breakdown or "No breakdown available.",
            "data": [{"label": r.status or "Unknown", "value": r.c} for r in rows],
        }

    # ── Active / in-progress projects ─────────────────────────────────────────
    if any(k in ql for k in ["active project", "ongoing project", "in progress"]):
        if not allowed:
            return {"type": "text", "answer": "No projects accessible."}
        placeholders = ",".join(["%s"] * len(allowed))
        rows = frappe.db.sql(
            f"""SELECT project_name, portal_project_code, status FROM `tabProject`
               WHERE name IN ({placeholders}) AND status IN ('Active','In Progress','Open')
               ORDER BY modified DESC LIMIT 15""",
            allowed,
            as_dict=True,
        )
        names = [f"{r.get('portal_project_code') or ''} {r.project_name}".strip() for r in rows]
        return {
            "type": "list",
            "answer": f"**{len(rows)} active/in-progress projects** found.",
            "data": names,
        }

    # ── Completed projects ─────────────────────────────────────────────────────
    if any(k in ql for k in ["completed project", "finished project", "done project"]):
        if not allowed:
            return {"type": "text", "answer": "No projects accessible."}
        placeholders = ",".join(["%s"] * len(allowed))
        rows = frappe.db.sql(
            f"SELECT project_name, portal_project_code FROM `tabProject` WHERE name IN ({placeholders}) AND status IN ('Completed','Done') ORDER BY modified DESC LIMIT 15",
            allowed,
            as_dict=True,
        )
        names = [f"{r.get('portal_project_code') or ''} {r.project_name}".strip() for r in rows]
        return {
            "type": "list",
            "answer": f"**{len(rows)} completed projects** found.",
            "data": names,
        }

    # ── Files uploaded recently ────────────────────────────────────────────────
    if any(k in ql for k in ["file", "upload", "document"]) and any(k in ql for k in ["recent", "last", "week", "today", "this month"]):
        days = 7
        if "today" in ql:
            days = 1
        elif "month" in ql:
            days = 30
        if not allowed:
            return {"type": "text", "answer": "You don't have access to any projects yet."}
        # nowdate() is site-timezone aware; datetime.now() would use the server's clock (usually UTC).
        since = add_days(nowdate(), -days)
        rows = _scoped_file_rows(allowed, since=since, limit=20)
        period = "today" if days == 1 else ("this month" if days == 30 else "this week")
        return {
            "type": "list",
            "answer": f"**{len(rows)} files** uploaded {period}.",
            "data": [f"{r.file_name} ({_fmt_size(r.file_size)})" for r in rows],
        }

    # ── Total files ──────────────────────────────────────────────────────────
    if any(k in ql for k in ["how many file", "total file", "file count", "number of file"]):
        c = _scoped_file_count(allowed)
        return {
            "type": "stat",
            "answer": f"There are **{c:,} files** across the projects you can access.",
            "data": [],
        }

    # ── Tasks ────────────────────────────────────────────────────────────────
    if any(k in ql for k in ["task", "todo", "pending task", "open task"]):
        if not allowed:
            return {"type": "text", "answer": "No projects accessible to count tasks."}
        placeholders = ",".join(["%s"] * len(allowed))
        rows = frappe.db.sql(
            f"SELECT status, COUNT(*) as c FROM `tabTask` WHERE project IN ({placeholders}) GROUP BY status ORDER BY c DESC",
            allowed,
            as_dict=True,
        )
        total = sum(r.c for r in rows)
        breakdown = ", ".join(f"{r.status}: {r.c}" for r in rows)
        return {
            "type": "stat",
            "answer": f"There are **{total} tasks** across your accessible projects.",
            "subtitle": breakdown or "",
            "data": [{"label": r.status or "Unknown", "value": r.c} for r in rows],
        }

    # ── Budget / cost ─────────────────────────────────────────────────────────
    if any(k in ql for k in ["budget", "cost", "contract value", "estimated", "sar", "value"]):
        value_visible = helper.get_value_visible_project_names()
        if not value_visible:
            return {"type": "text", "answer": "No budget-visible projects for your account."}
        placeholders = ",".join(["%s"] * len(value_visible))
        rows = frappe.db.sql(
            f"""SELECT project_name, portal_project_code, estimated_costing
               FROM `tabProject` WHERE name IN ({placeholders}) AND estimated_costing > 0
               ORDER BY estimated_costing DESC LIMIT 10""",
            value_visible,
            as_dict=True,
        )
        total = frappe.db.sql(
            f"SELECT SUM(estimated_costing) FROM `tabProject` WHERE name IN ({placeholders})",
            value_visible,
        )[0][0] or 0
        items = [
            f"{r.get('portal_project_code') or ''} {r.project_name}: SAR {flt(r.estimated_costing):,.2f}".strip()
            for r in rows
        ]
        return {
            "type": "list",
            "answer": f"Total estimated portfolio value: **SAR {flt(total):,.2f}**",
            "data": items if items else ["No budget data set on projects yet."],
        }

    # ── Project search by keyword ────────────────────────────────────────────
    if allowed:
        keywords = re.findall(r"\b[a-z0-9]{3,}\b", ql)
        stop = {"what","which","show","list","give","find","tell","about","project","me","the","and","for","are","is","in","of","on","with"}
        terms = [w for w in keywords if w not in stop]
        if terms and any(k in ql for k in ["find","search","show","list","which","what","projects"]):
            placeholders = ",".join(["%s"] * len(allowed))
            kw_clauses = " OR ".join("(LOWER(project_name) LIKE %s OR LOWER(IFNULL(portal_project_code,'')) LIKE %s)" for _ in terms)
            params = allowed + [f"%{t}%" for t in terms for _ in range(2)]
            rows = frappe.db.sql(
                f"SELECT project_name, portal_project_code, status FROM `tabProject` WHERE name IN ({placeholders}) AND ({kw_clauses}) LIMIT 10",
                params,
                as_dict=True,
            )
            if rows:
                names = [f"{r.get('portal_project_code') or ''} — {r.project_name} ({r.status})".strip("— ") for r in rows]
                return {
                    "type": "list",
                    "answer": f"Found **{len(rows)} projects** matching your search.",
                    "data": names,
                }

    # ── Fallback: general DB summary ─────────────────────────────────────────
    proj_count = len(allowed)
    file_count = _scoped_file_count(allowed)
    task_count = frappe.db.count("Task", {"project": ["in", allowed]}) if allowed else 0
    return {
        "type": "summary",
        "answer": "I can answer questions about your projects, files, tasks, and budgets. Here's a quick overview of your data:",
        "data": [
            {"label": "Projects",   "value": proj_count},
            {"label": "Tasks",      "value": task_count},
            {"label": "Files",      "value": file_count},
        ],
        "hint": 'Try: "How many active projects?", "Show tasks", "Find projects with Villa", "Budget overview"',
    }


def _fmt_size(n):
    try:
        n = cint(n)
        if n >= 1_048_576:
            return f"{n/1_048_576:.1f} MB"
        if n >= 1024:
            return f"{n/1024:.0f} KB"
        return f"{n} B"
    except Exception:
        return ""
