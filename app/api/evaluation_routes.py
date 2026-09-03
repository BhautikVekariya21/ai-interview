"""
Evaluation API routes — Module 5.
FIXED: Properly handles all data types.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from app.services.answer_evaluator import get_evaluator

# ─── REQUEST/RESPONSE SCHEMAS ─────────────────────────────────


class EvaluateAnswerRequest(BaseModel):
    """Request to evaluate a single answer."""

    session_id: str = Field(default="", min_length=0)
    question_id: str = Field(default="q1", min_length=0)
    question_number: int = Field(default=1, ge=1)
    question_text: str = Field(..., min_length=1)
    question_category: str = Field(default="T")
    answer_text: str = Field(..., min_length=1)
    resume_context: Optional[Dict[str, Any]] = None
    generate_followup: bool = True


class HintRequest(BaseModel):
    """Request to generate a hint for a question."""

    question_text: str = Field(..., min_length=1)


class EvaluationResult(BaseModel):
    """Single answer evaluation result."""

    success: bool = True
    score: int = Field(ge=0, le=100, default=0)
    grade: str = "Insufficient"
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    feedback: str = ""
    ideal_answer: Optional[str] = None
    followup_question: Optional[str] = None
    authenticity_report: Optional[Dict[str, Any]] = None
    word_count: int = 0
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class BatchEvaluationRequest(BaseModel):
    """Request to evaluate multiple answers."""

    session_id: str = ""
    qa_pairs: List[Dict[str, Any]]
    resume_context: Optional[Dict[str, Any]] = None
    candidate_name: Optional[str] = None


class BatchEvaluationResult(BaseModel):
    """Comprehensive batch evaluation result."""

    success: bool = True
    session_id: str = ""
    candidate_name: Optional[str] = None
    total_questions: int = 0
    answered_questions: int = 0
    overall_score: float = 0.0
    overall_grade: str = "Insufficient"
    recommendation: str = ""
    hire_decision: str = ""
    category_breakdown: Dict[str, Any] = Field(default_factory=dict)
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    strengths_overall: List[str] = Field(default_factory=list)
    improvements_overall: List[str] = Field(default_factory=list)
    plagiarism_summary: Dict[str, Any] = Field(default_factory=dict)
    interview_duration_estimate: str = "~10 minutes"


# ─── HELPER FUNCTIONS ─────────────────────────────────────────


def ensure_string_list(items: Any) -> List[str]:
    """Convert any input to a list of strings."""
    if items is None:
        return []

    if isinstance(items, str):
        return [items] if items.strip() else []

    if not isinstance(items, list):
        return [str(items)] if items else []

    result = []
    for item in items:
        if item is None:
            continue
        elif isinstance(item, str):
            if item.strip():
                result.append(item.strip())
        elif isinstance(item, dict):
            text = (
                item.get("text")
                or item.get("point")
                or item.get("strength")
                or item.get("improvement")
                or item.get("message")
                or ""
            )
            if isinstance(text, str) and text.strip():
                result.append(text.strip())
        else:
            text = str(item).strip()
            if text and text not in ["None", "null", "{}", "[]"]:
                result.append(text)

    return result


# ─── ROUTER ───────────────────────────────────────────────────


evaluation_router = APIRouter(
    prefix="/evaluation",
    tags=["Module 5: Answer Evaluation"],
)


@evaluation_router.post(
    "/evaluate",
    response_model=EvaluationResult,
    summary="Evaluate a single answer",
)
async def evaluate_answer(request: EvaluateAnswerRequest):
    """Evaluate a candidate's answer to an interview question."""
    evaluator = get_evaluator()

    if not request.answer_text or len(request.answer_text.strip()) < 3:
        return EvaluationResult(
            success=False,
            score=0,
            grade="Insufficient",
            strengths=[],
            improvements=["No answer provided"],
            feedback="Please provide an answer to evaluate.",
            error="Answer text is required",
        )

    if not request.question_text or len(request.question_text.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question text is required")

    try:
        result = evaluator.evaluate(
            question=request.question_text,
            answer=request.answer_text,
            question_category=request.question_category,
            resume_context=request.resume_context,
            generate_followup=request.generate_followup,
        )

        # Ensure string lists
        result["strengths"] = ensure_string_list(result.get("strengths"))
        result["improvements"] = ensure_string_list(result.get("improvements"))

        logger.info(
            f"Evaluation complete: Q{request.question_number} - "
            f"Score: {result.get('score', 0)}, Grade: {result.get('grade', 'Unknown')}"
        )


        return EvaluationResult(**result)

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return EvaluationResult(
            success=False,
            score=0,
            grade="Error",
            strengths=[],
            improvements=[],
            feedback=f"Evaluation error: {str(e)}",
            error=str(e),
        )


@evaluation_router.post(
    "/evaluate-batch",
    response_model=BatchEvaluationResult,
    summary="Evaluate all interview answers (End Interview)",
)
async def evaluate_batch(request: BatchEvaluationRequest):
    """Evaluate all Q&A pairs and generate comprehensive assessment."""
    evaluator = get_evaluator()

    if not request.qa_pairs:
        raise HTTPException(status_code=400, detail="qa_pairs list cannot be empty")

    try:
        # Convert qa_pairs to proper format
        qa_list = []
        for i, qa in enumerate(request.qa_pairs):
            if isinstance(qa, dict):
                qa_list.append(
                    {
                        "question": str(qa.get("question", "")),
                        "answer": str(qa.get("answer", "")),
                        "category": str(qa.get("category", "T")),
                        "question_id": str(qa.get("question_id", f"q{i + 1}")),
                        "question_number": int(qa.get("question_number", i + 1)),
                    }
                )
            else:
                qa_list.append(
                    {
                        "question": "",
                        "answer": "",
                        "category": "T",
                        "question_id": f"q{i + 1}",
                        "question_number": i + 1,
                    }
                )

        logger.info(f"Batch evaluation starting: {len(qa_list)} questions")

        # Call evaluator
        result = evaluator.evaluate_batch(
            qa_pairs=qa_list,
            resume_context=request.resume_context,
        )

        # Add candidate info
        result["candidate_name"] = request.candidate_name
        result["session_id"] = request.session_id

        # Calculate answered questions
        answered = len([qa for qa in qa_list if qa.get("answer", "").strip()])
        result["answered_questions"] = answered

        # Hire decision
        score = result.get("overall_score", 0)
        if score >= 80:
            result["hire_decision"] = "✅ STRONG HIRE"
        elif score >= 65:
            result["hire_decision"] = "👍 HIRE"
        elif score >= 50:
            result["hire_decision"] = "🤔 MAYBE - Additional Screening Recommended"
        else:
            result["hire_decision"] = "❌ NO HIRE"

        # Interview duration estimate
        total_words = sum(len(qa.get("answer", "").split()) for qa in qa_list)
        minutes = max(5, total_words // 150)
        result["interview_duration_estimate"] = f"~{minutes} minutes"

        # Category breakdown grades
        cat_breakdown = {}
        for cat_name, cat_data in result.get("category_breakdown", {}).items():
            if isinstance(cat_data, dict):
                avg = cat_data.get("average_score", 0)
                if avg >= 80:
                    grade = "Excellent"
                elif avg >= 65:
                    grade = "Good"
                elif avg >= 50:
                    grade = "Fair"
                else:
                    grade = "Needs Work"

                cat_breakdown[cat_name] = {
                    "average_score": avg,
                    "questions_count": cat_data.get("questions_count", 0),
                    "grade": grade,
                }
        result["category_breakdown"] = cat_breakdown

        # Extract overall strengths/improvements (ensure strings)
        all_strengths: List[str] = []
        all_improvements: List[str] = []

        for ev in result.get("evaluations", []):
            if ev.get("score", 0) >= 70:
                strengths = ensure_string_list(ev.get("strengths", []))
                if strengths:
                    all_strengths.append(strengths[0])

            if ev.get("score", 0) < 60:
                improvements = ensure_string_list(ev.get("improvements", []))
                if improvements:
                    all_improvements.append(improvements[0])

        # Deduplicate and limit
        result["strengths_overall"] = list(dict.fromkeys(all_strengths))[:5]
        result["improvements_overall"] = list(dict.fromkeys(all_improvements))[:5]

        logger.info(
            f"Batch evaluation complete: {result['total_questions']} questions, "
            f"Overall: {result['overall_score']:.1f}/100 ({result['overall_grade']})"
        )


        return BatchEvaluationResult(**result)

    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")


@evaluation_router.post("/evaluate-simple", summary="Simple evaluation (test)")
async def evaluate_simple(
    question: str = Query(..., min_length=3),
    answer: str = Query(..., min_length=3),
    category: str = Query(default="T"),
):
    """Simple evaluation for testing."""
    evaluator = get_evaluator()
    result = evaluator.evaluate(
        question=question,
        answer=answer,
        question_category=category,
        generate_followup=True,
    )
    return result


@evaluation_router.get("/rubric", summary="Get evaluation rubric")
async def get_rubric():
    """Get the evaluation rubric."""
    return {
        "scoring_ranges": {
            "Exceptional": {"min": 90, "max": 100},
            "Strong": {"min": 75, "max": 89},
            "Adequate": {"min": 60, "max": 74},
            "Needs Work": {"min": 40, "max": 59},
            "Insufficient": {"min": 0, "max": 39},
        },
        "hire_thresholds": {
            "strong_hire": {"min": 80, "label": "✅ STRONG HIRE"},
            "hire": {"min": 65, "label": "👍 HIRE"},
            "maybe": {"min": 50, "label": "🤔 MAYBE"},
            "no_hire": {"min": 0, "label": "❌ NO HIRE"},
        },
    }


@evaluation_router.post("/hint", summary="Generate a hint for a question")
async def generate_hint(request: HintRequest):
    """Generate a contextual hint for an interview question."""
    evaluator = get_evaluator()
    hint = evaluator.generate_hint(request.question_text)
    return {"hint": hint}


@evaluation_router.get("/health", summary="Health check")
async def health_check():
    """Check if evaluation service is operational."""
    evaluator = get_evaluator()
    has_llm = evaluator._llm is not None

    return {
        "status": "healthy" if has_llm else "degraded",
        "llm_available": has_llm,
        "llm_provider": evaluator._llm.active_provider if evaluator._llm is not None else None,
        "fallback_mode": not has_llm,
    }
