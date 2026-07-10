"""
TTS API Routes — Module 3 endpoints.
All text-to-speech endpoints for the AI Interview System.
"""

import io
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger

from app.core.config import settings
from app.models.tts_schemas import (
    AudioQueueResponse,
    CacheStatusResponse,
    InterviewSpeechRequest,
    LanguageDetectRequest,
    LanguageDetectResponse,
    TTSConfigResponse,
    TTSHealthResponse,
    TTSRequest,
    TTSResponse,
    TTSUsageResponse,
    VoiceInfo,
    VoiceListResponse,
)
from app.services.language_detector import LANGUAGE_NAMES
from app.services.tts_service import get_tts

tts_router = APIRouter(prefix="/tts", tags=["Module 3: Text-to-Speech"])


# ============================================================
#  CORE TTS ENDPOINTS
# ============================================================


@tts_router.post(
    "/speak",
    response_class=StreamingResponse,
    summary="Convert text to speech audio",
    description=(
        "Convert any text to speech audio (MP3). Auto-fallback: ElevenLabs → gTTS → pyttsx3."
    ),
)
async def speak_text(request: TTSRequest):
    """
    Main TTS endpoint — returns audio stream.

    Response headers include metadata:
      X-TTS-Provider, X-TTS-Cached, X-TTS-Duration-Ms, etc.
    """
    start = time.time()
    tts = get_tts()

    provider_str = request.provider.value if request.provider else None

    audio_bytes, provider_used, was_cached = tts.generate(
        text=request.text,
        voice_id=request.voice_id,
        language=request.language,
        speech_rate=request.speech_rate,
        provider=provider_str,
        use_cache=request.use_cache,
    )

    if not audio_bytes:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "All TTS providers failed",
                "available_providers": tts.available_providers,
                "text_length": len(request.text),
            },
        )

    elapsed = time.time() - start
    content_type = "audio/wav" if provider_used == "offline" else "audio/mpeg"

    headers = {
        "Content-Disposition": "inline; filename=speech.mp3",
        "X-TTS-Provider": provider_used,
        "X-TTS-Cached": str(was_cached).lower(),
        "X-TTS-Duration-Ms": str(int(elapsed * 1000)),
        "X-TTS-Text-Length": str(len(request.text)),
        "X-TTS-Audio-Size": str(len(audio_bytes)),
    }

    logger.info(
        f"/speak: {len(request.text)} chars → "
        f"{len(audio_bytes):,} bytes via {provider_used} "
        f"({'cached' if was_cached else f'{elapsed:.2f}s'})"
    )

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type=content_type,
        headers=headers,
    )


@tts_router.get(
    "/speak",
    response_class=StreamingResponse,
    summary="Convert text to speech (GET — browser-friendly)",
)
async def speak_text_get(
    text: str = Query(..., min_length=1, max_length=5000, description="Text to speak"),
    voice_id: Optional[str] = Query(default=None),
    language: str = Query(default="en"),
    speech_rate: float = Query(default=1.0, ge=0.5, le=2.0),
    provider: Optional[str] = Query(default=None),
):
    """
    GET version of /speak for browser testing.
    Paste URL in browser address bar to hear audio directly.

    Example: /tts/speak?text=Hello+world
    """
    tts = get_tts()

    audio_bytes, provider_used, _ = tts.generate(
        text=text,
        voice_id=voice_id,
        language=language,
        speech_rate=speech_rate,
        provider=provider,
    )

    if not audio_bytes:
        raise HTTPException(500, detail="TTS generation failed")

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "X-TTS-Provider": provider_used,
        },
    )


@tts_router.post(
    "/stream",
    response_class=StreamingResponse,
    summary="Stream audio in real-time (ElevenLabs)",
)
async def stream_audio(
    text: str = Query(..., min_length=1, max_length=5000),
    voice_id: Optional[str] = Query(default=None),
):
    """
    Stream audio chunks as they are generated.
    Only ElevenLabs supports true streaming.
    Other providers fall back to full generation.
    """
    tts = get_tts()

    async def audio_generator():
        for chunk in tts.generate_stream(text, voice_id):
            yield chunk

    return StreamingResponse(
        audio_generator(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=stream.mp3",
            "Transfer-Encoding": "chunked",
        },
    )


