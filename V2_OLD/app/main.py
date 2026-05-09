import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slugify import slugify
from starlette.middleware.sessions import SessionMiddleware

from app.auth import ROLES, current_user, hash_password, require_role, verify_password
from app.config import SECRET_KEY, UPLOAD_DIR
from app.db import close_db, init_db, seed_default_admin
from app.services.proposal_parser import parse_proposal
from app.services.teams_notifier import send_teams_notification


class LeaderboardHub:
    def __init__(self) -> None:
        self.version = int(time.time())

    def bump(self) -> None:
        self.version += 1

    async def stream(self, app_ref: FastAPI):
        last_seen = -1
        while True:
            if self.version != last_seen:
                last_seen = self.version
                conn = app_ref.state.db
                projects = await get_project_rows(conn, "stars")
                tbody_html = templates.get_template("_leaderboard_tbody.html").render({"projects": projects})
                c1 = await (await conn.execute("SELECT COUNT(*) c FROM projects WHERE status='active'")).fetchone()
                c2 = await (await conn.execute("SELECT COUNT(*) c FROM endorsements")).fetchone()
                c3 = await (await conn.execute("SELECT COALESCE(SUM(CAST(estimated_hours AS INTEGER)),0) c FROM resource_requests")).fetchone()
                stats_html = (
                    "<div id='stats' class='stats'>"
                    f"<strong>Active Projects:</strong> {c1['c']} | "
                    f"<strong>Endorsements:</strong> {c2['c']} | "
                    f"<strong>Lab Hours:</strong> {c3['c']}"
                    "</div>"
                )
                payload = json.dumps({"tbody": tbody_html, "stats": stats_html})
                yield f"event: refresh\ndata: {payload}\n\n"
            await __import__("asyncio").sleep(1)


hub = LeaderboardHub()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(app)
    await seed_default_admin(app, hash_password("admin123"))
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / "proposals").mkdir(exist_ok=True)
    (UPLOAD_DIR / "updates").mkdir(exist_ok=True)
    yield
    await close_db(app)


app = FastAPI(title="HOIISP Prototype", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=60 * 60 * 12)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def db(request: Request):
    return request.app.state.db


async def get_project_rows(conn, sort: str = "stars"):
    sort_sql = {
        "stars": "stars DESC, p.created_at DESC",
        "date": "p.created_at DESC",
        "title": "p.title ASC",
        "endorsements": "endorsements DESC, stars DESC",
    }.get(sort, "stars DESC, p.created_at DESC")
    q = f"""
    SELECT p.*,
           COALESCE(SUM(CASE WHEN e.type='star' THEN 1 ELSE 0 END),0) AS stars,
           COALESCE(COUNT(e.id),0) AS endorsements,
           COALESCE((SELECT created_at FROM project_updates u WHERE u.project_id=p.id ORDER BY u.created_at DESC LIMIT 1), p.created_at) AS last_update
    FROM projects p
    LEFT JOIN endorsements e ON e.project_id = p.id
    GROUP BY p.id
    ORDER BY {sort_sql}
    """
    cur = await conn.execute(q)
    return await cur.fetchall()


async def render_leaderboard_tbody(request: Request, sort: str = "stars") -> str:
    rows = await get_project_rows(db(request), sort)
    return templates.get_template("_leaderboard_tbody.html").render({"request": request, "projects": rows})


async def stats_payload(request: Request) -> dict:
    conn = db(request)
    c1 = await (await conn.execute("SELECT COUNT(*) c FROM projects WHERE status='active'")).fetchone()
    c2 = await (await conn.execute("SELECT COUNT(*) c FROM endorsements")).fetchone()
    c3 = await (await conn.execute("SELECT COALESCE(SUM(CAST(estimated_hours AS INTEGER)),0) c FROM resource_requests")).fetchone()
    return {"active_projects": c1["c"], "endorsements": c2["c"], "lab_hours": c3["c"]}


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request, sort: str = "stars"):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "projects": await get_project_rows(db(request), sort), "stats": await stats_payload(request), "sort": sort},
    )


