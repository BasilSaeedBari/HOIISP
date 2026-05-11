# Habib Open Innovation & Independent Study Platform (HOIISP)

**Version:** 3.0  
**Status:** Specification — Clean Reimplementation  
**Last Revised:** May 2026

---

## What HOIISP Is

HOIISP is a **read-only discovery and notification platform** for student-led technical projects at Habib University.

It does one thing well: it watches GitHub repositories, verifies Habib affiliation, extracts structured project data, and makes that data visible and discoverable — to faculty, peers, and the public — without requiring students to manage a second account or upload files to a second system.

HOIISP is not a project management tool. It does not host files. It does not issue tasks. It does not replace GitHub.

---

## Core Principle

> **GitHub is the source of truth. HOIISP is the window.**

Students work on GitHub as they normally would. HOIISP watches, verifies, and presents. When something changes in the repo, HOIISP reflects it. When milestones are updated in `project.md`, the leaderboard updates. When a new commit is pushed, the "last activity" timestamp ticks forward. Faculty find out every Friday via an automated digest email.

---

## How It Works (Student's Perspective)

1. Create a GitHub repository for your project.
2. Add a `project.md` to the root of the repo, following the format in `ProjectFormat.md`.
3. Make sure at least one contributor has committed using a `@st.habib.edu.pk` email address (this is how HOIISP verifies you are a Habib student).
4. Submit your GitHub repo URL at `hoiisp.habib.edu.pk/submit` — no account required.
5. An admin reviews the submission (within 48 hours). If approved, your project page goes live automatically.
6. From that point forward, every push to your repo that changes `project.md` is reflected on HOIISP within minutes. You never need to touch the HOIISP website again.

---

## How It Works (Faculty's Perspective)

- No login required. Browse the public leaderboard and project directory.
- Every Friday morning, a digest email arrives in your inbox summarising new projects, milestone completions, and stale projects in your domain.
- A Microsoft Teams notification fires whenever a project in a domain you follow is approved, or completes a milestone.
- If you want to endorse a project, contact the HOIISP admin — endorsements are recorded manually to keep the trust signal high.

---

## How It Works (Admin's Perspective)

