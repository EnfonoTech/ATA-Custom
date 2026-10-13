# ATA Project Portal — Full Test Guide (Before Client Handover)

**Site:** https://ata.enfonoerp.com
**Portal address staff will use:** https://ata.enfonoerp.com/portal-app
**Written for:** `64c8002` (the five-role release: Super Admin, Department Admin, Team Lead, Team Member, Client Customer; the editable Org Chart; password reset; the client Incoming / Outgoing folders)

---

## How to use this guide

Work through it **top to bottom**. Later tests depend on data created in earlier ones.

Every test has:
- **Do this** — the exact clicks.
- **You should see** — what a correct system does.
- **If you see this instead** — what a failure looks like, so you don't pass a broken test by accident.

Tick the box when a test passes. If a test fails, **stop and write down the test number** — do not carry on and hope.

> **Important:** Do this on the real production site, but only with the throwaway test data this guide tells you to create. At the end there is a **Clean-up** section that removes it all. Do not test with a real client's documents.

---

## Part 0 — Before you start

### 0.1 The five kinds of user

The portal behaves completely differently depending on the user's role and team. You must understand this before testing, or the results will look like bugs when they are correct behaviour.

| Role | Which projects they see | Can they edit projects? | Can they see project money? |
|---|---|---|---|
| **Super Admin** (the ERPNext role System Manager) | Every project on the system | Yes | Yes — every project |
| **Department Admin** | The projects of the teams they administer, **plus the projects that belong to no team** | Yes, any project they can see | **Only projects where they are named "Lead Architect"** |
| **Team Lead** | The projects of the team they lead | Yes, on those projects | No |
| **Team Member** (the ERPNext role Projects User) | **Only** projects they were added to (or lead as Lead Architect) | Yes, on those projects — never anyone else's | No |
| **Client Customer** | Only projects belonging to their linked Customer(s), and in them only the **06-CLIENT SUBMITTAL** folder | No | No |
| **Auditor** (an extra ERPNext role) | (as per their other roles) | — | No — but can edit the folder template |

How a project "belongs to a team": its **Portal Team** is that team, or somebody from that team is on its Team card or is its Lead Architect. Every other project belongs to **no team**.

Points people get wrong:

1. A **Department Admin does not see every project**. They see their own teams' projects and the projects that belong to no team (so somebody can put those under a team), and nothing that belongs to another team. What is also restricted for them is the **money**: only on projects where they are the Lead Architect.
2. A **Team Member sees only their own projects**, and starts with an empty list until somebody puts them on one. On those projects they can work (edit, upload, rename folders, share), but they never see money, never see the Lead Architect column, and cannot take people off the team.
3. A **Team Lead** sees only the projects of their team, never the no-team projects, and can add people to those projects but not remove them.
4. A **Client Customer** can send files to ATA, but only into the **Outgoing** folder inside 06-CLIENT SUBMITTAL. They read both **Incoming** (what ATA sends them) and **Outgoing**, and nothing else.

### 0.2 Accounts you need before starting

Ask the administrator to create these seven test logins. Write the passwords here and keep this sheet safe. (The address names are older than the role names; use the role in the third column, not the address, to tell them apart.)

| # | Login email | Role to give | Password |
|---|---|---|---|
| A | `test.sysmgr@ata-test.local` | Super Admin | ____________ |
| B | `test.pm@ata-test.local` | Department Admin (of TEAM-1 only) | ____________ |
| C | `test.staff@ata-test.local` | Team Member (in TEAM-1) | ____________ |
| D | `test.staff2@ata-test.local` | Team Member (in TEAM-2) | ____________ |
| E | *(created during Test 8)* | Client Customer | ____________ |
| F | `test.lead@ata-test.local` | Team Lead (of TEAM-1) | ____________ |
| G | `test.consultant@ata-test.local` | Team Member, in **no** team | ____________ |

Also ask the administrator for **two teams**, called here TEAM-1 and TEAM-2 (each is a Department with an office; a Super Admin creates it with **Create team** on the Teams page and fills it from the Teams page or the Org Chart). User B administers TEAM-1 only; user F leads TEAM-1; user C is in TEAM-1; user D is in TEAM-2; user G is in no team. Users C and D start with **no project**.

Use a **different browser** (or a private/incognito window) for each user. If you just log out and back in, old data stays cached and you will get confusing results.

### 0.3 Test files to prepare

Put these on your desktop before starting:

| File | What it is | Used in |
|---|---|---|
| `test-plan.pdf` | any small PDF | Test 5 |
| `test-drawing.dwg` | any file, rename the extension to `.dwg` | Test 5 |
| `test-photo.jpg` | any small image | Test 5 |
| `test-bundle.zip` | a ZIP containing 3–4 files inside a folder | Test 6 |
| `test-bad.html` | any text file renamed to `.html` | Test 14 |

---

## Part 1 — Getting in

### Test 1.1 — The login page loads

- [ ] **Do this:** Open a private browser window. Go to `https://ata.enfonoerp.com/portal-app`.
- **You should see:** A login page with the company logo and name.
- **If you see this instead:** A blank white page, or "Site not found" → stop, the deployment is broken.

### Test 1.2 — Wrong password is refused

- [ ] **Do this:** Type user A's email with a deliberately wrong password. Click Login.
- **You should see:** An error message. You stay on the login page.
- **If you see this instead:** You get in → **critical failure, stop immediately.**

### Test 1.3 — Correct password works

- [ ] **Do this:** Log in as **user A (Super Admin)**.
- **You should see:** The Dashboard, with a menu down the left side.

### Test 1.4 — A user with no portal access is refused

This checks that having *an* ERPNext login is not enough to enter the portal.

- [ ] **Do this:** Ask the administrator to create `test.outsider@ata-test.local` with **only** the "Blogger" role (or any role not in the table in 0.1). Log in as that user and go to `/portal-app`.
- **You should see:** A message saying you do not have access to the project portal, and you are logged out.
- **If you see this instead:** They reach the Dashboard → **failure, report it.**

### Test 1.5 — Logout really logs you out

This one is easy to get wrong, so follow it exactly.

- [ ] **Do this:** As user A, click your name (top right) → **Logout**. Then press the browser **Back** button. Then type `https://ata.enfonoerp.com/portal-app/projects` directly in the address bar.
- **You should see:** The login page both times.
- **If you see this instead:** You land back inside the portal still logged in → **failure.** (This was a real bug that was fixed — worth checking properly.)

### Test 1.6 — "Forgot Password?" opens a reset form on the login card

- [ ] **Do this:** Open a private window, go to the login page and click **Forgot Password?** (just above the Sign In button).
- **You should see:** The card changes to "Reset your password" with a box for your email and a **Send reset link** button. You stay inside the portal (it does not jump to an ERPNext page). **Back to sign in** returns you to the normal form.
- **If you see this instead:** The link does nothing, or opens a different site → **failure.** (Requesting a link is tested in Part 19.)

