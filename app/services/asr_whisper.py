"""
Local Whisper ASR — Fallback engine (runs on CPU/GPU).
FIXED VERSION with proper error handling and format support.
"""

import os
import time
import tempfile
import subprocess
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from loguru import logger

from app.core.config import settings


class WhisperASR:
    """
    Local Whisper inference (fallback only).
    Model sizes: tiny (39M), base (74M), small (244M), medium (769M), large (1550M).
    """

    SUPPORTED_FORMATS = {"wav", "mp3", "m4a", "webm", "ogg", "flac", "mp4", "opus"}

    def __init__(self):
        self._model = None
        self._model_size: str = settings.WHISPER_MODEL_SIZE
        self._device: str = settings.WHISPER_DEVICE
        self._available: bool = False
        self._ffmpeg_available: bool = False
        self._check_ffmpeg()
        self._initialize()

    def _check_ffmpeg(self) -> None:
        """Check if FFmpeg is available for audio conversion."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            self._ffmpeg_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._ffmpeg_available = False
            logger.debug("FFmpeg not found - some audio formats may not work")

    def _initialize(self):
        """Load Whisper model."""
        try:
            import whisper

            logger.info(
                f"  Loading local Whisper '{self._model_size}' on {self._device}..."
            )
            
            self._model = whisper.load_model(
                self._model_size,
                device=self._device
            )
            
            self._available = True
            logger.info(
                f"  ✓ Local Whisper '{self._model_size}' loaded on {self._device}"
            )
            
        except ImportError:
            logger.debug(
                "  · Local Whisper not installed — pip install openai-whisper"
            )
        except Exception as e:
            logger.warning(f"  ✗ Local Whisper init failed: {e}")

    @property
    def is_available(self) -> bool:
        """Check if model is loaded."""
        return self._available and self._model is not None

    def _convert_to_wav(
        self,
        audio_data: bytes,
        input_format: str
    ) -> Tuple[bytes, str]:
        """
        Convert audio to WAV format for Whisper.
        
        Returns:
            Tuple of (converted_bytes, format)
        """
        if not self._ffmpeg_available:
            return audio_data, input_format

        if input_format.lower() == "wav":
            return audio_data, "wav"

        input_file = None
        output_file = None

        try:
            # Write input to temp file
            with tempfile.NamedTemporaryFile(
                suffix=f".{input_format}",
                delete=False
            ) as f:
                f.write(audio_data)
                input_file = f.name

            # Create output temp file
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            ) as f:
                output_file = f.name

            # Convert using FFmpeg
            cmd = [
                "ffmpeg", "-y",
                "-i", input_file,
                "-acodec", "pcm_s16le",
                "-ar", "16000",  # 16kHz for Whisper
                "-ac", "1",  # Mono
                output_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0:
                with open(output_file, "rb") as f:
                    converted = f.read()
                logger.debug(f"Converted {input_format} to WAV ({len(converted):,} bytes)")
                return converted, "wav"
            else:
                logger.warning(f"FFmpeg conversion failed: {result.stderr.decode()[:200]}")
                return audio_data, input_format

        except Exception as e:
            logger.warning(f"Audio conversion error: {e}")
            return audio_data, input_format

        finally:
            for path in [input_file, output_file]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

    def transcribe(
        self,
        audio_data: bytes,
        input_format: str = "wav",
        language: Optional[str] = None,
        task: str = "transcribe",
        word_timestamps: bool = True,
        initial_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio using local Whisper model.

        Args:
            audio_data: Raw audio bytes
            input_format: File format (wav, webm, mp3, etc.)
            language: ISO 639-1 code (e.g., 'en', 'hi')
            task: transcribe | translate
            word_timestamps: Extract word-level timestamps
            initial_prompt: Optional context prompt

        Returns:
            Dict with text, segments, word_timestamps, language, confidence
        """
        if not self.is_available:
            return {"error": "Local Whisper model not loaded", "provider": "whisper-local"}

        if not audio_data or len(audio_data) < 100:
            return {"error": "Audio data too small", "provider": "whisper-local"}

        start_time = time.time()
        tmp_path = None

        try:
            # Normalize format
            fmt = (input_format or "wav").lower().strip()
            if fmt not in self.SUPPORTED_FORMATS:
                fmt = "wav"

            # Convert non-WAV formats
            if fmt != "wav" and fmt in {"webm", "ogg", "opus", "m4a", "mp4"}:
                audio_data, fmt = self._convert_to_wav(audio_data, fmt)

            # Save to temp file
            with tempfile.NamedTemporaryFile(
                suffix=f".{fmt}",
                delete=False
            ) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            logger.debug(f"Whisper processing: {tmp_path} ({len(audio_data):,} bytes)")

            # Transcription options
            opts: Dict[str, Any] = {
                "task": task,
                "word_timestamps": word_timestamps,
                "fp16": settings.WHISPER_FP16 and self._device != "cpu",
            }
            
            if language:
                opts["language"] = language
            if initial_prompt:
                opts["initial_prompt"] = initial_prompt

            # Run transcription
            result = self._model.transcribe(tmp_path, **opts)
            
            elapsed_ms = (time.time() - start_time) * 1000

            # Parse segments
            segments = []
            word_ts = []
            
            for seg in result.get("segments", []):
                seg_confidence = 1.0 - seg.get("no_speech_prob", 0.0)
                segments.append({
                    "text": seg.get("text", "").strip(),
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "confidence": seg_confidence,
                })
                
                # Extract word timestamps
                for w in seg.get("words", []):
                    word_ts.append({
                        "word": w.get("word", "").strip(),
                        "start": w.get("start", 0.0),
                        "end": w.get("end", 0.0),
                        "probability": w.get("probability", 0.0),
                    })

            # Calculate average confidence
            confidences = [s["confidence"] for s in segments if s["confidence"] > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            text = result.get("text", "").strip()
            detected_language = result.get("language", language or "en")

            # Calculate duration from segments
            duration_seconds = 0.0
            if segments:
                duration_seconds = max(s.get("end", 0.0) for s in segments)

            logger.info(
                f"Local Whisper: {len(text)} chars, "
                f"lang={detected_language}, conf={avg_confidence:.2f}, {elapsed_ms:.0f}ms"
            )

            return {
                "text": text,
                "transcript": text,  # Alias for compatibility
                "segments": segments,
                "word_timestamps": word_ts,
                "language": detected_language,
                "confidence": avg_confidence,
                "duration_seconds": duration_seconds,
                "processing_time_ms": elapsed_ms,
                "model_size": self._model_size,
                "provider": "whisper-local",
            }

        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            return {
                "error": str(e),
                "provider": "whisper-local",
                "text": "",
            }

        finally:
            # Clean up temp file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def detect_language(
        self,
        audio_data: bytes,
        input_format: str = "wav"
    ) -> Tuple[str, float]:
        """
        Detect language from audio.

        Returns:
            (language_code, confidence)
        """
        if not self.is_available:
            return "en", 0.0
            
        tmp_path = None
        
        try:
            import whisper
            
            # Convert if needed
            if input_format.lower() != "wav":
                audio_data, input_format = self._convert_to_wav(audio_data, input_format)
            
            with tempfile.NamedTemporaryFile(
                suffix=f".{input_format}",
                delete=False
            ) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            # Load and pad/trim audio
            audio = whisper.load_audio(tmp_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self._model.device)
            
            # Detect language
            _, probs = self._model.detect_language(mel)
            lang = max(probs, key=probs.get)
            
            return lang, probs[lang]
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en", 0.0
            
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "whisper-local",
            "model_size": self._model_size,
            "device": self._device,
            "available": self._available,
            "ffmpeg_available": self._ffmpeg_available,
            "fp16": settings.WHISPER_FP16,
            "supports_streaming": False,
            "supports_word_timestamps": True,
            "cost_per_minute": 0.0,  # Free (local)
            "supported_formats": list(self.SUPPORTED_FORMATS),
        }