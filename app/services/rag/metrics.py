"""RAG metrics instrumentation helpers (Module 14, item 11).

Thin wrappers over the Prometheus primitives in app.core.metrics so the service
and route layers can record retrieval latency / top-k score / request counts
without repeating the label bookkeeping. Everything here is best-effort: metrics
must never change behavior or raise into the request path.

Usage
-----
Service layer (time a FAISS retrieval and record the top hit's score)::

    from app.services.rag.metrics import observe_retrieval

    with observe_retrieval("generate_question") as rec:
        hits = store.search(query_vec, top_k)
        rec(hits)  # records top_k_score from hits[0].similarity

Route layer (count an endpoint call, success or error)::

    from app.services.rag.metrics import track_endpoint

    async with track_endpoint("generate-question"):
        ...  # any exception is counted as status="error" and re-raised
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Iterator, Sequence

from app.core.metrics import (
    RAG_ENDPOINT_REQUEST_COUNT,
    RETRIEVAL_LATENCY_SECONDS,
    RETRIEVAL_TOP_K_SCORE,
)


def _top_similarity(hits: Sequence[Any]) -> float | None:
    """Pull the best similarity from a list of RetrievedChunk-like objects."""
    if not hits:
        return None
    top = hits[0]
    sim = getattr(top, "similarity", None)
    if sim is None and isinstance(top, dict):
        sim = top.get("similarity")
    try:
        return float(sim) if sim is not None else None
    except (TypeError, ValueError):
        return None


@contextmanager
def observe_retrieval(operation: str) -> Iterator[Any]:
    """Time a retrieval call and (optionally) record its top-k similarity.

    Yields a `record(hits)` callback; call it with the retrieved list to log the
    top hit's score. Latency is always recorded on exit, even if `record` is not
    called or the block raises.
    """
    recorded: dict[str, bool] = {"done": False}

    def record(hits: Sequence[Any]) -> None:
        if recorded["done"]:
            return
        recorded["done"] = True
        score = _top_similarity(hits)
        if score is not None:
            try:
                RETRIEVAL_TOP_K_SCORE.labels(operation=operation).observe(score)
            except Exception:  # metrics must never break the request path
                pass

    start = time.perf_counter()
    try:
        yield record
    finally:
        try:
            RETRIEVAL_LATENCY_SECONDS.labels(operation=operation).observe(
                time.perf_counter() - start
            )
        except Exception:
            pass


@asynccontextmanager
async def track_endpoint(endpoint: str):
    """Count a RAG endpoint invocation as success/error around an async block."""
    try:
        yield
    except Exception:
        _safe_count(endpoint, "error")
        raise
    else:
        _safe_count(endpoint, "success")


def _safe_count(endpoint: str, status: str) -> None:
    try:
        RAG_ENDPOINT_REQUEST_COUNT.labels(endpoint=endpoint, status=status).inc()
    except Exception:
        pass
