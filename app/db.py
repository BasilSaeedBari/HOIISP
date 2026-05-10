import aiosqlite
import json
from .config import DATABASE_PATH
import bcrypt
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

def verify_password(plain_password, hashed_password):
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password, salt).decode('utf-8')

SCHEMA = """
CREATE TABLE IF NOT EXISTS admin_users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS submissions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    github_url          TEXT NOT NULL,
    repo_owner          TEXT NOT NULL,
    repo_name           TEXT NOT NULL,
    lead_email          TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    verification_detail TEXT,
    parse_status        TEXT NOT NULL,
    parse_report        TEXT,
    status              TEXT DEFAULT 'pending',
    admin_notes         TEXT,
    submitted_at        TEXT DEFAULT (datetime('now')),
    reviewed_at         TEXT
);

CREATE TABLE IF NOT EXISTS projects (
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
    status              TEXT DEFAULT 'active',
    last_push_at        TEXT,
    last_sync_at        TEXT,
    sync_warning        TEXT,
    approved_at         TEXT,
    completed_at        TEXT,
    webhook_id          INTEGER
);

CREATE TABLE IF NOT EXISTS team_members (
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

CREATE TABLE IF NOT EXISTS milestones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    number          INTEGER,
    name            TEXT,
    deliverables    TEXT,
    start_date      TEXT,
    end_date        TEXT,
    status          TEXT DEFAULT 'Not Started',
    completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS resources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    resource_name   TEXT,
    lab_location    TEXT,
    estimated_hours REAL,
    purpose         TEXT,
    required_from   TEXT,
    required_until  TEXT
);

CREATE TABLE IF NOT EXISTS success_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    metric_text     TEXT,
    target_value    TEXT,
    measurement_method TEXT
);

CREATE TABLE IF NOT EXISTS endorsements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    faculty_name    TEXT,
    faculty_dept    TEXT,
    endorsement_type TEXT,
    quote           TEXT,
    recorded_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS faculty (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    title           TEXT,
    department      TEXT,
    email           TEXT,
    expertise_tags  TEXT
);

CREATE TABLE IF NOT EXISTS digest_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sent_at     TEXT DEFAULT (datetime('now')),
    recipient_count INTEGER,
    status      TEXT
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_full_name TEXT,
    received_at TEXT DEFAULT (datetime('now')),
    ref         TEXT,
    pusher      TEXT,
    sync_result TEXT
);
"""

async def get_db():
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON;")
    return db

async def init_db():
    db = await get_db()
    await db.executescript(SCHEMA)
    
    # Seed admin user if none exists
    cursor = await db.execute("SELECT COUNT(*) FROM admin_users")
    count = (await cursor.fetchone())[0]
    if count == 0:
        hashed = get_password_hash("admin123")
        await db.execute(
            "INSERT INTO admin_users (email, password_hash) VALUES (?, ?)",
            ("admin@hoiisp.local", hashed)
        )
        print("WARNING: Seeded default admin account (admin@hoiisp.local / admin123). Change immediately.")
    
    await db.commit()
    await db.close()

# --- Helper DB functions for phase 1 ---

async def get_admin_user(email: str):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM admin_users WHERE email = ?", (email,))
    user = await cursor.fetchone()
    await db.close()
    return user