# ============================================================
#  INTERVIEW SPEECH ENDPOINTS
# ============================================================


@tts_router.post(
    "/interview/question/{question_number}",
    response_class=StreamingResponse,
    summary="Speak a specific interview question",
)
async def speak_question(
    question_number: int,
    question_text: str = Query(..., min_length=5, max_length=2000),
    total_questions: int = Query(default=15),
    include_transition: bool = Query(default=True),
    voice_id: Optional[str] = Query(default=None),
):
    """
    Generate audio for a single interview question.

    Includes optional transition: "Moving on to question 3..."
    followed by the question text.
    """
    tts = get_tts()

    audio, full_text = tts.generate_question_audio(
        question_text=question_text,
        question_number=question_number,
        total_questions=total_questions,
        include_transition=include_transition,
        voice_id=voice_id,
    )

    if not audio:
        raise HTTPException(500, detail="Failed to generate question audio")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": (f"inline; filename=q{question_number}.mp3"),
            "X-TTS-Question-Number": str(question_number),
            "X-TTS-Full-Text": full_text[:300],
        },
    )


@tts_router.post(
    "/interview/full-sequence",
    response_model=AudioQueueResponse,
    summary="Generate entire interview audio sequence",
)
async def generate_full_interview_audio(
    request: InterviewSpeechRequest,
):
    """
    Generate audio for the complete interview.

    Returns metadata about each segment (intro, questions, outro).
    Use individual endpoints to fetch actual audio.
    """
    tts = get_tts()

    queue_items, audio_map = tts.generate_full_interview_audio(
        candidate_name=request.candidate_name,
        questions=request.questions,
        voice_id=request.voice_id,
        include_intro=request.include_intro,
        include_outro=request.include_outro,
        include_transitions=request.include_transitions,
        score=request.score,
    )

    total_duration = sum(item.duration_estimate_seconds for item in queue_items)

    return AudioQueueResponse(
        success=True,
        candidate_name=request.candidate_name,
        total_segments=len(queue_items),
        estimated_total_duration_seconds=round(total_duration, 1),
        provider=tts.active_provider,
        segments=queue_items,
    )


# ============================================================
#  VOICE MANAGEMENT
# ============================================================


@tts_router.get(
    "/voices",
    summary="List all available TTS voices",
)
async def list_voices(
    provider: Optional[str] = Query(
        default=None, description="Filter: elevenlabs | gtts | offline"
    ),
):
    """List available voices across all TTS providers."""
    tts = get_tts()
    voices = tts.list_voices(provider=provider)

    return {
        "total_voices": len(voices),
        "active_provider": tts.active_provider,
        "voices": voices,
    }


@tts_router.get(
    "/voices/presets",
    summary="List ElevenLabs preset voice names",
)
async def list_preset_voices():
    """
    Quick reference for ElevenLabs preset voices.
    Use the name (e.g., 'rachel') as voice_id in requests.
    """
    tts = get_tts()
    presets = tts.get_preset_voices()

    return {
        "total_presets": len(presets),
        "note": "Use preset name or voice_id in voice_id parameter",
        "default": settings.ELEVENLABS_VOICE_ID,
        "presets": presets,
    }


@tts_router.post(
    "/voices/preview/{voice_id}",
    response_class=StreamingResponse,
    summary="Preview a specific voice",
)
async def preview_voice(
    voice_id: str,
    text: str = Query(
        default=(
            "Hello! I'm your AI interviewer. Let me ask you about your experience with Python."
        ),
    ),
):
    """Preview any voice with sample text."""
    tts = get_tts()

    audio, provider, _ = tts.generate(text=text, voice_id=voice_id)

    if not audio:
        raise HTTPException(500, detail=f"Failed to preview voice {voice_id}")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": (f"inline; filename=preview_{voice_id}.mp3"),
            "X-TTS-Voice-ID": voice_id,
        },
    )


# ============================================================
#  LANGUAGE DETECTION
# ============================================================