---

## Part 2 — Creating a customer

### Test 2.1 — Create a customer from inside the portal

- [ ] **Do this:**
  1. Log in as **user A (Super Admin)**.
  2. Left menu → **Projects**.
  3. Click **New Project** (the button top-right of the project list), type the title `ZZ TEST CUSTOMER SETUP`, leave everything else blank and click **Create project**. The new project opens.
  4. Scroll to the panel headed **Customer** and click **Create customer (no duplicate name)**.
  5. In the **Customer name** box type `ATA Test Client One` and click **Create or link**.
- **You should see:** A green "Customer linked." message, and the **Client** tile at the top of the project now shows `ATA Test Client One`.
- **Note:** The Customer box on the *New Project* form is a pick-list of existing customers; it cannot create one. New customers are created from a project's **Customer** panel, as above.

### Test 2.2 — A Team Member with no project cannot search or create customers

- [ ] **Do this:** Log in as **user C (Team Member)** in a different browser. C is on no project yet. Go to Projects. If there is a **New Project** button (it appears while "Allow any portal user to create projects" is ticked in Portal Project Settings, which is the default), click it and click into the **Customer** box.
- **You should see:** Either no New Project button at all, or a Customer box that offers no customers to pick.
- **If you see this instead:** C can see and pick customers from the list → **failure, report it.**

---

## Part 3 — Creating a project

### Test 3.1 — Create the test project

- [ ] **Do this:** As **user A**, go to Projects → **New Project** and fill in:

| Field | Value to type |
|---|---|
| Title | `ZZ TEST PROJECT ALPHA` |
| Portal code | `ZZ-001` |
| Customer | click the box and pick `ATA Test Client One` from the list |
| Lead Architect | **user B** (`test.pm@ata-test.local`) |
| Phase | pick any (e.g. DD) |
| Start / End | any two dates a month apart |

Click **Create project**. Then open the project and, with the pencil icon in the Projects table (Table view), set the **Office** (any), the **Status** and an **Estimated Cost (SAR)** of `500000`, and save.

- **You should see:** The project is created and opens, or appears at the top of the project list.
- **Write down the project name exactly** — you need it for every later test.

### Test 3.2 — The project appears in the list

- [ ] **Do this:** Go back to the **Projects** list.
- **You should see:** `ZZ TEST PROJECT ALPHA` in the list, showing its code, status and customer.

### Test 3.3 — Renaming works

- [ ] **Do this:** Open the project, use the **Rename project** box, change the title to `ZZ TEST PROJECT ALPHA (renamed)`, click **Save title**. Then change it back.
- **You should see:** The title updates in the list both times.

---

## Part 4 — Folder automation (the important one)

When a project is created, the portal is supposed to build a **fixed folder structure** underneath it automatically. This is the heart of the system — test it carefully.

### Test 4.1 — The folder tree was created automatically

- [ ] **Do this:** Left menu → **Files**. Choose `ZZ TEST PROJECT ALPHA` from the project selector.
- **You should see** six top-level folders, in this order:

```
01-DOCUMENTS
02-CONCEPT
03-BALADIYA
04-WORKGDRAWINGS
05-SUPERVISION
06-CLIENT SUBMITTAL
```

All six can be opened with their arrow; `06-CLIENT SUBMITTAL` now holds two folders (see 4.2).

- **If you see this instead:** An empty area, or only some folders → **failure.**

### Test 4.2 — Sub-folders are correct

- [ ] **Do this:** Click into `01-DOCUMENTS`.
- **You should see:**

```
01-CLIENT DATA
02-LOCATION
03-BUILDING SYSTEM
04-DRAWINGS
05-CONSTRUCTION PERMIT
06-SITE PICTURE
```

- [ ] **Do this:** Click into `01-CLIENT DATA`.
- **You should see:**

```
01-BUSINESS CARD
02-TITLE DEED
03-ID
04-MASTER PLAN
05-AUTHORIZATION LTR
06-OTHERS
```

- [ ] **Do this:** Go back and click into `02-CONCEPT` → `01-CONCEPT STUDIES`.
- **You should see:** Nine folders, `01-ARCHITECTURE` through `09-PROJECT RENDERS`.
- [ ] **Do this:** Go back and click into `06-CLIENT SUBMITTAL`.
- **You should see:** Exactly two folders, `Incoming` and `Outgoing`. (They are written with a capital first letter only; that is correct.)

> The complete template is **69 folder paths** (93 folders in all, because the parent folders are created too). You do not need to count them all — checking the levels above proves the automation works.

### Test 4.3 — Every new project gets the same structure

This proves it is automatic, not a one-off.

- [ ] **Do this:** Create a second project called `ZZ TEST PROJECT BETA`, code `ZZ-002`, same customer. Go to Files and select it.
- **You should see:** The identical six top-level folders, and `Incoming` and `Outgoing` inside `06-CLIENT SUBMITTAL`.
- **If you see this instead:** Empty, or different folders → **failure.**

### Test 4.4 — Renaming a folder

There is no button to create a single folder by hand; new folders come from the company template (File tools) and apply to *new* projects only. What you can do in a project is rename a folder.

- [ ] **Do this:** In `ZZ TEST PROJECT ALPHA`, use the **Rename** button on the `03-BALADIYA` folder card and rename it to `03-BALADIYA RENAMED`. Open it.
- **You should see:** The new name appears, and the three folders that were inside it are still inside it.
- [ ] **Do this:** Rename it back to `03-BALADIYA`.
- **You should see:** The original name is back.

### Test 4.5 — A bad folder name is refused

- [ ] **Do this:** Try to rename `05-SUPERVISION` to `05-SUPERVISION/EXTRA` (with a slash).
- **You should see:** It is refused with a message about not using slashes.
- **If you see this instead:** It accepts the slash → report it.

---

## Part 5 — Uploading files

### Test 5.1 — Upload one file into the right folder

- [ ] **Do this:**
  1. Files → `ZZ TEST PROJECT ALPHA`.
  2. Click into `01-DOCUMENTS` → `01-CLIENT DATA` → `02-TITLE DEED`.
  3. Upload `test-plan.pdf`.
- **You should see:** The file appears **inside `02-TITLE DEED`**, not at the top level.
- **If you see this instead:** The file lands in the project root or another folder → **failure**, note which folder it went to.

### Test 5.2 — The "Private upload" tick box is ON by default

**This is a security setting. Check it carefully.**

- [ ] **Do this:** Start another upload. Look at the **Private upload** checkbox before you confirm.
- **You should see:** It is **already ticked**.
- **If you see this instead:** It is unticked → **failure, report immediately.** Files uploaded with it unticked can be downloaded by anyone on the internet who knows the file name.

