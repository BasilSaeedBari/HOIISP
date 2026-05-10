# Website Specification
## HOIISP Platform — GitHub-Synced Edition

**Document Version:** 3.0  
**Status:** Draft — Python/FastAPI + μJS Implementation  
**Last Revised:** May 2026

---

## 1. Purpose & Scope

This document defines the full UX specification, information architecture, and page-by-page implementation guide for the HOIISP web platform, Version 3.

The fundamental shift in V3: **HOIISP is a display and notification engine, not a management platform.** Students manage their projects on GitHub. HOIISP watches, verifies, aggregates, and presents that data to the university community. No student accounts. No file uploads. No second system to maintain.

---

## 2. Design Philosophy

1. **Zero Friction for Students.** Paste a GitHub URL, wait for approval. That's it. Students never return to the HOIISP website to do anything — pushing to GitHub is the update mechanism.
2. **Read-Only Public Face.** Every page visible to non-admin visitors is entirely read-only. No logins, no forms (except the submission page), no sessions.
3. **GitHub Is the Source of Truth.** The displayed data is always derived from the student's GitHub repository. HOIISP does not let anyone edit project content through the web interface — edits happen in the repo.
4. **Notify, Don't Nag.** Faculty receive one digest email per week (Friday) and targeted Teams notifications for events they care about. HOIISP does not send daily emails or push notifications.

---

## 3. User Roles

| Role | How They Interact with HOIISP | Login Required? |
|---|---|---|
| Student | Submits a GitHub URL; never needs to return | No |
| Faculty | Browses leaderboard and project pages; reads Friday digest email | No |
| Lab Technician | Receives resource request summary from admin; no direct HOIISP login | No |
| Public | Read-only access to all public project data | No |
| HOIISP Admin | Approves/rejects submissions, manages faculty directory, manages digest | Yes (admin account only) |

---

## 4. Information Architecture

```
/                           → Landing Page + Live Leaderboard
/projects                   → Full Project Directory (filterable)
/projects/{slug}            → Individual Project Page
/submit                     → GitHub URL Submission Form (no login)
/faculty                    → Faculty Directory
/terms                      → Terms & Conditions
/admin                      → Admin Panel (admin login required)
/admin/review/{id}          → Single submission review
/admin/faculty              → Manage faculty directory
/admin/digest               → Digest preview and manual trigger
```

No `/auth` route for students. No `/resources` dashboard (resource data is visible within each project page). No `/about` page needed — the README and terms cover it.

---

## 5. Page Specifications

### 5.1 Landing Page (`/`)

The primary public face of the platform. Communicates the initiative's purpose instantly and surfaces active projects.

**Components, in order:**

**Hero Block**  
A single sentence: *"HOIISP is Habib University's live directory of student-led technical projects."*  
One call-to-action button: `Submit Your GitHub Repo`.  
One secondary link: `How It Works` → anchors to the short explanation below.

**How It Works Block** (static, three steps)  
`1. Put a project.md in your GitHub repo → 2. Submit the URL here → 3. Your project goes live on approval.`  
Link to `ProjectFormat.md` download.

**Stats Bar** (three live counters, SSE-updated)  
- `Active Projects` — count of approved, non-archived projects
- `Faculty Endorsements` — total endorsement records
- `Total Lab Hours Requested` — sum across all active resource matrices

**Live Leaderboard** (see Section 6 for full spec)

**Recent Activity Feed**  
Five most recent GitHub push events recorded by HOIISP, shown as compact cards:  
`[Project Name] — pushed an update — X minutes ago`  
Each card links to the project page.

**Footer**  
Links to: `ProjectFormat.md`, `TermsAndConditions`, `Faculty Directory`, `hoiisp@habib.edu.pk`.

---

### 5.2 Project Directory (`/projects`)

A searchable, filterable grid of all approved project cards.

**Filter Controls (all `<form method="GET">`, no JavaScript required):**
- Domain (Electrical Engineering, Computer Science, Mechatronics, etc.)
- Status (`Active` / `Completed` / `Archived`)
- Sort by: Stars, Last GitHub Push, Milestone Progress, Date Approved

**Project Card:**
```
┌──────────────────────────────────────────────────┐
│  [DOMAIN TAG]  [STATUS BADGE]                    │
│  Project Title                                   │
│  ──────────────────────────────────────────────  │
│  Lead: Name   Team: N members   Repo: [GitHub↗]  │
│  Progress: ████████░░ 80%  [M3 of 5]            │
│  ★ N Stars   ✓ N Faculty Endorsements           │
│  Last push: 3 days ago                          │
└──────────────────────────────────────────────────┘
```

The "Last push" timestamp comes from the GitHub webhook event log, not from any manual update. If a repo has not had a push in 14 days, a `Stale` warning badge appears on the card.

---

