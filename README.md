### ATA Project Portal (`portal_app`)

A custom Frappe app for **ERPNext v15**. It adds the ATA Project Portal, a web app at **`/portal-app`** for projects, tasks, planning views, a standard project folder tree, file sharing and a client portal. Everything is stored in normal ERPNext records such as Project, Task, File, Customer and User.

### Documentation

**Start with [DOCUMENTATION.md](./DOCUMENTATION.md).** It has an overview, a list of every feature and the key addresses.

| Document | For whom | Hosted copy on the site |
|---|---|---|
| [DOCUMENTATION.md](./DOCUMENTATION.md) | Everyone. Start here. | — |
| [USER_GUIDE.md](./USER_GUIDE.md) | Staff and client users | `/handbook` (public, no login) |
| [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) | People who maintain the portal: how it works with ERPNext, the API, build and deploy | `/tech-guide` (login, System Managers only) |
| [TESTING.md](./TESTING.md) and [docs/UAT_TEST_GUIDE.md](./docs/UAT_TEST_GUIDE.md) | Testers | `/test-guide` (login, System Managers only) |

> **Warning:** this repository and `/handbook` are public. Never commit passwords, API keys, server addresses, test logins or real client names.

### Requirements

- Frappe and ERPNext v15 on a bench. The app lists `erpnext` as a required app.
- Node 22 (see `frontend/.nvmrc`) and yarn, to build the portal screens.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench --site <site> install-app portal_app
bench build --app portal_app
```

`bench build --app portal_app` also runs the `build` script in the app's root `package.json`, which builds the Vue screens into `portal_app/public/frontend`. That folder is **not** stored in git, so it has to be built on every server.

Installing (and every `bench migrate`) adds the portal's custom fields to Project, Department, User, Event and File. It also creates the **Portal Customer** role, adds the default file types and imports the Desk workspace **Project Portal**.

### Updating a site

1. `cd apps/portal_app && git pull`
2. Build the screens with Node 22 (for example through nvm): `cd frontend && yarn build`. Run `yarn install` first if `frontend/package.json` changed.
3. Check what changed: `git diff --name-only ORIG_HEAD HEAD`. If the list has a DocType JSON, `install.py`, `patches.txt` / `patches/`, `fixtures/`, or a change to `scheduler_events`, `fixtures` or `after_migrate` in `hooks.py` (check with `git diff ORIG_HEAD HEAD -- portal_app/hooks.py`), you must migrate. Only `bench migrate` syncs fixtures and scheduled jobs and runs the `after_migrate` hook; `clear-cache` does none of these:
   1. Take a backup first: `bench --site <site> backup --with-files`.
   2. `bench --site <site> migrate`.

   Otherwise: `bench --site <site> clear-cache`. (Full steps: [DEVELOPER_GUIDE.md §10.1](./DEVELOPER_GUIDE.md#101-deploy-a-change).)
4. `bench --site <site> clear-website-cache`
5. Reload the web and background workers: `bench restart`, or send a QUIT signal to the gunicorn and worker processes through `supervisorctl`.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/portal_app
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

Automated tests live in `portal_app/tests/`. Run them on a **test site** that has tests allowed, never on production:

```bash
bench --site <test-site> run-tests --app portal_app
```

### License

agpl-3.0
