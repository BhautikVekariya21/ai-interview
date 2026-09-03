"""Auth rate limiting, lockout, and CAPTCHA verification.

Backed by Valkey/Redis when available, with a thread-safe process-local
fallback. All state is keyed by a caller-supplied identifier (client IP and/or
email) so no schema changes are required.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Optional

import httpx
from fastapi import Request
from loguru import logger

from app.core.config import settings
from app.services.cache_service import get_cache


@dataclass
class RateDecision:
    allowed: bool          # False → hard block (return 429)
    captcha_required: bool  # True → client must present a valid CAPTCHA token
    retry_after: int        # seconds hint for Retry-After header


# Rate limiting remains a security control when ordinary caching is disabled or
# Valkey is unavailable, so its local fallback is independent of CacheService.
_fallback_counters: dict[str, tuple[int, float]] = {}
_fallback_lock = Lock()


def _local_is_active(key: str) -> bool:
    now = time.monotonic()
    with _fallback_lock:
        record = _fallback_counters.get(key)
        if not record:
            return False
        _, expires_at = record
        if expires_at <= now:
            _fallback_counters.pop(key, None)
            return False
        return True


def _local_set(key: str, ttl_seconds: int) -> None:
    with _fallback_lock:
        _fallback_counters[key] = (1, time.monotonic() + ttl_seconds)


def _local_delete(*keys: str) -> None:
    with _fallback_lock:
        for key in keys:
            _fallback_counters.pop(key, None)


def _incr(key: str, window_seconds: int) -> int:
    """Increment a windowed counter and return the new value.

    Uses native Redis INCR/EXPIRE when available for atomicity; otherwise uses
    a thread-safe, process-local fallback.
    """
    cache = get_cache()
    redis = getattr(cache, "_redis", None)
    if redis is not None:
        try:
            count = int(redis.incr(key))
            # Only a new counter sets its window. Refreshing expiry on every
            # request can keep an attacker blocked indefinitely.
            if count == 1:
                redis.expire(key, window_seconds)
            return count
        except Exception:  # pragma: no cover - network dependent
            pass

    now = time.monotonic()
    with _fallback_lock:
        count, expires_at = _fallback_counters.get(key, (0, now + window_seconds))
        if expires_at <= now:
            count, expires_at = 0, now + window_seconds
        count += 1
        _fallback_counters[key] = (count, expires_at)
        return count


def client_ip(request: Request) -> str:
    """Return the source IP, trusting forwarded headers only by configuration."""
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


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


# ── Sliding window (plan-aware) ──────────────────────────────────────────────
_sliding_local: dict[str, list[float]] = {}


def check_sliding(scope: str, identifier: str, limit: int, window_seconds: int) -> RateDecision:
    """True sliding-window limiter.

    Fixed windows allow 2x bursts at the boundary; this keeps a sorted set of
    timestamps (Redis ZSET) so the limit holds for *any* ``window_seconds``
    span. Falls back to an in-process list when Redis is unavailable.
    """
    key = f"slide:{scope}:{identifier}"
    now = time.time()
    floor = now - window_seconds
    cache = get_cache()
    redis = getattr(cache, "_redis", None)
    if redis is not None:
        try:
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, floor)
            pipe.zadd(key, {f"{now:.6f}": now})
            pipe.zcard(key)
            pipe.zrange(key, 0, 0, withscores=True)
            pipe.expire(key, window_seconds + 1)
            _, _, count, oldest, _ = pipe.execute()
            if int(count) > limit:
                # Roll back our own entry so a blocked request doesn't consume quota.
                redis.zrem(key, f"{now:.6f}")
                oldest_ts = float(oldest[0][1]) if oldest else now
                return RateDecision(
                    allowed=False,
                    captcha_required=False,
                    retry_after=max(1, int(oldest_ts + window_seconds - now) + 1),
                )
            return RateDecision(allowed=True, captcha_required=False, retry_after=0)
        except Exception:  # pragma: no cover - network dependent
            logger.warning("sliding limiter backend error; using local fallback")

    with _fallback_lock:
        stamps = [t for t in _sliding_local.get(key, []) if t > floor]
        if len(stamps) >= limit:
            _sliding_local[key] = stamps
            return RateDecision(
                allowed=False,
                captcha_required=False,
                retry_after=max(1, int(stamps[0] + window_seconds - now) + 1),
            )
        stamps.append(now)
        _sliding_local[key] = stamps
        return RateDecision(allowed=True, captcha_required=False, retry_after=0)


def plan_limited(resource: str, window_seconds: int = 60):
    """FastAPI dependency: enforce the signed-in user's plan quota for ``resource``.

    ``resource`` maps to a key in ``session_service.PLANS`` such as
    ``llm_calls_per_minute`` or ``code_runs_per_minute``. Anonymous callers get
    the free plan keyed by IP. Response headers advertise the quota.
    """
    from fastapi import Depends, HTTPException, Response, status

    from app.api.auth_routes import get_current_user  # local import: avoid cycle
    from app.services.mysql_service import get_mysql
    from app.services.session_service import PLANS, SessionService

    def _optional_user(request: Request, db=Depends(get_mysql)):
        try:
            return get_current_user(request, request.headers.get("authorization"), db)
        except Exception:
            return None

    def _dep(request: Request, response: Response, current=Depends(_optional_user), db=Depends(get_mysql)):
        user_id = str(current["user"].id) if current else None
        plan = SessionService(db).get_plan(user_id) if user_id else "free"
        limit = int(PLANS.get(plan, PLANS["free"]).get(resource, 30))
        ident = user_id or client_ip(request)
        decision = check_sliding(f"plan:{resource}", ident, limit, window_seconds)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Plan"] = plan
        if not decision.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"{plan.title()} plan limit reached for {resource.replace('_', ' ')}. Try again shortly.",
                headers={"Retry-After": str(decision.retry_after), "X-RateLimit-Limit": str(limit)},
            )
        return {"plan": plan, "limit": limit, "user": current["user"] if current else None}

    return _dep


def check_quota(scope: str, identifier: str, limit: int, window_seconds: int) -> RateDecision:
    """Fixed-window quota with no CAPTCHA escalation.

    ``check_rate`` above is tuned for auth, where a suspicious caller should be
    challenged rather than blocked. Expensive-but-legitimate endpoints (code
    execution) just need a ceiling, so this returns a plain allow/deny.
    """
    key = f"quota:{scope}:{identifier}"
    try:
        count = _incr(key, window_seconds)
    except Exception:  # pragma: no cover - never fail-open loudly
        logger.warning("rate limit backend error; allowing request")
        return RateDecision(allowed=True, captcha_required=False, retry_after=0)

    if count > limit:
        return RateDecision(allowed=False, captcha_required=False, retry_after=window_seconds)
    return RateDecision(allowed=True, captcha_required=False, retry_after=0)


# ─────────────────────── Per-account login lockout ───────────────────────

def _lockout_key(identifier: str) -> str:
    return f"lockout:login:{identifier}"


def is_locked_out(identifier: str) -> bool:
    key = _lockout_key(identifier) + ":until"
    redis = getattr(get_cache(), "_redis", None)
    if redis is not None:
        try:
            return bool(redis.get(key))
        except Exception:  # pragma: no cover - network dependent
            pass
    return _local_is_active(key)


def record_login_failure(identifier: str) -> None:
    fail_key = _lockout_key(identifier) + ":fails"
    count = _incr(fail_key, settings.AUTH_LOCKOUT_SECONDS)
    if count >= settings.AUTH_LOCKOUT_MAX_FAILURES:
        until_key = _lockout_key(identifier) + ":until"
        redis = getattr(get_cache(), "_redis", None)
        if redis is not None:
            try:
                redis.setex(until_key, settings.AUTH_LOCKOUT_SECONDS, "1")
                return
            except Exception:  # pragma: no cover - network dependent
                pass
        _local_set(until_key, settings.AUTH_LOCKOUT_SECONDS)


def clear_login_failures(identifier: str) -> None:
    fail_key = _lockout_key(identifier) + ":fails"
    until_key = _lockout_key(identifier) + ":until"
    cache = get_cache()
    redis = getattr(cache, "_redis", None)
    if redis is not None:
        try:
            redis.delete(fail_key, until_key)
            return
        except Exception:  # pragma: no cover
            pass
    _local_delete(fail_key, until_key)


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
