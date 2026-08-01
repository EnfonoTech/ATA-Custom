# Testing Guide — Portal App (Complete Walkthrough)

This is a complete, start-to-finish walkthrough — as if opening the app for a client for the very first time and going through every single screen, in order. Follow it top to bottom. For each step: what to click, and what happens.

---

## 1. Opening the app & logging in

- Open the app link in a browser → a **login page** appears (email + password, with the company logo/branding).
- Enter the email and password given, click login → lands on the **Dashboard**.
- Refresh the page (F5) → stays logged in, does not ask to log in again.
- (Keep this tab open — logout is the very last step, at the end of this guide.)

---

## 2. Dashboard (home screen)

The first screen after login — an overview of everything.

- Loads with summary cards even if there are zero projects yet — no blank/broken screen.
- Shows total project count and a breakdown by status.
- Shows a budget/health indicator per project (colors like healthy / at-risk / over-budget).
- Shows "planned % complete" per project — roughly how far along it should be based on its dates.
- Shows team member count for projects.
- Shows a "recent activity" feed — newest upload or task change at the top.
- Shows "my tasks" — only tasks assigned to the logged-in person, not everyone's.

---

## 3. Projects

Click **Projects** in the side menu.

- A table of every project the logged-in user can access appears.
- Type into the search box → the list narrows to matching projects.
- Use the status filter (dropdown/buttons) → only projects with that status show.
- Each row shows three small colored letter badges — **T**, **A**, **C** (server links: Google Drive, Autodesk, Client/AWS). A colored badge opens that link in a new tab when clicked; a grey badge means no link is set and does nothing when clicked.
- Click **New Project** (if available) → fill in a name and save → the new project appears in the list, and the person who created it is automatically added to its team.
- Open a project's edit option → change its status, dates, progress %, notes, and the three server links → save → refresh the page → every change is still there.
- If allowed, delete a test project → it disappears from every other screen that lists projects too (Dashboard, Kanban, Calendar, Gantt).

---

## 4. Opening one project ("Project detail")

Click on any project's name/row from the Projects list.

- A detail page opens with a summary: status, dates, cost, progress.
- Find the **Customer** section → search for an existing customer and link it → save → the link stays after refresh. Typing a customer name that already exists reuses it instead of making a duplicate.
- Find the **Team** section → add or remove a person → save → the team list updates.
- Find the **Files** area on this page → upload a file (same behavior as the main Files page, see step 10).
- Find the **Tasks** list for this one project.
- If logged in as a client/customer account: the Customer and Team sections should be view-only (no edit controls), and Files should allow viewing/downloading only, no uploading.

---

## 5. Organization Chart

Click **Organization Chart** in the side menu.

- A tree of teams appears, one box per team.
- Click the **+** next to a team → it expands and shows the people in that team; the button turns into **−**.
- Click the **−** → it collapses back.
- Click directly on a person's name → their details (photo, role, office) appear in the panel on the right.
- If there are office filter buttons (e.g. city/branch names) → clicking one narrows the tree to just that office; an "All" option resets it.

---

## 6. Teams

Click **Teams** in the side menu.

- A list of teams appears, each with its members and how many people are in it.
- If allowed to manage teams: add a member → the list and the count update right away. Remove a member → they disappear from the list.

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
- If you're a manager, try assigning a task to someone else → it should appear on their board, not yours.

---

## 9a. Contracts (management only)

Click **Contracts** in the side menu. This screen only appears for System Manager / Projects Manager.

- Pick a project on the left → its uploaded contract documents (if any) appear on the right.
- Upload a contract file → only `.pdf`, `.doc`, `.docx`, `.jpg`, `.jpeg`, `.png` should be accepted; anything else should show an error and not upload.
- Delete a file → confirm prompt appears, then it's removed from the list.
- Log in as a regular team member (not a manager) → the **Contracts** link should not appear in the sidebar at all.

---

## 10. Files

Click **Files** in the side menu, or open the Files section inside a project.

- Pick a project → its files and folder structure appear (a standard set of folders should already exist even for a brand-new project).
- Upload a single file → it appears in the correct folder.
- If there's a **Private** option when uploading, try it both on and off — a private file should only open for someone logged in with permission; a normal one shouldn't need that.
- Upload a ZIP file → it should unpack into folders/files rather than staying as one ZIP.
- Select a folder or some files and download as ZIP → the downloaded archive contains the right files.
- Rename a folder (if allowed) → the new name applies everywhere that folder is shown.
- Create a **share link** for a folder with an expiry date → open that link in a private/incognito browser window (logged out) → the contents are visible until the expiry date, and stop working after it expires or after it's manually revoked.
- Share a file or folder directly with another person's account → log in as that person and check **Shared with me** → it appears there.
- If logged in as a client/customer account: uploading, renaming, and sharing should not be available — view and download only.

