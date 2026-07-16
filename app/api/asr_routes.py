"""
ASR API routes — Module 4.
FIXED VERSION with proper response handling and Streamlit compatibility.

Supports real-time transcription (primary) + backend fallback.
"""

from typing import Optional
from pathlib import Path
from datetime import datetime
import uuid

from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from loguru import logger

from app.services.asr_service import get_asr
from app.schemas.asr_schemas import (
    BrowserTranscriptRequest,
    StartRecordingRequest,
    SubmitTranscriptionRequest,
    CorrectionRequest,
    ReRecordRequest,
    TranscriptionResult,
    RecordingSessionResponse,
    ASRConfigResponse,
    ASRHealthResponse,
    SimpleTranscriptResponse,
)
from app.core.config import settings


asr_router = APIRouter(
    prefix="/asr",
    tags=["Module 4: Speech Recognition"],
)


# ─── BROWSER TRANSCRIPT (PRIMARY) ─────────────────────────────


@asr_router.post(
    "/transcript",
    response_model=TranscriptionResult,
    summary="Process real-time transcript",
)
@asr_router.post(
    "/browser-transcript",
    response_model=TranscriptionResult,
    include_in_schema=False,
)
async def process_browser_transcript(request: BrowserTranscriptRequest):
    """
    Process transcript from real-time speech capture.
    This is the PRIMARY transcription path.
    
    The client handles speech recognition; we just:
    1. Analyze filler words
    2. Store in session
    3. Return processed result
    """
    asr = get_asr()

    if not request.transcript or len(request.transcript.strip()) < 2:
        raise HTTPException(400, detail="Transcript is empty or too short")

    result = asr.process_browser_transcript(
        session_id=request.session_id,
        question_id=request.question_id,
        question_number=request.question_number,
        question_text=request.question_text,
        question_category=request.question_category,
        transcript=request.transcript,
        duration_seconds=request.duration_seconds,
        word_count=request.word_count,
    )

    return result


# ─── BACKEND TRANSCRIBE (FALLBACK) ────────────────────────────


@asr_router.post(
    "/transcribe",
    response_model=TranscriptionResult,
    summary="Transcribe audio file (backend fallback)",
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file"),
    language: str = Query(default="en"),
    provider: Optional[str] = Query(default=None),
    enable_filler_detection: bool = Query(default=True),
    enable_noise_reduction: bool = Query(default=True),
    session_id: Optional[str] = Query(default=None),
    question_id: Optional[str] = Query(default=None),
):
    """
    Transcribe audio using backend providers.
    This is the FALLBACK when real-time capture isn't available.
    """
    asr = get_asr()

    audio_data = await file.read()
    if not audio_data or len(audio_data) < 100:
        raise HTTPException(400, detail="Audio file is empty or too small")

    filename = file.filename or "audio.webm"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
    
    logger.info(f"/transcribe: {filename} ({len(audio_data):,} bytes)")

    result = asr.transcribe(
        audio_data=audio_data,
        input_format=ext,
        language=language,
        provider=provider,
        preprocess=enable_noise_reduction,
        detect_fillers=enable_filler_detection,
        allow_backend_fallback=True,
        session_id=session_id,
        question_id=question_id,
        save_audio=True,
    )

    if not result.success:
        logger.warning(f"Backend transcription failed: {result.error}")
    else:
        logger.info(
            f"Backend transcription success: provider={result.provider_used}, "
            f"chars={len((result.text or '').strip())}, words={result.word_count}"
        )

    return result


@asr_router.post(
    "/transcribe-simple",
    response_model=SimpleTranscriptResponse,
    summary="Simple transcription endpoint (Streamlit compatible)",
)
async def transcribe_simple(
    file: UploadFile = File(..., description="Audio file"),
    language: str = Query(default="en"),
):
    """
    Simple transcription endpoint that returns a flat response.
    Designed for Streamlit compatibility.
    """
    asr = get_asr()

    audio_data = await file.read()
    if not audio_data or len(audio_data) < 100:
        raise HTTPException(400, detail="Audio file is empty or too small")

    filename = file.filename or "audio.wav"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
    
    logger.info(f"/transcribe-simple: {filename} ({len(audio_data):,} bytes)")

    result = asr.transcribe(
        audio_data=audio_data,
        input_format=ext,
        language=language,
        provider=None,
        preprocess=True,
        detect_fillers=True,
        allow_backend_fallback=True,
        save_audio=True,
    )

    # Return simple flat response
    return SimpleTranscriptResponse(
        success=result.success,
        transcript=result.text or "",
        text=result.text or "",
        word_count=result.word_count,
        confidence=result.confidence,
        duration_seconds=result.duration_seconds,
        provider=result.provider_used,
        attempted_providers=result.attempted_providers,
        error=result.error,
        audio_path=result.audio_path,
        filler_analysis=result.filler_analysis.model_dump() if result.filler_analysis else None,
    )


@asr_router.post(
    "/session/upload",
    response_model=RecordingSessionResponse,
    summary="Upload recorded audio for a session",
)
async def upload_session_audio(
    session_id: str = Query(...),
    question_id: str = Query(...),
    format: str = Query(default="webm"),
    language: str = Query(default="en"),
    file: UploadFile = File(..., description="Audio file"),
):
    """Upload audio for an existing session."""
    asr = get_asr()
    session = asr.get_session_status(session_id, question_id)
    if not session:
        raise HTTPException(404, detail="Session not found")

    audio_data = await file.read()
    if not audio_data or len(audio_data) < 100:
        raise HTTPException(400, detail="Audio file is empty or too small")

    result = asr.process_recording(
        session_id=session_id,
        question_id=question_id,
        audio_data=audio_data,
        input_format=format,
        language=language,
    )
    updated = asr.get_session_status(session_id, question_id)

    return RecordingSessionResponse(
        success=result.success,
        message="Audio processed" if result.success else (result.error or "Processing failed"),
        session=updated,
        can_re_record=True,
        can_correct=bool(updated and updated.final_text),
        can_submit=bool(updated and updated.final_text),
    )


