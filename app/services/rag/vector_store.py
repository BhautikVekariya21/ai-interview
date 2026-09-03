"""Vector store abstraction.

Defines the retrieval interface the RAG service codes against so the concrete
backend (FAISS today; pgvector / Qdrant later) can be swapped without touching
callers. Only this interface — add(), search(), save(), load() — is contractual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence


@dataclass(frozen=True)
class Chunk:
    """A single indexed unit of text plus its provenance metadata."""

    chunk_id: str
    source_text: str
    source_type: str  # "resume" | "job_description" | "reference_qa" | "answer"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    """A search hit: the stored chunk plus how close it was to the query.

    `distance` is the true Euclidean distance between unit-norm vectors, so it
    lies in [0, 2] and means the same thing for every metric (lower = closer).
    `score` carries the backend-native cosine in [-1, 1] when the backend knows
    it directly; `FaissVectorStore` always populates it.
    """

    chunk: Chunk
    distance: float
    score: Optional[float] = None

    @property
    def cosine(self) -> float:
        """Raw cosine in [-1, 1] — unrounded and unclamped.

        Use this for sorting and comparisons, where negative values must stay
        ordered relative to each other. `similarity` clamps them all to 0.0 and
        would make the order among anti-correlated hits arbitrary.
        """
        if self.score is not None:
            return float(self.score)
        # Fallback for a backend that reports only a distance: invert the unit
        # sphere identity ||a-b||^2 = 2 - 2*cos.
        return 1.0 - (float(self.distance) ** 2) / 2.0

    @property
    def similarity(self) -> float:
        """Interpretable 0-1 relevance: the cosine clamped to [0, 1].

        A negative cosine means anti-correlated, i.e. irrelevant, so it clamps to
        0.0 — 0 genuinely means "no relevance". The clamp is also a hard API
        requirement: `RetrievalChunk.similarity` is declared `ge=0.0, le=1.0`
        (app/schemas/rag_schemas.py), so an unclamped value would fail validation.
        """
        return round(min(1.0, max(0.0, self.cosine)), 4)


class VectorStore(Protocol):
    """Backend-agnostic retrieval contract.

    Implementations own their embedding dimension and persistence format. The
    RAG service depends only on these four methods, so swapping FAISS for
    pgvector/Qdrant means writing a new class — not editing retrieval code.
    """

    def add(self, embeddings: Sequence[Sequence[float]], chunks: Sequence[Chunk]) -> None:
        """Index `embeddings` aligned 1:1 with `chunks`."""

    def search(self, embedding: Sequence[float], top_k: int) -> List[RetrievedChunk]:
        """Return up to `top_k` nearest chunks to `embedding`, closest first."""

    def save(self) -> None:
        """Persist the index + metadata to durable storage."""

    def load(self) -> bool:
        """Load a previously persisted index. Returns False if none exists."""

    def __len__(self) -> int:
        ...
