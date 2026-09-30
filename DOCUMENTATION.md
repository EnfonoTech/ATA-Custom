# ATA Project Portal — Start here

This page is the front door to the documentation. It tells you what the portal is, which guide to read, what features exist and where to find them.

---

## What the portal is

The **ATA Project Portal** is a web app for ATA's architecture projects.

- It runs on the company's **ERPNext v15** site. ERPNext is the business system that holds the real records. ERPNext is built on **Frappe**, a framework for business apps.
- The portal is a Frappe **app** called `portal_app`. An app is a package of extra code installed on the site.
- The screens are a **Vue single-page app** (SPA: one web page that changes screens without reloading). It lives at **`/portal-app`**.
- The portal has **no separate database**. It stores its data in the ERPNext site: mostly standard ERPNext records (listed below), plus a few DocTypes (tables) of its own: Portal User Customer, Portal Folder Share, Portal Project Settings, Portal Folder Route Rule, Portal File Type and Portal Demo Seed Run. The standard records are:
  - each project is an ERPNext **Project**;
  - each document is an ERPNext **File** attached to that project;
  - each folder is also a **File** record, marked as a folder, under `Home/Attachments/<project ID>/…`. Folders are not attached to the Project. The portal finds them by their path;
  - each project team member is a row in the project's **Users** table;
  - each client company is an ERPNext **Customer**.
- **Staff** use the portal to plan projects, keep documents in a standard folder tree and share them.
- **Client contacts** sign in to see their own projects. They send and receive files mainly through one folder, **06-CLIENT SUBMITTAL**. Staff can also share other files with them by name.

> **Words used in these guides**
> - **DocType** = a table/form in ERPNext (for example *Project*, *Task*, *File*).
> - **Desk** = ERPNext's normal back-office screens, at `/app`.
> - **Role** = a named set of permissions given to a user (for example *Projects User*).
> - **Staff** = any ATA login that is not a client contact (System Manager, Projects Manager, Projects User, or anyone on a project team).
>   **Careful:** DEVELOPER_GUIDE.md and `/tech-guide` use these words differently. There, **staff** means only System Managers and Projects Managers, and everyone else who is not a client is an **internal user**.
> - **Manager** = a user with the System Manager or Projects Manager role. A Lead Architect or a team lead is not a manager unless they also have one of these roles.
> - **Edit rights on a project** = you are a manager, or you are on that project's project team. Being in a Portal Team does not count. Client contacts never have edit rights.
> - **Client contact** = a login with the *Portal Customer* role and no System Manager or Projects Manager role. A manager role always wins; a Projects User role does not.
> - **Everyone** (in the tables below) = every signed-in portal user, client contacts included.
> - **Website User** = a login with no access to Desk. Client contacts are Website Users.
> - **Assign To** = Desk's way of giving a record to a person. It creates a *ToDo* for them.
> - **Project team** = the people in a project's *Users* table. Being on it gives a Projects User edit rights on that project.
> - **Portal Team** = a group of staff in one office, stored as an ERPNext *Department*. The Teams page, the Org Chart and the Gantt chart use it. It gives **no** access to any project.
> - **Department** = the ERPNext record that holds a Portal Team.
> - **Lead Architect** = the person in a project's *Portal Project Manager* field. It is a field, not a role. Some error messages call it the "portal project manager".
> - **Kanban** = a board with one column per project stage. **Gantt chart** = a timeline of projects and milestones.
> - **Webhook URL** = the web address the portal sends a file to when it also stores the file on an external drive.
> - **Scheduler** = the site's background timer. It sends queued emails and, once an hour, switches off shares that have expired. If it is off, no email goes out and no share expires.
> - **Error Log** / **Email Queue** = Desk lists of background errors and of emails waiting to be sent.
> - **`bench migrate`** = the server command that applies app updates to the site.

---

## Which document do I need?

