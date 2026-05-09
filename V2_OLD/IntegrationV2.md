```markdown
# Integration Specification  
## OIISP Platform — Ultra-Lightweight Edition  

**Document Version:** 2.0  
**Status:** Draft — Python/FastAPI Implementation Guide  
**Audience:** Developer / Platform Maintainer  
**Last Revised:** May 2026  

---

## 1. Overview

This document describes the integration architecture of the OIISP platform in its minimal, self‑contained form.  
It covers three primary integration concerns:

1. **The Markdown Ingest Pipeline** — How an uploaded `.md` proposal becomes a structured project entry in SQLite and on the leaderboard.  
2. **The Microsoft Teams Notification Engine** — How platform events push to a Teams channel using an incoming webhook.  
3. **The Auth Layer** — How users register and log in with local accounts (no external SSO).  

The guiding constraint is **extreme lightness**: every piece of infrastructure runs inside a single Python process with SQLite as the database. No separate database server, no message broker, no heavy frontend frameworks.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────┐
│           OIISP Server (FastAPI)             │
│                                              │
│  ┌───────────────┐  ┌──────────────────────┐ │
│  │  Jinja2       │  │  FastAPI Routes      │ │
│  │  Templates    │  │  /api/* , SSE        │ │
│  └───────┬───────┘  └──────────┬───────────┘ │
│          │                      │             │
│  ┌───────┴──────────────────────┴──────────┐ │
│  │           Services Layer                │ │
│  │  - markdown_parser.py (mistune)         │ │
│  │  - teams_notifier.py (httpx)            │ │
│  │  - auth.py (bcrypt + sessions)          │ │
│  └───────────┬─────────────────────────────┘ │
│              │                                │
│  ┌───────────┴────────────┐  ┌────────────┐  │
│  │   SQLite (app.db)      │  │  Uploads/   │  │
│  │   (projects, users,..) │  │  (file      │  │
│  └────────────────────────┘  │  storage)   │  │
│                              └────────────┘  │
└─────────────────────────────────────────────┘
         │                           ▲
         ▼                           │
  Microsoft Teams             Browser (μJS)
  Incoming Webhook            SSE + AJAX
```

- **Why SQLite?** Zero‑configuration, atomic, perfect for single‑server usage.  
- **Why local file storage?** Simple, no object storage overhead.  
- **Why SSE?** Trivial to implement with FastAPI’s streaming responses; μJS handles it natively.

---

## 3. Authentication (Local User Accounts)

No third‑party identity provider. All user management is internal.

### 3.1 Registration & Login
- `POST /api/auth/register` – accepts email, password, role (defaults to `student`). Password hashed with `bcrypt` via `passlib`.  
- `POST /api/auth/login` – verifies credentials, creates a session using Starlette’s `SessionMiddleware`.  
- Session secret stored in `SECRET_KEY` environment variable.  
- Users table stores `id`, `email` (unique), `password_hash`, `role` (`student`, `faculty`, `admin`, `technician`).  

No password resets via email are implemented (admin can manually reset). This keeps the stack minimal.

### 3.2 Role Protection
FastAPI dependencies check the session for role before allowing access to protected routes.  
```python
def require_role(role: str):
    async def dependency(request: Request):
        user = request.session.get("user")
        if not user or user["role"] != role:
            raise HTTPException(status_code=403)
        return user
    return dependency
```

---

## 4. Markdown Ingest Pipeline (Python)

### 4.1 Parsing Strategy
- **Library:** `mistune` (pure Python, fast).  
- **Frontmatter:** `python-frontmatter` extracts YAML if present.  
- **Section extraction:** Walk the mistune AST; identify headings by text and level. The required section map is identical to the original spec (see `ProposalFormat.md`).  
- **Table parsing:** Directly access `table` and `table_row` nodes in the AST, build list of dicts.  

