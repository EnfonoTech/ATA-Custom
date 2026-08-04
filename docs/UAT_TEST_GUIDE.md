# ATA Project Portal — Full Test Guide (Before Client Handover)

**Site:** https://ata.enfonoerp.com
**Portal address staff will use:** https://ata.enfonoerp.com/portal-app
**Version tested:** `bf41e64` (deployed 5 Aug 2026)

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

The portal behaves completely differently depending on the user's role. You must understand this before testing, or the results will look like bugs when they are correct behaviour.

| Role | Which projects they see | Can they edit projects? | Can they see project money? |
|---|---|---|---|
| **System Manager** | Every project on the system | Yes | Yes — every project |
| **Projects Manager** | Every project on the system | Yes | **Only projects where they are named "Portal Project Manager"** |
| **Projects User** | **Only** projects they were added to as a team member | **No — read only** | No |
| **Portal Customer** | Only projects belonging to their linked Customer | No | No |
| **Auditor** | (as per their other roles) | — | No — but can edit the folder template |

Two points people get wrong:

1. A **Projects Manager sees every project**, not just their own. That is intended. What is restricted for them is the **money**, not the list.
2. A **Projects User cannot edit anything**, even a project they are the lead on. They are read-only by design.

### 0.2 Accounts you need before starting

Ask the administrator to create these five test logins. Write the passwords here and keep this sheet safe.

| # | Login email | Role to give | Password |
|---|---|---|---|
| A | `test.sysmgr@ata-test.local` | System Manager | ____________ |
| B | `test.pm@ata-test.local` | Projects Manager | ____________ |
| C | `test.staff@ata-test.local` | Projects User | ____________ |
| D | `test.staff2@ata-test.local` | Projects User | ____________ |
| E | *(created during Test 8)* | Portal Customer | ____________ |

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

- [ ] **Do this:** Log in as **user A (System Manager)**.
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

---

## Part 2 — Creating a customer

### Test 2.1 — Create a customer from inside the portal

- [ ] **Do this:**
  1. Log in as **user A (System Manager)**.
  2. Left menu → **Projects**.
  3. Click **New Project** (the button top-right of the project list).
  4. In the form, find the **Customer** field. Type `ATA Test Client One`.
  5. The field searches as you type. Since no such customer exists, choose the option to **create** it.
- **You should see:** The customer name appears in the field, accepted.

### Test 2.2 — A Projects User cannot create customers

- [ ] **Do this:** Log in as **user C (Projects User)** in a different browser. Go to Projects → try to create a new project and reach the Customer field.
- **You should see:** Either no New Project button at all, or you cannot search/create customers.
- **If you see this instead:** They can create a Customer record → **failure, report it.**

---

## Part 3 — Creating a project

### Test 3.1 — Create the test project

- [ ] **Do this:** As **user A**, go to Projects → **New Project** and fill in:

| Field | Value to type |
|---|---|
| Project name | `ZZ TEST PROJECT ALPHA` |
| Project code | `ZZ-001` |
| Customer | `ATA Test Client One` |
| Portal Project Manager | **user B** (`test.pm@ata-test.local`) |
| Office | pick any (e.g. RIYADH) |
| Phase | pick any (e.g. Schematic Design) |
| Expected start / end date | any two dates a month apart |
| Estimated cost | `500000` |

Click Save / Create.

- **You should see:** The project is created and opens, or appears at the top of the project list.
- **Write down the project name exactly** — you need it for every later test.

### Test 3.2 — The project appears in the list

- [ ] **Do this:** Go back to the **Projects** list.
- **You should see:** `ZZ TEST PROJECT ALPHA` in the list, showing its code, customer, status and value.

### Test 3.3 — Renaming works

- [ ] **Do this:** Open the project, use Edit, change the title to `ZZ TEST PROJECT ALPHA (renamed)`, save. Then change it back.
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

> The complete template is **67 folders**. You do not need to count them all — checking the three levels above proves the automation works.

### Test 4.3 — Every new project gets the same structure

This proves it is automatic, not a one-off.

- [ ] **Do this:** Create a second project called `ZZ TEST PROJECT BETA`, code `ZZ-002`, same customer. Go to Files and select it.
- **You should see:** The identical six top-level folders.
- **If you see this instead:** Empty, or different folders → **failure.**

### Test 4.4 — Creating a folder by hand

