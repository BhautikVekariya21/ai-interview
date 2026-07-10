"""
System Design API Routes — AI-powered evaluation of system design answers.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

system_design_router = APIRouter(prefix="/system-design", tags=["System Design"])

class EvaluateRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=3000)
    answer: str = Field(..., min_length=20, max_length=10000)
    topic: str = ""

@system_design_router.post("/evaluate")
async def evaluate_system_design(req: EvaluateRequest):
    """Evaluate a system design answer using AI with multi-criteria scoring."""
    from app.services.system_design_service import get_system_design_service
    try:
        service = get_system_design_service()
        return service.evaluate_answer(
            question=req.question, answer=req.answer, topic=req.topic,
        )
    except Exception as e:
        logger.exception(f"System design evaluation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate system design answer.")