| I want to… | Read this file | Hosted page on the site |
|---|---|---|
| Use the portal day to day (staff or client contact) | [USER_GUIDE.md](./USER_GUIDE.md) | **`/handbook`**. Public, no login needed. |
| Use the portal as a client contact | [USER_GUIDE.md → 22. For clients](./USER_GUIDE.md#22-for-clients-how-to-use-the-portal) | `/handbook` |
| Give a client access to their projects | [USER_GUIDE.md → 23. Giving a client access, end to end](./USER_GUIDE.md#23-for-ata-staff-giving-a-client-access-end-to-end) | `/handbook` |
| Take a client's access away | [USER_GUIDE.md → 23.11 Removing access](./USER_GUIDE.md#2311-removing-access) | `/handbook` |
| A staff member joins, changes role or leaves | [USER_GUIDE.md → 20.4 Staff joining, changing role or leaving](./USER_GUIDE.md#204-staff-joining-changing-role-or-leaving) | `/handbook` |
| Look after, fix or extend the portal, or understand how it works with ERPNext | [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) | **`/tech-guide`**. Needs a login. System Managers only. |
| Test the portal before handover (UAT = user acceptance testing) | [TESTING.md](./TESTING.md) (a quick walk through every screen) and [docs/UAT_TEST_GUIDE.md](./docs/UAT_TEST_GUIDE.md) (the full test script) | **`/test-guide`**. Needs a login. System Managers only. |
| Hand the site over to ATA | [DEVELOPER_GUIDE.md → 10.10 Before handing over a site](./DEVELOPER_GUIDE.md#1010-before-handing-over-a-site) | `/tech-guide` |
| Fix something that is not working | 1. [Known issues in this release](#known-issues-in-this-release) (this page)<br>2. [USER_GUIDE.md → 27. Known issues and workarounds](./USER_GUIDE.md#27-known-issues-and-workarounds) and [28. FAQ and troubleshooting](./USER_GUIDE.md#28-faq-and-troubleshooting)<br>3. [DEVELOPER_GUIDE.md → 10. Operations runbook](./DEVELOPER_GUIDE.md#10-operations-runbook) | `/handbook`, `/tech-guide` |
| Install the app on a site, or update it | [README.md](./README.md), then [DEVELOPER_GUIDE.md → 10.0 Installing on a new site](./DEVELOPER_GUIDE.md#100-installing-on-a-new-site) | — |
| Deploy a change, roll it back, or upgrade Frappe/ERPNext | [README.md → Updating a site](./README.md#updating-a-site), [DEVELOPER_GUIDE.md → 10.1](./DEVELOPER_GUIDE.md#101-deploy-a-change), [Roll back a bad deploy](./DEVELOPER_GUIDE.md#roll-back-a-bad-deploy), [10.14](./DEVELOPER_GUIDE.md#1014-before-and-after-upgrading-frappe-or-erpnext) | `/tech-guide` |
| Get the big picture (this page) | [DOCUMENTATION.md](./DOCUMENTATION.md) | — |

Before you use or set up the portal, read [Important rules and limits](#important-rules-and-limits).

The old address `/user-guide` still works. It sends you to `/handbook`.

> **Warning — keep it safe.** This repository is public on GitHub, and `/handbook` can be read by anyone. Never put any of these in these documents: passwords or app passwords (including the outgoing mailbox), API keys or tokens, `site_config.json` values such as the encryption key, server IP addresses, SSH or jump-host details, test or UAT logins, real people's names or emails, or real client names. Use neutral examples such as `client@example.com`, "Customer A" or `PROJ-0001`.

---

## Who is who (roles at a glance)

| Role | Who has it | What they can see | What they can change |
|---|---|---|---|
| **System Manager** | ERP administrators | Every project, including every project's money value (estimated cost) | Everything. Only a System Manager can reset a client's password. Once a project has a Lead Architect, only a System Manager or that Lead Architect can hand it to someone else. |
| **Projects Manager** | Senior staff | Every project. Money value only on projects where they are the Lead Architect | Every project, with three limits:<br>1. They can set the **Portal Team** only on projects where they are the Lead Architect.<br>2. They can see and change the money value (**estimated cost**) only on those projects.<br>3. They cannot hand a project that has a different Lead Architect to someone else (only a System Manager can).<br>They can add an existing client login to a customer. They cannot invite a new client login unless they are allowed to create user accounts. |
| **Projects User** | Staff | Every project | **Any project:** upload and share files; delete files they uploaded; revoke shares they created; update and comment on tasks assigned to them.<br>**Projects whose project team they are on (in the portal):** edit the details, rename or delete the project, link a customer, move its stage, rename folders, delete any file, revoke any share, send a copy to the client folder (**Submit** in the File Browser), create tasks and milestones, remove client logins.<br>**Not allowed:** change the project team (unless they are the Lead Architect); add an existing client login (System and Projects Managers only) or invite a new one (System Manager by default). |
| **Portal Customer** | Client contacts (Website Users) | Only the projects of their own customer(s). On each project page they see its status, stage, dates and progress, but no tasks, no project team and no Portal Team. Among files: only **06-CLIENT SUBMITTAL**, plus anything staff shared with them by name | Nothing on projects except uploading files into 06-CLIENT SUBMITTAL (plus their own profile and password) |
| **Auditor** (add-on role) | Staff who look after the folder standard | Same as their other portal role | The company-wide folder template (**File tools**, and the folder template import on the **Admin** page) |
| **Team lead** (not an ERPNext role: the *Portal Team Lead* field on a Portal Team) | The person named as *Portal Team Lead* on a Portal Team | Their own Portal Team on the **Teams** page | Their Portal Team's name, office and members. They cannot create new teams. |

*Auditor* is an add-on role. Give it together with Projects User or Projects Manager. On its own it does not let a person sign in to the portal.

> **Warning:** Auditor is a standard ERPNext role. In Desk it also opens many accounting reports, for example Trial Balance and Profit and Loss. Give it only to people who may see those. Otherwise ask a System Manager to edit the folder template for you.

*Administrator* holds every role automatically, including Portal Customer. The portal treats it as a System Manager, but some screens act differently (header search shows no teams, for example). Check client and Projects User behaviour with real test logins of those roles, never with Administrator.

**What a Lead Architect can do on their project**

The Lead Architect of a project also gets these rights on that one project:

1. Apart from System and Projects Managers, only the Lead Architect can change who is on the project team (the **Team** card and its **Save team** button).
2. Only the Lead Architect or a System Manager can set the project's **Portal Team** (the team it is grouped under on the Gantt chart).
3. A Projects Manager sees the project's money value, and can change it, only if they are its Lead Architect.

**Who can set the Lead Architect:** only managers get a list of names in the Lead Architect picker, so in practice only they can fill it. A Projects Manager can fill it while it is empty or while they hold it. Once someone else holds it, only a System Manager can change it. To edit the project's other details, a person needs edit rights on the project. Saving other changes leaves the Lead Architect as it is.

**In practice:**

- A Lead Architect sees the Team controls only if they are also on the project team, or are a manager.
- A Lead Architect who is a Projects User sees an empty **Portal Team** list, unless they lead a Portal Team. Ask a manager to set the Portal Team.

---

## Feature overview

**Staff**, **Manager**, **Edit rights** and **Everyone** are explained in *Words used in these guides* above. The **Guide** column says where to read more: the user guide explains how to use a feature, and the developer guide explains how it works inside.

| Feature / screen | Who uses it | Where | Guide |
|---|---|---|---|
| **Getting in and your account** | | | |
| Sign in (standard ERPNext login; anyone without portal access is signed out again). **Forgot Password?** opens ERPNext's standard password reset. Use it if you never set a password. | Everyone | `/portal-app/login` | [User](./USER_GUIDE.md#3-signing-in-and-your-account) · [Developer](./DEVELOPER_GUIDE.md#61-portal_appapiauth) |
| Profile: name, mobile, language, time zone, change password, linked customers | Everyone | `/portal-app/profile` | [User](./USER_GUIDE.md#3-signing-in-and-your-account) |
| Top bar: search for projects (staff also get tasks and teams) with Ctrl/⌘ + K, notifications bell, light/dark mode, colour theme, **New Project** button (it opens the create form only for people allowed to create projects), avatar menu (**Profile**, **Switch to Desk**, **Logout**). Ctrl/⌘ + B folds the side menu. | Everyone | Every page | [User](./USER_GUIDE.md#4-finding-your-way-around) |
| Coming Soon page: a placeholder for modules that are not built yet (the Dashboard's **Total Team Members** card opens it) | Everyone | `/portal-app/coming-soon` | — |
| **Projects and planning** | | | |
| Dashboard: headline numbers, milestones, recent activity | System Manager, Projects Manager | `/portal-app/dashboard` | [User](./USER_GUIDE.md#5-dashboard-managers) · [Developer](./DEVELOPER_GUIDE.md#69-portal_appapidashboard) |
| Projects list: Year / Cards / Table views, search, status filter, print. Create, edit, delete and assign a Lead Architect (needs rights) | Everyone. Clients see only their customers' projects | `/portal-app/projects` | [User](./USER_GUIDE.md#6-projects-list) · [Developer](./DEVELOPER_GUIDE.md#63-portal_appapiprojects--projects-tasks-teams-customers-client-logins) |
| Project page: rename, link a customer, project team members, **Portal Team** (the team the project is grouped under on the Gantt chart), files, tasks | Anyone who can open the project. Changes need edit rights. Client contacts do not see the Team, Portal Team or Tasks cards | `/portal-app/projects/<ID>` | [User](./USER_GUIDE.md#7-the-project-page) · [Developer](./DEVELOPER_GUIDE.md#63-portal_appapiprojects--projects-tasks-teams-customers-client-logins) |
| Client logins (Project page → **Customer** and **Customer portal users** cards) | Staff with edit rights on the project. See [Client logins](#client-logins) for who can do each action. | Project page | [User](./USER_GUIDE.md#23-for-ata-staff-giving-a-client-access-end-to-end) · [Developer](./DEVELOPER_GUIDE.md#65-customer-portal-flows-in-plain-steps) |
| Kanban: see projects by stage. Moving a project needs edit rights on it | Staff | `/portal-app/kanban` | [User](./USER_GUIDE.md#8-kanban-board) |
| Gantt Chart & Milestones | Staff | `/portal-app/gantt` | [User](./USER_GUIDE.md#9-gantt-chart-and-milestones) · [Developer](./DEVELOPER_GUIDE.md#610-portal_appapigantt) |
| Calendar of project and task dates | Staff | `/portal-app/calendar` | [User](./USER_GUIDE.md#10-calendar) |
| Tasks: filter, edit in the list, comments, quick create (creating a task needs edit rights on the project; **Assign to** lists staff logins only) | Staff | `/portal-app/tasks` | [User](./USER_GUIDE.md#11-tasks) · [Developer](./DEVELOPER_GUIDE.md#63-portal_appapiprojects--projects-tasks-teams-customers-client-logins) |
| Daily Task: a personal 4-week reminder board | Staff. Managers can also add reminders for someone else (see [Projects and teams](#projects-and-teams)) | `/portal-app/daily-task` | [User](./USER_GUIDE.md#12-daily-task-personal-reminders) |
| Contracts: contract documents, stored in their own folder apart from the project folders. See [Files and uploads](#files-and-uploads) for who sees their names. | **Contracts page:** System Manager, Projects Manager.<br>**A project's contracts:** managers list, upload, delete and download them on the Contracts page. Anyone else with edit rights on the project, a Projects User on its project team included, sees and opens them on the Shares page.<br>**In Desk** they are ordinary Project attachments: any staff member who can open the Project in Desk can open them. | `/portal-app/contracts` | [User](./USER_GUIDE.md#17-file-tools-routing-rules-and-contracts) · [Developer](./DEVELOPER_GUIDE.md#612-portal_appapicontracts) |
| ATA AI Chat: answers simple questions (counts, lists, budgets) from live data. It matches keywords; it is not a real AI | Staff (see [Projects and teams](#projects-and-teams) for client contacts) | `/portal-app/ai-chat` | [User](./USER_GUIDE.md#21-ata-ai-chat) · [Developer](./DEVELOPER_GUIDE.md#613-portal_appapiai_chat) |
| **Files and sharing** | | | |
| Files hub: pick a project and folder, upload files, a whole folder or a ZIP, rename folders (needs edit rights), delete (edit rights, or your own uploads), download several files as a ZIP, share. | Staff. Clients see 06-CLIENT SUBMITTAL only and can upload into it | `/portal-app/files` | [User: uploading](./USER_GUIDE.md#14-uploading-files) · [User: files](./USER_GUIDE.md#15-working-with-files-files-hub-and-file-browser) · [Developer](./DEVELOPER_GUIDE.md#64-portal_appapifiles--folders-uploads-downloads-sharing) |
| File type: each upload can carry a file type from the **Portal File Type** list. The portal picks one from the file extension, and you can change it before you upload. | Staff | Files hub, and the **Files** card on a project page | [User](./USER_GUIDE.md#14-uploading-files) · [Developer](./DEVELOPER_GUIDE.md#46-portal-file-type) |
| File Browser: browse by year, project and folder. **Submit** (it opens *Submit to Client*) copies a file into the project's 06-CLIENT SUBMITTAL folder as `NN_<today>_<file name>`, so the project's client contacts can see the copy. Check the project before you click it. | Everyone (clients see their folder only). **Submit** needs edit rights on the project. **Share** works for any staff member. Client contacts see neither button | `/portal-app/file-browser` | [User](./USER_GUIDE.md#15-working-with-files-files-hub-and-file-browser) |
| Shared: everything shared with you, your team projects and your own uploads | Everyone | `/portal-app/shared-with-me` | [User](./USER_GUIDE.md#16-sharing-files-and-folders) |
| Shares: check and revoke every share on projects you have edit rights on | Users with edit rights on at least one project | `/portal-app/manage-shares` | [User](./USER_GUIDE.md#16-sharing-files-and-folders) · [Developer](./DEVELOPER_GUIDE.md#510-sharing-model) |
| Public share link: view and download a shared folder without logging in | Anyone who has the link | `/portal-app/shared-folder?token=…` | [User](./USER_GUIDE.md#16-sharing-files-and-folders) · [Developer](./DEVELOPER_GUIDE.md#510-sharing-model) |
| Routing rules: copy uploads into a second folder automatically. See [Files and uploads](#files-and-uploads). | Page: users with edit rights on at least one project. Saving: System Manager, Projects Manager | `/portal-app/folder-rules` | [User](./USER_GUIDE.md#17-file-tools-routing-rules-and-contracts) · [Developer](./DEVELOPER_GUIDE.md#93-folder-route-rules) |
| File tools: edit the company-wide folder template for new projects | Auditor, System Manager | `/portal-app/file-tools` | [User](./USER_GUIDE.md#17-file-tools-routing-rules-and-contracts) · [Developer](./DEVELOPER_GUIDE.md#92-folder-template) |
| **Teams and administration** | | | |
| Teams: Portal Team cards; create teams, rename them, change their office, add and remove members | **Create teams:** System Manager, Projects Manager. **Edit a team:** those managers, or the team lead for their own team only. | `/portal-app/teams` | [User](./USER_GUIDE.md#18-teams) · [Developer](./DEVELOPER_GUIDE.md#66-portal_appapiteams) |
| Org Chart: Portal Teams drawn as a tree. Managers can also rename a team, change its office and add or remove members from here | System Manager, Projects Manager | `/portal-app/org-chart` | [User](./USER_GUIDE.md#19-org-chart) |
| Admin: create portal users, run and delete demo data, import the folder template (from a ZIP or by picking a folder) | See [Admin and setup](#admin-and-setup) | `/portal-app/admin` | [User](./USER_GUIDE.md#20-admin-page) · [Developer](./DEVELOPER_GUIDE.md#67-portal_appapiportal_admin) |
| **Inside ERPNext (Desk and background)** | | | |
| Desk workspace **Project Portal**: shortcuts and links to every portal DocType | Desk users | `/app/project-portal` | [Developer](./DEVELOPER_GUIDE.md#49-desk-page-portal_app-and-workspace-project-portal) |
| Desk page **Portal App** (`/app/portal_app`) and the **Project Portal** tile on `/apps` open the same portal | Desk users | Desk | [Developer](./DEVELOPER_GUIDE.md#49-desk-page-portal_app-and-workspace-project-portal) |
| Portal Project Settings: logo and name, who may create projects, folder template, optional external-drive upload settings (Frappe Drive, Google Drive and BIM 360 webhook URLs), client welcome text | System Manager | Desk → **Portal Project Settings** | [Developer](./DEVELOPER_GUIDE.md#91-portal-project-settings) |
| **Portal User Customer**: which client login may see which customer. Add and remove customers from the project page instead (see [Client logins](#client-logins)). | System Manager | Desk → **Portal User Customer** | [Developer](./DEVELOPER_GUIDE.md#41-portal-user-customer) |
| **Portal File Type**: the file types offered when uploading, picked from the file extension | System Manager (Projects Manager and Projects User can read) | Desk → **Portal File Type** | [User](./USER_GUIDE.md#14-uploading-files) |
| **Portal Folder Share**: a record of every share and public link | System Manager, Projects Manager | Desk → **Portal Folder Share** | [Developer](./DEVELOPER_GUIDE.md#42-portal-folder-share) |
| **Portal Folder Route Rule**: the routing rules | System Manager (Projects Manager can read) | Desk → **Portal Folder Route Rule** | [Developer](./DEVELOPER_GUIDE.md#47-portal-folder-route-rule) |
| **Portal Demo Seed Run**: demo data batches that can be deleted again | System Manager | Desk → **Portal Demo Seed Run** | [Developer](./DEVELOPER_GUIDE.md#48-portal-demo-seed-run-and-portal-demo-seed-item) |
| Files uploaded by clients are tagged **Client Upload** in Desk and show a **Client upload** badge in the portal's file lists | Staff | Desk → File list, filter by tag; portal file lists | [User](./USER_GUIDE.md#15-working-with-files-files-hub-and-file-browser) |
| Desk **Assign To** on a Project keeps the project team up to date (and the other way round). It never adds a client contact to a team | Background | Desk → Project form | [Developer](./DEVELOPER_GUIDE.md#33-hookspy-entry-by-entry) |
| Client contacts are sent to `/portal-app` after signing in or setting a password | Background | ERPNext login | [Developer](./DEVELOPER_GUIDE.md#75-where-clients-land-after-setting-a-password) |
| Removing the Portal Customer role from a User removes all their customer links and shares | Background | Desk → User form | [Developer](./DEVELOPER_GUIDE.md#59-client-access-comes-only-from-portal-user-customer) |
| Hourly job that switches off expired shares | Background | Scheduler | [Developer](./DEVELOPER_GUIDE.md#106-checking-the-hourly-share-expiry) |

---

## Where the data lives in ERPNext

| In the portal | In ERPNext |
|---|---|
| A project | A **Project** record. The extra portal fields start with `portal_`, for example the project code, Lead Architect and Kanban stage. |
| A project team member | A row in the project's **Users** table (*Project User*). It is kept in step with Desk **Assign To**. |
| A task and its comments | An ERPNext **Task**. Comments are **Comment** records on the Task and show on its Desk timeline. |
| A document | A **File** record attached to the Project, in the File Manager folder `Home/Attachments/<project ID>/…`. **Add files through the portal, not with the Desk form's Attach button.** A file attached in Desk goes to `Home/Attachments` with no project folder. It shows in no folder in the portal, clients never see it, and folder shares and links do not include it. |
| A folder | A **File** row with *Is Folder* ticked, under `Home/Attachments/<project ID>/…`. Folders are not attached to the project. The portal finds them by their path. |
| A file's type | The *Portal File Type* field on the File |
| A client upload | A private File in 06-CLIENT SUBMITTAL, tagged **Client Upload** |
| A contract | A private **File** attached to the Project, in `Home/Contracts/<project ID>`. Managers, and anyone with edit rights on the project (Shares page), can see its name in some portal lists, and in Desk anyone who can open the Project can open it (see [Files and uploads](#files-and-uploads)). |
| A client company | A **Customer** record |
| A client login | A **User** (Website User) with the role *Portal Customer*, plus one **Portal User Customer** row for each customer it may see. Only these rows give access. |
| A share | A **Portal Folder Share** record. A share with a named person also adds ERPNext **DocShare** rows (DocShare = Frappe's "shared with this person" record). A public link has no DocShare: it is the Portal Folder Share record plus a signed token that expires. |
| A routing rule | A **Portal Folder Route Rule** record |
| A Portal Team | A **Department** directly under *All Departments* that has a *Portal Office*. Members are **Assign To** entries on the Department. Being in a Portal Team gives no project rights at all. Staff can read every project because of their role. Edit rights on a project come from a manager role, or from being on that project's own project team (its Users table). |
| A milestone | A row in the project's *Portal Milestones* table |
| A daily reminder | A private **Event** (calendar entry) |
| A notification (the bell) | A **Notification Log** record, the same one the Desk bell uses |
| Demo data | A **Portal Demo Seed Run** record that lists everything it created |
| Portal settings | **Portal Project Settings** (a DocType with a single record) |

---

## Key URLs

| Address | What it is | Who can open it |
|---|---|---|
| `/portal-app` | The portal. Managers land on the Dashboard, everyone else on Projects. | Signed-in portal users |
| `/portal-app/login` | The portal sign-in page. Good to bookmark. | Anyone |
| `/handbook` | The illustrated user handbook | Anyone, no login |
| `/tech-guide` | The technical guide | Signed-in System Managers |
| `/test-guide` | The UAT tester guide | Signed-in System Managers |
| `/user-guide` | Old address. Sends you to `/handbook`. | Anyone |
| `/portal-app/shared-folder?token=…` | A public share link | Anyone who has the link, until it expires or is revoked |
| Desk → workspace **Project Portal** (`/app/project-portal`) | Shortcuts: Open Portal, Project, Task, Portal Project Settings, **User Guide** (opens `/handbook`), **Technical Guide** (opens `/tech-guide`). Cards: Portal Setup, Files & Sharing, Projects. | Desk users |

---

## Important rules and limits

### Projects and teams

- **Staff can open every project.** Being on a project's **project team** is what gives a Projects User edit rights on it.
- **The project-team rule applies in the portal only.** In Desk, ERPNext's standard permissions give every Projects User read, write, create, delete and share on **every** Project, and so on every file attached to a project. A staff member who can use Desk can change or delete any project there. Give Desk access only to people you trust with the whole portfolio.
- **"Allow any portal user to create projects" is on by default** in Portal Project Settings. Switch it off if only managers should create projects.
- **Desk Assign To changes project rights.**
  1. Assigning a Project to someone in Desk adds them to the project team, so they get edit rights on that project. Client contacts are never added this way.
  2. Closing or cancelling that assignment in Desk removes them from the project team again. This does not happen if they have another open assignment on the same project.
  3. If this sync fails, nobody sees a message. The only trace is an entry in Desk → **Error Log** titled "sync_project_access_from_todo failed".
- **Portal Teams need an Office.** Only Departments directly under *All Departments* that have a *Portal Office* show on Teams, the Org Chart, the Gantt and the pickers. If you clear a team's office, the team disappears from all of them.
- **Portal Team membership is an Assign To on the Department.** If a member's ToDo is closed or cancelled in Desk, they drop out of the Portal Team.
- **Team leads** are set in Desk on the Department's *Portal Team Lead* field, or when a new user is created on the Admin page (**Team Manager**). A team lead can rename their Portal Team and change its office and members, but cannot create teams.
- **Staff pages are for staff only.** Client contacts do not see Tasks, Kanban, Calendar, Gantt, Daily Task or ATA AI Chat in the menu. If they type one of those addresses, the portal sends them to the Projects page.
- **Long lists stop at 500 without a warning.** The Projects list and Kanban show at most 500 projects, and Tasks and Calendar at most 500 tasks. Use search or filters to narrow the list.
- **Header search finds projects by name or project code only.** It does not search the project ID (for example PROJ-0001), the customer or file names. To find a project by its ID, use the search box on the Projects list. To find a file, open its project in the File Browser and use its search box.
- **ERPNext rules can block a save.** A task's dates cannot be later than its project's Expected End Date: move the project's end date first. A project cannot be deleted while any task, timesheet or share record (revoked ones too) still points to it, and the Projects list then shows "Could not delete project". Setting a task to **Completed** makes ERPNext close all its assignments. The task leaves *Only my tasks* and *Assigned to you*, and an assignee who is not on the project team can no longer edit it or add comments.
- **When a manager adds a reminder for someone else, the manager still owns it.** It shows on the other person's Daily Task board, but only the manager sees it in the Desk calendar and can change or delete it there. Frappe's daily "Upcoming Events for Today" email also goes to the manager, not to the other person. Staff get that daily email for their own reminders too.

### Files and uploads

- **The client folder name must be exact.** Clients see only a folder named **`06-CLIENT SUBMITTAL`**. Some older projects use `06 - CLIENT SUBMITTAL` (with spaces), and clients cannot see those. The portal will not add a correct folder next to an old one. To fix an old project:
  1. Open the **Files** hub and pick the project. You need edit rights on it.
  2. On the `06 - CLIENT SUBMITTAL` folder, click **Rename**.
  3. Type `06-CLIENT SUBMITTAL` exactly and save.
  4. Share the folder again, and make new links. Old shares and links on it stop working.

  **Once a folder is named `06-CLIENT SUBMITTAL`, never rename it.** Clients lose it at once, and its shares and public links stop working.

  Clients see only that exact folder and what is inside it. A folder with a longer name, for example `06-CLIENT SUBMITTAL OLD`, stays hidden from them.
- **Folders are built once per project.** The portal builds the folder tree from the template only when a project has no folders yet: when a project is created in the portal, at the first portal upload, when a template import on the Admin page or in File tools is applied to that project, or when a Mirror routing rule needs a folder. Opening a project does not build it.
- **A project created in Desk has no folders.** To build them:
  1. Open the **Files** hub and pick the project.
  2. Click the **Project folder (all files)** card.
  3. Click **Use this folder for upload**.
  4. Upload one file.
- **Template changes affect new projects only.** Changing the template never adds or renames folders in existing projects. Importing a template on the Admin page or in File tools replaces the live template at once. On the Admin page, **Apply to project** says "Folders applied" but builds nothing on a project that already has folders.
- **Upload files and Upload folder put each upload in a new dated folder.**
  1. The portal makes a new sub-folder inside the folder you picked. Its name is a running number plus today's date, for example `03_2026-09-30`. When you upload one file or one folder, its name is added at the end, for example `03_2026-09-30_plan`.
  2. With **Upload files**, each file is also renamed to *file name*\_*folder name*\_*date*. For example, `plan.pdf` uploaded into `01-DOCUMENTS` becomes `plan_01-DOCUMENTS_2026-09-30.pdf`. You can change the name in the confirm box before you upload.
  3. **Upload folder** keeps the original file names and the folder's own sub-folders inside the new dated folder.

  Exceptions:
  - **Upload ZIP** and uploads by client contacts: no dated folder, no renaming.
  - **Store in = "External platform only"**: nothing is stored in the portal. **Upload files** in the Files hub makes no dated folder. **Upload folder**, and any upload from a project page, still leave an empty dated folder behind.

  The running number counts every sub-folder already in the chosen folder, standard ones included. The first upload into `01-DOCUMENTS` is therefore numbered `07`. A second upload with the same name on the same day gets `_v2`, `_v3`. If the exact same file content is already stored on the site, ERPNext may keep that file's existing name instead of the one you typed.
- **Only the Upload ZIP button unpacks a ZIP.** A ZIP that you drop in or pick with **Upload files** is stored as one file.
- **Uploads are private by default.** A private file can be opened only by a signed-in person who can open its project. Staff can open every project, so they can open every private file. Client contacts can open only files in 06-CLIENT SUBMITTAL and files shared with them by name. Client uploads are always private. If you untick **Private upload** before **Upload files** or **Upload folder**, the file is **public**. Anyone who has its web address can open it without signing in, and revoking shares does not change that. Leave the box ticked unless the file is meant for the public. (**Upload ZIP** and **Submit** in the File Browser always store private files.)
- **Some file types are blocked.** Web and program files cannot be uploaded, for example .html, .svg, .js, .exe, .php, .py and .bat. Put such a file inside a ZIP and upload the ZIP with **Upload files** (it is stored as one file). **Upload ZIP** skips blocked file types when it unpacks and reports them as failed.
- **ERPNext can block more file types.** If Desk → System Settings → *Allowed File Extensions* is filled in (one type per line, for example `PDF`), every portal upload whose type is not on that list is refused: normal uploads, files inside a ZIP, contracts, client uploads and **Submit** in the File Browser. Leave the field empty, or list every type ATA uses, including the CAD/BIM formats and `ZIP`.
- **Upload size limits.** Several limits apply, and the smallest one wins:
  1. The site's `max_file_size` setting (in the site's configuration file). If it is not set, each file can be at most **10 MB**.
  2. Desk → System Settings → *Max File Size (MB)*. If this has a smaller number than (1), the smaller number applies. Leave it empty, or set it at least as high as (1).
  3. The whole upload request: capped at `max_file_size` if it is set, otherwise at 25 MB.
  4. The web server's own upload limit.

  These limits apply to single uploads, each file inside a ZIP, contracts and **Submit** in the File Browser. A file over the limit fails with "File size exceeded the maximum allowed size…" or an "HTTP 413" error. Ask an administrator to raise the limits ([DEVELOPER_GUIDE.md → 9.10](./DEVELOPER_GUIDE.md#910-raising-the-upload-limit) and [10.7](./DEVELOPER_GUIDE.md#107-common-problems-and-fixes)). The portal's own ZIP limits (up to 2000 files or 500 MB per upload, 500 files or 500 MB per download) apply only after these.
- **External drives are optional.** In the Files hub, **Advanced options → Store in** can also send a file to Frappe Drive, Google Drive or BIM 360 / ACC. This works only when that provider is switched on in Portal Project Settings and has a webhook URL.
- **Treat each drive webhook URL like a password.** Anyone who has the URL can send files to that drive. The URLs are set in Portal Project Settings (Frappe Drive, Google Drive or BIM 360). The portal uses them only on the server and never sends them to the browser. Never put a password, key or token inside a webhook URL.
- **Routing rules run only from a project page.** They copy an upload into a second folder: either the same path in another tree (*Mirror*), or, for files of a chosen classification, a different folder (*Cross-route*). They run only when you upload from the **Files** card on a project page, not from the Files hub, **Upload ZIP**, Desk or client uploads. No rules come with the app: a manager must create them. The **Add documents mirror** button fills in the 01-DOCUMENTS → 03-BALADIYA/01-DOCUMENTS rule (Baladiya = the municipality).

  Separately from routing rules, the project-page panel also copies an upload made into a `02-CONCEPT/01-CONCEPT STUDIES/<discipline>` folder into that folder's sub-folders (except those whose name starts with `1.`). An upload into such a `1. …` folder is copied into its own sub-folders. Each copy gets its own dated folder. The copies are listed in the confirm box, and you can remove them there before you upload.
- **Who sees contracts.** They are private Files attached to the project in `Home/Contracts/<project ID>`.
  - Managers see contract **file names** in ATA AI Chat answers and in the Dashboard's Recent Activity. Other staff do not see them in AI Chat.
  - Anyone with edit rights on the project, a Projects User on its project team included, also sees the project's contract files on the **Shares** page, under *Project folder (all files)*, and can open them there.
  - Contracts never appear in the Files hub or the File Browser. They cannot be shared, and **Submit** cannot send them to the client folder.
  - The Contracts page shows only to managers. Other people with edit rights on the project see its contracts only on the Shares page.
  - In Desk, anyone who can open that Project can see and open them.

  Give contract files neutral names. Allowed types: .pdf, .doc, .docx, .jpg, .jpeg, .png.
- **Portal downloads are not in the Access Log.** Files opened from the Files hub, the File Browser, a project page, a ZIP download or a public link are sent by the portal itself and write no entry in Desk → **Access Log**. Only private files opened through ERPNext's own file links (for example from the Shared page, the Contracts page or Desk) are logged. The *opens* count on a public link is not reliable either (see [Known issues](#known-issues-in-this-release)).

### Sharing

- **Shares expire.** A share with a person lasts 30 days by default and a public link 7 days. In the Files hub share dialog you can choose any number from 1 to 365 days. A share made from the File Browser always lasts 30 days. There is no Extend button: share again with the same person to reset the date (this also makes you the owner of that share, so the person who first made it can no longer revoke it unless they have edit rights on the project), or make a new link. An hourly job switches off expired shares, so the site scheduler must be on. Access ends when the hourly job runs, so it can last up to an hour after the expiry date.
- **A public link opens every file in that folder and its sub-folders, private files included.** A link on the whole project folder also opens 01-DOCUMENTS/01-CLIENT DATA (IDs, title deeds). Use short expiries, and revoke links when you are done.
- **Always revoke from the portal** (the share dialog or the Shares page). In Desk, never delete Portal Folder Share records and never tick their **Revoked** box by hand. If you do, a share with a person keeps its DocShare rows and stays open with no end date (the hourly job skips rows already marked revoked).
- **Public links depend on the site's encryption key.** Each link carries a code made from the `encryption_key` value in the site's configuration. If that key changes, for example when the site is restored onto a new server without its old configuration, every existing public link stops working. Make new links after such a move. (Never copy the key itself into any document.)

### Client logins

For the steps in order (link the customer, invite, the client sets a password, first upload), see [USER_GUIDE.md → 23](./USER_GUIDE.md#23-for-ata-staff-giving-a-client-access-end-to-end).

**Who can do what.** Every action is on the project page, needs edit rights on the project, and needs a Customer on the project first.

| Action | Who can do it |
|---|---|
| Invite a new login (**Invite customer user**) | System Manager (or anyone allowed to create user accounts) |
| Add an existing login (**Add existing user**) | System Manager, Projects Manager, or anyone allowed to create user accounts |
| Remove a login | Anyone with edit rights on the project, including a Projects User on its project team |
| Reset a password | System Manager only |

- **Inviting.** By default the new login gets a welcome email with a link to set its own password. You may instead type a password (at least 8 characters; the site's password policy also applies) and pass it on by a safe route. If the email already has a login, that login is linked to this customer and keeps its current password. If it has never set a password, keep **Send a welcome email** ticked, or the invite is refused.
- **Only Portal User Customer rows give a client access.** The *Portal linked Customer* field on the User form is display-only. It shows one customer (the primary one) and does not control what the client sees. Use the project page (**Customer portal users** card) to add or remove a customer. The **Portal User Customer** list in Desk works only for a login that already has the Portal Customer role. A row added there gives no role, runs no staff check and sends no email. Deleting the last row there does not remove the role. **Admin → Create portal user** makes new logins only, with one customer; add more customers later from each project page.
- **The project's Customer decides which clients see it, straight away.** Linking a Customer on the project page shows the project (its 06-CLIENT SUBMITTAL folder, status, stage, dates and progress) to every client contact of that customer at once. Changing or clearing the Customer removes it from the old customer's contacts at once. Check the customer name before you click it. After a change, open the **Shares** page and revoke any shares made to the old customer's contacts on that project; they are not removed for you.
- **Removing a client login works per customer, not per project.** It removes the login's access to every project of that customer and cancels its folder and file shares there. Its other customers stay. When a login loses its last customer, it also loses the Portal Customer role, but the login itself stays enabled. To shut a client contact out completely:
  1. On a project page of each of its customers, click **Remove from portal** next to the login. This also cancels its shares.
  2. Then disable the User in Desk.

  Do it in this order. A disabled login no longer shows on the card, so you cannot remove it from its customers afterwards.
- **Removing the Portal Customer role in Desk removes every customer from that login, and its shares.** Adding the role back does not bring them back.
- **Invite only client email addresses.** The portal refuses a login that has System Manager or Projects Manager, or that is on any project team. It does **not** refuse a Projects User who is on no project team. That login gets the Portal Customer role and from then on is treated as a client, because Portal Customer wins over Projects User. To undo it, remove the customer from that login.
- **Some pickers list client logins too.** The Team card's **Add user** box, the Lead Architect list, the Teams page's **Add member** dialog and the share pickers list every enabled login, client contacts included. Check the email before you add someone. (The **Assign to** boxes on the Tasks and Daily Task pages list staff logins only. A staff login that was later given client access can still appear there, and the Tasks page refuses it with "Tasks cannot be assigned to customer portal users.")
- **The portal never puts a client contact on a project team.** **Save team** refuses a login that has client access ("Client contacts cannot be added to the project team…"), and Desk **Assign To** does not add one. A client contact who was on a project team before this update stays on it. Until they are removed, **Save team** on that project is refused with that message and names them. Click **Remove** next to them in the Team card, then **Save team** again. Closing their assignment in Desk does not remove them. If a login joins a project team *before* it gets client access, it can no longer be linked to a customer or have its password reset from a project page ("This is an internal user and cannot be linked…"), and ERPNext emails it a Project Collaboration Invitation. To undo it, remove the person from every project team (and from any Portal Team you added them to), then link them again.
- **What clients see on a project.** A client's project page shows the project's status, stage, dates and progress, the **Customer** card and the **Files** card. It shows no tasks, no project team and no Portal Team, and header search finds no tasks for them.
- **Resetting a client's password (System Manager only).** On the **Customer portal users** card, click **Reset password** and choose one:
  1. **Email them a reset link.** This needs a working outgoing Email Account.
  2. **Set a new password now.** It must be at least 8 characters and must pass the site's password policy, if one is switched on in System Settings. It signs the client out everywhere. Pass it to the client by a safe route, for example by phone, not in a plain email.
- **See who has signed in.** Each login on the card shows when it last signed in, or "Invited — hasn't signed in yet".
- **Client contacts land in the portal.** After they sign in on the normal ERPNext login page, or set a password from an email link, they are sent to `/portal-app`.

### Email

For every email the portal sends, see [USER_GUIDE.md → 25. Emails the portal sends](./USER_GUIDE.md#25-emails-the-portal-sends).

- **Emails are queued.** When the portal says an email was sent, it means the email was queued. The site's scheduler sends it within a few minutes through the outgoing **Email Account**. Both must work: the Email Account must be set up, and the scheduler must be switched on. If an email does not arrive, look in Desk → **Email Queue**.
- **Welcome and reset links expire.** How long they last is set in Desk → System Settings → *Reset Password Link Expiry Duration*. Frappe's default is 20 minutes, which is too short for welcome emails, so set it to a few days (for example 72 hours). If that field is empty, the links never expire. Each link works only once.
- **Inviting someone again does not spoil their first link.** If the person still has an unused welcome link that has not expired, the portal does not send a new one, because a new link would make the old one stop working. It sends a short "You now have access" email instead. A person who already has a password gets the same short email.
- **Share emails are optional.** When you share with a person from the Files hub, tick **Email the user when I add them** to queue a "You were granted access…" email with a link to the **Shared** page. Shares made from the File Browser never send an email.
- **ERPNext sends its own project emails.** Whenever someone is added to a project team (by **New project**, by Desk **Assign To**, or by **Save team**), ERPNext emails them a "Project Collaboration Invitation" with a link to the project in Desk.
- **Staff land on the apps screen after setting a password.** Staff who set their password from a welcome email are taken to the ERPNext apps screen (`/apps`), or to the default app if one is set in System Settings. Tell them to click the **Project Portal** tile or use `/portal-app`. Only client contacts are sent to the portal automatically.

### Admin and setup

- **Before first use, set these in ERPNext** (full list in [DEVELOPER_GUIDE.md → 10.0 Installing on a new site](./DEVELOPER_GUIDE.md#100-installing-on-a-new-site)):
  - a default **Company**. Without it, creating a project or a team fails with "Set a default Company…";
  - **Selling Settings → Default Customer Group** and **Default Territory**, which are used for customers created from the portal;
  - a default outgoing **Email Account**, and the **scheduler** switched on;
  - **System Settings → Reset Password Link Expiry Duration**. Frappe's default is 20 minutes, which is too short for welcome emails;
  - the upload size limits, if people will upload large drawings (see *Upload size limits* in [Files and uploads](#files-and-uploads));
  - leave **Two Factor Authentication** and **Force User to Reset Password** off for portal users (the portal sign-in page cannot handle them, see [Known issues](#known-issues-in-this-release));
  - at least one Portal Team: a Department under *All Departments* with a *Portal Office*.
- **Who can use the Admin page.**
  - **Create users:** people allowed to create user accounts (System Manager by default). The roles offered are Projects User, Projects Manager and Portal Customer. Two extra options: **Team Manager** makes the new user the team lead (*Portal Team Lead*) of a Portal Team you pick; only managers see it. **Super Admin** also gives the System Manager role, that is, full ERP rights; only a System Manager sees it. This form makes new logins only.
  - **Folder template import:** Auditor or System Manager. Import from a ZIP (**Upload ZIP…**) or by picking a folder on your computer (**Upload Folder…**). An Auditor does not see Admin in the menu, so they open `/portal-app/admin` by address.
  - **Demo data:** System Manager only, and only when **Allow portal demo seed** is ticked in Portal Project Settings or the site is in developer mode.
- **The built screens are not in git.** The folder `portal_app/public/frontend` is created by the build. Every install and deploy must build it (Node 22). See [README.md](./README.md).
- **Change portal fields and the workspace in the app's code, not in Desk.** Every `bench migrate` resets the portal's custom fields (for example the Kanban stage and Phase options) and the **Project Portal** workspace to what the app defines. The ten default **Portal File Types** also come back on every migrate if deleted. Edit them instead of deleting them.
- **Demo data is for test sites only.** A demo run creates real, working logins (one of them a Projects Manager), projects and files. Tick **Allow portal demo seed** only on a test site, and delete each run from the Admin page when you are done. Use only the Admin page (or a Portal Demo Seed Run) to make demo data. The older command-line seed (`portal_app.demo_seed.seed_showcase`) records nothing, so its users and projects cannot be removed automatically.
- **Before handing the site over** (full list in [DEVELOPER_GUIDE.md → 10.10](./DEVELOPER_GUIDE.md#1010-before-handing-over-a-site)):
  1. Remove the test logins. `/test-guide` shows the UAT accounts stored in the site configuration key `ata_uat_accounts`. Empty it (`bench --site <site> set-config ata_uat_accounts "[]" --parse`), run `bench --site <site> clear-website-cache`, and disable the test users in Desk.
  2. Delete every Portal Demo Seed Run from the Admin page, then untick **Allow portal demo seed**.
  3. Decide on **Allow any portal user to create projects** (it ships switched on).
  4. Check the outgoing Email Account and the reset-link expiry.
  5. Check that no webhook URL in Portal Project Settings contains a password, key or token, and that no project files are public.

---

## Known issues in this release

These bugs are in the current code. Use the workaround until they are fixed.

- **Client menu:** the avatar menu shows **Switch to Desk** to client contacts; it opens ERPNext's "not permitted" page. Clients should ignore it.
- **Sign-in:** someone who has no portal access sees "Server error. Please try again." instead of an access message. Check their roles and project teams. The **Remember me** box does nothing.
- **Two Factor Authentication / Force User to Reset Password:** the portal sign-in page cannot complete either step. If either is switched on for a user, `/portal-app/login` shows "Sign-in did not keep a session (cookies blocked or wrong site URL)…" and the user stays signed out. Leave both off for portal users, or ask those users to sign in at ERPNext's normal `/login` page instead (client contacts are then sent on to `/portal-app`). A password changed from the portal's Profile page, or set with **Reset password → Set a new password now**, also does not reset the "days since last password change" counter, so a *Force User to Reset Password* policy keeps asking. See [DEVELOPER_GUIDE.md → 9.8](./DEVELOPER_GUIDE.md#98-other-erpnext-settings-the-portal-depends-on).
- **Upload to an external drive:** with **Store in the portal and send to the external drive**, a failed drive upload still shows as a success. Check the drive, and look in Desk → **Error Log** for "External upload failed".
- **Edit Project (the pencil icon in the Projects Table view):**
  1. ERPNext works out Progress from the tasks, so the slider value does not stick (unless the project's *% Complete Method* is set to Manual in Desk).
  2. *In Progress* and *On Hold* are portal-only statuses, not real ERPNext statuses. Saving this form keeps them. Other changes to the project (for example renaming it, moving its stage, a milestone, **Save team** or a save in Desk) put it back to Open or Completed. On a project whose *% Complete Method* is Manual, those changes fail with 'Status cannot be "On Hold"…' instead: set the status to Open in this form first.
- **Team and Portal Team cards:** everyone with edit rights on the project sees **Add user**, **Remove**, **Save team** and the Portal Team picker. Saving the team works only for System Managers, Projects Managers and the project's Lead Architect. Others get "Only a Projects Manager, System Manager, or this project's own lead can manage its team." Setting the Portal Team works only for a System Manager or the Lead Architect, so a Projects Manager who does not lead the project is refused too. A Lead Architect who has no manager role must also be on the project team to see these controls.
- **Save team:** every save rebuilds the team rows, so ERPNext emails a new "Project Collaboration Invitation" to every member each time.
- **Kanban:** a column shows only when at least one project is in that stage, so you cannot move a project into an empty stage.
- **Dashboard:** "Projects Delayed" can count finished (Done) projects, "Planning" counts as At Risk, and the period drop-downs (This Month, This Week…) do not change any number. "Sales This Month" is the estimated value of projects *created* this month, not ERPNext sales. "Active Projects" counts every project, finished ones too. "Team Performance" is always empty. "Budget Utilization" shows the same portfolio average on every row. "Total Team Members" counts every enabled staff login, not Portal Team members. The side menu's **ATA Teams** count uses Employee records, and the Org Chart total counts team places (someone in two teams counts twice), so the three numbers differ.
- **Gantt:** only the current calendar year can be shown. The office filter moves projects of teams in other offices to "Unassigned to a team" instead of hiding them.
- **Shares page:** "Created by me" also shows shares that other people created.
- **Shares page, "ERPNext share" rows:** **Revoke** fails with "Could not revoke share.". These rows are shares made in Desk. Remove them in Desk, from the **Share** panel in the File's or Project's sidebar.
- **Renaming a shared folder:** existing shares and public links on that folder stop working. Share the folder again after renaming it.
- **Public link "opens" count:** it never goes above 1, so do not use it to tell how often a link was used.
- **Routing rules:** saving a rule from the portal clears its Notes. A Mirror rule always matches the source folder and everything inside it (like "starts with"), whatever match mode is chosen.
- **Teams page:** a team lead sees **Create team**, but the server refuses it. Ask a manager to create the team.
- **Admin → Create portal user → Team Manager** may fail with "No permission to share Department" for a System Manager who has no HR role, and then the user is not created (not yet confirmed on this site). Workaround: create the user without Team Manager, then add them on the Teams page and set *Portal Team Lead* on the Department in Desk.
- **Demo data in Desk:** saving a new *Portal Demo Seed Run* in Desk runs the seed at once, even when **Allow portal demo seed** is off. Only create seed runs from the Admin page, and only on a test site.

---

## Background: the original requirements

ATA's original business requirements document (BRD, version 1.0, February 2026) used to be copied at the end of this file. It lists *functional requirements* (FRs) by area: FR-PM projects, FR-TM tasks, FR-GC Gantt chart, FR-CB costing, FR-TS timesheets and FR-RA reports. Some parts are not built as portal screens (timesheets, detailed cost tracking, a report builder). Use standard ERPNext Desk for those. To read the full BRD, ask the repository owner.