### 5.3 Individual Project Page (`/projects/{slug}`)

Auto-generated from the parsed `project.md` content, cross-referenced with the GitHub repo. This page is entirely read-only.

**Sections (in order):**

**Project Header**
- Title, Status badge, Domain tags
- Team members (Name, Program, Year — no email addresses displayed publicly)
- GitHub repo link (external)
- Date Approved, last GitHub push timestamp
- "Star" count (cosmetic — stars are given by admin on behalf of faculty)

**Abstract & Problem Statement**
Auto-populated from `project.md`. Rendered as prose.

**Objectives**
Rendered as a numbered list from `project.md`.

**Milestone Tracker**
Visual progress bar, segmented by milestone count, filled by `Complete` milestones.  
Below the bar, each milestone as a card:
```
M1 | Design & Simulation | Planned: 2026-06-01 | Status: Complete ✓
M2 | Procurement          | Planned: 2026-06-15 | Status: In Progress ⏳
```
Status is read directly from the WBS table in `project.md`. Students update status by editing the file and pushing.

**Recent GitHub Activity Feed**
Last 5 commits to the repository (title + date + author + link to commit), fetched from GitHub API. This section is live — it shows real engineering activity, not manually written updates.

**Resource Log**
Table rendered from the Resource Management Matrix in `project.md`.  
Columns: Resource | Lab | Estimated Hours | Required From → Until.  
This is informational. Actual bookings are handled offline between the student and lab technician.

**Success Metrics**
Table rendered from `project.md`. Shows target values and measurement methods.

**Endorsements Panel** (right sidebar or bottom section)
Faculty endorsements recorded by admin. Each shows: Faculty Name, Department, optional quote.  
If no endorsements yet: "No endorsements yet. Faculty: contact the HOIISP admin."

**Repository Link Block**
Prominent link to the GitHub repo with the last-updated timestamp.  
Message: *"All project files, code, data, and reports live in the GitHub repository above."*

---

### 5.4 Submission Page (`/submit`)

The only page with a user-facing form. No login required.

**Form fields:**
1. GitHub Repository URL (text input, validated as a valid `github.com` URL)
2. Lead student's Habib email (text input, `@st.habib.edu.pk` only — for admin contact, not stored as an account)
3. Checkbox: "This repository is set to Public on GitHub"
4. Checkbox: "At least one commit in this repo was made using a `@st.habib.edu.pk` Git email"
5. Checkbox: "I have read and agree to the HOIISP Terms and Conditions" (links to `/terms`)
6. `Submit Repository` button

**After submission:**
- HOIISP immediately calls the GitHub API to:
  - Verify the repo is public and accessible
  - Check commit history for a `@st.habib.edu.pk` author email
  - Fetch `project.md` from the repo root
  - Run the structural parser against `project.md`
- The page shows one of:
  - **Instant rejection (not stored):** Repo not found / not public / no Habib commit email found. Specific error shown.
  - **Parser warnings (stored, queued for admin):** Repo verified, but `project.md` has missing or malformed sections. Submission is queued with the parser report so the admin can see exactly what's wrong.
  - **Clean submission (stored, queued for admin):** All checks pass. "Your submission is queued for admin review. You'll hear back within 48 hours."
- The lead email is used only for admin contact if needed. It is not stored in any user table.

**No account is created. No session is set. The form clears on success.**

---

### 5.5 Faculty Directory (`/faculty`)

Publicly browsable directory, fully managed by the HOIISP admin.

**Each Faculty Card:**
- Name, Title, Department
- Expertise / domain tags (manually set by admin)
- "Active in X Projects" — count of projects in their domain, linked
- "Has Endorsed X Projects" — count of endorsements recorded by admin, linked
- Habib email (mailto link)

This page directly addresses the original problem: students not knowing which professor to approach for guidance.

---

### 5.6 Admin Panel (`/admin`)

Only accessible after admin login (`POST /api/admin/login`). Admin credentials are the only accounts in the system.

**Panel sections:**

**Submission Queue**  
List of all pending submissions. For each:
- GitHub repo URL
- Lead email
- GitHub verification status (✓ Habib email found / ✗ Not found / ⚠ Repo not accessible)
- Parser status: list of required sections with ✓ / ✗ / ⚠
- `Review` button → opens `/admin/review/{id}`

**Single Submission Review (`/admin/review/{id}`)**
- Full parsed preview of the `project.md` content
- GitHub verification detail (which commit email matched, when)
- Approve form: optional notes → `Approve`
- Reject form: rejection reason (shown to admin as record; admin manually contacts student) → `Reject`
- On approval: project slug is auto-generated from title; project page goes live; Teams notification fires; student's lead email is logged.