async def create_submission(github_url, owner, repo, lead_email, verify_status, verify_detail, parse_status, parse_report):
    db = await get_db()
    cursor = await db.execute(
        '''INSERT INTO submissions (github_url, repo_owner, repo_name, lead_email, verification_status, verification_detail, parse_status, parse_report)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (github_url, owner, repo, lead_email, verify_status, json.dumps(verify_detail), parse_status, json.dumps(parse_report))
    )
    await db.commit()
    submission_id = cursor.lastrowid
    await db.close()
    return submission_id

async def get_all_submissions():
    db = await get_db()
    cursor = await db.execute("SELECT * FROM submissions ORDER BY submitted_at DESC")
    subs = await cursor.fetchall()
    await db.close()
    return [dict(s) for s in subs]

async def get_submission(submission_id: int):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
    sub = await cursor.fetchone()
    await db.close()
    return dict(sub) if sub else None

async def update_submission_status(submission_id: int, status: str, admin_notes: str = None):
    db = await get_db()
    await db.execute("UPDATE submissions SET status = ?, admin_notes = ?, reviewed_at = datetime('now') WHERE id = ?", (status, admin_notes, submission_id))
    await db.commit()
    await db.close()

def generate_slug(title: str):
    import re
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip().lower()
    return re.sub(r'[\s-]+', '-', slug)

async def create_project_from_submission(submission: dict, parsed_data: dict, last_push_at: str):
    db = await get_db()
    slug_base = generate_slug(parsed_data.get("title", "project"))
    slug = slug_base
    counter = 1
    while True:
        cursor = await db.execute("SELECT id FROM projects WHERE slug = ?", (slug,))
        if not await cursor.fetchone():
            break
        slug = f"{slug_base}-{counter}"
        counter += 1

    domain_data = parsed_data.get('domain_data', {})
    
    cursor = await db.execute(
        '''INSERT INTO projects (submission_id, slug, title, github_url, repo_owner, repo_name, abstract, problem_statement, domain, sub_field, ieee_society, methodology, last_push_at, approved_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))''',
        (submission['id'], slug, parsed_data.get('title'), submission['github_url'], submission['repo_owner'], submission['repo_name'],
         parsed_data.get('abstract'), parsed_data.get('problem_statement'), domain_data.get('domain'), domain_data.get('sub_field'), domain_data.get('ieee_society'),
         parsed_data.get('methodology'), last_push_at)
    )
    project_id = cursor.lastrowid

    for member in parsed_data.get('team', []):
        await db.execute(
            "INSERT INTO team_members (project_id, full_name, student_id, github_username, habib_email, program, year, role) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, member.get('Full Name'), member.get('Student ID'), member.get('GitHub Username'), member.get('Habib Email'), member.get('Program'), member.get('Year'), member.get('Role'))
        )

    for m in parsed_data.get('milestones', []):
        await db.execute(
            "INSERT INTO milestones (project_id, number, name, deliverables, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, m.get('Milestone #'), m.get('Milestone Name'), m.get('Key Deliverables'), m.get('Start Date'), m.get('End Date'), m.get('Status', 'Not Started'))
        )
    
    for r in parsed_data.get('resources', []):
        await db.execute(
            "INSERT INTO resources (project_id, resource_name, lab_location, estimated_hours, purpose, required_from, required_until) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, r.get('Resource'), r.get('Lab / Location'), r.get('Estimated Hours'), r.get('Purpose in Project'), r.get('Required From'), r.get('Required Until'))
        )
        
    for m in parsed_data.get('success_metrics', []):
        await db.execute(
            "INSERT INTO success_metrics (project_id, metric_text, target_value, measurement_method) VALUES (?, ?, ?, ?)",
            (project_id, m.get('Metric', ''), m.get('Target Value'), m.get('Measurement Method'))
        )

    await db.commit()
    await db.close()
    return project_id

async def get_projects(domain: str = None, status: str = None, sort: str = "stars"):
    db = await get_db()
    query = "SELECT projects.*, (SELECT COUNT(*) FROM endorsements WHERE project_id = projects.id AND endorsement_type='star') as stars FROM projects WHERE 1=1"
    params = []
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    if status:
        query += " AND status = ?"
        params.append(status)
        
    if sort == "stars":
        query += " ORDER BY stars DESC"
    elif sort == "recent":
        query += " ORDER BY last_push_at DESC"
    else:
        query += " ORDER BY approved_at DESC"
        
    cursor = await db.execute(query, params)
    projects = await cursor.fetchall()
    
    res = []
    for p in projects:
        d = dict(p)
        c2 = await db.execute("SELECT COUNT(*) FROM milestones WHERE project_id=?", (d['id'],))
        total_m = (await c2.fetchone())[0]
        c3 = await db.execute("SELECT COUNT(*) FROM milestones WHERE project_id=? AND status='Complete'", (d['id'],))
        comp_m = (await c3.fetchone())[0]
        d['total_milestones'] = total_m
        d['completed_milestones'] = comp_m
        c4 = await db.execute("SELECT COUNT(*) FROM team_members WHERE project_id=?", (d['id'],))
        d['team_size'] = (await c4.fetchone())[0]
        res.append(d)
        
    await db.close()
    return res

async def get_project_by_slug(slug: str):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM projects WHERE slug = ?", (slug,))
    p = await cursor.fetchone()
    if not p:
        await db.close()
        return None
        
    d = dict(p)
    d['team'] = [dict(row) for row in await (await db.execute("SELECT * FROM team_members WHERE project_id=?", (d['id'],))).fetchall()]
    d['milestones'] = [dict(row) for row in await (await db.execute("SELECT * FROM milestones WHERE project_id=?", (d['id'],))).fetchall()]
    d['resources'] = [dict(row) for row in await (await db.execute("SELECT * FROM resources WHERE project_id=?", (d['id'],))).fetchall()]
    d['success_metrics'] = [dict(row) for row in await (await db.execute("SELECT * FROM success_metrics WHERE project_id=?", (d['id'],))).fetchall()]
    d['endorsements'] = [dict(row) for row in await (await db.execute("SELECT * FROM endorsements WHERE project_id=?", (d['id'],))).fetchall()]
    
    c = await db.execute("SELECT COUNT(*) FROM endorsements WHERE project_id=? AND endorsement_type='star'", (d['id'],))
    d['stars'] = (await c.fetchone())[0]
    
    await db.close()
    return d

async def get_stats():
    db = await get_db()
    c = await db.execute("SELECT COUNT(*) FROM projects WHERE status='active'")
    active = (await c.fetchone())[0]
    c = await db.execute("SELECT COUNT(*) FROM endorsements")
    endorsements = (await c.fetchone())[0]
    
    c = await db.execute("SELECT SUM(estimated_hours) FROM resources r JOIN projects p ON r.project_id=p.id WHERE p.status='active'")
    row = await c.fetchone()
    hours = row[0] if row and row[0] else 0
    
    await db.close()
    return active, endorsements, hours

async def get_recent_webhooks(limit=5):
    db = await get_db()
    c = await db.execute("SELECT * FROM webhook_events ORDER BY received_at DESC LIMIT ?", (limit,))
    res = [dict(row) for row in await c.fetchall()]
    await db.close()
    return res

async def get_all_faculty():
    db = await get_db()
    c = await db.execute("SELECT * FROM faculty ORDER BY full_name")
    res = [dict(row) for row in await c.fetchall()]
    await db.close()
    return res
