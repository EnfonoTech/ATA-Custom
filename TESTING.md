# Testing Guide — Portal App (Complete Walkthrough)

This is a complete, start-to-finish walkthrough — as if opening the app for a client for the very first time and going through every single screen, in order. Follow it top to bottom. For each step: what to click, and what happens.

The portal has **five roles**, and many screens look different for each of them. Where a step says "as a Team Member" (or another role), use a test login that has exactly that role. Near the end there is a short section on what to check after an update that changes data, and one on the automated tests developers run.

---

## The five roles (read this first)

| Role | Which projects they see | What else to know |
|---|---|---|
| **Super Admin** | Every project | Does everything: roles, passwords, teams. Always sees project money. |
| **Department Admin** | The projects of the teams they administer, plus the projects that belong to no team | Edits those projects and looks after their teams' people. Sees money only on projects where they are the Lead Architect. |
| **Team Lead** | The projects of the team they lead | Can add people to those projects, but not remove them. Never sees money. |
| **Team Member** | Only the projects they were added to (or lead as Lead Architect) | Works on those projects. Never sees money. Starts with an empty Projects list until someone puts them on a project. |
| **Client Customer** | Only the projects of their own customer — and in them only the **06-CLIENT SUBMITTAL** folder | Reads **Incoming** and **Outgoing**, and can send files to **Outgoing** only. No internal screens. |

A project belongs to a team when its Portal Team is that team, or somebody from that team is on its Team card or is its Lead Architect. Every other project belongs to no team: Super Admins and every Department Admin see it, a Team Lead never does, and a Team Member only if they are on it.

---

## 1. Opening the app & logging in

- Open the app link in a browser → a **login page** appears (email + password, with the company logo/branding).
- Enter a wrong password → you are refused and stay on the login page.
- Enter the email and password given, click login → a Super Admin or Department Admin lands on the **Dashboard**; every other role lands on **Projects** (they have no Dashboard).
- Refresh the page (F5) → stays logged in, does not ask to log in again.
- Click **Forgot Password?** on the login page → the card changes to "Reset your password". Type an email address and click **Send reset link** → the same green message appears whether or not the address belongs to a login ("If that address belongs to a portal login, a reset link is on its way."). Click the link in the mail and choose a new password → you can sign in with it, and a client lands back on the portal. More than five requests within an hour from one network are refused.
- (Keep this tab open — logout is the very last step, at the end of this guide.)

---

## 2. Dashboard (home screen)

The first screen after login for a Super Admin or Department Admin — an overview of everything. (The other roles have no Dashboard in their menu; opening its address takes them to Projects.)

- Loads with summary cards even if there are zero projects yet — no blank/broken screen.
- Shows total project count and a breakdown by status.
- Shows a budget/health indicator per project (colors like healthy / at-risk / over-budget).
- Shows "planned % complete" per project — roughly how far along it should be based on its dates.
- Shows team member count for projects.
- Shows a "recent activity" feed — newest upload or task change at the top.
- Shows "my tasks" — only tasks assigned to the logged-in person, not everyone's.
- The numbers cover only the projects that person may see, so a Department Admin's totals can be smaller than a Super Admin's.

---

## 3. Projects

Click **Projects** in the side menu.

- A table of every project the logged-in user can access appears. Check it with a login of each role: a Super Admin sees all of them; a Department Admin sees their teams' projects and the no-team projects; a Team Lead sees their team's projects; a Team Member sees only the projects they are on; a Client Customer sees only their customer's.
- Type into the search box → the list narrows to matching projects.
- Use the status filter (dropdown/buttons) → only projects with that status show.
- Each row shows three small colored letter badges — **T**, **A**, **C** (server links: Google Drive, Autodesk, Client/AWS). A colored badge opens that link in a new tab when clicked; a grey badge means no link is set and does nothing when clicked.
- Money (the estimated cost) shows for a Super Admin on every project and for a Department Admin only on projects where they are the Lead Architect. A Team Lead, a Team Member and a Client Customer never see it, and the **Lead Architect** column is not shown to them either.
- Click **New Project** (if available) → fill in a name and save → the new project appears in the list, and the person who created it is automatically added to its team. The button (here and in the top bar) is always shown to a Super Admin and a Department Admin, to a Team Lead or Team Member only while "Allow any portal user to create projects" is ticked in Portal Project Settings, and never to a Client Customer.
- Open a project's edit option → change its status, dates, progress %, notes, and the three server links → save → refresh the page → every change is still there. (A Team Member can edit only the projects they are on.)
- If allowed, delete a test project → it disappears from every other screen that lists projects too (Dashboard, Kanban, Calendar, Gantt).

