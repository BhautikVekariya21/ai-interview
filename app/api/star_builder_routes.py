"""
STAR Builder API Routes — AI-powered generation and improvement
of STAR method interview stories.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

star_builder_router = APIRouter(prefix="/star-builder", tags=["STAR Builder"])


# ─── Schemas ──────────────────────────────────────────────


class GenerateStarRequest(BaseModel):
    situation_context: str = Field(..., min_length=10, max_length=2000)
    role: Optional[str] = None
    skills: Optional[List[str]] = None


class ImproveStarRequest(BaseModel):
    situation: str = Field(..., min_length=5, max_length=2000)
    task: str = Field(..., min_length=5, max_length=2000)
    action: str = Field(..., min_length=5, max_length=3000)
    result: str = Field(..., min_length=5, max_length=2000)


# ─── Endpoints ────────────────────────────────────────────


@star_builder_router.post("/generate")
async def generate_star_story(req: GenerateStarRequest):
    """Generate a STAR story skeleton from a situation context using AI."""
    from app.services.star_builder_service import get_star_builder_service

    try:
        service = get_star_builder_service()
        return service.generate_star_story(
            situation_context=req.situation_context,
            role=req.role,
            skills=req.skills,
        )
    except Exception as e:
        logger.exception(f"STAR generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate STAR story.")


@star_builder_router.post("/improve")
async def improve_star_story(req: ImproveStarRequest):
    """Improve an existing STAR story draft using AI."""
    from app.services.star_builder_service import get_star_builder_service

    try:
        service = get_star_builder_service()
        return service.improve_star_story(
            situation=req.situation,
            task=req.task,
            action=req.action,
            result=req.result,
        )
    except Exception as e:
        logger.exception(f"STAR improvement failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to improve STAR story.")
