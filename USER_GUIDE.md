# ATA Project Portal — User Guide

**Last updated: 13 October 2026**

This is the complete guide to the ATA Project Portal. It is for everyone who uses it:

- **ATA staff**: Super Admins, Department Admins, Team Leads and Team Members.
- **Client contacts**: people at a client company who sign in to see their own projects. Their role is **Client Customer**.

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

5. [Dashboard (admins)](#5-dashboard-admins)
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
| Typical users | Super Admins | All staff and client contacts |
| Examples | Roles, users, settings, email set-up, audit lists | Projects, files, sharing, tasks, clients |

The portal does **not** keep a separate copy of your data. Every project, file, share, team and reminder is a normal ERPNext record. If you change something in the portal, you see the change in the Desk, and the other way round.

What the portal does for you:

| It does this | So that |
|---|---|
| Builds the same folder tree for every project | Anyone who opens a project knows where a title deed or a permit is. |
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
| **Frappe** | The framework ERPNext is built on. Some screens (for example the page where you choose a new password) are Frappe's own. |
| **Desk** | ERPNext's normal back-office screens, at `/app`. |
| **Portal** | This app, at `/portal-app`. |
| **DocType** | A type of record in ERPNext, like a table with its own form. Examples: Project, Customer, File, User. |
| **Record** | One entry of a DocType, for example one project. |
| **Role** | What a person is in the portal. There are five: Super Admin, Department Admin, Team Lead, Team Member and Client Customer (next five rows, and section 2). |
| **Super Admin** | The portal's top role. It sees and changes everything. In ERPNext it is the Frappe **System Manager** role. |
| **Department Admin** | Looks after one or more teams: sees their projects and manages their people. |
| **Team Lead** | Leads one team. Sees the team's projects and puts people on them. |
| **Team Member** | Ordinary staff. Sees only the projects they are on. |
| **Client Customer** | The role of every client login. It sees only its own customers' projects. |
| **Admins** | In this guide, Super Admins and Department Admins. |
| **System User** | A staff login. It can use the Desk. |
| **Website User** | A client login. It cannot use the Desk. |
| **Project team** | The people listed in the project's **Users** table in ERPNext. In the portal it is the **Team** card on the project page. |
| **Lead Architect** | The person named in the project's **Portal Project Manager** field. The portal calls this person the Lead Architect. |
| **Assign To** | ERPNext's way of assigning a record to a person. It creates a **ToDo** entry for them. |
| **DocShare** | ERPNext's "share this record with this person" entry. The portal uses it when you share a folder or file. |
| **Department** | An ERPNext record. The portal uses Departments as **teams**. |
| **Team** | A group of staff in one office. In ERPNext it is a Department. For a Team Lead or a Department Admin, their team decides which projects they see. For a Team Member, being in a team opens no project by itself (section 2.2). |
| **Portal Team** | The one team a project is filed under, so the Gantt chart can group projects. |
| **Kanban stage** | ATA's working stage for a project: Planning, Active, On Hold, Review or Done. |
| **Portal code** | ATA's own project number, for example 2601. It is different from the Project ID (PROJ-0001). |
| **Files hub** | The Files page for one project (side menu → **Files**). |
| **File Browser** | A page to browse files across all projects. |
| **Incoming** | The folder inside 06-CLIENT SUBMITTAL for what ATA sends to the client. **Submit to Client** puts files here. |
| **Outgoing** | The folder inside 06-CLIENT SUBMITTAL for what the client sends to ATA. It is the only place a client can upload. |
| **Revoke** | Take back access that was shared. |
| **Customer** | An ERPNext record for a client company. |
| **Client contact** | A person at a client company with a portal login and the **Client Customer** role. |
| **Client login** | The account a client contact signs in with. The project page calls them **Client Customer logins** (the card of that name). The **Invite customer user** button and the **Add existing user** search work on the same accounts. |
| **Private file** | A file that only signed-in people with access can open. |
| **Guest link** | A share link that works without a login. The **Share folder** box calls it **Anyone with the link**. The **Shares** page calls it a **Public link**. |
| **Queued email** | An email saved in ERPNext's Email Queue and sent a few minutes later by a background job. |

---

## 2. Who can see and do what

### 2.1 The roles

Your role decides which projects you see, what you can change and which menu items you get. Often, when something looks broken, it is really this table working as designed.

The portal has **five roles**. Each person has one of them. In this guide, **admins** means Super Admins and Department Admins.

| Role | Who has it | Projects they see | Can change | Can upload | Sees project value |
|---|---|---|---|---|---|
| **Super Admin** | ATA's ERPNext administrators | Every project | Every project | Yes | Every project |
| **Department Admin** | People who look after one or more teams | The projects of their teams, the projects that belong to no team yet, and the projects they are on or lead | Every project they see | Yes | Only projects where they are the **Lead Architect** |
| **Team Lead** | The one person who leads a team | The projects of the team they lead, and the projects they are on or lead | Every project they see | Yes | No |
| **Team Member** | Ordinary ATA staff | **Only** the projects they are on or lead | Every project they see | Yes | No |
| **Client Customer** | People at a client company | Only their own customers' projects, and only the **06-CLIENT SUBMITTAL** folder (unless ATA has shared something with them) | Nothing | Only into **06-CLIENT SUBMITTAL / Outgoing** | No |

"On a project" means the person is listed on the project's **Team** card. "Lead" means the person is the project's **Lead Architect** (section 2.4). Section 2.2 explains who sees what.

**If you knew the old names:**

| Before October 2026 | Now |
|---|---|
| System Manager | Super Admin |
| Projects Manager | Department Admin |
| Team lead (a field on the team) and the **Team Manager** tick box | Team Lead |
| Projects User | Team Member |
| Portal Customer | Client Customer |

**In ERPNext**, the roles are these:

| Portal role | ERPNext role behind it |
|---|---|
| Super Admin | **System Manager** (the Frappe role) |
| Department Admin | **Department Admin**, a marker role. The teams come from the **Portal Department Admins** table on each Department. |
| Team Lead | **Team Lead**, a marker role. The team comes from the **Portal Team Lead** field on the Department. |
| Team Member | **Projects User** |
| Client Customer | **Client Customer** |

The two marker roles are not permissions on their own. The Department decides which teams they apply to. Give them from the Org Chart (section 19), or on the Department in the Desk. ERPNext then keeps the roles in step with the Department.

Two extra things can be added to a person:

- **Auditor** (an ERPNext role). It lets the person edit the company-wide folder template in **File tools**. It does not open the portal by itself. The person also needs one of the roles above. Auditor is a standard ERPNext role. It also opens many accounting reports and records in the Desk, so give it only to people who may see those.
- **Lead Architect**. This is not a role. It is a title one project gives to one person (section 2.4).

> **Note.** The ERPNext **Administrator** account holds every role. The portal treats it as a Super Admin.

> **Note.** Never give one login both a staff role and **Client Customer**. A login with **Client Customer** and **Team Member** or **Team Lead** (but not Super Admin or Department Admin) is treated as a **client**: it sees only its linked customers' projects and only 06-CLIENT SUBMITTAL. Only the **Super Admin** or **Department Admin** role overrides the client role. The Admin page does not allow the combination, but the Desk does.

### 2.2 Who sees which projects

This is the most important rule. **You see the projects your role gives you, and no others.**

| Role | Sees these projects |
|---|---|
| **Super Admin** | Every project. |
| **Department Admin** | The projects of the teams they administer, **plus** the projects that belong to no team yet (so somebody can put them under a team), **plus** the projects they are on or lead. |
| **Team Lead** | The projects of the team they lead, **plus** the projects they are on or lead. Never the projects that belong to no team. |
| **Team Member** | Only the projects they are on or lead. |
| **Client Customer** | Only the projects whose **Customer** is one of theirs. |

A project **belongs to a team** when its **Portal Team** (section 7.5) is that team, or when somebody from that team is on its Team card or is its Lead Architect. A project that belongs to no team is seen by Department Admins, Super Admins and the people on it. A Team Lead does not see it unless they are on it or lead it.

- **A new Team Member sees no projects at first.** They can sign in, but their **Projects** list is empty (it says "No projects match your filters."), and so are the Kanban board, Gantt chart, Calendar, Tasks, the Files hub and the search. They can still use **Daily Task**, **Profile** and **Shared** (files other people shared with them). A project appears for them as soon as somebody puts them on it: a Super Admin, a Department Admin, a Team Lead or the project's Lead Architect adds them to the project's **Team** card (section 7.6), or does it from the Org Chart with **Assign to project…** (section 19.3).
- **What you see, you can change.** A staff member can edit, rename and delete the projects they see, move them on the Kanban board, upload to them and share from them. A client contact can open their projects but change nothing. Narrower rules apply to project money (section 2.5), to the Team card, the Portal Team and the client logins (section 2.3).
- **Being in a team is not the same as being on a project.** For a Team Lead and a Department Admin, the team is their scope: it decides which projects they see. For a Team Member, being in a team opens no project. Only the project's own **Team** card does.
- **Being on any project team counts as portal access.** A login on a project team can sign in and see that project, even without a portal role (it then counts as a Team Member). This includes someone added with **Assign To** on a Project in the Desk. Only put ATA staff on project teams. Client logins cannot join a project team: the portal refuses them, and a Desk **Assign To** does not add them to the team. Still, never assign a project to a client login (also not through **Assign To User Group**) or to an outside person.

> **Note.** These rules apply in the portal. In the ERPNext Desk, the standard **Projects User** role has wider rights over Projects than the portal gives (for example, ERPNext lets that role edit and delete a Project). Keep staff working in the portal, and give Desk access with care.

### 2.3 Who can do each task

"On the project" means the person sees it (section 2.2). "Team card" means the project's **Team** card (the **Users** table in ERPNext).

| Task | Super Admin | Department Admin | Team Lead | Team Member | Client Customer |
|---|---|---|---|---|---|
| Open and read a project | Every project | Their teams' projects, the projects of no team, their own | Their team's projects, their own | Only projects they are on or lead | Only their customers' projects |
| See the project value | Yes | Only if Lead Architect | No | No | No |
| Create a project | Yes | Yes | Yes, while the setting **Allow any portal user to create projects** is ticked (on by default) | Yes, while the setting **Allow any portal user to create projects** is ticked (on by default) | No |
| Edit, rename or delete a project | Yes | Yes | Yes | Yes | No |
| Move it on the Kanban board, add milestones, create tasks | Yes | Yes | Yes | Yes | No |
| Link a Customer to the project | Yes | Yes | Yes | Yes | No |
| Add people to the Team card | Yes | Yes | Yes | Only as the project's Lead Architect | No |
| Remove people from the Team card | Yes | Yes | No | No | No |
| Set the Portal Team (Gantt grouping) | Yes, any team | Yes, only a team they administer | Only as Lead Architect (the list offers the team they lead) | Only as Lead Architect (the list is empty, so ask an admin) | No |
| Change the Lead Architect once it names someone else | Yes | Yes (not to themselves) | No | No | No |
| Upload files | Yes | Yes | Yes | Yes | Only into 06-CLIENT SUBMITTAL / Outgoing |
| Submit a file to the client (File Browser) | Yes | Yes | Yes | Yes | No |
| Share a folder or file, create a guest link | Yes | Yes | Yes | Yes | No |
| Rename folders (not the client folders), delete anyone's file, revoke anyone's share | Yes | Yes | Yes | Yes | No |
| Add an existing client login to a customer | Yes | Yes | No | No | No |
| Invite a new client login | Yes | Only with ERPNext's permission to create Users (see note) | No | No | No |
| Remove a client login from a customer | Yes | Yes | Yes | Yes | No |
| Reset a client's password (project page) | Yes | No | No | No | No |
| Dashboard and Contracts | Yes | Yes | No | No | No |
| Open the Org Chart | Yes, and edit it | Yes, and edit their teams | Yes, and assign people to projects | No | No |
| Teams page | Every team; the only role that can create a team | Sees every team; edits only the teams they administer | No | No | No |
| Change a person's role in a team, or remove them from it | Yes, any team | Their teams only; not a Department Admin or a Super Admin | No | No | No |
| Make or remove a Super Admin | Yes (not themselves, never the last one) | No | No | No | No |
| Reset someone else's password from the portal | Any login except their own: an email link, or a new password | The Team Leads and Team Members of their teams: an email link only | No | No | No |
| Create a login (Admin page) | All five roles | Only with ERPNext's permission to create Users: Team Lead, Team Member or Client Customer | No | No | No |
| Edit the company folder template (File tools) | Yes | Only with the Auditor role | Only with the Auditor role | Only with the Auditor role | No |
| Save routing rules | Yes | Yes | No | No | No |

> **Note.** Inviting a new client login and creating logins on the Admin page need ERPNext's permission to **create Users**. A Super Admin has it. A Department Admin has it only if a Super Admin has given it to them in the Desk.

> **Note.** The server checks every one of these rules. Hiding a button is only a convenience. A button that is hidden from you is refused if it is called some other way.

### 2.4 The Lead Architect (Portal Project Manager)

Each project can name one **Lead Architect**. In ERPNext this is the **Portal Project Manager** field on the Project.

Being the Lead Architect gives four things:

1. **The project is yours.** You see it and may change it, even when you are not on its Team card.
2. **Money (Department Admins).** A Department Admin sees a project's value only when they are its Lead Architect.
3. **Team.** The Lead Architect may add people to the project's Team card. They may not remove people. Only Super Admins and Department Admins can.
4. **Gantt grouping.** The Lead Architect may set the project's Portal Team.

Rules for changing it:

- A **Super Admin** may name anyone, or clear it.
- A **Department Admin** may name anyone else, or clear it. They may not make themselves the Lead Architect of a project that somebody else leads. Ask a Super Admin.
- A **Team Lead** or **Team Member** may only claim a project that has no Lead Architect. Once it names someone else, only a Super Admin or a Department Admin can change it.
- Saving a project without changing the Lead Architect (for example in **Edit Project**, section 6.5) is not a change, so anyone who can change the project can save it.
- A client login can never be the Lead Architect.

In practice only Super Admins and Department Admins can pick a Lead Architect in the portal. The **Lead Architect** / **Select Architect** list is empty for Team Leads and Team Members, so they must ask an admin. For admins the list shows every enabled login (up to 200), client logins included. Never pick a client login.

### 2.5 Who sees money

The project's value is the ERPNext field **Estimated Cost** (shown in SAR).

| Person | Sees value on |
|---|---|
| Super Admin | Every project |
| Department Admin | Only projects where they are the Lead Architect |
| Everyone else (Team Leads, Team Members and clients) | No project |

This rule applies everywhere money appears: the Dashboard, the Projects list, the project page and ATA AI Chat. So two admins can correctly see different totals. The project's other money fields (for example billing totals and the margin) are hidden from the same people.

### 2.6 How ATA is set up today

At the October 2026 update, ATA's existing logins were carried over to the five roles:

- ERPNext administrators are **Super Admins**.
- People who held the old manager role became **Department Admins of every team**. Because they administer every team, they keep seeing and managing every project, as before. A Super Admin can narrow a Department Admin to fewer teams from the Org Chart.
- People who already led a team became **Team Leads**.
- Everyone else on staff is a **Team Member**. A Team Member now sees only the projects they are on. Before the update, every staff member could open every project. Until someone puts a Team Member on a project, their Projects list is empty.
- Client contacts are **Client Customers**. They see only their own company, as before.

---

## 3. Signing in and your account

### 3.1 Signing in

**To sign in:**

1. Open `https://<your-ERP-address>/portal-app` and bookmark it.
2. In **Email / Username**, type your work email.
3. In **Password**, type your password. Click the eye button to show or hide it.
4. Click **Sign In**.

Where you land:

- Super Admins and Department Admins go to the **Dashboard**.
- Everyone else (Team Leads, Team Members and Client Customers) goes to **Projects**.

Good to know:

- The **Remember me** box has no effect.
- If your login has no portal role, you are signed out again straight away. The screen then shows "Server error. Please try again." Ask an administrator to give you a portal role (ordinary staff are Team Members), or to put you on a project's **Team** card.
- A new Team Member can sign in at once, but sees no projects until somebody puts them on one ([section 2.2](#22-who-sees-which-projects)).
- If you forget your password, click **Forgot Password?** under the **Password** box ([section 3.3](#33-forgot-password)).

**In ERPNext:** the portal uses ERPNext's normal login. It then checks that you have a portal role (or are on a project team). If you do not, it signs you out.

### 3.2 First time: setting your password

There are two ways you get your first password.

- **You get a welcome email.** Its subject is "Welcome to …" or "Complete Registration". It has a **Complete Registration** button. Click it and choose a password.
  - Client contacts are then taken straight into the portal.
  - Staff are usually taken to the ERPNext apps screen (`/apps`), or to the default app if one is set in System Settings. Click the **Project Portal** tile, or open `/portal-app` yourself.
- **You got no email.** Some staff logins were created without a welcome email. Use **Forgot Password?** (next section) to set your first password.

> **Note.** The link in the email expires. On the ATA site it lasts **72 hours**. A Super Admin sets this in the Desk under **System Settings → Reset Password Link Expiry Duration**. If it has expired, use **Forgot Password?** or ask for a new link.

### 3.3 Forgot password

You can ask for a reset link yourself, on the portal's own sign-in screen. It does not send you to ERPNext's page, and nobody has to know your old password.

**To reset your own password:**

1. On the sign-in screen, click **Forgot Password?** (next to **Remember me**). The same card now says **Reset your password**.
2. In **Email**, type the email of your account. If you had already typed your email in the sign-in box, it is filled in for you.
3. Click **Send reset link**. A green message appears: "If that address belongs to a portal login, a reset link is on its way."
4. Open the email "Password Reset" and click **Reset your password**.
5. Choose a new password.

To go back without sending anything, click **Back to sign in**.

What to know:

- **The answer is always the same.** The portal never tells you whether the address has a login, so nobody can use the form to find out who has an account. If no email arrives, check how you spelled the address, then see [section 28](#28-faq-and-troubleshooting).
- **Only portal logins get a link.** A disabled login, or an address that is not a portal login, gets no email, but sees the same green message.
- **The email is queued**, like every portal email. It normally arrives within a few minutes.
- **The link has a lifetime.** On the ATA site it works for **72 hours**. A Super Admin sets this in System Settings (see 3.2). A newer link replaces the older one.
- **There is a limit.** To stop misuse, the form accepts at most five requests an hour from the same internet address. After that, wait and try again.
- **Where you land.** A client contact who chooses a new password is taken straight back into the portal. Staff go where ERPNext normally sends them after choosing a password (usually the apps screen, `/apps`): click the **Project Portal** tile, or open `/portal-app` yourself.

**In ERPNext:** the portal asks ERPNext for a normal password-reset link and queues ERPNext's "Password Reset" email. Choosing the new password then happens on ERPNext's own page.

Administrators can also send you a reset link (or, for a Super Admin, set a new password for you): see [section 3.8](#38-resetting-someone-elses-password-administrators).

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
- **Portal role**: your role (Super Admin, Department Admin, Team Lead, Team Member or Client Customer). A Department Admin or Team Lead also sees the teams it applies to, for example "Team Lead · TEAM A".
- **Roles**: the ERPNext roles you hold, the portal ones first. A Super Admin shows **System Manager** here, and a Team Member shows **Projects User**. Click **+N more** to see the rest, and **Show fewer** to hide them.
- **Portal permissions** (only if it applies): how many projects you can manage, what the Org Chart lets you do, and whether you can edit the company folder template. Buttons **Open Files**, **Org Chart** and **File tools**.
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

> **Note (password expiry).** If a Super Admin has switched on **Force User to Reset Password** in System Settings, changing your password here does not restart that clock. When ERPNext asks for a new password, sign in once at `https://<your-ERP-address>/login` (ERPNext's own sign-in page) to set it.

### 3.7 Notifications (the bell)

The bell at the top right shows your recent ERPNext notifications. Examples: someone assigned you to a project or a team, or mentioned you. A number shows how many are unread.

- Click the bell to open the list. It shows your latest 20.
- Click **Mark all read** to clear the count.
- Click one item to mark it read and open it. A project opens its project page. A task opens the Tasks page.
- The bell checks for new items every minute.

**In ERPNext:** these are the same notifications as the bell in the Desk (the **Notification Log**).

### 3.8 Resetting someone else's password (administrators)

**Who:** Super Admins and Department Admins. Your own password is changed on **Profile** (section 3.6).

| Who resets | Whose password | How |
|---|---|---|
| **Super Admin** | Any enabled login except their own, staff and clients | **Email a reset link**, or **Set a password now** |
| **Department Admin** | The Team Leads and Team Members of the teams they administer | **Email a reset link** only |
| Everyone else | Nobody | — |

A Department Admin cannot reset a Super Admin, another Department Admin or a client contact. Nobody can reset the built-in Administrator account.

You can do it in three places:

- **Org Chart:** click the person, then **Reset password…** ([section 19.3](#193-what-each-button-does)).
- **Admin page:** the **Reset a password** card ([section 20.5](#205-reset-a-password)).
- **Project page:** the **Client Customer logins** card, **Reset password** next to a client contact (Super Admins only; [section 23.10](#2310-resetting-a-clients-password)).

The two ways:

- **Email a reset link** (recommended). The person gets the "Password Reset" email and chooses their own new password. You see "A reset link is on its way to <email>." The link lasts as long as System Settings says (72 hours on the ATA site). If no outgoing email account is set up, you get "No outgoing email account is configured, so the reset link could not be sent."
- **Set a password now** (Super Admins only). Type a new password of at least 8 characters. The site's password policy may ask for more. The person is signed out on every device. No email is sent, so you must pass the password on yourself, by phone or another separate channel, never in the same message as their email address. Ask them to change it on **Profile** at once.

Each new reset link makes any earlier link stop working.

---

## 4. Finding your way around

### 4.1 The screen layout

- **Side menu** on the left. Hide or show it with the arrow button, or press **Ctrl + B** (**Cmd + B** on a Mac). The portal remembers this in your browser.
- **Top bar** across the top.
- **Page** in the middle. Only the page scrolls; the menu and top bar stay in place.

If a page crashes you see a box "Something went wrong". Click another menu item to clear it, or reload the page.

### 4.2 The side menu for each role

| Menu group | Item | Super Admin | Department Admin | Team Lead | Team Member | Client Customer |
|---|---|---|---|---|---|---|
| **Project Management** | Dashboard | Yes | Yes | No | No | No |
| | Org Chart | Yes | Yes | Yes | No | No |
| | Projects | Yes | Yes | Yes | Yes | Yes |
| | Teams | Yes | Yes | No | No | No |
| | Gantt Chart | Yes | Yes | Yes | Yes | No |
| | Tasks | Yes | Yes | Yes | Yes | No |
| | Daily Task | Yes | Yes | Yes | Yes | No |
| | Kanban | Yes | Yes | Yes | Yes | No |
| | Calendar | Yes | Yes | Yes | Yes | No |
| | Contracts | Yes | Yes | No | No | No |
| **AI** | ATA AI CHAT | Yes | Yes | Yes | Yes | No |
| **Team Structure** | ATA Teams (head count per team) | Yes | Yes | No | No | No |
| **Files** | Files | Yes | Yes | Yes | Yes | Yes (06-CLIENT SUBMITTAL only) |
| | File Browser | Yes | Yes | Yes | Yes | Yes (06-CLIENT SUBMITTAL only) |
| | Shared | Yes | Yes | Yes | Yes | Yes |
| | Shares | Yes | Yes | Yes | Yes | No |
| | Routing rules | Yes | Yes | No | No | No |
| | File tools | Yes | With Auditor role | With Auditor role | With Auditor role | No |
| **Account** | Profile | Yes | Yes | Yes | Yes | Yes |
| | Admin | Yes | Yes | With Auditor role | With Auditor role | No |

> **Note (Shares).** **Shares** appears once you can open at least one project. A Team Member with no project yet does not see it.

> **Note (Admin).** A Department Admin sees **Admin** for the **Reset a password** card, and for **Create portal user** only if they hold ERPNext's permission to create Users. Anyone with the Auditor role sees **Admin** too, with only the **Project folder structure** card (section 20).

> **Note (clients).** Tasks, Kanban, Calendar, Gantt Chart, Daily Task and ATA AI Chat are ATA's internal working tools. If a client contact opens one of them by its address, the portal takes them back to **Projects**. See [section 22](#22-for-clients-how-to-use-the-portal).

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
| **New Project** | Opens the new project form on the Projects page. It is shown only to people who may create projects (section 6.4). Client contacts never see it. |
| Your name and email | Shown for information. |
| Picture or initials | Menu with **Profile**, **Switch to Desk** and **Logout**. |

The mode, colour theme and menu state are saved **in this browser only**. They do not follow you to another computer.

**Switch to Desk** opens ERPNext's Desk. Client logins cannot use the Desk and see a "not permitted" page.

### 4.4 Global search

**To search:**

1. Click the search box (or press **Ctrl + K**).
2. Type at least 2 letters.
3. Results appear in three groups: **Projects**, **Tasks** and **Teams**, up to 5 each.
4. Click a result. A project opens its page. A task opens the Tasks page. A team opens the Teams page (people who are not Super Admins or Department Admins go to Projects instead).
5. Press **Esc** to close the results.

What it searches:

- **Projects**: by project name or portal code. It does not search the project ID (such as `PROJ-0001`) or the customer.
- **Tasks**: by task subject.
- **Teams**: by team name.
- Client contacts get only **Projects** results, never tasks or teams.
- It does **not** search files. To find a file, use the Files hub or the File Browser (section 15).

You only get results from projects you are allowed to see.

---

# Part B — Projects and planning

<a id="5-dashboard-managers"></a>

## 5. Dashboard (admins)

**Who:** Super Admins and Department Admins only. Others are sent to Projects.

**Where:** side menu → **Dashboard**. The page greets you with "Welcome back, <your name>".

All numbers are live from ERPNext. They cover the projects you can see ([section 2.2](#22-who-sees-which-projects)): a Super Admin sees the whole portfolio, a Department Admin the projects of their teams and the projects that belong to no team. Money figures follow the rule in [section 2.5](#25-who-sees-money).

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
- **All accessible / I'm a team member / I manage**: show all the projects you can see, only the ones whose Team card you are on, or only the ones you can change.
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
| **Lead Architect** | Super Admins and Department Admins only. |
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

**Who:** Super Admins and Department Admins. Also Team Leads and Team Members while the Desk setting **Allow any portal user to create projects** is ticked. It is ticked by default. Client contacts never can. The **New project** buttons are shown only to people who may create projects.

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
   - **Estimated Cost (SAR)** (admins only)
   - **Servers (links)**: T-Server (Google Drive link), A-Server (Autodesk link), ERP Server (client server link)
   - **Remarks**
3. Click **Save Changes**.

Only the boxes you changed are saved. Everything else stays as it was.

> **Good to know about this form.**
> - **Lead Architect.** It changes only if you pick a different person. Once it names someone else, only a Super Admin or a Department Admin can change it (others get "Only a Super Admin or a Department Admin can reassign the Lead Architect."). Everyone who can change the project can still save the rest of the form. Team Leads and Team Members see the box empty, because the list is for admins; saving keeps the current Lead Architect.
> - **Remarks** open with the text saved on the project, shown as plain text. If you change them, they are saved as plain paragraphs, so any formatting added in the Desk (bold, lists, links) is lost. If you do not touch **Remarks**, they are not changed.
> - **Progress** is normally worked out by ERPNext from the project's tasks. The slider value is replaced, unless the project's **% Complete Method** in the Desk is set to **Manual**.
> - **Status.** ERPNext itself only knows the statuses Open, Completed and Cancelled. **In Progress** and **On Hold** stay when you save this form again, assign the Lead Architect or set the Portal Team. Other changes turn them back to Open or Completed: **Rename project** on the project page, Kanban stage, team, customer, milestones, a save in the Desk, and any task of the project being created, changed or deleted (ERPNext also re-checks overdue tasks every night). Use the **Kanban stage** for working stages instead.
> - If the project's **% Complete Method** is **Manual**, task changes leave the status alone, but the other changes above fail with a "Status cannot be…" error while the status is **In Progress** or **On Hold**. Set the status back to **Open** in this form first.
> - Estimated Cost is ignored for people who cannot see the value.

### 6.6 Assigning the Lead Architect

**To set the Lead Architect:**

1. Click the user-plus **Manage members** button on the project row.
2. In **Assign Architect**, choose a person in **Select Architect**.
3. Click **Assign**.

The rules in [section 2.4](#24-the-lead-architect-portal-project-manager) apply. If the save is refused, nothing is shown on screen. Ask a Super Admin.

If **Select Architect** is empty, you are not an admin. Ask a Department Admin or a Super Admin.

### 6.7 Deleting a project

**Who:** anyone who can change the project. This includes Team Members.

> **Warning.** Deleting cannot be undone. Only do it for projects made by mistake. Back up first:
> - In the Files hub, clear any search and set **Subfolder filter** to **All locations**. The header tick box ticks only the rows shown.
> - Click **Download as ZIP**. One ZIP holds at most 500 files or 500 MB, so for a big project download folder by folder.
> - Contracts are not in the Files hub. Open and save each one from the **Contracts** page (Super Admins and Department Admins).
> - Open the ZIP and check that the number of files matches before you delete.

**To delete a project:**

1. Back up the files first. Follow the box above.
2. Click the bin **Delete project**.
3. Click it again within 3 seconds. The bin turns red (its tooltip says "Click again to confirm delete").

This deletes the ERPNext Project **and every file attached to it**: all uploads in its folders, client uploads and its contracts. The files are removed from the server and cannot be recovered from the portal. The empty folder tree is left behind in the File Manager.

In the Desk, every deleted project and file is listed under **Deleted Document**, with who deleted it and when. A Super Admin can try to restore the Project record there, but the files themselves cannot be restored. If you delete the newest project, ERPNext gives its ID to the next project created, so old links to that ID will open the new project.

ERPNext refuses the delete if other records still point to the project: tasks, timesheets, or any share record, including shares that were already revoked. You then see "Could not delete project". So a project that was ever shared cannot be deleted from the portal. Ask a Super Admin. Do not delete share records yourself (see [section 24](#24-where-things-live-in-erpnext-desk-for-administrators)).

---

## 7. The project page

**Where:** click a project on the Projects list. The address is `/portal-app/projects/<project ID>`.

**Who:** anyone who can open the project. Buttons that change things appear only for people who can change the project. Client contacts do not see the **Tasks** button or the **Portal Team**, **Team** and **Tasks** cards.

### 7.1 Header

- **Back to projects** returns to the list.
- The header shows the status, the Kanban stage, the title and the project ID.
- **Files** opens the Files hub for this project.
- **Tasks** (staff only) opens the Tasks page filtered to this project.
- **Rename project** (people who can change the project): type a new title and click **Save title**. The project ID never changes.

> **Note.** Every project title must be unique. If another project already has the same title, ERPNext refuses the save with a duplicate error. Use a different title, for example add the portal code.

### 7.2 Summary cards

**Status**, **Kanban stage**, **Client**, **Timeline** (start and end dates), **Estimated cost** (admins only; shows "—" if you may not see the value) and **Progress**.

### 7.3 Customer card

This links the project to a client company (an ERPNext **Customer**). The client contacts of that customer can then see this project.

**Who can change it:** anyone who can change the project (every staff member who sees it). Client contacts see the customer link but cannot change it.

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

### 7.4 Client Customer logins card

This card appears when you can change the project **and** the project has a customer. It lists everyone who can sign in and see this customer's projects.

- **People with access**: each person shows "Last signed in <when>" or "Invited — hasn't signed in yet".
- **Invite new user** (Super Admins, and Department Admins who may create Users in ERPNext): create a new client login.
- **Reset password** (Super Admins only).
- **Remove from portal** (anyone who can change the project): takes away this customer only. The person's other customers stay.
- **Add existing user** (Super Admins and Department Admins): search and click to add an existing client login.

Buttons you may not use are not shown. Where you may not add logins, the card says "Only a Super Admin or a Department Admin can add Client Customer logins."

Disabled logins are not listed, and **Add** / **Remove from portal** do not change them. Enable the login in the Desk first if you need to manage it.

The full step-by-step is in [section 23](#23-for-ata-staff-giving-a-client-access-end-to-end).

### 7.5 Portal Team (Gantt grouping) card

This puts the project under one team, so the Gantt chart can group projects by team. It also decides which team's Team Lead and Department Admins see the project ([section 2.2](#22-who-sees-which-projects)).

**Who can save it:**

- A **Super Admin**: any team.
- A **Department Admin**: only a team they administer (or **Clear team**). For any other team they get "A Department Admin can only put a project under a department they administer."
- The project's own **Lead Architect**, whatever their role.

Everyone else gets "Only a Super Admin, a Department Admin, or the project's own Lead Architect can set its team."

A Lead Architect who is a Team Lead or a Team Member has more limits:

- The team list shows only the team a Team Lead leads. For a Team Member it is empty.
- **Create team** is refused for everyone except a Super Admin. Ask a Super Admin or a Department Admin.

**To set the team:**

1. Click **Search teams** to see teams, or type to filter.
2. Click a team.

Other buttons:

- **Create team (no duplicate name)** (Super Admins only) opens **New team** (**Team name**, **Office (optional)**). Click **Create and assign**. If the name already exists, the existing team is used.
- **Clear team** removes the team.

**In ERPNext:** the project's **Portal Team** field points to a **Department**.

### 7.6 Team card

The team is the list of people the project belongs to. A Team Member sees a project only while they are on it. Everybody on it can change it.

**Who can add people:** Super Admins, Department Admins and Team Leads (on the projects they see), and the project's own Lead Architect.

**Who can remove people:** Super Admins and Department Admins only.

Everyone else sees the card without controls: "View only. A Team Lead, Department Admin or Super Admin adds people to a project." Someone who can add but not remove sees: "You can add people to this project. Only a Super Admin or a Department Admin can remove them."

The number next to the title **Team** is how many people are on it. Each person is shown with their name and email, and a **Lead Architect** tag where it applies. There is no separate save step: people are added and removed at once.

**To add people:**

1. In **Add user**, click to see users or type part of a name, email or username. Click a person (or click **Add** next to them) to add them. Pressing **Enter** adds the top match. The list offers staff only: client logins are never shown. People already on the team show "on team".
2. Or click **Add from org chart**. Tick people, who are grouped by team, and click **Add N to the team**. People already on the project are greyed. Admins also get a **Not in a team yet** group. This button is shown to people who can open the Org Chart: Super Admins, Department Admins and Team Leads.
3. Or choose a group in **Or add a whole User Group** and click **Add group** (Super Admins and Department Admins only).

You see "Added to the team." or "N people added to the team."

**To remove someone** (Super Admins and Department Admins): click **Remove** next to the person and confirm. You see "Removed from the team."

> **Note.** If you add a person whose login is disabled, you get "User is disabled: <login>". A disabled person who is already on the team can still be taken off with **Remove**.

> **Note.** A client login cannot join a project team. If one is in a User Group you add, or was on the team from before, you get "Client contacts cannot be added to the project team: <login>". A Super Admin or Department Admin must **Remove** them first. Client contacts get their access through the **Client Customer logins** card instead (section 7.4).

**In ERPNext:**

- The people are saved in the project's **Users** table.
- Each person also gets an **Assign To** on the project (a ToDo).
- ERPNext emails each person you add a "Project Collaboration Invitation".

> **Note.** It also works the other way. If someone assigns the project to a person in the Desk (**Assigned To** in the sidebar), that person joins the team. If the assignment is closed or cancelled (for example ticked done in their To Do list), they leave the team. Client logins are the exception: a Desk assignment never adds them to the team. Even so, never assign a project to a client login in the Desk.

### 7.7 Files card

- **Open in Files hub** opens the Files hub for this project.
- **Staff** get an upload panel. It works like the Files hub (section 14), plus automatic copies from routing rules (section 14.10).
- **Client contacts** see "You can upload into 06-CLIENT SUBMITTAL / Outgoing from the Files hub." with a link.
- The file list shows each file with **Open**. A **private** tag appears where it applies. Files in the client folder carry a pill: **Sent to client** (in Incoming) or **From client** (in Outgoing). An orange **Client upload** badge appears only on a client's upload that sits outside Incoming and Outgoing (section 15.1).
- **Delete** appears for anyone who can change the project (any file), and for the person who uploaded the file (their own files). It asks you to confirm first.
- The **Share** button on the upload panel opens the share box in the Files hub for the chosen folder.

### 7.8 Tasks card

A list of the project's latest 50 tasks with their status. **Open task workspace** opens the Tasks page filtered to this project. Staff only: client contacts do not see this card.

---

## 8. Kanban board

**Who:** staff. The board shows the projects you can see, and you can move any of them.

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

People without rights get an error (usually "Could not save milestone."), because only people who can change the project can change its milestones ([section 2.3](#23-who-can-do-each-task)).

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

**Who:** staff. Client contacts cannot open this page. Creating a task needs the right to change at least one project. Saving a task row or commenting needs the right to change its project, or being assigned to the task.

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
  - An assignee who is not on the project team can no longer change it or comment on it. They see "Only project managers or assigned users can update this task." (Here "project managers" means anyone who can change the project.)
  - To reopen it, ask someone on the project team.

### 11.3 Comments

1. Click **Comments** on a row.
2. Type in the box and click **Send** (or press **Ctrl + Enter** / **Cmd + Enter**).

Comments can be up to 5000 characters. **In ERPNext:** they appear on the task's timeline in the Desk.

> **Note.** Tasks and their comments are internal to ATA. Client contacts cannot see them anywhere in the portal: not on the project page, not in search and not on the Tasks page.

### 11.4 Creating a task

1. Click **New task**.
2. Fill in **Subject \*** and **Project \*** (search; only projects you can change).
3. Optional: in **Assign to**, search by name or email and click a person. Only ATA staff logins are listed.
4. Fill in **Priority** and **Due date**.
5. Click **Create Task**.

The **Due date** must not be after the project's end date, or ERPNext refuses the task.

If you picked someone in **Assign to**, the task is assigned to them at once. It shows under their **Assigned to you (open)** and **Only my tasks**, they can update it and comment on it, and ERPNext sends them its usual assignment notification (not when you assign yourself). If the person is not an active staff login, the form shows "Assign the task to an active ATA staff login." and no task is created.

**In ERPNext:** the assignment is a normal **Assign To** (a ToDo) on the Task.

---

## 12. Daily Task (personal reminders)

**Who:** staff. Only Super Admins and Department Admins can put a reminder on someone else's board.

**Where:** side menu → **Daily Task**.

This is a private four-week reminder board. It is not linked to projects.

- **Prev 4 Weeks** / **Next 4 Weeks** move the board. "(Current)" marks the present four weeks.
- Click a day to see its reminders on a timeline from 7:00 to 19:00.
- Dots on each day show how many reminders there are (green = done, amber = open).

**To add a reminder:**

1. Click the day, then **Task**.
2. In **Add Task**, fill in **Title**, **Time** and **Color**.
3. (Admins only) In **Assign to (optional — defaults to you)**, search for a colleague.
4. Click **Add Task**.

A reminder you put on a colleague's board is **not** on your own board. To change or remove it later, use the Desk calendar (**Event**). The **Assign to** search lists only ATA staff logins.

Other actions:

- Click the circle to mark it done or not done.
- Click the title to edit the title or time, then **Save** (or **Cancel**).
- Click **×** to delete it. There is no confirmation.
- You cannot move a reminder to another day or change its colour. Delete it and add it again.
- If a change does not stick, reload the page. Errors are not shown on screen.

**In ERPNext:** each reminder is a private **Event**. The person who creates it stays its owner. So a reminder an admin creates for you shows on **your** board, but in the Desk it belongs to that admin. ERPNext may also send the owner a daily "Upcoming Events for Today" email.

The board uses the date on your own computer. Today's tile is highlighted and opens selected, with a **TODAY** badge in its heading. A reminder is saved on the day of the tile where you added it.

> **Note.** An older version of the portal saved reminders one day early (in Saudi time, always). Reminders added with that version may now show one day before the tile where you added them. If the day matters, delete the reminder and add it again.

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

This is the built-in ATA standard. (An Auditor or a Super Admin can change it; see section 17.1.)

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
| **06-CLIENT SUBMITTAL** | Everything exchanged with the client. **This is the only folder client contacts can see.** It holds two folders, Incoming and Outgoing. |
| └ Incoming | What ATA sends to the client. **Submit to Client** copies files here (section 15.5). |
| └ Outgoing | What the client sends to ATA. It is the only place a client can upload (section 22.4). |

The full list of 69 folder paths is in [Appendix B](#appendix-b--the-full-standard-folder-list). With parent folders counted, it makes 93 folders.

> **Note.** Some folder names are spelled exactly as they are in the system, for example **04-WORKGDRAWINGS** and **06-LIGHTNING**. Do not rename them.

> **Warning.** The portal finds the client folder and its two folders, **Incoming** and **Outgoing**, by their names. So they cannot be renamed: the **Rename** button is not shown on them. A project whose folder is spelled "06 - CLIENT SUBMITTAL" (with spaces) is found too, and needs no change. See [section 23.7](#237-if-the-client-cannot-see-the-folder).

> **Warning.** 01-CLIENT DATA holds IDs and title deeds. Never send a guest link to this folder or to the whole project folder.

### 13.3 When the folders are created

- **Project created in the portal**: the tree is built at once.
- **Project created in the Desk or by import**: the tree is built the first time someone uploads to it from the portal. Until then the Files hub shows only the project folder. See [section 28](#28-faq-and-troubleshooting) for how to start it.
- **Template changes** only reach projects that have no folders yet. Existing projects keep their folders. Folders are never renamed automatically.
- **Incoming and Outgoing** are part of every project. If a company template (File tools) leaves out 06-CLIENT SUBMITTAL, Incoming or Outgoing, the portal adds them to every new project anyway. Projects that already had folders got the two folders at the October 2026 update. The files that were lying loose in 06-CLIENT SUBMITTAL were sorted then: what a client had uploaded went to **Outgoing**, everything else to **Incoming**.
- There is **no "New folder" button**. Extra sub-folders appear when you upload (dated upload folders), use **Upload folder** or **Upload ZIP**, or when a routing rule creates a mirror folder.

---

## 14. Uploading files

### 14.1 Where you can upload

**Who:** all staff, on any project they can open. Client contacts upload only into 06-CLIENT SUBMITTAL / Outgoing (see section 22).

Staff can upload from two places:

| Place | Extras |
|---|---|
| **Files hub** (side menu → **Files**) | **Upload ZIP**, drag files onto a folder card. |
| **Project page → Files card** | **Browse folders** (step by step), automatic copies from routing rules. |

> **Note (the client folder).** To give files to a client, use **File Browser → Submit** (section 15.5), or choose **06-CLIENT SUBMITTAL / Incoming** as the destination folder. Files in Incoming are labelled **Sent to client**. Do not upload into **Outgoing**: it is the client's folder, and files in it are labelled as the client's. Files that sit in 06-CLIENT SUBMITTAL but outside both folders are still visible to the client, but carry no label.

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

The portal keeps every upload session in its own dated folder. This keeps history tidy. **Upload files** and **Upload folder** each put the upload into a new dated folder. **Upload ZIP** goes straight into the chosen folder, with no dated folder. So do a client's uploads, which go straight into Outgoing.

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
4. Wait while it shows **Extracting…**. Then you see "ZIP extracted: N file(s) uploaded, M failed." The file list and the folders refresh by themselves.

Good to know:

- The folders inside the ZIP are kept. If everything sits in one top folder, that top folder is dropped.
- All unpacked files are private.
- Blocked file types inside the ZIP are skipped and counted as failed. Hidden files and Mac `__MACOSX` folders are skipped silently.
- A `.zip` dragged onto the drop area or chosen with **Upload files** is stored as one ZIP file. Only the **Upload ZIP** button unpacks.
- The `.zip` itself must fit the site's upload limit. By default that is about **25 MB** for the whole ZIP, and a bigger ZIP is refused before anything is unpacked. Each file inside must be within the per-file limit (about **10 MB**), or it counts as failed. If the developer sets `max_file_size` in the site configuration, that one number becomes the limit for both. Split big ZIPs, or use **Upload folder**.
- The message shows only **how many** files failed, not which. Compare the folder with your ZIP, and upload any missing files with **Upload files** to see the reason.

### 14.7 Private and public

The **Private upload** box is ticked by default. **Leave it ticked.**

- **Private**: only signed-in people with access can open the file. In practice this means everyone who can open the project ([section 2.2](#22-who-sees-which-projects)), plus client contacts for files in 06-CLIENT SUBMITTAL or files shared with them.
- **Public**: **anyone** on the internet with the file's address can open it, with no login and no record.

Guest links and shares with named people both work with private files, so there is almost never a reason to untick the box. ZIP uploads and client uploads are always private.

> **Note.** The Files hub help box says private files can be opened only by "people on this project". That is nearly right. A Team Member opens files only on the projects they are on. A Team Lead or a Department Admin also opens files on the projects of their teams, and a Super Admin on every project.

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

**In ERPNext:** the file type is saved in the File's **Portal File Type** field. A Super Admin maintains the list in the Desk (**Portal File Type**).

**To add a file type** (Super Admin):

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
- **Project folder & subfolders**: the folders as **Grid** cards or a **Tree**. Click the arrow to open or close a folder. Each card shows how many files it holds. Inside 06-CLIENT SUBMITTAL, the cards **Incoming** and **Outgoing** carry a pill: **Sent to client** on Incoming and **From client** on Outgoing. Clients see **From ATA** and **Your uploads** instead.
- **Showing files in: <folder>**, with **Clear filter**, **Show all files** and **Use this folder for upload**.
- **Search file** and **Subfolder filter** (All locations, Project folder (all files), or one folder).
- **Client portal guidance**: the welcome text for clients, if the administrator wrote one.
- The staff upload card (section 14).
- The provider cards and the **File policy:** note, if set.
- The file table: **File** (with "(private)" and, where they apply, a pill: **Sent to client** for a file in Incoming, **From client** for a file in Outgoing; clients see **From ATA** and **Your upload**; an orange **Client upload** badge marks a client's upload that sits outside both folders), **Size**, **Subfolder**, **Owner**, **Upload date**, **Link**, **Share**, **Delete**.
- Round buttons at the side scroll to the top or bottom.

### 15.2 Opening and downloading

- **Open** (in the **Link** column) opens the file in a new tab. The portal checks your access first.
- **To download several files as one ZIP:**
  1. Tick the files (or the box in the header to tick all).
  2. The bar shows "N files selected".
  3. Click **Download as ZIP**. (**Clear** unticks all.)

  The ZIP is named `<project>-files.zip` and keeps the folder paths. The limit is 500 files or 500 MB.

  The header box ticks only the rows shown after your search and folder filter. If a file cannot be read, it is left out of the ZIP with no warning (a Super Admin finds it in the Error Log as "Portal: zip include …"). Check the number of files in the ZIP.

### 15.3 Renaming a folder

**Who:** anyone who can change the project.

1. Click **Rename** on a folder card or tree row.
2. In **Rename subfolder**, type the **New folder name**.
3. Click **Rename**.

Rules: one name only, no `/`, `\` or `..`. The name must not exist already. The project folder itself cannot be renamed. Folders at any level can be renamed, and the files inside move with the folder.

**06-CLIENT SUBMITTAL, Incoming and Outgoing cannot be renamed.** The portal finds them by name, so the **Rename** button is not shown on them, and the server refuses a rename.

> **Warning.** Shares and guest links made on the old folder name may stop working after a rename. Share the folder again after a rename.

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
- Each row has a share icon (staff), and **Submit** on projects you can change.

Client contacts see only the 06-CLIENT SUBMITTAL files of their own projects (Incoming and Outgoing), with no **Submit** or share buttons. Their files carry the pills **From ATA** and **Your upload**.

The File Browser remembers each project's files until you reload the page. Reload to see new uploads.

**To submit a file to the client (copy into 06-CLIENT SUBMITTAL / Incoming):**

1. Click **Submit** on the file's row.
2. The **Submit to Client** box says it copies to **06-CLIENT SUBMITTAL / Incoming**, and shows "Will be saved as NN_<today>_<file name>". `NN` is the next serial number in Incoming.
3. Click **Confirm & Submit to Client**.

You see "Submitted as "…" (SL n) to the client's Incoming folder." The original file stays where it was. The copy is private, in **Incoming**, and the client can see it at once, marked **From ATA**.

If you submitted the wrong file, open the Files hub, open **06-CLIENT SUBMITTAL / Incoming** and **Delete** the copy (you uploaded it, so you may delete it). The serial number `NN` is the number of files already at the top of Incoming plus one. So after a deletion, the next copy can get a number that is already used.

**Who:** anyone who can change the project: every staff member who sees it (Super Admins, Department Admins, Team Leads and Team Members). Client contacts do not see **Submit**. If the project has no client folder yet, the portal creates it, with Incoming and Outgoing, on the spot. Contract files can never be submitted to the client.

The share icon opens **Share File** (see 16.2).

---

## 16. Sharing files and folders

There are two kinds of sharing:

- **With a named person** who has a login. They see it on their **Shared** page.
- **With a guest link** for someone without a login.

**Who can share:** all staff, on any project they can open. Client contacts can never share. Contract files can never be shared (section 17.3).

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

> **Warning (client contacts).** A folder share lets a client contact open every file in that folder and its sub-folders, including files you add there later while the share is active. So share a folder with a client contact only if they may see everything in it. If they may not, copy the files into 06-CLIENT SUBMITTAL / Incoming instead (**File Browser → Submit**, section 15.5), or share single files.

> **Note.** Files you add to a shared folder later show on the person's **Shared** page by themselves while the share is active. You do not need to share again.

Sharing the same folder with the same person again **extends** the existing share. It does not make a second one. The share is then recorded as made by you. The colleague who shared it first can then no longer revoke it, unless they can change the project.

**In ERPNext:** a **Portal Folder Share** record is saved (the audit record). ERPNext **DocShare** entries give read access to the folder and to each file in it at that moment. A staff member also gets a read share on the project. A client contact never gets a share on the project record.

> **Note.** You can share with a colleague who is not on the project's team too. They find the folder on their **Shared** page. The share does not put them on the team, and the project does not appear in their Projects list. For a colleague who is already on the project, sharing mainly puts the folder on their Shared page and sends the email. Sharing matters most for **client contacts**.

If the box says "Sharing is running in basic mode. Expiry dates and public share links will be available once your administrator completes the portal setup.", tell your administrator. Sharing with people still works.

### 16.2 Sharing a single file

- In the Files hub, click **Share** in the file's row. The **Share file** box works like 16.1, without a guest link.
- In the File Browser, click the share icon. The **Share File** box lets you search "by name or email" and click a person. It always shares for 30 days and sends no email. **Shared with** lists people with a revoke button. Click **Done** to close.

A single-file share gives a client contact that one file only. (As in 16.1, a staff member also gets a read share on the project.)

### 16.3 Who may receive a share

The portal checks the person you choose:

- Staff: yes, whether or not they are on the project's team.
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

**Who:** staff who can change at least one project (that is, every staff member who can open a project). Client contacts, and staff with no project yet, are sent back to their start page (Projects).

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

**Who:** people with the **Auditor** role, and Super Admins. Others are sent back to their start page (Dashboard for admins, Projects for everyone else).

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

> **Note.** The client folder is always part of the template. Whatever the list says, every new project also gets **06-CLIENT SUBMITTAL**, **Incoming** and **Outgoing**, because the client features depend on them (section 13.3).

**In ERPNext:** the template is the **Subfolder template** table in **Portal Project Settings**.

### 17.2 Routing rules

**Who:** Super Admins and Department Admins. The page is not in anyone else's menu, and anyone else who opens its address is sent back to Projects. Only these two roles can **save** or **delete** rules.

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

**Who:** Super Admins and Department Admins.

**Where:** side menu → **Contracts** (lock icon). The page says "Management Only".

This is a locked-down place for signed contracts, apart from the normal project files.

1. On the left, use **Search projects…** and click a project.
2. Click **Upload Contract** and pick one or more files. Allowed types: `.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, `.png`. Each file must be within the site's file-size limit (default about 10 MB). The files are uploaded one by one. If one fails, the files after it are not uploaded. Click the project again to refresh the list, check which files are there, and upload the rest again.
3. Click a file name to open it.
4. Click the bin to delete it, and confirm "Delete "<name>"? This cannot be undone."

Contract files never appear in the Files hub or the File Browser. They cannot be shared with anyone, and they cannot be submitted to the client. Their **file names** (not their contents) can still appear to Super Admins and Department Admins in the Dashboard's **Recent Activity** and in ATA AI Chat answers about recent files, and to staff on the **Shares** page under "Project folder (all files)". Give contract files neutral names.

**In ERPNext:** contracts are private Files attached to the project, in the folder `Home / Contracts / <project ID>`. Give Desk access with care (see the note in 2.2).

---

# Part D — Teams, admin and AI

## 18. Teams

**Who:** Super Admins and Department Admins. A Super Admin sees and can edit every team, and is the only role that can **create** a team. A Department Admin sees every team too, but can edit (rename, change the office, add and remove people) only the teams they administer. Team Leads and Team Members have no Teams page. A Team Lead uses the Org Chart ([section 19](#19-org-chart)).

**Where:** side menu → **Teams**. The page is called **Teams & Members**.

ATA works across offices such as **RIYADH**, **LISBON** and **MANILA**. Each team belongs to one office.

What you see:

- Office buttons (**ALL** and each office) to filter.
- One card per team: the Team Lead's initials (or the first member's), member count, office, active and total projects, and member pictures. "Click to view members".

**To see a team's members:** click its card. The **Team Members** box opens. Under a name it shows the person's role when it is more than Team Member: **Team Lead**, **Department Admin** or **Super Admin**.

**To create a team** (Super Admins only):

1. Click **Create team**.
2. Type the **Team Name** and **Office (optional)**.
3. Click **Create team**. If the name already exists, the existing team is used.

**To edit a team** (a Super Admin, or the Department Admin of that team): click the pencil **Edit team**, change **Team Name** or **Office**, then **Save Changes**.

**Office** here offers only offices that already exist. To start a new office, type it in **Office** when you **Create team**.

**To add a member** (a Super Admin, or the Department Admin of that team):

1. Open the team and click **Add member**.
2. Type in "Search users or user groups".
3. Click a **User Group** to add everyone in it, or click a **User** to add one person.

The list shows enabled staff logins that are not on this team yet. Client logins are never offered. If a User Group holds a client login or a disabled login, the whole group is refused, and the message names that login.

**To make a person the Team Lead or a Department Admin:** use the Org Chart ([section 19.3](#193-what-each-button-does)). The Teams page does not change roles.

**To remove a member** (a Super Admin, or the Department Admin of that team): click the red **×** "Remove from team". There is no confirmation on this page (the Org Chart asks first). Only a Super Admin can remove a Department Admin. Removing someone from a team does **not** take them off any project. Do that on the project's **Team** card.

> **Warning.** A team without an **Office** does not appear on the Teams page, the Org Chart or the team pickers. Always give a team an office. Choosing "— Select —" in **Office** hides the team.

> **Note.** Being in a team does **not** open any project for a Team Member. A Team Lead sees the projects of the team they lead, and a Department Admin the projects of the teams they administer ([section 2.2](#22-who-sees-which-projects)). A Team Member's project rights come from the project's own **Team** card ([section 7.6](#76-team-card)).

**In ERPNext:**

- A team is a **Department** directly under "All Departments", with a **Portal Office**.
- A member is an open **Assign To** (ToDo) on that Department. If the member's ToDo is closed or cancelled (for example ticked done in their To Do list), they leave the team.
- The Team Lead is the Department's **Portal Team Lead** field. The Department Admins are the Department's **Portal Department Admins** table. Both are set from the Org Chart, on the Admin page for new users, or in the Desk. ERPNext keeps the **Team Lead** and **Department Admin** roles in step with them, whichever way you change them.
- Renaming a team changes its label only. The Department's ID keeps the old name.

---

## 19. Org Chart

**Who:** Super Admins and Department Admins run it. Team Leads open it too, but only to put people on projects. Team Members and client contacts do not have it.

**Where:** side menu → **Org Chart**. The page is called **Organization Chart**. You do not only look at it. You click a person, and the buttons your role allows appear.

### 19.1 What the page shows

- The top line says how many people and teams there are, and "You are <your role>". Four coloured labels show the roles: Super Admin, Department Admin, Team Lead and Team Member.
- A line of help says what a click does. A Team Lead sees "As a Team Lead you can click anyone to assign them to your team's projects."
- **All Offices** and the office buttons filter the teams. **Find a person…** searches by name or email and opens every team with a match. **Expand all** and **Collapse all** open and close the teams. At first only your own teams are open (the first team, if you have none).
- **Super Admins**: a block at the top with everyone who is a Super Admin.
- **One block per team**: its name, its office, how many people it has and, on your own teams, the tag **Your team**. Click the block's **+** or **−** to open or close it. Each person shows their name, their email, how many projects they are on, and a label for their role (a Team Member has none). A Super Admin who is also in a team shows the **Super Admin** label, and their team role too when it is more than Team Member. Department Admins come first, then the Team Lead, then the members.
- **Not in a team yet** (admins only; a dashed block at the bottom): staff who are in no team. Click one to add them to a team.
- A pencil **Manage team** on a team (section 19.4). It is shown only on teams you may edit.
- On the right, a panel for the person you click. With nobody chosen it says "Select a person". Below it, **Headcount Summary** shows numbers per office.

> **Note.** The numbers here count team memberships, so a person in two teams counts twice. The sidebar "ATA Teams" count uses ERPNext Employee records instead, so the two can differ.

### 19.2 Choosing a person

Click a person. The panel on the right shows their picture or initials, name, email, role label, the team you chose them in, and "On N projects". Under that come the controls your role allows (section 19.3). Click the same person again to close the panel.

### 19.3 What each button does

| Control | What it does | Who sees it |
|---|---|---|
| **Role in <team>** and **Save** | Sets what the person is in this team: **Team Member**, **Team Lead** or **Department Admin**. If they are not on the team yet, they are added first. | Super Admins: all three roles, in any team. Department Admins: Team Member and Team Lead, in their own teams, for people who are not Department Admins or Super Admins. |
| **Add to a team** and **Add** | For a person in no team: pick a team in **— Select team —** and click **Add**. | Super Admins and Department Admins. The list holds only the teams you may edit. |
| **Assign to project…** | Puts the person on projects (see below). | Super Admins, Department Admins and Team Leads. |
| **Reset password…** | Sends a reset link, or sets a new password (see below). | Super Admins (anyone but themselves). Department Admins (the Team Leads and Team Members of their teams). |
| **Remove as Team Lead** | Takes the person off as Team Lead. They stay on the team as a Team Member. You confirm first. | Super Admins, and Department Admins for their own teams. |
| **Remove from team** | Takes the person out of this team. You confirm first. If they were the Team Lead, the team has no lead afterwards. | Super Admins, and Department Admins for their own teams. Only a Super Admin removes a Department Admin. |
| **Make Super Admin** / **Remove Super Admin access** | Gives or takes the Super Admin role. You confirm first. | Super Admins, for anyone but themselves. |

Rules behind the buttons:

- A person has **one role per team**. Choosing a role replaces the one they had in that team.
- A team has **one Team Lead**. Naming a new one makes the previous lead a Team Member.
- Only a Super Admin can make or change a Department Admin. The **Department Admin** choice is offered only to Super Admins. For a Department Admin's row, everyone else sees "Only a Super Admin can change a Department Admin."
- You cannot change your own Super Admin role ("Ask another Super Admin."). The last Super Admin cannot be removed ("This is the last Super Admin. Make someone else a Super Admin first.").
- A client login is never shown in the chart, and can never be a Super Admin.
- Taking someone out of a team does **not** take them off the projects they are on. Remove them on each project's **Team** card ([section 7.6](#76-team-card)).

**To put a person on projects:**

1. Click the person, then **Assign to project…**. The box **Assign to project** opens.
2. In **Search projects**, find the projects and tick each one. The list holds the projects you may add people to. Projects the person is already on show "On team".
3. Click **Add to N projects**. You see "<name> was added to N projects." If one project fails, the message names it and gives the reason.

**To reset a password:**

1. Click the person, then **Reset password…**.
2. Choose **Email them a reset link** ("They choose their own new password. The link expires after a few days.") and click **Send reset link**. You see "A reset link is on its way to <email>."
3. Or, as a Super Admin, choose **Set a password now** ("They are signed out everywhere and must use the new password."), type at least 8 characters and click **Set password**. You see "The password was changed and they were signed out everywhere."

More about resetting passwords is in [section 3.8](#38-resetting-someone-elses-password-administrators).

### 19.4 Managing a team (the pencil)

The pencil **Manage team** is shown on a team you may edit: every team for a Super Admin, the teams they administer for a Department Admin. It opens a box with the team's name, office and head count, and two controls:

- **Edit team** (the small pencil in the box): rename the team or change its office, then **Save Changes**.
- **Add member**: type in "Search users or user groups". Click a **User Group** to add everyone in it, or a **User** to add one person. The list and the rules are the same as on the Teams page ([section 18](#18-teams)).

To change someone's role, or to remove them, click the person in the chart (section 19.3).

### 19.5 What each role sees

| | Super Admin | Department Admin | Team Lead |
|---|---|---|---|
| Teams shown | Every team | Every team | Every team |
| **Super Admins** block | Yes | Yes | Yes |
| **Not in a team yet** block | Yes | Yes | No |
| Pencil **Manage team** | Every team | Their own teams | No |
| Change a role, remove people | Every team | Their own teams (not Department Admins or Super Admins) | No |
| **Assign to project…** | Yes | Yes | Yes |
| **Reset password…** | Anyone but themselves | Their Team Leads and Team Members | No |
| **Make Super Admin** | Yes | No | No |

**In ERPNext:** a role change is saved on the **Department** (the **Portal Team Lead** field or the **Portal Department Admins** table), and the person's **Team Lead** or **Department Admin** role follows. Adding someone to a team is an **Assign To** on the Department. **Make Super Admin** adds the **System Manager** role to the **User**. **Assign to project…** adds the person to the project's **Users** table, the same as the Team card does.

---

## 20. Admin page

**Who:** Super Admins, and anyone who can create Users in ERPNext. The page has up to four cards, and what you see depends on your role:

- **Create portal user**: Super Admins, and anyone else who holds ERPNext's permission to create Users.
- **Reset a password**: Super Admins and Department Admins ([section 20.5](#205-reset-a-password)).
- **Demo dataset**: Super Admins, and only when the setting **Allow portal demo seed** is ticked ([section 20.2](#202-demo-dataset)).
- **Project folder structure**: shown to everyone who can open the page, but it only works for Auditors and Super Admins ([section 20.3](#203-project-folder-structure)).

Anyone else is sent back to their start page (Dashboard for admins, Projects for everyone else). **Admin** is in the side menu of Super Admins, Department Admins and Auditors. For an Auditor the page shows only the **Project folder structure** card.

**Where:** side menu → **Admin**. The page is called **Portal administration**.

### 20.1 Create portal user

**Who:** Super Admins, and anyone with ERPNext's permission to create Users. A Department Admin who has that permission can create Team Leads (for their own teams), Team Members and Client Customers. Only a Super Admin can create a Super Admin or a Department Admin.

1. Fill in **Email (username)** and **Full name**.
2. Choose one **Role**. A line under the choices explains the one you picked:
   - **Super Admin** (offered only to Super Admins): sees and changes everything in the portal and in the whole ERP (HR, Accounts, Stock and the rest), not just the portal. A warning says so. In ERPNext it is the System Manager role.
   - **Department Admin** (offered only to Super Admins): looks after one or more teams. Tick them under **Departments they look after**. At least one is needed.
   - **Team Lead**: leads one team. Pick it in **Team they lead** (required).
   - **Team Member** (the default): ordinary staff. **Team (optional)** puts them in a team at once. "— No team yet —" leaves them in none.
   - **Client Customer**: a client login. Pick the **Customer** (search "Search customers by name…", then **Change** to pick again). The customer must already exist. If it does not, the screen says "No customer matches. Create it first from a project's Customer card." A client login cannot be in a team.
3. Choose how they get a password:
   - Tick **Send welcome email with a link to set their own password**. **Password (optional)** can stay empty. (Choosing Client Customer ticks this box for you and locks it: a client login always gets the welcome email.) **Or**
   - Untick it and type a password (**Password (min 6)**). The site's password policy may ask for more.
4. Click **Create user**.

Messages:

- "Created <email>. A welcome email with a set-password link is on its way."
- "Created <email>. No email was sent; share the password with them yourself."
- "… but the welcome email could not be sent — check the outgoing email account."

> **Tip.** Prefer the welcome email. If you must set a password, tell it to the person by phone or another separate channel, never in the same message as their email address. Ask them to change it on **Profile** at once.

Rules: the email must be new ("User already exists" otherwise). To give an existing login another customer, use the project page (section 23). A new Team Member sees no projects until somebody puts them on one (section 2.2).

**In ERPNext:** a **User** is created. Staff become System Users with the **Projects User** role (a Super Admin also gets **System Manager**). A Client Customer becomes a Website User with the **Client Customer** role, and a **Portal User Customer** record for the chosen customer. For a Team Lead or a Department Admin, the person is put on the team, and the Department's **Portal Team Lead** field or **Portal Department Admins** table is filled in. The **Team Lead** and **Department Admin** roles then follow.

### 20.2 Demo dataset

**Who:** Super Admins, and only when **Allow portal demo seed (System Manager only)** is ticked in Portal Project Settings (or the site is in developer mode). That is the label as it appears in the Desk.

> **Warning.** Never run a demo seed on the live ATA site. It creates five real, working logins (one Department Admin, three Team Members and one Client Customer that is not linked to any customer), projects, tasks and a sample file. (The **Customers** option currently creates nothing.) Saving a new **Portal Demo Seed Run** record in the Desk runs the seed at once, even when **Allow portal demo seed** is off. Never create these records on the live site.

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

**Who:** the card is shown to everyone who can open the Admin page, but it only works for Auditors and Super Admins. Others get "You are not allowed to change the portal folder template."

- **Upload ZIP…**: import the company template from a ZIP whose folders are your standard.
- **Upload Folder…**: pick the real folder on your computer. No zipping needed.
- **Apply to project** (optional): type a Project ID in the box before you import, and the portal also builds the new folders on that project. This works only on a project that has no folders yet.

> **Warning.** Both imports **replace** the current template immediately.

### 20.4 Staff joining, changing role or leaving

**Who:** Super Admins. Department Admins can do the steps for their own teams. Team Leads can put people on projects.

**A new staff member joins:**

1. On the Admin page, use **Create portal user** with the role **Team Member** (or **Team Lead**) and the welcome email ([section 20.1](#201-create-portal-user)). Pick their **Team** there, or add them to a team later on the **Teams** page ([section 18](#18-teams)) or in the Org Chart.
2. Put them on the projects they will work on: the project's **Team** card ([section 7.6](#76-team-card)), or **Assign to project…** in the Org Chart ([section 19.3](#193-what-each-button-does)). Until you do, a Team Member sees no projects.

**A staff member changes role** (for example becomes a Team Lead or a Department Admin): use the Org Chart. Click the person, pick the role in **Role in <team>** and click **Save** ([section 19.3](#193-what-each-button-does)). Only a Super Admin can make someone a Department Admin or a Super Admin. The Admin page cannot change an existing login. The person then reloads the portal.

**A staff member leaves:**

1. **Find their projects.** In the Org Chart, click the person: the panel says how many projects they are on. In the Desk, open the **Project** list and filter on **Users → User** = their login.
2. **Take them off each project's Team card.** Click **Remove** (Super Admins and Department Admins). This also works after the login has been disabled.
3. **Hand over their projects.** Where they are the Lead Architect, a Super Admin or a Department Admin picks a new one ([section 6.5](#65-editing-a-project) and [section 6.6](#66-assigning-the-lead-architect)).
4. **Take them out of their teams.** In the Org Chart click **Remove from team**, or use the **Teams** page. If they led the team, it has no lead afterwards: pick a new Team Lead in **Role in <team>**. Taking someone out of a team does not take them off projects.
5. **Check their shares.** On the **Shares** page, click **By user** and revoke what was shared with them ([section 16.7](#167-shares-manage-all-shares)). Revoke any guest links that are no longer needed.
6. **Disable the login.** Desk → **User** → untick **Enabled**. Do not delete it.

### 20.5 Reset a password

**Who:** Super Admins and Department Admins. [Section 3.8](#38-resetting-someone-elses-password-administrators) says who may reset whom.

1. In the card **Reset a password**, click the search box and type part of a name or email. Click the person. The list shows only the people whose password you may reset, each with their role.
2. Choose **Email a reset link** ("They choose their own new password.") or, as a Super Admin, **Set a password now** ("They are signed out everywhere and must use the new password.").
3. Click **Send reset link**. For **Set a password now**, type the new password first (at least 8 characters) and click **Set password**.

You see "A reset link is on its way to <email>." or "The password for <email> was changed and they were signed out everywhere." Click **Change** to pick another person.

You can do the same from a person in the Org Chart. Your own password is changed on **Profile**.

---

## 21. ATA AI Chat

**Who:** staff. Client contacts cannot open it.

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

File answers leave out contract files, except for Super Admins and Department Admins.

---

# Part E — Clients

## 22. For clients: how to use the portal

*This section is written for you, the client.*

ATA gives you a login so you can see your own projects, get the documents ATA sends you, and send files to ATA.

### 22.1 What you can see and do

| You can | You cannot |
|---|---|
| See the projects of your company (or companies) | See any other client's projects |
| Open each project's page: status, stage, client, dates and progress | See project values or costs |
| Open and download the files in the **06-CLIENT SUBMITTAL** folder: **Incoming** (what ATA sends you) and **Outgoing** (what you send ATA) | See ATA's internal folders (unless ATA shares a folder with you by name) |
| Download several files as one ZIP | Delete files, rename folders or share files |
| Upload files into **Outgoing**, inside 06-CLIENT SUBMITTAL | Create projects or change project details |
| See files ATA shared with you personally (side menu → **Shared**) | Use ATA's internal office system |
| See the 06-CLIENT SUBMITTAL files of all your projects in one list (side menu → **File Browser**) | See ATA's internal tasks, team lists, calendars or planning boards |
| Open the project's server links (T / A / erp) on the Projects list, if ATA has given you access to those drives | — |

Your side menu has **Projects**, **Files**, **File Browser**, **Shared** and **Profile**. If you open the address of one of ATA's internal pages (for example Tasks or Calendar), the portal takes you back to **Projects**.

### 22.2 Signing in for the first time

**Already have a portal login** (for example for another of your companies)? You get the email "You now have access to <Customer> projects" instead. Sign in with your existing password and skip the steps below.

1. ATA sends you an email. Its subject is "Welcome to …" or "Complete Registration".
2. In the email, click the **Complete Registration** button.
3. Choose your password.
4. The portal opens.

The link in the email expires after about 72 hours. If it has expired, go to the portal sign-in page, click **Forgot Password?** under the **Password** box, type your email and click **Send reset link**. You get a new email. The portal always shows the same message, whether or not it knows the address. After you choose a password, the portal opens (see [section 3.3](#33-forgot-password)).

Next time, open the portal address ATA gave you (it ends in `/portal-app`). Type your email and password and click **Sign In**. You land on **Projects**.

### 22.3 Finding your project and its files

1. Click **Projects** in the side menu. You see only your company's projects.
2. Click a project to open its page.
3. Click **Files** at the top of the page (or **Open in Files hub** on the Files card). Both open the **Project files** page. You can also click **Files** in the side menu.
4. On the **Project files** page you see the **06-CLIENT SUBMITTAL** folder with its two folders. **Incoming** is marked **From ATA**: it holds what ATA sends you. **Outgoing** is marked **Your uploads**: it holds what you send ATA.
5. Click a folder to show its files. In the file list, ATA's files carry the pill **From ATA** and yours carry **Your upload**.
6. Click **Open** to open a file.

To switch to another project, use **Active project** at the top of the Project files page.

**To download several files at once:** on the Project files page, tick them, then click **Download as ZIP**.

**File Browser** (side menu) shows the 06-CLIENT SUBMITTAL files of all your projects in one place. Click a project on the left, then click a file name to open it.

### 22.4 Sending files to ATA

1. Open the project's **Project files** page (section 22.3).
2. In the card **Send files to ATA**, click **Choose files**.
3. Pick one or more files.
4. Wait for "Uploaded N files to Outgoing. The ATA team sees them marked as from you."

Good to know:

- Your files always go into **06-CLIENT SUBMITTAL / Outgoing**, whichever folder you are looking at. It is the only place you can upload.
- Your files are always private.
- ATA sees them with the pill **From client**.
- You cannot delete a file after uploading it. If you uploaded the wrong file, tell your ATA contact.
- Some file types are refused, for example `.html`, `.svg`, `.js` and `.exe`. If you need to send a drawing export such as `.svg` or `.xml`, put it in a `.zip` first. Do not send programs.
- Very large files may be refused. The usual limit is about 10 MB per file.

### 22.5 Files shared with you

ATA may share a folder or file with you by name. It then appears on the **Shared** page (side menu → **Shared**). Click **Open** next to a file. Shares can have an end date ("Expires <date>").

If a shared file will not open, ask your ATA contact to share it again.

Files you uploaded yourself are not always listed here. To check them, open the project's **Project files** page (section 22.3).

ATA may also send you a **guest link** (a link that needs no login). It opens a page called **Shared folder** with a **Download** button on each file. If it says "Cannot open this share", the link has expired or was withdrawn. Ask ATA for a new one.

### 22.6 More than one company

One login can belong to several client companies. You then see the projects of all of them. Your **Profile** page shows the list under **Linked customers (portal)**.

### 22.7 Your account

- **Profile** (side menu): change your name, mobile, language and time zone; change your password (section 3.6).
- **Logout**: click your picture at the top right, then **Logout**, then **Logout** again.
- Ignore **Switch to Desk** in the menu at the top right. It is not for client logins.

---

## 23. For ATA staff: giving a client access, end to end

### 23.1 The whole flow

1. **Set the customer** on the project (Customer card).
2. **Give a person a login** for that customer: invite a new login, or add an existing one.
3. The person gets an **email** and sets a password.
4. They sign in and see **all projects of that customer**, but only the **06-CLIENT SUBMITTAL** folder (unless ATA has shared something with them).
5. Later you can **reset their password** or **remove** their access.

**In ERPNext:** a client login is a **Website User** with the role **Client Customer**. What they can see is decided **only** by **Portal User Customer** records (one record = "this login may see this customer's projects"). One login can have several. The **Portal linked Customer** field on the User is read-only and for display only. It shows one of the login's customers. It does not give or take away access. ERPNext also creates a **Contact** for each new login, but it is not linked to the Customer, so client logins do not appear in the Customer's Contacts in the Desk. To see who has access, use the **Client Customer logins** card or the **Portal User Customer** list.

### 23.2 Step 1: set the customer

1. Open the project page.
2. In the **Customer** card, click **Search customers** and pick the customer, or use **Create customer (no duplicate name)**.

Every client contact of that customer can now see this project.

### 23.3 Step 2a: invite a new person

**Who:** Super Admins, and Department Admins who hold ERPNext's permission to create Users.

1. On the project page, click **Invite customer user** (Customer card) or **Invite new user** (Client Customer logins card).
2. In **Invite a Client Customer**, fill in **Email (username)** and **Full name**.
3. Keep **Send a welcome email** ticked. Leave the password box ("Password (optional — leave blank to let them choose)") empty.
4. Click **Create & send invite**.

You see "Created <email> and linked them to this customer. An invite email is on its way."

Other cases:

- If you untick **Send a welcome email**, you must type a password (at least 8 characters). The button becomes **Create & link**. You then pass the password on yourself. Prefer the email. If you must set a password, tell it to the person by phone or another separate channel, never in the same message as their email address. Ask them to change it on **Profile** at once.
- If the email already has a login, that login is linked instead. It keeps its current password: "Linked the existing user <email> to this customer — they keep their current password."
- If the email belongs to a **disabled** login, you get "… is a disabled login. Re-enable it in Desk before inviting them." A Super Admin must enable it first.
- If the existing login has never set a password, keep **Send a welcome email** ticked. Otherwise you get "… already exists but has no password yet. Tick Send a welcome email."
- If you link an existing login with **Send a welcome email** unticked, no email is sent. Tell the person yourself.
- Super Admins, Department Admins and anyone on a project team are refused, as in 23.4. Other staff logins are **not** refused; see the warning in 23.4.
- If the warning "The invite email could not be sent — check the outgoing email account." appears, the login was created but no email was queued. Tell a Super Admin. Once an outgoing Email Account exists, a Super Admin uses **Reset password → Email them a reset link** ([section 23.10](#2310-resetting-a-clients-password)). Do not remove and re-add the person: re-adding only sends a notice telling them to use the earlier email, which never arrived.

### 23.4 Step 2b: add an existing login

Use this when the person already has a client login, for example for another customer.

**Who:** Super Admins and Department Admins. Others see "Only a Super Admin or a Department Admin can add Client Customer logins."

1. In **Client Customer logins**, go to **Add existing user**.
2. Click the box to see client logins, or type part of a name or email.
3. Click the person. They are added at once ("Added").

You see "Added <email>. An access email is on its way."

Super Admins, Department Admins and anyone on a project team cannot be linked. You get "This is an internal user and cannot be linked as a customer portal contact".

> **Warning.** Other staff logins are **not** blocked. If you type a colleague's email in **Invite customer user**, their login is linked and gets the **Client Customer** role. From then on it sees only that customer's projects. Check the email before you invite. (**Add existing user** lists only client logins, so staff do not appear there.)

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
- On each project page: status, stage, client, dates, progress, the **Customer** card (view only) and the **Files** card. They do not see the tasks, the **Team** card or the **Portal Team** card.
- Files: only **06-CLIENT SUBMITTAL** and its two folders, **Incoming** (what you send them, marked **From ATA**) and **Outgoing** (what they send you, marked **Your uploads**), plus anything you shared with them by name. Their side menu has **Files**, **File Browser** and **Shared**.
- They can upload into **Outgoing**, and only there. They cannot delete, share or change anything.
- Tasks, Kanban, Gantt, Calendar, Daily Task and AI Chat are not in their menu. If they open one by its address, the portal takes them back to **Projects**. Global search gives them no task results.
- On the Projects list they see the **Servers** badges (T, A, erp): only enter links the client may see.

Check the **People with access** list. It shows "Last signed in <when>" once they have signed in, or "Invited — hasn't signed in yet".

### 23.7 If the client cannot see the folder

The client folder is found by its name, **06-CLIENT SUBMITTAL**, directly inside the project folder. Older projects that spell it "06 - CLIENT SUBMITTAL" (with spaces) are found too, so you do not have to rename them. A project that has no client folder yet gets one, with **Incoming** and **Outgoing**, the first time you use **Submit** in the File Browser or the client uploads a file.

If a client still sees nothing:

1. Check the project's **Customer** and the client's login ([sections 23.2 to 23.4](#232-step-1-set-the-customer)).
2. In the Files hub, open the project as staff. The client folder, with Incoming and Outgoing, should be there. If the project has no folders at all, build them first ([section 28](#28-faq-and-troubleshooting), "A project made in the Desk has no folders").
3. A folder with any other name (for example a typing mistake) is not recognised as the client folder. Tell a Super Admin.

### 23.8 Giving files to the client

Choose one:

- **Upload into 06-CLIENT SUBMITTAL / Incoming** from the Files hub or the project page. (Your upload goes into a dated sub-folder inside Incoming. The client sees it marked **From ATA**.) Do not upload into **Outgoing**: it is for the client's own uploads.
- **File Browser → Submit**: copies an existing file into Incoming as `NN_<date>_<name>` (section 15.5). This needs the right to change the project.
- **Share a folder or file by name** with the client contact (section 16.1; read the warning there first). They find it on their Shared page.
- **Guest link** for someone without a login (section 16.4). Use a short expiry. Never link the whole project.

### 23.9 Spotting client uploads

- **In the portal:** a file in **Outgoing** carries the pill **From client**, in the Files hub, the project page and the File Browser. (A file you put in Incoming carries **Sent to client**.) In the Files hub and the File Browser, point at the pill to see "Uploaded by the client: <name>". On the Shared page, and for a client's upload that sits outside Outgoing, an orange **Client upload** badge shows instead.
- **In the Desk:** open the **File** list. In the left sidebar, open **Tags** and click **Client Upload**.

Client uploads are always private. They go straight into Outgoing, with no dated folder, and they are not renamed.

The pill comes from the folder a file sits in. The name in the pill's tooltip, and the orange badge, are worked out each time from who uploaded the file. If that login later loses the **Client Customer** role (for example when its last customer is removed, [section 23.11](#2311-removing-access)), its earlier uploads in Outgoing keep the **From client** pill, but lose the name and the badge. The Desk tag **Client Upload** stays, so use the Desk tag to find everything a client ever sent.

### 23.10 Resetting a client's password

**Who:** Super Admins only. A Department Admin cannot reset a client's password. The person must be a client contact of this project's customer.

1. In **Client Customer logins**, click **Reset password** next to the person.
2. Choose one:
   - **Email them a reset link** (recommended). They choose a new password. Click **Send reset link**. You see "A password reset link is on its way to <email>."
   - **Set a new password now**. Type a **New password (min 8)** and click **Set password**. They are signed out everywhere. No email is sent; you must pass the password on to them safely. You see "New password set for <email>. Their other sessions were signed out."

> **Tip.** Prefer the email link. If you must set a password, tell it to the person by phone or another separate channel, never in the same message as their email address. Ask them to change it on **Profile** at once.

Each new reset link makes any earlier link stop working. If no email account is set up, you get "No outgoing email account is configured…". A Super Admin can also reset a client's password from the **Reset a password** card on the Admin page ([section 20.5](#205-reset-a-password)).

### 23.11 Removing access

**Who:** anyone who can change the project, Team Members included.

1. In **Client Customer logins**, click **Remove from portal** next to the person.

> **Warning.** There is no confirmation. The access is removed as soon as you click. To undo it, add the person again with **Add existing user** (section 23.4). Their old shares do not come back.

This removes **this customer** from their login, so they lose **every project of this customer**, not just this one. Their other customers stay.

Behind the scenes:

- Their shares on this customer's projects are withdrawn.
- A note is added to their User record in the Desk.
- If this was their last customer, the **Client Customer** role is removed. The login stays enabled, but the next time they sign in, the portal signs them out again and shows "Server error. Please try again." (A session that is already open keeps working but shows no projects.) To give access back, add them with **Add existing user** ([section 23.4](#234-step-2b-add-an-existing-login)).

Other ways access ends:

- Removing the **Client Customer** role from the User in the Desk removes **all** their customers and shares. Giving the role back does **not** bring them back.
- Changing or clearing the project's Customer hides that project from the old customer's contacts. Folder and file shares you made for the old customer's contacts are **not** withdrawn automatically. Revoke them on the **Shares** page.
- To stop a person signing in at all (for example when they leave their company), a Super Admin opens their **User** in the Desk and unticks **Enabled**. Their customer links stay, and ticking **Enabled** again restores the same access.
- Do not delete a client's **User** in the Desk. Untick **Enabled** instead. Deleting it removes all its customer links and shares, and cannot be undone. A Customer that is still linked to projects cannot be deleted.

### 23.12 Other places to manage client logins

- **Admin page → Create portal user** with **Client Customer** (Super Admins; section 20.1).
- **Desk → Portal User Customer** list (Super Admins): one row per login and customer. Deleting a row removes that access and its shares. Adding a row in the Desk is not recommended. It gives access only if the User also has the **Client Customer** role, no email is sent, and the portal's checks (not staff, not on a project team) are skipped. A row for a User without the role grants nothing, and it is deleted the next time the User is saved. Use the project page (sections 23.3 and 23.4) instead.

---

# Part F — Reference

## 24. Where things live in ERPNext Desk (for administrators)

| In the portal | In the Desk |
|---|---|
| A project | **Project** record. The portal adds fields such as Portal Project Code, Portal Project Manager, Portal Kanban Stage, Portal Office, Portal Phase, Portal Team, the server links and Portal Milestones. |
| Project team | The Project's **Users** table, kept in step with **Assign To** on the Project. The portal never adds client logins to it, not even from a Desk Assign To. |
| Files | **File** records under `Home / Attachments / <project>`. Contracts under `Home / Contracts / <project>`. |
| Client uploads | Files with the tag **Client Upload**. |
| Shares and guest links | **Portal Folder Share** list (audit: who, what, expiry, revoked, opens), plus ERPNext **DocShare** entries. Always revoke from the portal. Never tick **Revoked** or delete rows here by hand: a share with a person then keeps working with no end date, because its DocShares are never removed. |
| Roles | Super Admin is the ERPNext role **System Manager**. Team Member is **Projects User**. Client Customer is the role **Client Customer**. Department Admin and Team Lead are marker roles of the same names. The Department's data decides which teams they apply to (see Teams below). |
| Client logins and their customers | **User** (Website User, role Client Customer) and **Portal User Customer** (Super Admin only). |
| Teams | **Department** records under "All Departments", with **Portal Office**, **Portal Team Lead** (the Team Lead) and the **Portal Department Admins** table (the Department Admins). Members are ToDo assignments on the Department. Whoever is named there gets the matching **Team Lead** or **Department Admin** role, whether you change the Department in the portal or in the Desk. |
| Daily Task reminders | Private **Event** records. |
| Tasks and comments | **Task** records and their comments. |
| File types | **Portal File Type** list. |
| Routing rules | **Portal Folder Route Rule** list. |
| Demo runs | **Portal Demo Seed Run** (never on the live site). Creating one in the Desk runs it immediately. |

**Portal Project Settings** (Super Admin only) holds the portal's settings:

| Section | Setting |
|---|---|
| Branding | **Company Logo**, **Company Name**, **Company Tagline** (sign-in screen and side menu). |
| Portal access | **Allow any portal user to create projects** (ticked by default; untick to let only Super Admins and Department Admins create projects). **Allow portal demo seed (System Manager only)** (keep unticked on the live site). |
| Project file subfolders (template) | **Subfolder template**: the company folder tree. |
| Central storage (Frappe Drive) | **Use Frappe Drive on this server**, **Drive / site base URL**, **Frappe Drive upload webhook URL**, **Internal file policy note** (shown on the Files hub as "File policy:"). |
| Cloud integrations | Google Drive and BIM 360 / ACC switches, notes and upload webhook URLs. Although labelled "(planned)", they work once switched on with an address. |
| Client portal | **Welcome text for client document access** (shown on the Files hub as "Client portal guidance"). |

> **Warning.** The three upload webhook URLs stay on the server; the portal never sends them to a browser. Every other setting here (branding, the Drive base URL, the notes and the welcome text) can be read by every signed-in user, clients included. Never put passwords or secret keys in those.

Other Desk settings the portal depends on:

- **System Settings → Reset Password Link Expiry Duration**: how long welcome and reset links last (72 hours on the ATA site).
- **System Settings → Enable Password Policy** and **Minimum Password Score**: stronger passwords.
- **Selling Settings → Default Customer Group and Territory**: used for customers created in the portal. If they are empty, the portal uses the first Customer Group and Territory.
- An **outgoing Email Account**, and the background **scheduler**, for all emails and for the hourly share expiry.

The Desk sidebar has a **Project Portal** workspace. Its shortcuts are **Open Portal**, **Project**, **Task**, **Portal Project Settings**, **User Guide** (opens `/handbook`) and **Technical Guide** (opens `/tech-guide`, Super Admins only). Its link cards list the portal's DocTypes, including **Portal User Customer**.

> **Warning.** Each update (`bench migrate`) re-creates the portal's own fields and its **Project Portal** workspace. Desk changes to them are lost: for example new **Portal Kanban Stage** or **Portal Phase** options added in Customize Form, renamed labels, or edits to the workspace. Ask the developer to change these in the app instead.

---

## 25. Emails the portal sends

All portal emails are queued and sent a few minutes later. That includes the **Forgot Password?** email from the sign-in page. All emails need an outgoing Email Account in the Desk.

| Email | When | To |
|---|---|---|
| Welcome ("Welcome to …" or "Complete Registration", with a **Complete Registration** button) | A new client is invited; or a user is created on the Admin page with the welcome box ticked; or an existing login with no password (and no unexpired link) is added to a customer | The user |
| "You now have access to <Customer> projects" | An existing client login is added to a customer | The client |
| "Password Reset" | **Forgot Password?**; or an admin uses **Email them a reset link** (Org Chart, Admin page, or the project page for a client) | The user |
| "You were granted access to a folder on <project>" / "…a file on <project>" | A share with **Email the user when I add them** ticked | The person shared with |
| "Project Collaboration Invitation" (from ERPNext) | Someone is added to a project team (Team card, **Add from org chart**, **Assign to project…**, or a Desk **Assign To**) | The person added |
| "<name> assigned a new task Project <title> to you" (or "…Task <subject>…") and "Your assignment on … has been removed by <name>" (from ERPNext) | Someone is added to or removed from a project team (Team card, Org Chart or Desk **Assign To**), or added to or removed from a team (Teams page or Org Chart); or someone is picked in **Assign to** when a task is created (section 11.4) | The person (not when you add or remove yourself), unless they turned off assignment emails in their Notification Settings |
| "Upcoming Events for Today" (from ERPNext) | Daily, for Daily Task reminders | The reminder's owner |

To change the wording of the welcome and password-reset emails, a Super Admin creates an **Email Template** in the Desk and chooses it in **System Settings → Welcome Email Template** or **Reset Password Template**. The "You now have access…" and share emails have fixed wording.

---

## 26. House rules

1. **One login per person, never shared.** Every upload, share and deletion is recorded against the account that did it.
2. **Leave uploads private.** Public means anyone on the internet with the address. Share with a named person, or use a guest link, instead.
3. **Choose the right folder before uploading.** Check "Goes into <folder>".
4. **Short expiries on guest links, and revoke them when done.** Use the Share box or the **Shares** page.
5. **Do not change the standard folders.** Their sameness across every project is what makes them useful. The portal does not allow renaming **06-CLIENT SUBMITTAL**, **Incoming** or **Outgoing**.
6. **Never send a guest link to 01-CLIENT DATA or to the whole project.**
7. **Always give a team an office.** Otherwise it disappears from the lists.
8. **Never run a demo seed on the live site.**
9. **Name files as if the client will read the name.** Keep file names professional and neutral.
10. **Share a folder with a client contact only if they may see everything in it.** Otherwise use **File Browser → Submit** ([section 16.1](#161-sharing-a-folder-with-a-person)).
11. **Give files to a client through Incoming, never Outgoing.** Use **File Browser → Submit**, or upload into **06-CLIENT SUBMITTAL / Incoming**. Outgoing is for the client's own uploads.

---

## 27. Known issues and workarounds

These are known as of 13 October 2026. They may be fixed later.

| Where | Problem | Workaround |
|---|---|---|
| Sign-in | A login without a portal role sees "Server error. Please try again." | Give the user a portal role. |
| Edit Project form | Progress is replaced by ERPNext. In Progress / On Hold are reset by task changes and other project changes; on Manual projects the non-task changes fail. | Use the Kanban stage for working stages. On a Manual project, set the status back to Open first. |
| Tasks table | The **Assigned** column shows login emails, not names. | — |
| Kanban | Empty stages have no column. | Set the stage in the Desk. |
| Gantt | Picking an office moves other offices' projects into "Unassigned to a team". | Use the **All Teams** filter too, or ignore that group. |
| Daily Task | Reminders added with an older version may show one day early. | Delete and add them again if the day matters. |
| Dashboard | **Projects Delayed** counts finished projects; period drop-downs do nothing; Team Performance is empty. | Read the cards as described in section 5. |
| Folder rename | Shares and guest links on the old name may stop working. | Share again after renaming. |
| Shares page | **Created by me** shows everyone's shares; **Revoke** fails on "ERPNext share" rows; the opens counter stops at 1. | Remove Desk shares in the Desk. |
| Top bar | **Switch to Desk** shows a "not permitted" page for clients. | Ignore. |
| Admin page | If no team exists yet, the **Department Admin** choice says to create a team "in the Org Chart". Teams are created on the Teams page, by a Super Admin. | Create the team on the **Teams** page first. |
| Project page (clients) | In the Files card, a client sees the staff wording **Sent to client** and **From client**, not **From ATA** and **Your upload**. | The **Project files** page and the File Browser use the client wording. |

---

## 28. FAQ and troubleshooting

**I still see the old screens after an update.**
Reload the page. If that does not help, do a hard refresh: **Ctrl + Shift + R** (Windows) or **Cmd + Shift + R** (Mac). If it is still old, close every portal tab and open the portal again, or try a private window.

**I cannot see a project I know exists.**
- A **Team Member** sees only the projects they are on. If the project is not in your list, ask a Super Admin, a Department Admin, a Team Lead or the project's Lead Architect to add you to its **Team** card ([section 7.6](#76-team-card)).
- A **Team Lead** or a **Department Admin** sees the projects of their teams ([section 2.2](#22-who-sees-which-projects)). A project filed under another team, with nobody from your team on it, is not in your list. Only Department Admins see the projects that belong to no team.
- If you see no project at all, your login may have no portal role. Ask a Super Admin to give you one (ordinary staff are Team Members).
- Client contacts: the project needs its **Customer** set to your company, and your login must be linked to that customer. Ask your ATA contact.
- You opened the portal from the Desk (the `/apps` tile) and the Projects list is empty: your login has no portal role. The portal does not sign you out in this case. Ask a Super Admin to give you a role.
- You use the **Active project** picker on the Files hub, or the project lists on the File Browser or Contracts: these list only the 500 most recently changed projects. Find the project with the search on the Projects page instead.

**Sign-in says "Sign-in did not keep a session (cookies blocked or wrong site URL). Check browser settings."**
Check that your browser allows cookies for the site, and that you are using the portal address ATA gave you. If cookies are fine, your account may need an extra step that the portal's sign-in screen cannot show: a two-factor code, or a forced password change because your password has expired. Sign in once at `https://<your-ERP-address>/login` (ERPNext's own sign-in page), complete the step it asks for, then open `/portal-app`.

**What do the sign-in error messages mean?**
- **Invalid login credentials**: the email or password is wrong. Use **Forgot Password?**.
- **User disabled or missing**: your login is disabled. Ask a Super Admin.
- **Your account has been locked and will resume after N seconds**: too many wrong passwords in a row (by default 10). Wait that long and try once more, or use **Forgot Password?**.
- **Server error. Please try again.**: your login has no portal role (section 3.1).
- **Sign-in did not keep a session…**: see the entry above.

**A button I expected is missing.**
Buttons appear only when your role allows the action ([section 2.3](#23-who-can-do-each-task)). For example: **Remove** on a project's Team card is for Super Admins and Department Admins; **Create team** is for Super Admins; **Dashboard** and **Routing rules** are for admins; **New Project** shows only if you may create projects. Client contacts can open their projects but never change them. After a change of role, sign out and sign in again.

**I am new and my Projects list is empty.**
A new Team Member sees no projects until somebody adds them to a project's **Team** card ([section 2.2](#22-who-sees-which-projects)). Ask your Team Lead, or an admin.

**I took someone out of a team, but they still see projects.**
Taking a person out of a team does not take them off projects. Remove them on each project's **Team** card ([section 7.6](#76-team-card)).

**"Client contacts cannot be added to the project team: <login>"**
A client login is in a User Group you added, or was already on the team from before this rule. (The **Add user** search never offers client logins.) Client contacts get their access through the **Client Customer logins** card instead (section 23). A Super Admin or a Department Admin must click **Remove** next to that person on the **Team** card.

**"Assign the task to an active ATA staff login."** (New task)
The person in **Assign to** is disabled or is not an ATA staff login. Pick someone else, or leave the box empty (section 11.4). If the person is an active staff member, the email of their login may have been changed after the login was created; ask a Super Admin.

**Why can I see the project but not its value?**
See section 2.5. Only Super Admins see all values. A Department Admin sees only projects where they are the Lead Architect. Team Leads and Team Members see no values.

**The welcome or reset link has expired.**
Links last 72 hours on the ATA site. Use **Forgot Password?**, or ask an admin to send you a new link ([section 3.8](#38-resetting-someone-elses-password-administrators)).

**The email did not arrive.**
- Check your spam or junk folder.
- Emails are queued and can take a few minutes.
- **Forgot Password?** shows the same message for every address, so it cannot tell you the address was wrong. Check how you spelled it and try again. The form accepts five requests an hour. Or ask an admin to send you a reset link ([section 3.8](#38-resetting-someone-elses-password-administrators)).
- If the screen said the email "could not be sent", no outgoing email account is set up. Tell a Super Admin.
- A Super Admin can check the **Email Queue** list in the Desk.
- If the **Email Queue** shows the email as **Not Sent** for more than a few minutes, the background scheduler may be off. The developer or server administrator must switch it on. The hourly share expiry also depends on it.

**The client cannot see the 06-CLIENT SUBMITTAL folder.**
The portal finds the folder by its name, `06-CLIENT SUBMITTAL` ("06 - CLIENT SUBMITTAL" with spaces is found too). See section 23.7.

**A client says a link to Tasks, Calendar or another page takes them to Projects.**
Those pages are ATA's internal working tools, and client logins cannot open them. Clients find their files under **Files**, **File Browser** and **Shared** in the side menu (section 22).

**My upload was refused.**
- The file type may be blocked (Appendix C).
- The file may be too big.
- Clients can only upload into 06-CLIENT SUBMITTAL / Outgoing ("You can upload only into the 06-CLIENT SUBMITTAL/Outgoing folder.").
- For staff, **Upload files** and **Upload ZIP** are grey only when the project has no folders yet (see "A project made in the Desk has no folders" below). Otherwise the first folder is pre-selected, so always check **Goes into <folder>**.

**A project made in the Desk has no folders.**
The standard folders are built on the first portal upload. In the Files hub, click the **Project folder (all files)** card, then **Use this folder for upload**, and upload one file. The standard folders (Incoming and Outgoing included) are then created. Reload the page.
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
No Customer Group or Territory exists on the site. A Super Admin creates at least one of each in the Desk, and ideally sets them as **Default Customer Group** and **Default Territory** in **Selling Settings**. Without those defaults, the portal uses the first group and territory.

**"Set a default Company or pass company" / "Set a default Company first."** (creating a project or a team)
A Super Admin sets the default Company in the Desk (**Global Defaults**).

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
- For Super Admins: the tester guide at `/test-guide`, and the technical guide at `/tech-guide` (both need a Super Admin login).

For Super Admins, portal entries in the **Error Log** have titles such as:

- "Portal ZIP upload: <file>": a file inside an uploaded ZIP failed.
- "Portal: zip include <file ID>": a file was left out of a ZIP download.
- "External upload failed for <project>": the copy to an external drive failed.
- "sync_project_access_from_todo failed": a Desk **Assign To** did not update a project team.
- "Portal: cron revoke <share>": the hourly share expiry failed for one share.
- "Portal: share email" / "Portal: file share email": a share email could not be queued.
- "Portal: Failed creating project folders": the standard folder tree was not built.
- "Portal: forgot-password mail": the reset link for a **Forgot Password?** request could not be created or queued. The person sees the usual message either way.

For Super Admins: after acceptance testing, disable the test logins used with the tester guide (Desk → **User** → untick **Enabled**), and ask the developer to remove them from the tester guide.

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
| Tester guide (Super Admins) | `/test-guide` |
| Technical guide (Super Admins) | `/tech-guide` |
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

This is the built-in template (69 paths). Your site may use a changed template (see File tools).

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
06-CLIENT SUBMITTAL/Incoming
06-CLIENT SUBMITTAL/Outgoing
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
| Forgot Password? form | 5 requests an hour from one internet address |
| Contracts | `.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, `.png` |

**Blocked file types** (cannot be uploaded anywhere in the portal):

`.html` `.htm` `.xhtml` `.shtml` `.xht` `.svg` `.svgz` `.xml` `.xsl` `.xslt` `.js` `.mjs` `.cjs` `.jse` `.vbs` `.hta` `.php` `.phtml` `.php3` `.php4` `.php5` `.phar` `.jsp` `.asp` `.aspx` `.cgi` `.pl` `.py` `.sh` `.bash` `.exe` `.dll` `.scr` `.com` `.bat` `.cmd` `.msi` `.jar`

Capital letters make no difference: `.PHP` is blocked too.
