```markdown
# Website Specification  
## OIISP Platform — Ultra-Lightweight Edition  

**Document Version:** 2.0  
**Status:** Draft – Python/FastAPI + μJS Implementation  
**Last Revised:** May 2026  

---

## 1. Purpose & Scope

Same as before: the platform is the single source of truth for independent student projects.  
This edition is rebuilt for maximum speed and simplicity, using server‑rendered HTML with a thin layer of JavaScript.

---

## 2. Design Philosophy

1. **Instant‑Load Pages.** Full HTML delivered in one round‑trip; CSS under 2 KB; no build step.  
2. **Simplest Real‑Time.** Server‑Sent Events (SSE) push HTML fragments, handled by a <5 KB micro‑library.  
3. **Minimal Dependencies.** SQLite, FastAPI, Jinja2, μJS, Sakura.css – everything stays small and auditable.  

---

## 3. User Roles

| Role | Permissions |
|------|-------------|
| Student (Owner) | Submit proposal, post updates, upload files, invite collaborators |
| Student (Collaborator) | Post updates, upload files |
| Faculty (Observer) | Star, Vouch, Endorse |
| Lab Technician | Approve resource requests |
| OIISP Admin | Approve proposals, manage users, moderate |
| Public | Read‑only access to projects, leaderboard, faculty directory |

---

## 4. Information Architecture

```
/                       → Landing Page + Live Leaderboard
/projects               → Full Project Directory (filterable)
/projects/{slug}        → Individual Project Page
/submit                 → Proposal Upload (students only)
/faculty                → Faculty Directory
/resources              → Lab Resource Dashboard
/about                  → How‑It‑Works, Documentation
/admin                  → Admin panel (gated)
```

All routes served by FastAPI via Jinja2 templates. Each page is a simple server‑rendered HTML document.

---

## 5. Page Implementations

### 5.1 Landing Page (`/`)
- **Hero Block** – static text with call‑to‑action.  
- **Leaderboard** – a `<table>` rendered by Jinja2 with current data. A hidden `u-sse="/api/stream/leaderboard"` attribute on the table body replaces the content whenever the server pushes an updated HTML fragment.  
- **Stats Bar** – three numbers fetched via SSE or included in the initial page load.  
- **Recent Activity Feed** – five most recent updates, also updated via SSE.  

No page reload needed; the leaderboard stays live as long as the tab is open.

### 5.2 Project Directory (`/projects`)
- Rendered entirely server‑side using query parameters for filtering.  
- Filters are simple `<form method="GET">` controls; submitting the form reloads the page with the applied filters.  
- Project cards are HTML blocks with Sakura‑styled elements.  

### 5.3 Individual Project Page (`/projects/{slug}`)
- Server‑rendered with all sections (header, abstract, milestone progress bar, update feed, resources, endorsements).  
- **Endorsement buttons** use μJS: `u-post="/api/projects/{slug}/endorse"` sends the action without page refresh. A success response updates the endorsement count via SSE or a returned HTML snippet.  
- **Update posting** is a form with a file input; submitted via AJAX (μJS) to `/api/projects/{slug}/updates`.  

### 5.4 Proposal Upload Portal (`/submit`)
- A GET request shows the upload form (drag‑and‑drop file picker).  
- The form POSTs the `.md` file to `/api/proposals/submit` using `fetch` (handled by μJS).  
- Validation errors are returned as JSON and displayed inline; on success, the user is redirected to the new project page.  
- No live preview in the first iteration to keep complexity minimal; validation is enough.

### 5.5 Faculty Directory (`/faculty`)
- Server‑rendered list of faculty with their expertise tags and project involvement.  
- Clicking a name opens the person’s email client.

### 5.6 Resource Availability Dashboard (`/resources`)
- A table showing current OIISP bookings; refreshed automatically via SSE or a simple `setTimeout` reload.  
- Only technicians and admins can edit.

---

## 6. Leaderboard (SSE‑Powered)

The leaderboard is the central dynamic feature.  
- The server endpoint `/api/stream/leaderboard` is an SSE stream that sends the entire `<tbody>...</tbody>` HTML whenever a project is created, updated, or endorsed.  
- μJS’s `u-sse` automatically swaps the old tbody with the new content – no flicker.  

Default sorting by stars, but clicking a column header reloads the page with a `?sort=stars` parameter.

---

## 7. Technical Stack (No‑Build Edition)

| Layer | Technology | Reason |
|-------|------------|--------|
| **Backend** | Python 3.11 + FastAPI | Async, lightweight, built‑in SSE support |
| **Database** | SQLite (via `aiosqlite`) | Zero‑configuration, single‑file |
| **Templating** | Jinja2 | Fast, server‑side HTML rendering |
| **Frontend logic** | μJS (<5 KB) | AJAX, SSE, form handling without a framework |
| **Styling** | Sakura.css (~2 KB) | Classless, instantly styles semantic HTML |
| **Real‑time** | Server‑Sent Events | Simpler than WebSockets, works over HTTP/1.1 |
| **Teams** | Incoming Webhook + `httpx` | Lightest possible notification path |
| **File storage** | Local filesystem (`uploads/`) | No object store needed; served via FastAPI `StaticFiles` |
| **Auth** | Bcrypt + server‑side sessions | No external provider; passwords stored hashed |
| **Deployment** | Docker (python:3.11-slim) | Single container, easy to ship |

---

## 8. Frontend Behavior Summary

- All dynamic interactions (voting, endorsing, posting updates) use HTML forms with `u-post` or `u-sse` attributes provided by μJS.  
- No page reloads unless necessary (e.g., applying project filters).  
- Sakura.css gives a clean typographic baseline; custom overrides are inline in `<style>` (no separate CSS file).  
- Total frontend payload (HTML + CSS + JS) stays under 14 KB for most pages.

---

## 9. Content Policy & Data Retention

(Unchanged from original – all projects public by default, archiving after 60 days of inactivity, etc.)

---

## 10. Pilot Success Metrics (Adjusted for Lightweight Stack)

| Metric | Target |
|--------|--------|
| Proposals submitted | ≥ 8 |
| Average page load time (TTFB) | < 50 ms |
| Teams notifications delivered | ≥ 20 |
| SSE leaderboard updates without errors | 100 % |
| User‑reported submission time | ≤ 5 minutes |

---

*This specification replaces all JavaScript‑heavy components with the μJS/Sakura.css/Jinja2 stack.  
No build tooling, no npm, no heavy frameworks – just fast, real‑time HTML.*

```