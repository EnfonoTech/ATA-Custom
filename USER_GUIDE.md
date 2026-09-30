# ATA Project Portal — User Guide

**Last updated: 30 September 2026**

This is the complete guide to the ATA Project Portal. It is for everyone who uses it:

- **ATA staff**: System Managers, Projects Managers and Projects Users (ordinary staff).
- **Client contacts**: people at a client company who sign in to see their own projects.

The guide is written in simple English. It goes screen by screen and names the exact button to click. For each task it says **who** can do it. It also says in one or two sentences what happens **in ERPNext**, the system behind the portal.

Client contacts can go straight to [Part E, section 22](#22-for-clients-how-to-use-the-portal). That part is written for you.

> **Note.** The examples in this guide use made-up names such as `client@example.com`, "Customer A" and `PROJ-0001`. They are not real people or projects.

---

## Table of contents

**Part A — Getting started**

1. [What the portal is](#1-what-the-portal-is)
2. [Who can see and do what](#2-who-can-see-and-do-what)
3. [Signing in and your account](#3-signing-in-and-your-account)
4. [Finding your way around](#4-finding-your-way-around)

**Part B — Projects and planning**

5. [Dashboard (managers)](#5-dashboard-managers)
6. [Projects list](#6-projects-list)
7. [The project page](#7-the-project-page)
8. [Kanban board](#8-kanban-board)
9. [Gantt chart and milestones](#9-gantt-chart-and-milestones)
10. [Calendar](#10-calendar)
11. [Tasks](#11-tasks)
12. [Daily Task (personal reminders)](#12-daily-task-personal-reminders)

**Part C — Files**

13. [The standard folder tree](#13-the-standard-folder-tree)
14. [Uploading files](#14-uploading-files)
15. [Working with files: Files hub and File Browser](#15-working-with-files-files-hub-and-file-browser)
16. [Sharing files and folders](#16-sharing-files-and-folders)
17. [File tools, Routing rules and Contracts](#17-file-tools-routing-rules-and-contracts)

**Part D — Teams, admin and AI**

18. [Teams](#18-teams)
19. [Org Chart](#19-org-chart)
20. [Admin page](#20-admin-page)
21. [ATA AI Chat](#21-ata-ai-chat)

**Part E — Clients**

22. [For clients: how to use the portal](#22-for-clients-how-to-use-the-portal)
23. [For ATA staff: giving a client access, end to end](#23-for-ata-staff-giving-a-client-access-end-to-end)

**Part F — Reference**

24. [Where things live in ERPNext Desk (for administrators)](#24-where-things-live-in-erpnext-desk-for-administrators)
25. [Emails the portal sends](#25-emails-the-portal-sends)
26. [House rules](#26-house-rules)
27. [Known issues and workarounds](#27-known-issues-and-workarounds)
28. [FAQ and troubleshooting](#28-faq-and-troubleshooting)
29. [Getting help](#29-getting-help)

**Appendices**

- [Appendix A — Web addresses](#appendix-a--web-addresses)
- [Appendix B — The full standard folder list](#appendix-b--the-full-standard-folder-list)
- [Appendix C — Limits and allowed file types](#appendix-c--limits-and-allowed-file-types)

---

# Part A — Getting started

## 1. What the portal is

ATA keeps all its project information in **ERPNext**, a business (ERP) system. ERPNext is built on a framework called **Frappe**.

ERPNext has its own screens, called the **Desk** (the address ends in `/app`). The Desk is powerful but complex. The **portal** is a simpler set of screens on top of the same data. It is built around how ATA works day to day: projects, drawings, the standard folder tree, sharing and clients.

| | ERPNext Desk | Project Portal |
|---|---|---|
| Address | `https://<your-ERP-address>/app` | `https://<your-ERP-address>/portal-app` |
| Used for | Setting things up and administration | Daily work |
| Typical users | System Managers | All staff and client contacts |
| Examples | Roles, users, settings, email set-up, audit lists | Projects, files, sharing, tasks, clients |

The portal does **not** keep a separate copy of your data. Every project, file, share, team and reminder is a normal ERPNext record. If you change something in the portal, you see the change in the Desk, and the other way round.

What the portal does for you:

| It does this | So that |
|---|---|
| Builds the same folder tree for every project | Anyone can open any project and know where a title deed or a permit is. |
| Keeps documents private by default | Only signed-in people with access can open them. |
| Gives each client their own door | A client sees only their own company's projects, never another client's. |
| Records who did what | Every upload, share and deletion is saved against the person who did it. |

Other ways in:

- On the ERPNext **apps** screen (`/apps`) there is a **Project Portal** tile. It opens the portal.
- In the Desk there is a **Project Portal** workspace with shortcuts (see [section 24](#24-where-things-live-in-erpnext-desk-for-administrators)).
- There is also a **Portal App** page inside the Desk (`/app/portal_app`). The normal way in is still `/portal-app`.

### 1.1 Words used in this guide

| Word | Meaning |
|---|---|
| **ERPNext** | The ERP system that stores ATA's data. |
| **Frappe** | The framework ERPNext is built on. Some screens (login, password reset) are Frappe's own. |
| **Desk** | ERPNext's normal back-office screens, at `/app`. |
| **Portal** | This app, at `/portal-app`. |
| **DocType** | A type of record in ERPNext, like a table with its own form. Examples: Project, Customer, File, User. |
| **Record** | One entry of a DocType, for example one project. |
| **Role** | A group of permissions given to a user, for example "Projects User". |
| **System User** | A staff login. It can use the Desk. |
| **Website User** | A client login. It cannot use the Desk. |
| **Project team** | The people listed in the project's **Users** table in ERPNext. In the portal it is the **Team** card on the project page. |
| **Lead Architect** | The person named in the project's **Portal Project Manager** field. The portal calls this person the Lead Architect. |
| **Assign To** | ERPNext's way of assigning a record to a person. It creates a **ToDo** entry for them. |
| **DocShare** | ERPNext's "share this record with this person" entry. The portal uses it when you share a folder or file. |
| **Department** | An ERPNext record. The portal uses Departments as **teams**. |
| **Team (Teams page)** | A group of staff in one office. In ERPNext it is a Department. It does NOT give access to any project. |
| **Portal Team** | The one team a project is filed under, so the Gantt chart can group projects. |
| **Kanban stage** | ATA's working stage for a project: Planning, Active, On Hold, Review or Done. |
| **Portal code** | ATA's own project number, for example 2601. It is different from the Project ID (PROJ-0001). |
| **Files hub** | The Files page for one project (side menu → **Files**). |
| **File Browser** | A page to browse files across all projects. |
| **Revoke** | Take back access that was shared. |
| **Customer** | An ERPNext record for a client company. |
| **Client contact** | A person at a client company with a portal login and the **Portal Customer** role. |
| **Client login** | The account a client contact signs in with. The screens call these **customer portal users** (for example the **Customer portal users** card and the **Invite customer user** button). They all mean the same thing. |
| **Portal Customer** | The ERPNext role every client login has. |
| **Private file** | A file that only signed-in people with access can open. |
| **Guest link** | A share link that works without a login. The **Share folder** box calls it **Anyone with the link**. The **Shares** page calls it a **Public link**. |
| **Queued email** | An email saved in ERPNext's Email Queue and sent a few minutes later by a background job. |

---

## 2. Who can see and do what

### 2.1 The roles

Your role decides which projects you see, what you can change and which menu items you get. Often, when something looks broken, it is really this table working as designed.

| Role | Who has it | Projects they see | Can change | Can upload | Sees project value |
|---|---|---|---|---|---|
| **System Manager** | ERPNext administrators | All | All projects | Yes | All projects |
| **Projects Manager** | Senior staff | All | All projects | Yes | Only projects where they are the **Lead Architect** |
| **Projects User** | Most ATA staff | All | Only projects whose **team** they are on | Yes, on any project | No |
| **Client contact** (role **Portal Customer**) | People at a client company | Only their own customers' projects, and only the **06-CLIENT SUBMITTAL** folder (unless ATA has shared something with them) | Nothing | Only into **06-CLIENT SUBMITTAL** | No |

Two extra things can be added to a person:

- **Auditor** (an ERPNext role). It lets the person edit the company-wide folder template in **File tools**. It does not open the portal by itself. The person also needs one of the roles above. Auditor is a standard ERPNext role. It also opens many accounting reports and records in the Desk, so give it only to people who may see those.
- **Team lead**. This is not a role. It is the **Portal Team Lead** field on a Department (team). A team lead can manage their own team on the **Teams** page.

> **Note.** The ERPNext **Administrator** account holds every role. The portal treats it as staff.

> **Note.** Never give one login both a staff role and **Portal Customer**. A login with **Portal Customer** and **Projects User** (but no manager role) is treated as a **client**: it sees only its linked customers' projects and only 06-CLIENT SUBMITTAL. Only **System Manager** or **Projects Manager** overrides the client role. The Admin page does not allow the combination, but the Desk does.

### 2.2 Read wide, write narrow

This is the most important rule.

- Every staff member (System Manager, Projects Manager or Projects User) can **open every project** in the practice. They can also upload to it and share from it.
- Only some people can **change** a project. For a Projects User, that means projects whose team they are on.
- Being on a **team** in the Teams page does **not** give access to any project. Only the project's own **Team** card does.
- Being on **any** project team counts as portal access. A login on a project team can sign in and read **every** project, even without a portal role. This includes someone added with **Assign To** on a Project in the Desk. Only put ATA staff on project teams. Never assign a project to a client login or an outside person.

> **Note.** The "only your team's projects" rule applies in the portal only. In the ERPNext Desk, the standard **Projects User** role can edit and delete **any** Project. Keep staff working in the portal, and give Desk access with care.

### 2.3 Who can do each task

"On the team" means the person is in the project's **Team** card (the **Users** table in ERPNext).

| Task | System Manager | Projects Manager | Projects User on the team | Projects User not on the team | Client contact |
|---|---|---|---|---|---|
| Open and read the project | Yes | Yes | Yes | Yes | Only own customers' projects |
| See the project value | Yes | Only if Lead Architect | No | No | No |
| Create a project | Yes | Yes | Yes, while the setting **Allow any portal user to create projects** is ticked (on by default) | Yes, while the setting **Allow any portal user to create projects** is ticked (on by default) | No |
| Edit, rename or delete the project | Yes | Yes | Yes | No | No |
| Move it on the Kanban board, add milestones, create tasks | Yes | Yes | Yes | No | No |
| Link a Customer to the project | Yes | Yes | Yes | No | No |
| Save the project team | Yes | Yes | Only if Lead Architect | No (the Team controls are hidden) | No |
| Set the Portal Team (Gantt grouping) | Yes | Only if Lead Architect | Only if Lead Architect **and** lead of that team on the Teams page | No | No |
| Change the Lead Architect once it names someone else | Yes | No | No | No | No |
| Upload files | Yes | Yes | Yes | Yes | Only into 06-CLIENT SUBMITTAL |
| Submit a file to the client (File Browser) | Yes | Yes | Yes | Yes | No |
| Share a folder or file, create a guest link | Yes | Yes | Yes | Yes | No |
| Rename folders, delete anyone's file, revoke anyone's share | Yes | Yes | Yes | No (only your own uploads and your own shares) | No |
| Add an existing client login to a customer | Yes | Yes | No | No | No |
| Invite a new client login | Yes | No (see note) | No | No | No |
| Remove a client login from a customer | Yes | Yes | Yes | No | No |
| Reset a client's password | Yes | No | No | No | No |
| Dashboard, Org Chart, Contracts | Yes | Yes | No | No | No |
| Teams page | All teams | All teams | Own team only, if team lead | Own team only, if team lead | No |
| Edit the company folder template (File tools) | Yes | Only with the Auditor role | Only with the Auditor role | Only with the Auditor role | No |
| Save routing rules | Yes | Yes | No | No | No |
| Admin page (create users) | Yes | No (see note) | No | No | No |

> **Note.** Inviting a new login and the Admin page need ERPNext's permission to **create Users**. In standard ERPNext only the System Manager has it.

### 2.4 The Lead Architect (Portal Project Manager)

Each project can name one **Lead Architect**. In ERPNext this is the **Portal Project Manager** field on the Project.

Being the Lead Architect does **not**, by itself, let a person change the project. It gives three things:

1. **Money.** A Projects Manager sees a project's value only when they are its Lead Architect.
2. **Team.** The Lead Architect may save the project's team.
3. **Gantt grouping.** The Lead Architect may set the project's Portal Team.

Rules for changing it:

- Anyone who can change the project may set the Lead Architect while the field is **empty**, or when it already names **themselves**.
- Once it names **someone else**, only a **System Manager** can change it.

In practice only System Managers and Projects Managers can pick a Lead Architect in the portal. The **Lead Architect** / **Select Architect** list is empty for Projects Users, so a Projects User must ask a manager. For managers the list shows every enabled login (up to 200), client logins included. Never pick a client login.

### 2.5 Who sees money

The project's value is the ERPNext field **Estimated Cost** (shown in SAR).

| Person | Sees value on |
|---|---|
| System Manager | Every project |
| Projects Manager | Only projects where they are the Lead Architect |
| Everyone else, clients included | No project |

This rule applies everywhere money appears: the Dashboard, the Projects list, the project page and ATA AI Chat. So two managers can correctly see different totals.

### 2.6 How ATA is set up today

At handover, most staff are **Projects Users**. They can open any project and upload to it, but can only change projects they are team members of. A small number of people are **Projects Managers** and **System Managers**. Client contacts see only their own company.

---

## 3. Signing in and your account

### 3.1 Signing in

**To sign in:**

1. Open `https://<your-ERP-address>/portal-app` and bookmark it.
2. In **Email / Username**, type your work email.
3. In **Password**, type your password. Click the eye button to show or hide it.
4. Click **Sign In**.

Where you land:

- System Managers and Projects Managers go to the **Dashboard**.
- Everyone else, clients included, goes to **Projects**.

Good to know:

- The **Remember me** box has no effect.
- If your login has no portal role, you are signed out again straight away. The screen then shows "Server error. Please try again." Ask your administrator to give you a portal role.

**In ERPNext:** the portal uses ERPNext's normal login. It then checks that you have a portal role (or are on a project team). If you do not, it signs you out.

### 3.2 First time: setting your password

There are two ways you get your first password.

- **You get a welcome email.** Its subject is "Welcome to …" or "Complete Registration". It has a **Complete Registration** button. Click it and choose a password.
  - Client contacts are then taken straight into the portal.
  - Staff are usually taken to the ERPNext apps screen (`/apps`), or to the default app if one is set in System Settings. Click the **Project Portal** tile, or open `/portal-app` yourself.
- **You got no email.** Some staff logins were created without a welcome email. Use **Forgot Password?** (next section) to set your first password.

> **Note.** The link in the email expires. On the ATA site it lasts **72 hours**. A System Manager sets this in the Desk under **System Settings → Reset Password Link Expiry Duration**. If it has expired, use **Forgot Password?** or ask for a new link.

### 3.3 Forgot password

**To reset your own password:**

1. On the sign-in screen, click **Forgot Password?**. This opens ERPNext's own password page.
2. Type your email and click **Reset Password**.
3. Open the email "Password Reset" and click **Reset your password**.
4. Choose a new password.

If no email arrives, see [section 28](#28-faq-and-troubleshooting).

### 3.4 Signing out

**To sign out:**

1. Click your picture or initials at the top right.
2. Click **Logout**.
3. In **Confirm Logout**, click **Logout**.

This ends your session on the server, not just on your screen. Always sign out on a shared computer.

### 3.5 Your profile

**To open your profile:** click your picture at the top right, then **Profile**. Or click **Profile** in the side menu. The page is called **Your account**.

It shows:

- Your picture or initial, name and login.
- **Roles**: your portal roles first. Click **+N more** to see the rest, and **Show fewer** to hide them.
- **Portal permissions** (only if it applies): how many projects you can manage, and whether you can edit the company folder template. Buttons **Open Files** and **File tools**.
- **Linked customer (portal)** or **Linked customers (portal)** (client contacts only): the customers whose projects you can see. It says "You only see projects of the customers listed here." This list is for information only. You cannot change it here.

**To change your details:**

1. In **Preferences**, edit **Full name**, **Mobile**, **Language** (for example `en`) or **Time zone** (for example `Asia/Riyadh`).
2. Click **Save changes**. You see "Saved."

The name in the top bar changes after you reload the page. Language and time zone must be valid ERPNext values, or the save fails with an error.

**In ERPNext:** this updates your own **User** record. You cannot change your picture here.

### 3.6 Changing your password

**To change your password:**

1. On **Profile**, go to the **Password** card.
2. Type your **Current password**.
3. Type the **New password** twice (**New password** and **Confirm new password**). Tick **Show passwords** to check what you typed.
4. Click **Change password**.

Rules:

- At least 8 characters.
- It must be different from your current password.
- The site's password policy may ask for a stronger password.
- You are signed out on all your other devices. You stay signed in on this one.

> **Note (password expiry).** If a System Manager has switched on **Force User to Reset Password** in System Settings, changing your password here does not restart that clock. When ERPNext asks for a new password, sign in once at `https://<your-ERP-address>/login` (ERPNext's own sign-in page) to set it.

### 3.7 Notifications (the bell)

The bell at the top right shows your recent ERPNext notifications. Examples: someone assigned you to a project or a team, or mentioned you. A number shows how many are unread.

- Click the bell to open the list. It shows your latest 20.
- Click **Mark all read** to clear the count.
- Click one item to mark it read and open it. A project opens its project page. A task opens the Tasks page.
- The bell checks for new items every minute.

**In ERPNext:** these are the same notifications as the bell in the Desk (the **Notification Log**).

---

## 4. Finding your way around

### 4.1 The screen layout

- **Side menu** on the left. Hide or show it with the arrow button, or press **Ctrl + B** (**Cmd + B** on a Mac). The portal remembers this in your browser.
- **Top bar** across the top.
- **Page** in the middle. Only the page scrolls; the menu and top bar stay in place.

If a page crashes you see a box "Something went wrong". Click another menu item to clear it, or reload the page.

### 4.2 The side menu for each role

| Menu group | Item | System / Projects Manager | Projects User | Client contact |
|---|---|---|---|---|
| **Project Management** | Dashboard | Yes | No | No |
| | Org Chart | Yes | No | No |
| | Projects | Yes | Yes | Yes |
| | Teams | Yes | Only if team lead | No |
| | Gantt Chart | Yes | Yes | No |
| | Tasks | Yes | Yes | No |
| | Daily Task | Yes | Yes | No |
| | Kanban | Yes | Yes | No |
| | Calendar | Yes | Yes | No |
| | Contracts | Yes | No | No |
| **AI** | ATA AI CHAT | Yes | Yes | No |
| **Team Structure** | ATA Teams (head count per team) | Yes | No | No |
| **Files** | Files | Yes | Yes | Hidden (known issue, see note) |
| | File Browser | Yes | Yes | Hidden (known issue) |
| | Shared | Yes | Yes | Hidden (known issue); open `/portal-app/shared-with-me` |
| | Shares | Yes | If on at least one project team | No |
| | Routing rules | Yes | If on at least one project team | No |
| | File tools | With Auditor role, or System Manager | With Auditor role | No |
| **Account** | Profile | Yes | Yes | Yes |
| | Admin | System Manager (see note in 2.3) | No | No |

> **Known issue (clients).** Client contacts see a **FILES** heading with no links under it. To reach files, a client opens a project and clicks **Files**. See [section 22](#22-for-clients-how-to-use-the-portal).

The **ATA Teams** block under Team Structure shows the number of active employees per team. It is for information only. Click **ATA Teams** to open or close the list. Clicking a team does nothing.

At the bottom of the menu there is a **Need Help?** card.

### 4.3 The top bar

From left to right:

| Item | What it does |
|---|---|
| Search box "Search projects, teams, tasks, documents..." | Global search. Press **Ctrl + K** (**Cmd + K**) to jump to it. See 4.4. |
| Date | Today's date (wide screens only). |
| Moon / sun button | Switch between dark and light mode. |
| Colour dot | Opens **Color Theme**: Indigo, Sky, Emerald, Rose, Amber, Brown. |
| Bell | Notifications (see 3.7). |
| **New Project** | Opens the new project form on the Projects page. If you are not allowed to create projects, it only takes you to the Projects page. |
| Your name and email | Shown for information. |
| Picture or initials | Menu with **Profile**, **Switch to Desk** and **Logout**. |

The mode, colour theme and menu state are saved **in this browser only**. They do not follow you to another computer.

**Switch to Desk** opens ERPNext's Desk. Client logins cannot use the Desk and see a "not permitted" page.

### 4.4 Global search

**To search:**

1. Click the search box (or press **Ctrl + K**).
2. Type at least 2 letters.
3. Results appear in three groups: **Projects**, **Tasks** and **Teams**, up to 5 each.
4. Click a result. A project opens its page. A task opens the Tasks page. A team opens the Teams page (people who are neither managers nor team leads go to Projects instead).
5. Press **Esc** to close the results.

What it searches:

- **Projects**: by project name or portal code. It does not search the project ID (such as `PROJ-0001`) or the customer.
- **Tasks**: by task subject.
- **Teams**: by team name. Client contacts do not get team results.
- It does **not** search files. To find a file, use the Files hub or the File Browser (section 15).

You only get results from projects you are allowed to see.

---

# Part B — Projects and planning

## 5. Dashboard (managers)

**Who:** System Managers and Projects Managers only. Others are sent to Projects.

**Where:** side menu → **Dashboard**. The page greets you with "Welcome back, <your name>".

All numbers are live from ERPNext. Money figures follow the rule in [section 2.5](#25-who-sees-money).

### 5.1 The six cards at the top

| Card | What it really counts |
|---|---|
| **Sales This Month** | The total **Estimated Cost** of projects **created** this month, for projects whose value you may see. It is not invoices or sales orders. Shows the change against last month, or "No prior-month data yet". |
| **Active Projects** | All projects you can see, of any status. Click it to open Projects. |
| **Projects On Track** | Projects whose Kanban stage is Active. |
| **Projects At Risk** | Projects whose Kanban stage is Review, On Hold or Planning. |
| **Projects Delayed** | Meant for delayed projects. See the note below. |
| **Total Team Members** | All enabled staff logins. Click it to open a "Coming Soon" page. |

> **Known issue.** ATA's Kanban stages do not include a "Delayed" stage. So **Projects Delayed** in practice counts projects in **Done** plus projects with no stage. Do not read it as "late projects".

> **Note (reading the cards after handover).**
> - When the register was loaded, every project was put in the **Planning** stage. So **Projects At Risk** starts high, until stages are set on the Kanban board (section 8).
> - **Sales This Month** uses the date a project record was created. So the month of the import shows the value of all imported projects.
> - The change shown on **Active Projects** and **Total Team Members** compares with the count 30 days ago. It shows "No prior-month data yet" while nothing is older than 30 days.

### 5.2 The panels

| Panel | What it shows |
|---|---|
| **Team Performance** | Always "No performance data" at the moment. |
| **Upcoming Milestones** | Your open tasks with due dates, plus projects ending in the next 14 days. Up to 5 items. |
| **Tasks Overview** | A donut of **your** open assigned tasks (up to 8). Because only open tasks are counted, **Completed** is always 0, and statuses other than Open and Working (for example Pending Review) show as **Overdue**. **View all tasks** opens Tasks. |
| **Recent Activity** | The latest file uploads and the tasks changed in the last 14 days. **View all** opens Projects. |
| **Project Status Overview** | A donut of On Track / At Risk / Delayed. **View all projects** opens Projects. |
| **Project Progress Summary** | Planned % (time passed) against Actual % (progress) for 5 recent projects. |
| **Top Projects by Revenue** | The 5 projects with the highest Estimated Cost that you may see. |
| **Team Structure Overview** | All teams, largest first (up to 9). |
| **Recent Projects** | 5 recent projects: name, stage, progress, budget use, value (if visible), status and due date. Click a row to open the project. |

Good to know:

- The period drop-downs (This Month, This Week, Next 30 Days and so on) change only the label. They do not change the numbers.
- **Budget Utilization** in Recent Projects is one portfolio average, repeated on every row. It is 0% if ATA does not book purchases or expense claims against projects.
- The status pill in Recent Projects uses its own grouping: Planning and Review show as **On Track** there, but count as **At Risk** in the cards.
- The **...** button on a row has no menu of its own. Clicking it opens the project, like clicking the row.

---

## 6. Projects list

**Who:** everyone. Client contacts see only their own customers' projects and no edit buttons.

**Where:** side menu → **Projects**. The page is called **Projects** with the label "Portfolio".

### 6.1 Views, search and filters

- **Year / Cards / Table**: switch the view.
  - **Year** groups projects by the year of their start date (or end date). Projects without dates go under "No Year".
  - **Cards** shows one card per project.
  - **Table** shows one row per project.
- **Print**: switches to the table and prints it as a **Project Register**, without buttons.
- Counters show "x of y projects", **Open** and **Completed**.
- **All accessible / I'm a team member / I manage**: show all projects, only the ones whose team you are on, or only the ones you can change.
- **Search name or code**: searches the project name, the project ID and the portal code.
- **All statuses / Open / Completed / Cancelled**: filter by status. Projects saved as **In Progress** or **On Hold** (section 6.5) show only under **All statuses**.

At most 500 projects are shown.

### 6.2 Table columns

| Column | Meaning |
|---|---|
| **Project** | Name and code. |
| **Assignee** | Shows the project's **Office** (despite the heading). |
| **Phase** | Schematic Design, CD, CD+, DD, TD, FC or Construction. |
| **Status** | ERPNext status. |
| **Lead Architect** | Managers only. |
| **Servers** | Badges **T**, **A** and **erp** (below). |
| **Upcoming Milestone** | The title of the next milestone from the Gantt chart (no date). It is worked out only when someone adds or removes a milestone. Once that date has passed, the column keeps showing it until the next change. If every milestone is in the past, it shows the latest one. Check the dates on the Gantt chart. |
| **Progress** | Percent complete. |
| **Actions** | Buttons (below). |

The **Servers** badges:

- **T** opens the project's Google Drive link (T-Server). Grey means not set.
- **A** opens the project's Autodesk link (A-Server). Grey means not set.
- **erp** opens a small **ERP Server** box with **Client Server** (the client link, or "(not set)") and **Project Files** (opens the Files hub for this project).

The **Actions** buttons:

- Eye **View project**: opens the project page. Clicking the row does the same. This button is on every row.

The other three buttons appear only on projects you can change:

- User-plus **Manage members**: sets the Lead Architect (6.6). It does not change the team.
- Pencil **Edit project**: opens **Edit Project** (6.5).
- Bin **Delete project**: see 6.7.

Rows with status On Hold or Cancelled look dimmed.

### 6.3 Project codes and the 2026 register

Every project has two codes:

- **Project ID**, for example `PROJ-0001`. ERPNext makes it automatically. It never changes.
- **Portal code** (the **Portal Project Code** field). This is ATA's own project number. Search uses it.

ATA's own numbers are loaded as portal codes:

- Registered projects use the year and a serial number, for example `2601`.
- Concept briefs without a number use `CB-` and a serial number, for example `CB-01`.
- Older projects keep their original numbers with the prefix `ATA-`.

### 6.4 Creating a project

**Who:** System Managers and Projects Managers. Also every staff member while the Desk setting **Allow any portal user to create projects** is ticked. It is ticked by default. Client contacts never can.

**To create a project:**

1. Click **New project** on the Projects page (or **New Project** in the top bar).
2. Fill in:
   - **Title \*** (required).
   - **Portal code**: ATA's project number.
   - **Start** and **End** dates.
   - **Phase**.
   - **Lead Architect**.
   - **Customer**: click the box to see customers, or type to filter, then click one.
3. Click **Create project**. (**Cancel** closes the form.)

The new project page opens.

**In ERPNext:** a new **Project** record is created with the next `PROJ-` number and the default company. Its Kanban stage starts as **Planning**. You are added to its team, and ERPNext emails you a "Project Collaboration Invitation". The standard folder tree is built straight away.

> **Note.** Every project title must be unique. If another project already has the same title, ERPNext refuses the save with a duplicate error. Use a different title, for example add the portal code.

### 6.5 Editing a project

**Who:** anyone who can change the project (see 2.3).

**To edit a project:**

1. On the Projects list, click the pencil **Edit project**.
2. Change what you need:
   - **Project Name**, **Office**, **Phase**, **Status**, **Lead Architect**
   - **Start Date**, **End Date**, **Progress** (slider)
   - **Estimated Cost (SAR)** (managers only)
   - **Servers (links)**: T-Server (Google Drive link), A-Server (Autodesk link), ERP Server (client server link)
   - **Remarks**
3. Click **Save Changes**.

> **Known issues with this form.**
> - **Lead Architect.** If the project's Lead Architect is someone else, only a System Manager can save this form. Others get "Only a System Manager can reassign the portal project manager." Projects Users always see the **Lead Architect** box empty; if you are the Lead Architect and save, it is **cleared**. To change only the title, use **Rename project** on the project page. For anything else, ask a System Manager or Projects Manager.
> - The **Remarks** box always opens empty. Saving the form clears any earlier remarks.
> - **Progress** is normally worked out by ERPNext from the project's tasks. The slider value is replaced, unless the project's **% Complete Method** in the Desk is set to **Manual**.
> - ERPNext itself only knows the statuses Open, Completed and Cancelled. **In Progress** and **On Hold** are saved, but the next save of the project anywhere turns them back to Open or Completed. Use the **Kanban stage** for working stages instead.
> - If the project's **% Complete Method** is **Manual**, choosing **In Progress** or **On Hold** makes the save fail with a "Status cannot be…" error.
> - Estimated Cost is ignored for people who cannot see the value.

### 6.6 Assigning the Lead Architect

**To set the Lead Architect:**

1. Click the user-plus **Manage members** button on the project row.
2. In **Assign Architect**, choose a person in **Select Architect**.
3. Click **Assign**.

The rules in [section 2.4](#24-the-lead-architect-portal-project-manager) apply. If the save is refused, nothing is shown on screen. Ask a System Manager.

If **Select Architect** is empty, you are not a manager. Ask a Projects Manager or System Manager.

### 6.7 Deleting a project

**Who:** anyone who can change the project. This includes team members.

> **Warning.** Deleting cannot be undone. Only do it for projects made by mistake. Back up first:
> - In the Files hub, clear any search and set **Subfolder filter** to **All locations**. The header tick box ticks only the rows shown.
> - Click **Download as ZIP**. One ZIP holds at most 500 files or 500 MB, so for a big project download folder by folder.
> - Contracts are not in the Files hub. Open and save each one from the **Contracts** page (System Managers and Projects Managers).
> - Open the ZIP and check that the number of files matches before you delete.

**To delete a project:**

1. Back up the files first. Follow the box above.
2. Click the bin **Delete project**.
3. Click it again within 3 seconds. The bin turns red (its tooltip says "Click again to confirm delete").

This deletes the ERPNext Project **and every file attached to it**: all uploads in its folders, client uploads and its contracts. The files are removed from the server and cannot be recovered from the portal. The empty folder tree is left behind in the File Manager.

In the Desk, every deleted project and file is listed under **Deleted Document**, with who deleted it and when. A System Manager can try to restore the Project record there, but the files themselves cannot be restored. If you delete the newest project, ERPNext gives its ID to the next project created, so old links to that ID will open the new project.

ERPNext refuses the delete if other records still point to the project: tasks, timesheets, or any share record, including shares that were already revoked. You then see "Could not delete project". So a project that was ever shared cannot be deleted from the portal. Ask a System Manager. Do not delete share records yourself (see [section 24](#24-where-things-live-in-erpnext-desk-for-administrators)).

---

## 7. The project page

**Where:** click a project on the Projects list. The address is `/portal-app/projects/<project ID>`.

**Who:** anyone who can open the project. Buttons that change things appear only for people who can change the project.

### 7.1 Header

- **Back to projects** returns to the list.
- The header shows the status, the Kanban stage, the title and the project ID.
- **Files** opens the Files hub for this project.
- **Tasks** opens the Tasks page filtered to this project.
- **Rename project** (people who can change the project): type a new title and click **Save title**. The project ID never changes.

> **Note.** Every project title must be unique. If another project already has the same title, ERPNext refuses the save with a duplicate error. Use a different title, for example add the portal code.

### 7.2 Summary cards

**Status**, **Kanban stage**, **Client**, **Timeline** (start and end dates), **Estimated cost** (managers only; shows "—" if you may not see the value) and **Progress**.

### 7.3 Customer card

This links the project to a client company (an ERPNext **Customer**). The client contacts of that customer can then see this project.

**Who can change it:** anyone who can change the project. Others see "You can view the customer link; only project managers can change it." (Here "project managers" means anyone who can change the project, team members included.)

**To link an existing customer:**

1. Click **Search customers** to see existing customers, or type part of the name.
2. Click the customer. You see "Customer linked."

**To create a new customer:**

1. Click **Create customer (no duplicate name)**.
2. In **New customer**, type the **Customer name**.
3. Click **Create or link**. If a customer with the same name already exists (capital letters ignored), it is reused. Nothing is duplicated.

**To remove the link:** click **Clear customer**.

**In ERPNext:** the project's **Customer** field is set. New customers take the **Default Customer Group** and **Default Territory** from **Selling Settings**. If those are empty, the portal uses the first Customer Group and the first Territory.

> **Warning.** Changing or clearing the customer hides the project from the old customer's client contacts at once. Folder and file shares you made for the old customer's contacts are **not** withdrawn automatically. Revoke them on the **Shares** page.

If the project has a customer and you may invite users, a box says "Give someone at <Customer> a portal login…" with the button **Invite customer user**. See [section 23](#23-for-ata-staff-giving-a-client-access-end-to-end).

### 7.4 Customer portal users card

This card appears when you can change the project **and** the project has a customer. It lists everyone who can sign in and see this customer's projects.

- **People with access**: each person shows "Last signed in <when>" or "Invited — hasn't signed in yet".
- **Invite new user** (System Managers only): create a new client login.
- **Reset password** (System Managers only).
- **Remove from portal** (anyone who can change the project): takes away this customer only. The person's other customers stay.
- **Add existing user** (System Managers and Projects Managers): search and click to add an existing client login.

Buttons you may not use are not shown.

Disabled logins are not listed, and **Add** / **Remove from portal** do not change them. Enable the login in the Desk first if you need to manage it.

The full step-by-step is in [section 23](#23-for-ata-staff-giving-a-client-access-end-to-end).

### 7.5 Portal Team (Gantt grouping) card

This puts the project under one team, so the Gantt chart can group projects by team.

**Who can save it:** a System Manager, or the project's own Lead Architect. Others get "Only a System Manager, or the project's own Portal Project Manager, can set its team."

A Projects User who is Lead Architect has two more limits:

- They see the controls only if they are also on the project's **Team**.
- The team list shows only teams they lead on the Teams page (none if they lead no team). **Create team** is refused for them. Ask a System Manager or Projects Manager.

**To set the team:**

1. Click **Search teams** to see teams, or type to filter.
2. Click a team.

Other buttons:

- **Create team (no duplicate name)** opens **New team** (**Team name**, **Office (optional)**). Click **Create and assign**. If the name already exists, the existing team is used.
- **Clear team** removes the team.

**In ERPNext:** the project's **Portal Team** field points to a **Department**.

### 7.6 Team card

The team is the list of people who can **change** this project. (Everyone on staff can already read it.)

**Who can save the team:**

- System Managers and Projects Managers: yes.
- The project's Lead Architect: yes, but only if they are also on the team. If not, ask a manager to add them first.
- Other team members: they see the controls, but saving fails with "Only a Projects Manager, System Manager, or this project's own lead can manage its team."
- Everyone else sees "View only — ask a project manager to change membership." (On this screen "project manager" means anyone who can change the project.)

**To change the team:**

1. In **Add user**, click to see users or type part of a name or email. Click a person to add them. (Pressing **Enter** adds the top match and saves.)
2. Or choose a group in **Or add a whole User Group** and click **Add group** (System Managers and Projects Managers only). The group is added and the team is saved at once.
3. Click **Remove** next to a person to take them off.
4. Click **Save team**.

> **Note.** If someone on the team has a disabled login, **Save team** fails with "User is disabled: <login>". Click **Remove** next to that person first, then **Save team**.

> **Warning.** The **Add user** search also lists client logins. Never add a client login to a project team. Such a login keeps seeing only its customers' projects, but the portal's checks then count it as internal: it can no longer be linked to another customer, and its password cannot be reset from the project page. If it later loses the **Portal Customer** role (for example when its last customer is removed), it can read **every** project and change the projects whose team it is on.

**In ERPNext:**

- The people are saved in the project's **Users** table.
- Each person also gets an **Assign To** on the project (a ToDo).
- ERPNext emails each member a "Project Collaboration Invitation".

> **Known issue.** Every **Save team** sends the "Project Collaboration Invitation" email again to every member.

> **Note.** It also works the other way. If someone assigns the project to a person in the Desk (**Assigned To** in the sidebar), that person joins the team. If the assignment is closed or cancelled (for example ticked done in their To Do list), they leave the team.

### 7.7 Files card

- **Open in Files hub** opens the Files hub for this project.
- **Staff** get an upload panel. It works like the Files hub (section 14), plus automatic copies from routing rules (section 14.10).
- **Client contacts** see "You can upload into 06-CLIENT SUBMITTAL from the Files hub." with a link.
- The file list shows each file with **Open**. A **private** tag and a **Client upload** badge appear where they apply.
- **Delete** appears for anyone who can change the project (any file), and for the person who uploaded the file (their own files). It asks you to confirm first.
- The **Share** button on the upload panel opens the share box in the Files hub for the chosen folder.

### 7.8 Tasks card

A list of the project's latest 50 tasks with their status. **Open task workspace** opens the Tasks page filtered to this project.

---

## 8. Kanban board

**Who:** staff. Only people who can change a project can move it.

**Where:** side menu → **Kanban**. The page is called **Project board**.

Each project is a card in a column for its **Kanban stage**. ATA's stages are **Planning**, **Active**, **On Hold**, **Review** and **Done**. A card shows the portal code, the name and the customer ID ("No client" if none).

**To move a project:**

- Drag its card to another column, **or**
- Choose a new stage in **Update stage** on the card.

The board reloads after each change. Click a card to open the project.

> **Known issue.** A column appears only when at least one project is in that stage. So you cannot drag a project into an empty stage (for example "Review" when no project is in Review). Change the stage from the Desk (**Portal Kanban Stage** field) instead.

**In ERPNext:** this sets the project's **Portal Kanban Stage** field. New projects start in **Planning**.

---

## 9. Gantt chart and milestones

**Who:** staff. Adding or removing milestones needs the right to change that project.

**Where:** side menu → **Gantt Chart**. The page is called **Gantt Chart & Milestones**.

### 9.1 Reading the chart

- Each project is a bar from its expected start date to its expected end date.
- The fill shows progress. Green is 80% or more, blue is 40% or more, amber is below 40%.
- A red line marks today. Red flags mark milestones.
- Projects are grouped under their **Portal Team** (section 7.5). Projects without a team are under **Unassigned to a team**.
- Only teams directly under "All Departments" that have an **Office** count. A project whose Portal Team is any other Department is shown under **Unassigned to a team**.
- "No dates set" means the project has no dates inside the period shown.

### 9.2 Controls

- **Full Year / Quarterly / Monthly**: the current year, the current quarter, or the current month (with weeks and days). You cannot move to another year.
- **All Teams**: show one team only.
- Office buttons (**ALL** and each office): show one office only. They use the office of the project's **Portal Team** (7.5), not the **Office** field on the project itself.
- **Print**: prints a clean copy.

> **Known issue.** When you pick one office, projects of teams in other offices move into "Unassigned to a team" instead of disappearing.

### 9.3 Adding and removing milestones

**To add a milestone:**

1. Click the flag icon on a project's row (**Add / manage milestones**). Or click **Milestone** at the top and pick a project in **Pick a project**.
2. In **Milestones**, under **Add a milestone**, type a title (for example "Client presentation") and pick a date. Both are required.
3. Click **Add milestone**.

**To remove a milestone:** click the bin **Remove milestone** next to it. Click **Close** when done.

To change a milestone's title or date, remove it and add it again.

People without rights get an error (usually "Could not save milestone."), because only people who can change the project (its team members, and System or Projects Managers) can change its milestones.

**In ERPNext:** milestones are saved in the project's **Portal Milestones** table. The next milestone is also copied into the project's upcoming-milestone fields, which the Projects list shows. This copy is refreshed only when a milestone is added or removed, not every day.

---

## 10. Calendar

**Who:** staff.

**Where:** side menu → **Calendar**. The page is called **Project & task timeline**.

Each project and each task is drawn on every day from its start to its end. Projects are blue. Tasks are violet.

Controls:

- **Month / Week / Agenda**: the view. Weeks start on Monday.
- **Today**, and the previous and next arrows.
- **Search**: "Title, project or task id…".
- **Type**: Projects & tasks / Projects only / Tasks only.
- **Project**: all accessible projects, or one project.
- Search matches an entry's own title or ID. Typing a project ID shows the project, but not its tasks. To see one project's tasks, pick it in **Project** instead.
- Projects and tasks with no dates are not shown.

Click any entry to open its **project** page (a task also opens its project). If a day has more than 3 entries, click **+N more** to see them all.

Gantt milestones are not shown on the calendar.

**In ERPNext:** projects use their expected dates (or actual dates). Tasks use their expected dates, then actual dates, then the closing date.

---

## 11. Tasks

**Who:** staff. (Client contacts can open this page read-only; see 11.3.) Creating a task needs the right to change at least one project. Saving a task row or commenting needs the right to change its project, or being assigned to the task.

**Where:** side menu → **Tasks**. The page is called **Tasks workspace**.

### 11.1 What you see

- Tiles **Total**, **Open** and **Overdue** (open tasks whose end date has passed).
- **Assigned to you (open)**: up to 8 of your own open tasks. Click one to open its project.
- Filters: **Search by task name or title**, **All status**, **All priority**, **Filter by project ID** (type the exact ID), **Only my tasks**, **Clear filters**.
- A table: **Task**, **Project**, **Assigned**, **Status**, **Priority**, **Progress**, **End**, **Discuss**, **Action**.

At most 500 tasks are shown.

### 11.2 Updating a task

1. On the task's row, change **Status**, **Priority**, **Progress** or the **End** date.
2. Click **Save** on that row.

Options:

- Status: Open, Working, Pending Review, Overdue, Completed, Cancelled.
- Priority: Low, Medium, High, Urgent.

ERPNext rules:

- A task's dates cannot be after the project's expected end date.
- Setting **Completed** makes progress 100% and closes the task's assignments. Three things follow:
  - The task leaves **Only my tasks**.
  - An assignee who is not on the project team can no longer change it or comment on it. They see "Only project managers or assigned users can update this task."
  - To reopen it, ask someone on the project team.

### 11.3 Comments

1. Click **Comments** on a row.
2. Type in the box and click **Send** (or press **Ctrl + Enter** / **Cmd + Enter**).

Comments can be up to 5000 characters. **In ERPNext:** they appear on the task's timeline in the Desk.

> **Clients can read task comments.** A project's client contacts can open the Tasks page from the project page (the **Tasks** and **Open task workspace** buttons). There they can read every task's title, who it is assigned to, and its **Comments**. They cannot change tasks or add comments. Write task titles and comments as if the client will read them.

### 11.4 Creating a task

1. Click **New task**.
2. Fill in **Subject \***, **Project \*** (search; only projects you can change), **Priority** and **Due date**.
3. Click **Create Task**.

The **Due date** must not be after the project's end date, or ERPNext refuses the task.

> **Known issue.** The **Assign to** box in this form is not saved. Tasks are created with nobody assigned. To assign a task, open it in the Desk and use **Assign To**.

---

## 12. Daily Task (personal reminders)

**Who:** staff. Only System Managers and Projects Managers can put a reminder on someone else's board.

**Where:** side menu → **Daily Task**.

This is a private four-week reminder board. It is not linked to projects.

- **Prev 4 Weeks** / **Next 4 Weeks** move the board. "(Current)" marks the present four weeks.
- Click a day to see its reminders on a timeline from 7:00 to 19:00.
- Dots on each day show how many reminders there are (green = done, amber = open).

**To add a reminder:**

1. Click the day, then **Task**.
2. In **Add Task**, fill in **Title**, **Time** and **Color**.
3. (Managers only) In **Assign to (optional — defaults to you)**, search for a colleague.
4. Click **Add Task**.

A reminder you put on a colleague's board is **not** on your own board. To change or remove it later, use the Desk calendar (**Event**). The **Assign to** search also lists client logins. Never pick a client login.

Other actions:

- Click the circle to mark it done or not done.
- Click the title to edit the title or time, then **Save** (or **Cancel**).
- Click **×** to delete it. There is no confirmation.
- You cannot move a reminder to another day or change its colour. Delete it and add it again.
- If a change does not stick, reload the page. Errors are not shown on screen.

**In ERPNext:** each reminder is a private **Event**. The person who creates it stays its owner. So a reminder a manager creates for you shows on **your** board, but in the Desk it belongs to the manager. ERPNext may also send the owner a daily "Upcoming Events for Today" email.

> **Known issue.** In Saudi time the dates are one day off. The **TODAY** badge appears on tomorrow's tile, and in the Desk calendar each reminder shows one day earlier. Inside the portal, a reminder stays on the tile where you added it. Go by the date labels, not by the TODAY badge.

---

# Part C — Files

## 13. The standard folder tree

### 13.1 Where files live

Every project has its own folder tree in ERPNext's File Manager:

`Home / Attachments / <project ID> / <standard folders>`

Every document is a normal ERPNext **File** record attached to the project. Contracts are kept apart, in `Home / Contracts / <project ID>` (section 17.3).

> **Note (Desk users).** Only files **attached to the Project** show in the portal.
> - **Paperclip on the Project form:** the file goes to `Home / Attachments`, not into a project folder. Staff see it with no folder card. Clients never see it. A folder ZIP leaves it out.
> - **Uploaded into a project folder in File Manager, without attaching it:** it does not appear in the portal at all.
>
> Upload through the portal instead.

### 13.2 The top-level folders and what goes where

This is the built-in ATA standard. (An Auditor or System Manager can change it; see section 17.1.)

| Folder | Use it for |
|---|---|
| **01-DOCUMENTS** | Documents about the project and the client. |
| └ 01-CLIENT DATA | The client's business card, title deed, ID, master plan, authorization letter and other client papers. |
| └ 02-LOCATION, 03-BUILDING SYSTEM, 04-DRAWINGS | Location information, building system information and drawings. |
| └ 05-CONSTRUCTION PERMIT, 06-SITE PICTURE | Permits and site photos. |
| **02-CONCEPT** | Concept design work. |
| └ 01-CONCEPT STUDIES | Studies by discipline: 01-ARCHITECTURE, 02-INTERIORS, 03-LANDSCAPE, 04-TECHNICAL, 05-OPERATIONS, 06-LIGHTNING, 07-TRAFFIC, 08-FIRE FIGHTING, 09-PROJECT RENDERS. |
| └ 02-SKETCH UP, 03-PERSPECTIVES | 3D models and perspective images. |
| └ 04-FEASIBILITY STUDY, 05-PRESENTATION | Feasibility studies and presentations. |
| └ 06-REFERENCES, 07-SCHEDULES & GUIDELINES | References (layers, survey) and schedules or guidelines. |
| **03-BALADIYA** | Municipality (Baladiya) submissions: documents, Baladiya plans, area statement. |
| **04-WORKGDRAWINGS** | Working drawings. **01-DOCUMENT TRANSMITTAL** has one folder per discipline (architectural, structural, mechanical, electrical, plumbing, survey, technical feedback, technical feasibility), each with **INCOMING** (received) and **OUTGOING** (sent) folders, except 08-TECHNICAL FEASIBILITY, which has none. |
| **05-SUPERVISION** | Site supervision: document transmittal and projects. |
| **06-CLIENT SUBMITTAL** | Everything shared with or received from the client. **This is the only folder client contacts can see.** |

The full list of 67 folder paths is in [Appendix B](#appendix-b--the-full-standard-folder-list). With parent folders counted, it makes 91 folders.

> **Note.** Some folder names are spelled exactly as they are in the system, for example **04-WORKGDRAWINGS** and **06-LIGHTNING**. Do not rename them.

> **Warning.** The client folder must be named exactly **06-CLIENT SUBMITTAL**: no spaces around the dash. Some older projects use "06 - CLIENT SUBMITTAL". Clients cannot see those folders. See [section 23.7](#237-if-the-client-cannot-see-the-folder).

> **Warning.** 01-CLIENT DATA holds IDs and title deeds. Never send a guest link to this folder or to the whole project folder.

### 13.3 When the folders are created

- **Project created in the portal**: the tree is built at once.
- **Project created in the Desk or by import**: the tree is built the first time someone uploads to it from the portal. Until then the Files hub shows only the project folder. See [section 28](#28-faq-and-troubleshooting) for how to start it.
- **Template changes** only reach projects that have no folders yet. Existing projects keep their folders. Folders are never renamed automatically.
- There is **no "New folder" button**. Extra sub-folders appear when you upload (dated upload folders), use **Upload folder** or **Upload ZIP**, or when a routing rule creates a mirror folder.

---

## 14. Uploading files

### 14.1 Where you can upload

**Who:** all staff, on any project they can open. Client contacts upload only into 06-CLIENT SUBMITTAL (see section 22).

Staff can upload from two places:

| Place | Extras |
|---|---|
| **Files hub** (side menu → **Files**) | **Upload ZIP**, drag files onto a folder card. |
| **Project page → Files card** | **Browse folders** (step by step), automatic copies from routing rules. |

### 14.2 Step 1: choose the project and the folder

1. Side menu → **Files**. The page is called **Project files**.
2. In **Active project**, type part of the project name or ID and click the project.
3. Choose the folder. Either:
   - Click a folder card (Grid) or row (Tree). It becomes the upload folder, and the page scrolls to the upload card. **Or**
   - Click the **Upload to** tile. In **Choose folder**, search or open the tree and click a folder (the box closes by itself).

The drop area always says **Goes into <folder>**. Check it before you drop files.

> **Note.** When the Files hub opens it selects the most recently changed project, and the upload folder is set to the first folder (normally 01-DOCUMENTS). The upload panel on the project page also starts on the first folder. If you drop files without choosing, they go there.

On the project page, **Browse folders** opens **Select a folder**, where you click down step by step and then **Select this folder**.

### 14.3 Step 2: upload files

1. Drag files onto the area "Drop files or a folder here, or click to upload files", **or** click it, **or** click **Upload files**.
2. The **Confirm upload** box opens. For each file you can change:
   - **File name**
   - **Category (folder)**: the destination folder
   - **Date**
   - **File type** (see 14.9)
   - **File Classification** (worked out automatically) and, for PDFs, **Document Type** (Files hub) or **PDF Type — Plan or Presentation?** (project page)
   - On the project page: **Also auto-upload to** (see 14.10)

   > **Note (project page).** Changing **File Classification** or **PDF Type** can also change **Category (folder)** to a matching first- or second-level folder (for example Presentation Files → `02-CONCEPT/05-PRESENTATION`). If nothing matches (for example Uncategorized), it jumps to the first folder, normally 01-DOCUMENTS. Check **Category (folder)** again after changing either box.

3. Click **Upload N files**. (**Cancel** stops.)

You see a message such as: Uploaded "<file>" to <folder>/<dated folder> on <date>.

**In ERPNext:** each file becomes a **File** record attached to the project, in the chosen folder.

### 14.4 Dated upload folders and automatic names

The portal keeps every upload session in its own dated folder. This keeps history tidy. **Upload files** and **Upload folder** each put the upload into a new dated folder. **Upload ZIP** and client uploads go straight into the chosen folder, with no dated folder.

- Each upload creates a **new folder** inside the folder you chose. Its name is `NN_YYYY-MM-DD`. For a single file the file name is added: `NN_YYYY-MM-DD_<file name>`.
- `NN` is the next number after the folders already there. For example, in a folder that already has 6 sub-folders, the first upload gets `07_`.
- If the same name already exists, `_v2`, `_v3` and so on are added.
- **Upload files only:** each file is renamed to `<name>_<folder>_<date>.<extension>`. (**Upload folder** keeps the original file names; see 14.5.) Spaces in the folder name become dashes, and other signs such as `&` are dropped. For example, a file `plan.pdf` in **02-TITLE DEED** becomes `plan_02-TITLE-DEED_2026-09-30.pdf`. Change the **File name** box if you want a different name.
- The **Date** box changes only the file name. The dated folder always uses today's date.
- If a file with exactly the same content is already stored on the site, ERPNext reuses that earlier file's name, so the name you typed may not be used.
- If the name is already taken by another file on the site, ERPNext adds six characters before the extension (for example `plan_02-TITLE-DEED_2026-09-30a1b2c3.pdf`).

### 14.5 Uploading a whole folder

**To upload a folder from your computer:**

1. Click **Upload folder** (or drag a folder onto the drop area).
2. Pick exactly one folder.
3. In **Confirm folder upload**, check **Folder name** (the `NN_` part is added for you) and **Upload into**. The box says "Will create <name> inside <folder>".
4. Click **Upload "<name>" (N files)**.

The whole folder, with all its sub-folders, is recreated inside the destination. Files keep their original names.

### 14.6 Uploading a ZIP (unpacked)

**Where:** Files hub only.

**To upload and unpack a ZIP:**

1. Choose the destination folder first. The upload folder starts as the first folder (normally 01-DOCUMENTS), so pick the right one and check **Goes into <folder>** before you click. **Upload ZIP** is grey only when the project has no folders yet ([section 28](#28-faq-and-troubleshooting)).
2. Click **Upload ZIP** and pick the `.zip` file.
3. Confirm the destination in the browser box.
4. Wait while it shows **Extracting…**. Then you see "ZIP extracted: N file(s) uploaded, M failed."

Good to know:

- The folders inside the ZIP are kept. If everything sits in one top folder, that top folder is dropped.
- All unpacked files are private.
- Blocked file types inside the ZIP are skipped and counted as failed. Hidden files and Mac `__MACOSX` folders are skipped silently.
- A `.zip` dragged onto the drop area or chosen with **Upload files** is stored as one ZIP file. Only the **Upload ZIP** button unpacks.
- The `.zip` itself must fit the site's upload limit. By default that is about **25 MB** for the whole ZIP, and a bigger ZIP is refused before anything is unpacked. Each file inside must be within the per-file limit (about **10 MB**), or it counts as failed. If the developer sets `max_file_size` in the site configuration, that one number becomes the limit for both. Split big ZIPs, or use **Upload folder**.
- The message shows only **how many** files failed, not which. Reload, compare the folder with your ZIP, and upload any missing files with **Upload files** to see the reason.

> **Known issue.** After a successful ZIP upload you may also see a red message "loadFilesAndFolders is not defined". The files were uploaded. Reload the page to see them.

### 14.7 Private and public

The **Private upload** box is ticked by default. **Leave it ticked.**

- **Private**: only signed-in people with access can open the file. In practice this means all staff, plus client contacts for files in 06-CLIENT SUBMITTAL or files shared with them.
- **Public**: **anyone** on the internet with the file's address can open it, with no login and no record.

Guest links and shares with named people both work with private files, so there is almost never a reason to untick the box. ZIP uploads and client uploads are always private.

> **Note.** The Files hub help box says private files can be opened only by "people on this project". In fact every staff member can open them, because staff can read every project.

### 14.8 Sending a copy to an external drive

**Advanced options** (click to open, **Hide advanced options** to close):

- **Store in**:
  - **Store in the portal only** (normal)
  - **External platform only**: the file goes only to the external drive. No copy stays in the portal.
  - **Store in the portal and send to the external drive**
- **External provider**: **Frappe Drive**, **Google Drive** or **BIM 360 / ACC**.

This works only if an administrator has switched the provider on and entered its upload address in **Portal Project Settings**. Three small cards on the Files hub show whether each provider is **Enabled** or **Not enabled**. Client uploads are never sent outside.

> **Note.** If the external copy fails in the "both" mode, the portal copy is still saved and the screen still shows success.

Good to know:

- With **External platform only**, **Upload folder** in the Files hub and every upload on the project page still create an empty dated folder in the portal (only **Upload files** in the Files hub skips it). Folders cannot be deleted from the portal. Just ignore it.
- Sending to an external drive can make the upload take up to 30 seconds longer.

### 14.9 File type and classification

- **File type** is a tag chosen from the list of **Portal File Types**: AutoCAD, PDF Document, GAD File, Document, Spreadsheet, Presentation, Image, 3D Model, Archive, Other. The portal picks one from the file extension. You can change it or choose "— Not set —".
- **File Classification** is worked out from the extension (and, for PDFs, from words in the name): Presentation Files, Drawing / Layout Files, 3D Model Files, Feasibility / Area Calculation Files, Editable Design Source Files, Rendering / Image Files, Submission Files, Uncategorized.

**In ERPNext:** the file type is saved in the File's **Portal File Type** field. A System Manager maintains the list in the Desk (**Portal File Type**).

**To add a file type** (System Manager):

1. In the Desk, open **Portal File Type** and click **New**.
2. Fill **Type name**.
3. Fill **Extensions** as a comma-separated list with the dot, for example `.rvt,.rfa`.
4. Save.

Uploads with those extensions then pre-select the type. Some common formats, such as Revit (`.rvt`), are not in any default type. The ten default types are created again on every update if they are missing. Edit them instead of deleting them.

### 14.10 Automatic copies (routing rules)

On the **project page** upload panel only, routing rules can add extra copies of your upload in other folders.

- Before you confirm, the box shows **Also auto-upload to** with the extra folders.
- Click **×** on a folder to drop that copy. Use the add option to add another folder.
- Each copy is a separate file in its own dated folder.
- Uploads from the Files hub, ZIP uploads and client uploads are never copied.
- If an extra copy fails, no error is shown and the main upload still reports success. If the copy matters, check the target folder.

Uploads into the concept-studies folders get extra copies even with no rules:

- Upload into a discipline folder (for example `02-CONCEPT/01-CONCEPT STUDIES/01-ARCHITECTURE`): each folder **directly inside** it (one level down) is added to **Also auto-upload to**. Only folders whose name starts with `1.` or `1 ` are skipped. The dated folders of earlier uploads count too, so the list can be long.
- Upload into a folder whose name starts with `1.` or `1 ` inside a discipline folder: each folder directly inside it is added.

These copies **are uploaded** unless you click **×** on each one before you confirm. Always check **Also auto-upload to**.

Routing rules are explained in [section 17.2](#172-routing-rules).

### 14.11 Blocked file types and size

Some file types cannot be uploaded, because they can run code in a browser. The screen says "This file type cannot be uploaded to the portal: <ext>". The full list is in [Appendix C](#appendix-c--limits-and-allowed-file-types). Examples: `.html`, `.svg`, `.xml`, `.js`, `.php`, `.py`, `.exe`, `.bat`, `.jar`.

If you really must store one, put it inside a `.zip` and upload it with **Upload files** (not **Upload ZIP**).

> **Warning.** Never open or run a program file (.exe, .bat, .js, .cmd) that came from a client ZIP.

The largest allowed file is set by your administrator in the site configuration (`max_file_size`); the default is about **10 MB** per file. The **Max File Size** field in System Settings cannot raise that limit, but if it holds a smaller number it lowers it, so leave it empty or at least as large. A ZIP sent with **Upload ZIP** must also fit the whole-request limit (about **25 MB** by default).

---

## 15. Working with files: Files hub and File Browser

### 15.1 The Files hub

**Where:** side menu → **Files**, or **Files** / **Open in Files hub** on a project page.

What is on the page, from top to bottom:

- **Manage the company-wide folder template** (only for template editors): opens File tools.
- **Active project**: pick the project.
- **A few things worth knowing**: a short help box for staff.
- **Project folder & subfolders**: the folders as **Grid** cards or a **Tree**. Click the arrow to open or close a folder. Each card shows how many files it holds.
- **Showing files in: <folder>**, with **Clear filter**, **Show all files** and **Use this folder for upload**.
- **Search file** and **Subfolder filter** (All locations, Project folder (all files), or one folder).
- **Client portal guidance**: the welcome text for clients, if the administrator wrote one.
- The staff upload card (section 14).
- The provider cards and the **File policy:** note, if set.
- The file table: **File** (with "(private)" and **Client upload** where they apply), **Size**, **Subfolder**, **Owner**, **Upload date**, **Link**, **Share**, **Delete**.
- Round buttons at the side scroll to the top or bottom.

### 15.2 Opening and downloading

- **Open** (in the **Link** column) opens the file in a new tab. The portal checks your access first.
- **To download several files as one ZIP:**
  1. Tick the files (or the box in the header to tick all).
  2. The bar shows "N files selected".
  3. Click **Download as ZIP**. (**Clear** unticks all.)

  The ZIP is named `<project>-files.zip` and keeps the folder paths. The limit is 500 files or 500 MB.

  The header box ticks only the rows shown after your search and folder filter. If a file cannot be read, it is left out of the ZIP with no warning (a System Manager finds it in the Error Log as "Portal: zip include …"). Check the number of files in the ZIP.

### 15.3 Renaming a folder

**Who:** anyone who can change the project.

1. Click **Rename** on a folder card or tree row.
2. In **Rename subfolder**, type the **New folder name**.
3. Click **Rename**.

Rules: one name only, no `/`, `\` or `..`. The name must not exist already. The project folder itself cannot be renamed. Folders at any level can be renamed, and the files inside move with the folder.

> **Warning.** Do not rename **06-CLIENT SUBMITTAL**. Clients would lose sight of it. Also, shares and guest links made on the old folder name may stop working. Share the folder again after a rename.

### 15.4 Deleting a file

**Who:** anyone who can change the project (any file), and the person who uploaded the file (their own files). Client contacts cannot delete.

1. Click **Delete** at the end of the file's row.
2. Confirm "Delete "<file>"? This removes the ERPNext File record and its attachment."

Folders cannot be deleted from the portal. Rows you may not delete show a dash.

### 15.5 File Browser (browse across projects)

**Where:** side menu → **File Browser**.

- The left panel groups projects by year (2026 and 2025 open first). The year comes from a portal code of the form `ATA-YYnn` (`ATA-2201` is 2022); codes starting `ATA-CDB` go under 2026. Otherwise a project whose **name** starts with a 4-digit number and a dash is grouped by its first two digits ("2601 – …" goes under 2026). Everything else, for example a `CB-01` brief whose name does not start with a number, is under **Other** at the end. Use **Search projects…** to find one.
- Click a project to load its folder tree under it. Click a folder to show only its files.
- At the top: the folder path, **Search files…**, and "<shown> / <total> files".
- Category chips (for example Presentation, Drawing, 3D Model, Feasibility, Design Source, Renders, Other) filter by file extension. PDFs always count as Presentation. **Clear** resets them.
- Sort by **File**, **Date** or **Size** by clicking the column header.
- Click a file name to open it.
- Each row has **Submit** and a share icon.

The File Browser remembers each project's files until you reload the page. Reload to see new uploads.

**To submit a file to the client (copy into 06-CLIENT SUBMITTAL):**

1. Click **Submit** on the file's row.
2. The **Submit to Client** box shows "Will be saved as NN_<today>_<file name>". `NN` is the next serial number in that folder.
3. Click **Confirm & Submit to Client**.

You see "Submitted as "…" (SL n) to Client Submittal." The original file stays where it was. The copy is private, at the top level of 06-CLIENT SUBMITTAL, and the client can see it at once.

If you submitted the wrong file, open the Files hub, open **06-CLIENT SUBMITTAL** and **Delete** the copy (you uploaded it, so you may delete it). The serial number `NN` is the number of files already at the top of that folder plus one. So after a deletion, the next copy can get a number that is already used.

**Who:** staff only. The project must have a folder named exactly 06-CLIENT SUBMITTAL, or you get "This project has no 06-CLIENT SUBMITTAL folder."

The share icon opens **Share File** (see 16.2).

---

## 16. Sharing files and folders

There are two kinds of sharing:

- **With a named person** who has a login. They see it on their **Shared** page.
- **With a guest link** for someone without a login.

**Who can share:** all staff, on any project they can open. Client contacts can never share.

### 16.1 Sharing a folder with a person

1. In the Files hub, click **Share** on a folder card or tree row (or next to the **Upload to** tile).
2. In **Share folder**, under **Add people**, search "by email, username, or full name".
3. Set **Days** (1 to 365; the default is 30).
4. Tick **Email the user when I add them** if you want them to get an email.
5. Click **+ Add** on the person.
6. Click **Done**.

**People with access** then lists each person with "· expires <date>" and a **Revoke** button. In basic mode (see below) the rows show "· shared directly" instead of a date.

What the person gets:

- Read access to every file in the folder and its sub-folders, until the share ends.
- The folder on their **Shared** page.
- If ticked, an email "You were granted access to a folder on <project title>" with a link to the Shared page.

> **Warning (client contacts).** Any share with a client contact, of a folder or of a single file, also opens the **project record** to them. While the share is active, ERPNext may then let them open other files of that project too, not only the shared ones. Files you add to a shared folder later also become visible to them. So share with a client contact only if they may see everything in that project. If they may not, copy the files into 06-CLIENT SUBMITTAL instead (**File Browser → Submit**, section 15.5).

> **Note.** Files you add to a shared folder later show on the person's **Shared** page by themselves while the share is active. You do not need to share again.

Sharing the same folder with the same person again **extends** the existing share. It does not make a second one. The share is then recorded as made by you. The colleague who shared it first can then no longer revoke it, unless they can change the project.

**In ERPNext:** a **Portal Folder Share** record is saved (the audit record). ERPNext **DocShare** entries give read access to the folder, to each file in it at that moment, and to the project.

> **Note.** All staff can already read every project. So sharing with a colleague mainly puts the folder on their Shared page and sends the email. Sharing matters most for **client contacts**.

If the box says "Sharing is running in basic mode. Expiry dates and public share links will be available once your administrator completes the portal setup.", tell your administrator. Sharing with people still works.

### 16.2 Sharing a single file

- In the Files hub, click **Share** in the file's row. The **Share file** box works like 16.1, without a guest link.
- In the File Browser, click the share icon. The **Share File** box lets you search "by name or email" and click a person. It always shares for 30 days and sends no email. **Shared with** lists people with a revoke button. Click **Done** to close.

Sharing one file with a client contact also opens the project record to them. Read the warning in 16.1 first.

### 16.3 Who may receive a share

The portal checks the person you choose:

- Staff: yes.
- A client contact: only if the project's customer is one of theirs. Otherwise "That user belongs to a different customer and cannot be given access."
- Someone with no portal access: refused with "That user does not have access to the project portal."

You can share a folder outside 06-CLIENT SUBMITTAL with a client contact of that project's customer. They can then open those files from their Shared page. Read the warning in 16.1 first.

### 16.4 Guest links (anyone with the link)

**To create a guest link for a folder:**

1. Open **Share folder** on the folder (16.1).
2. Under **Anyone with the link**, set **Expiry (days)** (1 to 365; the default is 7).
3. Click **Create link**. The link is copied to your clipboard ("Link created and copied to clipboard.").
4. Paste it into your email or message.

The box then shows the link, **Copy**, "Expires <date> · N opens" and **Revoke link**.

What the guest sees:

- A page **Shared folder** marked "Secure portal share", with the project, the folder, the expiry time and a file list.
- A **Download** button on each file.
- All files in the folder and its sub-folders, **private ones included**.
- The project's name and project ID and the folder's name. If the recipient should not see the project name, copy the files somewhere else instead of sending a link.
- Files added to the folder **after** you created the link too. The list is read fresh every time the link is opened. While a link is active, do not upload anything into that folder (or its sub-folders) that the recipient should not see.
- After expiry or revoke: "Cannot open this share", with a note to ask the sender for a new link.

Good to know:

- Guest links are for folders only, not single files.
- A folder can have one active guest link in the **Share folder** box. While a link is active, the box shows it with **Copy** and **Revoke link**, and no **Create link** button. To make a new link (for example to give more time), click **Revoke link** first and then **Create link**.
- A link to the project folder ("Project folder (all files)") opens the **whole project**, client ID papers included. Do not do this.

> **Warning.** Treat a guest link like a key. Anyone it is forwarded to can open it, and you cannot tell who. Use the shortest expiry that works, and revoke it when the client has what they need.

**In ERPNext:** a **Portal Folder Share** record of kind "Link" is saved. The link carries a signed code that cannot be changed or guessed.

### 16.5 Revoking, expiry and extending

**To revoke:**

- In the share box: **Revoke** next to a person, or **Revoke link**. Confirm "Revoke this access? The user/link will lose access immediately."
- Or on the **Shares** page (16.7).

**Who can revoke:** the person who created the share, and anyone who can change the project.

**Expiry:**

- A guest link stops working at its expiry time.
- A share with a person is switched off by a background job that runs every hour. So access can last up to about an hour after the expiry date.

**To give more time:**

- For a person: share the same folder with them again, with more days.
- For a guest link: revoke the current link, then create a new one.

There is no **Extend** button.

### 16.6 Shared (what others shared with you)

**Where:** side menu → **Shared**. The page is called **Files shared with you**.

- Tiles: **Projects**, **Folders**, **Files**.
- **Search by project, folder, or file name…** and **Refresh**. The page also refreshes when you come back to the window.
- Each project can be opened or closed. **Open** opens the project page.
- Inside each project you may see:
  - **Team access**: projects whose team you are on.
  - Shared folders, and **single file** shares, with **Expires <date>** or **ERPNext share** (shared in the Desk).
  - **Your uploads**: files you uploaded, but only for projects that are already listed here (through a share or your team). Uploads to other projects are not listed. Find them in the Files hub.
- **Open in Files** opens that folder in the Files hub.
- Each file shows **You** if you uploaded it, **Client upload** if a client did, "(private)", its folder path, size and date, and **Open**.

If nothing is shared yet, the page says "Nothing shared with you yet".

### 16.7 Shares (manage all shares)

**Who:** staff who can change at least one project. Others are sent back to their start page (Projects).

**Where:** side menu → **Shares**. The page is called **Active shares across your projects**.

- Tiles: **Projects**, **Folders**, **Files**, **User grants**, **Public links**.
- **By project** / **By user**: two ways to look at the same shares.
- **Search by project, folder, user, email, or link…**
- **All shares** / **Created by me**.
- **Expand all** / **Collapse**.
- Each project row: status, counts and **Open**.
- Each folder row: "N files", "N users", "N links" or "no shares", and **Manage** (opens the share box in the Files hub).
- Inside a folder: user grants with **Revoke**; public links with "Public link · N opens", expiry, last open, **Copy** and **Revoke**; **Files in this folder** with single-file shares, each with a revoke **×**.

> **Known issues.**
> - **Created by me** does not limit the list to you. It shows every share made in the portal and hides only shares made in the Desk.
> - **Revoke** on rows marked **ERPNext share** fails. Remove those shares in the Desk instead (the share settings on the File or the Project).
> - The "opens" counter on guest links is not reliable. It never goes above 1.

---

## 17. File tools, Routing rules and Contracts

### 17.1 File tools (the company folder template)

**Who:** people with the **Auditor** role, and System Managers. Others are sent back to their start page (Dashboard for managers, Projects for everyone else).

**Where:** side menu → **File tools**. Also from the callout on the Files hub.

This page sets the folder tree that every **new** project gets.

- **Default file subfolders** lists one folder path per row. Use `/` for nesting, for example `01-DOCUMENTS/01-CLIENT DATA/01-BUSINESS CARD`.
- If no custom template was saved, a note says the rows are the built-in default.
- Use **Move up**, **Move down** and **Remove row** on each row.
- **Add row** adds an empty row.
- **Save template** saves the whole list.
- **Import ZIP structure** reads the folders inside a `.zip` and **saves them straight away** as the new template. Only the deepest folders are kept; their parents are created automatically.
- **Back to Files** returns to the Files hub.

**To change the template:**

1. Side menu → **File tools**.
2. Edit a row, or click **Add row** and type a path such as `01-DOCUMENTS/01-CLIENT DATA/07-CONTRACTS`.
3. Use **Move up** / **Move down** to order the rows, and **Remove row** to delete one.
4. Click **Save template**.

Only projects with no folders yet get the new template.

Rules: at most 200 rows. `..` is not allowed. Saving an empty list goes back to the built-in default.

> **Note.** Existing projects never change. Only projects that have no folders yet get the new template.

**In ERPNext:** the template is the **Subfolder template** table in **Portal Project Settings**.

### 17.2 Routing rules

**Who:** the page is shown to staff who can change at least one project. Others are sent back to their start page (Projects). Only System Managers and Projects Managers can **save** or **delete** rules. Others get an error ("API Error") when they save.

**Where:** side menu → **Routing rules**. The page is called **Folder Routing Rules**.

A routing rule adds an extra copy of an upload in another folder. There are two types:

| Type | What it does | Example |
|---|---|---|
| **Mirror** | Copies every upload from a source folder (and its sub-folders) into a matching folder somewhere else. The sub-folder structure is copied too. | Upload to `01-DOCUMENTS/04-DRAWINGS` also saves to `03-BALADIYA/01-DOCUMENTS/04-DRAWINGS`. |
| **Cross-route** | Copies only files of one classification into the first folder that matches a pattern. | A drawing uploaded in the concept studies folder also goes to the presentation folder. |

**To add a rule:**

1. Click **+ Add** on the **Mirror** or **Cross-route** card, or click **New rule** (a Cross-route rule).
2. Or click **Add documents mirror** to pre-fill the ATA standard mirror: `01-DOCUMENTS` → `03-BALADIYA/01-DOCUMENTS`.
3. Fill in the steps:
   - **IF uploaded inside**: the source folder pattern and match mode (contains, starts with, or exact).
   - **AND file type is**: the classification (Cross-route only; "— Any classification —" cannot be saved).
   - **THEN also copy to** (Cross-route) or **MIRROR into** (Mirror): the target folder pattern.
4. Optionally type a description. If left blank, one is made for you.
5. Click **Save**.

Other controls:

- **Enabled / Disabled** switches a saved rule on or off at once.
- The bin **Delete rule** removes it, after you confirm.

Good to know:

- Rules work **only** when uploading from the **project page** upload panel. The Files hub, ZIP uploads and client uploads are not copied.
- For Mirror rules, only the first matching rule is used.
- Cross-route rules are checked by file classification. If an upload is inside the source folder of **any** Cross-route rule, every Cross-route rule with that file's classification adds its copy, even rules with a different source folder. Keep one Cross-route rule per classification.
- Files already uploaded are never moved.
- No rules are created automatically. If a rule is missing, add it. (The project page still adds its own concept-studies copies; see [section 14.10](#1410-automatic-copies-routing-rules).)
- The project page reads the rules when it opens. After adding or changing a rule, reload the project page before uploading.
- Mirror rules always match the source folder and anything below it. The match-mode box is not used for Mirror rules.
- Saving a rule on this page clears any **Notes** typed on it in the Desk.
- **How routing works** at the bottom of the page explains the details again.

**In ERPNext:** each rule is a **Portal Folder Route Rule** record.

### 17.3 Contracts

**Who:** System Managers and Projects Managers.

**Where:** side menu → **Contracts** (lock icon). The page says "Management Only".

This is a locked-down place for signed contracts, apart from the normal project files.

1. On the left, use **Search projects…** and click a project.
2. Click **Upload Contract** and pick one or more files. Allowed types: `.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, `.png`. Each file must be within the site's file-size limit (default about 10 MB). The files are uploaded one by one. If one fails, the files after it are not uploaded. Click the project again to refresh the list, check which files are there, and upload the rest again.
3. Click a file name to open it.
4. Click the bin to delete it, and confirm "Delete "<name>"? This cannot be undone."

Contract files never appear in the Files hub or the File Browser. Their **file names** (not their contents) can still appear to staff in the Dashboard's **Recent Activity**, in ATA AI Chat answers about recent files, and on the **Shares** page under "Project folder (all files)". Give contract files neutral names.

**In ERPNext:** contracts are private Files attached to the project, in the folder `Home / Contracts / <project ID>`. Because they are attached to the project, Desk users with access to the project can see them in the Project's attachments.

---

# Part D — Teams, admin and AI

## 18. Teams

**Who:** System Managers and Projects Managers see all teams. A team lead sees only their own team(s). Only System Managers and Projects Managers can **create** teams.

**Where:** side menu → **Teams**. The page is called **Teams & Members**.

ATA works across offices such as **RIYADH**, **LISBON** and **MANILA**. Each team belongs to one office.

What you see:

- Office buttons (**ALL** and each office) to filter.
- One card per team: the team lead's initials (or the first member's), member count, office, active and total projects, and member pictures. "Click to view members".

**To see a team's members:** click its card. The **Team Members** box opens.

**To create a team:**

1. Click **Create team**.
2. Type the **Team Name** and **Office (optional)**.
3. Click **Create team**. If the name already exists, the existing team is used.

**To edit a team:** click the pencil **Edit team**, change **Team Name** or **Office**, then **Save Changes**.

**Office** here offers only offices that already exist. To start a new office, type it in **Office** when you **Create team**.

**To add a member:**

1. Open the team and click **Add member**.
2. Type in "Search users or user groups".
3. Click a **User Group** to add everyone in it (staff only), or click a **User** to add one person.

The list shows every enabled login, client logins included. Never add a client login to a team.

**To make an existing person a team lead:**

1. Add them to the team with **Add member**.
2. In the Desk, open the **Department** and set **Portal Team Lead** to them. This needs rights to edit Departments in the Desk (for example an HR Manager).

The lead must also be a member to be shown first.

**To remove a member:** click the red **×** "Remove from team". There is no confirmation.

> **Warning.** A team without an **Office** does not appear on the Teams page, the Org Chart or the team pickers. Always give a team an office. Choosing "— Select —" in **Office** hides the team.

> **Note.** Being in a team does **not** give access to any project. Project access comes from the project's own **Team** card (section 7.6).

**In ERPNext:**

- A team is a **Department** directly under "All Departments", with a **Portal Office**.
- A member is an open **Assign To** (ToDo) on that Department. If the member's ToDo is closed or cancelled (for example ticked done in their To Do list), they leave the team.
- The team lead is the Department's **Portal Team Lead** field. It is set on the Admin page for new users, or in the Desk.
- Renaming a team changes its label only. The Department's ID keeps the old name.

---

## 19. Org Chart

**Who:** System Managers and Projects Managers only.

**Where:** side menu → **Org Chart**. The page is called **Organization Chart**.

- Each team is drawn as a tree. The team lead is on top (or, if no lead is set, the first member by name) and the other members below.
- **All Offices** and the office buttons filter the tree.
- **+** and **−** open and close a team.
- Click a person to see them in the side panel: name, role, office and "Direct reports". With nobody chosen it says "Select a Member".
- **Headcount Summary** shows numbers per office.
- The pencil **Manage team** on a team opens the same edit, add and remove controls as the Teams page.

> **Note.** The numbers here count team memberships. A person in two teams counts twice. The sidebar "ATA Teams" count uses ERPNext Employee records instead, so the two can differ.

---

## 20. Admin page

**Who:** people who can create Users in ERPNext (in standard ERPNext: System Managers). The **Demo dataset** section also needs the setting **Allow portal demo seed** (see 20.2). Others are sent back to their start page (Dashboard for managers, Projects for everyone else).

Auditors can also open this page, but it is not in their menu. They can type `/portal-app/admin`, or use **File tools** instead. They see only the **Project folder structure** card.

**Where:** side menu → **Admin**. The page is called **Portal administration**.

### 20.1 Create portal user

1. Fill in **Email (username)** and **Full name**.
2. Tick the roles:
   - **Projects User** (ticked by default), **Projects Manager**: staff logins.
   - **Portal Customer**: a client login. It cannot be combined with staff roles.
   - **Team Manager** (staff only): makes the person the lead of a team. Pick it in **Team they lead**. Also tick **Projects User** or **Projects Manager**. Team Manager on its own gives "Select at least one role."
   - **Super Admin** (shown only to System Managers): gives full System Manager rights to the whole ERP, not just the portal. A warning says so.

   > **Note.** If **Create user** fails with "No permission to share Department" when **Team Manager** is ticked, create the user without **Team Manager**. Then add them to the team on the **Teams** page (**Add member**), and set the Department's **Portal Team Lead** field to them in the Desk (section 18).
3. For **Portal Customer**, pick the **Customer** (search "Search customers by name…", then **Change** to pick again). The customer must already exist. If it does not, the screen says "No customer matches. Create it first from a project's Customer card."
4. Choose how they get a password:
   - Tick **Send welcome email with a link to set their own password**. **Password (optional)** can stay empty. (Ticking Portal Customer ticks this box for you. You can untick it and set a password instead, but the welcome email is preferred.) **Or**
   - Untick it and type a password (**Password (min 6)**). The site's password policy may ask for more.
5. Click **Create user**.

Messages:

- "Created <email>. A welcome email with a set-password link is on its way."
- "Created <email>. No email was sent; share the password with them yourself."
- "… but the welcome email could not be sent — check the outgoing email account."

> **Tip.** Prefer the welcome email. If you must set a password, tell it to the person by phone or another separate channel, never in the same message as their email address. Ask them to change it on **Profile** at once.

Rules: the email must be new ("User already exists" otherwise). To give an existing login another customer, use the project page (section 23).

**In ERPNext:** a **User** is created. Staff become System Users. A Portal Customer becomes a Website User, with a **Portal User Customer** record for the chosen customer. Team Manager sets the Department's **Portal Team Lead** and adds the person to the team.

### 20.2 Demo dataset

**Who:** System Managers, and only when **Allow portal demo seed (System Manager only)** is ticked in Portal Project Settings (or the site is in developer mode).

> **Warning.** Never run a demo seed on the live ATA site. It creates five real, working logins (one Projects Manager, three Projects Users and one Portal Customer that is not linked to any customer), projects, tasks and a sample file. (The **Customers** option currently creates nothing.) Saving a new **Portal Demo Seed Run** record in the Desk runs the seed at once, even when **Allow portal demo seed** is off. Never create these records on the live site.

**To create a new run:**

1. Type a **Label**.
2. Tick what to create: **Users**, **Customers**, **Projects**, **Tasks** and **Sample file**.
3. Click **Run seed**.

**To seed from a project list (.docx):**

1. Click **Choose .docx file…**.
2. Pick a Word file with one project per line, for example `2601 – EXAMPLE PROJECT`.
3. Check the preview table (**Code**, **Project name**).
4. Type a **Run label**.
5. Click **Seed N projects**.

Other controls:

- **Past runs** lists every run with its status and counts. **Delete & clean up** removes one run and everything it created. **Clear all demo data** removes every active run.
- **Refresh** reloads the list.

Records that already existed before a run are never deleted.

### 20.3 Project folder structure

**Who:** the card is shown to everyone on the Admin page, but it only works for Auditors and System Managers. Others get "You are not allowed to change the portal folder template."

- **Upload ZIP…**: import the company template from a ZIP whose folders are your standard.
- **Upload Folder…**: pick the real folder on your computer. No zipping needed.
- **Apply to project** (optional): type a Project ID in the box before you import, and the portal also builds the new folders on that project. This works only on a project that has no folders yet.

> **Warning.** Both imports **replace** the current template immediately.

### 20.4 Staff joining, changing role or leaving

**Who:** System Managers. Projects Managers can also do the project **Team** card, **Teams** page and **Shares** steps.

**A new staff member joins:**

1. On the Admin page, use **Create portal user** with **Projects User** and the welcome email ([section 20.1](#201-create-portal-user)).
2. Add them to their office team on the **Teams** page ([section 18](#18-teams)).
3. Add them to the **Team** card of each project they will change ([section 7.6](#76-team-card)).

**A staff member changes role** (for example becomes a Projects Manager): the Admin page cannot change an existing login. A System Manager opens the **User** in the Desk, changes **Roles** and saves. The person then reloads the portal.

**A staff member leaves:**

1. **Find their projects.** In the Desk, open the **Project** list and filter on **Users → User** = their login.
2. **Take them off each project's Team card.** Click **Remove**, then **Save team**.
3. **Hand over their projects.** Where they are the Lead Architect, a System Manager picks a new one ([section 6.5](#65-editing-a-project) and [section 6.6](#66-assigning-the-lead-architect)).
4. **Hand over their teams.** Remove them on the **Teams** page. If the Department's **Portal Team Lead** field names them, change it in the Desk.
5. **Check their shares.** On the **Shares** page, click **By user** and revoke what was shared with them ([section 16.7](#167-shares-manage-all-shares)). Revoke any guest links that are no longer needed.
6. **Disable the login.** Desk → **User** → untick **Enabled**. Do not delete it.

> **Warning.** If a login is disabled while it is still on a project team, every **Save team** on that project fails with "User is disabled: <login>". Click **Remove** next to that person first, then **Save team**.

---

## 21. ATA AI Chat

**Who:** staff.

**Where:** side menu → **ATA AI CHAT**.

This screen answers simple questions about the portal's data. **It is not a real AI.** It looks for certain words in your question and runs fixed counts and lists. It cannot answer open questions. It only reads; it never changes anything.

**To ask a question:**

1. Type in "Ask anything about your projects, files, or tasks..." and press **Enter** (**Shift + Enter** for a new line), or click the send arrow.
2. Or click a suggestion: "How many active projects are there?", "Show files uploaded this week", "How many tasks are open?", "Give me a summary of all projects", "Find projects with Tower in the name", "How many files are in the system?".
3. **Clear** wipes the conversation. Nothing is saved.

What it can answer:

| Ask about | You get |
|---|---|
| "how many projects", "summary", "overview" | Project counts by status |
| "active projects" | Up to 15 open projects |
| "completed projects" | Up to 15 completed projects |
| "files uploaded" + "today" / "this week" / "this month" | Up to 20 recent files (this month = last 30 days) |
| "how many files" | The number of project files |
| "tasks" | Task counts by status (all statuses) |
| "budget", "cost", "value" | The top 10 projects by value, and the total, only for projects whose value you may see |
| "find" / "show" / "list" + words | Up to 10 projects whose name or code contains any of the words |

Anything else returns a summary of projects, tasks and files. Words like "summary" or "value" anywhere in the question change the answer, so keep questions short.

---

# Part E — Clients

## 22. For clients: how to use the portal

*This section is written for you, the client.*

ATA gives you a login so you can see your own projects, get the documents ATA sends you, and send files to ATA.

### 22.1 What you can see and do

| You can | You cannot |
|---|---|
| See the projects of your company (or companies) | See any other client's projects |
| Open each project's page: status, stage, dates, progress, the ATA team and the latest tasks | See project values or costs |
| Open and download files in the **06-CLIENT SUBMITTAL** folder | See ATA's internal folders (unless ATA shares a folder with you by name) |
| Download several files as one ZIP | Delete files, rename folders or share files |
| Upload files into **06-CLIENT SUBMITTAL** | Create projects or change project details |
| See files ATA shared with you personally | Use ATA's internal office system |
| See your project's tasks and their comments (the **Tasks** button on the project page) | Change tasks or add comments |
| Open the project's server links (T / A / erp) on the Projects list, if ATA has given you access to those drives | — |

### 22.2 Signing in for the first time

**Already have a portal login** (for example for another of your companies)? You get the email "You now have access to <Customer> projects" instead. Sign in with your existing password and skip the steps below.

1. ATA sends you an email. Its subject is "Welcome to …" or "Complete Registration".
2. In the email, click the **Complete Registration** button.
3. Choose your password.
4. The portal opens.

The link in the email expires after about 72 hours. If it has expired, go to the portal sign-in page, click **Forgot Password?**, type your email and click **Reset Password**. You get a new email.

Next time, open the portal address ATA gave you (it ends in `/portal-app`). Type your email and password and click **Sign In**. You land on **Projects**.

### 22.3 Finding your project and its files

1. Click **Projects** in the side menu. You see only your company's projects.
2. Click a project to open its page.
3. Click **Files** at the top of the page (or **Open in Files hub** on the Files card). Both open the **Project files** page.
4. On the **Project files** page you see the **06-CLIENT SUBMITTAL** folder and any folders inside it.
5. Click a folder to show its files.
6. Click **Open** to open a file.

> **Note.** The side menu shows a **FILES** heading with nothing under it. This is a known issue. Use the **Files** button on the project page, as above.

To switch to another project, use **Active project** at the top of the Project files page.

**To download several files at once:** tick them, then click **Download as ZIP**.

### 22.4 Sending files to ATA

1. Open the project's **Project files** page (section 22.3).
2. Optional: click the folder inside 06-CLIENT SUBMITTAL where the files should go. The card then says **Files go into <folder>**. Check it before the next step.
3. In the card **Upload to 06-CLIENT SUBMITTAL**, click **Choose files**.
4. Pick one or more files.
5. Wait for "Uploaded N files. The ATA team sees them marked as a client upload."

Good to know:

- Your files are always private.
- ATA sees them with an orange **Client upload** badge.
- You cannot delete a file after uploading it. If you uploaded the wrong file, tell your ATA contact.
- Some file types are refused, for example `.html`, `.svg`, `.js` and `.exe`. If you need to send a drawing export such as `.svg` or `.xml`, put it in a `.zip` first. Do not send programs.
- Very large files may be refused. The usual limit is about 10 MB per file.
- If the card says "This project has no 06-CLIENT SUBMITTAL folder yet.", tell your ATA contact.

### 22.5 Files shared with you

ATA may share a folder or file with you by name. It then appears on the **Shared** page, which you can open at `/portal-app/shared-with-me`. Click **Open** next to a file. Shares can have an end date ("Expires <date>").

If a shared file will not open, ask your ATA contact to share it again.

Files you uploaded yourself are not always listed here. To check them, open the project's **Project files** page (section 22.3).

ATA may also send you a **guest link** (a link that needs no login). It opens a page called **Shared folder** with a **Download** button on each file. If it says "Cannot open this share", the link has expired or was withdrawn. Ask ATA for a new one.

### 22.6 More than one company

One login can belong to several client companies. You then see the projects of all of them. Your **Profile** page shows the list under **Linked customers (portal)**.

### 22.7 Your account

- **Profile** (side menu): change your name, mobile, language and time zone; change your password (section 3.6).
- **Logout**: click your picture at the top right, then **Logout**, then **Logout** again.
- Ignore **New Project** and **Switch to Desk** at the top. They are not for client logins.

---

## 23. For ATA staff: giving a client access, end to end

### 23.1 The whole flow

1. **Set the customer** on the project (Customer card).
2. **Give a person a login** for that customer: invite a new login, or add an existing one.
3. The person gets an **email** and sets a password.
4. They sign in and see **all projects of that customer**, but only the **06-CLIENT SUBMITTAL** folder (unless ATA has shared something with them).
5. Later you can **reset their password** or **remove** their access.

**In ERPNext:** a client login is a **Website User** with the role **Portal Customer**. What they can see is decided **only** by **Portal User Customer** records (one record = "this login may see this customer's projects"). One login can have several. The **Portal linked Customer** field on the User is read-only and for display only. It shows one of the login's customers. It does not give or take away access. ERPNext also creates a **Contact** for each new login, but it is not linked to the Customer, so client logins do not appear in the Customer's Contacts in the Desk. To see who has access, use the **Customer portal users** card or the **Portal User Customer** list.

### 23.2 Step 1: set the customer

1. Open the project page.
2. In the **Customer** card, click **Search customers** and pick the customer, or use **Create customer (no duplicate name)**.

Every client contact of that customer can now see this project.

### 23.3 Step 2a: invite a new person

**Who:** System Managers (it needs permission to create Users).

1. On the project page, click **Invite customer user** (Customer card) or **Invite new user** (Customer portal users card).
2. In **Invite customer portal user**, fill in **Email (username)** and **Full name**.
3. Keep **Send a welcome email** ticked. Leave the password box ("Password (optional — leave blank to let them choose)") empty.
4. Click **Create & send invite**.

You see "Created <email> and linked them to this customer. An invite email is on its way."

Other cases:

- If you untick **Send a welcome email**, you must type a password (at least 8 characters). The button becomes **Create & link**. You then pass the password on yourself. Prefer the email. If you must set a password, tell it to the person by phone or another separate channel, never in the same message as their email address. Ask them to change it on **Profile** at once.
- If the email already has a login, that login is linked instead. It keeps its current password: "Linked the existing user <email> to this customer — they keep their current password."
- If the email belongs to a **disabled** login, you get "… is a disabled login. Re-enable it in Desk before inviting them." A System Manager must enable it first.
- If the existing login has never set a password, keep **Send a welcome email** ticked. Otherwise you get "… already exists but has no password yet. Tick Send a welcome email."
- If you link an existing login with **Send a welcome email** unticked, no email is sent. Tell the person yourself.
- System Managers, Projects Managers and anyone on a project team are refused, as in 23.4. Other staff logins are **not** refused; see the warning in 23.4.
- If the warning "The invite email could not be sent — check the outgoing email account." appears, the login was created but no email was queued. Tell your System Manager. Once an outgoing Email Account exists, a System Manager uses **Reset password → Email them a reset link** ([section 23.10](#2310-resetting-a-clients-password)). Do not remove and re-add the person: re-adding only sends a notice telling them to use the earlier email, which never arrived.

### 23.4 Step 2b: add an existing login

Use this when the person already has a client login, for example for another customer.

**Who:** System Managers and Projects Managers. Others see "Only a System Manager or Projects Manager can add customer portal users."

1. In **Customer portal users**, go to **Add existing user**.
2. Click the box to see client logins, or type part of a name or email.
3. Click the person. They are added at once ("Added").

You see "Added <email>. An access email is on its way."

System Managers, Projects Managers and anyone on a project team cannot be linked. You get "This is an internal user and cannot be linked as a customer portal contact".

> **Warning.** Other staff logins are **not** blocked. If you type a colleague's email in **Invite customer user**, their login is linked and gets the **Portal Customer** role. From then on it sees only that customer's projects. Check the email before you invite. (**Add existing user** lists only client logins, so staff do not appear there.)

### 23.5 Step 3: what the client receives

| Situation | Email |
|---|---|
| New login | The welcome email with **Complete Registration**. After setting a password, they land in the portal. |
| Existing login with a password | "You now have access to <Customer> projects", with the sign-in link. |
| Existing login whose welcome link is still unused | The same notice, telling them to use the earlier welcome email or **Forgot Password?**. The earlier link keeps working. |
| Existing login that never set a password, and whose welcome link has expired (or never existed) | A new welcome email with **Complete Registration**. |

Emails are **queued**. They normally leave within a few minutes.

### 23.6 Step 4: what the client sees

- Projects: all projects of their customer(s).
- On each project page: status, stage, client, dates, progress, the task list, and the **Team** card (with the ATA team's login emails). Keep task titles professional.
- Files: only **06-CLIENT SUBMITTAL** and its sub-folders, plus anything you shared with them by name.
- They can upload into 06-CLIENT SUBMITTAL. They cannot delete, share or change anything.
- Tasks, Kanban, Gantt, Calendar, Daily Task and AI Chat are not in their menu, but the **Tasks** buttons on the project page open the Tasks page for them, read-only (task titles, assignees and comments). On the Projects list they also see the **Servers** badges (T, A, erp): only enter links the client may see.

Check the **People with access** list. It shows "Last signed in <when>" once they have signed in, or "Invited — hasn't signed in yet".

### 23.7 If the client cannot see the folder

The folder must be named exactly **06-CLIENT SUBMITTAL**, directly inside the project folder. Older projects may use "06 - CLIENT SUBMITTAL" (with spaces). Clients cannot see that.

**To fix it** (someone who can change the project):

1. In the Files hub, open the project.
2. Click **Rename** on the old folder.
3. Type `06-CLIENT SUBMITTAL` exactly and click **Rename**.
4. Share again anything you had shared on the old folder.

### 23.8 Giving files to the client

Choose one:

- **Upload into 06-CLIENT SUBMITTAL** from the Files hub or the project page. (Your upload goes into a dated sub-folder inside it. The client sees sub-folders too.)
- **File Browser → Submit**: copies an existing file into 06-CLIENT SUBMITTAL as `NN_<date>_<name>` (section 15.5).
- **Share a folder or file by name** with the client contact (section 16.1; read the warning there first). They find it on their Shared page.
- **Guest link** for someone without a login (section 16.4). Use a short expiry. Never link the whole project.

### 23.9 Spotting client uploads

- **In the portal:** an orange **Client upload** badge next to the file name, in the Files hub, the project page, the File Browser and the Shared page. Point at it to see "Uploaded by the client: <name>".
- **In the Desk:** open the **File** list. In the left sidebar, open **Tags** and click **Client Upload**.

Client uploads are always private. They are not put into dated folders and not renamed.

The badge is worked out each time from who uploaded the file. If that login later loses the **Portal Customer** role (for example when its last customer is removed, [section 23.11](#2311-removing-access)), its earlier uploads no longer show the badge in the portal. The Desk tag **Client Upload** stays, so use the Desk tag to find everything a client ever sent.

### 23.10 Resetting a client's password

**Who:** System Managers only. The person must be a client contact of this project's customer.

1. In **Customer portal users**, click **Reset password** next to the person.
2. Choose one:
   - **Email them a reset link** (recommended). They choose a new password. Click **Send reset link**. You see "A password reset link is on its way to <email>."
   - **Set a new password now**. Type a **New password (min 8)** and click **Set password**. They are signed out everywhere. No email is sent; you must pass the password on to them safely. You see "New password set for <email>. Their other sessions were signed out."

> **Tip.** Prefer the email link. If you must set a password, tell it to the person by phone or another separate channel, never in the same message as their email address. Ask them to change it on **Profile** at once.

Each new reset link makes any earlier link stop working. If no email account is set up, you get "No outgoing email account is configured…".

### 23.11 Removing access

**Who:** anyone who can change the project, team members included.

1. In **Customer portal users**, click **Remove from portal** next to the person.

> **Warning.** There is no confirmation. The access is removed as soon as you click. To undo it, add the person again with **Add existing user** (section 23.4). Their old shares do not come back.

This removes **this customer** from their login, so they lose **every project of this customer**, not just this one. Their other customers stay.

Behind the scenes:

- Their shares on this customer's projects are withdrawn.
- A note is added to their User record in the Desk.
- If this was their last customer, the **Portal Customer** role is removed. The login stays enabled, but the next time they sign in, the portal signs them out again and shows "Server error. Please try again." (A session that is already open keeps working but shows no projects.) To give access back, add them with **Add existing user** ([section 23.4](#234-step-2b-add-an-existing-login)).

Other ways access ends:

- Removing the **Portal Customer** role from the User in the Desk removes **all** their customers and shares. Giving the role back does **not** bring them back.
- Changing or clearing the project's Customer hides that project from the old customer's contacts. Folder and file shares you made for the old customer's contacts are **not** withdrawn automatically. Revoke them on the **Shares** page.
- To stop a person signing in at all (for example when they leave their company), a System Manager opens their **User** in the Desk and unticks **Enabled**. Their customer links stay, and ticking **Enabled** again restores the same access.
- Do not delete a client's **User** in the Desk. Untick **Enabled** instead. Deleting it removes all its customer links and shares, and cannot be undone. A Customer that is still linked to projects cannot be deleted.

### 23.12 Other places to manage client logins

- **Admin page → Create portal user** with **Portal Customer** (System Managers; section 20.1).
- **Desk → Portal User Customer** list (System Managers): one row per login and customer. Deleting a row removes that access and its shares. Adding a row in the Desk is not recommended. It gives access only if the User also has the **Portal Customer** role, no email is sent, and the portal's checks (not staff, not on a project team) are skipped. A row for a User without the role grants nothing, and it is deleted the next time the User is saved. Use the project page (sections 23.3 and 23.4) instead.

---

# Part F — Reference

## 24. Where things live in ERPNext Desk (for administrators)

| In the portal | In the Desk |
|---|---|
| A project | **Project** record. The portal adds fields such as Portal Project Code, Portal Project Manager, Portal Kanban Stage, Portal Office, Portal Phase, Portal Team, the server links and Portal Milestones. |
| Project team | The Project's **Users** table, kept in step with **Assign To** on the Project. |
| Files | **File** records under `Home / Attachments / <project>`. Contracts under `Home / Contracts / <project>`. |
| Client uploads | Files with the tag **Client Upload**. |
| Shares and guest links | **Portal Folder Share** list (audit: who, what, expiry, revoked, opens), plus ERPNext **DocShare** entries. Always revoke from the portal. Never tick **Revoked** or delete rows here by hand: a share with a person then keeps working with no end date, because its DocShares are never removed. |
| Client logins and their customers | **User** (Website User, role Portal Customer) and **Portal User Customer** (System Manager only). |
| Teams | **Department** records under "All Departments", with **Portal Office** and **Portal Team Lead**. Members are ToDo assignments on the Department. |
| Daily Task reminders | Private **Event** records. |
| Tasks and comments | **Task** records and their comments. |
| File types | **Portal File Type** list. |
| Routing rules | **Portal Folder Route Rule** list. |
| Demo runs | **Portal Demo Seed Run** (never on the live site). Creating one in the Desk runs it immediately. |

**Portal Project Settings** (System Manager only) holds the portal's settings:

| Section | Setting |
|---|---|
| Branding | **Company Logo**, **Company Name**, **Company Tagline** (sign-in screen and side menu). |
| Portal access | **Allow any portal user to create projects** (ticked by default; untick to let only managers create projects). **Allow portal demo seed (System Manager only)** (keep unticked on the live site). |
| Project file subfolders (template) | **Subfolder template**: the company folder tree. |
| Central storage (Frappe Drive) | **Use Frappe Drive on this server**, **Drive / site base URL**, **Frappe Drive upload webhook URL**, **Internal file policy note** (shown on the Files hub as "File policy:"). |
| Cloud integrations | Google Drive and BIM 360 / ACC switches, notes and upload webhook URLs. Although labelled "(planned)", they work once switched on with an address. |
| Client portal | **Welcome text for client document access** (shown on the Files hub as "Client portal guidance"). |

> **Warning.** Every signed-in user, clients included, can read these settings through the portal. Never put passwords or secret keys in the webhook addresses or the notes.

Other Desk settings the portal depends on:

- **System Settings → Reset Password Link Expiry Duration**: how long welcome and reset links last (72 hours on the ATA site).
- **System Settings → Enable Password Policy** and **Minimum Password Score**: stronger passwords.
- **Selling Settings → Default Customer Group and Territory**: used for customers created in the portal. If they are empty, the portal uses the first Customer Group and Territory.
- An **outgoing Email Account**, and the background **scheduler**, for all emails and for the hourly share expiry.

The Desk sidebar has a **Project Portal** workspace. Its shortcuts are **Open Portal**, **Project**, **Task**, **Portal Project Settings**, **User Guide** (opens `/handbook`) and **Technical Guide** (opens `/tech-guide`, System Managers only). Its link cards list the portal's DocTypes, including **Portal User Customer**.

> **Warning.** Each update (`bench migrate`) re-creates the portal's own fields and its **Project Portal** workspace. Desk changes to them are lost: for example new **Portal Kanban Stage** or **Portal Phase** options added in Customize Form, renamed labels, or edits to the workspace. Ask the developer to change these in the app instead.

---

## 25. Emails the portal sends

All portal emails are queued and sent a few minutes later. The **Forgot Password?** email from the sign-in page is sent at once by ERPNext. All emails need an outgoing Email Account in the Desk.

| Email | When | To |
|---|---|---|
| Welcome ("Welcome to …" or "Complete Registration", with a **Complete Registration** button) | A new client is invited; or a user is created on the Admin page with the welcome box ticked; or an existing login with no password (and no unexpired link) is added to a customer | The user |
| "You now have access to <Customer> projects" | An existing client login is added to a customer | The client |
| "Password Reset" | **Forgot Password?**; or a System Manager uses **Email them a reset link** | The user |
| "You were granted access to a folder on <project>" / "…a file on <project>" | A share with **Email the user when I add them** ticked | The person shared with |
| "Project Collaboration Invitation" (from ERPNext) | Someone is added to a project team; also on every **Save team** | Team members |
| "<name> assigned a new task Project <title> to you" and "Your assignment on … has been removed by <name>" (from ERPNext) | Someone is added to or removed from a project team (**Save team** or Desk **Assign To**), or added to or removed from a team on the Teams page | The person (not when you add or remove yourself), unless they turned off assignment emails in their Notification Settings |
| "Upcoming Events for Today" (from ERPNext) | Daily, for Daily Task reminders | The reminder's owner |

To change the wording of the welcome and password-reset emails, a System Manager creates an **Email Template** in the Desk and chooses it in **System Settings → Welcome Email Template** or **Reset Password Template**. The "You now have access…" and share emails have fixed wording.

---

## 26. House rules

1. **One login per person, never shared.** Every upload, share and deletion is recorded against the account that did it.
2. **Leave uploads private.** Public means anyone on the internet with the address. Share with a named person, or use a guest link, instead.
3. **Choose the right folder before uploading.** Check "Goes into <folder>".
4. **Short expiries on guest links, and revoke them when done.** Use the Share box or the **Shares** page.
5. **Do not change the standard folders.** Their sameness across every project is what makes them useful. Never rename **06-CLIENT SUBMITTAL**.
6. **Never send a guest link to 01-CLIENT DATA or to the whole project.**
7. **Always give a team an office.** Otherwise it disappears from the lists.
8. **Never run a demo seed on the live site.**
9. **Name files as if the client will read the name.** Keep file names professional and neutral.
10. **Write task titles and comments for the client too** ([section 11.3](#113-comments)).

---

## 27. Known issues and workarounds

These were found while writing this guide (30 September 2026). They may be fixed later.

| Where | Problem | Workaround |
|---|---|---|
| Side menu (clients) | The **FILES** heading shows no links. | Open a project and click **Files**. |
| Sign-in | A login without a portal role sees "Server error. Please try again." | Give the user a portal role. |
| Edit Project form | Non-System Managers cannot save when the Lead Architect is someone else. | Ask a System Manager, or rename from the project page. |
| Edit Project form (Projects Users) | The Lead Architect box is empty. Saving clears the Lead Architect if it named you. | Ask a manager to edit, or rename on the project page. |
| Edit Project form | Remarks are cleared on every save; Progress is replaced by ERPNext; On Hold / In Progress do not stick (and fail to save on Manual projects). | Keep notes elsewhere; use the Kanban stage for working stages. |
| Project team | **Save team** re-sends the "Project Collaboration Invitation" email to every member. | Save the team only when needed. |
| Tasks → New task | **Assign to** is not saved. | Assign the task in the Desk. |
| Tasks table | The **Assigned** column shows login emails, not names. | — |
| Kanban | Empty stages have no column. | Set the stage in the Desk. |
| Gantt | Picking an office moves other offices' projects into "Unassigned to a team". | Use the **All Teams** filter too, or ignore that group. |
| Daily Task | Dates are one day off in Saudi time; TODAY badge on tomorrow's tile. | Go by the date labels. |
| Dashboard | **Projects Delayed** counts finished projects; period drop-downs do nothing; Team Performance is empty. | Read the cards as described in section 5. |
| Files hub → Upload ZIP | A red "loadFilesAndFolders is not defined" message after success. | Reload the page. |
| Folder rename | Shares and guest links on the old name may stop working. | Share again after renaming. |
| Shares page | **Created by me** shows everyone's shares; **Revoke** fails on "ERPNext share" rows; the opens counter stops at 1. | Remove Desk shares in the Desk. |
| File Browser | If a client opens the File Browser address directly, they see **Submit** and share buttons that always fail. | — |
| Top bar | **New Project** only opens the Projects page for people who cannot create; **Switch to Desk** errors for clients. | Ignore. |
| Teams | Team leads see **Create team** but cannot use it. | Ask a manager. |
| Routing rules | Team members can open the page but cannot save. | Ask a System Manager or Projects Manager. |
| Old projects | "06 - CLIENT SUBMITTAL" is invisible to clients. | Rename it (section 23.7). |

---

## 28. FAQ and troubleshooting

**I still see the old screens after an update.**
Reload the page. If that does not help, do a hard refresh: **Ctrl + Shift + R** (Windows) or **Cmd + Shift + R** (Mac). If it is still old, close every portal tab and open the portal again, or try a private window.

**I cannot see a project I know exists.**
- Staff see every project. If you see none, your login may have no portal role. Ask a System Manager to give you **Projects User**.
- Client contacts: the project needs its **Customer** set to your company, and your login must be linked to that customer. Ask your ATA contact.
- You opened the portal from the Desk (the `/apps` tile) and the Projects list is empty: your login has no portal role. The portal does not sign you out in this case. Ask a System Manager to give you **Projects User**.
- You use the **Active project** picker on the Files hub, or the project lists on the File Browser or Contracts: these list only the 500 most recently changed projects. Find the project with the search on the Projects page instead.

**Sign-in says "Sign-in did not keep a session (cookies blocked or wrong site URL). Check browser settings."**
Check that your browser allows cookies for the site, and that you are using the portal address ATA gave you. If cookies are fine, your account may need an extra step that the portal's sign-in screen cannot show: a two-factor code, or a forced password change because your password has expired. Sign in once at `https://<your-ERP-address>/login` (ERPNext's own sign-in page), complete the step it asks for, then open `/portal-app`.

**What do the sign-in error messages mean?**
- **Invalid login credentials**: the email or password is wrong. Use **Forgot Password?**.
- **User disabled or missing**: your login is disabled. Ask a System Manager.
- **Your account has been locked and will resume after N seconds**: too many wrong passwords in a row (by default 10). Wait that long and try once more, or use **Forgot Password?**.
- **Server error. Please try again.**: your login has no portal role (section 3.1).
- **Sign-in did not keep a session…**: see the entry above.

**I can see a project but cannot change it.**
You are not on its **Team**. Ask a Projects Manager or the Lead Architect to add you (section 7.6).

**Why can I see the project but not its value?**
See section 2.5. Only System Managers see all values. A Projects Manager sees only projects where they are the Lead Architect.

**The welcome or reset link has expired.**
Links last 72 hours on the ATA site. Use **Forgot Password?**, or ask a System Manager to use **Reset password** (for clients).

**The email did not arrive.**
- Check your spam or junk folder.
- Emails are queued and can take a few minutes.
- If the screen said the email "could not be sent", no outgoing email account is set up. Tell your System Manager.
- A System Manager can check the **Email Queue** list in the Desk.
- If the **Email Queue** shows the email as **Not Sent** for more than a few minutes, the background scheduler may be off. The developer or server administrator must switch it on. The hourly share expiry also depends on it.

**The client cannot see the 06-CLIENT SUBMITTAL folder.**
The folder name must be exactly `06-CLIENT SUBMITTAL`. See section 23.7.

**My upload was refused.**
- The file type may be blocked (Appendix C).
- The file may be too big.
- Clients can only upload into 06-CLIENT SUBMITTAL ("You can upload only into the 06-CLIENT SUBMITTAL folder.").
- For staff, **Upload files** and **Upload ZIP** are grey only when the project has no folders yet (see "A project made in the Desk has no folders" below). Otherwise the first folder is pre-selected, so always check **Goes into <folder>**.

**A project made in the Desk has no folders.**
The standard folders are built on the first portal upload. In the Files hub, click the **Project folder (all files)** card, then **Use this folder for upload**, and upload one file. The standard folders are then created. Reload the page.
Your file is saved in a new dated folder at the top of the project (for example `07_2026-09-30_<name>`), next to the new standard folders. Use a harmless file, or upload the first real document this way on purpose.

**A new folder from the template is missing in an existing project.**
Template changes reach only projects that had no folders. Existing projects keep their own folders.

**The file went into a folder I did not expect.**
**Upload files** and **Upload folder** put your files into a new dated folder inside the folder you chose (section 14.4). A routing rule, or the project page's own concept-studies copies (section 14.10), may also have placed a copy elsewhere. On the project page, changing **File Classification** or **PDF Type** can also change the destination folder (section 14.3).

**A guest link stopped working.**
It expired or was revoked. Create a new link (section 16.4).

**Someone left my project team without anyone removing them.**
Their **Assign To** on the project may have been closed or cancelled in the Desk. That removes them from the team. Add them again.

**I get "Invalid Request" after signing in.**
Reload the page once. The portal gets a fresh security token automatically. If it keeps happening, check that your browser allows cookies for the site.

**"Maximum Attachment Limit … has been reached" when uploading.**
Ask an administrator to run `bench migrate`, which lifts the limit for projects.

**"Set default Customer Group and Territory in Selling Settings, or create masters first."**
No Customer Group or Territory exists on the site. A System Manager creates at least one of each in the Desk, and ideally sets them as **Default Customer Group** and **Default Territory** in **Selling Settings**. Without those defaults, the portal uses the first group and territory.

**"Set a default Company or pass company" / "Set a default Company first."** (creating a project or a team)
A System Manager sets the default Company in the Desk (**Global Defaults**).

**"Daily Task is not set up on this site yet. Run `bench migrate` and try again."**
Ask the administrator to run the update.

**"Folder sharing is unavailable: this site has no encryption_key configured."**
Ask the administrator. If the site's encryption key is ever changed, every existing guest link stops working.

**A client lands on a plain ERPNext page instead of the portal after signing in.**
They can open `/portal-app` directly. An administrator should check that none of their roles has a **Home Page** set, and that **Portal Settings → Default Portal Home** is empty. Either of those overrides the portal's own redirect.

**Something else is wrong.**
See section 29.

---

## 29. Getting help

1. **Reload the page.** This clears most one-off problems.
2. **Sign out and sign in again.** This fixes problems after a permission change.
3. **Report it with details.** Tell your administrator what you were doing, which project or file, the exact message, and roughly what time. The time matters most, because it lets them find the entry in the Desk's **Error Log**.

Other guides:

- The short public **handbook** at `/handbook`.
- For System Managers: the tester guide at `/test-guide`, and the technical guide at `/tech-guide` (both need a System Manager login).

For System Managers, portal entries in the **Error Log** have titles such as:

- "Portal ZIP upload: <file>": a file inside an uploaded ZIP failed.
- "Portal: zip include <file ID>": a file was left out of a ZIP download.
- "External upload failed for <project>": the copy to an external drive failed.
- "sync_project_access_from_todo failed": a Desk **Assign To** did not update a project team.
- "Portal: cron revoke <share>": the hourly share expiry failed for one share.
- "Portal: share email" / "Portal: file share email": a share email could not be queued.
- "Portal: Failed creating project folders": the standard folder tree was not built.

For System Managers: after acceptance testing, disable the test logins used with the tester guide (Desk → **User** → untick **Enabled**), and ask the developer to remove them from the tester guide.

---

## Appendix A — Web addresses

All portal addresses start with `https://<your-ERP-address>/portal-app`.

| Page | Address |
|---|---|
| Sign in | `/portal-app/login` |
| Dashboard | `/portal-app/dashboard` |
| Projects | `/portal-app/projects` |
| One project | `/portal-app/projects/<project ID>` |
| Kanban | `/portal-app/kanban` |
| Gantt Chart | `/portal-app/gantt` |
| Calendar | `/portal-app/calendar` |
| Tasks | `/portal-app/tasks` |
| Daily Task | `/portal-app/daily-task` |
| Contracts | `/portal-app/contracts` |
| Files hub | `/portal-app/files` (add `?project=<project ID>` to open one project) |
| File Browser | `/portal-app/file-browser` |
| Shared | `/portal-app/shared-with-me` |
| Shares | `/portal-app/manage-shares` |
| Routing rules | `/portal-app/folder-rules` |
| File tools | `/portal-app/file-tools` |
| Teams | `/portal-app/teams` |
| Org Chart | `/portal-app/org-chart` |
| ATA AI Chat | `/portal-app/ai-chat` |
| Profile | `/portal-app/profile` |
| Admin | `/portal-app/admin` |
| Guest link page | `/portal-app/shared-folder?token=…` |
| Public handbook | `/handbook` |
| Old user guide address | `/user-guide` (opens `/handbook`) |
| Tester guide (System Managers) | `/test-guide` |
| Technical guide (System Managers) | `/tech-guide` |
| ERPNext Desk | `/app` |

Keyboard shortcuts:

| Keys | Action |
|---|---|
| Ctrl + B (Cmd + B) | Hide or show the side menu |
| Ctrl + K (Cmd + K) | Jump to search |
| Esc | Close the search results |
| Enter | Sign in; send an AI Chat question; add the top person in the Team search |
| Ctrl + Enter (Cmd + Enter) | Send a task comment |

---

## Appendix B — The full standard folder list

This is the built-in template (67 paths). Your site may use a changed template (see File tools).

```
01-DOCUMENTS/01-CLIENT DATA/01-BUSINESS CARD
01-DOCUMENTS/01-CLIENT DATA/02-TITLE DEED
01-DOCUMENTS/01-CLIENT DATA/03-ID
01-DOCUMENTS/01-CLIENT DATA/04-MASTER PLAN
01-DOCUMENTS/01-CLIENT DATA/05-AUTHORIZATION LTR
01-DOCUMENTS/01-CLIENT DATA/06-OTHERS
01-DOCUMENTS/02-LOCATION
01-DOCUMENTS/03-BUILDING SYSTEM
01-DOCUMENTS/04-DRAWINGS
01-DOCUMENTS/05-CONSTRUCTION PERMIT
01-DOCUMENTS/06-SITE PICTURE
02-CONCEPT/01-CONCEPT STUDIES/01-ARCHITECTURE
02-CONCEPT/01-CONCEPT STUDIES/02-INTERIORS
02-CONCEPT/01-CONCEPT STUDIES/03-LANDSCAPE
02-CONCEPT/01-CONCEPT STUDIES/04-TECHNICAL
02-CONCEPT/01-CONCEPT STUDIES/05-OPERATIONS
02-CONCEPT/01-CONCEPT STUDIES/06-LIGHTNING
02-CONCEPT/01-CONCEPT STUDIES/07-TRAFFIC
02-CONCEPT/01-CONCEPT STUDIES/08-FIRE FIGHTING
02-CONCEPT/01-CONCEPT STUDIES/09-PROJECT RENDERS
02-CONCEPT/02-SKETCH UP
02-CONCEPT/03-PERSPECTIVES
02-CONCEPT/04-FEASIBILITY STUDY/REF
02-CONCEPT/05-PRESENTATION
02-CONCEPT/06-REFERENCES/ATTLAYERS
02-CONCEPT/06-REFERENCES/SURVEY
02-CONCEPT/07-SCHEDULES & GUIDELINES
03-BALADIYA/01-DOCUMENTS
03-BALADIYA/02-BALADIYA PLANS
03-BALADIYA/03-AREA STATEMENT
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/1. ARCHITECTURAL
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/2. LANDSCAPE
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/3. INTERIOR DESIGN
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/4. CLIENT
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/INCOMING/5. BALADIYA
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/1. ARCHITECTURAL
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/2. LANDSCAPE
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/3. INTERIOR DESIGN
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/4. CLIENT
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/01-ARCHITECTURAL/OUTGOING/5. BALADIYA
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/02-STRUCTURAL/INCOMING
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/02-STRUCTURAL/OUTGOING
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/03-MECHANICAL/INCOMING
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/03-MECHANICAL/OUTGOING
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/INCOMING/1. ELECTRICAL DRAWINGS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/INCOMING/2. BILL OF QUANTITIES
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/INCOMING/3. PEN ASSIGNMENT
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/OUTGOING/1. ELECTRICAL DRAWINGS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/OUTGOING/2. BILL OF QUANTITIES
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/04-ELECTRICAL/OUTGOING/3. PEN ASSIGNMENT
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/INCOMING/1. PLUMBING DRAWINGS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/INCOMING/2. PLUMBING CALCULATIONS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/INCOMING/3. PEN ASSIGNMENT
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/OUTGOING/1. PLUMBING DRAWINGS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/OUTGOING/2. PLUMBING CALCULATIONS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/05-PLUMBING/OUTGOING/3. PEN ASSIGNMENT
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/1. SURVEY DRAWINGS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/2. DOCUMENTS
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/3. IMAGES
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/INCOMING/4. DATA
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/06-SURVEY/OUTGOING
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/07-TECHNICAL FEEDBACK/INCOMING
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/07-TECHNICAL FEEDBACK/OUTGOING
04-WORKGDRAWINGS/01-DOCUMENT TRANSMITTAL/08-TECHNICAL FEASIBILITY
05-SUPERVISION/01-DOCUMENT TRANSMITTAL
05-SUPERVISION/02-PROJECTS
06-CLIENT SUBMITTAL
```

---

## Appendix C — Limits and allowed file types

| Item | Limit |
|---|---|
| Share with a person | 1 to 365 days; default 30 |
| Guest link | 1 to 365 days; default 7 |
| Download as ZIP | 500 files or 500 MB |
| Upload ZIP | The .zip itself: about 25 MB by default. Each file inside: about 10 MB. At most 2000 files or 500 MB unpacked. |
| One file | Set by the administrator in the site configuration (`max_file_size`); default about 10 MB. The System Settings **Max File Size** field cannot raise it, but a smaller number there lowers it. |
| Company folder template | 200 rows |
| Projects list, Kanban, Tasks | 500 items each |
| Global search | 5 results per group |
| People and customer search boxes | 25 matches; type more of the name or email to narrow the list. An empty customer search shows the 25 most recently changed customers. |
| Calendar | 500 tasks |
| Task subject / milestone title | 140 characters |
| Task comment | 5000 characters |
| Password | At least 8 characters on Profile, project invite and reset; at least 6 on the Admin page. The site's password policy may ask for more. |
| Welcome and reset links | 72 hours on the ATA site (System Settings) |
| Contracts | `.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, `.png` |

**Blocked file types** (cannot be uploaded anywhere in the portal):

`.html` `.htm` `.xhtml` `.shtml` `.xht` `.svg` `.svgz` `.xml` `.xsl` `.xslt` `.js` `.mjs` `.cjs` `.jse` `.vbs` `.hta` `.php` `.phtml` `.php3` `.php4` `.php5` `.phar` `.jsp` `.asp` `.aspx` `.cgi` `.pl` `.py` `.sh` `.bash` `.exe` `.dll` `.scr` `.com` `.bat` `.cmd` `.msi` `.jar`

Capital letters make no difference: `.PHP` is blocked too.
