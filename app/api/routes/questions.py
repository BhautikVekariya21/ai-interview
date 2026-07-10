"""
FastAPI routes for question generation.

SECURITY:
  - No API keys exposed
  - No token counts exposed
  - No model names exposed
  - No raw LLM output exposed
  - Frontend sees ONLY clean question data
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.schemas.question_schemas import (
    QuestionGenerationRequest,
    QuestionSet,
    FollowUpRequest,
    FollowUpResponse,
)
from app.services.question_generator import QuestionGenerator


router = APIRouter(
    prefix="/api/v1/questions",
    tags=["questions"],
)

_generator: Optional[QuestionGenerator] = None


def _get_generator() -> QuestionGenerator:
    """Lazy singleton."""
    global _generator
    if _generator is None:
        _generator = QuestionGenerator()
    return _generator


@router.post(
    "/generate",
    response_model=QuestionSet,
    summary="Generate personalized interview questions",
    description=(
        "Analyzes resume and generates unique, personalized "
        "interview questions using AI. Each call produces "
        "different questions for the same resume."
    ),
)
async def generate_questions(
    request: QuestionGenerationRequest,
) -> QuestionSet:
    """
    Generate questions from resume data.
    Response contains ONLY question data — nothing internal.
    """
    try:
        generator = _get_generator()
        session_id = request.session_id or str(uuid.uuid4())

        logger.info(
            f"Question generation: "
            f"{request.num_questions} questions, "
            f"session={session_id[:8]}..."
        )

        result = generator.generate(
            resume_data=request.resume_data,
            num_questions=request.num_questions,
            categories=request.categories,
            session_id=session_id,
        )

        logger.info(
            f"Generated {result.total_questions} questions "
            f"for {result.candidate_name}"
        )

        return result

    except RuntimeError as e:
        # LLM completely failed — no providers available
        logger.error(f"Generation failed (runtime): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI service temporarily unavailable. "
                "Please try again in a few minutes."
            ),
        )
    except Exception as e:
        logger.error(f"Generation failed (unexpected): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate questions. Please try again.",
        )


@router.post(
    "/follow-up",
    response_model=FollowUpResponse,
    summary="Generate adaptive follow-up question",
)
async def generate_follow_up(
    request: FollowUpRequest,
) -> FollowUpResponse:
    """Generate follow-up based on candidate's answer."""
    try:
        generator = _get_generator()

        follow_up = generator.generate_follow_up(
            original_question=request.original_question,
            candidate_answer=request.candidate_answer,
            resume_data=request.resume_data,
        )

        return FollowUpResponse(
            question=follow_up,
            based_on_answer=request.candidate_answer[:200],
        )

    except Exception as e:
        logger.error(f"Follow-up failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate follow-up question.",
        )


@router.get(
    "/health",
    summary="Service health check",
)
async def health_check():
    """
    Health check — ONLY availability status.
    No model names, no keys, no internal details.
    """
    try:
        generator = _get_generator()
        return {
            "status": "healthy",
            "ai_available": generator.llm.is_available,
            "classifier": "ready",
            "version": "2.0",
        }
    except Exception:
        return {
            "status": "degraded",
            "ai_available": False,
            "classifier": "unknown",
            "version": "2.0",
        }