**Active Projects Dashboard**  
Table of all approved projects:
- Title / Slug / Status / Last Push / Milestone progress
- `Force Sync` button — re-fetches `project.md` from GitHub immediately (outside normal webhook cycle)
- `Archive` button — marks project as Archived (appears greyed on leaderboard)
- `Add Endorsement` button — modal to record a faculty endorsement (faculty name, dept, optional quote)

**Faculty Directory Management**  
Simple CRUD: add/edit/remove faculty entries. Name, title, department, email, expertise tags.

**Digest Management (`/admin/digest`)**  
- Preview of the Friday digest email (rendered HTML)
- Last sent timestamp
- `Send Now` button (for testing or off-cycle sends)
- Digest recipient list (editable)

---

## 6. The Leaderboard — Full Specification

The leaderboard is the discovery engine for the platform.

### 6.1 Default Columns

| Column | Description |
|---|---|
| # | Rank (sorted by Stars by default) |
| Project Name | Linked to project page |
| Domain | Primary domain tag |
| Sub-Field | e.g., "FPGA Design", "Computer Vision" |
| Team | Number of members (hover or click expands names) |
| Status | `Active` / `Completed` / `Archived` |
| Progress | Visual milestone bar |
| Stars | Total admin-recorded faculty stars |
| Last Push | Days since last GitHub push |

### 6.2 Staleness Indicator

Any project with no GitHub push in 14 days receives a `Stale ⚠` badge on its row. This is computed from the webhook event log, not from `project.md`.

### 6.3 Real-Time Updates via SSE

The leaderboard `<tbody>` has a `u-sse="/api/stream/leaderboard"` attribute. The server pushes a new `<tbody>` HTML fragment whenever:
- A new project is approved
- A GitHub push webhook is received for any tracked repo
- An endorsement or star is recorded by admin

No page reload is needed. The table updates silently while the page is open.

### 6.4 Sorting & Filtering

All sorting and filtering is server-side via `?sort=stars&domain=cs&status=active` query parameters. Column header clicks reload the page with updated parameters. No client-side JavaScript sorting.

---

## 7. Technical Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | Python 3.14 + FastAPI | Lightweight, async-native, built-in SSE support |
| Database | SQLite via `aiosqlite` | Zero config, single file, sufficient for pilot scale |
| Templating | Jinja2 | Server-rendered HTML; fast; no build step |
| Frontend JS | μJS (< 5 KB) | Handles SSE, AJAX form posts, no framework |
| Styling | Sakura.css (~ 2 KB) | Classless; styles semantic HTML out of the box |
| GitHub Integration | `httpx` + GitHub REST API v3 | Verification, commit fetch, `project.md` fetch |
| Webhooks | FastAPI `POST /api/webhook/github` | Receives push events; triggers re-sync |
| Email | `aiosmtplib` + APScheduler | Friday digest; async send; no external service |
| Teams | Incoming Webhook + `httpx` | Event notifications; always non-blocking |
| Auth | Bcrypt sessions (admin only) | Single admin account; Starlette SessionMiddleware |
| Deployment | Docker (python:3.11-slim) | One container, one volume mount |

---

## 8. Frontend Behaviour Summary

- All dynamic elements (leaderboard, stats bar, activity feed) use SSE via `u-sse` attributes.
- The submission form posts via `fetch` (μJS `u-post`) and displays the result inline — no page reload on success or error.
- All other interactions (filtering, sorting) are plain `<form method="GET">` submissions — no JavaScript involved.
- Total frontend payload (HTML + CSS + JS) stays under 14 KB for most pages.
- No npm. No build step. No bundler.

---

## 9. Content Policy

- All project content parsed from GitHub is public by default. Students agree to this at submission.
- HOIISP never stores or displays source code — only the structured data from `project.md`.
- The GitHub repository link is displayed on every project page. Students are responsible for what they commit.
- Faculty endorsements are voluntary, non-binding, and do not constitute formal academic supervision.
- HOIISP is not a grading platform. No grades are issued through it.

---

## 10. Data Retention & Archival

- Approved projects are retained permanently as a public portfolio.
- Projects with no GitHub push for 60 days, not marked Complete, are moved to `Archived` after admin notification.
- HOIISP does not store project files. Archival only affects the HOIISP display status. The GitHub repo is untouched.
- At the end of each academic year, a compiled summary PDF of completed projects is generated from the database and published on the platform.

---

## 11. Pilot Success Metrics

| Metric | Target |
|---|---|
| GitHub URLs submitted | ≥ 8 |
| Verified and approved projects | ≥ 6 |
| Average page load time (TTFB) | < 50 ms |
| Teams notifications delivered | ≥ 20 |
| Friday digest emails sent without error | 100% |
| SSE leaderboard updates without errors | 100% |
| Student-reported time from repo-ready to submission | ≤ 5 minutes |
| Faculty-reported discovery of a relevant project via HOIISP | ≥ 2 incidents |
