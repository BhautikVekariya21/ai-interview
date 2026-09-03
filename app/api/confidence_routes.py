"""
Confidence Pulse API Routes — Module 12.

Provides speech intelligence analysis endpoints. Full analysis (trajectory,
per-question breakdown, filler breakdown, and all coaching tips) is free for
all users.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.confidence_analyzer import get_confidence_analyzer


# ─── Schemas ──────────────────────────────────────────────────

class ConfidenceAnalyzeRequest(BaseModel):
    """Request body for confidence analysis."""
    qa_pairs: List[Dict[str, Any]] = Field(..., min_length=1)
    interview_duration_seconds: int = Field(default=0, ge=0)


class FillerWordEntry(BaseModel):
    word: str
    count: int


class CoachingTip(BaseModel):
    category: str
    icon: str
    title: str
    tip: str


class OverallMetrics(BaseModel):
    confidence_score: float = 0
    confidence_label: str = "No Data"
    vocabulary_richness: float = 0
    speaking_pace_wpm: int = 0
    pace_label: str = "unknown"
    filler_percentage: float = 0
    total_fillers: int = 0
    total_words: int = 0
    momentum: str = "stable"
    questions_answered: int = 0
    questions_total: int = 0


class ConfidenceReport(BaseModel):
    """Full confidence analysis response."""
    success: bool = True
    overall: OverallMetrics
    trajectory: List[int] = Field(default_factory=list)
    per_question: List[Dict[str, Any]] = Field(default_factory=list)
    filler_breakdown: List[FillerWordEntry] = Field(default_factory=list)
    coaching: List[CoachingTip] = Field(default_factory=list)


class HeatmapSegment(BaseModel):
    """A single scored sentence-level segment within an answer."""
    text: str
    score: int
    start_pct: float
    end_pct: float
    filler_words: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)


class HeatmapQuestion(BaseModel):
    """Heatmap segments for a single answer."""
    question_number: int
    question: str = ""
    segments: List[HeatmapSegment] = Field(default_factory=list)
    weakest_segment_index: Optional[int] = None
    skipped: bool = False


class HeatmapReport(BaseModel):
    """Interview Replay Heatmap response."""
    success: bool = True
    questions: List[HeatmapQuestion] = Field(default_factory=list)


# ─── Router ───────────────────────────────────────────────────

confidence_router = APIRouter(
    prefix="/confidence",
    tags=["Module 12: AI Confidence Pulse"],
)


@confidence_router.post(
    "/analyze",
    response_model=ConfidenceReport,
    summary="Analyze interview speech patterns",
)
async def analyze_confidence(request: ConfidenceAnalyzeRequest):
    """
    Analyze all Q&A pairs for confidence, filler words, vocab richness, pace, and momentum.

    Returns the full report: trajectory, per-question breakdown, filler
    breakdown, and all coaching tips.
    """
    if not request.qa_pairs:
        raise HTTPException(status_code=400, detail="qa_pairs cannot be empty")

    analyzer = get_confidence_analyzer()

    try:
        # Prepare qa_pairs
        qa_list = []
        for i, qa in enumerate(request.qa_pairs):
            qa_list.append({
                "question": str(qa.get("question", "")),
                "answer": str(qa.get("answer", "")),
                "category": str(qa.get("category", "T")),
                "question_number": int(qa.get("question_number", i + 1)),
            })

        result = analyzer.analyze(
            qa_pairs=qa_list,
            interview_duration_seconds=request.interview_duration_seconds,
        )

        logger.info(
            f"Confidence analysis complete: confidence={result['overall']['confidence_score']}, "
            f"fillers={result['overall']['total_fillers']}"
        )

        return ConfidenceReport(
            success=True,
            overall=OverallMetrics(**result["overall"]),
            trajectory=result["trajectory"],
            per_question=result["per_question"],
            filler_breakdown=[
                FillerWordEntry(**f) for f in result["filler_breakdown"]
            ],
            coaching=[CoachingTip(**c) for c in result["coaching"]],
        )

    except Exception as e:
        logger.error(f"Confidence analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@confidence_router.post(
    "/heatmap",
    response_model=HeatmapReport,
    summary="Sentence-level replay heatmap for interview answers",
)
async def analyze_heatmap(request: ConfidenceAnalyzeRequest):
    """
    Break each answer into sentence-level segments and score each one, so
    users can see exactly where inside an answer their confidence dipped.

    Segment position (start_pct/end_pct) is proportional to word count
    within the answer, not real audio timing.
    """
    if not request.qa_pairs:
        raise HTTPException(status_code=400, detail="qa_pairs cannot be empty")

    analyzer = get_confidence_analyzer()

    try:
        qa_list = []
        for i, qa in enumerate(request.qa_pairs):
            qa_list.append({
                "question": str(qa.get("question", "")),
                "answer": str(qa.get("answer", "")),
                "category": str(qa.get("category", "T")),
                "question_number": int(qa.get("question_number", i + 1)),
            })

        results = analyzer.analyze_heatmap(qa_list)

        return HeatmapReport(
            success=True,
            questions=[HeatmapQuestion(**q) for q in results],
        )

    except Exception as e:
        logger.error(f"Heatmap analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Heatmap analysis failed: {str(e)}")


@confidence_router.get("/health", summary="Health check")
async def health():
    """Check if confidence analysis service is ready."""
    return {"status": "healthy", "module": "12_confidence_pulse"}
