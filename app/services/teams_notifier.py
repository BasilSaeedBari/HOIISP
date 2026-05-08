import logging

import httpx

from app.config import TEAMS_WEBHOOK_URL

logger = logging.getLogger(__name__)


def _card(title: str, facts: list[tuple[str, str]], summary: str, url: str = "") -> dict:
    body = [
        {"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": title},
        {
            "type": "FactSet",
            "facts": [{"title": k, "value": v} for k, v in facts],
        },
        {"type": "TextBlock", "text": summary, "wrap": True},
    ]
    actions = []
    if url:
        actions.append({"type": "Action.OpenUrl", "title": "View Project", "url": url})
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": body,
                    "actions": actions,
                },
            }
        ],
    }


def build_card(event_type: str, data: dict) -> dict:
    p = data.get("project", {})
    title = p.get("title", "Project")
    slug = p.get("slug", "")
    url = f"{data.get('base_url', '').rstrip('/')}/projects/{slug}" if slug else ""

    if event_type == "NEW_PROPOSAL":
        return _card("🆕 New Proposal Submitted", [("Project", title), ("Domain", p.get("domain", "Unspecified")), ("Status", "Pending Review")], p.get("abstract", "")[:220], url)
    if event_type == "PROPOSAL_APPROVED":
        return _card("✅ New Project Approved", [("Project", title), ("Domain", p.get("domain", "Unspecified")), ("Status", "Active")], p.get("abstract", "")[:220], url)
    if event_type == "MILESTONE_COMPLETE":
        return _card("🏁 Milestone Complete", [("Project", title), ("Milestone", data.get("milestone_name", "Milestone"))], data.get("message", "A milestone has been marked complete."), url)
    if event_type == "FACULTY_ENDORSE":
        return _card("⭐ Faculty Endorsement", [("Project", title), ("Faculty", data.get("faculty", "Faculty"))], data.get("message", "A faculty member endorsed this project."), url)
    if event_type == "PROJECT_COMPLETE":
        return _card("🎉 Project Complete", [("Project", title), ("Status", "Complete")], data.get("message", "Project has been marked complete."), url)
    return _card("OIISP Update", [("Event", event_type)], "Platform event received.", url)


async def send_teams_notification(event_type: str, data: dict) -> None:
    if not TEAMS_WEBHOOK_URL:
        return
    payload = build_card(event_type, data)
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(TEAMS_WEBHOOK_URL, json=payload)
    except Exception:
        logger.exception("Teams notification failed for %s", event_type)
