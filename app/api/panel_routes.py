"""
Module 13 — AI Panel Interview API routes.

Exposes the multi-persona panel: persona roster, live per-answer reactions, and
the closing deliberation with a weighted hire / no-hire verdict.

SECURITY (mirrors questions.py):
  - No API keys, model names, or token counts exposed.
  - Internal persona agendas/prompts never leave the backend.
  - Frontend sees ONLY clean, character-safe panel data.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from loguru import logger

from app.services.panel_service import get_panel_service, get_personas_public


# ─── Schemas ──────────────────────────────────────────────────

class PersonaCard(BaseModel):
    id: str
    name: str
    role: str
    emoji: str
    accent: str
    temperament: str


class PersonaListResponse(BaseModel):
    success: bool = True
    personas: List[PersonaCard] = Field(default_factory=list)


class PanelReactRequest(BaseModel):
    persona_id: str = Field(..., description="Which panelist reacts")
    question: str = Field(..., min_length=1, max_length=4000)
    answer: str = Field(default="", max_length=8000)
    category: str = Field(default="T", description="Question category code")


class PanelReactResponse(BaseModel):
    success: bool = True
    persona_id: str
    name: str
    role: str
    emoji: str
    accent: str
    reaction: str
    follow_up: str = ""
    impression: str = "neutral"
    lean: int = 0


class TranscriptItem(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    answer: str = Field(default="", max_length=8000)
    category: str = "T"


class PanelDeliberateRequest(BaseModel):
    candidate_name: str = Field(default="Candidate", max_length=120)
    transcript: List[TranscriptItem] = Field(..., min_length=1, max_length=40)


class PanelMember(BaseModel):
    persona_id: str
    name: str
    role: str
    emoji: str
    accent: str
    argument: str
    vote: str
    confidence: int
    one_line: str


class PanelVerdict(BaseModel):
    decision: str
    hire_votes: int
    total_votes: int
    confidence: int
    summary: str


class PanelDeliberateResponse(BaseModel):
    success: bool = True
    candidate_name: str
    average_score: int
    members: List[PanelMember] = Field(default_factory=list)
    verdict: PanelVerdict


# ─── Router ───────────────────────────────────────────────────

panel_router = APIRouter(
    prefix="/api/v1/panel",
    tags=["Module 13: AI Panel Interview"],
)


@panel_router.get(
    "/personas",
    response_model=PersonaListResponse,
    summary="List the AI interview panel personas",
)
async def list_personas() -> PersonaListResponse:
    return PersonaListResponse(personas=get_personas_public())


@panel_router.post(
    "/react",
    response_model=PanelReactResponse,
    summary="Get one panelist's live reaction to an answer",
)
async def panel_react(request: PanelReactRequest) -> PanelReactResponse:
    try:
        service = get_panel_service()
        result = service.react(
            persona_id=request.persona_id,
            question=request.question,
            answer=request.answer,
            question_category=request.category,
        )
        return PanelReactResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Panel react failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Panel reaction failed",
        )


@panel_router.post(
    "/deliberate",
    response_model=PanelDeliberateResponse,
    summary="Run the closing panel deliberation and verdict",
)
async def panel_deliberate(
    request: PanelDeliberateRequest,
) -> PanelDeliberateResponse:
    try:
        service = get_panel_service()
        transcript: List[Dict[str, Any]] = [t.model_dump() for t in request.transcript]
        result = service.deliberate(
            candidate_name=request.candidate_name,
            transcript=transcript,
        )
        return PanelDeliberateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Panel deliberation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Panel deliberation failed",
        )
