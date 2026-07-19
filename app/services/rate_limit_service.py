"""Auth rate limiting, lockout, and CAPTCHA verification.

Backed by the shared cache (Valkey/Redis with in-memory fallback) so counters
survive across workers when Valkey is available and degrade gracefully when it
is not. All state is keyed by a caller-supplied identifier (client IP and/or
email) so no schema changes are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.services.cache_service import get_cache


@dataclass
class RateDecision:
    allowed: bool          # False → hard block (return 429)
    captcha_required: bool  # True → client must present a valid CAPTCHA token
    retry_after: int        # seconds hint for Retry-After header


def _incr(key: str, window_seconds: int) -> int:
    """Increment a windowed counter and return the new value.

    Uses native Redis INCR/EXPIRE when available for atomicity; otherwise falls
    back to the in-memory cache's get/set (best-effort, single-process).
    """
    cache = get_cache()
    redis = getattr(cache, "_redis", None)
    if redis is not None:
        try:
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            count, _ = pipe.execute()
            return int(count)
        except Exception:  # pragma: no cover - network dependent
            pass

    current = cache.get(key) or 0
    current = int(current) + 1
    cache.set(key, current, ttl_seconds=window_seconds)
    return current


def check_rate(scope: str, identifier: str) -> RateDecision:
    """Record one attempt for (scope, identifier) and decide how to respond."""
    window = settings.AUTH_RATELIMIT_WINDOW_SECONDS
    key = f"ratelimit:{scope}:{identifier}"
    try:
        count = _incr(key, window)
    except Exception:  # pragma: no cover - never fail-open loudly
        logger.warning("rate limit backend error; allowing request")
        return RateDecision(allowed=True, captcha_required=False, retry_after=0)

    if count > settings.AUTH_RATELIMIT_HARD_THRESHOLD:
        return RateDecision(allowed=False, captcha_required=True, retry_after=window)
    if count > settings.AUTH_RATELIMIT_CAPTCHA_THRESHOLD:
        return RateDecision(allowed=True, captcha_required=True, retry_after=0)
    return RateDecision(allowed=True, captcha_required=False, retry_after=0)


# ─────────────────────── Per-account login lockout ───────────────────────

def _lockout_key(identifier: str) -> str:
    return f"lockout:login:{identifier}"


def is_locked_out(identifier: str) -> bool:
    return bool(get_cache().get(_lockout_key(identifier) + ":until"))


def record_login_failure(identifier: str) -> None:
    cache = get_cache()
    fail_key = _lockout_key(identifier) + ":fails"
    count = _incr(fail_key, settings.AUTH_LOCKOUT_SECONDS)
    if count >= settings.AUTH_LOCKOUT_MAX_FAILURES:
        cache.set(
            _lockout_key(identifier) + ":until",
            1,
            ttl_seconds=settings.AUTH_LOCKOUT_SECONDS,
        )


def clear_login_failures(identifier: str) -> None:
    cache = get_cache()
    redis = getattr(cache, "_redis", None)
    if redis is not None:
        try:
            redis.delete(_lockout_key(identifier) + ":fails", _lockout_key(identifier) + ":until")
            return
        except Exception:  # pragma: no cover
            pass
    cache._memory.pop(_lockout_key(identifier) + ":fails", None)  # type: ignore[attr-defined]
    cache._memory.pop(_lockout_key(identifier) + ":until", None)  # type: ignore[attr-defined]


# ─────────────────────── Cloudflare Turnstile ───────────────────────

def captcha_configured() -> bool:
    return bool(settings.TURNSTILE_SECRET_KEY)


def verify_captcha(token: Optional[str], remote_ip: Optional[str] = None) -> bool:
    """Verify a Turnstile token. No-op (returns True) when not configured."""
    if not captcha_configured():
        return True
    if not token:
        return False
    data = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        resp = httpx.post(settings.TURNSTILE_VERIFY_URL, data=data, timeout=10)
        return bool(resp.json().get("success"))
    except Exception:  # pragma: no cover - network dependent
        logger.warning("Turnstile verification request failed")
        return False