---

## 4. Opening one project ("Project detail")

Click on any project's name/row from the Projects list.

- A detail page opens with a summary: status, dates, progress, and — where the role may see it — cost.
- Find the **Customer** section → search for an existing customer and link it → "Customer linked." appears and the link stays after refresh. Typing a customer name that already exists reuses it instead of making a duplicate.
- Find the **Team** card → type a name or email and click the person → they are added at once ("Added to the team."; there is no Save button). **Add from org chart** lets you tick several people (shown to a Super Admin, Department Admin and Team Lead).
- **Remove** beside a person (confirm the pop-up) → "Removed from the team." It is offered only to a Super Admin and a Department Admin. A Team Lead can add people but sees no Remove. A Team Member sees "View only…" and cannot add anyone unless they are the project's Lead Architect (then they can add, still not remove). A client is never offered in either picker.
- Once the project has a Customer, a Super Admin sees a **Client Customer logins** card with **Invite new user** → invite a login for that customer → it is listed under "People with access". A Department Admin sees the card and can add an existing client login, but cannot invite a new one.
- Find the **Files** area on this page → upload a file (same behavior as the main Files page, see step 10).
- Find the **Tasks** list for this one project.
- If logged in as a Client Customer: there is no Team card and no Tasks list at all, the Customer section is view-only, and Files shows only 06-CLIENT SUBMITTAL (see step 10).

---

## 5. Org Chart

Click **Org Chart** in the side menu. It is there for a Super Admin, a Department Admin and a Team Lead; a Team Member or Client Customer has no menu entry and is taken to Projects if they type the address.

- A **Super Admins** group and one box per team appear, and, for a Super Admin or Department Admin, a **Not in a team yet** list (people who are in no team). A Client Customer never appears.
- Click the **+** next to a team → it expands and shows the people in that team; the button turns into **−**. Click the **−** → it collapses back.
- Click directly on a person's name → their details (name, email, role tag, team, number of projects) appear in the panel on the right, together with the actions you may take.
- If there are office filter buttons (e.g. city/branch names) → clicking one narrows the tree to just that office; "All Offices" resets it.
- As a **Super Admin**, click a person in a team → **Role in <team>** offers Team Member, Team Lead and Department Admin → **Save**. A team has one Team Lead: choosing a new one makes the previous lead a Team Member. Also try **Remove as Team Lead**, **Remove from team**, **Assign to project…**, **Reset password…** and **Make Super Admin** / **Remove Super Admin access**. You cannot change your own Super Admin access, and the last Super Admin cannot be removed.
- As a **Department Admin**, changing a role, **Remove from team** and **Reset password…** work only on Team Leads and Team Members of the teams you administer (the role box offers only Team Member and Team Lead). A person in another team, another Department Admin and a Super Admin show none of those. Click a person under **Not in a team yet** → **Add to a team** → pick one of your teams → **Add**.
- As a **Team Lead**, the only action is **Assign to project…**, and it lists only your team's projects.
- **Assign to project…** → tick one or more projects → **Add to N projects** → "… was added to N projects." and that person now sees them.
- **Reset password…** → **Email them a reset link** ("A reset link is on its way to …"), or, for a Super Admin only, **Set a password now** (at least 8 characters; they are signed out everywhere). A Department Admin is offered the button only for the Team Leads and Team Members of their own teams.

---

## 6. Teams

Click **Teams** in the side menu (Super Admin and Department Admin only).

