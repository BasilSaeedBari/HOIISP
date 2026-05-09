# Integration Specification
## HOIISP Platform — GitHub-Synced Edition

**Document Version:** 3.0  
**Status:** Draft — Python/FastAPI Implementation Guide  
**Audience:** Developer / Platform Maintainer  
**Last Revised:** May 2026

---

## 1. Overview

This document describes every external integration in the HOIISP V3 platform.

There are four:

1. **GitHub Integration** — Verifying Habib affiliation via commit emails, fetching and parsing `project.md`, and receiving push webhooks to keep data current.
2. **Microsoft Teams Notification Engine** — Pushing event cards to a Teams channel via an incoming webhook.
3. **Friday Email Digest** — A weekly automated email summarising platform activity, sent to a configured recipient list every Friday morning.
4. **Auth Layer** — Admin-only session auth. No student accounts.

The guiding constraint is the same as V2: **extreme lightness**. Everything runs inside a single Python process with SQLite. The new constraint added in V3: **HOIISP never asks students to create accounts or upload files**. All student-side data flow goes through GitHub.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  HOIISP Server (FastAPI)                  │
│                                                          │
│  ┌─────────────────┐   ┌──────────────────────────────┐  │
│  │  Jinja2          │   │  FastAPI Routes               │  │
│  │  Templates       │   │  /api/*, /admin/*, SSE        │  │
│  └────────┬────────┘   └──────────────┬───────────────┘  │
│           │                            │                  │
│  ┌────────┴────────────────────────────┴──────────────┐  │
│  │                  Services Layer                     │  │
│  │  github_client.py   — GitHub API calls              │  │
│  │  project_parser.py  — mistune AST parser            │  │
│  │  teams_notifier.py  — Teams webhook sender          │  │
│  │  email_digest.py    — Digest composer & sender      │  │
│  │  scheduler.py       — APScheduler (Friday cron)     │  │
│  └────────┬──────────────────────────────────────────┘  │
│           │                                               │
│  ┌────────┴──────────────┐  ┌────────────────────────┐   │
│  │  SQLite (app.db)       │  │  No uploads folder     │   │
│  │  projects, admin, etc. │  │  (files stay on GitHub)│   │
│  └───────────────────────┘  └────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
        │               │                      ▲
        ▼               ▼                      │
  Microsoft Teams   SMTP Server          GitHub REST API
  Incoming Webhook  (Friday digest)      (verify + fetch)
                                               ▲
                                               │
                                    Student's GitHub Repo
                                    (push webhook → HOIISP)
```

---

## 3. GitHub Integration

This is the core new integration in V3. It has three distinct responsibilities:

- **Verification** — Confirm the repo belongs to a Habib student.
- **Fetch & Parse** — Read `project.md` from the repo and extract structured data.
- **Webhook Sync** — React to push events to keep data current without polling.

### 3.1 GitHub Personal Access Token

HOIISP uses a single GitHub PAT (Personal Access Token) with the following scopes:
- `public_repo` — read access to public repository content and commit history
- `read:user` — read public user profile data (email, if public)

Store as `GITHUB_TOKEN` environment variable. All API calls include `Authorization: Bearer {GITHUB_TOKEN}`.

Without a token, GitHub's unauthenticated rate limit is 60 requests/hour. With a PAT, it is 5,000 requests/hour — sufficient for the pilot scale.

### 3.2 Habib Affiliation Verification

**Strategy: Commit Email Scan**

HOIISP checks whether any commit in the repository's default branch was authored with a `@st.habib.edu.pk` email address. This approach is:
- Reliable: Git commit emails are set in the developer's local config and are embedded in every commit object.
- Non-invasive: does not require students to make their GitHub profile email public.
- Auditable: the specific commit(s) that passed verification are stored in the database.

**Implementation (`services/github_client.py`):**

```python
import httpx
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
HABIB_STUDENT_DOMAIN = "@st.habib.edu.pk"

async def verify_habib_affiliation(owner: str, repo: str) -> dict:
    """
    Scan up to 100 commits on the default branch.
    Return the first commit found with a @st.habib.edu.pk author email.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": 100}

    async with httpx.AsyncClient(headers=HEADERS) as client:
        response = await client.get(url, params=params)

    if response.status_code == 404:
        return {"verified": False, "reason": "Repository not found or is private."}
    if response.status_code != 200:
        return {"verified": False, "reason": f"GitHub API error: {response.status_code}"}

    commits = response.json()
    for commit in commits:
        author_email = commit.get("commit", {}).get("author", {}).get("email", "")
        committer_email = commit.get("commit", {}).get("committer", {}).get("email", "")
        for email in [author_email, committer_email]:
            if email.lower().endswith(HABIB_STUDENT_DOMAIN):
                return {
                    "verified": True,
                    "matching_email": email,
                    "matching_commit_sha": commit["sha"],
                    "matching_commit_date": commit["commit"]["author"]["date"],
                }

    return {
        "verified": False,
        "reason": (
            f"No commit found with a {HABIB_STUDENT_DOMAIN} author email in the last "
            f"{len(commits)} commits. Ensure your Git client is configured with your "
            f"Habib email: git config user.email 'name@st.habib.edu.pk'"
        ),
    }
```

**Important:** If a repo has more than 100 commits and no Habib email is found in the first page, HOIISP returns a soft failure with a note suggesting the student add a new commit with the correct email configured. Scanning all commits for large repos is not cost-effective at pilot scale.

### 3.3 Fetching and Parsing `project.md`

**Fetch:**

```python
async def fetch_project_md(owner: str, repo: str) -> str | None:
    """
    Fetch the raw content of project.md from the repo root on the default branch.
    Returns the decoded string content, or None if not found.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/project.md"
    async with httpx.AsyncClient(headers=HEADERS) as client:
        response = await client.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    import base64
    return base64.b64decode(data["content"]).decode("utf-8")
```

**Parse** (identical section-extraction logic from V2, adapted for new `project.md` structure):

The parser in `services/project_parser.py` uses `mistune` with an AST renderer and `python-frontmatter`. The required section map is updated for V3:

```python
REQUIRED_SECTIONS = {
    'project-title':                {'level': 1, 'dbField': 'title'},
    'github-repository':            {'level': 2, 'dbField': 'github_url'},
    'team-members':                 {'level': 2, 'dbField': 'team', 'type': 'table'},
    'abstract':                     {'level': 2, 'dbField': 'abstract'},
    'problem-statement':            {'level': 2, 'dbField': 'problem_statement'},
    'domain--ieee-alignment':       {'level': 2, 'dbField': 'domain_data', 'type': 'mixed'},
    'objectives':                   {'level': 2, 'dbField': 'objectives', 'type': 'list'},
    'methodology':                  {'level': 2, 'dbField': 'methodology'},
    'work-breakdown-structure-wbs': {'level': 2, 'dbField': 'milestones', 'type': 'table'},
    'resource-management-matrix':   {'level': 2, 'dbField': 'resources', 'type': 'table'},
    'success-metrics':              {'level': 2, 'dbField': 'success_metrics', 'type': 'table'},
    'declaration':                  {'level': 2, 'dbField': 'declaration_checked', 'type': 'checkboxes'},
}
```

**Validation rules:**
- Abstract must be at least 150 words.
- Team table must have at least 1 and at most 4 data rows.
- All required declaration checkboxes must be `[x]` (checked).
- WBS table must have at least 3 milestone rows.
- Success metrics table must have at least 3 rows.
- A repo URL matching `github.com/...` must be present in the GitHub Repository section.

### 3.4 GitHub Push Webhook

When a project is approved, HOIISP registers a webhook on the student's repository (using the GitHub API, with the admin's token). This webhook fires on `push` events and calls `POST /api/webhook/github` on the HOIISP server.

**Webhook Registration:**

```python
async def register_webhook(owner: str, repo: str, hoiisp_base_url: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
    payload = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": f"{hoiisp_base_url}/api/webhook/github",
            "content_type": "json",
            "secret": os.getenv("GITHUB_WEBHOOK_SECRET"),
            "insecure_ssl": "0",
        },
    }
    async with httpx.AsyncClient(headers=HEADERS) as client:
        await client.post(url, json=payload)
```

**Webhook Receiver:**

```python
# POST /api/webhook/github
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    # Verify HMAC signature
    secret = os.getenv("GITHUB_WEBHOOK_SECRET").encode()
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401)

    payload = await request.json()
    repo_full_name = payload.get("repository", {}).get("full_name")  # "owner/repo"
    pusher = payload.get("pusher", {}).get("name")
    ref = payload.get("ref")  # "refs/heads/main"

    # Only sync on pushes to the default branch
    if ref not in ("refs/heads/main", "refs/heads/master"):
        return {"status": "ignored"}

    # Queue a background re-sync for this project
    background_tasks.add_task(sync_project_from_github, repo_full_name)
    return {"status": "queued"}
```

**Sync task:**

```python
async def sync_project_from_github(repo_full_name: str):
    owner, repo = repo_full_name.split("/", 1)
    project = await db.get_project_by_repo(repo_full_name)
    if not project:
        return

    md_text = await fetch_project_md(owner, repo)
    if not md_text:
        return

    parsed = parse_project_md(md_text)
    last_push = await get_last_push_timestamp(owner, repo)

    await db.update_project_from_parse(project["id"], parsed, last_push)
    # Broadcast updated leaderboard HTML to all SSE clients
    await broadcast_leaderboard_update()
    # Check for milestone status changes → Teams notification
    await check_and_notify_milestone_changes(project, parsed)
```

**Design Principle:** A webhook failure must never crash the main server. All sync work runs as a FastAPI background task. If `project.md` has become malformed after a push, HOIISP logs the parse errors and keeps the last valid data, flagging the project with a `sync_warning` badge in the admin panel.

### 3.5 Fetching Recent Commits for Project Pages

The project detail page displays the last 5 commits. These are fetched from GitHub at page-render time with a short in-memory cache (60-second TTL) to avoid hammering the API on repeated page loads.

```python
async def get_recent_commits(owner: str, repo: str, count: int = 5) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": count}
    async with httpx.AsyncClient(headers=HEADERS) as client:
        response = await client.get(url, params=params)
    if response.status_code != 200:
        return []
    return [
        {
            "sha": c["sha"][:7],
            "message": c["commit"]["message"].split("\n")[0],  # first line only
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
            "url": c["html_url"],
        }
        for c in response.json()
    ]
```

---

## 4. Microsoft Teams Integration

### 4.1 Webhook Setup

Same as V2. Create an Incoming Webhook in a dedicated HOIISP Teams channel. Store the URL in `TEAMS_WEBHOOK_URL`.

### 4.2 Event Types and When They Fire

| Event | Trigger |
|---|---|
| `NEW_SUBMISSION` | A GitHub URL is submitted and passes instant verification |
| `SUBMISSION_APPROVED` | Admin approves a submission |
| `SUBMISSION_REJECTED` | Admin rejects a submission |
| `MILESTONE_COMPLETE` | A milestone's status changes to `Complete` during a sync |
| `PROJECT_STALE` | A project has had no GitHub push in 14 days (checked daily) |
| `ENDORSEMENT_ADDED` | Admin records a faculty endorsement |

### 4.3 Notification Service (`services/teams_notifier.py`)

```python
import httpx, os

WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

EVENT_CARD_BUILDERS = {
    'NEW_SUBMISSION':      build_new_submission_card,
    'SUBMISSION_APPROVED': build_approved_card,
    'SUBMISSION_REJECTED': build_rejected_card,
    'MILESTONE_COMPLETE':  build_milestone_card,
    'PROJECT_STALE':       build_stale_card,
    'ENDORSEMENT_ADDED':   build_endorsement_card,
}

async def send_teams_notification(event_type: str, data: dict):
    if not WEBHOOK_URL:
        return
    build = EVENT_CARD_BUILDERS.get(event_type)
    if not build:
        return
    card = build(data)
    async with httpx.AsyncClient() as client:
        try:
            await client.post(WEBHOOK_URL, json=card, timeout=5.0)
        except Exception:
            logger.error("Teams notification failed", exc_info=True)
```

All Teams calls are non-blocking (FastAPI background tasks). A failed Teams post never impacts the main operation.

---

## 5. Friday Email Digest

### 5.1 Purpose

Every Friday morning, HOIISP sends a plain-HTML digest email to a configurable recipient list (faculty mailing list, HOIISP admin, lab technicians). The digest provides a structured weekly summary without requiring anyone to visit the platform.

### 5.2 Digest Content

The digest covers the past 7 days and contains:

**Section 1 — New Projects This Week**  
Newly approved projects: title, domain, team, GitHub link, one-sentence abstract summary.

**Section 2 — Milestone Completions**  
Projects that marked a milestone as `Complete` during the week. Project name, milestone name, GitHub repo link.

**Section 3 — Active Projects Summary**  
Total count of active projects, breakdown by domain.

**Section 4 — Stale Projects (Warning)**  
Projects with no GitHub push in 14 days. Project name, last push date, days stale. Encourages faculty to follow up with students.

**Section 5 — Newly Completed Projects**  
Projects whose final milestone is now `Complete`. Full project summary with GitHub repo link.

**Section 6 — Platform Stats**  
Active project count, total endorsements, total lab hours requested across all projects.

### 5.3 Email Composer (`services/email_digest.py`)

```python
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
import os
from datetime import date, timedelta

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
DIGEST_RECIPIENTS = os.getenv("DIGEST_RECIPIENTS", "").split(",")

env = Environment(loader=FileSystemLoader("app/templates/email"))

async def compose_and_send_digest():
    since = date.today() - timedelta(days=7)
    db = await get_db()

    data = {
        "week_ending": date.today().strftime("%d %B %Y"),
        "new_projects":   await db.get_projects_approved_since(since),
        "milestones_done": await db.get_milestones_completed_since(since),
        "active_count":   await db.count_active_projects(),
        "stale_projects": await db.get_stale_projects(days=14),
        "completed_projects": await db.get_projects_completed_since(since),
        "stats":          await db.get_platform_stats(),
    }

    html_body = env.get_template("digest.html").render(**data)
    plain_body = env.get_template("digest_plain.txt").render(**data)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"HOIISP Weekly Digest — {data['week_ending']}"
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(DIGEST_RECIPIENTS)
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
        start_tls=True,
    )
    await db.log_digest_sent(date.today())
```

### 5.4 Scheduler (`services/scheduler.py`)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import os

DIGEST_DAY  = os.getenv("DIGEST_SEND_DAY", "friday")
DIGEST_TIME = os.getenv("DIGEST_SEND_TIME", "08:00")
hour, minute = map(int, DIGEST_TIME.split(":"))

def start_scheduler():
    scheduler = AsyncIOScheduler()

    # Friday digest
    scheduler.add_job(
        compose_and_send_digest,
        CronTrigger(day_of_week=DIGEST_DAY[:3].lower(), hour=hour, minute=minute),
        id="friday_digest",
        replace_existing=True,
    )

    # Daily stale-project check (fires at 09:00 every day)
    scheduler.add_job(
        check_stale_projects_and_notify,
        CronTrigger(hour=9, minute=0),
        id="stale_check",
        replace_existing=True,
    )

    # Hourly: re-sync any project whose webhook has not fired in 24 hours (fallback polling)
    scheduler.add_job(
        poll_missed_projects,
        CronTrigger(minute=0),
        id="fallback_poll",
        replace_existing=True,
    )

    scheduler.start()
    return scheduler
```

The scheduler is started inside FastAPI's `lifespan` context manager so it shuts down cleanly.

---

## 6. Database Schema (SQLite)

```sql
CREATE TABLE admin_users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE submissions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    github_url          TEXT NOT NULL,
    repo_owner          TEXT NOT NULL,
    repo_name           TEXT NOT NULL,
    lead_email          TEXT NOT NULL,           -- stored only for admin contact
    verification_status TEXT NOT NULL,           -- 'pending','verified','failed'
    verification_detail TEXT,                    -- JSON: matching email, sha, date
    parse_status        TEXT NOT NULL,           -- 'ok','warnings','errors'
    parse_report        TEXT,                    -- JSON: section-by-section report
    status              TEXT DEFAULT 'pending',  -- 'pending','approved','rejected'
    admin_notes         TEXT,
    submitted_at        TEXT DEFAULT (datetime('now')),
    reviewed_at         TEXT
);

CREATE TABLE projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id       INTEGER REFERENCES submissions(id),
    slug                TEXT UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    github_url          TEXT NOT NULL,
    repo_owner          TEXT NOT NULL,
    repo_name           TEXT NOT NULL,
    abstract            TEXT,
    problem_statement   TEXT,
    domain              TEXT,
    sub_field           TEXT,
    ieee_society        TEXT,
    methodology         TEXT,
    status              TEXT DEFAULT 'active',   -- 'active','completed','archived'
    last_push_at        TEXT,
    last_sync_at        TEXT,
    sync_warning        TEXT,                    -- null or description of parse error after push
    approved_at         TEXT,
    completed_at        TEXT,
    webhook_id          INTEGER                  -- GitHub webhook ID for removal on archive
);

CREATE TABLE team_members (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    full_name       TEXT,
    student_id      TEXT,
    github_username TEXT,
    habib_email     TEXT,
    program         TEXT,
    year            TEXT,
    role            TEXT
);

CREATE TABLE milestones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    number          INTEGER,
    name            TEXT,
    deliverables    TEXT,
    start_date      TEXT,
    end_date        TEXT,
    status          TEXT DEFAULT 'Not Started',
    completed_at    TEXT                         -- set when status changes to Complete
);

CREATE TABLE resources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    resource_name   TEXT,
    lab_location    TEXT,
    estimated_hours REAL,
    purpose         TEXT,
    required_from   TEXT,
    required_until  TEXT
);

CREATE TABLE success_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    metric_text     TEXT,
    target_value    TEXT,
    measurement_method TEXT
);

CREATE TABLE endorsements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    faculty_name    TEXT,
    faculty_dept    TEXT,
    endorsement_type TEXT,                       -- 'star','vouch','endorse'
    quote           TEXT,
    recorded_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE faculty (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    title           TEXT,
    department      TEXT,
    email           TEXT,
    expertise_tags  TEXT                         -- JSON array of strings
);

CREATE TABLE digest_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sent_at     TEXT DEFAULT (datetime('now')),
    recipient_count INTEGER,
    status      TEXT                             -- 'sent','failed'
);

CREATE TABLE webhook_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_full_name TEXT,
    received_at TEXT DEFAULT (datetime('now')),
    ref         TEXT,
    pusher      TEXT,
    sync_result TEXT                             -- 'ok','parse_error','not_found'
);
```

---

## 7. Environment Variables

```bash
# .env — never commit
SECRET_KEY=change-me-to-a-random-string
DATABASE_PATH=./app.db

# GitHub
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=change-me
HOIISP_BASE_URL=https://hoiisp.habib.edu.pk    # used when registering webhooks

# Microsoft Teams
TEAMS_WEBHOOK_URL=https://...

# Email Digest
SMTP_HOST=smtp.habib.edu.pk
SMTP_PORT=587
SMTP_USER=hoiisp@habib.edu.pk
SMTP_PASSWORD=...
DIGEST_RECIPIENTS=faculty-list@habib.edu.pk,admin@habib.edu.pk
DIGEST_SEND_DAY=friday
DIGEST_SEND_TIME=08:00
```

---

## 8. Deployment

Same single-container Docker model as V2. No additional services.

```dockerfile
FROM python:3.11-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /code/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

Mount a volume for `app.db` only. No uploads directory needed.

```yaml
# docker-compose.yml
services:
  hoiisp:
    build: .
    ports:
      - "80:80"
    volumes:
      - hoiisp_data:/code/app.db_dir
    env_file:
      - .env
volumes:
  hoiisp_data:
```

---

## 9. Python Requirements

```text
fastapi
uvicorn[standard]
aiosqlite
jinja2
mistune
python-frontmatter
httpx
passlib[bcrypt]
itsdangerous          # Starlette SessionMiddleware
APScheduler
aiosmtplib
python-dotenv
```

---

## 10. Key Design Principles

| Principle | Implementation |
|---|---|
| GitHub is source of truth | HOIISP never allows editing project data through its UI |
| Webhook-first, polling as fallback | Push webhooks trigger immediate syncs; hourly cron catches missed events |
| Failed integrations never block | Teams posts and email sends run as background tasks; errors are logged, not raised |
| No student accounts | The only credentials in the system are admin passwords |
| Staleness is visible | Projects with no push in 14 days are flagged on leaderboard and in the digest |
| Admin is the trust gate | All endorsements, stars, and approvals go through admin — no self-service for faculty |

---

## 11. Future Integrations

| Integration | Complexity | Notes |
|---|---|---|
| GitHub Actions status badge on project page | Low | Fetch workflow run status via API |
| ORCID / DOI archival for completed projects | Medium | On project completion, mint a DOI via Zenodo API |
| Power Automate triggers for lab technicians | Low | POST to a Power Automate HTTP trigger on resource request |
| Slack digest alternative | Low | Same composer, different sender |
| GitHub Discussions as update comments | Medium | Thread discussions on the repo's Discussions tab |