# ─── SESSION MANAGEMENT ───────────────────────────────────────


@asr_router.post(
    "/session/start",
    response_model=RecordingSessionResponse,
    summary="Start recording session",
)
async def start_session(request: StartRecordingRequest):
    """Start a recording session for a question."""
    asr = get_asr()
    
    session = asr.start_recording_session(
        session_id=request.session_id,
        question_id=request.question_id,
        question_number=request.question_number,
        question_text=request.question_text,
        question_category=request.question_category,
    )
    
    return RecordingSessionResponse(
        success=True,
        message=f"Session started for Q{request.question_number}",
        session=session,
        can_re_record=True,
        can_correct=False,
        can_submit=False,
    )


@asr_router.post(
    "/session/correct",
    response_model=RecordingSessionResponse,
    summary="Correct transcription",
)
async def correct_transcription(request: CorrectionRequest):
    """Apply correction to transcription."""
    asr = get_asr()
    
    session = asr.correct_transcription(
        request.session_id,
        request.question_id,
        request.corrected_text,
    )
    
    if not session:
        raise HTTPException(404, detail="Session not found")
        
    return RecordingSessionResponse(
        success=True,
        message="Correction applied",
        session=session,
        can_re_record=True,
        can_correct=True,
        can_submit=True,
    )


@asr_router.post(
    "/session/re-record",
    response_model=RecordingSessionResponse,
    summary="Re-record answer",
)
async def re_record(request: ReRecordRequest):
    """Reset session for re-recording."""
    asr = get_asr()
    
    session = asr.re_record(request.session_id, request.question_id)
    
    if not session:
        raise HTTPException(
            400,
            detail=f"Cannot re-record. Max attempts ({settings.ASR_MAX_RE_RECORDS}) reached."
        )
        
    return RecordingSessionResponse(
        success=True,
        message=f"Re-record attempt #{session.recording_number}",
        session=session,
        can_re_record=session.recording_number < settings.ASR_MAX_RE_RECORDS,
        can_correct=False,
        can_submit=False,
    )


@asr_router.post(
    "/session/submit",
    response_model=RecordingSessionResponse,
    summary="Submit final answer",
)
async def submit_answer(request: SubmitTranscriptionRequest):
    """Submit final answer for evaluation."""
    asr = get_asr()

    session = asr.submit_answer(
        session_id=request.session_id,
        question_id=request.question_id,
        final_text=request.final_text,
    )
    
    if not session:
        raise HTTPException(400, detail="Cannot submit — no transcript available")
        
    return RecordingSessionResponse(
        success=True,
        message=f"Submitted ({len(session.final_text or '')} chars)",
        session=session,
        can_re_record=False,
        can_correct=False,
        can_submit=False,
    )


@asr_router.get(
    "/session/{session_id}/{question_id}/status",
    summary="Get session status",
)
async def get_session_status(session_id: str, question_id: str):
    """Get recording session status."""
    asr = get_asr()
    session = asr.get_session_status(session_id, question_id)
    
    if not session:
        raise HTTPException(404, detail="Session not found")
        
    return session.model_dump()


@asr_router.get(
    "/session/{session_id}/all-answers",
    summary="Get all submitted answers",
)
async def get_all_answers(session_id: str):
    """Get all submitted answers for evaluation."""
    asr = get_asr()
    answers = asr.get_all_answers(session_id)
    
    return {
        "session_id": session_id,
        "total_submitted": len(answers),
        "answers": answers,
    }


# ─── FILLER ANALYSIS ──────────────────────────────────────────


@asr_router.post("/analyze-fillers", summary="Analyze text for filler words")
async def analyze_fillers(text: str = Query(..., min_length=3, max_length=10000)):
    """Analyze text for filler words."""
    asr = get_asr()
    return asr.filler_detector.analyze(text).model_dump()


# ─── STATUS ───────────────────────────────────────────────────


@asr_router.get("/config", response_model=ASRConfigResponse, summary="Get ASR config")
async def get_config():
    """Get ASR configuration."""
    return get_asr().get_config()


@asr_router.get("/stats", summary="Get ASR statistics")
async def get_stats():
    """Get usage statistics."""
    return get_asr().get_stats()


@asr_router.get("/providers", summary="List configured ASR providers")
async def list_providers():
    """List all configured ASR providers."""
    cfg = get_asr().get_config()
    if isinstance(cfg, dict):
        active_provider = cfg.get("active_provider")
        available = cfg.get("available_providers", [])
    else:
        active_provider = cfg.active_provider
        available = cfg.available_providers
    return {
        "active_provider": active_provider,
        "providers": [
            {"name": name, "available": True}
            for name in available
        ],
    }


@asr_router.get("/health", response_model=ASRHealthResponse, summary="Health check")
async def health_check():
    """Check ASR health status."""
    return get_asr().get_health()


@asr_router.get("/recordings", summary="List saved recordings")
async def list_recordings(limit: int = Query(default=50, le=200)):
    """List saved audio recordings."""
    recordings_dir = Path(settings.ASR_RECORDINGS_DIR)
    
    if not recordings_dir.exists():
        return {"recordings": [], "total": 0}
    
    files = sorted(recordings_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    recordings = []
    for f in files[:limit]:
        stat = f.stat()
        recordings.append({
            "filename": f.name,
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    
    return {
        "recordings": recordings,
        "total": len(files),
        "showing": len(recordings),
    }