- A list of teams appears, each with its members and how many people are in it.
- Add a member → the list and the count update right away. Remove a member → they disappear from the list. A Department Admin can change only the teams they administer; only a Super Admin can create a new team.

---

## 7. Kanban board

Click **Kanban** in the side menu.

- Projects appear as cards, grouped into columns by stage (e.g. Planning, Active, On Hold, Done).
- If allowed, drag a card into a different column → refresh the page → it stays in the new column.

---

## 8. Calendar

Click **Calendar** in the side menu.

- Project and task dates appear plotted on a calendar.
- Click any date entry → it opens that project or task.

---

## 9. Gantt Chart & Daily Task

Click **Gantt Chart** in the side menu.

- A horizontal timeline appears, showing projects grouped by team.
- If there are office/team filter options, try one → the chart narrows accordingly.
- Click the flag icon on a project row (or the **+ Milestone** button) → add a short label and pick a **date** → save. A red flag should appear on the timeline at that exact date (not at the project's end date), and hovering it shows the label + date.

Click **Daily Task** in the side menu.

- A day-by-day board appears, showing roughly four weeks — your own personal reminders (not tied to a project).
- Add a new task with a title, date, time, and optionally a color → it appears on the correct day.
- Edit it → the change saves. Mark it complete → its look changes (e.g. a strikethrough). Delete it → it disappears from the board.
- If you're a Super Admin or Department Admin, try assigning a task to someone else → it should appear on their board, not yours.

---

## 9a. Contracts (management only)

Click **Contracts** in the side menu. This screen only appears for a Super Admin or Department Admin.

- Pick a project on the left → its uploaded contract documents (if any) appear on the right.
- Upload a contract file → only `.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, `.png` should be accepted; anything else should show an error and not upload.
- Delete a file → confirm prompt appears, then it's removed from the list.
- Log in as a Team Lead or Team Member → the **Contracts** link should not appear in the sidebar at all.

---

## 10. Files

Click **Files** in the side menu, or open the Files section inside a project.

- Pick a project → its files and folder structure appear (a standard set of folders should already exist even for a brand-new project; **06-CLIENT SUBMITTAL** holds two folders, **Incoming** and **Outgoing**).
- Upload a single file → it appears in the correct folder.
- If there's a **Private** option when uploading, try it both on and off — a private file should only open for someone logged in with permission; a normal one shouldn't need that.
- Upload a ZIP file → it should unpack into folders/files rather than staying as one ZIP.
- Select a folder or some files and download as ZIP → the downloaded archive contains the right files.
- Rename a folder (if allowed) → the new name applies everywhere that folder is shown. The client folder and its Incoming and Outgoing folders have no Rename button, because they are found by name.
- Create a **share link** for a folder with an expiry date → open that link in a private/incognito browser window (logged out) → the contents are visible until the expiry date, and stop working after it expires or after it's manually revoked.
- Share a file or folder directly with another person's account → log in as that person and check **Shared with me** → it appears there.
- If logged in as a Client Customer: only 06-CLIENT SUBMITTAL appears, with **Incoming** (marked "From ATA") and **Outgoing** (marked "Your uploads"). There is no upload button, no drop area, no renaming and no sharing. The one way to upload is the **Send files to ATA** card → **Choose files** → the files go into Outgoing and the ATA team sees them marked as from the client. A file type that is not allowed (for example `.html`) is refused.

---

## 11. File Browser (all files, across projects)

Click **File Browser** (or similarly named) in the side menu.

- A cross-project file list appears.
- Use the search or category filters → results narrow down correctly, pulling from multiple projects at once.
- As a Super Admin, Department Admin, Team Lead or Team Member on the project, click **Submit** on a file row → **Confirm & Submit to Client** → "Submitted as "01_<date>_<file name>" (SL 1) to the client's Incoming folder." The copy sits in 06-CLIENT SUBMITTAL / Incoming (the original stays where it was), and the next file gets the next number. Log in as the client → it opens from Incoming.
- A Client Customer sees no Submit or Share buttons.

---

## 12. Shared with me / Manage Shares

Click **Shared with me** in the side menu.

- Files and folders that others have shared with the logged-in user appear, grouped by project.

Click **Manage Shares** (shown to anyone who can manage at least one project, never to a client).

- A list of all active shares across every project the logged-in user manages appears.
- Try revoking one → it disappears from the list and the recipient loses access immediately.

---

## 13. Routing rules & File Tools (admin/auditor screens)

Click **Routing rules** in the side menu (Super Admin and Department Admin; if visible).

- Create a rule (e.g. "Mirror" or "Cross-route") for a file type → upload a matching file into a project → confirm it lands in both the normal folder and the extra configured location.

Click **File Tools** in the side menu (Super Admin, or a person with the Auditor role; if visible).

- The company-wide default folder template appears (the standard folders every new project starts with, including Incoming and Outgoing inside 06-CLIENT SUBMITTAL).
- Edit it manually, or import a new template from a ZIP file → create a new test project afterward → confirm it starts with the updated folder structure. Incoming and Outgoing are added even to a template that does not list them.

---

## 14. Tasks

Click **Tasks** in the side menu (not shown to a Client Customer).

- A list of tasks appears, with filters for status, priority, project, and "only mine."
- Open a task → change its status, priority, or progress → it saves.
- Add a comment on a task → it appears in the discussion thread immediately.
- Try the quick-create task button and look at the project/assignee dropdowns → they list people and projects you may use (a Team Member's project box lists only the projects they are on); the new task keeps the assignee you chose.

---

## 15. AI Chat

Click **ATA AI Chat** in the side menu (not shown to a Client Customer; typing its address takes them to Projects).

- The page opens. Ask something like "how many active projects are there" — the answer should roughly match the numbers seen elsewhere in the app, and it follows the role: a Team Member who asks how many projects there are gets the count of their own projects, not the total. Note this feature works by matching keywords in the question against the app's own data — it is not a live AI conversation, so it will only answer questions about projects/tasks/files/budgets.

---

## 16. Profile & notifications

Click **Profile** (usually near the account name/photo, top right).

- Update the name, phone number, language, or time zone, then save → refresh the page → the change is still there.
- The **Portal role** box shows the person's role (for example Team Lead) and the teams it applies to.
- In the **Password** card, change your own password: a wrong current password, two different new passwords and a new password shorter than 8 characters are each refused with a message; a proper one succeeds ("Password changed…") and other devices are signed out.
- Look for a notification bell icon → recent notifications appear; marking one as read clears its unread indicator.
- Switch the theme between **Light / Dark / System** → refresh → the choice is remembered.
- Try collapsing the side menu (a small arrow, or Ctrl+B / Cmd+B) → refresh → it stays collapsed.

---

## 17. Admin (Super Admin only for most cards — skip if not given this access)

Click **Admin** in the side menu.

- Create a new portal user, choosing one of the five roles (Super Admin, Department Admin, Team Lead, Team Member or Client Customer; a client needs a Customer, a Team Lead or Team Member a team) → that person should be able to log in and see only what their role allows. Only a Super Admin can create a Super Admin or a Department Admin.
- Use the **Reset a password** card → search for a person → email them a reset link; a Super Admin can also set a password directly. A Department Admin sees only this card and can email a link only to the Team Leads and Team Members of their own teams.
- Run a demo data seed → a tracked entry appears showing everything it created; deleting that entry removes everything it made (test projects, tasks, files, etc.) cleanly.
- Try importing a project list from an uploaded Word (.docx) file → the extracted list of project names should match what's actually written in the document before confirming.
- Import a folder template from an uploaded ZIP file → the template is replaced with what the archive contains. (Importing from a picked folder was listed as not working in earlier editions of this guide and has not been re-checked; if it shows an error, use the ZIP option.)
- Log out and log in as a non-administrator, then try to open the Admin page directly → should be blocked or redirected, not allowed in.

---

## 18. Wrapping up — logging out

- Click **Logout** (usually in the side menu or account menu) → returns to the login page.
- Press the browser's back button → should not be let back into any authenticated page without logging in again.

---

## Things to double-check throughout (not just once)

- If testing as a **Client Customer**: at every single screen, confirm only that customer's own projects are visible — never another client's project, anywhere in the app — and that inside a project only 06-CLIENT SUBMITTAL is visible. The menu holds only Projects, Files, File Browser, Shared and Profile; Tasks, Kanban, Calendar, Gantt Chart, Daily Task and AI Chat are not shown, and typing their address takes the client back to Projects.
- If testing as a **Team Member** or **Team Lead**: confirm no project outside their own (or their team's) ever shows up, in the Projects list or in Kanban, Gantt, Calendar, Files, File Browser and the search box, and that no money figure appears.
- Try the app on a narrow browser window or a phone → the side menu should still collapse usably, and tables should scroll sideways instead of breaking the layout.

---

## After an update that changes data (administrators)

Do this once on a copy of the site, then again right after the real update has been migrated. Write down the numbers first: how many logins hold the old client role, which former managers exist and how many projects each of them sees.

- Role list → the client role is now called **Client Customer** (the old name is gone), with the same number of logins as before; each client still signs in and sees only their customer's projects.
- Each former Projects Manager who is not also a Super Admin is now a **Department Admin** of every team, signs in, and sees the same number of projects as before the update (the projects that belong to no team included). A person who is also a Super Admin is not added to any team.
- Every project that already had a folder tree now has **Incoming** and **Outgoing** inside 06-CLIENT SUBMITTAL, including projects whose folder is spelled "06 - CLIENT SUBMITTAL"; no file is left loose in the client folder (what a client uploaded is in Outgoing, everything else in Incoming). A project that never had a folder tree is left alone.
- Run the update a second time → nothing changes and no new "Portal:" entries appear in the Error Log.

---

## Automated tests (for developers)

The app has an automated suite in `portal_app/tests/`: **74 tests** in three modules.

| Module | Tests | What it checks |
|---|---|---|
| `test_portal_roles.py` | 41 | The five roles: who sees which projects and money, the Org Chart and role changes, the project Team card rules, password reset, the client Incoming / Outgoing folders, the migration patches and creating users |
| `test_customer_portal_access.py` | 18 | Client Customer logins: landing on the portal, reset rules, linking one login to several customers |
| `test_portal_security.py` | 15 | Security regressions: file upload safety, share links that fail closed, staff-only endpoints, no fixed demo password |

Run them on a **development site only** — never on production (they create and delete users, projects and files):

```
bench --site <dev-site> run-tests --app portal_app
bench --site <dev-site> run-tests --app portal_app --module portal_app.tests.test_portal_roles
```

The second line runs a single module.

Writing a new test:

- Put it in `portal_app/tests/` and base it on `FrappeTestCase`. For anything about roles, reuse `PortalRoleTestBase` in `test_portal_roles.py`: it builds two teams, one login per role and five projects, all with throwaway names and `@roles.test` addresses.
- Assert what **each** of the five roles gets for the rule you test — what is allowed and what is refused — not only the happy path.
- **Make the fixtures look like production data, not like the design.** The first Department Admin rule passed its tests but would have hidden most of the portfolio from a converted manager: every test project was either inside a team or had nobody on it, while real projects are often staffed by people who sit in no team. The suite now has a project staffed from outside every department, and the migration test asserts that a converted manager still sees every project. Look at the shape of the real data before you trust a permission rule.

---

## Already-known issues (no need to report these again)

| Where | What happens |
|---|---|
| **Team Member with an empty Projects list** | Expected, not a bug: a Team Member sees only the projects they are on. Put them on a project from the Org Chart (**Assign to project…**) or from the project's Team card. |
| **Admin → import folder template from a folder (not ZIP)** | Not re-checked in this edition: if it shows an error, the ZIP upload option works instead. |
| **Org Chart** | A team with nobody in it reads "No people in this team yet." People who are in no team are listed under "Not in a team yet" until an admin adds them to one. This is data setup, not a bug in the screen itself. |

Anything else that doesn't work as described above is a real bug — write down the page, what was clicked, and what happened instead.
