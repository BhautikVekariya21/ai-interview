"""App Review API Routes (feedback forum).

Public reads (review list + aggregate stats) require no auth so the forum can
render for anyone. Posting a review requires an authenticated user and is
rate limited.
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.auth_routes import get_current_user
from app.repositories.review_repository import ReviewRepository
from app.services.mysql_service import MySQLService, get_mysql

review_router = APIRouter(prefix="/reviews", tags=["Reviews"])


# ─── Schemas ──────────────────────────────────────────────

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: str = Field("", max_length=200)
    review: str = Field(..., min_length=5, max_length=4000)


class ReviewResponse(BaseModel):
    id: str
    author_name: str
    rating: int
    title: str
    review: str
    created_at: Optional[str] = None


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int
    average: float


# ─── Rate limiting (in-memory) ────────────────────────────

_rate_limit: dict[str, list[float]] = defaultdict(list)
MAX_REVIEWS_PER_HOUR = 5


def _check_rate_limit(key: str) -> bool:
    now = time.time()
    window = 3600
    _rate_limit[key] = [ts for ts in _rate_limit[key] if now - ts < window]
    if len(_rate_limit[key]) >= MAX_REVIEWS_PER_HOUR:
        return False
    _rate_limit[key].append(now)
    return True


def get_review_repository(db: MySQLService = Depends(get_mysql)) -> ReviewRepository:
    return ReviewRepository(db)


def _iso(dt) -> Optional[str]:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


def _row_to_response(row) -> ReviewResponse:
    return ReviewResponse(
        id=row.id,
        author_name=row.author_name or "Anonymous",
        rating=row.rating,
        title=row.title or "",
        review=row.review or "",
        created_at=_iso(row.created_at),
    )


# ─── Routes ───────────────────────────────────────────────

@review_router.get("/", response_model=ReviewListResponse)
def list_reviews(limit: int = 50, repo: ReviewRepository = Depends(get_review_repository)):
    limit = max(1, min(limit, 100))
    stats = repo.stats()
    return ReviewListResponse(
        items=[_row_to_response(row) for row in repo.list_recent(limit)],
        total=stats["total"],
        average=stats["average"],
    )


@review_router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    current=Depends(get_current_user),
    repo: ReviewRepository = Depends(get_review_repository),
):
    user = current["user"]
    if not _check_rate_limit(str(user.id)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many reviews, please try again later.")

    review_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    author_name = getattr(user, "full_name", None) or getattr(user, "email", None) or "Anonymous"
    repo.insert(
        review_id=review_id,
        user_id=user.id,
        author_name=author_name,
        rating=payload.rating,
        title=payload.title,
        review=payload.review,
        created_at=now,
    )
    return ReviewResponse(
        id=review_id,
        author_name=author_name,
        rating=payload.rating,
        title=payload.title,
        review=payload.review,
        created_at=now.isoformat(),
    )
