from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from app.api.auth_routes import get_current_user
from app.repositories.history_repository import HistoryRepository
from app.services.mysql_service import MySQLService, get_mysql, get_mysql_health

history_router = APIRouter(prefix="/history", tags=["History"])

class FinalScores(BaseModel):
    overall: int
    completionRate: int

class HistoryCreate(BaseModel):
    candidateName: str
    finalScores: FinalScores
    finalGrade: str
    totalQuestions: int
    date: Optional[str] = None
    details_json: Optional[str] = None

class HistoryResponse(HistoryCreate):
    id: str


def get_history_repository(db: MySQLService = Depends(get_mysql)) -> HistoryRepository:
    return HistoryRepository(db)


def _row_to_response(row) -> HistoryResponse:
    return HistoryResponse(
        id=f"{row.user_id}_{row.created_at.timestamp()}",
        candidateName=row.candidate_name,
        date=row.created_at.isoformat() if row.created_at else None,
        finalScores=FinalScores(
            overall=row.overall_score,
            completionRate=row.completion_rate,
        ),
        finalGrade=row.final_grade,
        totalQuestions=row.total_questions,
        details_json=row.details_json,
    )


@history_router.get("/health")
def history_health():
    db = get_mysql_health()
    return {
        "status": "healthy" if db["status"] == "healthy" else "degraded",
        "service": "history",
        "mysql": db,
    }

@history_router.post("/", response_model=HistoryResponse, status_code=status.HTTP_201_CREATED)
def create_history_entry(
    entry: HistoryCreate,
    current=Depends(get_current_user),
    repo: HistoryRepository = Depends(get_history_repository),
):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    user_id = current["user"].id

    # Check for a duplicate entry within the last minute (dedup guard).
    existing = repo.find_duplicate(user_id, entry.candidateName, cutoff)
    if existing:
        return _row_to_response(existing)

    now = datetime.now(timezone.utc)
    repo.insert(
        user_id=user_id,
        created_at=now,
        candidate_name=entry.candidateName,
        overall_score=entry.finalScores.overall,
        completion_rate=entry.finalScores.completionRate,
        final_grade=entry.finalGrade,
        total_questions=entry.totalQuestions,
        details_json=entry.details_json,
    )

    return HistoryResponse(
        id=f"{user_id}_{now.timestamp()}",
        candidateName=entry.candidateName,
        date=now.isoformat(),
        finalScores=entry.finalScores,
        finalGrade=entry.finalGrade,
        totalQuestions=entry.totalQuestions,
        details_json=entry.details_json,
    )

@history_router.get("/", response_model=List[HistoryResponse])
def get_history(
    limit: int = 50,
    current=Depends(get_current_user),
    repo: HistoryRepository = Depends(get_history_repository),
):
    user_id = current["user"].id
    return [_row_to_response(row) for row in repo.list_for_user(user_id, limit)]

@history_router.delete("/")
def clear_history(current=Depends(get_current_user), repo: HistoryRepository = Depends(get_history_repository)):
    user_id = current["user"].id
    repo.delete_for_user(user_id)

    return {"message": "History cleared"}
