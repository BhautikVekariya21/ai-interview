"""
End-of-Speech Detection.
Energy-based VAD + WebRTC VAD + silence duration tracking.
"""

import time
from typing import Optional, Tuple, Dict, Any
from loguru import logger

from app.core.config import settings

# Optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    WEBRTCVAD_AVAILABLE = False


class EndOfSpeechDetector:
    """
    End-of-speech detection using:
    1. RMS energy threshold (is chunk loud enough?)
    2. WebRTC VAD (neural voice activity detection)
    3. Silence duration timer (>= threshold → speech ended)
    """

    def __init__(
        self,
        silence_threshold_db: Optional[float] = None,
        silence_duration_seconds: Optional[float] = None,
        sample_rate: Optional[int] = None,
        vad_aggressiveness: Optional[int] = None,
    ):
        self.silence_threshold_db = (
            silence_threshold_db
            if silence_threshold_db is not None
            else settings.SILENCE_THRESHOLD_DB
        )
        self.silence_duration = (
            silence_duration_seconds
            if silence_duration_seconds is not None
            else settings.SILENCE_DURATION_SECONDS
        )
        self.sample_rate = (
            sample_rate
            if sample_rate is not None
            else settings.ASR_SAMPLE_RATE
        )
        self.vad_aggressiveness = (
            vad_aggressiveness
            if vad_aggressiveness is not None
            else settings.VAD_AGGRESSIVENESS
        )

        # Internal state
        self._silence_start: Optional[float] = None
        self._last_speech_time: Optional[float] = None
        self._is_speaking: bool = False
        self._speech_detected: bool = False

        # WebRTC VAD
        self._vad = None
        if WEBRTCVAD_AVAILABLE:
            try:
                self._vad = webrtcvad.Vad(self.vad_aggressiveness)
                logger.debug(
                    f"WebRTC VAD initialized (aggressiveness={self.vad_aggressiveness})"
                )
            except Exception as e:
                logger.warning(f"WebRTC VAD init failed: {e}")

    def reset(self):
        """Reset detector state."""
        self._silence_start = None
        self._last_speech_time = None
        self._is_speaking = False
        self._speech_detected = False

    def process_chunk(
        self,
        audio_chunk: bytes,
        chunk_duration_ms: int = 30,
    ) -> Tuple[bool, float, bool]:
        """
        Process one audio chunk.

        Args:
            audio_chunk: PCM audio bytes (16-bit mono)
            chunk_duration_ms: Duration of chunk in milliseconds

        Returns:
            (is_speech, silence_duration_so_far, end_of_speech_detected)
        """
        current_time = time.time()

        # Check energy-based speech detection
        is_speech_energy = self._detect_speech_energy(audio_chunk)

        # Check WebRTC VAD
        is_speech_vad = True  # Default if VAD unavailable
        if self._vad is not None:
            try:
                needed_bytes = int(self.sample_rate * 2 * chunk_duration_ms / 1000)
                vad_bytes = audio_chunk[:needed_bytes]
                is_speech_vad = self._vad.is_speech(vad_bytes, self.sample_rate)
            except Exception:
                pass

        # Combine detections (either method can detect speech)
        is_speech = is_speech_energy or is_speech_vad

        if is_speech:
            # Speech detected
            self._is_speaking = True
            self._speech_detected = True
            self._last_speech_time = current_time
            self._silence_start = None
            return True, 0.0, False

        # Silence detected
        if self._silence_start is None:
            self._silence_start = current_time

        silence_duration = current_time - self._silence_start

        # Check if end of speech
        end_of_speech = (
            self._speech_detected
            and silence_duration >= self.silence_duration
        )

        if end_of_speech:
            logger.info(
                f"End-of-speech detected: {silence_duration:.1f}s silence "
                f"(threshold: {self.silence_duration}s)"
            )

        return False, silence_duration, end_of_speech

    def _detect_speech_energy(self, audio_chunk: bytes) -> bool:
        """Detect speech using RMS energy threshold."""
        if not NUMPY_AVAILABLE:
            return True  # Assume speech if numpy unavailable
            
        try:
            samples = np.frombuffer(audio_chunk, dtype=np.int16)
            
            if len(samples) == 0:
                return False
                
            rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
            
            if rms == 0:
                return False
                
            db = 20 * np.log10(rms / 32768.0)
            
            return db > self.silence_threshold_db
            
        except Exception:
            return True  # Assume speech on error

    def analyze_audio_for_speech(
        self,
        audio_data: bytes,
        chunk_size_ms: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze complete audio for speech vs silence statistics.

        Args:
            audio_data: Complete audio (PCM 16-bit)
            chunk_size_ms: Chunk size in milliseconds

        Returns:
            Statistics dict
        """
        if not NUMPY_AVAILABLE:
            return {"error": "numpy not available"}

        self.reset()
        
        samples = np.frombuffer(audio_data, dtype=np.int16)
        chunk_samples = int(self.sample_rate * chunk_size_ms / 1000)

        speech_chunks = 0
        silence_chunks = 0
        total_chunks = 0

        for i in range(0, len(samples) - chunk_samples, chunk_samples):
            chunk = samples[i : i + chunk_samples].tobytes()
            is_speech, _, _ = self.process_chunk(chunk, chunk_size_ms)
            
            total_chunks += 1
            if is_speech:
                speech_chunks += 1
            else:
                silence_chunks += 1

        total_duration = len(samples) / self.sample_rate
        speech_ratio = speech_chunks / max(total_chunks, 1)

        return {
            "total_duration_seconds": round(total_duration, 2),
            "speech_duration_seconds": round(speech_ratio * total_duration, 2),
            "silence_duration_seconds": round((1 - speech_ratio) * total_duration, 2),
            "speech_percentage": round(speech_ratio * 100, 1),
            "total_chunks_analyzed": total_chunks,
        }

    @property
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking

    @property
    def has_detected_speech(self) -> bool:
        """Check if any speech was detected."""
        return self._speech_detected

    def get_info(self) -> Dict[str, Any]:
        """Get detector configuration."""
        return {
            "silence_threshold_db": self.silence_threshold_db,
            "silence_duration_seconds": self.silence_duration,
            "sample_rate": self.sample_rate,
            "vad_aggressiveness": self.vad_aggressiveness,
            "webrtc_vad_available": self._vad is not None,
            "numpy_available": NUMPY_AVAILABLE,
        }