- [ ] **Do this:** In `ZZ TEST PROJECT ALPHA`, inside `01-DOCUMENTS`, create a new sub-folder called `99-TEST FOLDER`.
- **You should see:** It appears in the tree immediately.

### Test 4.5 — Renaming a folder

- [ ] **Do this:** Rename `99-TEST FOLDER` to `99-RENAMED`.
- **You should see:** The new name appears.
- [ ] **Do this:** Now try to rename it to `bad/name` (with a slash).
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

- [ ] **Do this:** Select several files (tick boxes) → choose **Download selected as ZIP**.
- **You should see:** A `.zip` downloads and contains the files you picked.
- **If you see this instead:** Nothing happens, or an error appears → **failure.** (This was broken before and was fixed — worth confirming.)

---

## Part 7 — Routing rules (automatic filing)

Routing rules move or copy files automatically based on where they were uploaded.

### Test 7.1 — Only the right people can see the rules

- [ ] **Do this:** Log in as **user C (Projects User)**. Look at the left menu under **Files**.
- **You should see:** **No** "Routing rules" or "File tools" entry.
- [ ] **Do this:** Now as **user A (System Manager)**, look again.
- **You should see:** "Routing rules" and "File tools" are present.

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

## Part 8 — Inviting a customer user

This is how a client gets their own login to see only their own projects.

### Test 8.1 — Create the customer portal user

- [ ] **Do this:**
  1. Log in as **user A (System Manager)**.
  2. Open `ZZ TEST PROJECT ALPHA`.
  3. Find the customer users / client access section.
  4. Add a new customer user: email `test.client@ata-test.local`, full name `Test Client User`.
- **You should see:** The account is created and linked to `ATA Test Client One`.
- **Note:** If no password box appears, that is correct and intended — the system now sends the user a welcome email so they set their own password. Ask the administrator to set a password manually for testing, and record it as **user E**.

### Test 8.2 — The customer user can log in

- [ ] **Do this:** In a fresh private window, log in as **user E**.
- **You should see:** The portal opens.

### Test 8.3 — The customer sees ONLY their own projects

**This is the most important test in the whole guide.**

- [ ] **Do this:** As user E, go to **Projects**.
- **You should see:** Only projects belonging to `ATA Test Client One` — that is `ZZ TEST PROJECT ALPHA` and `ZZ TEST PROJECT BETA`. **No other client's projects at all.**
- **If you see this instead:** Any project belonging to another customer → **critical failure, stop and report immediately.**

### Test 8.4 — The customer menu is reduced

- [ ] **Do this:** As user E, look at the left menu.
- **You should NOT see:** Dashboard, Org Chart, Teams, Contracts, Shares, Routing rules, File tools, Admin.
- **If you see this instead:** Any of those appear → report it.

### Test 8.5 — The customer cannot upload

- [ ] **Do this:** As user E, open Files for `ZZ TEST PROJECT ALPHA` and try to upload a file.
- **You should see:** Either no upload button, or a message saying customer portal users cannot upload files.
- **If you see this instead:** The upload succeeds → **failure, report it.**

### Test 8.6 — The customer cannot see money

- [ ] **Do this:** As user E, open `ZZ TEST PROJECT ALPHA` and look for the estimated cost / value.
- **You should see:** No value shown anywhere.
- **If you see this instead:** `500000` is visible → **failure, report it.**

### Test 8.7 — The customer cannot create projects

- [ ] **Do this:** As user E, go to Projects and look for a New Project button.
- **You should see:** No button, or a refusal message if you try.

---

## Part 9 — Project user restriction (internal staff)

### Test 9.1 — A staff member with no project sees nothing

- [ ] **Do this:** Log in as **user C (Projects User)** — who has not been added to any project yet. Go to **Projects**.
- **You should see:** An empty list.
- **If you see this instead:** Any projects appear → **failure, report it.**

### Test 9.2 — Add the staff member to one project

- [ ] **Do this:** As **user A**, open `ZZ TEST PROJECT ALPHA` → team / members section → add **user C**.
- **You should see:** User C listed as a team member.

### Test 9.3 — They now see exactly one project

- [ ] **Do this:** As **user C**, refresh and go to Projects.
- **You should see:** **Only** `ZZ TEST PROJECT ALPHA`. Not BETA. Not anything else.
- **If you see this instead:** BETA also appears → **failure, report it.**

### Test 9.4 — They can read but not change it