@tts_router.post(
    "/detect-language",
    response_model=LanguageDetectResponse,
    summary="Detect language from text (stretch goal)",
)
async def detect_language(
    request: LanguageDetectRequest,
):
    """
    Detect language from resume or candidate text.
    Use to auto-select TTS language for multilingual support.
    """
    tts = get_tts()
    lang_code = tts.detect_language(request.text)
    lang, confidence = tts.lang_detector.detect(request.text)
    lang_name = tts.lang_detector.get_language_name(lang)

    # Check if gTTS supports this language
    supported = True
    if tts.gtts.is_available:
        supported = lang[:2] in tts.gtts.SUPPORTED_LANGUAGES

    return LanguageDetectResponse(
        detected_language=lang,
        confidence=round(confidence, 2),
        tts_language_code=lang_code,
        language_name=lang_name,
        supported_for_tts=supported,
    )


# ============================================================
#  CONFIGURATION & STATUS
# ============================================================


@tts_router.get(
    "/config",
    response_model=TTSConfigResponse,
    summary="Get current TTS configuration",
)
async def get_tts_config():
    """Get active provider, fallback chain, voice, cache status."""
    tts = get_tts()
    return tts.get_config()


@tts_router.get(
    "/usage",
    response_model=TTSUsageResponse,
    summary="Get ElevenLabs API usage",
)
async def get_tts_usage():
    """Get ElevenLabs character count / limit / remaining."""
    tts = get_tts()
    usage = tts.get_usage()

    if usage:
        return TTSUsageResponse(
            provider="elevenlabs",
            characters_used=usage["character_count"],
            characters_limit=usage["character_limit"],
            characters_remaining=usage["remaining"],
            tier=usage.get("tier", "free"),
            usage_percent=round(
                usage["character_count"] / max(usage["character_limit"], 1) * 100,
                1,
            ),
        )

    return TTSUsageResponse(
        provider="none",
        tier="ElevenLabs not available",
    )


@tts_router.get(
    "/stats",
    summary="Get TTS usage statistics",
)
async def get_tts_stats():
    """Internal usage stats: requests, cache hits, provider usage."""
    tts = get_tts()
    return tts.get_stats()


# ============================================================
#  CACHE MANAGEMENT
# ============================================================


@tts_router.get(
    "/cache/status",
    response_model=CacheStatusResponse,
    summary="Get audio cache statistics",
)
async def cache_status():
    """Cache file count and total size."""
    tts = get_tts()

    return CacheStatusResponse(
        enabled=tts.cache_enabled,
        directory=str(tts.cache_dir),
        total_files=tts.get_cache_file_count(),
        total_size_mb=tts.get_cache_size_mb(),
    )


@tts_router.delete(
    "/cache/clear",
    summary="Clear all cached audio files",
)
async def clear_cache():
    """Delete all cached audio files."""
    tts = get_tts()
    count = tts.clear_cache()
    return {"success": True, "files_deleted": count}


# ============================================================
#  HEALTH CHECK
# ============================================================


@tts_router.get(
    "/health",
    response_model=TTSHealthResponse,
    summary="TTS module health check",
)
async def tts_health():
    """Full health check of TTS module."""
    tts = get_tts()

    return TTSHealthResponse(
        status=("healthy" if tts.available_providers else "degraded"),
        active_provider=tts.active_provider,
        available_providers=tts.available_providers,
        fallback_chain=(" → ".join(tts.available_providers) or "none"),
        cache_enabled=tts.cache_enabled,
        cache_size_mb=tts.get_cache_size_mb(),
    )