@app.get("/projects", response_class=HTMLResponse)
async def project_directory(request: Request, domain: str = "", status: str = "", endorsed: int = 0, sort: str = "stars"):
    rows = await get_project_rows(db(request), sort)
    filtered = []
    for r in rows:
        if domain and domain.lower() not in (r["domain"] or "").lower():
            continue
        if status and status != r["status"]:
            continue
        if endorsed and int(r["endorsements"]) == 0:
            continue
        filtered.append(r)
    return templates.TemplateResponse("projects.html", {"request": request, "projects": filtered, "domain": domain, "status": status, "endorsed": endorsed, "sort": sort})


@app.get("/projects/{slug}", response_class=HTMLResponse)
async def project_page(request: Request, slug: str):
    conn = db(request)
    p = await (await conn.execute("SELECT * FROM projects WHERE slug=?", (slug,))).fetchone()
    if not p:
        raise HTTPException(404, "Project not found")
    milestones = await (await conn.execute("SELECT * FROM milestones WHERE project_id=? ORDER BY number", (p["id"],))).fetchall()
    team = await (await conn.execute("SELECT * FROM team_members WHERE project_id=?", (p["id"],))).fetchall()
    resources = await (await conn.execute("SELECT * FROM resource_requests WHERE project_id=?", (p["id"],))).fetchall()
    updates = await (await conn.execute("SELECT u.*, usr.email as posted_by_email FROM project_updates u LEFT JOIN users usr ON usr.id=u.posted_by WHERE project_id=? ORDER BY created_at DESC", (p["id"],))).fetchall()
    endorsements = await (await conn.execute("SELECT e.*, usr.email as user_email FROM endorsements e LEFT JOIN users usr ON usr.id=e.user_id WHERE project_id=? ORDER BY created_at DESC", (p["id"],))).fetchall()
    return templates.TemplateResponse(
        "project_detail.html",
        {"request": request, "project": p, "milestones": milestones, "team": team, "resources": resources, "updates": updates, "endorsements": endorsements},
    )


@app.get("/submit", response_class=HTMLResponse)
async def submit_page(request: Request, user: dict = Depends(require_role("student"))):
    return templates.TemplateResponse("submit.html", {"request": request, "user": user})


@app.get("/faculty", response_class=HTMLResponse)
async def faculty_page(request: Request):
    conn = db(request)
    rows = await (
        await conn.execute(
            """
            SELECT u.id, u.email, COALESCE(fp.full_name, u.email) as full_name, COALESCE(fp.expertise_tags,'') as expertise_tags,
                   (SELECT COUNT(*) FROM endorsements e WHERE e.user_id=u.id) as endorsements_count,
                   (SELECT COUNT(DISTINCT p.id) FROM projects p JOIN endorsements e ON e.project_id=p.id WHERE e.user_id=u.id) as linked_projects
            FROM users u
            LEFT JOIN faculty_profiles fp ON fp.user_id=u.id
            WHERE u.role='faculty'
            ORDER BY full_name
            """
        )
    ).fetchall()
    return templates.TemplateResponse("faculty.html", {"request": request, "faculty": rows})


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, user: dict = Depends(require_role("admin"))):
    pending = await (await db(request).execute("SELECT * FROM projects WHERE status='pending_review' ORDER BY created_at DESC")).fetchall()
    return templates.TemplateResponse("admin.html", {"request": request, "pending": pending, "user": user})


@app.post("/api/auth/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), role: str = Form("student")):
    role = role if role in ROLES else "student"
    conn = db(request)
    try:
        cur = await conn.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", (email.lower().strip(), hash_password(password), role))
        await conn.commit()
        user_id = cur.lastrowid
    except Exception:
        return JSONResponse({"error": "Email already exists."}, status_code=400)
    if role == "faculty":
        await conn.execute(
            "INSERT OR IGNORE INTO faculty_profiles (user_id, full_name, expertise_tags) VALUES (?, ?, ?)",
            (user_id, email.split("@")[0].replace(".", " ").title(), "General"),
        )
        await conn.commit()
    request.session["user"] = {"id": user_id, "email": email.lower().strip(), "role": role}
    return JSONResponse({"ok": True, "redirect": "/"})


@app.post("/api/auth/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = db(request)
    user = await (await conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),))).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        return JSONResponse({"error": "Invalid credentials"}, status_code=401)
    request.session["user"] = {"id": user["id"], "email": user["email"], "role": user["role"]}
    return JSONResponse({"ok": True, "redirect": "/"})


