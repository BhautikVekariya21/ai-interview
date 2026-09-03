import time

from app.services import cache_service


def test_cache_falls_back_to_in_memory_when_valkey_unavailable(monkeypatch):
    monkeypatch.setattr(cache_service.settings, "CACHE_ENABLED", True)
    monkeypatch.setattr(cache_service.settings, "CACHE_DEFAULT_TTL_SECONDS", 60)
    monkeypatch.setattr(cache_service.settings, "VALKEY_URL", "redis://127.0.0.1:6399/0")
    monkeypatch.setattr(cache_service.settings, "REDIS_URL", "redis://127.0.0.1:6399/0")

    if cache_service.REDIS_AVAILABLE:
        class FailingRedis:
            @staticmethod
            def from_url(*args, **kwargs):
                raise RuntimeError("redis down")

        monkeypatch.setattr(cache_service.redis, "Redis", FailingRedis)

    cache = cache_service.CacheService()

    assert cache._redis is None

    key = cache.make_key("resume", "payload")
    value = {"ok": True, "source": "memory"}
    cache.set(key, value, ttl_seconds=1)

    assert cache.get(key) == value


def test_in_memory_cache_expires_entries(monkeypatch):
    monkeypatch.setattr(cache_service.settings, "CACHE_ENABLED", True)
    monkeypatch.setattr(cache_service.settings, "CACHE_DEFAULT_TTL_SECONDS", 60)
    monkeypatch.setattr(cache_service.settings, "VALKEY_URL", "redis://127.0.0.1:6399/0")
    monkeypatch.setattr(cache_service.settings, "REDIS_URL", "redis://127.0.0.1:6399/0")
    monkeypatch.setattr(cache_service, "REDIS_AVAILABLE", False)

    cache = cache_service.CacheService()

    key = cache.make_key("resume", "ttl-check")
    cache.set(key, {"ok": True}, ttl_seconds=1)
    assert cache.get(key) == {"ok": True}

    time.sleep(1.1)

    assert cache.get(key) is None


def test_cache_uses_legacy_redis_url_when_valkey_url_missing(monkeypatch):
    monkeypatch.setattr(cache_service.settings, "CACHE_ENABLED", True)
    monkeypatch.setattr(cache_service.settings, "CACHE_DEFAULT_TTL_SECONDS", 60)
    monkeypatch.setattr(cache_service.settings, "VALKEY_URL", None)
    monkeypatch.setattr(cache_service.settings, "REDIS_URL", "redis://127.0.0.1:6399/0")
    monkeypatch.setattr(cache_service, "REDIS_AVAILABLE", False)

    cache = cache_service.CacheService()
    key = cache.make_key("resume", "legacy-url")
    cache.set(key, {"ok": True})

    assert cache.get(key) == {"ok": True}