- [ ] **Do this:** As user C, open `ZZ TEST PROJECT ALPHA` and try to edit the title, change the stage, or delete it.
- **You should see:** No edit controls, or a message that only a Projects Manager can change it.
- **If you see this instead:** The edit saves → **failure, report it.** (Projects Users are read-only by design, even on their own projects.)

### Test 9.5 — They cannot see the money

- [ ] **Do this:** As user C, look for the project value.
- **You should see:** No value.

### Test 9.6 — Removing them takes access away

- [ ] **Do this:** As user A, remove user C from the project team. As user C, refresh Projects.
- **You should see:** The list is empty again.
- **If you see this instead:** They still see it → **failure, report it.**

---

## Part 10 — The Projects Manager view

### Test 10.1 — A Projects Manager sees every project

- [ ] **Do this:** Log in as **user B (Projects Manager)** → Projects.
- **You should see:** **All** projects on the system, including ones they do not manage. This is correct and intended.

### Test 10.2 — But only sees money for their own projects

This is the subtle one. User B was set as **Portal Project Manager** on ALPHA only (Test 3.1).

- [ ] **Do this:** As user B, look at the project list values.
- **You should see:** A value shown for `ZZ TEST PROJECT ALPHA` (500000), and **no value** for `ZZ TEST PROJECT BETA` or any project they do not manage.
- **If you see this instead:** Values shown for every project → **failure, report it.**

### Test 10.3 — Same rule on the project detail page

- [ ] **Do this:** As user B, open `ZZ TEST PROJECT BETA` and look for the value.
- **You should see:** No value.
- **If you see this instead:** The value appears → **failure, report it.**

### Test 10.4 — Manager-only menu items are present

- [ ] **Do this:** As user B, check the left menu.
- **You should see:** Dashboard, Org Chart, Teams and Contracts are all present.
- [ ] **Do this:** As user C (Projects User), check the same.
- **You should NOT see:** Dashboard, Org Chart, Teams, Contracts.

### Test 10.5 — A Projects Manager can edit projects

- [ ] **Do this:** As user B, open `ZZ TEST PROJECT ALPHA`, change the phase, save.
- **You should see:** It saves successfully.

### Test 10.6 — A Projects Manager cannot hand themselves a project

- [ ] **Do this:** As user B, open `ZZ TEST PROJECT BETA` and try to set **Portal Project Manager** to themselves.
- **You should see:** A message saying only a System Manager can reassign the portal project manager.
- **If you see this instead:** It saves, and BETA's value becomes visible to them → **failure, report it.**

---

## Part 11 — Sharing files

### Test 11.1 — Share a folder with a colleague

- [ ] **Do this:** As user A, add user C back to ALPHA's team. Then in Files, share the folder `01-DOCUMENTS` with **user D** (`test.staff2@ata-test.local`), expiry 30 days.
- **You should see:** A confirmation that the folder is shared.

### Test 11.2 — The recipient can see it

- [ ] **Do this:** Log in as **user D** → left menu → **Shared**.
- **You should see:** The shared folder and the files inside it.

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
- **You should see:** Departments with their members, and a chart of the structure.

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

- [ ] **Do this:** As **user E (Portal Customer)**, open the browser address bar and go to:
  `https://ata.enfonoerp.com/api/method/portal_app.api.teams.get_teams`
- **You should see:** A permission error.
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

## Part 16 — Clean-up

Once every test above has passed, remove the test data.

- [ ] Delete projects `ZZ TEST PROJECT ALPHA` and `ZZ TEST PROJECT BETA` (this also removes their folders and files).
- [ ] Delete the routing rule `ZZ Test Rule`.
- [ ] Delete customer `ATA Test Client One`.
- [ ] Disable or delete test users A–E and `test.outsider@ata-test.local`.
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
| 8. Customer invitation | ☐ | | | |
| 9. Project user restriction | ☐ | | | |
| 10. Projects Manager view | ☐ | | | |
| 11. Sharing | ☐ | | | |
| 12. Tasks and views | ☐ | | | |
| 13. Dashboard and AI | ☐ | | | |
| 14. Security | ☐ | | | |
| 15. Desk | ☐ | | | |
| 16. Clean-up | ☐ | | | |

**Do not hand over to the client until Part 14 passes completely and Test 14.5 is confirmed done.**

---

## If something fails

Record: the test number, which user you were logged in as, what you expected, what happened, and the time. The time matters — it lets the developer find the matching entry in the site's Error Log.

The Error Log is at `https://ata.enfonoerp.com/app/error-log` (System Manager only).
