"""
Main TTS Service — Orchestrates all providers with auto-fallback.
Provider priority: ElevenLabs → gTTS → pyttsx3 (offline)
"""

import hashlib
import random
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from loguru import logger

from app.core.config import settings
from app.schemas.tts_schemas import (
    AudioQueueItem,
    TTSConfigResponse,
)
from app.services.audio_queue_manager import AudioQueueManager
from app.services.interview_script_generator import (
    get_script_generator,
)
from app.services.language_detector import LanguageDetector
from app.services.ssml_processor import SSMLProcessor
from app.services.tts_elevenlabs import ElevenLabsTTS
from app.services.tts_gtts import GTTSProvider
from app.services.tts_offline import OfflineTTS


class TTSService:
    PROVIDER_PRIORITY = ["elevenlabs", "gtts", "offline"]

    def __init__(self):
        logger.info("=" * 55)
        logger.info("  Initializing TTS Service (Module 3)")
        logger.info("=" * 55)

        self.elevenlabs = ElevenLabsTTS()
        self.gtts = GTTSProvider()
        self.offline = OfflineTTS()
        self.lang_detector = LanguageDetector()
        self.ssml = SSMLProcessor()

        self.available_providers: List[str] = []
        # Keep ElevenLabs implementation intact but do not activate it in
        # runtime provider selection for this deployment.
        if self.elevenlabs.is_available:
            logger.info(
                "  · ElevenLabs detected but disabled by runtime policy; using gTTS/offline only"
            )
        if self.gtts.is_available:
            self.available_providers.append("gtts")
        if self.offline.is_available:
            self.available_providers.append("offline")

        forced = (settings.TTS_PROVIDER or "").lower().strip()
        if forced in self.available_providers:
            # Keep forced provider first so generate() prefers it.
            self.available_providers = [forced] + [
                p for p in self.available_providers if p != forced
            ]
        if forced and forced in self.available_providers:
            self.active_provider: Optional[str] = forced
        elif self.available_providers:
            self.active_provider = self.available_providers[0]
        else:
            self.active_provider = None

        self.cache_enabled: bool = settings.TTS_CACHE_ENABLED
        self.cache_dir: Path = Path(settings.TTS_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._queues: Dict[str, AudioQueueManager] = {}
        self._total_requests: int = 0
        self._cache_hits: int = 0
        self._provider_usage: Dict[str, int] = {}

        if self.active_provider:
            logger.info(
                f"  TTS ready | "
                f"Active: {self.active_provider} | "
                f"Chain: {' → '.join(self.available_providers)}"
                f" | Cache: "
                f"{'ON' if self.cache_enabled else 'OFF'}"
            )
        else:
            logger.warning(
                "  ⚠ No TTS provider available!\n"
                "    pip install gTTS  (recommended FREE)\n"
                "    pip install pyttsx3  (offline fallback)"
            )
        logger.info("=" * 55)

        self.script_generator = get_script_generator()
        self.last_intro_script_source: str = "template"
        self.last_outro_script_source: str = "template"
        logger.info(
            f"  Script AI: "
            f"{'✓ ' + self.script_generator._active_llm if self.script_generator.is_llm_available else '✗ Using templates'}"
        )

    # ═══════════════════ MAIN GENERATE ═══════════════════

    def generate(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "en",
        speech_rate: float = 1.0,
        provider: Optional[str] = None,
        use_cache: bool = True,
        process_ssml: bool = True,
    ) -> Tuple[Optional[bytes], str, bool]:
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return None, "none", False

        self._total_requests += 1

        if process_ssml:
            text = self.ssml.process(text)

        if use_cache and self.cache_enabled:
            cache_key = self._cache_key(text, voice_id, language)
            cached = self._get_cached(cache_key)
            if cached:
                self._cache_hits += 1
                logger.debug(f"Cache HIT: {cache_key[:16]}... ({len(cached):,} bytes)")
                return (
                    cached,
                    self.active_provider or "cache",
                    True,
                )

        if provider and provider in self.available_providers:
            providers_to_try = [provider] + [p for p in self.available_providers if p != provider]
        else:
            providers_to_try = list(self.available_providers)

        for prov in providers_to_try:
            try:
                logger.debug(f"TTS trying: {prov}")
                audio = self._dispatch_generate(
                    prov,
                    text,
                    voice_id,
                    language,
                    speech_rate,
                )

                if audio and len(audio) > 100:
                    self.active_provider = prov
                    self._provider_usage[prov] = self._provider_usage.get(prov, 0) + 1

                    logger.info(f"TTS [{prov}] ✓ {len(text)} chars → {len(audio):,} bytes")

                    if use_cache and self.cache_enabled:
                        self._save_cache(
                            self._cache_key(text, voice_id, language),
                            audio,
                        )

                    return audio, prov, False

                if prov == "elevenlabs":
                    self._demote_elevenlabs()

            except Exception as e:
                logger.warning(f"TTS [{prov}] failed: {e} — trying next")
                if prov == "elevenlabs":
                    self._demote_elevenlabs()
                continue

        logger.error("All TTS providers failed!")
        return None, "none", False

    def _demote_elevenlabs(self) -> None:
        """Disable ElevenLabs for this process when it repeatedly fails."""
        if "elevenlabs" in self.available_providers:
            self.available_providers = [p for p in self.available_providers if p != "elevenlabs"]
            logger.warning(
                "ElevenLabs unavailable in runtime — switching TTS chain to gTTS/offline"
            )

        self.elevenlabs._available = False

        if self.active_provider == "elevenlabs":
            self.active_provider = self.available_providers[0] if self.available_providers else None

    def _dispatch_generate(
        self,
        provider,
        text,
        voice_id,
        language,
        speech_rate,
    ):
        if provider == "elevenlabs":
            return self.elevenlabs.generate(
                text=text,
                voice_id=(voice_id or settings.ELEVENLABS_VOICE_ID),
                speed=speech_rate,
            )
        elif provider == "gtts":
            return self.gtts.generate(
                text=text,
                language=language,
                slow=speech_rate < 0.8,
            )
        elif provider == "offline":
            return self.offline.generate(
                text=text,
                rate=int(175 * speech_rate),
            )
        return None

    # ═══════════════════ STREAMING ═══════════════════

    def generate_stream(
        self,
        text,
        voice_id=None,
    ) -> Generator[bytes, None, None]:
        if self.elevenlabs.is_available:
            try:
                processed = self.ssml.process(text)
                yield from self.elevenlabs.generate_stream(processed, voice_id)
                return
            except Exception as e:
                logger.warning(f"Stream failed: {e}")

        audio, _, _ = self.generate(text, voice_id)
        if audio:
            yield audio

    # ═══════════════════ INTERVIEW AUDIO ═══════════════════

    def generate_interview_intro(
        self,
        candidate_name,
        num_questions,
        duration_minutes=30,
        voice_id=None,
        resume_data=None,
        question_categories=None,
    ) -> Tuple[Optional[bytes], str, str]:
        intro_text, script_source = self.script_generator.generate_intro(
            candidate_name=candidate_name,
            resume_data=resume_data,
            num_questions=num_questions,
            question_categories=question_categories,
            duration_minutes=duration_minutes,
        )
        logger.info(f"Intro via {script_source}: {len(intro_text)} chars")
        audio, provider, cached = self.generate(
            text=intro_text,
            voice_id=voice_id,
            process_ssml=True,
        )
        self.last_intro_script_source = script_source
        return audio, intro_text, script_source

    def generate_interview_outro(
        self,
        candidate_name,
        num_questions,
        score=0,
        voice_id=None,
        resume_data=None,
        grade="Strong",
        category_scores=None,
        strengths=None,
        improvements=None,
    ) -> Tuple[Optional[bytes], str, str]:
        outro_text, script_source = self.script_generator.generate_outro(
            candidate_name=candidate_name,
            resume_data=resume_data,
            num_questions=num_questions,
            num_answered=num_questions,
            overall_score=score,
            grade=grade,
            category_scores=category_scores,
            strengths=strengths,
            improvements=improvements,
        )
        logger.info(f"Outro via {script_source}: {len(outro_text)} chars")
        audio, provider, cached = self.generate(
            text=outro_text,
            voice_id=voice_id,
            process_ssml=True,
        )
        self.last_outro_script_source = script_source
        return audio, outro_text, script_source

    def generate_question_transition(
        self,
        question_number,
        total_questions,
        current_category="T",
        previous_category=None,
        candidate_name=None,
        previous_answer_quality=None,
    ) -> Tuple[Optional[bytes], str, str]:
        transition_text, script_source = self.script_generator.generate_transition(
            question_number=question_number,
            total_questions=total_questions,
            current_category=current_category,
            previous_category=previous_category,
            candidate_name=candidate_name,
            previous_answer_quality=(previous_answer_quality),
        )
        audio, provider, cached = self.generate(
            text=transition_text,
            process_ssml=False,
        )
        return audio, transition_text, script_source

    def generate_question_audio(
        self,
        question_text,
        question_number,
        total_questions,
        include_transition=True,
        voice_id=None,
        question_category="T",
        previous_category=None,
        candidate_name=None,
    ) -> Tuple[Optional[bytes], str]:
        full_text = ""
        if include_transition:
            trans_text, _ = self.script_generator.generate_transition(
                question_number=question_number,
                total_questions=total_questions,
                current_category=question_category,
                previous_category=previous_category,
                candidate_name=candidate_name,
            )
            full_text = f"{trans_text} ... {question_text}"
        else:
            full_text = question_text

        audio, provider, cached = self.generate(
            text=full_text,
            voice_id=voice_id,
            process_ssml=True,
        )
        return audio, full_text

    def generate_encouragement_audio(
        self,
        candidate_name=None,
        context="thinking",
        voice_id=None,
    ) -> Tuple[Optional[bytes], str]:
        text = self.script_generator.generate_encouragement(
            candidate_name=candidate_name,
            context=context,
        )
        audio, provider, cached = self.generate(
            text=text,
            voice_id=voice_id,
            process_ssml=False,
        )
        return audio, text

    def generate_followup_intro_audio(
        self,
        original_question,
        candidate_answer_summary=None,
        voice_id=None,
    ) -> Tuple[Optional[bytes], str]:
        text = self.script_generator.generate_followup_intro(
            original_question=original_question,
            candidate_answer_summary=(candidate_answer_summary),
        )
        audio, provider, cached = self.generate(
            text=text,
            voice_id=voice_id,
            process_ssml=False,
        )
        return audio, text

    def generate_full_interview_audio(
        self,
        candidate_name,
        questions,
        voice_id=None,
        include_intro=True,
        include_outro=True,
        include_transitions=True,
        score=0,
        resume_data=None,
        grade="Strong",
        strengths=None,
        improvements=None,
    ) -> Tuple[List[AudioQueueItem], Dict[str, bytes]]:
        queue: List[AudioQueueItem] = []
        audio_map: Dict[str, bytes] = {}
        item_counter = 0
        categories = [q.get("category", "T") for q in questions]

        if include_intro:
            item_counter += 1
            item_id = f"intro_{item_counter}"
            intro_audio, intro_text, script_src = self.generate_interview_intro(
                candidate_name=candidate_name,
                num_questions=len(questions),
                duration_minutes=max(len(questions) * 2, 10),
                voice_id=voice_id,
                resume_data=resume_data,
                question_categories=categories,
            )
            item = AudioQueueItem(
                id=item_id,
                text=intro_text,
                audio_type="intro",
                duration_estimate_seconds=(len(intro_text) / 15.0),
                audio_size_bytes=(len(intro_audio) if intro_audio else 0),
                status=("ready" if intro_audio else "failed"),
                provider_used=(f"{self.active_provider}+{script_src}"),
            )
            queue.append(item)
            if intro_audio:
                audio_map[item_id] = intro_audio

        prev_category = None
        for i, q in enumerate(questions):
            q_text = q.get(
                "question",
                q.get("question_text", ""),
            )
            q_category = q.get("category", "T")
            if not q_text:
                continue

            item_counter += 1
            item_id = f"q_{item_counter}"
            q_audio, full_text = self.generate_question_audio(
                question_text=q_text,
                question_number=i + 1,
                total_questions=len(questions),
                include_transition=(include_transitions),
                voice_id=voice_id,
                question_category=q_category,
                previous_category=prev_category,
                candidate_name=(candidate_name if i == 0 else None),
            )
            item = AudioQueueItem(
                id=item_id,
                text=full_text,
                audio_type="question",
                question_number=i + 1,
                question_category=q_category,
                duration_estimate_seconds=(len(full_text) / 15.0),
                audio_size_bytes=(len(q_audio) if q_audio else 0),
                status=("ready" if q_audio else "failed"),
                provider_used=self.active_provider,
            )
            queue.append(item)
            if q_audio:
                audio_map[item_id] = q_audio
            prev_category = q_category

        if include_outro:
            item_counter += 1
            item_id = f"outro_{item_counter}"
            outro_audio, outro_text, script_src = self.generate_interview_outro(
                candidate_name=candidate_name,
                num_questions=len(questions),
                score=score,
                voice_id=voice_id,
                resume_data=resume_data,
                grade=grade,
                strengths=strengths,
                improvements=improvements,
            )
            item = AudioQueueItem(
                id=item_id,
                text=outro_text,
                audio_type="outro",
                duration_estimate_seconds=(len(outro_text) / 15.0),
                audio_size_bytes=(len(outro_audio) if outro_audio else 0),
                status=("ready" if outro_audio else "failed"),
                provider_used=(f"{self.active_provider}+{script_src}"),
            )
            queue.append(item)
            if outro_audio:
                audio_map[item_id] = outro_audio

        logger.info(
            f"Full interview audio: "
            f"{len(queue)} segments, "
            f"{sum(len(v) for v in audio_map.values()):,}"
            f" bytes"
        )
        return queue, audio_map

    # ═══════════════════ QUEUE ═══════════════════

    def create_queue(self, session_id):
        queue = AudioQueueManager(session_id)
        self._queues[session_id] = queue
        return queue

    def get_queue(self, session_id):
        return self._queues.get(session_id)

    def delete_queue(self, session_id):
        if session_id in self._queues:
            del self._queues[session_id]

    # ═══════════════════ LANGUAGE ═══════════════════

    def detect_language(self, text):
        return self.lang_detector.get_tts_language(text)

    # ═══════════════════ CACHE ═══════════════════

    def _cache_key(self, text, voice_id, language="en"):
        raw = f"{text}|{voice_id or 'default'}|{language}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _get_cached(self, cache_key):
        path = self.cache_dir / f"{cache_key}.mp3"
        if path.exists():
            try:
                return path.read_bytes()
            except Exception:
                return None
        return None

    def _save_cache(self, cache_key, audio):
        try:
            path = self.cache_dir / f"{cache_key}.mp3"
            path.write_bytes(audio)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    def get_cache_size_mb(self):
        total = sum(f.stat().st_size for f in self.cache_dir.glob("*") if f.is_file())
        return round(total / (1024 * 1024), 2)

    def get_cache_file_count(self):
        return len(list(self.cache_dir.glob("*.mp3")))

    def clear_cache(self):
        count = 0
        for f in self.cache_dir.glob("*.mp3"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
        logger.info(f"Cleared {count} cached files")
        return count

    # ═══════════════════ VOICES ═══════════════════

    def list_voices(self, provider=None):
        voices = []
        if provider is None or provider == "elevenlabs":
            if self.elevenlabs.is_available:
                voices.extend(self.elevenlabs.list_voices())
        if provider is None or provider == "gtts":
            if self.gtts.is_available:
                voices.extend(self.gtts.list_voices())
        if provider is None or provider == "offline":
            if self.offline.is_available:
                voices.extend(self.offline.list_voices())
        return voices

    def get_preset_voices(self):
        return dict(settings.ELEVENLABS_VOICES)

    # ═══════════════════ STATUS ═══════════════════

    def get_config(self):
        return TTSConfigResponse(
            active_provider=self.active_provider,
            available_providers=self.available_providers,
            fallback_order=[p for p in self.PROVIDER_PRIORITY if p in self.available_providers],
            voice_id=settings.ELEVENLABS_VOICE_ID,
            speech_rate=settings.TTS_SPEECH_RATE,
            language=settings.TTS_LANGUAGE,
            cache_enabled=self.cache_enabled,
            cache_dir=str(self.cache_dir),
            cache_size_mb=self.get_cache_size_mb(),
        )

    def get_usage(self):
        return self.elevenlabs.get_usage()

    def get_stats(self):
        return {
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": round(
                self._cache_hits / max(self._total_requests, 1),
                3,
            ),
            "provider_usage": self._provider_usage,
            "active_queues": len(self._queues),
        }


_tts_instance: Optional[TTSService] = None


def get_tts() -> TTSService:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSService()
    return _tts_instance
