"""
Vosk offline ASR — Last-resort fallback (no internet required).
"""

import json
import time
from typing import Dict, Any
from pathlib import Path
from loguru import logger

from app.core.config import settings


class VoskASR:
    """
    Vosk Offline ASR:
    - No internet required
    - Free
    - Lower accuracy than cloud providers
    - Last resort fallback
    """

    def __init__(self):
        self._model = None
        self._available: bool = False
        self._initialize()

    def _initialize(self):
        """Load Vosk model if available."""
        try:
            from vosk import Model

            # Look for model in standard locations
            model_path = Path("models/vosk")
            
            if not model_path.exists():
                # Search for any vosk model
                for p in Path(".").glob("**/vosk*model*"):
                    if p.is_dir():
                        model_path = p
                        break

            if model_path.exists():
                self._model = Model(str(model_path))
                self._available = True
                logger.info(f"  ✓ Vosk offline ASR initialized ({model_path})")
            else:
                logger.debug(
                    "  · Vosk model not found — "
                    "download from https://alphacephei.com/vosk/models"
                )
                
        except ImportError:
            logger.debug("  · Vosk not installed — pip install vosk")
        except Exception as e:
            logger.debug(f"  · Vosk init failed: {e}")

    @property
    def is_available(self) -> bool:
        """Check if model is loaded."""
        return self._available and self._model is not None

    def transcribe(
        self,
        audio_data: bytes,
        input_format: str = "wav",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Vosk.

        Args:
            audio_data: WAV audio bytes (16kHz mono)
            input_format: Must be 'wav'
            language: Language code (ignored, depends on model)

        Returns:
            Dict with text, language
        """
        if not self.is_available:
            return {"error": "Vosk not available"}

        start_time = time.time()

        try:
            from vosk import KaldiRecognizer

            # Create recognizer
            recognizer = KaldiRecognizer(
                self._model,
                settings.ASR_SAMPLE_RATE
            )
            recognizer.SetWords(True)

            results = []
            chunk_size = 4000

            # Process audio in chunks
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]
                
                if recognizer.AcceptWaveform(chunk):
                    result = json.loads(recognizer.Result())
                    if result.get("text"):
                        results.append(result)

            # Get final result
            final_result = json.loads(recognizer.FinalResult())
            if final_result.get("text"):
                results.append(final_result)

            # Combine all text
            full_text = " ".join(
                result.get("text", "") for result in results
            ).strip()

            elapsed_ms = (time.time() - start_time) * 1000

            logger.info(f"Vosk: {len(full_text)} chars, {elapsed_ms:.0f}ms")

            return {
                "text": full_text,
                "segments": [],
                "word_timestamps": [],
                "language": language,
                "confidence": 0.7,  # Vosk doesn't provide confidence
                "processing_time_ms": elapsed_ms,
                "provider": "vosk-offline",
            }

        except Exception as e:
            logger.error(f"Vosk transcription failed: {e}")
            return {"error": str(e), "provider": "vosk-offline"}

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": "vosk-offline",
            "available": self._available,
            "supports_streaming": False,
            "supports_word_timestamps": False,
            "cost_per_minute": 0.0,  # Free
            "requires_internet": False,
        }