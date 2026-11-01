"""
STAR Coach API Routes (Module 18).

Behavioral-answer structure analyzer exposed over HTTP. Works entirely with
captured transcript text — no LLM provider needed — so the frontend STAR
panel works out of the box in demo mode.

* POST /star/analyze — one or many behavioral answers → per-answer STAR report
* GET  /star/health  — health check
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from app.services.star_analyzer import get_star_analyzer

star_router = APIRouter(
    prefix="/star",
    tags=["Module 18: STAR Coach"],
)


class STARAnswer(BaseModel):
    """One behavioral answer to analyze."""

    question: str = ""
    answer: str
    question_number: int = 1


class STARAnalyzeRequest(BaseModel):
    """Request body — accepts either `answer` (single) or `answers[]` (many)."""

    answer: str = ""
    answers: List[STARAnswer] = Field(default_factory=list)


class STARAnswerReport(BaseModel):
    question_number: int
    question: str
    skipped: bool
    star: Dict[str, float]
    structure_score: int
    grade: str
    missing: List[str]
    coaching: List[str]
    highlights: Dict[str, Any]
    words: int


class STARSessionSummary(BaseModel):
    answers_total: int
    answers_analyzed: int
    avg_structure_score: int
    grade: str
    weakest_dimension: str | None = None
    strongest_dimension: str | None = None


class STARReport(BaseModel):
    success: bool = True
    answers: List[STARAnswerReport]
    summary: STARSessionSummary


@star_router.post(
    "/analyze",
    response_model=STARReport,
    summary="Analyze behavioral answer(s) for STAR structure",
)
def analyze_star(request: STARAnalyzeRequest) -> STARReport:
    """
    Score behavioral answers against the STAR framework.

    Pass either a single `answer` string or a list of `answers` (question text
    optional). Returns per-answer S/T/A/R dimension scores, structuredness
    grade, missing-dimension list, and targeted coaching tips.
    """
    pairs: List[Dict[str, Any]] = []
    if request.answers:
        if len(request.answers) > 50:
            raise HTTPException(status_code=400, detail="answers cannot exceed 50 items")
        pairs = [a.model_dump() for a in request.answers]
    elif request.answer:
        pairs = [{"question": "", "answer": request.answer, "question_number": 1}]
    else:
        raise HTTPException(status_code=400, detail="Provide 'answer' (string) or 'answers' (list)")

    try:
        analyzer = get_star_analyzer()

        # Feed the single-answer form through the session pipeline so summary
        # always has ≥1 report.
        reports = analyzer.analyze_session(pairs) if pairs else []
        summary = analyzer.summarize(reports)

        return STARReport(
            success=True,
            answers=[STARAnswerReport(**r) for r in reports],
            summary=STARSessionSummary(**summary),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"STAR analysis failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="STAR analysis failed")


@star_router.get("/health", summary="Health check")
def health() -> Dict[str, str]:
    """Check if the STAR analyzer is ready."""
    return {"status": "healthy", "module": "18_star_coach"}