- Log in at `/admin` with an admin account (the only accounts that exist on HOIISP).
- Review submitted GitHub URLs: the system shows you the verification result (is a `@st.habib.edu.pk` commit email found?), a preview of the parsed `project.md`, and a summary of missing or malformed sections.
- Approve or reject with a note. Rejection sends a GitHub notification (via a comment on the repo's open submission issue, if one exists) or a plain message the admin can forward manually.
- Manage the faculty directory (names, departments, expertise tags). This is the only data HOIISP stores that doesn't come from GitHub.
- View the weekly digest preview before it sends every Friday.

---

## What HOIISP Stores (and What It Doesn't)

**HOIISP stores (in SQLite):**
- The GitHub repo URL and verification status for each registered project
- The last-fetched, parsed content from `project.md` (title, abstract, team, milestones, resources, metrics, domain)
- Timestamp of last GitHub push
- Admin approval decision and notes
- Faculty directory (manually managed)
- Admin account credentials (bcrypt-hashed, one or two accounts only)
- Email digest log (sent/not sent, timestamp)

**HOIISP does not store:**
- Student passwords or student accounts
- Uploaded files of any kind
- Project files, images, or data — those live in GitHub
- Any data that isn't derivable from the public GitHub API or the `project.md` in the repo

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + FastAPI |
| Database | SQLite via `aiosqlite` |
| Templating | Jinja2 (server-rendered HTML) |
| Frontend | μJS + Sakura.css (no build step) |
| Real-time | Server-Sent Events (SSE) |
| GitHub Integration | `httpx` → GitHub REST API v3 |
| GitHub Webhooks | FastAPI endpoint receives push events |
| Email Digest | `smtplib` / `aiosmtplib` + APScheduler (Friday cron) |
| Teams Notifications | Microsoft Teams Incoming Webhook via `httpx` |
| Markdown Parsing | `mistune` + `python-frontmatter` |
| Auth | Bcrypt sessions (admin only) |
| Deployment | Docker (single container) |

---

## Project Structure

```text
.
├── app/
│   ├── main.py                   # FastAPI app, route registration
│   ├── db.py                     # SQLite schema and helpers
│   ├── config.py                 # Environment variable loading
│   ├── services/
│   │   ├── github_client.py      # GitHub API: verify, fetch, parse
│   │   ├── project_parser.py     # project.md structural parser (mistune)
│   │   ├── teams_notifier.py     # Teams webhook sender
│   │   ├── email_service.py      # Digest composer and sender
│   │   └── scheduler.py          # APScheduler job definitions
│   ├── static/
│   │   └── app.js                # μJS micro-library
│   └── templates/
│       ├── base.html
│       ├── index.html            # Landing + leaderboard
│       ├── projects.html         # Project directory
│       ├── project_detail.html   # Individual project page
│       ├── submit.html           # GitHub URL submission form
│       ├── faculty.html          # Faculty directory
│       ├── admin.html            # Admin panel
│       ├── admin_review.html     # Single submission review
│       └── terms.html
├── docs/                         # Specifications and UI/UX design documents
├── tests/                        # Test scripts (e.g. parser, sse tests)
├── Dockerfile                    # Standalone docker image definition
├── docker-compose.yml            # Portainer-ready compose file
├── requirements.txt
├── project_template.md           # The template users download from the website
└── README.md
```

---

## Environment Variables

```bash
# .env — never commit
SECRET_KEY=replace-with-random-string
DATABASE_PATH=./app.db

# GitHub
GITHUB_WEBHOOK_SECRET=replace-me  # Used to verify incoming push events
HOIISP_BASE_URL=https://hoiisp.habib.edu.pk

# Microsoft Teams
TEAMS_WEBHOOK_URL=https://...

# Note: SMTP configurations (Host, Port, User, Sender, Password) and 
# the Mailing List are now managed dynamically via the Admin Panel UI 
# and stored securely in the database.
```

---

## Getting Started (Local Development)

```bash
# 1. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in environment variables
cp .env.example .env

# 4. Start
uvicorn app.main:app --reload

# 5. Open
http://127.0.0.1:8000
```

Default admin account seeded on every run:
- Username: `admin`
- Password: `adminpass`

---

## Running with Docker (Portainer Ready)

```bash
docker compose up --build -d
```

The `docker-compose.yml` is pre-configured to mount a persistent volume (`hoiisp_data`) to `/app/data` inside the container. This ensures your SQLite database survives container updates and restarts.

All environment variables can be securely injected using Portainer's environment variable interface. No local `.env` file is required for Docker deployments.

---

## Main Routes

| Route | Description |
|---|---|
| `GET /` | Landing page + live leaderboard |
| `GET /projects` | Project directory (filterable) |
| `GET /projects/{slug}` | Individual project page |
| `GET /submit` | GitHub URL submission form (no login required) |
| `GET /faculty` | Faculty directory |
| `GET /admin` | Admin panel (admin login required) |
| `GET /terms` | Terms and conditions |
| `POST /api/submit` | Handles GitHub URL submission |
| `POST /api/webhook/github` | Receives GitHub push webhook events |
| `POST /api/admin/approve/{id}` | Admin approves a submission |
| `POST /api/admin/reject/{id}` | Admin rejects a submission |
| `GET /api/stream/leaderboard` | SSE stream for live leaderboard updates |
| `POST /api/admin/digest/preview` | Preview the next Friday digest |
| `POST /api/admin/digest/send-now` | Manually trigger digest send |

---

## Key Differences from V2

| Concern | V2 | V3 |
|---|---|---|
| How projects are submitted | `.md` file upload | GitHub repo URL |
| Student accounts | Required (email + password) | Not required — no student accounts |
| Source of truth | HOIISP database | Student's GitHub repo |
| File storage | Local `uploads/` directory | None — files stay in GitHub |
| Data freshness | Manual update posts | Auto-synced on each GitHub push |
| Notifications | Teams only | Teams + Friday email digest |
| Auth complexity | Four roles with session management | Admin accounts only |
| Parser trigger | Upload event | GitHub push webhook or manual sync |

---

## Known Limitations (V3 Pilot)

- GitHub commit email verification requires students to configure their Git client with their `@st.habib.edu.pk` email. Students using a personal GitHub email will fail verification until they add a Habib-email commit to the repo.
- Faculty endorsements are recorded manually by admin (no self-service faculty login).
- Email digest requires a working SMTP relay. For pilot, a shared Habib SMTP account is sufficient.
- No automated test suite committed yet.

---

## Documentation Files in This Repository

| File | Purpose |
|---|---|
| `project_template.md` | The template students copy into their GitHub repo as `project.md` |
| `docs/TermsAndConditionsV3.md` | Rendered at `/terms`; students agree at submission |
| `docs/WebsiteV3.md` | Full UX and page-by-page specification |
| `docs/IntegrationV3.md` | GitHub API, webhook, email digest, and Teams integration spec |
| `README.md` | This file |

## Contributers
- Basil Saeed Bari : bb09892@st.habib.edu.pk
