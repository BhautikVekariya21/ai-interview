"""
LLM Service — HuggingFace PRIMARY → xAI/Groq/Gemini fallback chain.

Fallback chain:
  1. HuggingFace (DeepSeek-70B → Llama-3-8B → Mistral → Gemma)  ← PRIMARY (FREE)
  2. xAI Grok (if key available)
  3. Groq model pool (free fallback pool)
  4. Gemini models

Notes:
  - Paid-provider code is intentionally preserved.
  - Priority prefers free HuggingFace models first.
"""

import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.core.provider_chain import ProviderChain
from app.services.cache_service import get_cache
from app.services.llm_usage_service import get_usage_tracker

# ── Load .env ──
try:
    from dotenv import load_dotenv

    _env_path = None
    for _candidate in [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
    ]:
        if _candidate.exists():
            _env_path = _candidate
            break
    if _env_path:
        load_dotenv(_env_path, override=False)
        logger.info(f"Loaded .env from: {_env_path}")
    else:
        load_dotenv(override=False)
except ImportError:
    logger.warning("python-dotenv not installed")

# ── Import providers ──
try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai not installed → pip install google-genai")

try:
    from huggingface_hub import InferenceClient

    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("huggingface_hub not installed → pip install huggingface_hub")

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.debug("groq not installed → pip install groq")


