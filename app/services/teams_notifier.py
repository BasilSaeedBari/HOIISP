import httpx
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

def build_new_submission_card(data: dict) -> dict:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "New Project Submission",
        "themeColor": "0078D7",
        "title": "New Project Submission Received",
        "text": f"Repo: {data.get('repo_url')}\\nLead: {data.get('lead_email')}\\nVerification: {data.get('verification_status')}",
    }

def build_approved_card(data: dict) -> dict:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Project Approved",
        "themeColor": "22C55E",
        "title": "Project Approved",
        "text": f"Title: {data.get('title')}\\nDomain: {data.get('domain')}",
    }

def build_rejected_card(data: dict) -> dict:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Project Rejected",
        "themeColor": "EF4444",
        "title": "Project Rejected",
        "text": f"Repo: {data.get('repo_url')}\\nReason: {data.get('reason')}",
    }

def build_milestone_card(data: dict) -> dict:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Milestone Completed",
        "themeColor": "3B82F6",
        "title": "Milestone Completed",
        "text": f"Project: {data.get('title')}\\nMilestone: {data.get('milestone')}",
    }

def build_stale_card(data: dict) -> dict:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Project Stale",
        "themeColor": "F59E0B",
        "title": "Project Marked as Stale",
        "text": f"Project: {data.get('title')}\\nLast Push: {data.get('last_push')}",
    }

def build_endorsement_card(data: dict) -> dict:
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Endorsement Added",
        "themeColor": "8B5CF6",
        "title": "Faculty Endorsement Added",
        "text": f"Project: {data.get('title')}\\nFaculty: {data.get('faculty_name')}",
    }

EVENT_CARD_BUILDERS = {
    'NEW_SUBMISSION':      build_new_submission_card,
    'SUBMISSION_APPROVED': build_approved_card,
    'SUBMISSION_REJECTED': build_rejected_card,
    'MILESTONE_COMPLETE':  build_milestone_card,
    'PROJECT_STALE':       build_stale_card,
    'ENDORSEMENT_ADDED':   build_endorsement_card,
}

async def send_teams_notification(event_type: str, data: Dict[str, Any]):
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