@app.post("/api/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse({"ok": True, "redirect": "/"})


@app.post("/api/proposals/submit")
async def submit_proposal(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: dict = Depends(require_role("student")),
):
    if not file.filename.endswith(".md"):
        return JSONResponse({"errors": [{"section": "file", "message": "Only .md files are accepted."}]}, status_code=422)
    content = await file.read()
    parsed = parse_proposal(content.decode("utf-8", errors="ignore"))
    if not parsed["validation"]["valid"]:
        return JSONResponse({"errors": parsed["validation"]["errors"]}, status_code=422)

    slug_base = slugify(parsed["title"]) or "untitled-project"
    slug = f"{slug_base}-{int(time.time())}"
    rel_path = f"proposals/{user['id']}/{slug}.md"
    full_path = UPLOAD_DIR / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)

    conn = db(request)
    cur = await conn.execute(
        """
        INSERT INTO projects (slug,title,abstract,problem_statement,domain,methodology,objectives,success_metrics_text,status,submitted_by,file_path)
        VALUES (?,?,?,?,?,?,?,?, 'pending_review', ?, ?)
        """,
        (
            slug,
            parsed["title"],
            parsed["abstract"],
            parsed["problem_statement"],
            parsed["domain"],
            parsed["methodology"],
            parsed["objectives"],
            json.dumps(parsed["success_metrics"]),
            user["id"],
            rel_path,
        ),
    )
    project_id = cur.lastrowid
    for idx, row in enumerate(parsed["milestones"], start=1):
        await conn.execute(
            "INSERT INTO milestones (project_id,number,name,deliverables,start_date,end_date,status) VALUES (?,?,?,?,?,?,?)",
            (
                project_id,
                idx,
                row.get("milestone #", f"M{idx}"),
                row.get("milestone name", ""),
                row.get("key deliverables", ""),
                row.get("start date", ""),
                row.get("end date", ""),
                row.get("status", "Not Started"),
            ),
        )
    for row in parsed["team"]:
        await conn.execute(
            "INSERT INTO team_members (project_id,name,student_id,program,year,role) VALUES (?,?,?,?,?,?)",
            (project_id, row.get("name", ""), row.get("student id", ""), row.get("program", ""), row.get("year", ""), row.get("role", "")),
        )
    for row in parsed["resources"]:
        await conn.execute(
            "INSERT INTO resource_requests (project_id,resource_name,lab_location,estimated_hours,purpose,required_from,required_until) VALUES (?,?,?,?,?,?,?)",
            (
                project_id,
                row.get("resource", ""),
                row.get("lab / location", ""),
                row.get("estimated hours", ""),
                row.get("purpose in project", ""),
                row.get("required from", ""),
                row.get("required until", ""),
            ),
        )
    await conn.commit()
    hub.bump()

    project_data = {"title": parsed["title"], "slug": slug, "domain": parsed["domain"], "abstract": parsed["abstract"]}
    background_tasks.add_task(send_teams_notification, "NEW_PROPOSAL", {"project": project_data, "base_url": str(request.base_url)})
    return JSONResponse({"ok": True, "redirect": f"/projects/{slug}"}, status_code=201)