class LLMService:
    """
    Multi-provider LLM: HuggingFace → xAI → Groq → Gemini.

    Groq now has a MODEL QUEUE just like HuggingFace:
      deepseek-r1-distill-llama-70b → llama-3.3-70b-versatile
      → llama-3.1-8b-instant → gemma2-9b-it

    If one Groq model hits 429, it tries the next model.
    """

    def __init__(self):
        # ── OpenRouter (priority) ──
        self._openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "").strip() or (
            settings.OPENROUTER_API_KEY or ""
        )
        self._openrouter_base_url: str = (
            os.environ.get("OPENROUTER_BASE_URL", "").strip() or settings.OPENROUTER_BASE_URL
        ).rstrip("/")
        self._openrouter_model_queue: List[str] = list(settings.OPENROUTER_MODEL_QUEUE)

        # ── Claude / Anthropic (priority) ──
        self._claude_api_key: str = os.environ.get("CLAUDE_API_KEY", "").strip() or (
            settings.CLAUDE_API_KEY or ""
        )
        self._claude_model_queue: List[str] = list(settings.CLAUDE_MODEL_QUEUE)

        # ── AIMLAPI (priority) ──
        self._aiml_api_key: str = os.environ.get("AIML_API_KEY", "").strip() or (
            settings.AIML_API_KEY or ""
        )
        self._aiml_base_url: str = (
            os.environ.get("AIML_BASE_URL", "").strip() or settings.AIML_BASE_URL
        ).rstrip("/")
        self._aiml_model_queue: List[str] = list(settings.AIML_MODEL_QUEUE)

        # ── Mistral (priority) ──
        self._mistral_api_key: str = os.environ.get("MISTRAL_API_KEY", "").strip() or (
            settings.MISTRAL_API_KEY or ""
        )
        self._mistral_base_url: str = (
            os.environ.get("MISTRAL_BASE_URL", "").strip() or settings.MISTRAL_BASE_URL
        ).rstrip("/")
        self._mistral_model_queue: List[str] = list(settings.MISTRAL_MODEL_QUEUE)

        # ── Gemini ──
        self._gemini_api_key: str = (
            os.environ.get("GEMINI_API_KEY", "").strip() or settings.GEMINI_API_KEY
        )
        self._gemini_model_queue: List[str] = list(settings.GEMINI_MODEL_QUEUE)
        self._gemini_models: Dict[str, Any] = {}
        self._gemini_configured: bool = False
        self._gemini_client: Any = None

        # ── xAI Grok (fallback) ──
        self._xai_api_key: str = os.environ.get("XAI_API_KEY", "").strip() or (
            settings.XAI_API_KEY or ""
        )
        self._xai_base_url: str = (
            os.environ.get("XAI_BASE_URL", "").strip() or settings.XAI_BASE_URL
        ).rstrip("/")
        self._xai_model_queue: List[str] = list(settings.XAI_MODEL_QUEUE)

        # ── Groq (now with MODEL QUEUE) ──
        self._groq_api_key: str = os.environ.get("GROQ_API_KEY", "").strip() or (
            settings.GROQ_API_KEY or ""
        )
        self._groq_client: Optional[Groq] = None
        self._groq_model_queue: List[str] = list(settings.GROQ_MODEL_QUEUE)

        # ── HuggingFace ──
        self._hf_api_key: str = (
            os.environ.get("HUGGINGFACE_API_KEY", "").strip() or settings.HUGGINGFACE_API_KEY
        )
        self._hf_model_queue: List[str] = list(settings.HF_MODEL_QUEUE)
        self._hf_clients: Dict[str, InferenceClient] = {}

        # ── State ──
        self.active_provider: Optional[str] = None
        self.available_providers: List[str] = []
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self._last_success_key: Optional[str] = None
        self._cache = get_cache()

        self._initialize_all()

    # ═══════════════════ INITIALIZATION ═══════════════════

    def _initialize_all(self):
        """Initialize providers in priority order."""
        # Priority 1: User-configured third-party keys
        self._init_openrouter()
        self._init_claude()
        self._init_aiml()
        self._init_mistral()
        # Priority 2: Groq
        self._init_groq()
        # Priority 3: xAI Grok
        self._init_xai()
        # Priority 4: Gemini
        self._init_gemini()
        # HuggingFace intentionally disabled by default because
        # unsupported/provider-gated models were adding large latency.
        if os.environ.get("ENABLE_HUGGINGFACE_FALLBACK", "false").lower() in {"1", "true", "yes"}:
            self._init_huggingface()

        if self.available_providers:
            self.active_provider = self.available_providers[0]
            logger.info(
                f"LLM Service ready | "
                f"Active: {self.active_provider} | "
                f"Chain: {' → '.join(self.available_providers)}"
            )
        else:
            logger.error(
                "╔═══════════════════════════════════════════╗\n"
                "║  NO LLM PROVIDERS AVAILABLE!             ║\n"
                "║  Add to .env (at least one):             ║\n"
                "║    GEMINI_API_KEY=AIza...  (recommended) ║\n"
                "║    GROQ_API_KEY=gsk_...    (best free)   ║\n"
                "║    HUGGINGFACE_API_KEY=hf_...            ║\n"
                "╚═══════════════════════════════════════════╝"
            )

    def _init_openrouter(self):
        if not self._openrouter_api_key:
            logger.debug("OPENROUTER_API_KEY not set")
            return
        for model_id in self._openrouter_model_queue:
            key = f"openrouter:{model_id}"
            self._failure_counts[key] = 0
            self._last_failure_time[key] = 0.0
            self.available_providers.append(key)
            logger.info(f"  ✓ OpenRouter: {model_id} — PRIMARY")

    def _init_claude(self):
        if not self._claude_api_key:
            logger.debug("CLAUDE_API_KEY not set")
            return
        for model_id in self._claude_model_queue:
            key = f"claude:{model_id}"
            self._failure_counts[key] = 0
            self._last_failure_time[key] = 0.0
            self.available_providers.append(key)
            logger.info(f"  ✓ Claude: {model_id} — PRIMARY")

    def _init_aiml(self):
        if not self._aiml_api_key:
            logger.debug("AIML_API_KEY not set")
            return
        for model_id in self._aiml_model_queue:
            key = f"aiml:{model_id}"
            self._failure_counts[key] = 0
            self._last_failure_time[key] = 0.0
            self.available_providers.append(key)
            logger.info(f"  ✓ AIMLAPI: {model_id} — PRIMARY")

    def _init_mistral(self):
        if not self._mistral_api_key:
            logger.debug("MISTRAL_API_KEY not set")
            return
        for model_id in self._mistral_model_queue:
            key = f"mistral:{model_id}"
            self._failure_counts[key] = 0
            self._last_failure_time[key] = 0.0
            self.available_providers.append(key)
            logger.info(f"  ✓ Mistral: {model_id} — PRIMARY")

    def _init_xai(self):
        """Initialize xAI Grok model queue."""
        if not self._xai_api_key:
            logger.debug("XAI_API_KEY not set")
            return

        for model_id in self._xai_model_queue:
            key = f"xai:{model_id}"
            self._failure_counts[key] = 0
            self._last_failure_time[key] = 0.0
            self.available_providers.append(key)
            logger.info(f"  ✓ xAI: {model_id} — PRIMARY")

    def _init_gemini(self):
        """Initialize Google Gemini (google-genai SDK)."""
        if not GEMINI_AVAILABLE or not self._gemini_api_key:
            if not GEMINI_AVAILABLE:
                logger.warning("google-genai not installed")
            else:
                logger.warning("GEMINI_API_KEY not set")
            return

        try:
            self._gemini_client = google_genai.Client(api_key=self._gemini_api_key)
            self._gemini_configured = True
            logger.info("  ✓ Gemini API key configured")
        except Exception as e:
            logger.warning(f"  ✗ Gemini configure: {e}")
            return

        # The new SDK resolves models per request — register each queued
        # model so the family/queue availability checks keep working.
        for model_id in self._gemini_model_queue:
            self._gemini_models[model_id] = model_id
            key = f"gemini:{model_id}"
            self._failure_counts[key] = 0
            self._last_failure_time[key] = 0.0
            self.available_providers.append(key)
            logger.info(f"  ✓ Gemini: {model_id} — PRIMARY")

    def _init_groq(self):
        """
        Initialize Groq with MULTIPLE models.
        Each model gets its own circuit breaker.
        """
        if not GROQ_AVAILABLE or not self._groq_api_key:
            if not GROQ_AVAILABLE:
                logger.debug("groq library not installed")
            else:
                logger.debug("GROQ_API_KEY not set")
            return

        try:
            self._groq_client = Groq(api_key=self._groq_api_key)
            logger.info("  ✓ Groq client initialized")
        except Exception as e:
            logger.warning(f"  ✗ Groq init: {e}")
            return

        # Register each Groq model as a separate provider
        for model_id in self._groq_model_queue:
            key = f"groq:{model_id}"
            self._failure_counts[key] = 0
            self._last_failure_time[key] = 0.0
            self.available_providers.append(key)
            logger.info(f"  ✓ Groq: {model_id} — SECONDARY (FREE)")

    def _init_huggingface(self):
        """Initialize HuggingFace (last resort)."""
        if not HF_AVAILABLE or not self._hf_api_key:
            if not HF_AVAILABLE:
                logger.warning("huggingface_hub not installed")
            else:
                logger.warning("HUGGINGFACE_API_KEY not set")
            return

        for model_id in self._hf_model_queue:
            try:
                client = InferenceClient(
                    model=model_id,
                    token=self._hf_api_key,
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                )
                self._hf_clients[model_id] = client
                key = f"hf:{model_id}"
                self._failure_counts[key] = 0
                self._last_failure_time[key] = 0.0
                self.available_providers.append(key)
                logger.info(f"  ✓ HuggingFace: {model_id} — LAST RESORT")
            except Exception as e:
                logger.warning(f"  ✗ HuggingFace {model_id}: {e}")

    # ═══════════════════ CIRCUIT BREAKER ═══════════════════

    def _is_healthy(self, key: str) -> bool:
        failures = self._failure_counts.get(key, 0)
        if failures < settings.LLM_MAX_FAILURES_BEFORE_SKIP:
            return True
        elapsed = time.time() - self._last_failure_time.get(key, 0)
        if elapsed > settings.LLM_FAILURE_COOLDOWN_SECONDS:
            self._failure_counts[key] = 0
            logger.info(f"Circuit breaker RESET: {key}")
            return True
        return False

    def _record_failure(self, key: str, error: str):
        self._failure_counts[key] = self._failure_counts.get(key, 0) + 1
        self._last_failure_time[key] = time.time()
        logger.warning(f"FAIL #{self._failure_counts[key]} — {key}: {error[:200]}")

    def _record_success(self, key: str):
        self._failure_counts[key] = 0
        # Remember which provider:model answered so usage tracking can attribute it.
        self._last_success_key = key

    # ═══════════════════ PROVIDER ORDERING (shared ProviderChain) ═══════════════════

    def _hf_enabled(self) -> bool:
        return os.environ.get("ENABLE_HUGGINGFACE_FALLBACK", "false").lower() in {
            "1",
            "true",
            "yes",
        }

    def _available_families(self) -> List[str]:
        """Provider families with at least one usable path this process."""
        families: List[str] = []
        if self._openrouter_api_key:
            families.append("openrouter")
        if self._groq_client:
            families.append("groq")
        if self._claude_api_key:
            families.append("claude")
        if self._aiml_api_key:
            families.append("aiml")
        if self._mistral_api_key:
            families.append("mistral")
        if self._xai_api_key:
            families.append("xai")
        if getattr(self, "_gemini_models", None):
            families.append("gemini")
        if self._hf_enabled() and getattr(self, "_hf_clients", None):
            families.append("huggingface")
        return families

    def _get_family_order(self, preferred: Optional[str] = None) -> List[str]:
        """
        Fallback family order via the shared ProviderChain.

        Family names are case-sensitive (they key the model-queue maps), so
        normalize_case=False — matching ASR's adoption.
        """
        chain = ProviderChain(
            priority=settings.LLM_PROVIDER_PRIORITY,
            available=self._available_families(),
            forced=settings.LLM_PROVIDER,
            normalize_case=False,
        )
        return chain.order_for(preferred)

    def _run_family(
        self,
        family: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """
        Run one provider family's model queue with per-model circuit breaking.
        Sets active_provider on success; returns the generated text or None.
        Preserves the exact per-family dispatch of the old phase blocks.
        """
        if family == "openrouter":
            queue, guard = self._openrouter_model_queue, bool(self._openrouter_api_key)
        elif family == "groq":
            queue, guard = self._groq_model_queue, self._groq_client is not None
        elif family == "claude":
            queue, guard = self._claude_model_queue, bool(self._claude_api_key)
        elif family == "aiml":
            queue, guard = self._aiml_model_queue, bool(self._aiml_api_key)
        elif family == "mistral":
            queue, guard = self._mistral_model_queue, bool(self._mistral_api_key)
        elif family == "xai":
            queue, guard = self._xai_model_queue, bool(self._xai_api_key)
        elif family == "gemini":
            queue, guard = self._gemini_model_queue, True
        elif family == "huggingface":
            queue, guard = self._hf_model_queue, self._hf_enabled()
        else:
            return None

        if not guard:
            return None

        # Circuit-breaker / active_provider key prefix. Matches the family name
        # except HuggingFace, whose keys are prefixed "hf" (see _init_huggingface).
        key_prefix = "hf" if family == "huggingface" else family

        for model_id in queue:
            # Per-model runtime availability for object-backed families.
            if family == "gemini" and model_id not in getattr(self, "_gemini_models", {}):
                continue
            if family == "huggingface" and model_id not in getattr(self, "_hf_clients", {}):
                continue

            key = f"{key_prefix}:{model_id}"
            if not self._is_healthy(key):
                logger.debug(f"SKIP (circuit open): {key}")
                continue

            result = self._dispatch_model(
                family, model_id, system_prompt, user_prompt, temperature, max_tokens
            )
            if result:
                self.active_provider = key
                return result
        return None

    def _dispatch_model(
        self,
        family: str,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """Route one (family, model) call to the concrete _try_* function."""
        if family in ("openrouter", "aiml", "mistral"):
            base_url = {
                "openrouter": self._openrouter_base_url,
                "aiml": self._aiml_base_url,
                "mistral": self._mistral_base_url,
            }[family]
            api_key = {
                "openrouter": self._openrouter_api_key,
                "aiml": self._aiml_api_key,
                "mistral": self._mistral_api_key,
            }[family]
            return self._try_openai_compatible_model(
                provider=family,
                base_url=base_url,
                api_key=api_key,
                model_id=model_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        if family == "groq":
            return self._try_groq_model(
                model_id, system_prompt, user_prompt, temperature, max_tokens
            )
        if family == "claude":
            return self._try_claude_model(
                model_id=model_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        if family == "xai":
            return self._try_xai_model(
                model_id, system_prompt, user_prompt, temperature, max_tokens
            )
        if family == "gemini":
            return self._try_gemini(
                model_id, system_prompt, user_prompt, temperature, max_tokens
            )
        if family == "huggingface":
            return self._try_huggingface(
                model_id, system_prompt, user_prompt, temperature, max_tokens
            )
        return None

    # ═══════════════════ CORE GENERATE ═══════════════════

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """Generate text with priority chain: OpenRouter/Claude/AIML/Mistral → Groq → xAI → Gemini → HF."""
        if not self.available_providers:
            logger.error("No providers available")
            return None

        sys_prompt = system_prompt or (
            "You are an expert technical interviewer. Be specific, deep, and professional."
        )

        if temperature is None:
            temperature = random.uniform(
                settings.LLM_TEMPERATURE_MIN,
                settings.LLM_TEMPERATURE_MAX,
            )

        max_tokens = max_tokens or settings.LLM_MAX_TOKENS

        cache_payload = json.dumps(
            {
                "prompt": prompt,
                "system_prompt": sys_prompt,
                "temperature": round(float(temperature), 3),
                "max_tokens": int(max_tokens),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        cache_key = self._cache.make_key("llm:text", cache_payload)
        tracker = get_usage_tracker()
        started = time.perf_counter()

        cached = self._cache.get(cache_key)
        if isinstance(cached, str) and len(cached) > 30:
            logger.info("LLM cache HIT")
            tracker.record(
                provider="cache",
                model="cache",
                prompt_text=sys_prompt + prompt,
                completion_text=cached,
                latency_ms=int((time.perf_counter() - started) * 1000),
                cache_hit=True,
            )
            return cached

        # ── Ordered fallback across provider families (shared ProviderChain) ──
        for family in self._get_family_order():
            self._last_success_key = None
            result = self._run_family(
                family, sys_prompt, prompt, temperature, max_tokens
            )
            if result:
                self._cache.set(cache_key, result, ttl_seconds=1800)
                key = self._last_success_key or f"{family}:unknown"
                provider, _, model = key.partition(":")
                tracker.record(
                    provider=provider or family,
                    model=model or "unknown",
                    prompt_text=sys_prompt + prompt,
                    completion_text=result,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
                return result

        logger.error("ALL PROVIDERS FAILED — every configured family exhausted")
        return None

    def generate_structured(
        self,
        prompt: str,
        schema: Any,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        retries: int = 1,
    ) -> Optional[Any]:
        """Generate JSON and validate it against a Pydantic model.

        On validation failure the error is fed back to the model once so it can
        repair its own output — this removes most "almost right" responses that
        previously fell through as ``None``. Returns a model instance or ``None``.
        """
        try:
            schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        except Exception:
            schema_json = ""

        schema_hint = (
            f"\n\nThe JSON MUST conform to this JSON Schema:\n{schema_json}" if schema_json else ""
        )
        attempt_prompt = prompt + schema_hint
        last_error = ""
        for attempt in range(retries + 1):
            raw = self.generate_json(attempt_prompt, system_prompt=system_prompt, max_tokens=max_tokens)
            if raw is None:
                return None
            try:
                return schema.model_validate(raw)
            except Exception as exc:  # pydantic.ValidationError
                last_error = str(exc)[:800]
                logger.warning(f"structured output failed validation (attempt {attempt + 1}): {last_error[:200]}")
                attempt_prompt = (
                    prompt
                    + schema_hint
                    + "\n\nYour previous answer was:\n"
                    + json.dumps(raw, ensure_ascii=False)[:4000]
                    + "\n\nIt failed validation with:\n"
                    + last_error
                    + "\n\nFix the JSON so it validates. Return ONLY the corrected JSON."
                )
        return None

    def _try_openai_compatible_model(
        self,
        provider: str,
        base_url: str,
        api_key: str,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        key = f"{provider}:{model_id}"
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://localhost"
            headers["X-Title"] = "ai-interview"

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": min(max_tokens, 4096),
            "top_p": settings.LLM_TOP_P,
        }

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"{provider.upper()} → {model_id} (attempt {attempt + 1}/{settings.LLM_MAX_RETRIES + 1})"
                )
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as resp:
                    text = resp.read().decode("utf-8", errors="ignore")
                data = json.loads(text)
                out = str(
                    (((data.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
                ).strip()
                if len(out) > 30:
                    self._record_success(key)
                    logger.info(f"  ✓ {provider} {model_id} → {len(out)} chars")
                    return out
            except Exception as e:
                err = str(e)
                logger.warning(f"  ✗ {provider} {model_id} attempt {attempt + 1}: {err[:150]}")
                if attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 1))
        self._record_failure(key, "retries exhausted")
        return None

    def _try_claude_model(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        key = f"claude:{model_id}"
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self._claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model_id,
            "max_tokens": min(max_tokens, 4096),
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"CLAUDE → {model_id} (attempt {attempt + 1}/{settings.LLM_MAX_RETRIES + 1})"
                )
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as resp:
                    text = resp.read().decode("utf-8", errors="ignore")
                data = json.loads(text)
                chunks = data.get("content") or []
                out = "\n".join(
                    str(c.get("text", "")) for c in chunks if c.get("type") == "text"
                ).strip()
                if len(out) > 30:
                    self._record_success(key)
                    logger.info(f"  ✓ Claude {model_id} → {len(out)} chars")
                    return out
            except Exception as e:
                err = str(e)
                logger.warning(f"  ✗ Claude {model_id} attempt {attempt + 1}: {err[:150]}")
                if attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 1))
        self._record_failure(key, "retries exhausted")
        return None

    def _try_xai_model(
        self,
        model_id,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ) -> Optional[str]:
        """Try a single xAI Grok model via REST API."""
        key = f"xai:{model_id}"
        url = f"{self._xai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._xai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": min(max_tokens, 8000),
            "top_p": settings.LLM_TOP_P,
        }

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"XAI → {model_id} (attempt {attempt + 1}/{settings.LLM_MAX_RETRIES + 1})"
                )
                req = urllib.request.Request(
                    url=url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_SECONDS) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
                parsed = json.loads(raw)
                text = parsed.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if len(text) > 30:
                    self._record_success(key)
                    logger.info(f"  ✓ xAI {model_id} → {len(text)} chars")
                    return text
                logger.warning(f"  Empty/short from xAI {model_id}")
            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                err = f"HTTP {e.code}: {err_body[:200]}"
                logger.warning(f"  ✗ xAI {model_id} attempt {attempt + 1}: {err}")
                if e.code in (400, 404):
                    break
                if e.code == 429:
                    wait = settings.LLM_RETRY_DELAY_SECONDS * (attempt + 2)
                    time.sleep(wait)
                    break
                if attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 1))
            except Exception as e:
                err = str(e)
                logger.warning(f"  ✗ xAI {model_id} attempt {attempt + 1}: {err[:150]}")
                if attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 1))

        self._record_failure(key, "retries exhausted")
        return None

    # ═══════════════════ GEMINI ═══════════════════

    def _try_gemini(
        self,
        model_id,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ) -> Optional[str]:
        """Try a single Gemini model."""
        key = f"gemini:{model_id}"

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"GEMINI → {model_id} (attempt {attempt + 1}/{settings.LLM_MAX_RETRIES + 1})"
                )

                configured_model = self._gemini_client.models
                response = configured_model.generate_content(
                    model=model_id,
                    contents=user_prompt,
                    config=google_genai_types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        top_p=settings.LLM_TOP_P,
                        max_output_tokens=max_tokens,
                    ),
                )

                text = None
                try:
                    text = response.text
                except (ValueError, AttributeError):
                    pass

                if not text:
                    try:
                        if (
                            response.candidates
                            and response.candidates[0].content
                            and response.candidates[0].content.parts
                        ):
                            text = "".join(
                                part.text
                                for part in response.candidates[0].content.parts
                                if hasattr(part, "text")
                            )
                    except (
                        IndexError,
                        AttributeError,
                        TypeError,
                    ):
                        pass

                if text and isinstance(text, str) and len(text.strip()) > 30:
                    self._record_success(key)
                    logger.info(f"  ✓ Gemini {model_id} → {len(text)} chars")
                    return text.strip()

                logger.warning(f"  Empty/short from Gemini {model_id}")

            except Exception as e:
                err = str(e)
                logger.warning(f"  ✗ Gemini {model_id} attempt {attempt + 1}: {err[:200]}")
                err_lower = err.lower()

                # 404 → model doesn't exist, skip immediately
                if "404" in err or "not found" in err_lower:
                    logger.warning(f"  ⛔ {model_id} not available — skipping")
                    break

                # Rate limit → wait and retry
                if any(
                    kw in err_lower
                    for kw in [
                        "429",
                        "rate",
                        "quota",
                        "resource_exhausted",
                    ]
                ):
                    wait = settings.LLM_RETRY_DELAY_SECONDS * (attempt + 3)
                    logger.info(f"  Rate limited → waiting {wait:.1f}s")
                    time.sleep(wait)
                elif attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 1))

        self._record_failure(key, "retries exhausted")
        return None

    # ═══════════════════ GROQ (MULTI-MODEL) ═══════════════════

    def _try_groq_model(
        self,
        model_id,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ) -> Optional[str]:
        """
        Try a SINGLE Groq model with retries.
        Called once per model in the queue.
        """
        if not self._groq_client:
            return None

        key = f"groq:{model_id}"
        failure_reason = "retries exhausted"

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"GROQ → {model_id} (attempt {attempt + 1}/{settings.LLM_MAX_RETRIES + 1})"
                )

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ]

                response = self._groq_client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=min(max_tokens, 8000),
                    top_p=settings.LLM_TOP_P,
                )

                if response.choices:
                    text = (response.choices[0].message.content or "").strip()
                    if len(text) > 30:
                        self._record_success(key)
                        logger.info(f"  ✓ Groq {model_id} → {len(text)} chars")
                        return text

                logger.warning(f"  Empty from Groq {model_id}")

            except Exception as e:
                err = str(e)
                logger.warning(f"  ✗ Groq {model_id} attempt {attempt + 1}: {err[:150]}")
                err_lower = err.lower()

                # Model not found → skip immediately
                if any(
                    kw in err_lower
                    for kw in [
                        "not found",
                        "does not exist",
                        "404",
                        "invalid model",
                        "decommissioned",
                        "no longer supported",
                        "unsupported model",
                        "not supported",
                    ]
                ):
                    failure_reason = "model unavailable"
                    logger.warning(f"  ⛔ Groq {model_id} not available — trying next model")
                    break

                # Rate limit → wait then retry
                if any(kw in err_lower for kw in ["429", "rate", "limit"]):
                    failure_reason = "rate limited"
                    wait = settings.LLM_RETRY_DELAY_SECONDS * (attempt + 2)
                    logger.info(f"  Rate limited → waiting {wait:.1f}s, then trying next model")
                    time.sleep(wait)
                    # On 429, break to try next model
                    # instead of retrying same model
                    break

                # Other errors → retry
                elif attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 1))

        self._record_failure(key, failure_reason)
        return None

    # ═══════════════════ HUGGINGFACE ═══════════════════

    def _try_huggingface(
        self,
        model_id,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ) -> Optional[str]:
        """Try HuggingFace — chat API first, text gen fallback."""
        key = f"hf:{model_id}"
        client = self._hf_clients[model_id]

        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"HF → {model_id} (attempt {attempt + 1}/{settings.LLM_MAX_RETRIES + 1})"
                )

                # Try chat completion first
                text = self._hf_chat(
                    client,
                    system_prompt,
                    user_prompt,
                    temperature,
                    max_tokens,
                )

                # Fallback to text generation
                if not text:
                    text = self._hf_text_gen(
                        client,
                        system_prompt,
                        user_prompt,
                        temperature,
                        max_tokens,
                    )

                if text and isinstance(text, str) and len(text.strip()) > 30:
                    self._record_success(key)
                    logger.info(f"  ✓ {model_id} → {len(text)} chars")
                    return text.strip()

                logger.warning(f"  Empty/short from {model_id}")

            except Exception as e:
                err = str(e)
                logger.warning(f"  ✗ {model_id} attempt {attempt + 1}: {err[:150]}")
                err_lower = err.lower()

                if any(
                    kw in err_lower
                    for kw in [
                        "not found",
                        "not supported",
                        "404",
                    ]
                ):
                    logger.warning(f"  ⛔ {model_id} not available")
                    break

                if "rate" in err_lower or "429" in err:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 3))
                elif attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY_SECONDS * (attempt + 1))

        self._record_failure(key, "retries exhausted")
        return None

    def _hf_chat(
        self,
        client,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ) -> Optional[str]:
        """Try HuggingFace chat_completion API."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ]
            response = client.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=settings.LLM_TOP_P,
            )
            if response and response.choices and response.choices[0].message:
                text = response.choices[0].message.content or ""
                if len(text.strip()) > 30:
                    return text.strip()
        except Exception as e:
            logger.debug(f"  chat_completion failed: {str(e)[:100]}")
        return None

    def _hf_text_gen(
        self,
        client,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens,
    ) -> Optional[str]:
        """Try HuggingFace text_generation API."""
        try:
            formatted = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant: "
            response = client.text_generation(
                prompt=formatted,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=settings.LLM_TOP_P,
                repetition_penalty=(settings.LLM_REPETITION_PENALTY),
                do_sample=True,
                return_full_text=False,
            )
            if response and isinstance(response, str) and len(response.strip()) > 30:
                return response.strip()
        except Exception as e:
            logger.debug(f"  text_generation failed: {str(e)[:100]}")
        return None

    # ═══════════════════ JSON GENERATION ═══════════════════

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[Any]:
        """Generate + parse JSON from LLM."""
        json_inst = (
            "\n\nCRITICAL: Return ONLY valid JSON. "
            "No markdown fences. No explanation. "
            "Start with [ or { directly."
        )

        raw = self.generate(
            prompt=prompt + json_inst,
            system_prompt=system_prompt,
            temperature=random.uniform(0.3, 0.5),
            max_tokens=max_tokens,
        )

        if not raw:
            return None

        parsed = self._extract_json(raw)
        if parsed is not None:
            return parsed

        logger.warning(f"JSON extraction failed from {len(raw)} chars. Preview: {raw[:300]}...")
        return None

    def _extract_json(self, text: str) -> Optional[Any]:
        """Robust JSON extraction — 4 strategies."""
        if not text:
            return None
        text = text.strip()

        # Strategy 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Markdown fences
        for pattern in [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
        ]:
            match = re.search(pattern, text)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    repaired = self._repair_json(match.group(1).strip())
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        pass

        # Strategy 3: Bracket matching
        for open_c, close_c in [("[", "]"), ("{", "}")]:
            start = text.find(open_c)
            if start == -1:
                continue

            depth = 0
            in_string = False
            escape_next = False

            for i in range(start, len(text)):
                ch = text[i]
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\":
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == open_c:
                    depth += 1
                elif ch == close_c:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            try:
                                return json.loads(self._repair_json(candidate))
                            except json.JSONDecodeError:
                                pass
                        break

        # Strategy 4: Line-by-line extraction
        lines = text.strip().split("\n")
        questions = []
        for line in lines:
            line = line.strip()
            line = re.sub(r"^[\d]+[.):\-]\s*", "", line)
            line = re.sub(r"^[-*•►▸➤]\s*", "", line)
            line = line.strip("\" '")
            if len(line) > 20 and "?" in line:
                questions.append(line)

        if len(questions) >= 3:
            logger.info(f"Extracted {len(questions)} questions via line-by-line")
            return questions

        return None

    def _repair_json(self, text: str) -> str:
        """Fix common LLM JSON issues."""
        text = re.sub(r",\s*([}\]])", r"\1", text)
        text = re.sub(
            r"(?<![\\])'((?:[^'\\]|\\.)*)'",
            r'"\1"',
            text,
        )
        text = re.sub(
            r"(?<=\{|,)\s*(\w+)\s*:",
            r' "\1":',
            text,
        )
        text = re.sub(
            r'(?<=": ")([^"]*)\n([^"]*")',
            r"\1 \2",
            text,
        )
        return text

    # ═══════════════════ CONVENIENCE METHODS ═══════════════════

    def generate_follow_up(
        self,
        question,
        answer,
        resume_context="",
    ) -> Optional[str]:
        """Generate a single follow-up question."""
        system_prompt = (
            "You are a senior technical interviewer. "
            "Generate exactly ONE follow-up question. "
            "Return ONLY the question text."
        )
        user_prompt = f"ORIGINAL QUESTION:\n{question}\n\nCANDIDATE'S ANSWER:\n{answer}\n\n"
        if resume_context:
            user_prompt += f"RESUME CONTEXT:\n{resume_context}\n\n"
        user_prompt += "Generate ONE follow-up question:"

        result = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=300,
        )

        if result:
            result = result.strip().split("\n")[0].strip()
            result = re.sub(r"^[\d]+[.)]\s*", "", result).strip().strip("\"'")
            if len(result) > 15:
                return result

        return None

    def evaluate_answer(
        self,
        question,
        answer,
        expected_topics=None,
    ) -> Optional[Dict]:
        """Evaluate a candidate's answer."""
        topics_str = ""
        if expected_topics:
            topics_str = f"\nExpected topics: {', '.join(expected_topics)}"

        prompt = (
            f"QUESTION:\n{question}\n\n"
            f"CANDIDATE'S ANSWER:\n{answer}\n"
            f"{topics_str}\n\n"
            "Evaluate and return JSON:\n"
            '{"score": <0-100>, '
            '"grade": "<Exceptional|Strong|Adequate|'
            'Needs Work|Insufficient>", '
            '"strengths": ["point1", "point2"], '
            '"improvements": ["point1", "point2"], '
            '"feedback": "3-4 sentence paragraph", '
            '"follow_up_question": "one follow-up"}'
        )

        return self.generate_json(prompt=prompt)

    # ═══════════════════ PROPERTIES ═══════════════════

    @property
    def is_available(self) -> bool:
        return len(self.available_providers) > 0

    def get_status(self) -> Dict:
        """Internal status. NEVER expose API keys."""
        active_model = None
        if self.active_provider:
            provider_queues = {
                "openrouter": self._openrouter_model_queue,
                "claude": self._claude_model_queue,
                "aiml": self._aiml_model_queue,
                "mistral": self._mistral_model_queue,
                "xai": self._xai_model_queue,
                "gemini": self._gemini_model_queue,
                "groq": self._groq_model_queue,
                "huggingface": self._hf_model_queue,
            }
            queue = provider_queues.get(self.active_provider, [])
            active_model = queue[0] if queue else None
        return {
            "available": self.is_available,
            "active_provider": self.active_provider,
            "active_model": active_model,
            "provider_count": len(self.available_providers),
            "fallback_order": list(self.available_providers),
            "providers_status": {
                key: {
                    "healthy": self._is_healthy(key),
                    "failures": self._failure_counts.get(key, 0),
                }
                for key in self.available_providers
            },
            "providers": {
                key: {
                    "healthy": self._is_healthy(key),
                    "failures": self._failure_counts.get(key, 0),
                }
                for key in self.available_providers
            },
        }


# ═══════════════════ SINGLETON ═══════════════════

_llm_instance: Optional[LLMService] = None


def get_llm() -> LLMService:
    """Get or create the singleton LLM service."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMService()
    return _llm_instance


def reset_llm() -> LLMService:
    """Force re-initialization."""
    global _llm_instance
    _llm_instance = None
    return get_llm()
