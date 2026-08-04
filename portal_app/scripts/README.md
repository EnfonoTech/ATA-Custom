# One-off maintenance scripts

These are **not** part of the application. Each was written to repair or backfill
data on a specific site at a specific moment, and each has already been run.

They previously lived in `portal_app/api/`, which is the package that holds HTTP
endpoints. None of them carried `@frappe.whitelist()`, so they were never callable
over HTTP — but putting one-shot, destructive, `print()`-using repair code in the
API namespace invites someone to whitelist it by accident.

Run only via bench, never from application code:

```bash
bench --site <site> execute portal_app.scripts.sync_department_assignments.run
```

Before running any of them again: read the source, and take a backup. They perform
bulk `db.set_value` writes across Employee and Department with no dry-run mode.

`fix_teams_proper.py` and `setup_office.py` contain a hardcoded ATA team roster
including real staff names. Treat this directory as containing personal data.
