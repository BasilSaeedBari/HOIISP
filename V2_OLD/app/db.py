import aiosqlite
from fastapi import FastAPI

from app.config import DATABASE_PATH


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','faculty','admin','technician')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    problem_statement TEXT,
    domain TEXT,
    sub_field TEXT,
    ieee_society TEXT,
    methodology TEXT,
    objectives TEXT,
    success_metrics_text TEXT,
    status TEXT DEFAULT 'pending_review',
    submitted_by INTEGER REFERENCES users(id),
    file_path TEXT,
    admin_note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    approved_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    number INTEGER,
    name TEXT,
    deliverables TEXT,
    start_date TEXT,
    end_date TEXT,
    actual_end_date TEXT,
    status TEXT DEFAULT 'Not Started'
);

CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    student_id TEXT,
    program TEXT,
    year TEXT,
    role TEXT
);

CREATE TABLE IF NOT EXISTS resource_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    resource_name TEXT,
    lab_location TEXT,
    estimated_hours TEXT,
    purpose TEXT,
    required_from TEXT,
    required_until TEXT,
    approved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    posted_by INTEGER REFERENCES users(id),
    body TEXT,
    image_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS endorsements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    type TEXT CHECK(type IN ('star','vouch','endorse')),
    comment TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, user_id, type)
);

CREATE TABLE IF NOT EXISTS faculty_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT,
    expertise_tags TEXT
);
"""


async def init_db(app: FastAPI) -> None:
    app.state.db = await aiosqlite.connect(DATABASE_PATH)
    app.state.db.row_factory = aiosqlite.Row
    await app.state.db.executescript(SCHEMA_SQL)
    await app.state.db.commit()


async def close_db(app: FastAPI) -> None:
    await app.state.db.close()


async def seed_default_admin(app: FastAPI, password_hash: str) -> None:
    await app.state.db.execute(
        "INSERT OR IGNORE INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
        ("admin@hoiisp.local", password_hash),
    )
    await app.state.db.commit()
