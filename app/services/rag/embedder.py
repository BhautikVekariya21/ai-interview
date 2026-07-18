"""Sentence-transformers embedder + resume section chunking.

The model is loaded once as a process-wide singleton (it is several hundred MB
and thread-safe for inference). Chunking splits a resume into section-scoped
units so retrieval can cite a specific section rather than the whole document.

Throughput under concurrent load (Module 14 audit, item 5):
- ``embed_one`` is memoized with a bounded exact-match LRU so repeated queries
  (e.g. ``detect_similarity`` re-checking the same answer against the canned +
  past-answer indices) skip the encode entirely. The cache is keyed by text only
  and is scoped to one model instance, so a ``RAG_EMBEDDING_MODEL`` change builds
  a fresh ``Embedder`` (via the ``get_embedder`` singleton) with an empty cache —
  no stale vectors survive a model swap. Batch ``embed`` is intentionally *not*
  cached (session-init texts are unique and large).
- ``torch`` intra-op threads are bounded at init so many concurrent
  ``asyncio.to_thread`` encode calls don't each fan out across every core and
  thrash. See the README "Embedding throughput" note for the latency/throughput
  tradeoff.
"""

from __future__ import annotations

import os
import re
import time
import uuid
from functools import lru_cache
from typing import List, Sequence

from loguru import logger

from app.core.config import settings
from app.core.metrics import EMBEDDING_CACHE_EVENTS, EMBEDDING_DURATION_SECONDS
from app.services.rag.vector_store import Chunk


# Bound on torch intra-op threads per encode. Left at torch's default, every
# concurrent encode tries to use all cores, so N concurrent requests oversubscribe
# the CPU and each runs slower; capping trades a little single-call latency for
# much better aggregate throughput. Overridable via RAG_TORCH_NUM_THREADS.
_DEFAULT_TORCH_THREADS = 4
# Max distinct query texts memoized per model instance. ~1k keeps the working set
# of a busy session hot while bounding memory (a MiniLM vector is ~1.5 KB).
_QUERY_CACHE_SIZE = 1000



# Headings we treat as section boundaries when chunking a resume. Anything before
# the first heading becomes the "summary" chunk.
_SECTION_HEADINGS = re.compile(
    r"^\s*(summary|objective|profile|experience|work experience|employment|"
    r"projects?|skills?|technical skills|education|certifications?|"
    r"publications?|achievements?|awards?)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class Embedder:
    """Thin wrapper over a SentenceTransformer with a stable output dimension.

    Inference is thread-safe, so a single instance is shared process-wide. A
    per-instance LRU memoizes single-text (query) embeddings; batch embeddings
    are not cached.
    """

    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        self._bound_torch_threads()

        self.model_name = model_name or settings.RAG_EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

        # Bound exact-match cache for query embeds, scoped to THIS instance so a
        # model swap (new Embedder via get_embedder) starts empty — no cross-model
        # leakage, consistent with the metadata model_name versioning guard.
        self._embed_one_cached = lru_cache(maxsize=_QUERY_CACHE_SIZE)(self._embed_one_uncached)

    @staticmethod
    def _bound_torch_threads() -> None:
        """Cap torch intra-op threads before/at model load. Best-effort: torch may
        be absent (degraded mode) or already have spawned its pool."""
        try:
            import torch

            configured = getattr(settings, "RAG_TORCH_NUM_THREADS", 0) or 0
            n = configured if configured > 0 else min(_DEFAULT_TORCH_THREADS, os.cpu_count() or 1)
            torch.set_num_threads(int(n))
            logger.info(f"torch intra-op threads bounded to {n} for embedding throughput")
        except Exception as exc:  # torch missing or thread pool already fixed
            logger.debug(f"Could not set torch thread count (non-fatal): {exc}")

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """Batch-encode texts in a single encode() call (efficient on CPU/GPU).

        Not cached: session-init and doc-ingest batches are large and unique.
        """
        if not texts:
            return []
        with _timed("embed_batch"):
            vectors = self._model.encode(
                list(texts),
                convert_to_numpy=True,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        return vectors.astype("float32").tolist()

    def _embed_one_uncached(self, text: str) -> tuple:
        """Encode a single text. Returns a tuple so lru_cache stores an immutable
        value that callers can't mutate in place."""
        with _timed("embed_one"):
            vector = self._model.encode(
                [text],
                convert_to_numpy=True,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        return tuple(vector.astype("float32")[0].tolist())

    def embed_one(self, text: str) -> List[float]:
        """Exact-match cached single-text embed for the retrieval hot path.

        Repeated identical queries (e.g. the same answer checked against multiple
        indices in detect_similarity) reuse the cached vector instead of re-encoding.
        """
        info_before = self._embed_one_cached.cache_info()
        cached = self._embed_one_cached(text)
        hit = self._embed_one_cached.cache_info().hits > info_before.hits
        try:
            EMBEDDING_CACHE_EVENTS.labels(result="hit" if hit else "miss").inc()
        except Exception:  # metrics must never break the request path
            pass
        # Return a fresh list so a caller mutating the result can't corrupt the
        # cached tuple's derived state.
        return list(cached)

    def cache_clear(self) -> None:
        """Drop all memoized query embeddings (used by tests)."""
        self._embed_one_cached.cache_clear()


def _timed(operation: str):
    """Context manager recording encode() wall-time to Prometheus. Best-effort."""
    from contextlib import contextmanager

    @contextmanager
    def _cm():
        start = time.perf_counter()
        try:
            yield
        finally:
            try:
                EMBEDDING_DURATION_SECONDS.labels(operation=operation).observe(
                    time.perf_counter() - start
                )
            except Exception:
                pass

    return _cm()


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Process-wide singleton — loads the model once."""
    return Embedder()


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def chunk_resume(resume_text: str, candidate_id: str) -> List[Chunk]:
    """Split a resume into section-scoped chunks.

    Falls back to a single chunk when no recognizable headings are present, so a
    plain-text or oddly formatted resume still gets indexed.
    """
    text = resume_text or ""
    matches = list(_SECTION_HEADINGS.finditer(text))
    chunks: List[Chunk] = []

    if not matches:
        body = _clean(text)
        if body:
            chunks.append(
                Chunk(
                    chunk_id=f"{candidate_id}:resume:0",
                    source_text=body[:2000],
                    source_type="resume",
                    metadata={"section": "full", "candidate_id": candidate_id},
                )
            )
        return chunks

    # Preamble before the first heading (name/contact/title line).
    preamble = _clean(text[: matches[0].start()])
    if preamble:
        chunks.append(
            Chunk(
                chunk_id=f"{candidate_id}:resume:preamble",
                source_text=preamble[:2000],
                source_type="resume",
                metadata={"section": "preamble", "candidate_id": candidate_id},
            )
        )

    for i, match in enumerate(matches):
        section_name = _clean(match.group(1)).lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = _clean(text[start:end])
        if not body:
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{candidate_id}:resume:{section_name}",
                source_text=body[:2000],
                source_type="resume",
                metadata={"section": section_name, "candidate_id": candidate_id},
            )
        )
    return chunks


def chunk_job_description(jd_text: str, role: str) -> List[Chunk]:
    body = _clean(jd_text)
    if not body:
        return []
    return [
        Chunk(
            chunk_id=f"jd:{role}:{uuid.uuid5(uuid.NAMESPACE_URL, body[:256]).hex[:8]}",
            source_text=body[:2000],
            source_type="job_description",
            metadata={"role": role},
        )
    ]
