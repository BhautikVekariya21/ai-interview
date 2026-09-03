"""
OpenAI Whisper API — Cloud ASR (production-grade, handles all formats).
"""

import time
import tempfile
import os
from typing import Dict, Any, Optional
from loguru import logger

from app.core.config import settings


class OpenAIWhisperASR:
    """
    OpenAI Whisper Cloud API:
    - Automatic format detection (WebM, MP3, WAV, M4A, OGG)
    - Word-level timestamps
    - 99%+ accuracy
    - $0.006/minute
    """

    def __init__(self):
        self._client = None
        self._available = False
        self._initialize()

    def _initialize(self):
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.debug("  · OpenAI Whisper API — OPENAI_API_KEY not set")
            return

        try:
            from openai import OpenAI
            
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self._available = True
            logger.info("  ✓ OpenAI Whisper API initialized")
            
        except ImportError:
            logger.warning("  ✗ 'openai' package not installed — pip install openai")
        except Exception as e:
            logger.warning(f"  ✗ OpenAI Whisper init failed: {e}")

    @property
    def is_available(self) -> bool:
        """Check if provider is ready."""
        return self._available and self._client is not None

    def transcribe(
        self,
        audio_data: bytes,
        input_format: str = "webm",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "verbose_json",
    ) -> Dict[str, Any]:
        """
        Transcribe audio via OpenAI Whisper API.

        Args:
            audio_data: Raw audio bytes
            input_format: File format (webm, wav, mp3, m4a, ogg)
            language: ISO 639-1 code (en, es, fr) — auto-detect if None
            prompt: Optional context to guide transcription
            temperature: 0.0 = deterministic, 1.0 = creative
            response_format: verbose_json (timestamps) | json | text | srt | vtt

        Returns:
            Dict with text, segments, word_timestamps, language, confidence
        """
        if not self.is_available:
            return {"error": "OpenAI Whisper API not configured"}

        start_time = time.time()
        tmp_path = None

        try:
            # Normalize format
            fmt = (input_format or "webm").lower().strip()
            valid_formats = {"webm", "wav", "mp3", "m4a", "ogg", "flac", "mp4"}
            if fmt not in valid_formats:
                fmt = "webm"

            # Save to temp file (OpenAI requires file upload)
            with tempfile.NamedTemporaryFile(
                suffix=f".{fmt}",
                delete=False,
                mode="wb"
            ) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            # Prepare API call
            with open(tmp_path, "rb") as audio_file:
                api_kwargs = {
                    "file": audio_file,
                    "model": settings.OPENAI_WHISPER_MODEL,
                    "response_format": response_format,
                    "temperature": temperature,
                }
                
                if language:
                    api_kwargs["language"] = language
                if prompt:
                    api_kwargs["prompt"] = prompt

                # Call API
                result = self._client.audio.transcriptions.create(**api_kwargs)

            elapsed_ms = (time.time() - start_time) * 1000

            # Parse response
            if response_format == "verbose_json":
                text = result.text.strip()
                segments = []
                word_timestamps = []

                # Extract segments
                for seg in getattr(result, "segments", []):
                    segments.append({
                        "text": seg.get("text", "").strip(),
                        "start": seg.get("start", 0.0),
                        "end": seg.get("end", 0.0),
                        "confidence": 1.0 - seg.get("no_speech_probability", 0.0),
                    })

                # Extract word timestamps
                for word_obj in getattr(result, "words", []):
                    word_timestamps.append({
                        "word": word_obj.get("word", "").strip(),
                        "start": word_obj.get("start", 0.0),
                        "end": word_obj.get("end", 0.0),
                    })

                detected_language = getattr(result, "language", language or "en")
                duration = getattr(result, "duration", 0.0)

                logger.info(
                    f"OpenAI Whisper: {len(text)} chars, "
                    f"lang={detected_language}, {elapsed_ms:.0f}ms"
                )

                return {
                    "text": text,
                    "segments": segments,
                    "word_timestamps": word_timestamps,
                    "language": detected_language,
                    "confidence": 0.95,  # OpenAI doesn't provide overall confidence
                    "duration_seconds": duration,
                    "processing_time_ms": elapsed_ms,
                    "provider": "openai-whisper",
                }

            else:  # Simple text/json/srt/vtt response
                text = str(result).strip() if response_format == "text" else result.text.strip()
                
                logger.info(f"OpenAI Whisper: {len(text)} chars, {elapsed_ms:.0f}ms")
                
                return {
                    "text": text,
                    "segments": [],
                    "word_timestamps": [],
                    "language": language or "en",
                    "confidence": 0.95,
                    "processing_time_ms": elapsed_ms,
                    "provider": "openai-whisper",
                }

        except Exception as e:
            logger.error(f"OpenAI Whisper API failed: {e}")
            return {"error": str(e), "provider": "openai-whisper"}

        finally:
            # Clean up temp file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def detect_language(self, audio_data: bytes, input_format: str = "webm") -> tuple[str, float]:
        """
        Detect language from audio.

        Returns:
            (language_code, confidence)
        """
        result = self.transcribe(
            audio_data,
            input_format=input_format,
            language=None,  # Auto-detect
            response_format="json",
        )
        
        return result.get("language", "en"), 0.95

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": "openai-whisper",
            "model": settings.OPENAI_WHISPER_MODEL,
            "available": self._available,
            "supports_streaming": False,
            "supports_word_timestamps": True,
            "cost_per_minute": 0.006,
        }