### Test 5.3 — File type tagging

- [ ] **Do this:** Upload `test-drawing.dwg`. Watch the file-type field in the confirmation box.
- **You should see:** It pre-selects a sensible type (AutoCAD) based on the `.dwg` extension. You can change it before confirming.

### Test 5.4 — Upload several files at once

- [ ] **Do this:** Select `test-plan.pdf`, `test-photo.jpg` and `test-drawing.dwg` together and upload them into `01-DOCUMENTS/06-SITE PICTURE`.
- **You should see:** All three appear in that folder, and a message confirming 3 files.

### Test 5.5 — Downloading works

- [ ] **Do this:** Click a file you uploaded and download it.
- **You should see:** The correct file downloads and opens normally.

### Test 5.6 — Deleting a file

- [ ] **Do this:** Upload a throwaway file, then delete it.
- **You should see:** It disappears from the list.

---

## Part 6 — ZIP upload and folder upload

### Test 6.1 — Upload a ZIP

- [ ] **Do this:** Files → `ZZ TEST PROJECT ALPHA` → click into `02-CONCEPT` → `02-SKETCH UP`. Upload `test-bundle.zip` using the ZIP upload option.
- **You should see:** The files **inside** the ZIP appear as individual files. The ZIP's own internal folder structure is recreated underneath `02-SKETCH UP`.
- **If you see this instead:** The `.zip` file itself is stored as one file → that is a different feature; note it.

### Test 6.2 — Download a whole folder as a ZIP

- [ ] **Do this:** Select several files (tick boxes) → click **Download as ZIP** in the bar that appears.
- **You should see:** A `.zip` downloads and contains the files you picked.
- **If you see this instead:** Nothing happens, or an error appears → **failure.** (This was broken before and was fixed — worth confirming.)

---

## Part 7 — Routing rules (automatic filing)

Routing rules move or copy files automatically based on where they were uploaded.

### Test 7.1 — Only the right people can see the rules

- [ ] **Do this:** Log in as **user C (Team Member)**. Look at the left menu under **Files**.
- **You should see:** **No** "Routing rules" or "File tools" entry.
- [ ] **Do this:** Now as **user B (Department Admin, no Auditor role)**, look again.
- **You should see:** "Routing rules" is present; "File tools" is **not**.
- [ ] **Do this:** Now as **user A (Super Admin)**, look again.
- **You should see:** "Routing rules" and "File tools" are both present.

### Test 7.2 — Create a rule

- [ ] **Do this:** As user A → **Routing rules** → New rule:

| Field | Value |
|---|---|
| Rule name | `ZZ Test Rule` |
| Enabled | ticked |
| Rule type | `Cross-route` |
| Source folder pattern | `06-SITE PICTURE` |
| Source match mode | `contains` |
| Target folder pattern | `04-DRAWINGS` |
| Target match mode | `contains` |

Save.

- **You should see:** The rule appears in the rules list.

### Test 7.3 — The rule actually fires

- [ ] **Do this:** Upload `test-photo.jpg` into `01-DOCUMENTS/06-SITE PICTURE`.
- **You should see:** Depending on rule type, a copy also appears in `01-DOCUMENTS/04-DRAWINGS`.
- **If you see this instead:** Nothing happens → check the rule is Enabled and the patterns match the folder names exactly.

### Test 7.4 — Disable the rule

- [ ] **Do this:** Untick Enabled on `ZZ Test Rule`, save, upload another photo to the same place.
- **You should see:** No copy is made this time.

---

## Part 8 — Inviting a Client Customer

This is how a client gets their own login to see only their own projects.

### Test 8.1 — Create the Client Customer login

- [ ] **Do this:**
  1. Log in as **user A (Super Admin)**.
  2. Open `ZZ TEST PROJECT ALPHA`.
  3. Scroll to the panel headed **Client Customer logins** (it appears once the project has a Customer).
  4. Click **Invite new user**. In the window **Invite a Client Customer** type email `test.client@ata-test.local` and full name `Test Client User`. Leave **Send a welcome email** ticked and the password empty. Click **Create & send invite**.
- **You should see:** A green message "Created test.client@ata-test.local and linked them to this customer." (followed by "An invite email is on its way." when outgoing email is set up; if it is not, an amber line says the invite email could not be sent, and the login is still created), and the person listed under **People with access**.
- **Note:** With the welcome email ticked the password box is optional: the client is emailed a link to set their own password and then lands in the portal. Ask the administrator to set a password manually for testing (the **Reset password** button next to the person), and record it as **user E**.

### Test 8.2 — The Client Customer can log in

- [ ] **Do this:** In a fresh private window, log in as **user E**.
- **You should see:** The portal opens, on the Projects page.

### Test 8.3 — A Client Customer sees ONLY their own projects

**This is the most important test in the whole guide.**

- [ ] **Do this:** As user E, go to **Projects**.
- **You should see:** Only projects belonging to `ATA Test Client One` — that is `ZZ TEST PROJECT ALPHA`, `ZZ TEST PROJECT BETA` and `ZZ TEST CUSTOMER SETUP` (the project from Test 2.1 is linked to the same customer). **No other client's projects at all.**
- **If you see this instead:** Any project belonging to another customer → **critical failure, stop and report immediately.**

### Test 8.4 — The Client Customer menu is reduced

- [ ] **Do this:** As user E, look at the left menu.
- **You should see:** Only Projects, Files, File Browser, Shared and Profile.
- **You should NOT see:** Dashboard, Org Chart, Teams, Contracts, Gantt Chart, Tasks, Daily Task, Kanban, Calendar, ATA AI CHAT, Shares, Routing rules, File tools, Admin.
- **If you see this instead:** Any of those appear → report it.

### Test 8.5 — A Client Customer can upload only into Outgoing

- [ ] **Do this:** As user E, open Files for `ZZ TEST PROJECT ALPHA`. Look for any upload button or drop area, then find the card **Send files to ATA** and use **Choose files** to send `test-plan.pdf`.
- **You should see:** There is no "Upload to", "Upload files" or "Upload ZIP" button and no drop area. Only the **Send files to ATA** card is offered, and the file lands in `06-CLIENT SUBMITTAL/Outgoing` (see Part 20).
- **If you see this instead:** The client can choose any folder, or can upload anywhere else → **failure, report it.**

### Test 8.6 — A Client Customer cannot see money

- [ ] **Do this:** As user E, open `ZZ TEST PROJECT ALPHA` and look for the estimated cost / value.
- **You should see:** No value shown anywhere.
- **If you see this instead:** `500000` is visible → **failure, report it.**

### Test 8.7 — A Client Customer cannot create projects

