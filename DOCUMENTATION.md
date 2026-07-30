# Portal App — End-user & UAT guide

This document is for **people testing or using the Project Portal** (the web app served under **`/portal-app/`** on your ERPNext site). It describes the intended workflow, what each area does, and how **files** relate to **ERPNext** and **Frappe Drive**.

Your administrator may change permissions and settings; if something here conflicts with internal policy, follow your administrator.

---

## 1. How to open the portal

1. In a browser, go to:  
   `https://<your-site-domain>/portal-app/`  
   (or your host’s equivalent; the app lives under the path **`portal-app`**.)
2. You should see the **login** page. Sign in with the same **email/username and password** as ERPNext Desk (unless your org uses a different auth flow).
3. After login, the portal checks that your user is allowed to use the project portal (see **Who can access** below). If access is denied, you will be logged out with an error—contact your administrator.

**Tip:** Bookmark **`/portal-app/login`** for testers. After **Logout**, you are sent back to the portal login page.

---

## 2. Who can access the portal

A user can use the portal if **any** of the following is true:

- They have the ERPNext role **Projects User**, **Projects Manager**, or **System Manager**, or  
- They appear on at least one ERPNext **Project** in the **Project User** child table (team list), or  
- They have the role **Portal Customer** and their **User** record has **Portal linked Customer** set to a valid **Customer** ID (Desk → User). Those users only see projects whose **Customer** field matches that link.

**Projects Manager** and **System Manager** typically see **all** projects. **Portal Customer** users see **only** projects linked to their customer. Other internal users see projects where they are listed as team members.

Administrators maintain access in **Desk** → **Project** (team / Project User rows), **User** roles, and the **Portal linked Customer** field (after `portal_app` migrate). You can also create **Portal Customer** users from the portal **Admin** page (if you have User create permission), with the Customer ID filled in.

### Linking a customer to a project (internal users)

On **Project detail**, the **Customer (ERPNext)** section lets eligible users **search** existing customers, **create** a new one (same name reuses the existing record—no duplicate), or **clear** the link. Projects must have the correct **Customer** set for **Portal Customer** users to see them.

---

## 3. Recommended workflow for testing (UAT)

Use this order so each feature has data to work with.

| Step | Action | What to verify |
|------|--------|----------------|
| 1 | Log in | Access granted; redirect to dashboard |
| 2 | **Dashboard** | Portfolio metrics, recent projects, quick actions (if shown) |
| 3 | **Projects** | List, search, filters; open a project row |
| 4 | **Project detail** | Summary cards, **Customer** link (if permitted), **Team**, **Tasks**, **Files** |
| 5 | **Files** (hub) | Pick a project, list files; upload (internal users only—**Portal Customer** is view-only) |
| 6 | **Kanban** | Projects grouped by portal Kanban stage (or status fallback) |
| 7 | **Calendar** | Project and task dates appear |
| 8 | **Profile** | Name/contact fields save; header name updates after refresh if applicable |
| 9 | **Logout** | Returns to **`/portal-app/login`** |

**Optional (role-dependent):**

- **New project** (on **Projects**): Only if your role/settings allow creation; you are added to the team automatically on create.
- **Team changes** on a project: Only **Portal Project Manager** (field on the Project in Desk) or **Projects Manager** / **System Manager**.
- **Admin** (sidebar): Only for users who can create **User** records and/or run **demo seed** (System Manager + specific settings). Not a normal end-user screen.

---

## 4. Screen reference

### Dashboard

- Overview of **projects you can access**: counts, status / Kanban breakdowns, recent list.
- **Pinned from last visits** (if shown) is stored in **this browser only** (local storage), not on the server.
- Any **file policy** text comes from **Portal Project Settings** in Desk (see below).

### Projects

- Table of projects with search and **status** filter.
- Click a row to open **Project detail**.
- **New project** opens a form (title, optional code, dates, customer link name) when your user is allowed to create projects.
- **Servers column:** three small badges — **T** (Google Drive), **A** (Autodesk), and **ERP**. T/A open their linked server URL in a new tab when set on the project's edit form; greyed out and non-clickable when empty. **ERP** opens a small popup with two links: **Client Server** (the client-side server link set on the project) and **Project Files** (jumps to the **Files** hub filtered to this project).
- **Value visibility:** the **estimated cost** shown on a project (list, Kanban, dashboard) is only visible to **System Manager** (all projects) and **Projects Manager** (only the project(s) where they are the **Portal Project Manager**) — other roles never see it.

