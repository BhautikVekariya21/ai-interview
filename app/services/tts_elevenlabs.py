"""
ElevenLabs TTS — Uses raw HTTP requests (no SDK version issues).
Free tier: 10,000 characters/month.
"""

import io
import requests
from typing import Optional, List, Dict, Generator
from loguru import logger

from app.core.config import settings


class ElevenLabsTTS:
    """
    ElevenLabs TTS via direct REST API.

    No SDK dependency — uses requests library directly.
    This avoids all elevenlabs package version conflicts.

    API docs: https://elevenlabs.io/docs/api-reference/text-to-speech
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self):
        self.api_key: str = settings.ELEVENLABS_API_KEY or ""
        self.default_voice_id: str = settings.ELEVENLABS_VOICE_ID
        self.model_id: str = settings.ELEVENLABS_MODEL
        self._available: bool = False
        self._voices_cache: Optional[List[Dict]] = None

        self._initialize()

    def _initialize(self):
        """Validate API key by checking account."""
        if not self.api_key:
            logger.debug(
                "ELEVENLABS_API_KEY not set — ElevenLabs disabled"
            )
            return

        try:
            # Quick validation — check subscription
            resp = requests.get(
                f"{self.BASE_URL}/user/subscription",
                headers={"xi-api-key": self.api_key},
                timeout=10,
            )

            if resp.status_code == 200:
                data = resp.json()
                char_count = data.get("character_count", 0)
                char_limit = data.get("character_limit", 0)
                remaining = char_limit - char_count
                tier = data.get("tier", "free")

                self._available = True
                logger.info(
                    f"  ✓ ElevenLabs initialized | "
                    f"Tier: {tier} | "
                    f"Remaining: {remaining:,} chars | "
                    f"Voice: {self.default_voice_id}"
                )
            elif resp.status_code == 401:
                logger.warning(
                    "  ✗ ElevenLabs API key invalid (401)"
                )
            else:
                logger.warning(
                    f"  ✗ ElevenLabs check failed: "
                    f"{resp.status_code}"
                )

        except requests.exceptions.ConnectionError:
            logger.warning(
                "  ✗ ElevenLabs: cannot reach API "
                "(no internet?)"
            )
        except Exception as e:
            logger.warning(f"  ✗ ElevenLabs init failed: {e}")

    @property
    def is_available(self) -> bool:
        return self._available

    def generate(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speed: float = 1.0,
        output_format: str = "mp3_44100_128",
    ) -> Optional[bytes]:
        """
        Generate speech audio from text via REST API.

        Returns: MP3 audio bytes or None on failure.
        """
        if not self._available:
            return None

        if not text or not text.strip():
            return None

        voice = self._resolve_voice_id(
            voice_id or self.default_voice_id
        )
        model = model_id or self.model_id

        url = (
            f"{self.BASE_URL}/text-to-speech/{voice}"
            f"?output_format={output_format}"
        )

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True,
            },
        }

        try:
            logger.debug(
                f"ElevenLabs: generating {len(text)} chars, "
                f"voice={voice}, model={model}"
            )

            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            if resp.status_code == 200:
                audio_bytes = resp.content

                if audio_bytes and len(audio_bytes) > 100:
                    logger.info(
                        f"  ✓ ElevenLabs: "
                        f"{len(audio_bytes):,} bytes"
                    )
                    return audio_bytes

                logger.warning(
                    "ElevenLabs returned empty audio"
                )
                return None

            elif resp.status_code == 401:
                logger.error(
                    "ElevenLabs: invalid API key (401)"
                )
                self._available = False
                return None

            elif resp.status_code == 422:
                error_detail = ""
                try:
                    error_detail = resp.json().get(
                        "detail", {}
                    ).get("message", resp.text[:200])
                except Exception:
                    error_detail = resp.text[:200]
                logger.error(
                    f"ElevenLabs validation error: "
                    f"{error_detail}"
                )
                return None

            elif resp.status_code == 429:
                logger.warning(
                    "ElevenLabs: rate limited or "
                    "character quota exceeded (429)"
                )
                return None

            else:
                logger.error(
                    f"ElevenLabs error: "
                    f"{resp.status_code} — "
                    f"{resp.text[:200]}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error("ElevenLabs: request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("ElevenLabs: connection error")
            return None
        except Exception as e:
            logger.error(f"ElevenLabs generation failed: {e}")
            return None

    def generate_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> Generator[bytes, None, None]:
        """
        Stream audio chunks for real-time playback.
        Yields MP3 chunks as they arrive.
        """
        if not self._available:
            return

        voice = self._resolve_voice_id(
            voice_id or self.default_voice_id
        )
        model = model_id or self.model_id

        url = (
            f"{self.BASE_URL}/text-to-speech/{voice}"
            f"/stream?output_format=mp3_44100_128"
        )

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }

        try:
            logger.debug(
                f"ElevenLabs streaming: {len(text)} chars"
            )

            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60,
                stream=True,
            )

            if resp.status_code != 200:
                logger.error(
                    f"ElevenLabs stream error: "
                    f"{resp.status_code}"
                )
                return

            chunk_count = 0
            for chunk in resp.iter_content(chunk_size=4096):
                if chunk:
                    chunk_count += 1
                    yield chunk

            logger.debug(
                f"ElevenLabs stream done: "
                f"{chunk_count} chunks"
            )

        except Exception as e:
            logger.error(
                f"ElevenLabs streaming failed: {e}"
            )

    def list_voices(self) -> List[Dict]:
        """List all available voices."""
        if not self._available:
            return []

        if self._voices_cache is not None:
            return self._voices_cache

        try:
            resp = requests.get(
                f"{self.BASE_URL}/voices",
                headers={"xi-api-key": self.api_key},
                timeout=15,
            )

            if resp.status_code != 200:
                logger.error(
                    f"Failed to list voices: "
                    f"{resp.status_code}"
                )
                return []

            data = resp.json()
            voices = []

            for voice in data.get("voices", []):
                labels = voice.get("labels", {}) or {}
                voices.append({
                    "voice_id": voice.get("voice_id", ""),
                    "name": voice.get("name", "Unknown"),
                    "category": voice.get(
                        "category", "unknown"
                    ),
                    "gender": labels.get("gender", "unknown"),
                    "language": labels.get("language", "en"),
                    "description": labels.get(
                        "description",
                        voice.get("description", ""),
                    ),
                    "use_case": labels.get("use_case", ""),
                    "accent": labels.get("accent", ""),
                    "age": labels.get("age", ""),
                    "preview_url": voice.get(
                        "preview_url", None
                    ),
                    "provider": "elevenlabs",
                })

            self._voices_cache = voices
            logger.info(
                f"ElevenLabs: {len(voices)} voices loaded"
            )
            return voices

        except Exception as e:
            logger.error(
                f"Failed to list ElevenLabs voices: {e}"
            )
            return []

    def get_voice_info(
        self, voice_id: str
    ) -> Optional[Dict]:
        """Get details about a specific voice."""
        voice_id = self._resolve_voice_id(voice_id)
        for voice in self.list_voices():
            if voice["voice_id"] == voice_id:
                return voice
        return None

    def get_usage(self) -> Optional[Dict]:
        """Get character usage / quota info."""
        if not self._available:
            return None

        try:
            resp = requests.get(
                f"{self.BASE_URL}/user/subscription",
                headers={"xi-api-key": self.api_key},
                timeout=10,
            )

            if resp.status_code == 200:
                data = resp.json()
                return {
                    "character_count": data.get(
                        "character_count", 0
                    ),
                    "character_limit": data.get(
                        "character_limit", 0
                    ),
                    "remaining": (
                        data.get("character_limit", 0)
                        - data.get("character_count", 0)
                    ),
                    "tier": data.get("tier", "free"),
                }

            return None

        except Exception as e:
            logger.error(
                f"Failed to get ElevenLabs usage: {e}"
            )
            return None

    def _resolve_voice_id(self, voice_id: str) -> str:
        """Resolve preset name to actual voice ID."""
        if not voice_id:
            return self.default_voice_id

        preset_id = settings.ELEVENLABS_VOICES.get(
            voice_id.lower()
        )
        if preset_id:
            return preset_id

        return voice_id