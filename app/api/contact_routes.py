"""
Contact Form API Routes — accepts contact form submissions,
persists them to a JSON log, and applies basic rate limiting.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.services import rate_limit_service

contact_router = APIRouter(prefix="/contact", tags=["Contact"])

# ─── Schemas ──────────────────────────────────────────────

class ContactSubmission(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=10, max_length=5000)


class ContactResponse(BaseModel):
    success: bool
    message: str
    submission_id: Optional[str] = None


# ─── Rate Limiting (in-memory) ────────────────────────────

# ─── Persistence ──────────────────────────────────────────

CONTACT_LOG_DIR = Path("data/contact_submissions")


def _persist_submission(data: dict) -> str:
    """Append submission to a daily JSON-lines log file and return an ID."""
    CONTACT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = CONTACT_LOG_DIR / f"contacts_{today}.jsonl"

    submission_id = f"ct_{uuid.uuid4().hex}"
    record = {
        "id": submission_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"Contact form submission persisted: {submission_id}")
    return submission_id


# ─── Endpoint ─────────────────────────────────────────────

@contact_router.post("/submit", response_model=ContactResponse)
async def submit_contact_form(submission: ContactSubmission, request: Request):
    """
    Accept a contact form submission, persist it, and return a confirmation.
    Rate limited to 5 submissions per IP per hour.
    """
    decision = rate_limit_service.check_quota(
        "contact",
        rate_limit_service.client_ip(request),
        settings.CONTACT_RATELIMIT_PER_HOUR,
        3600,
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many submissions. Please try again later.",
            headers={"Retry-After": str(decision.retry_after)},
        )

    try:
        submission_id = _persist_submission(submission.model_dump())
        return ContactResponse(
            success=True,
            message="Thank you for reaching out! We'll get back to you within 24 hours.",
            submission_id=submission_id,
        )
    except Exception as e:
        logger.exception(f"Failed to persist contact submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit your message. Please try again.",
        )