### 4.2 Parser Module (`services/proposal_parser.py`)
```python
import mistune
from frontmatter import loads as fm_loads

REQUIRED_SECTIONS = {
    'project-title':          {'level': 1, 'dbField': 'title'},
    'team-members':           {'level': 2, 'dbField': 'team', 'type': 'table'},
    'abstract':               {'level': 2, 'dbField': 'abstract'},
    'problem-statement':      {'level': 2, 'dbField': 'problem_statement'},
    'domain--ieee-alignment': {'level': 2, 'dbField': 'domain_data', 'type': 'mixed'},
    'objectives':             {'level': 2, 'dbField': 'objectives', 'type': 'list'},
    'methodology':            {'level': 2, 'dbField': 'methodology'},
    'work-breakdown-structure-wbs': {'level': 2, 'dbField': 'milestones', 'type': 'table'},
    'resource-management-matrix':   {'level': 2, 'dbField': 'resources', 'type': 'table'},
    'success-metrics':        {'level': 2, 'dbField': 'success_metrics', 'type': 'table'},
    'declaration':            {'level': 2, 'dbField': 'declaration_checked', 'type': 'checkboxes'},
}

def parse_proposal(md_text: str):
    # Extract frontmatter if any, else just content
    post = fm_loads(md_text)
    content = post.content

    # Render to AST
    renderer = mistune.AstRenderer()
    markdown = mistune.Markdown(renderer)
    ast = markdown(content)

    sections = {}
    current_heading = None
    current_nodes = []

    for node in ast:
        if node['type'] == 'heading':
            if current_heading:
                sections[current_heading] = current_nodes
            raw_text = node['children'][0].get('raw', '') if node['children'] else ''
            current_heading = heading_to_slug(raw_text)
            current_nodes = [node]  # include heading node for later parsing
        else:
            if current_heading:
                current_nodes.append(node)
    if current_heading:
        sections[current_heading] = current_nodes

    # Derive title from H1
    title = extract_title(ast)

    validation = validate_sections(sections)

    return {
        'title': title,
        'sections': {k: {'level': REQUIRED_SECTIONS.get(k, {}).get('level'), 'nodes': v} for k, v in sections.items()},
        'validation': validation,
    }
```

### 4.3 Table & Content Extraction
- `parse_markdown_table(node)`: finds `table` node, iterates rows.  
- `extract_text(nodes)`: concatenates text from all children (skip headings).  
- These utilities are shared, DRY and live in the same module.

### 4.4 Proposal Ingestion API Route
```python
# POST /api/proposals/submit
async def submit_proposal(request: Request, file: UploadFile = File(...)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(401)

    content = await file.read()
    md_text = content.decode("utf-8")

    parsed = parse_proposal(md_text)
    if not parsed['validation']['valid']:
        return JSONResponse({"errors": parsed['validation']['errors']}, status_code=422)

    # Save file to uploads folder
    file_path = f"uploads/proposals/{user['id']}/{int(time.time())}-proposal.md"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # Insert project into SQLite (async)
    db = await get_db()
    # ... insert project, milestones, resource requests ...
    await db.commit()
    project_id = cursor.lastrowid

    # Send Teams notification (non-blocking)
    background_tasks.add_task(send_teams_notification, 'NEW_PROPOSAL', project)

    return JSONResponse({"projectId": project_id, "slug": slug}, status_code=201)
```

---

## 5. Microsoft Teams Integration

### 5.1 Webhook Setup
Same as original: configure an Incoming Webhook in a dedicated Teams channel, store the URL in `TEAMS_WEBHOOK_URL` environment variable.

### 5.2 Notification Service (`services/teams_notifier.py`)
```python
import httpx
import os

WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

EVENT_CARD_BUILDERS = {
    'NEW_PROPOSAL': build_new_proposal_card,
    'PROPOSAL_APPROVED': build_approved_card,
    # ... etc
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
            await client.post(WEBHOOK_URL, json=card)
        except Exception:
            logger.error("Teams notification failed", exc_info=True)
```
Adaptive Card templates remain as JSON. The call is always non‑blocking (using FastAPI’s background tasks).

> **Design Principle:** A failed Teams post must **never** impact the main operation.

---

## 6. Database Schema (SQLite)

All tables use SQLite’s type system (`INTEGER PRIMARY KEY`, `TEXT` for timestamps as ISO‑8601).

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('student','faculty','admin','technician')),
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE projects (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    slug             TEXT UNIQUE NOT NULL,
    title            TEXT NOT NULL,
    abstract         TEXT,
    problem_statement TEXT,
    domain           TEXT,
    methodology      TEXT,
    status           TEXT DEFAULT 'pending_review',
    submitted_by     INTEGER REFERENCES users(id),
    file_path        TEXT,   -- relative path to uploaded .md
    created_at       TEXT DEFAULT (datetime('now')),
    approved_at      TEXT,
    completed_at     TEXT
);

CREATE TABLE milestones (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    number       INTEGER,
    name         TEXT,
    deliverables TEXT,
    start_date   TEXT,
    end_date     TEXT,
    actual_end_date TEXT,
    status       TEXT DEFAULT 'Not Started'
);

-- team_members, resource_requests, project_updates, endorsements, lab_session_logs
-- follow the same lightweight structure (TEXT for dates).
```

---

## 7. Environment Variables

```bash
# .env (never commit)
SECRET_KEY=change-me-to-a-random-string
TEAMS_WEBHOOK_URL=https://...
DATABASE_PATH=./app.db
UPLOAD_DIR=./uploads
```
No Azure AD keys, no MinIO credentials.

---

## 8. Deployment

A single Docker container is enough. The `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /code/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

Mount a volume for `app.db` and `uploads/` for persistence. No other services needed.

---

## 9. Future Integrations (unchanged concept, but minimal)

| Integration | Complexity |
|-------------|------------|
| GitHub webhooks to update repo-linked projects | Low |
| ORCID / DOI archival | Medium |
| Power Automate triggers | Low |

---

```