"""Community Blog API Routes.

Public reads (list posts, single post, feedback list) require no auth so the
marketing Insights & Resources page can render for anyone. Writes (create post,
submit feedback) require an authenticated user and are rate limited.
"""
from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from app.api.auth_routes import get_current_user
from app.repositories.blog_repository import BlogRepository
from app.services import email_service
from app.services.blog_service import fetch_blog_feed
from app.services.cache_service import get_cache
from app.services.mysql_service import MySQLService, get_mysql

import logging

logger = logging.getLogger(__name__)

blog_router = APIRouter(prefix="/blog", tags=["Blog"])


# ─── Schemas ──────────────────────────────────────────────

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    category: str = Field(..., min_length=1, max_length=80)
    excerpt: str = Field("", max_length=600)
    content: str = Field(..., min_length=10)


class BlogPostResponse(BaseModel):
    id: str
    author_name: str
    title: str
    category: str
    excerpt: str
    content: str
    created_at: Optional[str] = None


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=2000)


class FeedbackResponse(BaseModel):
    id: str
    author_name: str
    rating: int
    comment: str
    created_at: Optional[str] = None


class SubscribeRequest(BaseModel):
    email: EmailStr


class SubscribeResponse(BaseModel):
    status: str
    already_subscribed: bool = False


# ─── Rate limiting (in-memory) ────────────────────────────

_rate_limit: dict[str, list[float]] = defaultdict(list)
MAX_WRITES_PER_HOUR = 20


def _check_rate_limit(key: str) -> bool:
    now = time.time()
    window = 3600
    _rate_limit[key] = [ts for ts in _rate_limit[key] if now - ts < window]
    if len(_rate_limit[key]) >= MAX_WRITES_PER_HOUR:
        return False
    _rate_limit[key].append(now)
    return True


def get_blog_repository(db: MySQLService = Depends(get_mysql)) -> BlogRepository:
    return BlogRepository(db)


def _iso(dt) -> Optional[str]:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


def _post_to_response(row) -> BlogPostResponse:
    return BlogPostResponse(
        id=row.id,
        author_name=row.author_name or "Anonymous",
        title=row.title,
        category=row.category,
        excerpt=row.excerpt or "",
        content=row.content or "",
        created_at=_iso(row.created_at),
    )


def _feedback_to_response(row) -> FeedbackResponse:
    return FeedbackResponse(
        id=row.id,
        author_name=row.author_name or "Anonymous",
        rating=row.rating,
        comment=row.comment or "",
        created_at=_iso(row.created_at),
    )


# ─── Routes ───────────────────────────────────────────────

@blog_router.get("/feed")
def blog_feed(
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=30, ge=6, le=100),
):
    """Aggregated developer/career articles from public RSS feeds.

    Public (no auth) so the marketing Blog page renders for anyone. Cached for
    15 minutes so we don't re-fetch every upstream feed on each page view.
    """
    cache = get_cache()
    cache_key = cache.make_key(
        "blog:feed",
        json.dumps({"category": category or "all", "limit": limit}, sort_keys=True),
    )
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and cached.get("items"):
        return cached

    payload = fetch_blog_feed(category=category, limit=limit)
    cache.set(cache_key, payload, ttl_seconds=900)
    return payload


@blog_router.get("/posts", response_model=List[BlogPostResponse])
def list_posts(
    category: Optional[str] = None,
    limit: int = 50,
    repo: BlogRepository = Depends(get_blog_repository),
):
    limit = max(1, min(limit, 100))
    return [_post_to_response(row) for row in repo.list_posts(limit=limit, category=category)]


@blog_router.post("/posts", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: BlogPostCreate,
    current=Depends(get_current_user),
    repo: BlogRepository = Depends(get_blog_repository),
):
    user = current["user"]
    if not _check_rate_limit(str(user.id)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many posts, please try again later.")

    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    author_name = getattr(user, "full_name", None) or getattr(user, "email", None) or "Anonymous"
    repo.insert_post(
        post_id=post_id,
        user_id=user.id,
        author_name=author_name,
        title=payload.title,
        category=payload.category,
        excerpt=payload.excerpt,
        content=payload.content,
        created_at=now,
    )
    return BlogPostResponse(
        id=post_id,
        author_name=author_name,
        title=payload.title,
        category=payload.category,
        excerpt=payload.excerpt,
        content=payload.content,
        created_at=now.isoformat(),
    )


@blog_router.get("/posts/{post_id}", response_model=BlogPostResponse)
def get_post(post_id: str, repo: BlogRepository = Depends(get_blog_repository)):
    row = repo.get_post(post_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _post_to_response(row)


@blog_router.get("/posts/{post_id}/feedback", response_model=List[FeedbackResponse])
def list_feedback(post_id: str, repo: BlogRepository = Depends(get_blog_repository)):
    return [_feedback_to_response(row) for row in repo.list_feedback(post_id)]


@blog_router.post("/posts/{post_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    post_id: str,
    payload: FeedbackCreate,
    current=Depends(get_current_user),
    repo: BlogRepository = Depends(get_blog_repository),
):
    user = current["user"]
    if not _check_rate_limit(str(user.id)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many submissions, please try again later.")

    if not repo.get_post(post_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    feedback_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    author_name = getattr(user, "full_name", None) or getattr(user, "email", None) or "Anonymous"
    repo.insert_feedback(
        feedback_id=feedback_id,
        post_id=post_id,
        user_id=user.id,
        author_name=author_name,
        rating=payload.rating,
        comment=payload.comment,
        created_at=now,
    )
    return FeedbackResponse(
        id=feedback_id,
        author_name=author_name,
        rating=payload.rating,
        comment=payload.comment,
        created_at=now.isoformat(),
    )


@blog_router.post("/subscribe", response_model=SubscribeResponse)
def subscribe(
    payload: SubscribeRequest,
    repo: BlogRepository = Depends(get_blog_repository),
):
    email = payload.email.strip().lower()

    if not _check_rate_limit(f"subscribe:{email}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts, please try again later.",
        )

    if repo.get_subscriber(email):
        return SubscribeResponse(status="ok", already_subscribed=True)

    repo.insert_subscriber(
        sub_id=str(uuid.uuid4()),
        email=email,
        created_at=datetime.now(timezone.utc),
    )

    # Send a confirmation email if SMTP is configured; never fail the request if
    # email delivery has a hiccup — the subscription itself is already stored.
    if email_service.is_configured():
        try:
            email_service.send_email(
                to_email=email,
                subject="You're subscribed to AI Interview",
                text_body=(
                    "Thanks for subscribing!\n\n"
                    "You'll now get the latest interview tips and career advice "
                    "delivered to your inbox every week.\n\n"
                    "If this wasn't you, you can ignore this email."
                ),
                html_body=(
                    '<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;'
                    'max-width:480px;margin:auto;padding:24px">'
                    '<h2 style="margin:0 0 12px">You\'re subscribed 🎉</h2>'
                    '<p style="color:#555;line-height:1.6">Thanks for subscribing! '
                    "You'll get the latest interview tips and career advice delivered "
                    "to your inbox every week.</p>"
                    '<p style="color:#aaa;font-size:12px;margin-top:24px">'
                    "If this wasn't you, you can safely ignore this email.</p></div>"
                ),
            )
        except Exception:  # pragma: no cover - delivery best-effort
            logger.exception("Failed to send subscription confirmation to %s", email)

    return SubscribeResponse(status="ok")
