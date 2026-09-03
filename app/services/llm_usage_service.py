"""LLM usage, latency, and cost tracking.

Every ``LLMService.generate`` call records one row (provider, model, tokens,
latency, cache hit, estimated USD). Token counts are estimated when providers
don't return them (chars / 4). Cost uses a small per-model price table; unknown
models fall back to a family default so totals are never silently zero.

Writes are buffered in memory and flushed to the ``llm_usage`` table in a
background thread so tracking never adds latency to the request path.
"""

from __future__ import annotations

import contextvars
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from loguru import logger

# USD per 1M tokens (input, output). Approximate public list prices.
_PRICES: Dict[str, tuple[float, float]] = {
    # OpenRouter / OpenAI-compatible
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4.1-mini": (0.40, 1.60),
    "anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "meta-llama/llama-3.3-70b-instruct": (0.12, 0.30),
    "deepseek/deepseek-chat": (0.14, 0.28),
    # Claude direct
    "claude-3-5-haiku-latest": (0.80, 4.00),
    "claude-3-5-sonnet-latest": (3.00, 15.00),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    # Groq (free tier → approximate paid pricing)
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "llama-3.1-8b-instant": (0.05, 0.08),
    "gemma2-9b-it": (0.20, 0.20),
    "deepseek-r1-distill-llama-70b": (0.75, 0.99),
    # Gemini
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    # xAI
    "grok-2-latest": (2.00, 10.00),
    "grok-beta": (5.00, 15.00),
}

_FAMILY_DEFAULTS: Dict[str, tuple[float, float]] = {
    "openrouter": (0.50, 1.50),
    "claude": (3.00, 15.00),
    "aiml": (0.50, 1.50),
    "mistral": (0.25, 0.75),
    "groq": (0.20, 0.40),
    "xai": (2.00, 10.00),
    "gemini": (0.10, 0.40),
    "huggingface": (0.00, 0.00),
    "cache": (0.00, 0.00),
}

# Per-request feature tag, set by routes so usage can be grouped by product area.
current_feature: contextvars.ContextVar[str] = contextvars.ContextVar("llm_feature", default="general")
current_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("llm_user_id", default=None)