@tts_router.post(
    "/interview/intro",
    response_class=StreamingResponse,
    summary="Generate AI-powered interview introduction",
)
async def generate_interview_intro(
    candidate_name: str = Query(default="Candidate"),
    num_questions: int = Query(default=15, ge=1, le=50),
    duration_minutes: int = Query(default=30, ge=5, le=120),
    voice_id: Optional[str] = Query(default=None),
    resume_json: Optional[str] = Query(
        default=None, description="URL-encoded resume JSON from Module 1 (optional)"
    ),
):
    """
    Generate AI-powered interview introduction audio.

    When resume_data is provided, the intro references the
    candidate's actual skills, experience, and background.

    Without resume_data, uses enhanced dynamic templates.

    Response headers:
      X-Script-Source: gemini / openai / groq / template
    """
    tts = get_tts()

    # Parse resume JSON if provided
    resume_data = None
    if resume_json:
        try:
            import json

            resume_data = json.loads(resume_json)
        except Exception:
            pass

    _intro_result = tts.generate_interview_intro(
        candidate_name=candidate_name,
        num_questions=num_questions,
        duration_minutes=duration_minutes,
        voice_id=voice_id,
        resume_data=resume_data,
    )
    audio, text, script_source = _intro_result

    if not audio:
        raise HTTPException(500, detail="Failed to generate intro")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=intro.mp3",
            "X-TTS-Provider": tts.active_provider or "unknown",
            "X-TTS-Script-Source": script_source,
            "X-Script-Source": script_source,
            "X-Script-Text": text[:300],
        },
    )


@tts_router.post(
    "/interview/intro/with-resume",
    response_class=StreamingResponse,
    summary="Generate AI intro from full resume data (POST body)",
)
async def generate_intro_with_resume(
    candidate_name: str = Query(default="Candidate"),
    num_questions: int = Query(default=15),
    duration_minutes: int = Query(default=30),
    voice_id: Optional[str] = Query(default=None),
    resume_data: Dict[str, Any] = Body(..., description="Full parsed resume JSON from Module 1"),
):
    """
    Generate AI intro using full resume data in POST body.

    Pass the complete output of Module 1 (/parse-resume)
    as the request body for maximum personalization.
    """
    tts = get_tts()

    # Extract name from resume if not provided
    if candidate_name == "Candidate":
        personal = resume_data.get("personal_info", {})
        if isinstance(personal, dict):
            candidate_name = personal.get("full_name", candidate_name)

    _intro_result = tts.generate_interview_intro(
        candidate_name=candidate_name,
        num_questions=num_questions,
        duration_minutes=duration_minutes,
        voice_id=voice_id,
        resume_data=resume_data,
    )
    audio, text, script_source = _intro_result

    if not audio:
        raise HTTPException(500, detail="Failed to generate intro")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=intro.mp3",
            "X-TTS-Provider": tts.active_provider or "unknown",
            "X-TTS-Script-Source": script_source,
            "X-Script-Source": script_source,
            "X-Script-Text": text[:300],
        },
    )


@tts_router.post(
    "/interview/outro",
    response_class=StreamingResponse,
    summary="Generate AI-powered interview closing speech",
)
async def generate_interview_outro(
    candidate_name: str = Query(default="Candidate"),
    num_questions: int = Query(default=15),
    score: int = Query(default=75, ge=0, le=100),
    grade: str = Query(default="Strong"),
    voice_id: Optional[str] = Query(default=None),
):
    """
    Generate AI-powered closing speech with performance awareness.

    The AI adjusts tone based on score:
      - High (>75): Congratulatory
      - Medium (50-75): Encouraging
      - Low (<50): Supportive
    """
    tts = get_tts()

    _outro_result = tts.generate_interview_outro(
        candidate_name=candidate_name,
        num_questions=num_questions,
        score=score,
        grade=grade,
        voice_id=voice_id,
    )
    audio, text, script_source = _outro_result

    if not audio:
        raise HTTPException(500, detail="Failed to generate outro")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=outro.mp3",
            "X-TTS-Provider": tts.active_provider or "unknown",
            "X-TTS-Script-Source": script_source,
            "X-Script-Source": script_source,
            "X-Script-Text": text[:300],
        },
    )


