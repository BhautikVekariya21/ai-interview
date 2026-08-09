"""Evidence coaching API routes.

Two stateless endpoints over evidence the frontend already holds:

* POST /api/v1/evidence/gap-report — resume-vs-reality action plan
* POST /api/v1/evidence/coach-tip  — between-question delivery tip

Stateless by design: no tables, no migrations, works against a read-only
database, and is trivially testable.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.evidence_service import (
    generate_coach_tip,
    generate_gap_report,
)

evidence_router = APIRouter(
    prefix="/api/v1/evidence",
    tags=["Verified Interview"],
)


# ─── Schemas ────────────────────────────────────────────────────────────


class GapReportRequest(BaseModel):
    resume_data: Optional[Dict[str, Any]] = Field(default=None)
    ats_report: Optional[Dict[str, Any]] = Field(
        default=None, description="ATS report, if one was computed at parse time"
    )
    assessments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Resume Proof Map rows: [{label, kind, status, ...}]",
    )
    candidate_name: str = Field(default="")
    target_role: str = Field(default="")


class CoachTipRequest(BaseModel):
    answer_text: str = Field(default="")
    word_count: Optional[int] = Field(default=None, ge=0)
    filler_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    filler_count: Optional[int] = Field(default=None, ge=0)
    wpm: Optional[int] = Field(default=None, ge=0)
    confidence_score: Optional[float] = Field(default=None, ge=0, le=100)
    momentum: str = Field(default="stable")
    question: str = Field(default="")


# ─── Routes ─────────────────────────────────────────────────────────────


@evidence_router.post("/gap-report", summary="Resume-vs-reality improvement plan")
def gap_report(payload: GapReportRequest) -> Dict[str, Any]:
    """Turn Resume Proof Map findings plus ATS keyword gaps into a concrete
    practice plan. Falls back to a deterministic plan when no LLM is
    configured."""
    return generate_gap_report(
        resume_data=payload.resume_data,
        ats_report=payload.ats_report,
        assessments=payload.assessments,
        candidate_name=payload.candidate_name,
        target_role=payload.target_role,
    )


@evidence_router.post("/coach-tip", summary="Between-question delivery tip")
def coach_tip(payload: CoachTipRequest) -> Dict[str, str]:
    """A single focused delivery tip computed from the last answer's speech
    signals. Deterministic and instant — safe to call between questions."""
    return generate_coach_tip(
        answer_text=payload.answer_text,
        word_count=payload.word_count,
        filler_percentage=payload.filler_percentage,
        filler_count=payload.filler_count,
        wpm=payload.wpm,
        confidence_score=payload.confidence_score,
        momentum=payload.momentum,
        question=payload.question,
    )


@evidence_router.get("/health", summary="Health check")
def health() -> Dict[str, str]:
    return {"status": "healthy", "module": "evidence_coaching"}
