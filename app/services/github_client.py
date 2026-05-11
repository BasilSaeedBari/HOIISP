import httpx
import base64
import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

HABIB_STUDENT_DOMAIN = "@st.habib.edu.pk"

async def verify_habib_affiliation(owner: str, repo: str) -> Dict[str, Any]:
    """
    Scan up to 100 commits on the default branch.
    Return the first commit found with a @st.habib.edu.pk author email.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": 100}

    async with httpx.AsyncClient(headers=HEADERS) as client:
        try:
            response = await client.get(url, params=params)
        except Exception as e:
            return {"verified": False, "reason": f"Connection error: {str(e)}"}

    if response.status_code == 404:
        return {"verified": False, "reason": "Repository not found or is private."}
    if response.status_code != 200:
        return {"verified": False, "reason": f"GitHub API error: {response.status_code} - {response.text}"}

    commits = response.json()
    for commit in commits:
        author_email = commit.get("commit", {}).get("author", {}).get("email", "")
        committer_email = commit.get("commit", {}).get("committer", {}).get("email", "")
        for email in [author_email, committer_email]:
            if email and email.lower().endswith(HABIB_STUDENT_DOMAIN):
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

async def fetch_project_md(owner: str, repo: str) -> Optional[str]:
    """
    Fetch the raw content of project.md from the repo root on the default branch.
    Uses raw.githubusercontent.com for strict unauthenticated approach.
    """
    
    # We should determine the default branch first, but often it's 'main' or 'master'
    # Try fetching default branch from API if possible
    branch = "main"
    url_repo = f"https://api.github.com/repos/{owner}/{repo}"
    async with httpx.AsyncClient(headers=HEADERS) as client:
        try:
            res = await client.get(url_repo)
            if res.status_code == 200:
                branch = res.json().get("default_branch", "main")
        except Exception:
            pass

    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/project.md"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.error(f"Error fetching raw project.md: {e}")
            
    # Fallback to API if raw fetch fails (maybe blocked by firewall/cors)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/project.md"
    async with httpx.AsyncClient(headers=HEADERS) as client:
        try:
            response = await client.get(api_url)
            if response.status_code == 200:
                data = response.json()
                return base64.b64decode(data["content"]).decode("utf-8")
        except Exception as e:
            logger.error(f"Error fetching project.md via API: {e}")
            
    return None

async def get_recent_commits(owner: str, repo: str, count: int = 5) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": count}
    async with httpx.AsyncClient(headers=HEADERS) as client:
        try:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                return []
            return [
                {
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\\n")[0],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"],
                    "url": c["html_url"],
                }
                for c in response.json()
            ]
        except Exception:
            return []