### Organization Chart

- Collapsible hierarchy of teams and members, built from **Teams** data (each department is a top-level node; members are children).
- Click the **+ / −** button on a node to expand/collapse its reports. Click a member row to see their details (avatar, role, office, direct-report count) in the right panel.
- **Office filter** buttons (RIYADH / LISBON / MANILA / All) narrow the tree; **Headcount Summary** panel shows active employee counts per office.

### Teams

- Workload view of teams (ERPNext **Department** records tagged with an office). Filter by office; see each team's member list and active-project count.
- **Add / remove member** (individually or by picking a whole **User Group** at once) — only for users allowed to manage teams. Membership is implemented as Frappe's native **Assign To** on the Department, kept in sync with each project's team.

### Contracts

- **Management-only** area (System Manager / Projects Manager on that specific project) for uploading contract/agreement documents — kept entirely separate from the shared project **Files** area so regular team members never see it.
- Files are stored under a dedicated `Home/Contracts/<project>` folder tree, always **private**, and restricted to **`.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, `.png`**.
- Pick a project on the left, then **Upload Contract**, open, or delete files on the right.

### Gantt Chart

- Team-grouped timeline of all projects you can access, with office/team filters. Useful for a portfolio-level view of overlapping schedules.
- **Milestones:** the **+ Milestone** button (or the flag icon on a project row) lets a manager set a short text label plus the **date** it falls on — the red flag on the timeline is positioned at that real date. A milestone with no date only shows the flag at the project's bar end (legacy rows saved before the date field existed).

### Daily Task

- A personal, per-user reminder board (4 weeks) of small dated-and-timed items — title, date/time, colour, complete/incomplete. Not tied to a project.
- Staff (System Manager / Projects Manager) can assign an item to someone else; regular users can only create items for themselves.
- Stored as standard calendar **Event** records (two small hidden custom fields), not a new DocType. Replaces the earlier **Daily Gantt** screen.

### AI Chat

- Sidebar link **"ATA AI Chat"** opens a Q&A-style panel that answers questions about project counts, budgets, recent uploads, and tasks using rule-based keyword matching over the portal's own data (not a live AI/LLM call).
- **Known issue:** as of this writing the `/ai-chat` route is not registered in the app router, so this screen does not currently load — see **Common issues** below.

### Project detail

- **Summary:** Status, Kanban stage, client, timeline, cost, progress (from ERPNext **Project**).
- **Customer (ERPNext):** Search customers, create without duplicate name, link or clear (project managers / others allowed by the portal; **Portal Customer** users cannot change this).
- **Team:** Search users, add/remove, **Save team** (only if you are allowed to manage the project). **Portal Customer** users do not manage team.
- **Files:** Internal users: drag-and-drop or click to upload; optional **Private**. **Portal Customer** users: list and open only (no upload). Same storage as the **Files** hub (see **Files and Frappe Drive**).
- **Tasks:** Read-only list of **Task** documents linked to this project.

### Kanban

- Columns follow the **Portal Kanban Stage** custom field on **Project** when present; otherwise ERP **status** is used.
- Click a card to open that project’s detail page.

### Calendar

- Shows dated **Project** and **Task** entries you are allowed to see.

### Files (hub)

- Select a **project**, then list and upload files attached to that **Project** in ERPNext.
- Banners may appear if administrators enabled flags in **Portal Project Settings** (Frappe Drive, Google Drive, BIM placeholders)—read them as **guidance**, not as automatic sync (see next section).

### File Browser (all files)

- Cross-project file listing with category/classification filters and search — for finding a file when you don't remember which project it's under.

### Shared with me / Manage shares

- **Shared with me:** files/folders another user has explicitly shared with you (Drive-style), grouped by project.
- **Manage shares** (project admins): audit and **revoke** active share links/grants across every project you manage.

### Folder Rules / File Tools (admin & auditor)

- **Folder Rules:** define automatic routing of uploaded files into secondary folders based on file type ("Mirror" or "Cross-route").
- **File Tools:** edit the company-wide folder template applied to new projects (manual rows, or import from a ZIP/folder structure).

### Admin (System Manager)

- Create portal users (Projects User / Projects Manager / Portal Customer roles only).
- Run or manage **demo seed** data runs (tracked and reversible) for training/sales demos — includes an option to import a project list from an uploaded `.docx` file.

### Profile

- Update **full name**, **mobile**, **language**, **time zone** where permitted.
- **Appearance:** Use the **profile menu** (top right) → **Theme · Light / Dark / System** to change display mode; choice is saved in the browser.

### Sidebar

- **Collapse:** Use the chevron on the sidebar or **Ctrl+B** (⌘+B on Mac); preference is saved in the browser.

---

## 5. Files, ERPNext, and Frappe Drive (important)

### What the portal actually stores

When you **upload a file** in the portal (project detail or **Files** hub), the system creates a standard ERPNext **File** document **attached to the Project** (`attached_to_doctype = Project`, `attached_to_name = <project id>`). Files live on **your ERPNext site** (public or private URL depending on the **Private** option and site configuration). They are the same attachments you would see on the **Project** form in **Desk**.

- **Open** uses the file URL returned by the system (respects login / private file rules).
- **Private:** When checked, the file is stored as a private attachment in Frappe/ERPNext (typical pattern: access only when logged in with permission).

#### Upload destination modes (new)

Portal upload now supports selectable destination modes in the Files screen:

- **ERPNext File only**: create attachment on `Project` (default behavior)
- **External platform only**: send file to configured external integration endpoint, no ERPNext File row
- **Both ERPNext + External**: save ERPNext File and send same file to external endpoint

External upload is provider-based:
- Frappe Drive
- Google Drive
- BIM 360 / ACC

To enable direct external upload, configure webhook URLs in **Portal Project Settings**:
- `Frappe Drive upload webhook URL`
- `Google Drive upload webhook URL`
- `BIM 360 / ACC upload webhook URL`

Also enable the corresponding provider flags in **Portal Project Settings**.

### What “Frappe Drive” means here

**Frappe Drive** is a **separate product** (often its own site or app) for team file management, sharing, and previews. It is **not** the same table as ERPNext **File** rows on **Project**.

In **Portal Project Settings** (Desk → **Portal Project Settings**, single):

- **Use Frappe Drive on this server** — When enabled, the **Files** area shows an informational banner that Drive is part of your organisation’s story.
- **Drive / site base URL** — Optional URL (e.g. your Drive or team wiki base) shown next to that banner so users can **open Drive in another tab** for large folders or collaboration workflows.

**The portal does not automatically upload or mirror portal attachments into Frappe Drive** with the stock app: uploads stay as **File** on **Project**. If your organisation wants a single source of truth in Drive, you either:

- use **Desk / Drive** for those assets and link to them in process documentation, or  
- add a **custom integration** (outside this guide).

Treat the Drive settings as **communication + deep-link helpers** for testers and staff, unless your implementer has added extra automation.

### Other flags in settings

- **Internal file policy note** — Shown on the dashboard / files context when filled; use for “classification”, retention, or naming rules.
- **Google Drive / BIM 360** — Currently **placeholders** in settings; any real integration would be custom or future work.

---

## 6. Where Desk still matters

Heavy ERPNext setup is done in **Desk**, not in the portal:

- **Project** master data, **Portal Project Manager**, **Portal Kanban Stage**, **Portal Project Code**
- **Customer** links, accounting, **Task** creation/editing in depth
- **Portal Project Settings** (Drive URL, file note, who can create projects, demo seed flags)
- **User** and **Role** assignment

The portal is for **day-to-day visibility**, **team membership** (where allowed), **file exchange on the project**, and **planning views** (Kanban / calendar).

---

## 7. Testing checklist (quick)

- [ ] Login and access check  
- [ ] Dashboard loads without error  
- [ ] At least one project visible (or create one if permitted)  
- [ ] Project detail → team save (as permitted)  
- [ ] Upload file → appears in list → open/download works  
- [ ] Private upload vs public (per your security test plan)  
- [ ] Kanban and Calendar show expected projects  
- [ ] Profile save  
- [ ] Theme: Light / Dark / System  
- [ ] Sidebar collapse (Ctrl+B)  
- [ ] Logout → portal login URL  

For a full manual QA checklist covering every screen (Org Chart, Teams, Gantt, Daily Task, Contracts, Files/sharing, Admin, known issues), see **[TESTING.md](TESTING.md)**.

---

## 8. Common issues

| Symptom | What to check |
|--------|----------------|
| “You do not have access to the project portal” | User needs a portal role or **Project User** row on a project. |
| No projects in the list | User not on any project team; or not Projects Manager / System Manager. |
| Cannot create project | **Portal Project Settings** → “Allow any portal user to create projects”, or user needs manager/create permission. |
| Cannot change team | User is not **Portal Project Manager** on that project and not Projects/System Manager. |
| Upload fails | Network; session expired (log in again); file size limits on server; permission on **Project**. |
| Drive banner but files “only” on ERPNext | Expected: see **Files, ERPNext, and Frappe Drive** above. |
| **"ATA AI Chat" sidebar link does nothing / blank page** | Known gap — the `/ai-chat` route is not yet wired up in the app; report to your administrator/developer rather than retrying. |
| Task quick-create project/assignee dropdown stays empty | Known gap — the underlying lookup endpoints are not yet implemented; create/assign the task from **Project detail** or Desk instead. |
| "Submit to Client Submittal" button in File Browser errors | Known gap — the backend action for this button is not yet implemented. |

---

## 9. For administrators (one line each)

- Install/build: `bench install-app portal_app`, `bench build --app portal_app`, migrate site after DocType changes.  
- **Node** for frontend build: match `frontend/.nvmrc` if Vite fails on old Node.  
- **Demo data** (if implemented): **Admin** page and/or `bench execute` per your implementation notes—**never** enable demo seed on production without review.

---

*This guide matches the **portal_app** behaviour: ERPNext **Project**–centric SPA at **`/portal-app/`**, files as **File** attachments on **Project**, and **Portal Project Settings** for policy text and Frappe Drive **URL/banner** hints.*

---

## 10. BRD Baseline (ATA Project Management System)

The following baseline is included from the official BRD:

### BUSINESS REQUIREMENTS DOCUMENT
- **Project Management System**
- **Based on ERPNext Platform**
- **ATA Architecture**
- **February 3, 2026**

### Document Information
- **Project Name:** ATA Project Management System
- **Organization:** ATA Architecture
- **Platform:** ERPNext (Frappe Framework)
- **Implementation Partner:** OpenArabia
- **Date:** 2/3/2026
- **Version:** 1.0

### 1. Executive Summary
ATA Architecture requires a comprehensive project management system to effectively manage architectural projects, track tasks, monitor costs, and optimize resource utilization. This BRD defines the business requirements for an ERPNext-based project management solution.

#### 1.1 Project Objectives
- Centralize project tracking and management
- Implement structured task assignment and tracking with Gantt charts
- Enable accurate project costing and budget management
- Track timesheet and resource utilization
- Provide real-time project visibility and reporting

#### 1.2 Key Benefits
- Enhanced project visibility (real-time status tracking and dashboards)
- Improved resource management (team allocation and utilization)
- Better cost control (actual vs budget tracking)
- Timeline management with visual Gantt planning
- Data-driven decisions with reporting and analytics

### 2. Current State Analysis
#### 2.1 Existing Challenges
- Manual spreadsheet-driven tracking
- Limited real-time portfolio visibility
- Informal task management
- Budget overruns from delayed cost visibility
- Resource conflicts
- Manual reporting burden

### 3. Business Objectives
- Centralized project management
- Task and timeline control
- Financial oversight
- Resource optimization
- Automated reporting

### 4. Functional Requirements

#### 4.1 Project Management
**FR-PM-001 (High): Project Assignment & Management**
- Create projects (name, code, client, dates)
- Assign project manager and team with roles
- Track project lifecycle and status
- Define budget and financial parameters
- Link projects to clients

**FR-PM-002 (High): Project Views & Dashboards**
- List view with filtering/sorting
- Kanban board
- Calendar view
- Portfolio dashboard
- Project-specific dashboard
- Role-customized views

#### 4.2 Task Management
**FR-TM-001 (High): Task Creation & Assignment**
- Task creation linked to projects
- Assignment to team members with deadlines
- Priority (Low/Medium/High/Urgent)
- Expected vs actual hours
- Dependencies and subtasks
- Task file attachments

**FR-TM-002 (High): Multiple Task Views**
- Tree view
- Kanban view with drag/drop status updates
- Calendar view
- Gantt integration
- My Tasks view
- Seamless view switching

**FR-TM-003 (High): Task Status & Progress Tracking**
- Configurable status workflow
- Progress tracking (0-100%)
- Completion indicators
- Status change notifications
- Activity logs
- Comment threads

#### 4.3 Gantt Chart Integration
**FR-GC-001 (High): Visual Timeline Representation**
- Timeline rendering for tasks
- Dependency lines
- Milestones
- Color coding by status/priority/assignee
- Zoom (day/week/month)
- Export image/PDF

**FR-GC-002 (Medium): Interactive Gantt Features**
- Drag/drop schedule changes
- Dependency recalculation
- Visual dependency creation
- Baseline vs actual
- Conflict alerts
- Today indicator

**FR-GC-003 (Medium): Milestone Management**
- Milestones with target dates
- Link tasks to milestones
- Track completion
- Approaching-date alerts
- Prominent milestone display
- Milestone reports

#### 4.4 Costing & Budgeting
**FR-CB-001 (High): Project Budget Management**
- Set total budget
- Category-level budget breakdown
- Revision audit history
- Threshold alerts (80/90/100%)

**FR-CB-002 (High): Cost Tracking**
- Labor cost from approved timesheets
- Manual expense entry
- Link costs to tasks
- Real-time budget vs actual
- Cost reporting by project/task/category/period

**FR-CB-003 (Medium): Profitability Analysis**
- Gross margin calculation
- Revenue vs costs (if available)
- Forecast profitability

#### 4.5 Time Sheet Management
**FR-TS-001 (High): Timesheet Entry & Submission**
- Daily/weekly entries
- Project/task linking
- Hours + notes
- Billable/non-billable
- Submission workflow
- Draft save
- Copy previous timesheet

**FR-TS-002 (High): Timesheet Approval Workflow**
- Route to manager/supervisor
- Approve/reject with comments
- Employee notifications
- Bulk approval
- Approval history
- Approved-only costing impact

**FR-TS-003 (Medium): Time Analysis & Reporting**
- Time by project/task/employee
- Actual vs estimated hours
- Utilization reports
- Export to payroll/billing
- Weekly/monthly/quarterly reporting

#### 4.6 Reporting & Analytics
**FR-RA-001 (High): Project Dashboards**
- Timeline/budget/task visuals
- Overdue and at-risk highlights

**FR-RA-002 (High): Standard Reports**
- Project status reports
- Task completion reports
- Timesheet summaries
- Export to PDF/Excel

**FR-RA-003 (Medium): Custom Report Builder**
- Field/filter/group/sort query builder
- Saved report templates
- Sharing custom reports

### 5. User Roles & Permissions
- **System Admin:** Full access
- **Director/Executive:** Read-only portfolio/report access
- **Project Manager:** Full control over assigned projects
- **Architect/Designer:** Project read + task/timesheet write
- **Team Member:** Assigned-task scope
- **Finance/Accounts:** Read-only financial scope

### 6. Technical Requirements
#### 6.1 Platform & Technology
- ERPNext on Frappe, MariaDB
- English + Arabic support
- Cloud deployment

#### 6.2 Performance Requirements
- Page load < 3s
- Gantt render < 5s for 100+ tasks
- Report generation < 10s
- 50+ concurrent users
- 99.5% uptime

#### 6.3 Security Requirements
- RBAC
- SSL/TLS
- Audit trail
- Strong passwords
- Optional 2FA

### 7. Success Criteria
#### 7.1 Adoption
- 100% active projects in-system within 4 weeks
- 90% daily active team use
- 90% timesheet compliance
- User satisfaction >= 4.0/5.0

#### 7.2 Business Impact
- 50% reduction in manual status effort
- Improved budget accuracy
- Better resource visibility
- Reduced project delays
- Better data-driven decisions

### 8. Implementation Approach
- **Timeline:** 8–12 weeks (OpenArabia proposal)
- **Phases:** setup/config -> migration/integration -> UAT/training -> pilot/go-live
- **Dependencies:** infra readiness, stakeholder availability, migration data quality, timely approvals

### 9. Conclusion
The BRD defines an ERPNext-based end-to-end project management solution for ATA Architecture, covering project lifecycle, tasks, timelines, resources, costs, and analytics.

#### 9.1 Next Steps
- Review and approve BRD
- Finalize OpenArabia contract
- Schedule kickoff
- Identify champions
- Prepare migration data

---

**End of BRD baseline section**
