from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from datetime import datetime
import os

from app import db, config
from app.services import github_client, project_parser, teams_notifier

logger = logging.getLogger(__name__)

# --- Global SSE queue list ---
# (In a real app, you might use a pub-sub or more robust queue management)
leaderboard_clients = []

async def broadcast_leaderboard_update():
    html = await render_leaderboard_tbody()
    for queue in leaderboard_clients:
        await queue.put(html)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    # In phase 4 we will start scheduler here
    yield
    # Cleanup

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)

# Ensure static and templates directories exist in same level as main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Custom Jinja filters
templates.env.filters['fromjson'] = json.loads

# --- Dependency ---
def get_current_admin(request: Request):
    user = request.session.get("admin_logged_in")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def admin_required(request: Request):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin/login", status_code=303)
    return None

# --- Public Routes ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    stats = await db.get_stats()
    recent_events = await db.get_recent_webhooks()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "stats": {"active": stats[0], "endorsements": stats[1], "hours": stats[2]},
        "recent_events": recent_events
    })

@app.get("/projects", response_class=HTMLResponse)
async def projects(request: Request, domain: str = None, status: str = None, sort: str = "stars"):
    proj_list = await db.get_projects(domain=domain, status=status, sort=sort)
    # determine if stale (e.g. > 14 days without push)
    now = datetime.utcnow()
    for p in proj_list:
        p['is_stale'] = False
        if p.get('last_push_at'):
            try:
                # Assuming ISO format from github
                lp_date = datetime.fromisoformat(p['last_push_at'].replace('Z', '+00:00')).replace(tzinfo=None)
                if (now - lp_date).days > 14:
                    p['is_stale'] = True
            except:
                pass

    return templates.TemplateResponse("projects.html", {"request": request, "projects": proj_list})

@app.get("/projects/{slug}", response_class=HTMLResponse)
async def project_detail(request: Request, slug: str):
    p = await db.get_project_by_slug(slug)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
        
    commits = await github_client.get_recent_commits(p['repo_owner'], p['repo_name'])
    
    now = datetime.utcnow()
    is_stale = False
    if p.get('last_push_at'):
        try:
            lp_date = datetime.fromisoformat(p['last_push_at'].replace('Z', '+00:00')).replace(tzinfo=None)
            if (now - lp_date).days > 14:
                is_stale = True
        except:
            pass

    return templates.TemplateResponse("project_detail.html", {
        "request": request, 
        "p": p, 
        "commits": commits,
        "is_stale": is_stale
    })

@app.get("/submit", response_class=HTMLResponse)
async def submit_page(request: Request):
    return templates.TemplateResponse("submit.html", {"request": request})

@app.get("/faculty", response_class=HTMLResponse)
async def faculty(request: Request):
    fac_list = await db.get_all_faculty()
    return templates.TemplateResponse("faculty.html", {"request": request, "faculty": fac_list})

@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    import mistune
    terms_path = os.path.join(os.path.dirname(BASE_DIR), "TermsAndConditionsV3.md")
    if os.path.exists(terms_path):
        with open(terms_path, "r", encoding="utf-8") as f:
            content = f.read()
            html = mistune.html(content)
    else:
        html = "<p>Terms not found.</p>"
    return templates.TemplateResponse("terms.html", {"request": request, "terms_html": html})

# --- SSE Endpoint ---

async def render_leaderboard_tbody():
    # Helper to render just the tbody for SSE
    proj_list = await db.get_projects(status='active', sort='stars')
    html = ""
    for i, p in enumerate(proj_list):
        stale_badge = '<span class="badge stale">Stale ⚠️</span>' if False else '' # Calculate stale properly if needed
        html += f"""
        <tr>
            <td>{i+1}</td>
            <td><a href="/projects/{p['slug']}">{p['title']}</a></td>
            <td>{p.get('domain', '')}</td>
            <td>{p['team_size']}</td>
            <td><span class="badge {p['status']}">{p['status']}</span> {stale_badge}</td>
            <td>{p['completed_milestones']} / {p['total_milestones']}</td>
            <td>{p['stars']}</td>
            <td>{p.get('last_push_at', 'Never')}</td>
        </tr>
        """
    if not html:
        html = '<tr><td colspan="8">No active projects.</td></tr>'
    return html

@app.get("/api/stream/leaderboard")
async def stream_leaderboard(request: Request):
    queue = asyncio.Queue()
    leaderboard_clients.append(queue)
    
    async def event_generator():
        # Send initial state
        initial_html = await render_leaderboard_tbody()
        yield f"data: {initial_html}\\n\\n"
        
        try:
            while True:
                # Wait for updates
                if await request.is_disconnected():
                    break
                html = await queue.get()
                yield f"data: {html}\\n\\n"
        except asyncio.CancelledError:
            pass
        finally:
            leaderboard_clients.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- Submission API ---

