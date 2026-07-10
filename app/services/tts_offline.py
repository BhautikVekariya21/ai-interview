"""
pyttsx3 offline TTS — Last resort fallback.
No internet required. Works on Windows, macOS, Linux.
"""

import os
import tempfile
from typing import Optional, List, Dict
from loguru import logger


class OfflineTTS:
    """
    pyttsx3-based offline TTS engine.
    Uses system voices (SAPI5 on Windows, espeak on Linux).
    Always available as last resort.
    """

    def __init__(self):
        self._available: bool = False
        self._voices_cache: Optional[List[Dict]] = None
        self._initialize()

    def _initialize(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.stop()
            self._available = True
            logger.info(
                "  ✓ pyttsx3 (offline) initialized — "
                "last resort fallback"
            )
        except ImportError:
            logger.debug(
                "  · pyttsx3 not installed — "
                "run: pip install pyttsx3"
            )
        except Exception as e:
            logger.debug(f"  · pyttsx3 init failed: {e}")

    @property
    def is_available(self) -> bool:
        return self._available

    def generate(
        self,
        text: str,
        rate: int = 175,
        volume: float = 1.0,
        voice_index: int = 0,
    ) -> Optional[bytes]:
        if not self._available:
            return None

        tmp_path = None
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)

            voices = engine.getProperty("voices")
            if voices and 0 <= voice_index < len(voices):
                engine.setProperty(
                    "voice", voices[voice_index].id
                )

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp_path = tmp.name

            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            engine.stop()

            if os.path.exists(tmp_path):
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()

                if audio_bytes and len(audio_bytes) > 44:
                    logger.debug(
                        f"pyttsx3: generated "
                        f"{len(audio_bytes):,} bytes"
                    )
                    return audio_bytes

            return None

        except Exception as e:
            logger.error(f"pyttsx3 generation failed: {e}")
            return None

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def list_voices(self) -> List[Dict]:
        if not self._available:
            return []

        if self._voices_cache is not None:
            return self._voices_cache

        try:
            import pyttsx3
            engine = pyttsx3.init()
            sys_voices = engine.getProperty("voices")
            engine.stop()

            result = []
            for i, v in enumerate(sys_voices or []):
                name_lower = v.name.lower()
                if any(
                    kw in name_lower
                    for kw in [
                        "female", "zira", "hazel", "susan",
                    ]
                ):
                    gender = "female"
                elif any(
                    kw in name_lower
                    for kw in [
                        "male", "david", "mark", "james",
                    ]
                ):
                    gender = "male"
                else:
                    gender = "unknown"

                lang = "en"
                if v.languages:
                    lang_raw = str(v.languages[0])
                    if len(lang_raw) >= 2:
                        lang = lang_raw[:2].lower()

                result.append({
                    "voice_id": f"offline_{i}",
                    "name": v.name,
                    "gender": gender,
                    "language": lang,
                    "provider": "offline",
                    "description": (
                        f"System voice: {v.name}"
                    ),
                })

            self._voices_cache = result
            return result

        except Exception as e:
            logger.error(
                f"Failed to list offline voices: {e}"
            )
            return []