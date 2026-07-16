"""
Main ASR Orchestrator — Browser-First Architecture.
FIXED VERSION with proper session management and response handling.

Strategy:
1. Browser Web Speech API is PRIMARY (fast, free, reliable)
2. Backend providers are FALLBACKS (will fail without API keys)
3. Filler detection always runs on backend
4. User doesn't know browser ASR is being used
"""

import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import uuid
from loguru import logger

from app.core.config import settings
from app.services.filler_word_detector import get_filler_detector
from app.services.asr_session_manager import get_asr_session_manager
from app.services.audio_preprocessor import get_preprocessor
from app.schemas.asr_schemas import (
    TranscriptionResult,
    TranscriptionSegment,
    RecordingSession,
    ASRConfigResponse,
    ASRHealthResponse,
    FillerAnalysis,
)


class ASRService:
    """
    Main ASR service with browser-first architecture.
    
    Priority:
    1. Browser Web Speech API (primary, silent) — always works
    2. Groq Whisper (free cloud) — needs API key
    3. OpenAI Whisper (paid cloud) — needs API key
    4. Google Speech (free) — needs internet
    5. Local Whisper (offline) — needs model
    6. Vosk (offline) — needs model
    """

    PROVIDER_PRIORITY = [
        "browser",         # Primary (silent)
        "groq-whisper",
        "openai-whisper",
        "deepgram",
        "google",
        "whisper-local",
        "vosk",
    ]

    def __init__(self):
        logger.info("=" * 55)
        logger.info("  Initializing ASR Service (Module 4)")
        logger.info("=" * 55)

        # Core components (always available)
        self.filler_detector = get_filler_detector()
        self.session_manager = get_asr_session_manager()
        self.preprocessor = get_preprocessor()

        # Recordings directory
        self._recordings_dir = Path(settings.ASR_RECORDINGS_DIR)
        self._recordings_dir.mkdir(parents=True, exist_ok=True)

        # Initialize backend providers (will fail gracefully)
        self._init_backend_providers()

        # Build provider list
        self._build_provider_list()

        # Stats
        self._total_transcriptions: int = 0
        self._browser_transcriptions: int = 0
        self._backend_transcriptions: int = 0
        self._provider_usage: Dict[str, int] = {}

        # Log status
        self._log_status()
        logger.info("=" * 55)

    def _init_backend_providers(self):
        """Initialize backend ASR providers (will fail without API keys)."""
        
        # Groq Whisper
        self.groq_whisper = None
        try:
            from app.services.asr_groq_whisper import GroqWhisperASR
            self.groq_whisper = GroqWhisperASR()
        except Exception as e:
            logger.debug(f"Groq Whisper not available: {e}")

        # OpenAI Whisper
        self.openai_whisper = None
        try:
            from app.services.asr_openai_whisper import OpenAIWhisperASR
            self.openai_whisper = OpenAIWhisperASR()
        except Exception as e:
            logger.debug(f"OpenAI Whisper not available: {e}")

        # Deepgram
        self.deepgram = None
        try:
            from app.services.asr_deepgram import DeepgramStreamingASR
            self.deepgram = DeepgramStreamingASR()
        except Exception as e:
            logger.debug(f"Deepgram not available: {e}")

        # Google Speech
        self.google = None
        try:
            from app.services.asr_google import GoogleSpeechASR
            self.google = GoogleSpeechASR()
        except Exception as e:
            logger.debug(f"Google Speech not available: {e}")

        # Local Whisper
        self.whisper_local = None
        try:
            from app.services.asr_whisper import WhisperASR
            self.whisper_local = WhisperASR()
        except Exception as e:
            logger.debug(f"Local Whisper not available: {e}")

        # Vosk
        self.vosk = None
        try:
            from app.services.asr_vosk import VoskASR
            self.vosk = VoskASR()
        except Exception as e:
            logger.debug(f"Vosk not available: {e}")

    def _build_provider_list(self):
        """Build list of available providers."""
        self.available_providers: List[str] = ["browser"]  # Always available
        self.cloud_providers: List[str] = []
        self.local_providers: List[str] = []

        # Groq Whisper
        if self.groq_whisper and getattr(self.groq_whisper, 'is_available', False):
            if hasattr(getattr(self.groq_whisper, "_client", None), "audio"):
                self.available_providers.append("groq-whisper")
                self.cloud_providers.append("groq-whisper")

        if self.openai_whisper and getattr(self.openai_whisper, 'is_available', False):
            self.available_providers.append("openai-whisper")
            self.cloud_providers.append("openai-whisper")

        if self.deepgram and getattr(self.deepgram, 'is_available', False):
            self.available_providers.append("deepgram")
            self.cloud_providers.append("deepgram")

        if self.google and getattr(self.google, 'is_available', False):
            self.available_providers.append("google")
            self.cloud_providers.append("google")

        if self.whisper_local and getattr(self.whisper_local, 'is_available', False):
            self.available_providers.append("whisper-local")
            self.local_providers.append("whisper-local")

        if self.vosk and getattr(self.vosk, 'is_available', False):
            self.available_providers.append("vosk")
            self.local_providers.append("vosk")

        # Active provider is always browser (but we don't tell user)
        self.active_provider = "browser"

    def _log_status(self):
        """Log initialization status."""
        logger.info("  ✓ Browser Web Speech API (primary)")
        
        if self.cloud_providers:
            logger.info(f"  ✓ Cloud fallbacks: {', '.join(self.cloud_providers)}")
        else:
            logger.info("  · No cloud providers configured")
            
        if self.local_providers:
            logger.info(f"  ✓ Local fallbacks: {', '.join(self.local_providers)}")
        else:
            logger.info("  · No local providers available")

    # ─── AUDIO STORAGE ─────────────────────────────────────────

    def save_audio(
        self,
        audio_data: bytes,
        filename: Optional[str] = None,
        session_id: Optional[str] = None,
        question_id: Optional[str] = None,
    ) -> Path:
        """
        Save audio to recordings directory.
        
        Args:
            audio_data: Raw audio bytes
            filename: Optional custom filename
            session_id: Optional session ID for naming
            question_id: Optional question ID for naming
            
        Returns:
            Path to saved audio file
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:8]
        
        if filename:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
            safe_ext = ext if ext.isalnum() else "wav"
        else:
            safe_ext = "wav"

        if session_id and question_id:
            out_name = f"{session_id}_{question_id}_{timestamp}_{uid}.{safe_ext}"
        else:
            out_name = f"audio_{timestamp}_{uid}.{safe_ext}"

        out_path = self._recordings_dir / out_name
        out_path.write_bytes(audio_data)
        
        logger.info(f"Audio saved: {out_path} ({len(audio_data):,} bytes)")
        return out_path

    # ─── BROWSER TRANSCRIPT (PRIMARY PATH) ─────────────────────

    def process_browser_transcript(
        self,
        session_id: str,
        question_id: str,
        question_number: int,
        question_text: str,
        question_category: str,
        transcript: str,
        duration_seconds: float = 0.0,
        word_count: int = 0,
    ) -> TranscriptionResult:
        """
        Process transcript from browser Web Speech API.
        This is the PRIMARY transcription path.
        """
        start_time = time.time()
        self._total_transcriptions += 1
        self._browser_transcriptions += 1
        self._provider_usage["browser"] = self._provider_usage.get("browser", 0) + 1

        # Get or create session
        session = self.session_manager.get_or_create_session(
            session_id=session_id,
            question_id=question_id,
            question_number=question_number,
            question_text=question_text,
            question_category=question_category,
        )

        # Analyze filler words
        filler_analysis = None
        if settings.FILLER_DETECTION_ENABLED and transcript.strip():
            filler_analysis = self.filler_detector.analyze(transcript, duration_seconds)

        # Calculate word count if not provided
        if word_count == 0:
            word_count = len(transcript.split())

        # Create result
        elapsed = (time.time() - start_time) * 1000
        
        result = TranscriptionResult(
            success=True,
            text=transcript,
            transcript=transcript,
            language="en",
            confidence=0.85,
            duration_seconds=duration_seconds,
            word_count=word_count,
            provider_used="browser",
            processing_time_ms=elapsed,
            filler_analysis=filler_analysis,
        )

        # Update session
        self.session_manager.set_browser_transcript(
            session_id=session_id,
            question_id=question_id,
            transcript=transcript,
            duration_seconds=duration_seconds,
            word_count=word_count,
            filler_analysis=filler_analysis,
        )

        logger.info(
            f"Browser transcript: {session_id}/{question_id} — "
            f"{word_count} words, {elapsed:.0f}ms"
        )

        return result

    # ─── BACKEND TRANSCRIPTION (FALLBACK) ──────────────────────

    def transcribe(
        self,
        audio_data: bytes,
        input_format: str = "webm",
        language: str = "en",
        provider: Optional[str] = None,
        preprocess: bool = True,
        detect_fillers: bool = True,
        allow_backend_fallback: bool = True,
        session_id: Optional[str] = None,
        question_id: Optional[str] = None,
        save_audio: bool = True,
    ) -> TranscriptionResult:
        """
        Transcribe audio using backend providers.
        This is the FALLBACK path when browser ASR isn't used.
        
        Args:
            audio_data: Raw audio bytes
            input_format: Input audio format
            language: Language code
            provider: Preferred provider
            preprocess: Apply audio preprocessing
            detect_fillers: Run filler word analysis
            allow_backend_fallback: Allow trying multiple providers
            session_id: Optional session ID
            question_id: Optional question ID
            save_audio: Save audio to recordings folder
            
        Returns:
            TranscriptionResult with transcription and metadata
        """
        start_time = time.time()
        self._total_transcriptions += 1
        
        audio_path = None

        # Save audio to recordings folder
        if save_audio and audio_data:
            try:
                audio_path = self.save_audio(
                    audio_data,
                    filename=f"audio.{input_format}",
                    session_id=session_id,
                    question_id=question_id,
                )
            except Exception as e:
                logger.warning(f"Failed to save audio: {e}")

        # Preprocess audio if enabled
        processed_audio = audio_data
        if preprocess and self.preprocessor and self.preprocessor.is_available:
            try:
                if input_format.lower() in {"webm", "ogg", "opus", "m4a", "mp4"}:
                    processed_audio = self.preprocessor.convert_to_wav_16k(
                        audio_data, input_format
                    )
                    input_format = "wav"
            except Exception as e:
                logger.warning(f"Audio preprocessing failed: {e}")

        # Get provider order
        providers = self._get_provider_order(provider)

        if not providers:
            elapsed = (time.time() - start_time) * 1000
            return TranscriptionResult(
                success=False,
                text="",
                transcript="",
                provider_used="none",
                processing_time_ms=elapsed,
                error="No ASR provider available",
                audio_path=str(audio_path) if audio_path else None,
            )

        result = None
        provider_used = "none"
        last_error = None
        attempted_providers: List[str] = []

        # Try each provider
        for prov in providers:
            attempted_providers.append(prov)
            try:
                logger.debug(f"Trying backend ASR: {prov}")
                raw = self._dispatch(prov, processed_audio, language, input_format)

                if raw and "error" not in raw and raw.get("text", "").strip():
                    result = raw
                    provider_used = prov
                    self._backend_transcriptions += 1
                    self._provider_usage[prov] = self._provider_usage.get(prov, 0) + 1
                    break

                if raw and "error" in raw:
                    last_error = raw["error"]
                    logger.warning(f"Backend ASR [{prov}] error: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Backend ASR [{prov}] failed: {e}")

        # No successful transcription
        if not result:
            elapsed = (time.time() - start_time) * 1000
            return TranscriptionResult(
                success=False,
                text="",
                transcript="",
                provider_used=provider_used,
                attempted_providers=attempted_providers,
                processing_time_ms=elapsed,
                error=last_error or "All backend providers failed",
                audio_path=str(audio_path) if audio_path else None,
            )

        # Build response
        text = result.get("text", "")
        elapsed = (time.time() - start_time) * 1000

        # Filler analysis
        filler_analysis = None
        if detect_fillers and settings.FILLER_DETECTION_ENABLED and text.strip():
            duration = result.get("duration_seconds", 0.0)
            filler_analysis = self.filler_detector.analyze(text, duration)

        logger.info(
            f"Backend ASR [{provider_used}]: "
            f"{len(text.split())} words, {elapsed:.0f}ms"
        )

        transcription_result = TranscriptionResult(
            success=True,
            text=text,
            transcript=text,
            segments=[
                TranscriptionSegment(
                    text=s.get("text", ""),
                    start_time=s.get("start", 0.0),
                    end_time=s.get("end", 0.0),
                    confidence=s.get("confidence", 0.0),
                )
                for s in result.get("segments", [])
            ],
            language=language,
            language_detected=result.get("language"),
            confidence=result.get("confidence", 0.0),
            duration_seconds=result.get("duration_seconds", 0.0),
            word_count=len(text.split()),
            provider_used=provider_used,
            attempted_providers=attempted_providers,
            processing_time_ms=elapsed,
            filler_analysis=filler_analysis,
            audio_path=str(audio_path) if audio_path else None,
        )

        # Update session if provided
        if session_id and question_id:
            try:
                self.session_manager.set_transcription(
                    session_id=session_id,
                    question_id=question_id,
                    transcription=transcription_result,
                )
            except Exception as e:
                logger.warning(f"Failed to update session: {e}")

        return transcription_result

    def _ensure_whisper_local_provider(self) -> None:
        """Lazy-load local Whisper if selected after startup."""
        if self.whisper_local and self.whisper_local.is_available:
            return
        try:
            from app.services.asr_whisper import WhisperASR
            self.whisper_local = WhisperASR()
            if self.whisper_local.is_available:
                if "whisper-local" not in self.available_providers:
                    self.available_providers.append("whisper-local")
                if "whisper-local" not in self.local_providers:
                    self.local_providers.append("whisper-local")
        except Exception as e:
            logger.debug(f"Lazy Whisper init failed: {e}")

    def _get_backend_provider_order(self, preferred: Optional[str] = None) -> List[str]:
        """Get backend provider order (excludes browser)."""
        backend = [p for p in self.available_providers if p != "browser"]

        if not backend:
            return []

        # Apply configured priority
        configured_priority = [
            p for p in settings.ASR_PROVIDER_PRIORITY
            if p in backend
        ]
        ordered = configured_priority + [p for p in backend if p not in configured_priority]

        # Handle forced provider
        forced = preferred or settings.ASR_PROVIDER
        if forced and forced in ordered:
            return [forced] + [p for p in ordered if p != forced]
        return ordered

    def _get_provider_order(self, preferred: Optional[str] = None) -> List[str]:
        """Backward-compatible alias for provider order selection."""
        return self._get_backend_provider_order(preferred)

    def _dispatch_backend(
        self,
        provider: str,
        audio_data: bytes,
        language: str,
        input_format: str,
    ) -> Optional[Dict[str, Any]]:
        """Dispatch to backend provider."""
        
        if provider == "groq-whisper" and self.groq_whisper:
            return self.groq_whisper.transcribe(
                audio_data, input_format=input_format, language=language
            )

        if provider == "openai-whisper" and self.openai_whisper:
            return self.openai_whisper.transcribe(
                audio_data, input_format=input_format, language=language
            )

        if provider == "deepgram" and self.deepgram:
            return self.deepgram.transcribe_file(
                audio_data, input_format=input_format, language=language
            )

        if provider == "google" and self.google:
            return self.google.transcribe(audio_data, language=language)

        if provider == "whisper-local":
            self._ensure_whisper_local_provider()
            if self.whisper_local and self.whisper_local.is_available:
                return self.whisper_local.transcribe(
                    audio_data, input_format=input_format, language=language
                )
            return {"error": "Local Whisper model not loaded"}

        if provider == "vosk" and self.vosk:
            return self.vosk.transcribe(audio_data, language=language)

        return {"error": f"Provider {provider} not available"}

    def _dispatch(
        self,
        provider: str,
        audio_data: bytes,
        language: str,
        input_format: str,
    ) -> Optional[Dict[str, Any]]:
        """Dispatcher with Google compatibility mapping."""
        if provider == "google" and self.google:
            mapped_language = {"hi": "hi-IN", "en": "en-US"}.get(language, language)
            data = audio_data
            if (input_format or "").lower() != "wav":
                if self.preprocessor and self.preprocessor.is_available:
                    try:
                        data = self.preprocessor.convert_to_wav_16k(audio_data, input_format)
                    except Exception:
                        pass
            return self.google.transcribe(data, language=mapped_language)

        return self._dispatch_backend(provider, audio_data, language, input_format)

    async def transcribe_stream(self, audio_queue, on_transcript, on_error):
        """Graceful compatibility endpoint for stream transcription."""
        if not getattr(self, "streaming_available", False):
            if on_error:
                await on_error("Streaming not available")
            return

    # ─── SESSION MANAGEMENT ──────────────────────────────────

    def start_recording_session(
        self,
        session_id: str,
        question_id: str,
        question_number: int,
        question_text: str,
        question_category: str = "T",
    ) -> RecordingSession:
        """Start a recording session."""
        session = self.session_manager.create_session(
            session_id=session_id,
            question_id=question_id,
            question_number=question_number,
            question_text=question_text,
            question_category=question_category,
        )
        return self.session_manager.start_recording(session_id, question_id) or session

    def process_recording(
        self,
        session_id: str,
        question_id: str,
        audio_data: bytes,
        input_format: str = "webm",
        language: str = "en",
    ) -> TranscriptionResult:
        """Process uploaded recording for an existing session."""
        session = self.session_manager.get_session(session_id, question_id)
        if not session:
            raise ValueError("Session not found")

        self.session_manager.stop_recording(
            session_id=session_id,
            question_id=question_id,
            audio_data=audio_data,
        )

        result = self.transcribe(
            audio_data=audio_data,
            input_format=input_format,
            language=language,
            session_id=session_id,
            question_id=question_id,
        )
        
        self.session_manager.set_transcription(session_id, question_id, result)
        return result

    def correct_transcription(
        self,
        session_id: str,
        question_id: str,
        corrected_text: str
    ) -> Optional[RecordingSession]:
        """Apply correction."""
        return self.session_manager.correct_transcription(
            session_id, question_id, corrected_text
        )

    def re_record(
        self,
        session_id: str,
        question_id: str
    ) -> Optional[RecordingSession]:
        """Reset for re-recording."""
        return self.session_manager.re_record(session_id, question_id)

    def submit_answer(
        self,
        session_id: str,
        question_id: str,
        final_text: Optional[str] = None,
    ) -> Optional[RecordingSession]:
        """Submit final answer."""
        if final_text:
            self.session_manager.correct_transcription(
                session_id, question_id, final_text
            )
        return self.session_manager.submit(session_id, question_id)

    def get_session_status(
        self,
        session_id: str,
        question_id: str
    ) -> Optional[RecordingSession]:
        """Get session status."""
        return self.session_manager.get_session(session_id, question_id)

    def get_all_answers(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all submitted answers."""
        submitted = self.session_manager.get_all_submitted(session_id)
        
        return [
            {
                "question_id": s.question_id,
                "question_number": s.question_number,
                "question_text": s.question_text,
                "question_category": s.question_category,
                "answer_text": s.final_text or "",
                "was_corrected": s.corrected_text is not None,
                "duration_seconds": s.duration_seconds,
                "confidence": s.transcription.confidence if s.transcription else 0.0,
                "filler_analysis": (
                    s.transcription.filler_analysis.model_dump()
                    if s.transcription and s.transcription.filler_analysis
                    else None
                ),
                "recording_number": s.recording_number,
                "provider": s.transcription.provider_used if s.transcription else "browser",
            }
            for s in submitted
        ]

    # ─── STATUS & CONFIG ─────────────────────────────────────

    def get_config(self) -> ASRConfigResponse:
        """Get ASR configuration."""
        return ASRConfigResponse(
            active_provider=self.active_provider,
            available_providers=self.available_providers,
            fallback_order=self.PROVIDER_PRIORITY,
            browser_asr_enabled=True,
            whisper_model_size=settings.WHISPER_MODEL_SIZE,
            sample_rate=settings.ASR_SAMPLE_RATE,
            silence_threshold_db=settings.SILENCE_THRESHOLD_DB,
            silence_duration_seconds=settings.SILENCE_DURATION_SECONDS,
            noise_reduction=settings.NOISE_REDUCTION_ENABLED,
            filler_detection=settings.FILLER_DETECTION_ENABLED,
            max_recording_seconds=settings.ASR_MAX_RECORDING_SECONDS,
            auto_submit=settings.ASR_AUTO_SUBMIT,
            allow_re_record=settings.ASR_ALLOW_RE_RECORD,
            max_re_records=settings.ASR_MAX_RE_RECORDS,
        )

    def get_health(self) -> ASRHealthResponse:
        """Get health status."""
        recordings_count = 0
        if self._recordings_dir.exists():
            recordings_count = len(list(self._recordings_dir.glob("*")))
        
        return ASRHealthResponse(
            status="healthy",
            active_provider=self.active_provider,
            available_providers=self.available_providers,
            fallback_chain=" → ".join(self.available_providers),
            browser_asr_available=True,
            cloud_providers=self.cloud_providers,
            local_providers=self.local_providers,
            recordings_dir=str(self._recordings_dir),
            total_recordings=recordings_count,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_transcriptions": self._total_transcriptions,
            "browser_transcriptions": self._browser_transcriptions,
            "backend_transcriptions": self._backend_transcriptions,
            "provider_usage": self._provider_usage,
            "active_sessions": self.session_manager.active_sessions_count,
            "session_stats": self.session_manager.get_stats(),
        }


# Singleton
_asr_instance: Optional[ASRService] = None


def get_asr() -> ASRService:
    """Get singleton ASRService instance."""
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = ASRService()
    return _asr_instance
