"""Cache service with Valkey primary and in-memory fallback."""

import hashlib
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from loguru import logger

from app.core.config import settings

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


def _get_cache_url() -> Optional[str]:
    return settings.VALKEY_URL or settings.REDIS_URL


def _is_expected_local_cache_url(cache_url: str) -> bool:
    try:
        parsed = urlparse(cache_url)
    except Exception:
        return False
    return parsed.scheme == "redis" and parsed.hostname in {"localhost", "127.0.0.1"}


class CacheService:
    def __init__(self):
        self.enabled = bool(settings.CACHE_ENABLED)
        self.default_ttl = int(settings.CACHE_DEFAULT_TTL_SECONDS)
        self._redis = None
        self._memory: Dict[str, Dict[str, Any]] = {}

        cache_url = _get_cache_url()

        if self.enabled and REDIS_AVAILABLE and cache_url:
            try:
                self._redis = redis.Redis.from_url(cache_url, decode_responses=True)
                self._redis.ping()
                logger.info("  Cache: Valkey connected")
            except Exception as e:
                self._redis = None
                if _is_expected_local_cache_url(cache_url):
                    logger.info(f"  Cache: local Valkey not running, using in-memory fallback ({e})")
                else:
                    logger.warning(f"  Cache: Valkey unavailable, using in-memory fallback ({e})")
        elif self.enabled:
            logger.info("  Cache: in-memory fallback")

    @staticmethod
    def make_key(namespace: str, payload: str) -> str:
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None

        if self._redis is not None:
            try:
                raw = self._redis.get(key)
                if raw is None:
                    return None
                return json.loads(raw)
            except Exception:
                return None

        rec = self._memory.get(key)
        if not rec:
            return None
        if rec["exp"] < time.time():
            self._memory.pop(key, None)
            return None
        return rec["val"]

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        if not self.enabled:
            return

        ttl = int(ttl_seconds or self.default_ttl)

        if self._redis is not None:
            try:
                self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
                return
            except Exception:
                pass

        self._memory[key] = {
            "val": value,
            "exp": time.time() + ttl,
        }


_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
