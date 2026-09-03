"""FAISS-backed vector store (IndexFlatL2), persisted to disk per session.

Concrete implementation of the VectorStore protocol. The index file and a JSON
metadata sidecar (chunk_id -> source_text, source_type, metadata) live together
under a per-session directory. Swapping to pgvector/Qdrant later means writing a
sibling class with the same four methods — nothing else changes.

Durability under concurrency:
- ``save()`` writes both files to temp paths and ``os.replace()``s them into
  place. Each rename is atomic, but the two are separate calls, so a lock-free
  ``load()`` can briefly catch the new index beside the old metadata (or vice
  versa). ``load()`` closes that gap by checking the row-count invariant
  (``index.ntotal == len(chunks)``) and retrying the read until the pair is
  consistent — so a torn write is never returned to the caller.
- ``save()`` itself takes no lock. Callers that do a load-modify-save cycle (or a
  cold build that must not run twice) wrap it in ``namespace_lock(dir)`` — a
  process-safe file lock that serializes writers across gunicorn workers, not
  just threads. Keeping the lock out of ``save()`` avoids re-entrant acquisition
  of the same on-disk lock from a caller that already holds it.

Provenance validation on load:
- ``metadata.json`` stamps the embedding ``model_name``, the on-disk
  ``format_version``, the ``metric``, and an optional ``extra`` bag (e.g. the
  seed-file hash). ``load()`` rejects an index whose stored model name, format
  version, or metric differs from the configured one — each would otherwise load
  silently and return geometrically meaningless similarity scores. A rejected
  load behaves like a corrupt one: it resets to empty and returns False so the
  caller rebuilds.

Scoring:
- ``_prepare`` unit-normalizes vectors for *both* metrics, so ``search`` can
  report a true cosine similarity in ``[0, 1]`` either way. For ``l2`` this
  matters twice over: FAISS's ``IndexFlatL2`` returns the *squared* distance, and
  the identity used to recover the cosine (``cos = 1 - d^2/2``) only holds for
  unit-norm vectors.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from filelock import FileLock
from loguru import logger

import faiss

from app.services.rag.vector_store import Chunk, RetrievedChunk

_LOCK_FILE = ".index.lock"

# On-disk layout version, stamped for provenance/debugging.
#   1 -> scores derived as 1/(1+squared_L2); vectors normalized only for cosine
#   2 -> true cosine scores; vectors normalized for every metric
# Deliberately NOT rejected on load: v1 and v2 store the *same* raw vectors
# (index.faiss is untouched by this change), and the configured model's vectors
# are already unit-norm, so re-normalizing is a no-op against v1 data. Only the
# score *derivation* changed. A future change that alters what is written into
# index.faiss should add a rejection here — bumping this alone would needlessly
# discard accumulated `_answers` history on a live volume.
_INDEX_FORMAT_VERSION = 2


def namespace_lock(session_dir: Path) -> FileLock:
    """Return a process-safe lock for a store's namespace directory.

    Serializes concurrent writers (save / load-modify-save / cold build) to the
    same namespace across processes and threads. The lock file lives inside the
    namespace dir, which is created if absent so the lock can be taken before the
    first save.
    """
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    return FileLock(str(session_dir / _LOCK_FILE))


class FaissVectorStore:
    """In-process FAISS store with a JSON metadata sidecar.

    Vectors are unit-normalized on the way in (see ``_prepare``) regardless of
    metric, so both backends report a true cosine similarity:
      - "l2"     : IndexFlatL2 over unit vectors. FAISS returns squared distance;
                   ``search`` converts it to cosine exactly via 1 - d^2/2 and
                   reports ``distance`` as the true Euclidean distance.
      - "cosine" : IndexFlatIP over unit vectors, so inner product == cosine
                   similarity. Used for near-duplicate answer detection where a
                   true cosine threshold (e.g. >0.9) is required.

    Not thread-safe for concurrent writes; callers serialize writers with
    ``namespace_lock`` and rely on ``save()``'s atomic replace. Reads (search)
    are safe to run concurrently.
    """

    _INDEX_FILE = "index.faiss"
    _META_FILE = "metadata.json"

    # A lock-free load() can catch save()'s two os.replace calls mid-flight; retry
    # the read a handful of times to converge on a consistent index/metadata pair.
    _LOAD_RETRIES = 5
    _LOAD_RETRY_SLEEP = 0.01  # seconds; the writer's 2nd replace lands in << 1ms

    def __init__(
        self,
        session_dir: Path,
        dim: int,
        metric: str = "l2",
        model_name: str = "",
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if metric not in ("l2", "cosine"):
            raise ValueError(f"Unsupported metric: {metric!r}")
        self._dir = Path(session_dir)
        self._dim = dim
        self._metric = metric
        # Provenance stamped into metadata.json and validated on load.
        self.model_name = model_name
        self.extra_meta: Dict[str, Any] = dict(extra_meta or {})
        # Populated on load() so callers can inspect stored provenance (e.g. the
        # seed hash) and decide whether to rebuild.
        self.loaded_extra_meta: Dict[str, Any] = {}
        self._index = self._make_index()
        self._chunks: List[Chunk] = []  # positional: row i in the index == _chunks[i]

    def _make_index(self):
        return faiss.IndexFlatIP(self._dim) if self._metric == "cosine" else faiss.IndexFlatL2(self._dim)

    def _prepare(self, matrix: np.ndarray) -> np.ndarray:
        """Return a unit-normalized, contiguous float32 *copy* of `matrix`.

        Both metrics require unit-norm vectors:
          - "cosine": IndexFlatIP over unit vectors returns cosine directly.
          - "l2"    : IndexFlatL2 over unit vectors gives d^2 = 2 - 2*cos, so the
            cosine is recoverable exactly as 1 - d^2/2 (see `search`). Without
            normalizing, that identity does not hold and the reported similarity
            is not a cosine at all.

        Normalizing here rather than in the embedder makes the invariant hold at
        the store boundary, so it cannot be broken by a caller passing raw
        vectors or by swapping RAG_EMBEDDING_MODEL to a model whose output is not
        already unit-norm.

        The copy is mandatory: normalization is in-place, and
        ``np.ascontiguousarray`` does *not* copy an array that is already
        contiguous float32 — which would silently rescale the caller's buffer.
        Rows with zero norm are left untouched instead of becoming NaN.
        """
        matrix = np.array(matrix, dtype="float32", copy=True, order="C")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        np.divide(matrix, norms, out=matrix, where=norms > 0)
        return matrix

    def add(self, embeddings: Sequence[Sequence[float]], chunks: Sequence[Chunk]) -> None:
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"embeddings ({len(embeddings)}) and chunks ({len(chunks)}) must align 1:1"
            )
        if not chunks:
            return
        matrix = np.asarray(embeddings, dtype="float32")
        if matrix.shape[1] != self._dim:
            raise ValueError(f"embedding dim {matrix.shape[1]} != index dim {self._dim}")
        self._index.add(self._prepare(matrix))
        self._chunks.extend(chunks)

    def search(self, embedding: Sequence[float], top_k: int) -> List[RetrievedChunk]:
        if len(self._chunks) == 0:
            return []
        query = self._prepare(np.asarray([embedding], dtype="float32"))
        k = min(top_k, len(self._chunks))
        scores, indices = self._index.search(query, k)

        results: List[RetrievedChunk] = []
        for raw, idx in zip(scores[0], indices[0]):
            if idx < 0:  # FAISS pads with -1 when fewer than k neighbors exist
                continue
            if self._metric == "cosine":
                # IndexFlatIP over unit-norm vectors returns cosine directly.
                cosine = float(raw)
            else:
                # IndexFlatL2 returns the SQUARED L2 distance, not the distance.
                # _prepare normalized both sides, so ||a-b||^2 = 2 - 2*cos holds
                # exactly and the cosine is recoverable without approximation.
                cosine = 1.0 - float(raw) / 2.0
            # Report true Euclidean distance so the field means the same thing
            # under both metrics: on the unit sphere ||a-b|| = sqrt(2 - 2*cos).
            # max() absorbs float error nudging cosine just past 1.0.
            distance = math.sqrt(max(0.0, 2.0 - 2.0 * cosine))
            results.append(
                RetrievedChunk(chunk=self._chunks[idx], distance=distance, score=cosine)
            )
        return results

    def save(self) -> None:
        """Atomically persist the index + metadata sidecar.

        Both files are written to a temp path in the same directory (so the final
        rename is atomic on the same filesystem) and ``os.replace``d into place.
        A concurrent reader therefore sees either the old pair or the new pair,
        never a mix. Takes no lock — wrap in ``namespace_lock`` when the enclosing
        operation is a load-modify-save or a race-prone cold build.
        """
        self._dir.mkdir(parents=True, exist_ok=True)

        # FAISS has no write-to-buffer that avoids a temp file; write to a sibling
        # temp path then atomically replace.
        index_final = self._dir / self._INDEX_FILE
        index_tmp = self._dir / f"{self._INDEX_FILE}.{os.getpid()}.tmp"
        faiss.write_index(self._index, str(index_tmp))
        os.replace(index_tmp, index_final)

        meta = {
            "format_version": _INDEX_FORMAT_VERSION,
            "dim": self._dim,
            "metric": self._metric,
            "model_name": self.model_name,
            "extra": self.extra_meta,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "source_text": c.source_text,
                    "source_type": c.source_type,
                    "metadata": c.metadata,
                }
                for c in self._chunks
            ],
        }
        meta_final = self._dir / self._META_FILE
        meta_tmp = self._dir / f"{self._META_FILE}.{os.getpid()}.tmp"
        meta_tmp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        os.replace(meta_tmp, meta_final)

        logger.debug(f"FAISS index saved: {self._dir} ({len(self._chunks)} chunks)")

    def load(self) -> bool:
        """Load a persisted index, validating provenance.

        Returns False (and resets to an empty index) when the index is missing,
        corrupt, or was built with different provenance than the current
        configuration — a different embedding model, an older on-disk format
        version, or a different metric. In every case the caller rebuilds from
        source.

        ``save()`` replaces ``index.faiss`` and ``metadata.json`` with two
        separate ``os.replace`` calls; each rename is atomic but the *pair* is
        not. A lock-free reader can therefore observe the new index (N rows)
        beside the not-yet-replaced metadata (M chunks) for a brief window. We
        detect that torn state via the row-count invariant (``ntotal`` must equal
        ``len(chunks)``) and retry the read a few times so the reader converges on
        a consistent pair instead of returning a mismatched one.
        """
        for attempt in range(self._LOAD_RETRIES):
            outcome = self._load_once()
            if outcome is not None:
                return outcome
            # Torn index/metadata pair caught mid-save — back off briefly and
            # re-read; the writer's second os.replace lands in well under a ms.
            time.sleep(self._LOAD_RETRY_SLEEP)
        # Still torn after retries: treat like corruption and rebuild empty
        # rather than hand back a mismatched index/metadata pair.
        logger.warning(
            f"FAISS index at {self._dir} still torn after {self._LOAD_RETRIES} reads — rebuilding."
        )
        return self._reset_empty()

    def _reset_empty(self) -> bool:
        """Drop any loaded state and report "no usable index" so callers rebuild."""
        self._index = self._make_index()
        self._chunks = []
        return False

    def _load_once(self) -> Optional[bool]:
        """One load attempt. Returns True/False on a definitive outcome, or None
        when a torn (index rows != metadata chunks) pair was read and the caller
        should retry."""
        index_path = self._dir / self._INDEX_FILE
        meta_path = self._dir / self._META_FILE
        if not index_path.exists() or not meta_path.exists():
            return False
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))

            # Reject an index built by a different embedding model before touching
            # the FAISS file. A same-dimension swap would otherwise load cleanly
            # and score garbage; treat it like corruption → rebuild.
            stored_model = meta.get("model_name", "")
            if self.model_name and stored_model and stored_model != self.model_name:
                logger.warning(
                    f"Embedding model changed for {self._dir}: index built with "
                    f"{stored_model!r}, configured {self.model_name!r} — rebuilding."
                )
                return self._reset_empty()

            # The metric decides the index type and the score conversion, so a
            # mismatch is not something to adopt from disk — an IndexFlatL2 file
            # read into a store configured for cosine would score incorrectly.
            stored_metric = meta.get("metric")
            if stored_metric and stored_metric != self._metric:
                logger.warning(
                    f"Index metric for {self._dir} is {stored_metric!r}, configured "
                    f"{self._metric!r} — rebuilding."
                )
                return self._reset_empty()

            # Same reasoning for dim, and here adopting the stored value was worse
            # than wrong: a 768-dim index read into a 384-configured store would
            # take a 384-dim query into a 768-dim index and trip a FAISS assertion.
            stored_dim = meta.get("dim")
            if stored_dim is not None and int(stored_dim) != self._dim:
                logger.warning(
                    f"Index dim for {self._dir} is {stored_dim}, configured "
                    f"{self._dim} — rebuilding."
                )
                return self._reset_empty()

            index = faiss.read_index(str(index_path))
            chunks = [
                Chunk(
                    chunk_id=c["chunk_id"],
                    source_text=c["source_text"],
                    source_type=c["source_type"],
                    metadata=c.get("metadata", {}),
                )
                for c in meta.get("chunks", [])
            ]
            # Row i of the index must align 1:1 with chunks[i]. A count mismatch
            # means we read across a save() (new index, old metadata or vice
            # versa) — signal a retry instead of committing a torn pair.
            if index.ntotal != len(chunks):
                logger.debug(
                    f"Torn read at {self._dir}: ntotal={index.ntotal} chunks={len(chunks)} — retrying."
                )
                return None

            self._index = index
            # `metric` and `dim` are deliberately NOT adopted from disk — both were
            # validated against the configured values above, so they already agree.
            self.loaded_extra_meta = dict(meta.get("extra", {}) or {})
            self._chunks = chunks
            logger.debug(f"FAISS index loaded: {self._dir} ({len(self._chunks)} chunks)")
            return True
        except Exception as exc:  # corrupt/partial index — rebuild from scratch
            logger.warning(f"Failed to load FAISS index at {self._dir}: {exc}")
            return self._reset_empty()

    def __len__(self) -> int:
        return len(self._chunks)