---

## 11. File Browser (all files, across projects)

Click **File Browser** (or similarly named) in the side menu.

- A cross-project file list appears.
- Use the search or category filters → results narrow down correctly, pulling from multiple projects at once.

---

## 12. Shared with me / Manage Shares

Click **Shared with me** in the side menu.

- Files and folders that others have shared with the logged-in user appear, grouped by project.

Click **Manage Shares** (usually only visible to project managers/admins).

- A list of all active shares across every project the logged-in user manages appears.
- Try revoking one → it disappears from the list and the recipient loses access immediately.

---

## 13. Folder Rules & File Tools (admin/auditor screens)

Click **Folder Rules** in the side menu (if visible).

- Create a rule (e.g. "Mirror" or "Cross-route") for a file type → upload a matching file into a project → confirm it lands in both the normal folder and the extra configured location.

Click **File Tools** in the side menu (if visible).

- The company-wide default folder template appears (the standard folders every new project starts with).
- Edit it manually, or import a new template from a ZIP file → create a new test project afterward → confirm it starts with the updated folder structure.

---

## 14. Tasks

Click **Tasks** in the side menu.

- A list of tasks appears, with filters for status, priority, project, and "only mine."
- Open a task → change its status, priority, or progress → it saves.
- Add a comment on a task → it appears in the discussion thread immediately.
- Try the quick-create task button and look at the project/assignee dropdowns — **these are known to stay empty currently** (see Known Issues below); this is expected, not a new bug.

---

## 15. AI Chat

Click **ATA AI Chat** in the side menu.

- **This is currently known not to open** (blank page) — see Known Issues below, no need to report it again.
- If it happens to be working, ask something like "how many active projects are there" — the answer should roughly match the numbers seen elsewhere in the app. Note this feature works by matching keywords in the question against the app's own data — it is not a live AI conversation, so it will only answer questions about projects/tasks/files/budgets.

---

## 16. Profile & notifications

Click **Profile** (usually near the account name/photo, top right).

- Update the name, phone number, language, or time zone, then save → refresh the page → the change is still there.
- Look for a notification bell icon → recent notifications appear; marking one as read clears its unread indicator.
- Switch the theme between **Light / Dark / System** → refresh → the choice is remembered.
- Try collapsing the side menu (a small arrow, or Ctrl+B / Cmd+B) → refresh → it stays collapsed.

---

## 17. Admin (only for full administrators — skip if not given this access)

Click **Admin** in the side menu.

- Create a new portal user, choosing a role (regular staff, manager, or client) → that person should be able to log in and see only what their role allows.
- Run a demo data seed → a tracked entry appears showing everything it created; deleting that entry removes everything it made (test projects, tasks, files, etc.) cleanly.
- Try importing a project list from an uploaded Word (.docx) file → the extracted list of project names should match what's actually written in the document before confirming.
- The option to import a folder template from a picked folder (not a ZIP) is **known not to work currently** — use the ZIP upload option instead, which does work.
- Log out and log in as a non-administrator, then try to open the Admin page directly → should be blocked or redirected, not allowed in.

---

## 18. Wrapping up — logging out

- Click **Logout** (usually in the side menu or account menu) → returns to the login page.
- Press the browser's back button → should not be let back into any authenticated page without logging in again.

---

## Things to double-check throughout (not just once)

- If testing as a **client/customer account**: at every single screen, confirm only that client's own projects are visible — never another client's project, anywhere in the app.
- Try the app on a narrow browser window or a phone → the side menu should still collapse usably, and tables should scroll sideways instead of breaking the layout.

---

## Already-known issues (no need to report these again)

| Where | What happens |
|---|---|
| **AI Chat** (side menu) | Doesn't open — blank page. |
| **Tasks → quick-create** | The project and assignee dropdown boxes stay empty. |
| **Files → "Submit to Client Submittal"** button | Shows an error. |
| **Admin → import folder template from a folder (not ZIP)** | Shows an error. The ZIP upload option works fine instead. |
| **Organization Chart** | May show teams with no members / no expand button, if those team members haven't been linked up yet on the backend — this is a data setup issue, not a bug in the screen itself. |

Anything else that doesn't work as described above is a real bug — write down the page, what was clicked, and what happened instead.
