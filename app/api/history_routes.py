import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from app.api.auth_routes import get_current_user
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
    db: MySQLService = Depends(get_mysql),
):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    user_id = current["user"].id
    
    s = db.get_session()
    
    # Check for a duplicate entry within the last minute (dedup guard).
    existing_rows = s.execute(
        "SELECT * FROM history WHERE user_id=%s ORDER BY created_at DESC LIMIT 5", (user_id,)
    )
    
    existing = None
    for row in existing_rows:
        if row.candidate_name == entry.candidateName and row.created_at >= cutoff:
            existing = row
            break

    if existing:
        return HistoryResponse(
            id=f"{existing.user_id}_{existing.created_at.timestamp()}",
            candidateName=existing.candidate_name,
            date=existing.created_at.isoformat(),
            finalScores=FinalScores(
                overall=existing.overall_score,
                completionRate=existing.completion_rate,
            ),
            finalGrade=existing.final_grade,
            totalQuestions=existing.total_questions,
            details_json=existing.details_json,
        )

    now = datetime.now(timezone.utc)
    s.execute(
        """
        INSERT INTO history (user_id, created_at, candidate_name, overall_score, completion_rate, final_grade, total_questions, details_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, now, entry.candidateName, entry.finalScores.overall, entry.finalScores.completionRate, entry.finalGrade, entry.totalQuestions, entry.details_json)
    )
    
    history_id = f"{user_id}_{now.timestamp()}"

    return HistoryResponse(
        id=history_id,
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
    db: MySQLService = Depends(get_mysql),
):
    user_id = current["user"].id
    s = db.get_session()
    
    entries = s.execute(
        "SELECT * FROM history WHERE user_id=%s ORDER BY created_at DESC LIMIT %s", (user_id, limit)
    )
    
    results = []
    for db_entry in entries:
        results.append(HistoryResponse(
            id=f"{db_entry.user_id}_{db_entry.created_at.timestamp()}",
            candidateName=db_entry.candidate_name,
            date=db_entry.created_at.isoformat() if db_entry.created_at else None,
            finalScores=FinalScores(
                overall=db_entry.overall_score,
                completionRate=db_entry.completion_rate,
            ),
            finalGrade=db_entry.final_grade,
            totalQuestions=db_entry.total_questions,
            details_json=db_entry.details_json
        ))
    return results

@history_router.delete("/")
def clear_history(current=Depends(get_current_user), db: MySQLService = Depends(get_mysql)):
    user_id = current["user"].id
    s = db.get_session()
    s.execute("DELETE FROM history WHERE user_id=%s", (user_id,))

    return {"message": "History cleared"}
