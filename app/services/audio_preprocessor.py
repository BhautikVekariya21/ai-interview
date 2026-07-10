"""
Audio Preprocessor — Converts and enhances audio for ASR.
"""

import os
import io
import tempfile
import subprocess
from typing import Optional, Tuple
from pathlib import Path
from loguru import logger

from app.core.config import settings


class AudioPreprocessor:
    """
    Audio preprocessing for ASR.
    Handles format conversion, resampling, and noise reduction.
    """

    SUPPORTED_FORMATS = {"wav", "mp3", "webm", "ogg", "m4a", "flac", "mp4", "opus"}

    def __init__(self):
        """Initialize preprocessor and check for FFmpeg."""
        self._ffmpeg_available = self._check_ffmpeg()
        if self._ffmpeg_available:
            logger.info("  ✓ FFmpeg available for audio processing")
        else:
            logger.warning("  · FFmpeg not found - audio conversion limited")

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @property
    def is_available(self) -> bool:
        """Check if preprocessor is functional."""
        return self._ffmpeg_available

    def convert_to_wav_16k(
        self,
        audio_data: bytes,
        input_format: str = "webm",
        normalize: bool = True
    ) -> bytes:
        """
        Convert audio to 16kHz mono WAV for ASR.
        
        Args:
            audio_data: Raw audio bytes
            input_format: Input format (webm, mp3, etc.)
            normalize: Normalize audio levels
            
        Returns:
            Converted WAV bytes
        """
        if not self._ffmpeg_available:
            logger.warning("FFmpeg not available, returning original audio")
            return audio_data

        input_format = input_format.lower().strip()
        if input_format not in self.SUPPORTED_FORMATS:
            input_format = "webm"

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

            # Build FFmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-i", input_file,
                "-acodec", "pcm_s16le",
                "-ar", str(settings.ASR_SAMPLE_RATE),
                "-ac", "1",  # Mono
            ]

            # Add normalization filter
            if normalize and settings.NORMALIZE_AUDIO:
                cmd.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])

            cmd.append(output_file)

            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr.decode()}")
                return audio_data

            # Read converted audio
            with open(output_file, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            return audio_data
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return audio_data
        finally:
            # Cleanup temp files
            for path in [input_file, output_file]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

    def reduce_noise(
        self,
        audio_data: bytes,
        input_format: str = "wav"
    ) -> bytes:
        """
        Apply noise reduction to audio.
        
        Args:
            audio_data: Audio bytes
            input_format: Input format
            
        Returns:
            Processed audio bytes
        """
        if not self._ffmpeg_available:
            return audio_data

        if not settings.NOISE_REDUCTION_ENABLED:
            return audio_data

        input_file = None
        output_file = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{input_format}",
                delete=False
            ) as f:
                f.write(audio_data)
                input_file = f.name

            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            ) as f:
                output_file = f.name

            # Apply high-pass and low-pass filters
            filters = [
                f"highpass=f={settings.HIGH_PASS_FILTER_HZ}",
                f"lowpass=f={settings.LOW_PASS_FILTER_HZ}",
                "afftdn=nf=-25",  # FFT-based denoising
            ]

            cmd = [
                "ffmpeg", "-y",
                "-i", input_file,
                "-af", ",".join(filters),
                "-acodec", "pcm_s16le",
                "-ar", str(settings.ASR_SAMPLE_RATE),
                "-ac", "1",
                output_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.warning(f"Noise reduction failed: {result.stderr.decode()}")
                return audio_data

            with open(output_file, "rb") as f:
                return f.read()

        except Exception as e:
            logger.warning(f"Noise reduction error: {e}")
            return audio_data
        finally:
            for path in [input_file, output_file]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

    def get_audio_duration(
        self,
        audio_data: bytes,
        input_format: str = "wav"
    ) -> float:
        """
        Get audio duration in seconds.
        
        Args:
            audio_data: Audio bytes
            input_format: Input format
            
        Returns:
            Duration in seconds
        """
        if not self._ffmpeg_available:
            return 0.0

        input_file = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{input_format}",
                delete=False
            ) as f:
                f.write(audio_data)
                input_file = f.name

            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                return float(result.stdout.decode().strip())
            return 0.0

        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return 0.0
        finally:
            if input_file and os.path.exists(input_file):
                try:
                    os.unlink(input_file)
                except OSError:
                    pass

    def get_audio_info(
        self,
        audio_data: bytes,
        input_format: str = "wav"
    ) -> dict:
        """Get audio file information."""
        return {
            "duration_seconds": self.get_audio_duration(audio_data, input_format),
            "size_bytes": len(audio_data),
            "format": input_format,
            "ffmpeg_available": self._ffmpeg_available,
        }


# Singleton instance
_preprocessor_instance: Optional[AudioPreprocessor] = None


def get_preprocessor() -> AudioPreprocessor:
    """Get singleton preprocessor instance."""
    global _preprocessor_instance
    if _preprocessor_instance is None:
        _preprocessor_instance = AudioPreprocessor()
    return _preprocessor_instance