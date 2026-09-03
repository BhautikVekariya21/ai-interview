"""
Groq Whisper ASR — FREE cloud transcription!
Groq provides Whisper API with generous free tier.
"""

import time
import tempfile
import os
import base64
from typing import Dict, Any, Optional
from loguru import logger

from app.core.config import settings


class GroqWhisperASR:
    """
    Groq Whisper API — FREE Speech-to-Text!
    
    Features:
    - FREE tier with high rate limits
    - Fast inference (Groq's LPU)
    - Whisper large-v3 model
    - Supports multiple languages
    """

    def __init__(self):
        self._client = None
        self._available = False
        self._initialize()

    def _initialize(self):
        """Initialize Groq client."""
        api_key = settings.GROQ_API_KEY
        
        if not api_key:
            logger.debug("  · Groq Whisper — GROQ_API_KEY not set")
            return

        try:
            from groq import Groq
            
            self._client = Groq(api_key=api_key)
            self._available = True
            logger.info("  ✓ Groq Whisper API initialized (FREE!)")
            
        except ImportError:
            logger.warning("  ✗ 'groq' package not installed — pip install groq")
        except Exception as e:
            logger.warning(f"  ✗ Groq Whisper init failed: {e}")

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
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Groq's Whisper API.

        Args:
            audio_data: Raw audio bytes
            input_format: File format (webm, wav, mp3, m4a, ogg)
            language: ISO 639-1 code (en, es, fr) — auto-detect if None
            prompt: Optional context to guide transcription

        Returns:
            Dict with text, language, segments, confidence
        """
        if not self.is_available:
            return {"error": "Groq Whisper API not configured"}

        start_time = time.time()
        tmp_path = None

        try:
            # Normalize format
            fmt = (input_format or "webm").lower().strip()
            valid_formats = {"webm", "wav", "mp3", "m4a", "ogg", "flac", "mp4", "mpeg", "mpga"}
            if fmt not in valid_formats:
                fmt = "webm"

            # Map format to proper extension
            ext_map = {
                "webm": "webm",
                "wav": "wav", 
                "mp3": "mp3",
                "m4a": "m4a",
                "ogg": "ogg",
                "flac": "flac",
                "mp4": "mp4",
                "mpeg": "mp3",
                "mpga": "mp3",
            }
            ext = ext_map.get(fmt, "webm")

            # Save to temp file
            with tempfile.NamedTemporaryFile(
                suffix=f".{ext}",
                delete=False,
                mode="wb"
            ) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            # Prepare API call
            with open(tmp_path, "rb") as audio_file:
                # Call Groq Whisper API
                transcription = self._client.audio.transcriptions.create(
                    file=(os.path.basename(tmp_path), audio_file),
                    model="whisper-large-v3",
                    language=language,  # None = auto-detect
                    response_format="verbose_json",
                    prompt=prompt,
                )

            elapsed_ms = (time.time() - start_time) * 1000

            # Parse response
            text = transcription.text.strip() if transcription.text else ""
            detected_language = getattr(transcription, 'language', language or 'en')
            duration = getattr(transcription, 'duration', 0.0)
            
            # Extract segments if available
            segments = []
            raw_segments = getattr(transcription, 'segments', [])
            
            for seg in raw_segments:
                segments.append({
                    "text": seg.get("text", "").strip() if isinstance(seg, dict) else getattr(seg, 'text', '').strip(),
                    "start": seg.get("start", 0.0) if isinstance(seg, dict) else getattr(seg, 'start', 0.0),
                    "end": seg.get("end", 0.0) if isinstance(seg, dict) else getattr(seg, 'end', 0.0),
                    "confidence": 1.0 - (seg.get("no_speech_prob", 0.0) if isinstance(seg, dict) else getattr(seg, 'no_speech_prob', 0.0)),
                })

            # Extract word timestamps if available
            word_timestamps = []
            for seg in raw_segments:
                words = seg.get("words", []) if isinstance(seg, dict) else getattr(seg, 'words', [])
                for word in words:
                    word_timestamps.append({
                        "word": word.get("word", "") if isinstance(word, dict) else getattr(word, 'word', ''),
                        "start": word.get("start", 0.0) if isinstance(word, dict) else getattr(word, 'start', 0.0),
                        "end": word.get("end", 0.0) if isinstance(word, dict) else getattr(word, 'end', 0.0),
                    })

            logger.info(
                f"Groq Whisper: {len(text)} chars, "
                f"lang={detected_language}, {elapsed_ms:.0f}ms"
            )

            return {
                "text": text,
                "segments": segments,
                "word_timestamps": word_timestamps,
                "language": detected_language,
                "confidence": 0.95,  # Groq doesn't provide overall confidence
                "duration_seconds": duration,
                "processing_time_ms": elapsed_ms,
                "provider": "groq-whisper",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Groq Whisper API failed: {error_msg}")
            
            # Check for specific errors
            if "rate_limit" in error_msg.lower():
                return {"error": "Rate limit exceeded, please try again", "provider": "groq-whisper"}
            elif "invalid_api_key" in error_msg.lower():
                return {"error": "Invalid Groq API key", "provider": "groq-whisper"}
            
            return {"error": error_msg, "provider": "groq-whisper"}

        finally:
            # Clean up temp file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def detect_language(self, audio_data: bytes, input_format: str = "webm") -> tuple:
        """
        Detect language from audio.

        Returns:
            (language_code, confidence)
        """
        result = self.transcribe(
            audio_data,
            input_format=input_format,
            language=None,  # Auto-detect
        )
        
        return result.get("language", "en"), 0.95

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": "groq-whisper",
            "model": "whisper-large-v3",
            "available": self._available,
            "supports_streaming": False,
            "supports_word_timestamps": True,
            "cost_per_minute": 0.0,  # FREE!
            "rate_limit": "Very high (free tier)",
        }