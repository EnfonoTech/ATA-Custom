# Portal App — User Guide

> A guided tour of the Portal App from sign-in to sharing your first folder,
> organised by what you actually do — not by what's on the menu. Use the table
> of contents to jump to your role.

**URL:** your bench's `/portal-app` (e.g. `https://erp.acme.com/portal-app`).

---

## Table of contents

1. [Who you are — five roles](#1-who-you-are)
2. [Signing in](#2-signing-in)
3. [Layout & navigation](#3-layout--navigation)
4. [Dashboard](#4-dashboard)
5. [Projects](#5-projects)
6. [Tasks](#6-tasks)
7. [Kanban](#7-kanban)
8. [Calendar](#8-calendar)
9. [Files](#9-files)
10. [Sharing — Drive-style](#10-sharing-drive-style)
11. [Shared with me](#11-shared-with-me)
12. [File tools (Auditor)](#12-file-tools-auditor)
13. [Profile & preferences](#13-profile--preferences)
14. [Admin (System Manager)](#14-admin-system-manager)
15. [Workflow recipes](#15-workflow-recipes)
16. [FAQ & troubleshooting](#16-faq--troubleshooting)

---

## 1. Who you are

The portal looks slightly different depending on your role. You can hold more
than one.

| Role | What you see |
|---|---|
| **Customer Portal User** | A read-only view of *your* projects' files. No upload, no share, no team chrome. Your linked customer is shown on Profile. |
| **Project Member** | Anyone listed on a Project (`Project Users` table or as Portal Project Manager). Can browse, upload, **share** folders/files with teammates, and revoke shares they themselves created. |
| **Portal Project Manager** | The user named in `portal_project_manager` on a Project (or its Owner if blank). Can rename folder segments, delete any file, revoke any share, manage Customer Portal Users on that project. |
| **Projects Manager / System Manager** | Full Frappe-side access. Can do everything a Portal Project Manager can do, on every project. |
| **Auditor** | Can edit the company-wide folder template via **File tools**. Doesn't grant project access on its own; combine with Project Member to actually use the portal. |

> Heuristic: if you can manage a project, you'll see **Rename**, **Delete**, and
> **Manage team** controls. If you can only collaborate, you'll still see
> **Share** and **Upload**.

---

## 2. Signing in

```
┌────────────────────────────────────────────────────────────────┐
│   ███  Portal · Projects · Files · Audit                       │
│                                                                │
│        Where projects, drawings & people                       │
│                  come into focus.                              │
│                                                                │
│   [ Sign in card ]                                             │
│      Email      ____________________                           │
│      Password   _______________👁                              │
│                                                                │
│      [ Sign in ]                                               │
└────────────────────────────────────────────────────────────────┘
```

* Use the email of any Frappe user assigned to one or more Projects.
* Click 👁 to reveal the password if you're double-checking.
* Click **Forgot?** to use the standard Frappe password reset.
* If sign-in succeeds but you don't see a dashboard, your user has no
  portal-visible projects. Ask your manager to add you to a project's *Users*
  table or set you as `portal_project_manager`.

---

## 3. Layout & navigation

```
┌────────────────────────────────────────────────────────────────┐
│ ☰  Portal           [search…]                Desk  ●  You      │  ← Header
├──────────────┬─────────────────────────────────────────────────┤
│ WORKSPACE    │                                                 │
│  • Dashboard │                                                 │
│  • Projects  │                                                 │
│  • Tasks     │                  Page content                   │
│  • Kanban    │             (router-view, scrollable)           │
│  • Calendar  │                                                 │
│              │                                                 │
│ FILES        │                                                 │
│  • Files     │                                                 │
│  • Shared    │                                                 │
│    with me   │                                                 │
│  • File tools│ (Auditor only)                                  │
│              │                                                 │
│ ACCOUNT      │                                                 │
│  • Profile   │                                                 │
│  • Admin     │ (System Manager / portal admin only)            │
└──────────────┴─────────────────────────────────────────────────┘
```

* **`Ctrl + B`** toggles the sidebar.
* The **Desk** button (top right) jumps you back to the Frappe desk.
* The avatar opens a small menu (Profile, Sign out).
* **The page itself scrolls** — header and sidebar stay anchored.

---

## 4. Dashboard

```
[Greeting hero]  Good morning, Siva
                 [ All projects ]   [ + New project ]

[KPI tiles]  Projects · Open tasks · Estimated cost · Budget risk

[Recently visited]  pinned chips you can click

[ERP status]            [Kanban stage]
[My open tasks]         [Upcoming deadlines]

[Recent projects table]
```

* The hero greeting changes with the time of day.
* **Recently visited** chips are remembered locally per browser, not synced.
* Click any row in **Recent projects** to open its detail page.
* **+ New project** appears only if your role can create projects.

---

## 5. Projects

The Projects page lists every project you can access.

```
[ Search by name / code / customer ]   [ status ▾ ] [ customer ▾ ]
                                                    [ + New project ]

┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│ Code · Name  │ Customer │  Status  │   End    │  Stage   │
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ FR-PM-001    │ Acme Co  │  Open    │ 30 Apr   │ Active   │
│ Tower 4      │          │          │          │          │
└──────────────┴──────────┴──────────┴──────────┴──────────┘
```

Click a project to open its **detail page**:

```
┌──────────────────────────────────────────────────────────────┐
│  Title editable inline · Customer pill · Stage pill          │
│  Project code · Manager · Dates                              │
│                                                              │
│  [ Tasks summary ]  [ Files ]  [ Team ]  [ Customer portal ] │
│                                                              │
│  Files panel (same Drive-style upload UI as /files)          │
│   ▸ Upload to <subfolder>     [Share] [Upload files]         │
│   ▸ Drop zone with "Goes into <path>"                        │
│   ▸ Recent files list with Open / Delete                     │
└──────────────────────────────────────────────────────────────┘
```

Things you can do:

| You are… | You can… |
|---|---|
| Project Member | Upload, see all files, share with users you know, delete *your* uploads |
| Portal PM | Above + rename folders, delete any file, edit project title, link a customer, manage team and customer-portal users |
| Customer Portal User | Read-only view of files |

---

## 6. Tasks

A unified workspace across every project you can see.

```
[KPI tiles]   Total · Open · Overdue

[Assigned to you (open)]  ← clickable cards that jump to the project

[Filters bar]
   🔎 search · status ▾ · priority ▾ · project ▾ · ☐ Only my tasks

[Task table]
   Task · Project · Status · Priority · Progress · Start · End · [Save]
```

* Each task row has **inline editors** for status, priority, progress, and
  dates. Click **Save** on the row to commit.
* Rows with status **Overdue** are tinted rose; **Completed** are tinted green.

---

## 7. Kanban

Visual project lifecycle.

```
[ Planning ]   [ Active ]   [ On Hold ]   [ Review ]   [ Done ]
   • A           • B            • C          • D         • E
   • B'          • F                                     • G
                              (color rail per stage)
```

* Each card shows project code, name, customer, and an arrow to open it.
* **Managers** see a stage selector at the bottom of each card. Change it to
  move the project. The board reloads after each update.

---

## 8. Calendar

Project + task dates plotted across a month / week / day grid.

```
[Type filter]  All / Projects only / Tasks only
[Project filter]
[Search]
[<  April 2026  >]
```

* Click any event to jump to its project or task.
* Use the type filter to focus on milestones vs. day-to-day tasks.

---

## 9. Files

The hub for everything attached to a project.

```
                                        ┌───────────────────────────┐
[Project picker ▾]      [Search] [↩]    │  Goal: drop files into    │
                                        │  the *right* subfolder of │
[Folder tree / list]                    │  the standard structure.  │
   ▸ 01-DOCUMENTS                       └───────────────────────────┘
       └ 01-CLIENT DATA
            └ 01-BUSINESS CARD            (3 files)
            └ 02-TITLE DEED               (1 file)
   ▸ 02-CONCEPT
   ...

[Filter pill] Showing files in: 01-DOCUMENTS / 01-CLIENT DATA / 01-BUSINESS CARD  [✕ clear]

──── Upload card (also on /projects/:name) ────────────────────────
 [ 📁 Upload to                       ]  [ Share ] [ Upload files ]
 [ 01-BUSINESS CARD                   ]
 [ 01-DOCUMENTS / 01-CLIENT DATA      ]
 │                                     │
 │   ☁  Drop files here or click       │
 │     Goes into 01-BUSINESS CARD      │
 │                                     │
 [ ☐ Private upload ]    [ ▾ Advanced options ]
────────────────────────────────────────────────────────────────────

[File table]   File · Size · Subfolder · Owner · Created · Open · Delete
```

### 9.1 Picking a folder

Clicking the **Upload to** tile opens a search-and-tree picker:

```
[ 🔎 Search folders…                                    ]

▾ 01-DOCUMENTS
   ▾ 01-CLIENT DATA
      • 01-BUSINESS CARD       ✓ (selected)
      • 02-TITLE DEED
      • 03-ID
      …
   • 02-LOCATION
▾ 02-CONCEPT
…

[ Done ]
```

* Type in the search box to flatten and filter.
* Click any leaf to select; the modal closes and the upload card scrolls to
  the drop zone with the new target.
* The drop zone always says **"Goes into <full path>"** so you can verify
  before letting go of files.

### 9.2 Uploading

* Drag-and-drop, or click the drop zone, or click **Upload files**.
* Multiple files at once is fine.
* "Private upload" hides the file from anyone who doesn't have explicit access.
* "Advanced options" lets you also send a copy to Frappe Drive / Google Drive /
  BIM 360 (admin must have configured the webhook in *Portal Project Settings*).

A toast confirms: **"Uploaded 3 files to 01-BUSINESS CARD."**

### 9.3 Folder cards

```
┌──────────────────────────────┐
│ 📁 01-CLIENT DATA            │
│    01-DOCUMENTS              │  ← parent path eyebrow
│    27 files                  │
│ ────────────────             │
│   [ Rename ]   [ Share ]     │  Rename = manager only
└──────────────────────────────┘
```

Clicking a card filters the file list to that folder, sets it as the upload
target, and smoothly scrolls down to the upload zone.

---

## 10. Sharing — Drive-style

```
[ Share button on any folder card or upload tile ]
                ↓
┌──────────────────────────────────────────────────┐
│ Share folder                                     │
│ 04-ELECTRICAL / INCOMING                         │
│ ─────────────────────────────────────────────────│
│ Add people                                       │
│   🔎 search by email or username   Days [30]     │
│   ▼ matching users                               │
│      Avatar  Name             email    + Add     │
│                                                  │
│ People with access                               │
│   ●  Maria S.  maria@…  · expires 2026-05-27     │
│                                          Revoke  │
│   ●  Karim     karim@…  · ERPNext share          │
│                                          Revoke  │
│                                                  │
│ Anyone with the link  (only if tracking is on)   │
│   🔗 https://…  Expires 4 May · 7 opens          │
│      [ Copy ]   Revoke link                      │
│                                                  │
│ [ Done ]                                         │
└──────────────────────────────────────────────────┘
```

What sharing actually does, behind the scenes:

```
share_folder_with_user
   ├─ ERPNext DocShare on the folder    → user can list it
   ├─ ERPNext DocShare on every file    → user can open each one
   ├─ ERPNext DocShare on the Project   → user can navigate to it
   └─ Audit row in Portal Folder Share  → expiry, "shared by", revoke history
```

So your colleague will see those files in:

* their portal **Shared with me** page,
* the project's Files panel,
* their normal Frappe desk view.

### 10.1 Who can share, who can revoke

| Action | Project member | Portal PM / Manager |
|---|---|---|
| Share a folder with someone | ✅ | ✅ |
| Revoke a share **you** created | ✅ | ✅ |
| Revoke a share **someone else** created | ❌ | ✅ |
| Create / revoke a public **link** share | ✅ (with expiry) | ✅ |

If the **Anyone with the link** section is replaced by an info strip
("Using ERPNext native sharing — install the migration to enable expiry…"),
your bench hasn't run `bench migrate` after the latest portal upgrade. Adding
and revoking *user* shares still works.

### 10.2 Public share links

A link share is a signed URL like `…/portal-app/shared-folder?token=…`. It
gives anyone with the URL **read-only** access to the non-private files in
that folder until the link expires or you revoke it. Use it for:

* sending a deliverable to a client who isn't a portal user,
* attaching evidence to a support ticket.

It's not the right tool for ongoing access — share with a specific user for
that.

---

## 11. Shared with me

```
[Refresh]                                       [3 projects · 8 folders · 41 files]

[🔎 search by project, folder, or file name]

▾ Project: Tower 4                       Open
   ▾ 04-WORKGDRAWINGS / … / INCOMING
       (12 files)                       Open in Files
        ▸ floor-plans-rev-3.pdf  · 4.2 MB   Open
        ▸ structural-grid.dwg    · 11 MB    Open
        …
   ▸ 02-CONCEPT / …
▸ Project: Acme HQ
▸ Project: Riverbank Towers
```

* Sources: portal share grants **and** ERPNext-native shares from desk users.
* Expiry tag appears when set; rows from desk users show **"ERPNext share"**.
* **Open in Files** deep-links to `/files?project=…&folder=…` with the folder
  pre-selected and the upload zone targeted there.
* Empty state ("Nothing shared with you yet") is shown when nobody has shared
  anything yet.

---

## 12. File tools (Auditor)

Only visible to users with the **Auditor** role (or System Manager). It's the
single place where the **company-wide standard folder structure** for new
projects is edited.

```
[Auditor tools] File tools                              [< Back to Files]

Default file subfolders                            [company-wide]
   • One path per row.
   • Use slashes for nesting:  Parent/Child
   • Mirrors Portal Project Settings → Subfolder template

  1.  📁 01-DOCUMENTS/01-CLIENT DATA/01-BUSINESS CARD     [↑] [↓] [🗑]
  2.  📁 01-DOCUMENTS/01-CLIENT DATA/02-TITLE DEED        [↑] [↓] [🗑]
  …
  67. 📁 06-CLIENT SUBMITTAL                              [↑] [↓] [🗑]

[ + Add row ]   [ 💾 Save template ]   [ 📤 Import ZIP structure ]
```

### 12.1 Editing rows

* Click **+ Add row** to append a blank row at the end.
* Use **↑ ↓** to reorder.
* Each row is one *leaf* path. Intermediate parents are auto-created on save.
* Save replaces the entire template atomically.

### 12.2 Importing from a ZIP

Click **Import ZIP structure** and pick a `.zip` of an existing folder
hierarchy. The system reads only the directory entries (no files) and
replaces the template with those leaf paths. Useful for adopting a layout
from disk verbatim.

> Existing project folders are **never renamed automatically**. New projects
> use the new template; existing projects keep their old folders and pick up
> any new leaves on next visit.

---

## 13. Profile & preferences

```
[Profile cover gradient]
  [Avatar]  Siva
            siva@enfono.com
            roles: Projects User · Portal Customer

[Portal permissions]
   ✓ You can manage 2 project(s)…
   ✓ You can edit the company-wide subfolder template
   [Open Files] [File tools]

[Linked customer]   (only for Portal Customer users)
   Acme Corporation
   CUST-0042

[Preferences]
   Full name __________
   Mobile ____________
   Language __ (e.g. en)
   Time zone ____________ (e.g. Asia/Riyadh)
   [ Save changes ]
```

Saving here also updates the avatar/name shown in the header.

---

## 14. Admin (System Manager)

Visible only to portal admins. Two main flows:

* **Create portal user** — make a Frappe `User`, set roles
  (Projects User / Projects Manager / Portal Customer), optionally link a
  Customer record (for client-side users), optionally send a welcome email.
* **Run demo seed** — populate Customers, Projects, Tasks for a showcase. Gated
  behind *Allow portal demo seed* in **Portal Project Settings**, plus
  developer mode.

---

## 15. Workflow recipes

### 15.1 First-time setup (administrator)

```
1.  bench --site <site> install-app portal_app
2.  bench --site <site> migrate
3.  Open Desk → Portal Project Settings  (auto-created Single doctype)
        ☐ Allow any portal user to create projects   (recommended OFF)
        ☐ Use Frappe Drive / Google Drive / BIM 360 (paste webhook URLs)
        ☐ Welcome text for client document access  (Markdown / rich text)
4.  Assign roles:
        – Projects Users  → people who collaborate
        – Portal Customer → external client users  (set portal_linked_customer)
        – Auditor         → people who curate the folder template
5.  Browse to /portal-app — every assigned user can sign in.
```

### 15.2 Onboarding a new project

```
[ Portal PM ]  Projects → + New project
                Title, code (FR-PM-001), customer, end date, manager
                Save
                ↓
The standard folder tree is created on first visit to /files for that project.
                ↓
Add team members:  Project detail → Team → search → Save
Add customer-portal users: Project detail → Customer portal → search → Save
                ↓
Drag a few files into 01-DOCUMENTS / … to seed the project.
```

### 15.3 Sharing a deliverable with a teammate

```
You are a Project Member.
1. Files page → pick the project
2. Click the folder card you want to share (or pick it as upload target)
3. Click Share
4. Type the user's email or name; click + Add (default 30 days)
5. Done

They will see it under Shared with me, plus in the normal project view.
```

### 15.4 Sending a deliverable outside the company

```
1. Open the share modal on the relevant folder
2. Anyone with the link → Days [7] → Create link
3. Link is auto-copied. Paste into your email / chat.
4. Recipient opens the URL → sees a read-only listing until expiry.
5. If circumstances change: open the modal → Revoke link → done.
```

### 15.5 Revoking access

```
Open the share modal on the folder
   ▸ User shares list  → Revoke  (you can revoke shares you created;
                                 manager can revoke any)
   ▸ Anyone with the link → Revoke link
Effect is immediate — within seconds the user / link can no longer open files.
```

### 15.6 Adopting a folder layout from a real project (Auditor)

```
1. Zip the folder structure you want.        $ zip -r layout.zip ./00-PROJECT
   (Tip: only directories matter; files inside are ignored.)
2. /file-tools → Import ZIP structure → choose layout.zip
3. Review the rows, save.
4. Tell project managers: "New projects will use this layout. Existing projects
   are unchanged but will pick up new leaves on next visit."
```

### 15.7 Deleting a file

```
You uploaded it             →  Files page row → Delete (always allowed)
You're the project manager  →  Files page row → Delete (any file)
You're a customer-portal    →  Cannot delete; ask your contact at the firm
```

### 15.8 If you can't find a project

```
1. Profile page → check your roles. You need Projects User OR Portal Customer
   (with portal_linked_customer set), OR be on the project's Users table.
2. Ask the manager to add you to the project (Project detail → Team).
3. Sign out and back in — capabilities are loaded once per session.
```

---

## 16. FAQ & troubleshooting

**Q. The Share button is greyed out.**
You're not allocated to that project. Ask the manager to add you to the
project's *Users* table.

**Q. I shared a folder but the user can list it but can't open files.**
The cascade DocShare on individual files failed for some reason. Re-share —
the share function is idempotent and re-issues every grant. If it persists,
ask an admin to check **Error Log** for `Portal: docshare grant`.

**Q. I get "Maximum Attachment Limit of 4 has been reached" when uploading.**
Your bench hasn't run the latest migration yet. Ask an admin to run
`bench migrate`. The portal also bypasses this at runtime, so if you keep
seeing it on every upload, the runtime fallback is failing — check the
Error Log.

**Q. I see "Invalid Request" / `CSRFTokenError` after I just signed in.**
Refresh once. The portal automatically refreshes the CSRF token and retries
the next call. If it persists, your cookies are blocked — check browser
settings.

**Q. The folder I want isn't in the picker.**
The folder structure for a project is created lazily. Visit
`/files` for that project once — the standard template runs and every leaf
appears. Auditors can extend the template via **File tools**.

**Q. Why do I see "ERPNext share" instead of an expiry?**
That share was created from Frappe desk (or before the portal share-tracking
DocType was installed). It still works, just without expiry / audit info.
Re-share through the modal to get the full feature set.

**Q. The shared folder link I sent has expired.**
Open the share modal again, create a fresh link, send it.

**Q. I'm a customer portal user — why don't I see Tasks / Kanban?**
Customer portal is intentionally focused on documents only. Speak to your
project manager for status updates.

**Q. Can I download a whole folder as a zip?**
Not yet. Open the folder, multi-select files, and use your browser's
download. (Bulk download is on the roadmap.)

**Q. Where is my data stored?**
* File contents → Frappe's `/private/files` or `/public/files` on the
  bench server.
* File metadata, shares, audit → MariaDB.
* Optional copies → Frappe Drive / Google Drive / BIM 360 if your admin
  configured webhooks.

---

## A. Cheat sheet

```
Sign in        →  /portal-app
Dashboard      →  /portal-app/dashboard
Projects       →  /portal-app/projects
A project      →  /portal-app/projects/<id>
Tasks          →  /portal-app/tasks
Kanban         →  /portal-app/kanban
Calendar       →  /portal-app/calendar
Files          →  /portal-app/files
Files w/folder →  /portal-app/files?project=<id>&folder=<File-name>
Shared w/ me   →  /portal-app/shared-with-me
File tools     →  /portal-app/file-tools     (Auditor)
Profile        →  /portal-app/profile
Admin          →  /portal-app/admin           (System Manager)

Public link    →  /portal-app/shared-folder?token=<signed-token>

Keyboard
   Ctrl + B    →  toggle sidebar
   Enter       →  submit (login form, password modal)
   Esc         →  close most modals
```