def estimate_tokens(text: Optional[str]) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price_in, price_out = _PRICES.get(model) or _FAMILY_DEFAULTS.get(provider, (0.0, 0.0))
    return round((prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000, 6)


@dataclass
class UsageRecord:
    id: str
    user_id: Optional[str]
    feature: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cache_hit: bool
    cost_usd: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LLMUsageTracker:
    """Thread-safe in-memory ring buffer + async DB flush."""

    def __init__(self, max_memory: int = 2000, flush_interval: float = 5.0):
        self._buffer: Deque[UsageRecord] = deque(maxlen=max_memory)
        self._pending: List[UsageRecord] = []
        self._lock = threading.Lock()
        self._flush_interval = flush_interval
        self._flusher: Optional[threading.Thread] = None
        self._stop = threading.Event()
        # running totals (process lifetime)
        self.totals: Dict[str, Any] = {
            "calls": 0,
            "cache_hits": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms_sum": 0,
            "by_provider": {},
            "by_feature": {},
        }

    # ── recording ──────────────────────────────────────────────────────────

    def record(
        self,
        *,
        provider: str,
        model: str,
        prompt_text: str,
        completion_text: str,
        latency_ms: int,
        cache_hit: bool = False,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> UsageRecord:
        p_tok = prompt_tokens if prompt_tokens is not None else estimate_tokens(prompt_text)
        c_tok = completion_tokens if completion_tokens is not None else estimate_tokens(completion_text)
        cost = 0.0 if cache_hit else estimate_cost(provider, model, p_tok, c_tok)
        rec = UsageRecord(
            id=str(uuid.uuid4()),
            user_id=current_user_id.get(),
            feature=current_feature.get(),
            provider=provider,
            model=model,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            latency_ms=int(latency_ms),
            cache_hit=cache_hit,
            cost_usd=cost,
        )
        with self._lock:
            self._buffer.append(rec)
            self._pending.append(rec)
            t = self.totals
            t["calls"] += 1
            t["cache_hits"] += int(cache_hit)
            t["prompt_tokens"] += p_tok
            t["completion_tokens"] += c_tok
            t["cost_usd"] = round(t["cost_usd"] + cost, 6)
            t["latency_ms_sum"] += int(latency_ms)
            prov = t["by_provider"].setdefault(provider, {"calls": 0, "cost_usd": 0.0, "latency_ms_sum": 0})
            prov["calls"] += 1
            prov["cost_usd"] = round(prov["cost_usd"] + cost, 6)
            prov["latency_ms_sum"] += int(latency_ms)
            feat = t["by_feature"].setdefault(rec.feature, {"calls": 0, "cost_usd": 0.0})
            feat["calls"] += 1
            feat["cost_usd"] = round(feat["cost_usd"] + cost, 6)
        self._ensure_flusher()
        return rec

    # ── reporting ──────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            t = dict(self.totals)
            calls = max(1, t["calls"])
            t["avg_latency_ms"] = round(t["latency_ms_sum"] / calls)
            t["cache_hit_rate"] = round(t["cache_hits"] / calls, 3)
            t["by_provider"] = {
                k: {**v, "avg_latency_ms": round(v["latency_ms_sum"] / max(1, v["calls"]))}
                for k, v in t["by_provider"].items()
            }
            recent = list(self._buffer)[-25:]
        t["recent"] = [
            {
                "provider": r.provider,
                "model": r.model,
                "feature": r.feature,
                "latency_ms": r.latency_ms,
                "cache_hit": r.cache_hit,
                "cost_usd": r.cost_usd,
                "created_at": r.created_at.isoformat(),
            }
            for r in reversed(recent)
        ]
        return t

    # ── persistence ────────────────────────────────────────────────────────

    def _ensure_flusher(self) -> None:
        if self._flusher and self._flusher.is_alive():
            return
        self._flusher = threading.Thread(target=self._flush_loop, name="llm-usage-flush", daemon=True)
        self._flusher.start()

    def _flush_loop(self) -> None:
        while not self._stop.wait(self._flush_interval):
            self.flush()

    def flush(self) -> int:
        with self._lock:
            batch, self._pending = self._pending, []
        if not batch:
            return 0
        try:
            from app.services.mysql_service import get_mysql

            s = get_mysql().get_session()
            for r in batch:
                s.execute(
                    "INSERT INTO llm_usage (id, user_id, feature, provider, model, prompt_tokens, "
                    "completion_tokens, latency_ms, cache_hit, cost_usd, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        r.id, r.user_id, r.feature, r.provider, r.model[:160], r.prompt_tokens,
                        r.completion_tokens, r.latency_ms, int(r.cache_hit), r.cost_usd, r.created_at,
                    ),
                )
            return len(batch)
        except Exception as exc:  # pragma: no cover - db optional
            logger.debug(f"llm_usage flush skipped: {exc}")
            return 0

    def stop(self) -> None:
        self._stop.set()
        self.flush()


_tracker: Optional[LLMUsageTracker] = None
_tracker_lock = threading.Lock()


def get_usage_tracker() -> LLMUsageTracker:
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = LLMUsageTracker()
    return _tracker


class track_feature:
    """Context manager to tag LLM calls with a feature and optional user id.

    Usage::

        with track_feature("jd_match", user_id=str(user.id)):
            llm.generate_json(...)
    """

    def __init__(self, feature: str, user_id: Optional[str] = None):
        self.feature = feature
        self.user_id = user_id
        self._tokens: list = []

    def __enter__(self):
        self._tokens.append(current_feature.set(self.feature))
        if self.user_id is not None:
            self._tokens.append(current_user_id.set(self.user_id))
        return self

    def __exit__(self, *exc):
        for tok in reversed(self._tokens):
            try:
                if tok.var is current_feature:
                    current_feature.reset(tok)
                else:
                    current_user_id.reset(tok)
            except ValueError:
                pass
        return False


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.ms = int((time.perf_counter() - self.start) * 1000)
        return False
