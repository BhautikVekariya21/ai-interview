"""
Daily Challenge API Routes — server-side streak tracking and
challenge completion persistence for authenticated users.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.auth_routes import get_current_user

daily_challenge_router = APIRouter(
    prefix="/daily-challenge", tags=["Daily Challenge"]
)

# ─── Schemas ──────────────────────────────────────────────


class DailyStreakResponse(BaseModel):
    streak: int = 0
    last_completed_date: Optional[str] = None
    today_completed_ids: List[str] = Field(default_factory=list)
    all_completed_today: bool = False


class CompleteChallengeRequest(BaseModel):
    challenge_id: str = Field(..., min_length=1)


class CompleteChallengeResponse(BaseModel):
    success: bool
    streak: int
    today_completed_ids: List[str]
    all_completed_today: bool


class UndoChallengeRequest(BaseModel):
    challenge_id: str = Field(..., min_length=1)


# ─── In-memory store (keyed by user ID) ──────────────────

_daily_store: dict[str, dict] = {}
CHALLENGES_PER_DAY = 3


def _get_user_daily(user_id: str) -> dict:
    if user_id not in _daily_store:
        _daily_store[user_id] = {
            "streak": 0,
            "last_completed_date": None,
            "today_date": None,
            "today_completed_ids": [],
        }
    return _daily_store[user_id]


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_if_new_day(state: dict) -> None:
    """Reset today's completions if the date has changed."""
    today = _today_str()
    if state["today_date"] != today:
        # Check streak continuity
        if state["last_completed_date"]:
            last = datetime.strptime(state["last_completed_date"], "%Y-%m-%d").date()
            curr = datetime.strptime(today, "%Y-%m-%d").date()
            diff = (curr - last).days
            if diff > 1:
                state["streak"] = 0  # Streak broken
        state["today_date"] = today
        state["today_completed_ids"] = []


# ─── Endpoints ────────────────────────────────────────────


@daily_challenge_router.get("/streak", response_model=DailyStreakResponse)
def get_streak(current=Depends(get_current_user)):
    """Get the user's current daily challenge streak and today's completions."""
    user_id = str(current["user"].id)
    state = _get_user_daily(user_id)
    _reset_if_new_day(state)

    return DailyStreakResponse(
        streak=state["streak"],
        last_completed_date=state["last_completed_date"],
        today_completed_ids=state["today_completed_ids"],
        all_completed_today=len(state["today_completed_ids"]) >= CHALLENGES_PER_DAY,
    )


@daily_challenge_router.post(
    "/complete",
    response_model=CompleteChallengeResponse,
    status_code=status.HTTP_200_OK,
)
def complete_challenge(
    req: CompleteChallengeRequest,
    current=Depends(get_current_user),
):
    """Mark a daily challenge as completed and update streak."""
    user_id = str(current["user"].id)
    state = _get_user_daily(user_id)
    _reset_if_new_day(state)

    today = _today_str()

    # Add to completed if not already
    if req.challenge_id not in state["today_completed_ids"]:
        state["today_completed_ids"].append(req.challenge_id)

    # Check if all 3 completed → update streak
    all_done = len(state["today_completed_ids"]) >= CHALLENGES_PER_DAY
    if all_done and state["last_completed_date"] != today:
        if state["last_completed_date"]:
            last = datetime.strptime(state["last_completed_date"], "%Y-%m-%d").date()
            curr = datetime.strptime(today, "%Y-%m-%d").date()
            diff = (curr - last).days
            if diff == 1:
                state["streak"] += 1
            elif diff > 1:
                state["streak"] = 1
            # diff == 0 means already counted
        else:
            state["streak"] = 1
        state["last_completed_date"] = today

    return CompleteChallengeResponse(
        success=True,
        streak=state["streak"],
        today_completed_ids=state["today_completed_ids"],
        all_completed_today=all_done,
    )


@daily_challenge_router.post("/undo")
def undo_challenge(
    req: UndoChallengeRequest,
    current=Depends(get_current_user),
):
    """Remove a challenge from today's completed list."""
    user_id = str(current["user"].id)
    state = _get_user_daily(user_id)
    _reset_if_new_day(state)

    today = _today_str()
    was_all_done = len(state["today_completed_ids"]) >= CHALLENGES_PER_DAY

    if req.challenge_id in state["today_completed_ids"]:
        state["today_completed_ids"].remove(req.challenge_id)

    # If we undid from a completed day, roll back streak
    if was_all_done and state["last_completed_date"] == today:
        state["streak"] = max(0, state["streak"] - 1)
        state["last_completed_date"] = None

    return {
        "success": True,
        "streak": state["streak"],
        "today_completed_ids": state["today_completed_ids"],
        "all_completed_today": len(state["today_completed_ids"]) >= CHALLENGES_PER_DAY,
    }
