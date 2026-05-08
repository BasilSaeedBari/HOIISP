# Open Innovation & Independent Study Platform (OIISP)

A lightweight FastAPI prototype for managing student innovation projects at Habib University.  
This platform lets students submit structured markdown proposals, enables admin review, supports faculty endorsements, and provides a live public project leaderboard.

## Vision and Intention

OIISP is designed to support independent, student-led technical projects with clear governance:

- make project discovery and progress visible
- keep proposal quality standardized and reviewable
- connect student teams with faculty support
- track milestones, resource needs, and activity updates
- preserve a lightweight deployment model for pilot use

## Current Implementation (What is already built)

- FastAPI backend with server-rendered Jinja templates
- SQLite persistence via `aiosqlite`
- session-based authentication and role-based access control
- markdown proposal ingestion with structural validation
- admin decision flow for approvals/rejections
- project updates (with optional image upload)
- endorsement system (`star`, `vouch`, `endorse`)
- live leaderboard refresh using SSE (`/api/stream/leaderboard`)
- optional Microsoft Teams webhook notifications
- Docker and Docker Compose support

## User Roles

- `student`: can submit proposals and interact as authenticated user
- `faculty`: can endorse projects and appears in faculty directory
- `admin`: can review pending proposals and approve/reject
- `technician`: role defined and available for access control extension

## Core Features

- **Proposal upload and validation**
  - accepts `.md` files only
  - validates required sections, abstract length, team rows, milestones, and declaration checkboxes
  - parses and stores title, abstract, domain, methodology, objectives, team, milestones, resources, and metrics
- **Project pages**
  - auto-generated from approved proposal data
  - include team, milestones, resources, endorsements, and timeline updates
- **Directories**
  - `/projects` with filtering/sorting
  - `/faculty` with expertise and endorsement activity stats
- **Leaderboard**
  - landing page leaderboard updates in real time with SSE
  - displays active project count, endorsements, and total requested lab hours
- **Admin moderation**
  - proposal queue at `/admin`
  - approve/reject decisions with optional notes
- **Teams notifications**
  - async webhook events for new submissions, approvals, milestone completions, and faculty endorsements
  - failures are logged and do not block app actions

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Jinja2 templates + vanilla JavaScript
- SQLite + `aiosqlite`
- `passlib[bcrypt]` for password hashing
- `mistune` + `python-frontmatter` for markdown parsing
- `httpx` for Teams webhook calls

## Project Structure

```text
.
|-- app/
|   |-- main.py
|   |-- auth.py
|   |-- db.py
|   |-- config.py
|   |-- services/
|   |   |-- proposal_parser.py
|   |   `-- teams_notifier.py
|   |-- static/
|   |   `-- app.js
|   `-- templates/
|       |-- base.html
|       |-- index.html
|       |-- projects.html
|       |-- project_detail.html
|       |-- submit.html
|       |-- faculty.html
|       |-- admin.html
|       |-- auth.html
|       `-- terms.html
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- ProposalFormat.md
|-- TermsAndConditions.md
|-- Website.md
|-- WebsiteV2.md
|-- Integration.md
|-- IntegrationV2.md
`-- README.md
```

## Documentation in Repository

- `ProposalFormat.md`: canonical markdown proposal format expected by parser
- `TermsAndConditions.md`: rendered at `/terms`
- `Website.md` and `WebsiteV2.md`: product/UX specification docs
- `Integration.md` and `IntegrationV2.md`: architecture and integration specs

## Getting Started (Local Development)

1. Create and activate a Python virtual environment (Python 3.11+).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables:

```bash
SECRET_KEY=replace-me
TEAMS_WEBHOOK_URL=
DATABASE_PATH=./app.db
UPLOAD_DIR=./uploads
```

4. Start the app:

```bash
uvicorn app.main:app --reload
```

5. Open:

`http://127.0.0.1:8000`

## Running with Docker

```bash
docker compose up --build
```

The app will be available at `http://127.0.0.1:8000` and uses a persistent Docker volume (`hoiisp_data`) for DB and uploads.

## Default Admin Account (Seeded on First Startup)

- email: `admin@hoiisp.local`
- password: `admin123`

Change this immediately for any shared or production-like environment.

## Main Routes

- `GET /` landing page + live leaderboard
- `GET /projects` project directory
- `GET /projects/{slug}` project detail page
- `GET /submit` proposal submission page (`student` role)
- `GET /faculty` faculty directory
- `GET /admin` admin review panel (`admin` role)
- `GET /auth` login/registration page
- `GET /terms` renders terms markdown

Key API endpoints include:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/proposals/submit`
- `POST /api/projects/{slug}/endorse`
- `POST /api/projects/{slug}/updates`
- `POST /api/admin/proposals/{project_id}/decision`
- `GET /api/stream/leaderboard`

## Proposal Format Requirements

Uploaded markdown proposals are expected to follow the structure in `ProposalFormat.md`, including required sections such as:

- project title
- team members table
- abstract
- problem statement
- domain and IEEE alignment
- objectives
- methodology
- WBS table
- resource matrix
- success metrics
- declaration checkboxes

## Data and Storage Notes

- SQLite database path is configurable via `DATABASE_PATH`
- uploads are stored under `UPLOAD_DIR` (proposal files and update images)
- static files are served from `app/static`
- terms page content is loaded from `TermsAndConditions.md`

## Known Scope of This Prototype

- no CI/CD pipeline configured yet
- no automated test suite committed yet
- no distributed background worker (notifications run as FastAPI background tasks)
- not yet hardened for production security/compliance requirements

## Suggested Next Steps

- add automated tests for parser, auth, and proposal lifecycle
- add DB migrations/versioning
- enforce stronger password policy and account verification
- add richer admin workflows (bulk actions, audit trail)
- instrument app observability (structured logs, metrics, health checks)
