"""
gTTS Provider — Free Google TTS (requires internet, NO API key).
This is the MOST RELIABLE free TTS option.
"""

import io
from typing import Optional, List, Dict
from loguru import logger


class GTTSProvider:
    """
    Google Text-to-Speech via gTTS library.

    This is the recommended FREE provider because:
      - No API key required
      - No character limits
      - Decent quality (Google's neural voices)
      - 50+ languages supported
      - Just needs internet connection

    Install: pip install gTTS
    """

    SUPPORTED_LANGUAGES = {
        "en": "English", "es": "Spanish", "fr": "French",
        "de": "German", "it": "Italian", "pt": "Portuguese",
        "nl": "Dutch", "ja": "Japanese", "ko": "Korean",
        "zh-CN": "Chinese (Simplified)", "hi": "Hindi",
        "ar": "Arabic", "ru": "Russian", "tr": "Turkish",
        "pl": "Polish", "sv": "Swedish", "da": "Danish",
        "fi": "Finnish", "no": "Norwegian", "el": "Greek",
        "cs": "Czech", "ro": "Romanian", "hu": "Hungarian",
        "th": "Thai", "vi": "Vietnamese", "id": "Indonesian",
        "ms": "Malay", "ta": "Tamil", "te": "Telugu",
        "bn": "Bengali", "gu": "Gujarati", "mr": "Marathi",
    }

    # Accent variants via TLD
    ACCENT_MAP = {
        "us": "com",
        "uk": "co.uk",
        "au": "com.au",
        "in": "co.in",
        "ca": "ca",
        "ie": "ie",
        "za": "co.za",
    }

    def __init__(self):
        self._available: bool = False
        self._initialize()

    def _initialize(self):
        """Check if gTTS is installed and working."""
        try:
            from gtts import gTTS

            # Quick test — don't actually generate, just
            # verify the import works
            self._available = True
            logger.info(
                "  ✓ gTTS initialized "
                "(FREE, no API key, internet required)"
            )
        except ImportError:
            logger.warning(
                "  ✗ gTTS not installed — "
                "run: pip install gTTS"
            )

    @property
    def is_available(self) -> bool:
        return self._available

    def generate(
        self,
        text: str,
        language: str = "en",
        slow: bool = False,
        tld: str = "com",
    ) -> Optional[bytes]:
        """
        Generate speech audio using Google TTS.

        Args:
            text: Text to speak
            language: Language code (en, es, fr, hi, etc.)
            slow: Slower speech rate
            tld: Top-level domain for accent variant
                 'com'=US, 'co.uk'=UK, 'co.in'=Indian

        Returns:
            Audio bytes (MP3) or None on failure
        """
        if not self._available:
            return None

        if not text or not text.strip():
            return None

        try:
            from gtts import gTTS

            # Validate language
            if language not in self.SUPPORTED_LANGUAGES:
                base = language.split("-")[0].lower()
                if base in self.SUPPORTED_LANGUAGES:
                    language = base
                else:
                    language = "en"

            # Split long text into chunks (gTTS has limits)
            # Max ~5000 chars per request
            if len(text) > 4500:
                return self._generate_long_text(
                    text, language, slow, tld
                )

            logger.debug(
                f"gTTS: generating {len(text)} chars, "
                f"lang={language}, slow={slow}, tld={tld}"
            )

            tts = gTTS(
                text=text,
                lang=language,
                slow=slow,
                tld=tld,
            )

            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.read()

            if audio_bytes and len(audio_bytes) > 100:
                logger.info(
                    f"  ✓ gTTS: {len(audio_bytes):,} bytes "
                    f"({len(text)} chars)"
                )
                return audio_bytes

            logger.warning("gTTS returned empty audio")
            return None

        except Exception as e:
            logger.error(f"gTTS generation failed: {e}")
            return None

    def _generate_long_text(
        self,
        text: str,
        language: str,
        slow: bool,
        tld: str,
    ) -> Optional[bytes]:
        """
        Handle long text by splitting into chunks.
        Concatenates resulting audio.
        """
        try:
            from gtts import gTTS
            from pydub import AudioSegment

            # Split on sentence boundaries
            sentences = []
            current = ""
            for char in text:
                current += char
                if char in ".!?" and len(current) > 20:
                    sentences.append(current.strip())
                    current = ""
            if current.strip():
                sentences.append(current.strip())

            # Group sentences into chunks < 4500 chars
            chunks = []
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > 4000:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    current_chunk += " " + sentence
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Generate audio for each chunk
            combined = AudioSegment.empty()
            for i, chunk in enumerate(chunks):
                tts = gTTS(
                    text=chunk, lang=language,
                    slow=slow, tld=tld,
                )
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                segment = AudioSegment.from_mp3(buf)
                combined += segment

            # Export combined audio
            output = io.BytesIO()
            combined.export(output, format="mp3")
            output.seek(0)
            result = output.read()

            logger.info(
                f"  ✓ gTTS (long): {len(result):,} bytes "
                f"from {len(chunks)} chunks"
            )
            return result

        except ImportError:
            # pydub not available — fall back to
            # generating just the first chunk
            logger.warning(
                "pydub not installed — truncating long text"
            )
            return self.generate(
                text[:4000], language, slow, tld
            )
        except Exception as e:
            logger.error(
                f"gTTS long text generation failed: {e}"
            )
            return None

    def list_voices(self) -> List[Dict]:
        """List available gTTS voices (English-only runtime policy)."""
        if not self._available:
            return []

        return [{
            "voice_id": "gtts_en",
            "name": "Google TTS - English",
            "gender": "female",
            "language": "en",
            "provider": "gtts",
            "description": "Google TTS English voice (free)",
            "preview_url": None,
        }]

    def get_supported_languages(self) -> Dict[str, str]:
        return dict(self.SUPPORTED_LANGUAGES)
