"""Regression coverage for shared rate limiting and client IP handling."""

from starlette.requests import Request

from app.services import rate_limit_service


class _NoRedisCache:
    _redis = None


def _request(client_ip: str = "198.51.100.10", forwarded: str | None = None) -> Request:
    headers = []
    if forwarded:
        headers.append((b"x-forwarded-for", forwarded.encode("ascii")))
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "https",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": headers,
            "client": (client_ip, 443),
            "server": ("testserver", 443),
        }
    )


def test_quota_works_when_general_cache_is_disabled(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "get_cache", lambda: _NoRedisCache())
    rate_limit_service._fallback_counters.clear()

    assert rate_limit_service.check_quota("test", "candidate", 2, 60).allowed
    assert rate_limit_service.check_quota("test", "candidate", 2, 60).allowed
    blocked = rate_limit_service.check_quota("test", "candidate", 2, 60)

    assert not blocked.allowed
    assert blocked.retry_after == 60


def test_lockout_fallback_is_enforced_and_cleared(monkeypatch):
    monkeypatch.setattr(rate_limit_service, "get_cache", lambda: _NoRedisCache())
    monkeypatch.setattr(rate_limit_service.settings, "AUTH_LOCKOUT_MAX_FAILURES", 2)
    monkeypatch.setattr(rate_limit_service.settings, "AUTH_LOCKOUT_SECONDS", 60)
    rate_limit_service._fallback_counters.clear()

    rate_limit_service.record_login_failure("candidate@example.com")
    assert not rate_limit_service.is_locked_out("candidate@example.com")

    rate_limit_service.record_login_failure("candidate@example.com")
    assert rate_limit_service.is_locked_out("candidate@example.com")

    rate_limit_service.clear_login_failures("candidate@example.com")
    assert not rate_limit_service.is_locked_out("candidate@example.com")


def test_forwarded_ip_is_used_only_for_trusted_proxy(monkeypatch):
    request = _request(forwarded="203.0.113.9, 198.51.100.10")

    monkeypatch.setattr(rate_limit_service.settings, "TRUST_PROXY_HEADERS", False)
    assert rate_limit_service.client_ip(request) == "198.51.100.10"

    monkeypatch.setattr(rate_limit_service.settings, "TRUST_PROXY_HEADERS", True)
    assert rate_limit_service.client_ip(request) == "203.0.113.9"
