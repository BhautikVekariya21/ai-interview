"""The Gauntlet API routes.

Stateless adaptive-pressure endpoints. The frontend already holds the
evaluation evidence, so the engine is a pure function of what the client
sends — no tables, no session state on the server.

* POST /api/v1/gauntlet/advance — next pressure move given recent scores
* GET  /api/v1/gauntlet/personas — the persona pool The Gauntlet shifts into
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.gauntlet_service import (
    MAX_LEVEL,
    evaluate_step,
    personas,
)

gauntlet_router = APIRouter(
    prefix="/api/v1/gauntlet",
    tags=["The Gauntlet"],
)


class GauntletStepRequest(BaseModel):
    recent_scores: List[float] = Field(
        default_factory=list,
        description="Evaluation scores for answered questions (0-100)",
    )
    current_level: int = Field(default=1, ge=1, le=10)
    answered_count: int = Field(default=0, ge=0)
    momentum: str = Field(default="stable")
    max_level: int = Field(default=MAX_LEVEL, ge=1, le=10)


@gauntlet_router.post(
    "/advance",
    summary="Compute the next adaptive-pressure move",
)
def advance(payload: GauntletStepRequest) -> Dict[str, Any]:
    """Given the candidate's recent scores and the current pressure level,
    decide the next move: escalate with tougher follow-ups or interruptions,
    shift to a colder persona, apply time pressure, or ease off."""
    return evaluate_step(
        recent_scores=payload.recent_scores,
        current_level=payload.current_level,
        answered_count=payload.answered_count,
        momentum=payload.momentum,
        max_level=payload.max_level,
    )


@gauntlet_router.get("/personas", summary="The Gauntlet persona pool")
def persona_pool() -> Dict[str, Any]:
    return {"personas": personas()}


@gauntlet_router.get("/health", summary="Health check")
def health() -> Dict[str, str]:
    return {"status": "healthy", "module": "gauntlet"}
