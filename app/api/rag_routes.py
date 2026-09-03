"""RAG endpoints — Module 14: Retrieval-Augmented Generation.

Exposes session index building, grounded question generation, and rubric-based
answer scoring. Request/response schemas live in app/schemas/rag_schemas.py (the
single source of truth); this module only wires them to handlers. The service is
synchronous (model inference + FAISS), so handlers offload it to a thread to
avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.schemas.rag_schemas import (
    AdjustDifficultyRequest,
    AdjustDifficultyResponse,
    BuildIndexRequest,
    BuildIndexResponse,
    CompanyContextRequest,
    CompanyContextResponse,
    DetectSimilarityRequest,
    DetectSimilarityResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    GenerateQuestionRequest,
    GenerateQuestionResponse,
    GenerateReportRequest,
    GenerateReportResponse,
)
from app.services.rag.metrics import track_endpoint
from app.services.rag_service import get_rag_service

rag_router = APIRouter(
    prefix="/rag",
    tags=["Module 14: Retrieval-Augmented Generation"],
)


# ───────────────────────────────── endpoints ────────────────────────────────


@rag_router.post("/build-index", response_model=BuildIndexResponse, summary="Build/refresh a session's FAISS index")
async def build_index(request: BuildIndexRequest) -> BuildIndexResponse:
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text cannot be empty")
    service = get_rag_service()
    try:
        count = await asyncio.to_thread(
            service.build_session_index,
            request.candidate_id,
            request.resume_text,
            request.job_description,
            request.role,
        )
        return BuildIndexResponse(candidate_id=request.candidate_id, chunks_indexed=count)
    except Exception as e:
        logger.error(f"RAG build-index failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Index build failed: {str(e)}")


@rag_router.post("/generate-question", response_model=GenerateQuestionResponse, summary="Retrieve + generate a grounded question")
async def generate_question(request: GenerateQuestionRequest) -> GenerateQuestionResponse:
    service = get_rag_service()
    try:
        async with track_endpoint("generate-question"):
            result: Dict[str, Any] = await asyncio.to_thread(
                service.generate_question,
                request.candidate_id,
                request.role,
                request.last_answer,
                request.asked_questions,
                request.difficulty,
                request.company_id,
            )
        return GenerateQuestionResponse(**result)
    except ValueError as e:
        # No session index yet — client must call /rag/build-index first.
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"RAG generate-question failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@rag_router.post("/evaluate-answer", response_model=EvaluateAnswerResponse, summary="Retrieve rubric + score an answer")
async def evaluate_answer(request: EvaluateAnswerRequest) -> EvaluateAnswerResponse:
    if not request.candidate_answer.strip():
        raise HTTPException(status_code=400, detail="candidate_answer cannot be empty")
    service = get_rag_service()
    try:
        result: Dict[str, Any] = await asyncio.to_thread(
            service.evaluate_answer,
            request.question,
            request.candidate_answer,
            request.role,
            request.candidate_id,
        )
        return EvaluateAnswerResponse(**result)
    except Exception as e:
        logger.error(f"RAG evaluate-answer failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Answer evaluation failed: {str(e)}")


@rag_router.post("/detect-similarity", response_model=DetectSimilarityResponse, summary="Flag near-duplicate answers (proctoring)")
async def detect_similarity(request: DetectSimilarityRequest) -> DetectSimilarityResponse:
    if not request.answer.strip():
        raise HTTPException(status_code=400, detail="answer cannot be empty")
    service = get_rag_service()
    try:
        result: Dict[str, Any] = await asyncio.to_thread(
            service.detect_similarity,
            request.answer,
            request.role,
            request.candidate_id,
            request.threshold,
        )
        return DetectSimilarityResponse(**result)
    except Exception as e:
        logger.error(f"RAG detect-similarity failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Similarity detection failed: {str(e)}")


@rag_router.post("/adjust-difficulty", response_model=AdjustDifficultyResponse, summary="Recommend next question difficulty")
async def adjust_difficulty(request: AdjustDifficultyRequest) -> AdjustDifficultyResponse:
    service = get_rag_service()
    try:
        result: Dict[str, Any] = await asyncio.to_thread(
            service.adjust_difficulty,
            request.role,
            request.recent_answers,
            request.current_difficulty,
        )
        return AdjustDifficultyResponse(**result)
    except Exception as e:
        logger.error(f"RAG adjust-difficulty failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Difficulty adjustment failed: {str(e)}")


@rag_router.post("/company-context", response_model=CompanyContextResponse, summary="Index per-company role docs")
async def company_context(request: CompanyContextRequest) -> CompanyContextResponse:
    if not request.documents:
        raise HTTPException(status_code=400, detail="documents cannot be empty")
    service = get_rag_service()
    try:
        count = await asyncio.to_thread(
            service.add_company_docs,
            request.company_id,
            request.documents,
            request.role,
        )
        return CompanyContextResponse(company_id=request.company_id, chunks_indexed=count)
    except Exception as e:
        logger.error(f"RAG company-context failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Company context indexing failed: {str(e)}")


@rag_router.post("/generate-report", response_model=GenerateReportResponse, summary="Grounded final interview report")
async def generate_report(request: GenerateReportRequest) -> GenerateReportResponse:
    if not request.qa_pairs:
        raise HTTPException(status_code=400, detail="qa_pairs cannot be empty")
    service = get_rag_service()
    try:
        result: Dict[str, Any] = await asyncio.to_thread(
            service.generate_report,
            request.session_id,
            request.role,
            [qa.model_dump() for qa in request.qa_pairs],
            request.candidate_name,
        )
        return GenerateReportResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"RAG generate-report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@rag_router.get("/health", summary="RAG module health")
async def rag_health() -> Dict[str, Any]:
    try:
        service = get_rag_service()
        return {"status": "healthy", "embedding_dim": service.dim, "model": service._embedder.model_name}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}
