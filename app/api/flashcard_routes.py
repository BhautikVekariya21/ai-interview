"""
Flashcard Progress API Routes — server-side persistence for authenticated users.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.api.auth_routes import get_current_user

flashcard_router = APIRouter(prefix="/flashcards", tags=["Flashcards"])

class FlashcardProgressEntry(BaseModel):
    card_id: str
    status: str = "unseen"
    times_reviewed: int = 0
    last_reviewed: Optional[str] = None

class FlashcardProgressResponse(BaseModel):
    total_cards_studied: int = 0
    mastered_count: int = 0
    learning_count: int = 0
    progress: Dict[str, dict] = Field(default_factory=dict)
    study_streak: int = 0
    last_study_date: Optional[str] = None

class UpdateCardRequest(BaseModel):
    card_id: str = Field(..., min_length=1)
    topic_id: str = Field(..., min_length=1)
    status: str = Field(..., pattern="^(unseen|learning|mastered)$")

_flashcard_store: dict[str, dict] = {}

def _get_user_flashcards(user_id: str) -> dict:
    if user_id not in _flashcard_store:
        _flashcard_store[user_id] = {"progress": {}, "study_streak": 0, "last_study_date": None}
    return _flashcard_store[user_id]

@flashcard_router.get("/progress", response_model=FlashcardProgressResponse)
def get_progress(current=Depends(get_current_user)):
    user_id = str(current["user"].id)
    state = _get_user_flashcards(user_id)
    progress = state["progress"]
    mastered = sum(1 for v in progress.values() if v.get("status") == "mastered")
    learning = sum(1 for v in progress.values() if v.get("status") == "learning")
    return FlashcardProgressResponse(
        total_cards_studied=len(progress), mastered_count=mastered,
        learning_count=learning, progress=progress,
        study_streak=state.get("study_streak", 0),
        last_study_date=state.get("last_study_date"),
    )

@flashcard_router.post("/progress")
def update_progress(req: UpdateCardRequest, current=Depends(get_current_user)):
    user_id = str(current["user"].id)
    state = _get_user_flashcards(user_id)
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    card_key = f"{req.topic_id}:{req.card_id}"
    existing = state["progress"].get(card_key, {})
    state["progress"][card_key] = {
        "status": req.status,
        "times_reviewed": existing.get("times_reviewed", 0) + 1,
        "last_reviewed": now.isoformat(),
    }
    last_date = state.get("last_study_date")
    if last_date != today:
        if last_date:
            diff = (now.date() - datetime.fromisoformat(last_date).date()).days
            state["study_streak"] = (state.get("study_streak", 0) + 1) if diff == 1 else 1
        else:
            state["study_streak"] = 1
        state["last_study_date"] = today
    return {"success": True, "card_id": card_key, "status": req.status}

@flashcard_router.delete("/progress")
def reset_progress(current=Depends(get_current_user)):
    user_id = str(current["user"].id)
    _flashcard_store[user_id] = {"progress": {}, "study_streak": 0, "last_study_date": None}
    return {"success": True, "message": "Flashcard progress reset."}
