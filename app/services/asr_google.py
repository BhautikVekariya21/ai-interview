"""
Google Speech-to-Text — Free fallback ASR (via SpeechRecognition library).
"""

import io
import time
from typing import Dict, Any
from loguru import logger

from app.core.config import settings


class GoogleSpeechASR:
    """
    Google Speech Recognition via SpeechRecognition library.
    - Free (no API key needed)
    - Requires internet
    - Good accuracy for English
    - Fallback provider
    """

    def __init__(self):
        self._recognizer = None
        self._available: bool = False
        self._initialize()

    def _initialize(self):
        """Initialize SpeechRecognition."""
        try:
            import speech_recognition as sr
            
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 2.0
            self._available = True
            
            logger.info("  ✓ Google Speech (free) initialized")
            
        except ImportError:
            logger.debug(
                "  · SpeechRecognition not installed — "
                "pip install SpeechRecognition"
            )
        except Exception as e:
            logger.warning(f"  ✗ Google Speech init failed: {e}")

    @property
    def is_available(self) -> bool:
        """Check if provider is ready."""
        return self._available and self._recognizer is not None

    def transcribe(
        self,
        audio_data: bytes,
        input_format: str = "wav",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Google Speech Recognition.

        Args:
            audio_data: WAV audio bytes (16kHz mono)
            input_format: Must be 'wav'
            language: Language code (en-US, es-ES, etc.)

        Returns:
            Dict with text, confidence, language
        """
        if not self._available:
            return {"error": "Google Speech not available"}

        start_time = time.time()

        try:
            import speech_recognition as sr

            # Load audio from bytes
            audio_file = sr.AudioFile(io.BytesIO(audio_data))
            
            with audio_file as source:
                audio = self._recognizer.record(source)

            # Transcribe
            try:
                text = self._recognizer.recognize_google(
                    audio,
                    language=language,
                    show_all=False
                )
                
            except sr.UnknownValueError:
                return {
                    "text": "",
                    "error": "Could not understand audio",
                    "confidence": 0.0,
                    "provider": "google-free",
                }
                
            except sr.RequestError as e:
                return {
                    "text": "",
                    "error": f"Google API error: {e}",
                    "confidence": 0.0,
                    "provider": "google-free",
                }

            elapsed_ms = (time.time() - start_time) * 1000

            # Try to get confidence
            confidence = 0.8  # Default
            try:
                detailed = self._recognizer.recognize_google(
                    audio,
                    language=language,
                    show_all=True
                )
                if isinstance(detailed, dict):
                    alternatives = detailed.get("alternative", [])
                    if alternatives:
                        confidence = alternatives[0].get("confidence", 0.8)
            except Exception:
                pass

            logger.info(
                f"Google Speech: {len(text)} chars, {elapsed_ms:.0f}ms"
            )

            return {
                "text": text.strip() if text else "",
                "segments": [],
                "word_timestamps": [],
                "language": language,
                "confidence": confidence,
                "processing_time_ms": elapsed_ms,
                "provider": "google-free",
            }

        except Exception as e:
            logger.error(f"Google Speech failed: {e}")
            return {"error": str(e), "provider": "google-free"}

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": "google-free",
            "available": self._available,
            "supports_streaming": False,
            "supports_word_timestamps": False,
            "cost_per_minute": 0.0,  # Free
            "requires_internet": True,
        }