@app.post("/api/submit")
async def api_submit(
    github_url: str = Form(...),
    lead_email: str = Form(...)
):
    # Validate GitHub URL
    if not github_url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL.")
    
    parts = github_url.replace("https://github.com/", "").split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL format.")
    
    owner = parts[0]
    repo = parts[1].replace(".git", "")
    
    # Verify affiliation
    verify_res = await github_client.verify_habib_affiliation(owner, repo)
    if not verify_res.get("verified"):
        raise HTTPException(status_code=400, detail=verify_res.get("reason", "Verification failed"))
        
    # Fetch project.md
    md_text = await github_client.fetch_project_md(owner, repo)
    if not md_text:
        raise HTTPException(status_code=400, detail="Could not find or fetch project.md from the repository root.")
        
    # Parse and validate
    parsed = project_parser.parse_project_md(md_text)
    val = project_parser.validate_project_md(parsed)
    
    parse_status = "ok" if val["valid"] else "errors"
    if val["warnings"] and parse_status == "ok":
        parse_status = "warnings"
        
    # Store submission
    await db.create_submission(
        github_url, owner, repo, lead_email, 
        "verified", verify_res, 
        parse_status, val
    )
    
    return {"message": "Submitted — you'll hear back within 48 hours."}


# --- Admin Routes ---

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    if request.session.get("admin_logged_in"):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/api/admin/login")
async def admin_login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await db.get_admin_user(email)
    if not user or not db.verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid credentials"})
        
    request.session["admin_logged_in"] = user["email"]
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/api/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    red = admin_required(request)
    if red: return red
    
    submissions = await db.get_all_submissions()
    pending = [s for s in submissions if s['status'] == 'pending']
    projects = await db.get_projects()
    
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "submissions": pending,
        "projects": projects
    })

@app.get("/admin/review/{sub_id}", response_class=HTMLResponse)
async def admin_review(request: Request, sub_id: int):
    red = admin_required(request)
    if red: return red
    
    sub = await db.get_submission(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    # Re-fetch and parse project.md to show preview
    md_text = await github_client.fetch_project_md(sub['repo_owner'], sub['repo_name'])
    parsed = {}
    if md_text:
        parsed = project_parser.parse_project_md(md_text)
        
    verify_detail = json.loads(sub['verification_detail']) if sub['verification_detail'] else {}
    parse_report = json.loads(sub['parse_report']) if sub['parse_report'] else {}
    
    return templates.TemplateResponse("admin_review.html", {
        "request": request, 
        "sub": sub,
        "verify_detail": verify_detail,
        "parse_report": parse_report,
        "parsed": parsed
    })

@app.post("/api/admin/approve/{sub_id}")
async def approve_submission(request: Request, sub_id: int, background_tasks: BackgroundTasks, admin_notes: str = Form(None)):
    red = admin_required(request)
    if red: return red
    
    sub = await db.get_submission(sub_id)
    if not sub:
        raise HTTPException(status_code=404)
        
    md_text = await github_client.fetch_project_md(sub['repo_owner'], sub['repo_name'])
    if not md_text:
        raise HTTPException(status_code=400, detail="Cannot fetch project.md for approval")
        
    parsed = project_parser.parse_project_md(md_text)
    
    # Update submission status
    await db.update_submission_status(sub_id, 'approved', admin_notes)
    
    # Create project
    commits = await github_client.get_recent_commits(sub['repo_owner'], sub['repo_name'], count=1)
    last_push = commits[0]['date'] if commits else None
    
    project_id = await db.create_project_from_submission(sub, parsed, last_push)
    
    # Notify teams
    background_tasks.add_task(teams_notifier.send_teams_notification, 'SUBMISSION_APPROVED', {
        'title': parsed.get('title'),
        'domain': parsed.get('domain_data', {}).get('domain', 'Unknown')
    })
    
    # Register webhook
    background_tasks.add_task(github_client.register_webhook, sub['repo_owner'], sub['repo_name'], config.HOIISP_BASE_URL)
    
    # Broadcast update to leaderboard
    background_tasks.add_task(broadcast_leaderboard_update)
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/api/admin/reject/{sub_id}")
async def reject_submission(request: Request, sub_id: int, background_tasks: BackgroundTasks, admin_notes: str = Form(...)):
    red = admin_required(request)
    if red: return red
    
    sub = await db.get_submission(sub_id)
    if not sub:
        raise HTTPException(status_code=404)
        
    await db.update_submission_status(sub_id, 'rejected', admin_notes)
    
    background_tasks.add_task(teams_notifier.send_teams_notification, 'SUBMISSION_REJECTED', {
        'repo_url': sub['github_url'],
        'reason': admin_notes
    })
    
    return RedirectResponse(url="/admin", status_code=303)
