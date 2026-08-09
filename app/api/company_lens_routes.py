"""Company Lens — employer-published exams.

* Employer (authenticated):
    POST   /api/v1/lens/exams                 — create an exam from a JD
    GET    /api/v1/lens/exams                 — my exams
    GET    /api/v1/lens/exams/{exam_id}       — detail (questions + attempts)
    POST   /api/v1/lens/exams/{exam_id}/publish — mint a candidate share link
    DELETE /api/v1/lens/exams/{exam_id}

* Candidate (public — no account needed, token is the gate):
    GET  /api/v1/lens/directory?role=         — browse published exams (role search)
    GET  /api/v1/lens/share/{token}           — exam intro + questions
    POST /api/v1/lens/share/{token}/submit    — evaluate + persist an attempt
    GET  /api/v1/lens/attempts/{attempt_token} — a stored scorecard
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.auth_routes import get_current_user
from app.repositories.company_lens_repository import CompanyLensRepository, loads
from app.services.answer_evaluator import get_evaluator
from app.services.company_lens_service import (
    build_scorecard,
    generate_exam_questions,
    is_valid_token,
    mint_share_token,
)
from app.services.mysql_service import MySQLService, get_mysql

lens_router = APIRouter(
    prefix="/api/v1/lens",
    tags=["Company Lens"],
)


class ExamCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    target_role: str = Field(default="", max_length=160)
    job_description: str = Field(..., min_length=20, max_length=20000)
    question_count: int = Field(default=10, ge=3, le=20)
    difficulty: str = Field(default="medium")


class LensSubmitRequest(BaseModel):
    candidate_name: str = Field(..., min_length=1, max_length=255)
    answers: List[Dict[str, Any]] = Field(default_factory=list)


def _lens_repository(db: MySQLService) -> CompanyLensRepository:
    return CompanyLensRepository(db)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _question_dict(question: Any, *, include_ideal: bool) -> Dict[str, Any]:
    return {
        "id": str(question.id),
        "question_number": question.question_number,
        "question": question.question,
        "category": question.category,
        "difficulty": question.difficulty,
        "ideal_answer": question.ideal_answer if include_ideal else None,
    }


def _attempt_summary(attempt: Any) -> Dict[str, Any]:
    return {
        "id": str(attempt.id),
        "candidate_name": attempt.candidate_name,
        "overall_score": attempt.overall_score,
        "overall_grade": attempt.overall_grade,
        "recommendation": attempt.recommendation,
        "hire_decision": attempt.hire_decision,
        "attempt_token": attempt.attempt_token,
        "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
    }


def _exam_summary(exam: Any, attempt_count: int = 0) -> Dict[str, Any]:
    return {
        "id": str(exam.id),
        "title": exam.title,
        "target_role": exam.target_role,
        "question_count": exam.question_count,
        "difficulty": exam.difficulty,
        "status": exam.status,
        "share_token": exam.share_token,
        "attempts": attempt_count,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }


# ══════════════════════════════════════════════════════════════════════
#  Employer routes
# ══════════════════════════════════════════════════════════════════════


@lens_router.post(
    "/exams",
    summary="Create an exam from a job description",
)
def create_exam(
    payload: ExamCreateRequest,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """Generate a JD-grounded question set, persist the exam, and return it."""
    repo = _lens_repository(db)
    employer_id = str(current["user"].id)
    exam_id = str(uuid.uuid4())

    questions = generate_exam_questions(
        job_description=payload.job_description,
        target_role=payload.target_role,
        question_count=payload.question_count,
        difficulty=payload.difficulty,
    )
    if not questions:
        raise HTTPException(500, detail="Could not generate any exam questions")

    repo.create_exam(
        exam_id=exam_id,
        employer_id=employer_id,
        title=payload.title.strip(),
        target_role=payload.target_role.strip(),
        job_description=payload.job_description,
        question_count=len(questions),
        difficulty=payload.difficulty,
        status="draft",
        created_at=_utcnow(),
    )
    repo.save_questions(exam_id, questions)

    return {
        **_exam_summary(repo.get_exam(exam_id)),
        "job_description": payload.job_description,
        "questions": [_question_dict(q, include_ideal=True) for q in repo.get_questions(exam_id)],
        "attempts": [],
    }


@lens_router.get("/exams", summary="List my exams")
def list_exams(
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    repo = _lens_repository(db)
    exams = repo.list_exams_for_employer(str(current["user"].id))
    summaries = []
    for exam in exams:
        attempts = repo.list_attempts_for_exam(str(exam.id), limit=500)
        summaries.append(_exam_summary(exam, attempt_count=len(attempts)))
    return {"exams": summaries}


@lens_router.get("/exams/{exam_id}", summary="Exam detail with attempts")
def get_exam_detail(
    exam_id: str,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    repo = _lens_repository(db)
    exam = repo.get_exam(exam_id)
    _require_owner(exam, current)

    attempts = repo.list_attempts_for_exam(exam_id)
    return {
        **_exam_summary(exam, attempt_count=len(attempts)),
        "job_description": exam.job_description,
        "questions": [_question_dict(q, include_ideal=True) for q in repo.get_questions(exam_id)],
        "attempts": [_attempt_summary(a) for a in attempts],
    }


@lens_router.post("/exams/{exam_id}/publish", summary="Publish an exam and mint a share link")
def publish_exam(
    exam_id: str,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, str]:
    repo = _lens_repository(db)
    exam = repo.get_exam(exam_id)
    _require_owner(exam, current)

    token = exam.share_token or mint_share_token()
    repo.publish_exam(exam_id, token)
    return {"token": token}


@lens_router.delete("/exams/{exam_id}", summary="Delete an exam and its attempts")
def delete_exam(
    exam_id: str,
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, bool]:
    repo = _lens_repository(db)
    exam = repo.get_exam(exam_id)
    _require_owner(exam, current)
    repo.delete_exam(exam_id)
    return {"success": True}


def _require_owner(exam: Any, current: Any) -> None:
    if not exam:
        raise HTTPException(404, detail="Exam not found")
    if str(exam.employer_id) != str(current["user"].id):
        raise HTTPException(403, detail="Not your exam")


# ══════════════════════════════════════════════════════════════════════
#  Public candidate routes
# ══════════════════════════════════════════════════════════════════════


@lens_router.get(
    "/directory",
    summary="Public directory of published exams",
)
def exam_directory(
    role: str = Query(default="", max_length=120, description="Role phrase to search for"),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """Browse every published exam, optionally filtered by role.

    Public by design — published exams are meant to be discoverable so
    candidates can find and take them. Each entry carries its share token,
    which is the same gate the direct /lens/<token> link uses.
    """
    repo = _lens_repository(db)
    exams = repo.list_published_exams(search=role.strip())
    return {
        "exams": [
            _exam_summary(exam, attempt_count=repo.count_attempts_for_exam(str(exam.id)))
            for exam in exams
        ]
    }


@lens_router.get("/share/{token}", summary="Candidate-facing exam by share token")
def share_exam(
    token: str,
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    if not is_valid_token(token):
        raise HTTPException(404, detail="Exam link not found")
    repo = _lens_repository(db)
    exam = repo.get_exam_by_share_token(token)
    if not exam or exam.status != "published":
        raise HTTPException(404, detail="Exam link not found")
    questions = [
        _question_dict(q, include_ideal=False)
        for q in repo.get_questions(str(exam.id))
    ]
    return {
        "id": str(exam.id),
        "title": exam.title,
        "target_role": exam.target_role,
        "question_count": len(questions),
        "difficulty": exam.difficulty,
        "questions": questions,
    }


@lens_router.post("/share/{token}/submit", summary="Submit an exam attempt and get the scorecard")
def submit_exam(
    token: str,
    payload: LensSubmitRequest,
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    if not is_valid_token(token):
        raise HTTPException(404, detail="Exam link not found")
    repo = _lens_repository(db)
    exam = repo.get_exam_by_share_token(token)
    if not exam or exam.status != "published":
        raise HTTPException(404, detail="Exam link not found")

    questions = repo.get_questions(str(exam.id))
    answers_by_number = {}
    for a in payload.answers:
        if not isinstance(a, dict):
            continue
        try:
            number = int(a.get("question_number"))
        except (TypeError, ValueError):
            continue
        answers_by_number[number] = str(a.get("answer") or "")

    qa_pairs = [
        {
            "question_number": question.question_number,
            "question": question.question,
            "category": question.category,
            "answer": answers_by_number.get(question.question_number, ""),
        }
        for question in questions
    ]

    scorecard = build_scorecard(
        qa_pairs=qa_pairs,
        candidate_name=payload.candidate_name.strip(),
        exam_title=exam.title,
        evaluator=get_evaluator(),
    )

    attempt_id = str(uuid.uuid4())
    attempt_token = mint_share_token()
    repo.create_attempt(
        attempt_id=attempt_id,
        exam_id=str(exam.id),
        candidate_name=payload.candidate_name.strip(),
        attempt_token=attempt_token,
        scorecard=scorecard,
        created_at=_utcnow(),
    )
    repo.save_answers(attempt_id, scorecard.get("answers") or [])

    return {"scorecard": scorecard, "attempt_token": attempt_token}


@lens_router.get("/attempts/{attempt_token}", summary="Fetch a stored scorecard")
def attempt_scorecard(
    attempt_token: str,
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    if not is_valid_token(attempt_token):
        raise HTTPException(404, detail="Scorecard not found")
    repo = _lens_repository(db)
    attempt = repo.get_attempt_by_token(attempt_token)
    if not attempt:
        raise HTTPException(404, detail="Scorecard not found")

    answers = repo.get_answers(str(attempt.id))
    answer_rows = [
        {
            "question_number": row.question_number,
            "question": row.question,
            "category": row.category,
            "answer": row.answer,
            "score": row.score,
            "grade": row.grade,
            "feedback": row.feedback,
            "strengths": list(loads(row.strengths) or []),
            "improvements": list(loads(row.improvements) or []),
            "authenticity": loads(row.authenticity),
        }
        for row in answers
    ]

    exam = repo.get_exam(str(attempt.exam_id))
    exam_title = exam.title if exam else "Exam"

    return {
        "scorecard": {
            "candidate_name": attempt.candidate_name,
            "exam_title": exam_title,
            "overall_score": attempt.overall_score,
            "overall_grade": attempt.overall_grade,
            "recommendation": attempt.recommendation,
            "hire_decision": attempt.hire_decision,
            "summary": attempt.summary or "",
            "category_breakdown": loads(attempt.category_breakdown) or {},
            "answered_questions": len(answer_rows),
            "total_questions": len(answer_rows),
            "answers": answer_rows,
            "plagiarism_summary": loads(attempt.plagiarism_summary),
            "generated_by": attempt.generated_by or "evaluator",
        }
    }