@tts_router.post(
    "/interview/outro/with-evaluation",
    response_class=StreamingResponse,
    summary="Generate AI outro with full evaluation data",
)
async def generate_outro_with_evaluation(
    candidate_name: str = Query(default="Candidate"),
    num_questions: int = Query(default=15),
    voice_id: Optional[str] = Query(default=None),
    evaluation_data: Dict[str, Any] = Body(..., description="Evaluation results from Module 5"),
):
    """
    Generate personalized outro using Module 5 evaluation results.

    Pass the full evaluation output for maximum personalization.
    The AI will mention specific strengths and areas for growth.
    """
    tts = get_tts()

    score = evaluation_data.get("overall_score", evaluation_data.get("score", 70))
    grade = evaluation_data.get("overall_grade", evaluation_data.get("grade", "Strong"))

    strengths = evaluation_data.get("strengths")
    improvements = evaluation_data.get("areas_for_improvement") or evaluation_data.get(
        "improvements"
    )

    # Support Module 5 batch payload shape:
    # { evaluations: [{ strengths: [...], improvements: [...] }, ...] }
    if not strengths or not improvements:
        evaluations = evaluation_data.get("evaluations", [])
        if isinstance(evaluations, list) and evaluations:
            if not strengths:
                merged_strengths = []
                for item in evaluations:
                    merged_strengths.extend(
                        item.get("strengths", []) if isinstance(item, dict) else []
                    )
                strengths = list(dict.fromkeys([s for s in merged_strengths if s]))[:6]
            if not improvements:
                merged_improvements = []
                for item in evaluations:
                    merged_improvements.extend(
                        item.get("improvements", []) if isinstance(item, dict) else []
                    )
                improvements = list(dict.fromkeys([s for s in merged_improvements if s]))[:6]

    category_scores = evaluation_data.get("category_scores", {})

    _outro_result = tts.generate_interview_outro(
        candidate_name=candidate_name,
        num_questions=num_questions,
        score=score,
        grade=grade,
        voice_id=voice_id,
        category_scores=category_scores,
        strengths=strengths,
        improvements=improvements,
    )
    audio, text, script_source = _outro_result

    if not audio:
        raise HTTPException(500, detail="Failed to generate outro")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=outro.mp3",
            "X-TTS-Provider": tts.active_provider or "unknown",
            "X-TTS-Script-Source": script_source,
            "X-Script-Source": script_source,
        },
    )


@tts_router.post(
    "/interview/encouragement",
    response_class=StreamingResponse,
    summary="Generate encouraging prompt audio",
)
async def generate_encouragement(
    context: str = Query(
        default="thinking",
        description="Context: thinking / repeat / struggling / good_answer / halfway",
    ),
    candidate_name: Optional[str] = Query(default=None),
    voice_id: Optional[str] = Query(default=None),
):
    """
    Generate context-aware encouragement audio.

    Use during the interview for natural interaction:
    - thinking: When candidate is taking time
    - repeat: Before repeating a question
    - struggling: When candidate seems stuck
    - good_answer: After a great response
    - halfway: At the midpoint of the interview
    """
    tts = get_tts()

    audio, text = tts.generate_encouragement_audio(
        candidate_name=candidate_name,
        context=context,
        voice_id=voice_id,
    )

    if not audio:
        raise HTTPException(500, detail="Failed to generate audio")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=encouragement.mp3",
            "X-TTS-Spoken-Text": text,
        },
    )


@tts_router.post(
    "/interview/followup-intro",
    response_class=StreamingResponse,
    summary="Generate follow-up question introduction",
)
async def generate_followup_intro(
    original_question: str = Query(..., min_length=5),
    answer_summary: Optional[str] = Query(default=None),
    voice_id: Optional[str] = Query(default=None),
):
    """
    Generate a natural lead-in before a follow-up question.

    "Based on what you described about your API design,
     I'd like to dig deeper..."
    """
    tts = get_tts()

    audio, text = tts.generate_followup_intro_audio(
        original_question=original_question,
        candidate_answer_summary=answer_summary,
        voice_id=voice_id,
    )

    if not audio:
        raise HTTPException(500, detail="Failed to generate audio")

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=followup_intro.mp3",
            "X-TTS-Spoken-Text": text,
        },
    )


@tts_router.get(
    "/interview/script-status",
    summary="Check AI script generator status",
)
async def script_generator_status():
    """Check which LLM is powering the script generation."""
    tts = get_tts()
    gen = tts.script_generator

    return {
        "ai_available": gen.is_llm_available,
        "active_llm": gen._active_llm or "none (using templates)",
        "llm_priority": "Gemini → OpenAI → Groq → Templates",
        "gemini_available": gen._gemini_client is not None,
        "openai_available": gen._openai_client is not None,
        "groq_available": gen._groq_client is not None,
    }