- [ ] **Do this:** As user E, go to Projects and look for a New Project button (also in the top bar).
- **You should see:** No button, whatever the "Allow any portal user to create projects" setting says.

---

## Part 9 — Team Member restriction (internal staff)

### Test 9.1 — A staff member with no project sees nothing

- [ ] **Do this:** Log in as **user C (Team Member)** — who has not been added to any project yet. Go to **Projects**.
- **You should see:** An empty list.
- **If you see this instead:** Any projects appear → **failure, report it.**

### Test 9.2 — Add the staff member to one project

- [ ] **Do this:** As **user A**, open `ZZ TEST PROJECT ALPHA` → **Team** card → in the search box type user C's email and click user C.
- **You should see:** A green "Added to the team." at once (there is no Save button), and user C listed in the team with their email.

### Test 9.3 — They now see exactly one project

- [ ] **Do this:** As **user C**, refresh and go to Projects.
- **You should see:** **Only** `ZZ TEST PROJECT ALPHA`. Not BETA. Not anything else.
- **If you see this instead:** BETA also appears → **failure, report it.**

### Test 9.4 — They can work on it, but not see money or manage the team

- [ ] **Do this:** As user C, open `ZZ TEST PROJECT ALPHA`. Look at the Actions column on the Projects table, the **Rename project** box, and the **Team** card.
- **You should see:** The edit (pencil), delete (bin) and manage-members icons on the project's row, and the **Rename project** box on the project page — a Team Member works on the projects they are on. The **Team** card says "View only. A Team Lead, Department Admin or Super Admin adds people to a project." and offers no add box and no **Remove** link.
- **If you see this instead:** User C can add or remove people on the team (without being the Lead Architect) → **failure, report it.**

### Test 9.5 — They cannot see the money

- [ ] **Do this:** As user C, look for the project value (the **Estimated cost** tile on the project page, and a **Lead Architect** column on the Projects table).
- **You should see:** No value, no tile and no column.

### Test 9.6 — Removing them takes access away

- [ ] **Do this:** As user A, open the project, find user C in the **Team** card and click **Remove** beside them (confirm the pop-up). As user C, refresh Projects.
- **You should see:** The list is empty again.
- **If you see this instead:** They still see it → **failure, report it.**

---

## Part 10 — The Department Admin view

### Test 10.1 — A Department Admin sees their team's projects and the no-team projects

- [ ] **Do this:** Log in as **user B (Department Admin of TEAM-1)** → Projects.
- **You should see:** `ZZ TEST PROJECT ALPHA` (B is its Lead Architect) and `ZZ TEST PROJECT BETA` (it belongs to no team), plus any other project of TEAM-1 or of no team. **No project that belongs only to TEAM-2** (Part 16 checks that in detail).

### Test 10.2 — But only sees money for their own projects

This is the subtle one. User B was set as **Lead Architect** on ALPHA only (Test 3.1).

- [ ] **Do this:** As user B, open ALPHA and BETA and read the **Estimated cost** tile on each.
- **You should see:** A value shown for `ZZ TEST PROJECT ALPHA` (SAR 500,000), and **no value** (a dash) for `ZZ TEST PROJECT BETA` or any project they do not lead.
- **If you see this instead:** Values shown for every project → **failure, report it.**

### Test 10.3 — Same rule on the project detail page

- [ ] **Do this:** As user B, open `ZZ TEST PROJECT BETA` and look for the value.
- **You should see:** No value.
- **If you see this instead:** The value appears → **failure, report it.**

### Test 10.4 — Menu items by role

- [ ] **Do this:** As user B, check the left menu.
- **You should see:** Dashboard, Org Chart, Teams and Contracts are all present.
- [ ] **Do this:** As user F (Team Lead), check the same.
- **You should see:** **Org Chart** is present. Dashboard, Teams and Contracts are **not**.
- [ ] **Do this:** As user C (Team Member), check the same.
- **You should NOT see:** Dashboard, Org Chart, Teams, Contracts.

### Test 10.5 — A Department Admin can edit projects

- [ ] **Do this:** As user B, open `ZZ TEST PROJECT ALPHA`, change the phase, save.
- **You should see:** It saves successfully.

### Test 10.6 — A Department Admin cannot hand themselves a project

