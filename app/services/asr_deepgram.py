"""
Deepgram Streaming ASR — Real-time transcription with live interim results.
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, Callable, Awaitable
from loguru import logger

from app.core.config import settings


class DeepgramStreamingASR:
    """
    Deepgram Nova-2 Streaming ASR:
    - Real-time transcription (50ms latency)
    - Live interim results
    - Automatic punctuation & filler detection
    - $0.0043/minute
    """

    def __init__(self):
        self._client = None
        self._available = False
        self._initialize()

    def _initialize(self):
        """Initialize Deepgram client."""
        if not settings.DEEPGRAM_API_KEY:
            logger.debug("  · Deepgram — DEEPGRAM_API_KEY not set")
            return

        try:
            from deepgram import DeepgramClient
            
            self._client = DeepgramClient(settings.DEEPGRAM_API_KEY)
            self._available = True
            logger.info("  ✓ Deepgram streaming ASR initialized")
            
        except ImportError:
            logger.warning("  ✗ 'deepgram-sdk' not installed — pip install deepgram-sdk")
        except Exception as e:
            logger.warning(f"  ✗ Deepgram init failed: {e}")

    @property
    def is_available(self) -> bool:
        """Check if provider is ready."""
        return self._available and self._client is not None

    async def transcribe_stream(
        self,
        audio_stream: asyncio.Queue,
        on_transcript: Callable[[Dict[str, Any]], Awaitable[None]],
        on_error: Optional[Callable[[str], Awaitable[None]]] = None,
        language: str = "en",
        interim_results: bool = True,
        punctuate: bool = True,
        filler_words: bool = True,
    ):
        """
        Real-time streaming transcription.

        Args:
            audio_stream: asyncio.Queue of audio chunks (bytes)
            on_transcript: Async callback for each transcript
                Receives: {
                    "text": str,
                    "is_final": bool,
                    "confidence": float,
                    "words": [{"word": str, "start": float, "end": float}]
                }
            on_error: Async callback for errors
            language: Language code
            interim_results: Show partial transcripts
            punctuate: Auto-add punctuation
            filler_words: Detect "um", "uh", etc.
        """
        if not self.is_available:
            if on_error:
                await on_error("Deepgram not configured")
            return

        try:
            from deepgram import LiveTranscriptionEvents, LiveOptions

            connection = self._client.listen.live.v("1")

            # Event handlers
            async def on_message(result, **kwargs):
                """Handle transcript events."""
                sentence = result.channel.alternatives[0].transcript
                
                if not sentence:
                    return

                is_final = result.is_final
                confidence = result.channel.alternatives[0].confidence
                
                words = [
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "confidence": w.confidence,
                    }
                    for w in result.channel.alternatives[0].words
                ]

                await on_transcript({
                    "text": sentence,
                    "is_final": is_final,
                    "confidence": confidence,
                    "words": words,
                    "speech_final": result.speech_final,
                })

            async def on_error_event(error, **kwargs):
                """Handle errors."""
                logger.error(f"Deepgram error: {error}")
                if on_error:
                    await on_error(str(error))

            # Attach event handlers
            connection.on(LiveTranscriptionEvents.Transcript, on_message)
            connection.on(LiveTranscriptionEvents.Error, on_error_event)

            # Connection options
            options = LiveOptions(
                language=language,
                model=settings.DEEPGRAM_MODEL,
                punctuate=punctuate,
                interim_results=interim_results,
                filler_words=filler_words,
                smart_format=True,
                encoding="linear16",
                sample_rate=settings.ASR_SAMPLE_RATE,
                channels=settings.ASR_CHANNELS,
            )

            # Start connection
            if not await connection.start(options):
                raise RuntimeError("Deepgram connection failed to start")

            logger.info("Deepgram streaming started")

            # Stream audio chunks
            while True:
                chunk = await audio_stream.get()
                
                if chunk is None:  # Sentinel value to stop
                    break
                    
                connection.send(chunk)

            # Finalize stream
            await connection.finish()
            logger.info("Deepgram streaming finished")

        except Exception as e:
            logger.error(f"Deepgram streaming failed: {e}")
            if on_error:
                await on_error(str(e))

    def transcribe_file(
        self,
        audio_data: bytes,
        input_format: str = "webm",
        language: str = "en",
        detect_language: bool = False,
    ) -> Dict[str, Any]:
        """
        Non-streaming file transcription (batch mode).

        Args:
            audio_data: Raw audio bytes
            input_format: File format
            language: Language code
            detect_language: Auto-detect language

        Returns:
            Dict with text, confidence, words, language
        """
        if not self.is_available:
            return {"error": "Deepgram not available"}

        start_time = time.time()

        try:
            from deepgram import PrerecordedOptions

            # deepgram-sdk compatibility: newer versions accept a plain dict payload
            # and some versions raise "Cannot instantiate typing.Union" with FileSource.
            source = {"buffer": audio_data}
            
            options = PrerecordedOptions(
                language=language,
                model=settings.DEEPGRAM_MODEL,
                punctuate=True,
                filler_words=True,
                smart_format=True,
                detect_language=detect_language,
            )

            response = self._client.listen.prerecorded.v("1").transcribe_file(
                source, options
            )

            # Parse response
            result = response.results.channels[0].alternatives[0]
            text = result.transcript.strip()
            confidence = result.confidence
            
            words = [
                {
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "confidence": getattr(w, "confidence", 0.0),
                }
                for w in (getattr(result, "words", None) or [])
            ]

            detected_language = (
                response.results.channels[0].detected_language
                if detect_language else language
            )

            elapsed_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Deepgram: {len(text)} chars, "
                f"conf={confidence:.2f}, {elapsed_ms:.0f}ms"
            )

            return {
                "text": text,
                "confidence": confidence,
                "language": detected_language,
                "word_timestamps": words,
                "segments": [],
                "processing_time_ms": elapsed_ms,
                "provider": "deepgram",
            }

        except Exception as e:
            logger.error(f"Deepgram file transcription failed: {e}")
            return {"error": str(e), "provider": "deepgram"}

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": "deepgram",
            "model": settings.DEEPGRAM_MODEL,
            "available": self._available,
            "supports_streaming": True,
            "supports_word_timestamps": True,
            "cost_per_minute": 0.0043,
            "latency_ms": 50,
        }