"""Background cache warmer for the News and Blog feeds.

Both pages aggregate ~16-20 external RSS feeds and then fetch article pages for
og:image enrichment, so a cold call can take ~10s. To keep every visitor on the
fast path, this warmer pre-populates the exact cache entries those routes read:
once at startup and then on a repeating interval just under the cache TTL, so
the cached payload never lapses and no user request hits the cold path.

Runs in a daemon thread — the aggregation is blocking (requests-based), so it
must stay off the asyncio event loop. Warming one entry never blocks startup.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Callable, List, Tuple

from loguru import logger

from app.services.cache_service import get_cache

# Matches the TTL the routes use in their own cache.set(...) calls, and a warm
# interval comfortably shorter than it so the entry is refreshed before expiry.
CACHE_TTL_SECONDS = 900        # 15 minutes
WARM_INTERVAL_SECONDS = 600    # 10 minutes

_warm_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _warm_targets() -> List[Tuple[str, dict, Callable[..., Any], dict]]:
    """(namespace, key_params, fetch_fn, fetch_kwargs) for each warmed entry.

    `key_params` MUST equal what the corresponding route hashes into its cache
    key, or the warmed entry won't be the one the route looks up. The frontend
    reads News with {category: "all", limit: 300} and Blog with
    {category: "all", limit: 30} (blog sends no category, which the route
    normalises to "all"). Imported lazily so a feed-service import error can't
    break app startup.
    """
    from app.services.blog_service import fetch_blog_feed
    from app.services.news_service import fetch_technology_news

    return [
        ("news:technology", {"category": "all", "limit": 300}, fetch_technology_news, {"category": None, "limit": 300}),
        ("blog:feed", {"category": "all", "limit": 30}, fetch_blog_feed, {"category": None, "limit": 30}),
    ]


def _warm_once() -> None:
    cache = get_cache()
    for namespace, key_params, fetch_fn, fetch_kwargs in _warm_targets():
        if _stop_event.is_set():
            return
        try:
            payload = fetch_fn(**fetch_kwargs)
            if isinstance(payload, dict) and payload.get("items"):
                cache_key = cache.make_key(namespace, json.dumps(key_params, sort_keys=True))
                cache.set(cache_key, payload, ttl_seconds=CACHE_TTL_SECONDS)
                logger.info(f"  Cache warm: {namespace} ({len(payload['items'])} items)")
            else:
                # Keep any existing (still-valid) entry rather than overwriting
                # it with an empty payload from a transient upstream failure.
                logger.warning(f"  Cache warm: {namespace} returned no items, keeping existing entry")
        except Exception as e:  # pragma: no cover - best-effort warming
            logger.warning(f"  Cache warm failed for {namespace}: {e}")


def _warm_loop() -> None:
    # Warm immediately on startup, then re-warm each interval until stopped.
    while not _stop_event.is_set():
        _warm_once()
        _stop_event.wait(WARM_INTERVAL_SECONDS)


def start_cache_warmer() -> None:
    """Start the background warmer (idempotent). No-op if caching is disabled."""
    global _warm_thread
    if _warm_thread is not None and _warm_thread.is_alive():
        return

    if not get_cache().enabled:
        logger.info("  Cache warmer: cache disabled, skipping")
        return

    _stop_event.clear()
    _warm_thread = threading.Thread(target=_warm_loop, name="cache-warmer", daemon=True)
    _warm_thread.start()
    logger.info("  Cache warmer: started (news + blog feeds)")


def stop_cache_warmer() -> None:
    """Signal the warmer thread to exit (called on app shutdown)."""
    _stop_event.set()