@app.post("/api/projects/{slug}/endorse")
async def endorse_project(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
    type: str = Form("star"),
    comment: str = Form(""),
    user: dict = Depends(current_user),
):
    p = await (await db(request).execute("SELECT * FROM projects WHERE slug=?", (slug,))).fetchone()
    if not p:
        raise HTTPException(404, "Project not found")
    kind = type if type in {"star", "vouch", "endorse"} else "star"
    try:
        await db(request).execute(
            "INSERT INTO endorsements (project_id, user_id, type, comment) VALUES (?, ?, ?, ?)",
            (p["id"], user["id"], kind, comment.strip()),
        )
        await db(request).commit()
    except Exception:
        return JSONResponse({"error": "You already submitted this endorsement type."}, status_code=400)
    hub.bump()
    if user["role"] == "faculty":
        background_tasks.add_task(
            send_teams_notification,
            "FACULTY_ENDORSE",
            {"project": {"title": p["title"], "slug": p["slug"]}, "faculty": user["email"], "message": comment or "Faculty endorsement", "base_url": str(request.base_url)},
        )
    return JSONResponse({"ok": True})


@app.post("/api/projects/{slug}/updates")
async def add_update(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
    body: str = Form(...),
    image: UploadFile | None = File(None),
    user: dict = Depends(current_user),
):
    p = await (await db(request).execute("SELECT * FROM projects WHERE slug=?", (slug,))).fetchone()
    if not p:
        raise HTTPException(404, "Project not found")
    image_path = None
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            rel = f"updates/{p['id']}-{int(time.time())}{ext}"
            dest = UPLOAD_DIR / rel
            dest.write_bytes(await image.read())
            image_path = rel
    await db(request).execute(
        "INSERT INTO project_updates (project_id, posted_by, body, image_path) VALUES (?, ?, ?, ?)",
        (p["id"], user["id"], body.strip(), image_path),
    )
    await db(request).commit()
    hub.bump()
    if "milestone" in body.lower() and "complete" in body.lower():
        background_tasks.add_task(
            send_teams_notification,
            "MILESTONE_COMPLETE",
            {"project": {"title": p["title"], "slug": p["slug"]}, "milestone_name": "Reported Milestone", "message": body[:220], "base_url": str(request.base_url)},
        )
    return JSONResponse({"ok": True})


@app.post("/api/admin/proposals/{project_id}/decision")
async def review_proposal(
    request: Request,
    project_id: int,
    background_tasks: BackgroundTasks,
    decision: str = Form(...),
    note: str = Form(""),
    user: dict = Depends(require_role("admin")),
):
    p = await (await db(request).execute("SELECT * FROM projects WHERE id=?", (project_id,))).fetchone()
    if not p:
        raise HTTPException(404, "Not found")
    if decision == "approve":
        await db(request).execute(
            "UPDATE projects SET status='active', approved_at=datetime('now'), admin_note=? WHERE id=?",
            (note, project_id),
        )
        await db(request).commit()
        hub.bump()
        background_tasks.add_task(
            send_teams_notification,
            "PROPOSAL_APPROVED",
            {"project": {"title": p["title"], "slug": p["slug"], "domain": p["domain"], "abstract": p["abstract"]}, "base_url": str(request.base_url)},
        )
    else:
        await db(request).execute(
            "UPDATE projects SET status='rejected', admin_note=? WHERE id=?",
            (note, project_id),
        )
        await db(request).commit()
        hub.bump()
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/api/stream/leaderboard")
async def leaderboard_stream():
    return StreamingResponse(hub.stream(app), media_type="text/event-stream")


@app.get("/api/fragments/leaderboard")
async def leaderboard_fragment(request: Request, sort: str = "stars"):
    return HTMLResponse(await render_leaderboard_tbody(request, sort))


@app.get("/api/fragments/stats")
async def stats_fragment(request: Request):
    s = await stats_payload(request)
    html = f"""
    <div id='stats'>
      <strong>Active Projects:</strong> {s['active_projects']} |
      <strong>Endorsements:</strong> {s['endorsements']} |
      <strong>Lab Hours:</strong> {s['lab_hours']}
    </div>
    """
    return HTMLResponse(html)


@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    terms_text = Path(__file__).resolve().parent.parent.joinpath("TermsAndConditions.md")
    content = terms_text.read_text(encoding="utf-8") if terms_text.exists() else "Terms file not found."
    return templates.TemplateResponse("terms.html", {"request": request, "content": content})
