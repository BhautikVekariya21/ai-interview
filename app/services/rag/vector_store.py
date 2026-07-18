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
    """A search hit: the stored chunk plus its distance (lower = closer).

    `score` optionally carries a backend-native similarity (e.g. cosine from an
    inner-product index) when it is known directly; otherwise similarity is
    derived from the L2 distance.
    """

    chunk: Chunk
    distance: float
    score: Optional[float] = None

    @property
    def similarity(self) -> float:
        """0-1 similarity. Uses the native score when present, else derives from L2 distance."""
        if self.score is not None:
            return round(float(self.score), 4)
        return round(1.0 / (1.0 + self.distance), 4)


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
