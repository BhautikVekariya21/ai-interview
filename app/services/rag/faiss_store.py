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
- ``metadata.json`` stamps the embedding ``model_name`` and an optional
  ``extra`` bag (e.g. the seed-file hash). ``load()`` rejects an index whose
  stored model name differs from the configured one — a same-dimension model
  swap would otherwise load silently and return geometrically meaningless
  similarity scores. A rejected load behaves like a corrupt one: it resets to
  empty and returns False so the caller rebuilds.
"""

from __future__ import annotations

import json
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

    Supports two metrics:
      - "l2"     : IndexFlatL2, raw Euclidean distance (default; resume/JD retrieval).
      - "cosine" : IndexFlatIP over L2-normalized vectors, so inner product == cosine
                   similarity. Used for near-duplicate answer detection where a true
                   cosine threshold (e.g. >0.9) is required.

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
        """Normalize for cosine; pass through for L2. FAISS mutates in place, so copy."""
        matrix = np.ascontiguousarray(matrix, dtype="float32")
        if self._metric == "cosine":
            faiss.normalize_L2(matrix)
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
                # IndexFlatIP over normalized vectors returns cosine similarity directly.
                results.append(
                    RetrievedChunk(chunk=self._chunks[idx], distance=float(1.0 - raw), score=float(raw))
                )
            else:
                results.append(RetrievedChunk(chunk=self._chunks[idx], distance=float(raw)))
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
        corrupt, or was built by a different embedding model than the one
        currently configured — in every case the caller rebuilds from source.

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
                self._index = self._make_index()
                self._chunks = []
                return False

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
            self._dim = int(meta.get("dim", self._dim))
            self._metric = meta.get("metric", self._metric)
            self.loaded_extra_meta = dict(meta.get("extra", {}) or {})
            self._chunks = chunks
            logger.debug(f"FAISS index loaded: {self._dir} ({len(self._chunks)} chunks)")
            return True
        except Exception as exc:  # corrupt/partial index — rebuild from scratch
            logger.warning(f"Failed to load FAISS index at {self._dir}: {exc}")
            self._index = self._make_index()
            self._chunks = []
            return False

    def __len__(self) -> int:
        return len(self._chunks)