- [ ] **Do this:** As user A, set the Lead Architect of `ZZ TEST PROJECT BETA` to user A. Then as user B, open BETA and try to set **Lead Architect** to themselves.
- **You should see:** A message saying "Ask a Super Admin to make you the Lead Architect of a project somebody else leads."
- **If you see this instead:** It saves, and BETA's value becomes visible to them → **failure, report it.**
- (Put BETA's Lead Architect back to blank afterwards.)

---

## Part 11 — Sharing files

### Test 11.1 — Share a folder with a colleague

- [ ] **Do this:** As user A, add user C back to ALPHA's team. Then in Files, share the folder `01-DOCUMENTS` with **user D** (`test.staff2@ata-test.local`), expiry 30 days.
- **You should see:** A confirmation that the folder is shared.

### Test 11.2 — The recipient can see it

- [ ] **Do this:** Log in as **user D** → left menu → **Shared**.
- **You should see:** The shared folder and the files inside it. (User D is not on ALPHA, so ALPHA appears only here, not in D's Projects list.)

### Test 11.3 — Create a public share link

- [ ] **Do this:** As user A, create a **share link** for `01-DOCUMENTS` on ALPHA. Copy the link.
- **You should see:** A long web address containing a token.

### Test 11.4 — The link works without logging in

- [ ] **Do this:** Paste that link into a **private browser window** where you are not logged in.
- **You should see:** A simple page listing the files in that folder, each downloadable.
- **If you see this instead:** "Invalid share token" → note it and report.

### Test 11.5 — A tampered link is refused

- [ ] **Do this:** Take the same link and change a few characters in the middle of the token. Open it.
- **You should see:** An error saying the token or signature is invalid.
- **If you see this instead:** It still shows the files → **critical failure, report immediately.**

### Test 11.6 — Revoking the link kills it immediately

- [ ] **Do this:** As user A → **Shares** in the left menu → find the link you made → **Revoke**. Now reload the share link in the private window.
- **You should see:** A message that the link has been revoked or expired.
- **If you see this instead:** The files still load → **critical failure, report immediately.**

---

## Part 12 — Tasks, planning and views

### Test 12.1 — Create a task

- [ ] **Do this:** As user A → **Tasks** → create a task on `ZZ TEST PROJECT ALPHA`: subject `ZZ Test Task 1`, priority Medium, an end date next week.
- **You should see:** It appears in the task list under that project.

### Test 12.2 — Assign it

- [ ] **Do this:** Assign the task to user C.
- **You should see:** User C's name against the task.

### Test 12.3 — Task comments

- [ ] **Do this:** Open the task, add a comment `Testing comment`.
- **You should see:** The comment appears with your name and the time.

### Test 12.4 — Kanban

- [ ] **Do this:** Left menu → **Kanban**. Drag `ZZ TEST PROJECT ALPHA` from one column to another.
- **You should see:** The card moves and stays after a page refresh.

### Test 12.5 — Gantt chart

- [ ] **Do this:** Left menu → **Gantt Chart**.
- **You should see:** Your test projects drawn as bars across the dates you set.

### Test 12.6 — Calendar

- [ ] **Do this:** Left menu → **Calendar**.
- **You should see:** Project dates and task deadlines on the calendar.

### Test 12.7 — Daily Task

- [ ] **Do this:** Left menu → **Daily Task**. Add a personal reminder for today.
- **You should see:** It appears on today's date.
- [ ] **Do this:** Log in as user C and check their Daily Task board.
- **You should NOT see:** User A's personal reminder. These are private per person.
- **If you see this instead:** They can see it → **failure, report it.**

### Test 12.8 — Teams and Org Chart

- [ ] **Do this:** As user A → **Teams**, then **Org Chart**.
- **You should see:** Teams with their members, and an Org Chart showing the whole organisation: a **Super Admins** group, each team with its people and their roles, and **Not in a team yet**. (What you can *do* in the Org Chart is tested in Part 17.)

---

## Part 13 — Dashboard

### Test 13.1 — Dashboard loads with real numbers

- [ ] **Do this:** As user A → **Dashboard**.
- **You should see:** Counts of projects and tasks, budget/health figures, recent activity — all reflecting your test data.

### Test 13.2 — The AI Chat page opens

- [ ] **Do this:** Left menu → **ATA AI CHAT**.
- **You should see:** A chat box. Type `how many projects` and send.
- **You should see:** A sensible answer with a project count.
- **If you see this instead:** A blank page, or "Sorry, I couldn't process that request" every time → **failure, report it.** (This feature was completely broken before and was fixed.)

### Test 13.3 — AI Chat respects permissions

- [ ] **Do this:** As **user C** (who is on one project only), open AI Chat and ask `how many projects`.
- **You should see:** A count of **1**, not the total number of projects on the system.
- **If you see this instead:** It reports every project → **failure, report it.**
- [ ] **Do this:** As **user E** (Client Customer), look for ATA AI CHAT in the menu and type `/portal-app/ai-chat` into the address bar.
- **You should see:** No menu entry, and the address sends you to the Projects page. A client has no AI chat.

---

## Part 14 — Security checks (do not skip)

These confirm the security repairs are live. They take five minutes and are the most valuable tests here.

### Test 14.1 — Uploaded files are NOT public

- [ ] **Do this:**
  1. As user A, upload `test-plan.pdf` to any folder in ALPHA.
  2. Click the file and copy its download web address.
  3. Look at the address. It should contain `/private/files/`.
  4. Paste that address into a **private browser window where you are not logged in**.
- **You should see:** "Not permitted", a login prompt, or error **403**.
- **If you see this instead:** The PDF downloads → **critical failure, stop and report immediately.**

### Test 14.2 — Dangerous file types are refused

- [ ] **Do this:** Try to upload `test-bad.html`.
- **You should see:** A message that this file type cannot be uploaded.
- [ ] **Do this:** Try the same with a file renamed to `.svg`.
- **You should see:** The same refusal.
- **If you see this instead:** They upload successfully → **failure, report it.**

### Test 14.3 — Staff directory is not open to everyone

- [ ] **Do this:** As **user E (Client Customer)**, open the browser address bar and go to:
  `https://ata.enfonoerp.com/api/method/portal_app.api.teams.get_teams`
- **You should see:** An empty list (nothing between the square brackets) or a permission error.
- **If you see this instead:** A long list of staff names and email addresses → **critical failure, report immediately.**

### Test 14.4 — The user list is not open to everyone

- [ ] **Do this:** As **user E**, go to:
  `https://ata.enfonoerp.com/api/method/portal_app.api.projects.get_portal_users`
- **You should see:** A permission error or an empty list.
- **If you see this instead:** Every user's email address → **critical failure, report immediately.**

### Test 14.5 — Demo accounts must not exist

- [ ] **Do this:** Ask the administrator to confirm that these accounts are **disabled or deleted**:

```
portal.manager@demo.local
portal.pm@demo.local
portal.member1@demo.local
portal.member2@demo.local
portal.client@demo.local
```

- **Why:** These were created by the demo data tool with a password that is published publicly. `portal.manager@demo.local` has manager-level access to every project.
- **This must be done before the client is given the system.**

---

## Part 15 — Desk (back office) checks

### Test 15.1 — The app appears in the ERPNext desk

- [ ] **Do this:** Go to `https://ata.enfonoerp.com/app`. Log in as user A.
- **You should see:** A **Project Portal** entry in the sidebar / apps screen.

### Test 15.2 — The workspace opens

- [ ] **Do this:** Click **Project Portal**.
- **You should see:** Shortcut cards (Open Portal, Project, Task, Portal Project Settings) and grouped links (Portal Setup, Files & Sharing, Projects).

### Test 15.3 — The "Open Portal" shortcut works

- [ ] **Do this:** Click **Open Portal**.
- **You should see:** The portal SPA opens.

---

## Part 16 — Who sees which projects (the five roles)

This part proves the central rule of the role model with five projects that sit in different places. The tests only look; they change very little.

### 16.0 Prepare these once

Ask the administrator (or do it yourself as user A) to set up five projects, each with a Start and End date:

| Project | Where it sits |
|---|---|
| `ZZ P-T1` | **Portal Team** = TEAM-1; user C on its Team card |
| `ZZ P-T2` | **Portal Team** = TEAM-2; user D on its Team card |
| `ZZ P-NONE` | no Portal Team; nobody on its Team card |
| `ZZ P-OUTSIDE` | no Portal Team; the only person on its Team card is user G, who is in **no** team |
| `ZZ P-CLIENT` | no Portal Team; nobody on its Team card; its Customer is `ATA Test Client One` |

(The Portal Team is set on the project page, in the card **Portal Team (Gantt grouping)**. A project created in the portal puts its creator on the Team card automatically; that is fine for user A, who is in no team, so "nobody on its Team card" means nobody from a team.) Make the data look like production: real projects are often staffed by someone who is in no team, and that is what `ZZ P-OUTSIDE` stands for. If you ran earlier parts first, users C and D may still be on other projects; ignore every project that is not one of these five.

What each person should see of the five:

| Project | A | B | F | C | D | G | E |
|---|---|---|---|---|---|---|---|
| `ZZ P-T1` | yes | yes | yes | yes | no | no | no |
| `ZZ P-T2` | yes | no | no | no | yes | no | no |
| `ZZ P-NONE` | yes | yes | no | no | no | no | no |
| `ZZ P-OUTSIDE` | yes | yes | no | no | no | yes | no |
| `ZZ P-CLIENT` | yes | yes | no | no | no | no | yes |

### Test 16.1 — A Super Admin sees every project

- [ ] **Do this:** Log in as **user A** → Projects. Search each of the five names. Compare the second number in the grey chip ("N of M projects") with the number of Projects in the ERPNext desk.
- **You should see:** All five listed, and M equal to the total number of projects.
- **If you see this instead:** Any project missing → **failure, report it.**

### Test 16.2 — A Department Admin sees their team's projects and the no-team projects, nothing from another team

- [ ] **Do this:** Log in as **user B** → Projects. Search each of the five names. Then type the address of `ZZ P-T2` (`/portal-app/projects/<its PROJ-xxxx ID>`).
- **You should see:** `ZZ P-T1`, `ZZ P-NONE`, `ZZ P-OUTSIDE` and `ZZ P-CLIENT` listed; **not** `ZZ P-T2`, and its address shows only a "Back to projects" link.
- **If you see this instead:** `ZZ P-T2` is visible → **failure** (another team's project). A missing `ZZ P-OUTSIDE` means the Department Admin has lost part of the portfolio → **failure.**

### Test 16.3 — A Team Lead sees only their team's projects

- [ ] **Do this:** Log in as **user F** → Projects. Search each of the five names.
- **You should see:** Only `ZZ P-T1`.
- **If you see this instead:** Any no-team project, or `ZZ P-T2` → **failure, report it.**

### Test 16.4 — A Team Member sees only their own projects, even when in no team

- [ ] **Do this:** Log in as **user C**, then **user D**, then **user G** and search the five names each time.
- **You should see:** C sees only `ZZ P-T1`; D only `ZZ P-T2`; G only `ZZ P-OUTSIDE`.
- **If you see this instead:** A project the person is not on is visible, or G sees nothing → **failure.**

### Test 16.5 — A Client Customer sees only their customer's projects

- [ ] **Do this:** Log in as **user E** → Projects and the Files project selector. Search the five names.
- **You should see:** Of the five, only `ZZ P-CLIENT`.
- **If you see this instead:** Any other of the five → **critical failure, report immediately.**

### Test 16.6 — The same list appears on every page

- [ ] **Do this:** As **user B**, then **user F**, open Projects, Kanban, Gantt Chart, Calendar, Files (project selector), File Browser and the top search box, and write down which of the five appear on each.
- **You should see:** On every page exactly the projects of the table above (B: four projects; F: only `ZZ P-T1`).
- **If you see this instead:** A project hidden from the Projects list shows up elsewhere → **failure, report it.**

### Test 16.7 — Project money by role

- [ ] **Do this:** As user A set `ZZ P-T1` to Lead Architect user B with an Estimated Cost of `500000`, and `ZZ P-NONE` to Lead Architect user A with `300000` (pencil icon in the Projects table). Then open `ZZ P-T1` as users A, B, F and C, and `ZZ P-NONE` as users A and B, and read the **Estimated cost** tile each time.
- **You should see:** A: "SAR 500,000" on `ZZ P-T1` and "SAR 300,000" on `ZZ P-NONE`. B: "SAR 500,000" on `ZZ P-T1` and only a dash on `ZZ P-NONE`. F and C: no Estimated cost tile at all, and no Lead Architect column in the Projects table.
- **If you see this instead:** B sees a number on `ZZ P-NONE`, or F or C sees any money → **critical failure, report immediately.**

### Test 16.8 — Putting a project under a team moves it out of the no-team pile

- [ ] **Do this:** As user A, open `ZZ P-NONE`, and in **Portal Team (Gantt grouping)** pick TEAM-2. Check user B's Projects list. Then click **Clear team** and check again.
- **You should see:** While under TEAM-2 user B cannot see it; after "Team cleared." it is back in B's list.

### Test 16.9 — The New Project button in the top bar

- [ ] **Do this:** Ask the administrator whether "Allow any portal user to create projects" is ticked (default: yes). Look at the top bar for an amber **New Project** button as users A, B, F, C and E.
- **You should see:** A and B always; E never; F and C only while the setting is ticked.

---

## Part 17 — The Org Chart

The Org Chart is now where people are organised. Most tests change a role and **put it back**; do the "put it back" steps.

### Test 17.1 — Who can open it

- [ ] **Do this:** Look for **Org Chart** in the menu and open `/portal-app/org-chart` as users A, B, F, C and E.
- **You should see:** It opens for A, B and F (the line under the title says "You are Super Admin / Department Admin / Team Lead"). For C and E there is no menu entry and the address sends them to Projects.
- **If you see this instead:** C or E can open it → **failure, report it.**

### Test 17.2 — What a Team Lead can do

- [ ] **Do this:** As user F open the Org Chart and click a person.
- **You should see:** The note "As a Team Lead you can click anyone to assign them to your team's projects."; a small "Your team" badge on TEAM-1; and for a person only the button **Assign to project…** — no "Role in…" box, no **Reset password…**, no **Remove from team**.

### Test 17.3 — A Super Admin changes a role; there is one Team Lead per team

- [ ] **Do this:** As user A click user D in TEAM-2, set **Role in TEAM-2** to **Team Lead**, click **Save**. Then in TEAM-1 click user C and make user C the Team Lead.
- **You should see:** "…is now Team Lead of TEAM-2." User D then has an Org Chart menu entry. In TEAM-1 exactly **one** person carries the Team Lead tag: user C; user F is now a Team Member.
- [ ] **Put it back:** Set user D to Team Member and user F back to Team Lead (and C to Team Member).

### Test 17.4 — A Department Admin changes roles only in their own team

- [ ] **Do this:** As user B click user C in TEAM-1 and open **Role in TEAM-1**. Then open TEAM-2 and click user D.
- **You should see:** The box offers only **Team Member** and **Team Lead** (never Department Admin). TEAM-2 has no pencil and user D has no role box, no Remove and no Reset password.
- **If you see this instead:** User B can change TEAM-2 → **failure, report it.**

### Test 17.5 — A Department Admin cannot touch a Department Admin or a Super Admin

- [ ] **Do this:** As user A make user C a Department Admin of TEAM-1. As user B click user C and then user A (in the Super Admins group).
- **You should see:** No role box, no Remove, no Reset password and no Make Super Admin; for user C the text "Only a Super Admin can change a Department Admin."
- [ ] **Put it back:** As user A set user C to Team Member.

### Test 17.6 — Remove from team, remove as Team Lead, add an unassigned person

- [ ] **Do this:** As user B: in **Not in a team yet** click user G → **Add to a team** → TEAM-1 → **Add**. Then click user G → **Remove from team** → OK. Then click user F → **Remove as Team Lead** → OK; set user F back to Team Lead.
- **You should see:** The add box offers only TEAM-1. User G joins TEAM-1 as a Team Member, then is back in "Not in a team yet" (still on `ZZ P-OUTSIDE`). After "Remove as Team Lead" user F stays in the team as a Team Member and loses the Org Chart menu entry.

### Test 17.7 — Assign people to projects

- [ ] **Do this:** As user F click user D → **Assign to project…**, tick `ZZ P-T1` → **Add to 1 project**. As user B do the same for two projects. Clean up by removing user D from those projects (Part 18).
- **You should see:** F is offered only `ZZ P-T1` (not `ZZ P-T2` or the no-team projects). The green line reads "… was added to 1 project." (or "2 projects") and the person now sees those projects.

### Test 17.8 — Super Admin on and off

- [ ] **Do this:** As user A click user D → **Make Super Admin** → OK. Look at user D's portal. Then click user D in **Super Admins** → **Remove Super Admin access** → OK. Click your own name in Super Admins.
- **You should see:** "… is now a Super Admin." — user D sees the Dashboard, every project and the Create portal user panel. After removal user D is a Team Member again. On your own name there is no Make / Remove button (a Super Admin cannot change their own role). User B is never offered Make Super Admin. (Removing the very last Super Admin is refused: "This is the last Super Admin. Make someone else a Super Admin first." — reachable only as the built-in Administrator.)

---

## Part 18 — The project Team card

### Test 18.1 — People are added at once

- [ ] **Do this:** As user A open `ZZ P-NONE` → **Team** card. Type user G's email in the search box and click user G. Then as user B use **Add from org chart**, tick user C and user D and click **Add 2 to the team**.
- **You should see:** "Added to the team." and, for the second, "2 people added to the team." No **Save team** button exists. The people appear with name and email.

### Test 18.2 — Remove is for Super Admins and Department Admins only

- [ ] **Do this:** As user A and as user B open `ZZ P-NONE` and click **Remove** beside user D and user C (confirm). As user F open `ZZ P-T1` and add user D by search; look for **Remove**.
- **You should see:** A and B see **Remove**; the line reads "Removed from the team." F can add ("You can add people to this project. Only a Super Admin or a Department Admin can remove them.") but has **no Remove** link. (Clean up: remove user D from `ZZ P-T1` as user A.)

### Test 18.3 — A Team Member can only look, unless they are the Lead Architect

- [ ] **Do this:** As user C open `ZZ P-T1`. Then as user A make user C the Lead Architect of it and look again as user C. Put the Lead Architect back to user B.
- **You should see:** First "View only. A Team Lead, Department Admin or Super Admin adds people to a project." with no add box; then an add box and the line about adding but not removing, with no Add from org chart and no Remove.

### Test 18.4 — A client can never be put on a team

- [ ] **Do this:** As user A open `ZZ P-NONE` → Team card and type user E's email in the search box; then open **Add from org chart** and search for user E.
- **You should see:** User E is not offered anywhere.
- **If you see this instead:** A client can be picked → **critical failure, report immediately.**
- (Clean up: remove user G from `ZZ P-NONE`.)

---

## Part 19 — Passwords

Needs working outgoing email, a staff login (use user G) and a client login whose email addresses you can read. Write real passwords on paper only.

### Test 19.1 — A known and an unknown address get the same answer

- [ ] **Do this:** Login page → **Forgot Password?** → type user G's email → **Send reset link**. Click **Back to sign in** and repeat with `nobody-here@ata-test.local`. Then once more with the Email box empty.
- **You should see:** Both addresses show the same green message: "If that address belongs to a portal login, a reset link is on its way." For the empty box a red message appears in the bottom-right corner: "Enter the email address of your account." Only user G's mailbox gets a "Password Reset" mail.
- **If you see this instead:** Any difference between known and unknown addresses (for example "user not found") → **failure, report it.**

### Test 19.2 — The reset link works, and a client lands on the portal

- [ ] **Do this:** Click the link in user G's mail, choose a new password and save; sign in with it (the old one must be refused; the link must not work twice). Repeat the whole flow for the client login.
- **You should see:** The staff login works with the new password. The client lands back **on the portal** (the Projects page), not on ERPNext's "My Account" page.

### Test 19.3 — Reset from the Org Chart by email

- [ ] **Do this:** As user B open the Org Chart → user C → **Reset password…**. As user A do the same for user D.
- **You should see:** User B is offered only "Email them a reset link" and gets "A reset link is on its way to <email>."; user A is offered "Email them a reset link" and "Set a password now".

### Test 19.4 — A Super Admin sets a password; a Department Admin cannot

- [ ] **Do this:** Keep user C signed in somewhere. As user A choose **Set a password now** for user C with a 5-letter word, then with a proper password. As user B look for **Reset password…** on user A, on a second Department Admin, on user D (another team) and on user B's own row.
- **You should see:** "Use at least 8 characters." for the short one; then "The password was changed and they were signed out everywhere." — user C's open page falls back to the sign-in page. User B has **no** Reset password button on any of those four rows.
- **If you see this instead:** B can reset a Super Admin → **critical failure, report immediately.**

### Test 19.5 — The Admin page reset tool

- [ ] **Do this:** As user A open Admin → **Reset a password**, search a person and send a reset link. As user B open Admin.
- **You should see:** A: the person list includes clients and both choices are offered. B: only the **Reset a password** card (no Create portal user), only people B may reset, and only the email choice.

### Test 19.6 — Change your own password from Profile

- [ ] **Do this:** As user G open Profile → **Password**. Try, one after the other: a wrong current password with the same proper new password (8 or more characters) typed twice; the right current password with two different new passwords; a 5-letter new password typed twice; and finally a proper new password typed twice.
- **You should see:** "Your current password is not correct.", "The two new passwords do not match.", "Your new password must be at least 8 characters long.", then "Password changed. Any other devices you were signed in on have been signed out."

### Test 19.7 — Repeated requests are rate limited (do this last)

- [ ] **Do this:** Request a reset link six times within an hour from the same network (every press counts).
- **You should see:** The sixth is refused with a red message; no further mail is sent. (This blocks the form for your network for up to an hour.)

---

## Part 20 — The client folder: Incoming and Outgoing

### Test 20.1 — New projects have both folders

- [ ] **Do this:** As user A create `ZZ CLIENT FOLDER TEST` (Customer `ATA Test Client One`), open it in Files and open `06-CLIENT SUBMITTAL`.
- **You should see:** Exactly `Incoming` (tag "Sent to client") and `Outgoing` (tag "From client").

### Test 20.2 — Submit to Client lands in Incoming

- [ ] **Do this:** Upload `test-plan.pdf` and `test-photo.jpg` into the project, then in the **File Browser** click **Submit** on a row and **Confirm & Submit to Client**, close the dialog with **Cancel**, and do the same for the other file.
- **You should see:** "Submitted as "01_<today>_<file name>" (SL 1) to the client's Incoming folder.", then `02_…` (SL 2). Both copies sit in `06-CLIENT SUBMITTAL/Incoming`; the originals are untouched.

### Test 20.3 — A client reads both folders and nothing else

- [ ] **Do this:** As user E open the project in Files and in the File Browser.
- **You should see:** Only `06-CLIENT SUBMITTAL`, `Incoming` (tag "From ATA") and `Outgoing` (tag "Your uploads"). The files ATA submitted open normally. No Rename, Share or Submit buttons, and nothing from the other folders.
- **If you see this instead:** Anything outside `06-CLIENT SUBMITTAL` → **critical failure, report immediately.**

### Test 20.4 — A client uploads only into Outgoing

- [ ] **Do this:** As user E use **Send files to ATA** → **Choose files** to send `test-plan.pdf`; then try `test-bad.html`. As user B look in `Outgoing`.
- **You should see:** "Uploaded 1 file to Outgoing. The ATA team sees it marked as from you." The file is in Outgoing with the tag "Your upload" (staff see "From client"). The `.html` file is refused with "This file type cannot be uploaded to the portal:".

### Test 20.5 — A client is refused anywhere else (technical)

- [ ] **Do this:** Ask a developer to resend the upload request with `target_folder` set to the Incoming folder's path, then to the project root and an internal folder.
- **You should see:** Each is refused: "You can upload only into the 06-CLIENT SUBMITTAL/Outgoing folder." and no file is created.

### Test 20.6 — The client folders cannot be renamed; a "06 - CLIENT SUBMITTAL" spelling works the same

- [ ] **Do this:** As user A look for **Rename** on the folder cards of `06-CLIENT SUBMITTAL`, `Incoming`, `Outgoing` and `05-SUPERVISION`. Then open an older project whose client folder is spelled `06 - CLIENT SUBMITTAL` (ask the administrator), submit a file and send one as the client.
- **You should see:** Rename exists only on `05-SUPERVISION`. (A developer rename attempt is refused: "The client folder and its Incoming and Outgoing folders cannot be renamed.") The older project keeps its single client folder, Incoming and Outgoing work inside it and no second client folder appears.

---

## Part 21 — After a migration (administrator)

Run these once, right after the release is deployed with `bench --site <site> migrate`. Practise first on a restored copy. Write down **before** migrating: how many users hold the role **Portal Customer**; every login holding **Projects Manager** who is not a System Manager, and the project count each one sees; one project that has files directly in `06-CLIENT SUBMITTAL`, and who uploaded each.

### Test 21.1 — The client role was renamed, not replaced

- [ ] **Do this:** In the ERPNext desk open the Role list; open an existing client login (user E); sign in as user E.
- **You should see:** A role **Client Customer** (and no Portal Customer) with the same number of users as before; user E still has it, signs in and sees only their customer's projects.
- **If you see this instead:** Clients are refused → **critical failure, report immediately.**

### Test 21.2 — Former Projects Managers are Department Admins of every team

- [ ] **Do this:** In the desk open one former Projects Manager (not a System Manager) and each team's **Portal Department Admins** table. Sign in as that person.
- **You should see:** They now hold **Department Admin**, are listed in **every** team's table, land on the Dashboard and see the **same number of projects as before the migration**. A person who is also a System Manager was not added to any team.
- **If you see this instead:** Fewer projects than before → **failure, report it.**

### Test 21.3 — Every project with a folder tree has Incoming and Outgoing, and loose files were sorted

- [ ] **Do this:** Open Files for three older projects that have a folder tree and for the project that had loose files in `06-CLIENT SUBMITTAL`.
- **You should see:** `Incoming` and `Outgoing` in each. No file is loose in `06-CLIENT SUBMITTAL`; files a client uploaded are in Outgoing, everything else in Incoming. (A project that never had a folder tree is left alone by the migration; it gets the whole standard tree, both folders included, when its tree is first created.)

### Test 21.4 — Running the migration again changes nothing

- [ ] **Do this:** On the test copy run `bench --site <site> migrate` a second time and compare the teams' Department Admin tables, the roles and the folders; check the Error Log for new "Portal:" entries.
- **You should see:** No difference and no new errors.

---

## Part 22 — Clean-up

Once every test above has passed, remove the test data.

- [ ] Delete projects `ZZ TEST PROJECT ALPHA`, `ZZ TEST PROJECT BETA`, `ZZ TEST CUSTOMER SETUP`, `ZZ CLIENT FOLDER TEST` and the five `ZZ P-…` projects (this also removes their folders and files).
- [ ] Delete the routing rule `ZZ Test Rule`.
- [ ] Delete customer `ATA Test Client One`.
- [ ] Put the roles back as they were (the Org Chart tests restore them as they go; check once more) and delete test users A–G, the extra Super Admin or Department Admin you made, and `test.outsider@ata-test.local`.
- [ ] Delete teams TEAM-1 and TEAM-2 if they were made only for this run.
- [ ] Confirm the five `@demo.local` accounts are gone (Test 14.5).
- [ ] Revoke any share links created during Part 11.

---

## Sign-off

| Section | Passed | Tester | Date | Notes |
|---|---|---|---|---|
| 1. Getting in | ☐ | | | |
| 2. Customer creation | ☐ | | | |
| 3. Project creation | ☐ | | | |
| 4. Folder automation | ☐ | | | |
| 5. File upload | ☐ | | | |
| 6. ZIP upload/download | ☐ | | | |
| 7. Routing rules | ☐ | | | |
| 8. Client Customer invitation | ☐ | | | |
| 9. Team Member restriction | ☐ | | | |
| 10. Department Admin view | ☐ | | | |
| 11. Sharing | ☐ | | | |
| 12. Tasks and views | ☐ | | | |
| 13. Dashboard and AI | ☐ | | | |
| 14. Security | ☐ | | | |
| 15. Desk | ☐ | | | |
| 16. Who sees which projects | ☐ | | | |
| 17. Org Chart | ☐ | | | |
| 18. Project Team card | ☐ | | | |
| 19. Passwords | ☐ | | | |
| 20. Client folder | ☐ | | | |
| 21. After a migration | ☐ | | | |
| 22. Clean-up | ☐ | | | |

**Do not hand over to the client until Parts 14, 16, 17 and 20 pass completely and Test 14.5 is confirmed done.**

---

## If something fails

Record: the test number, which user you were logged in as, what you expected, what happened, and the time. The time matters — it lets the developer find the matching entry in the site's Error Log.

The Error Log is at `https://ata.enfonoerp.com/app/error-log` (Super Admin only).
