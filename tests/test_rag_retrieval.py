"""RAG retrieval + grounding tests (Module 14, item 10).

Representative coverage:
  1. FAISS index build/query with MOCK embeddings — deterministic top-k ordering.
  2. Integration: /rag/generate-question path with a mocked LLM router, asserting
     the retrieved chunks are actually injected into the prompt the LLM sees.
  3. Regression: same resume+JD across a simulated multi-turn session must not
     repeat questions (diversity via asked_questions feedback).

Load-test note (documented, not executed): FaissVectorStore uses IndexFlatL2 —
exact brute-force search, correct and fast up to ~100k vectors per store. If a
company's doc corpus exceeds that, switch _make_index() to IndexIVFFlat (with a
trained coarse quantizer) to keep query latency bounded. `test_flat_index_is_exact`
pins the exact-search assumption so a silent swap to an approximate index fails CI.
"""

from __future__ import annotations

import numpy as np
import pytest

faiss = pytest.importorskip("faiss")

from app.services.rag.faiss_store import FaissVectorStore  # noqa: E402
from app.services.rag.vector_store import Chunk  # noqa: E402


# ───────────────────────── 1. FAISS build/query (mock embeddings) ───────────


def _chunk(cid: str) -> Chunk:
    return Chunk(chunk_id=cid, source_text=f"text-{cid}", source_type="resume")


def test_faiss_topk_ordering_with_mock_embeddings(tmp_path):
    """Nearest vector must rank first; ordering strictly by L2 distance."""
    dim = 4
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=dim)

    # Three basis-like vectors; query sits closest to 'b', then 'a', then 'c'.
    embeddings = [
        [1.0, 0.0, 0.0, 0.0],  # a
        [0.0, 1.0, 0.0, 0.0],  # b
        [0.0, 0.0, 1.0, 0.0],  # c
    ]
    store.add(embeddings, [_chunk("a"), _chunk("b"), _chunk("c")])

    query = [0.1, 0.9, 0.0, 0.0]  # closest to b
    hits = store.search(query, top_k=3)

    assert [h.chunk.chunk_id for h in hits] == ["b", "a", "c"]
    # Distances are non-decreasing (closest first).
    dists = [h.distance for h in hits]
    assert dists == sorted(dists)


def test_faiss_topk_respects_k(tmp_path):
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=3)
    store.add(
        [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0]],
        [_chunk(c) for c in "abcd"],
    )
    hits = store.search([1, 0, 0], top_k=2)
    assert len(hits) == 2  # never more than k
    assert hits[0].chunk.chunk_id == "a"  # exact match ranks first


def test_faiss_persist_roundtrip(tmp_path):
    d = tmp_path / "idx"
    store = FaissVectorStore(session_dir=d, dim=3)
    store.add([[1, 0, 0], [0, 1, 0]], [_chunk("a"), _chunk("b")])
    store.save()

    reloaded = FaissVectorStore(session_dir=d, dim=3)
    assert reloaded.load() is True
    assert len(reloaded) == 2
    assert reloaded.search([1, 0, 0], top_k=1)[0].chunk.chunk_id == "a"


def test_cosine_similarity_is_native_score(tmp_path):
    """Cosine store returns similarity directly from IndexFlatIP (0-1 range)."""
    store = FaissVectorStore(session_dir=tmp_path / "cos", dim=3, metric="cosine")
    store.add([[1.0, 0.0, 0.0]], [_chunk("a")])
    hit = store.search([2.0, 0.0, 0.0], top_k=1)[0]  # same direction, different magnitude
    assert hit.similarity == pytest.approx(1.0, abs=1e-4)  # cosine ignores magnitude


def test_flat_index_is_exact(tmp_path):
    """Pin the exact-search assumption behind the ~100k load-test note.

    IndexFlatL2 must return the true nearest neighbor for every query. If someone
    swaps in an approximate index (IndexIVFFlat) without a trained quantizer, this
    brute-force check would start missing exact matches — surfacing the tradeoff.
    """
    rng = np.random.default_rng(0)  # seeded — no wall-clock randomness
    vectors = rng.random((200, 8), dtype="float32")
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=8)
    store.add(vectors.tolist(), [_chunk(str(i)) for i in range(len(vectors))])

    for probe in (3, 57, 199):
        top = store.search(vectors[probe].tolist(), top_k=1)[0]
        assert top.chunk.chunk_id == str(probe)  # exact NN, always


# ───────────── 2. Integration: chunks are injected into the prompt ──────────


class _CapturingLLM:
    """Records the last user prompt so tests can assert on prompt contents."""

    def __init__(self, payload):
        self._payload = payload
        self.last_prompt = None
        self.last_system = None
        self.prompts: list[str] = []

    def generate_json(self, prompt, system_prompt=None, max_tokens=None):
        self.last_prompt = prompt
        self.last_system = system_prompt
        self.prompts.append(prompt)
        return self._payload


RESUME = (
    "Jane Doe\n"
    "Skills\nPython, FastAPI, Redis, Kafka.\n"
    "Experience\nBuilt a cursor-paginated feed service handling 10k rps.\n"
    "Projects\nDesigned an idempotent event-consumer pipeline.\n"
)


@pytest.fixture
def rag_env(tmp_path, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "RAG_INDEX_DIR", str(tmp_path / "rag_index"))
    monkeypatch.setattr(config.settings, "RAG_AUDIT_ENABLED", False)

    from app.services.rag_service import RAGService

    def make(payload):
        return RAGService(llm=_CapturingLLM(payload))

    return make


def test_generate_question_injects_retrieved_chunks_into_prompt(rag_env):
    pytest.importorskip("sentence_transformers")
    svc = rag_env(
        {"question": "Explain your cursor pagination.", "grounded_on": "feed service", "topic": "api"}
    )
    svc.build_session_index(
        candidate_id="c1", resume_text=RESUME,
        job_description="Backend role needing Kafka.", role="backend_engineer",
    )
    result = svc.generate_question(candidate_id="c1", role="backend_engineer", asked_questions=[])

    llm = svc._llm  # the capturing stub
    assert llm.last_prompt is not None
    # Every chunk reported as retrieved must appear verbatim in the prompt context.
    assert result["retrieved_chunks"], "expected retrieval to ground the question"
    for view in result["retrieved_chunks"]:
        snippet = view["text"][:60]
        assert snippet in llm.last_prompt, f"retrieved chunk not passed to LLM: {snippet!r}"


# ───────────── 3. Regression: multi-turn question diversity ─────────────────


def test_multi_turn_session_does_not_repeat_questions(rag_env):
    pytest.importorskip("sentence_transformers")

    # Each turn returns a distinct question; the service must forward the growing
    # asked_questions list into the prompt so the LLM is told what to avoid.
    scripted = [
        {"question": "Explain cursor pagination.", "topic": "pagination"},
        {"question": "How do you make consumers idempotent?", "topic": "idempotency"},
        {"question": "Describe your Redis caching strategy.", "topic": "caching"},
    ]

    from app.services.rag_service import RAGService

    class _SequenceLLM:
        def __init__(self, seq):
            self._seq = list(seq)
            self._i = 0
            self.prompts: list[str] = []

        def generate_json(self, prompt, system_prompt=None, max_tokens=None):
            self.prompts.append(prompt)
            item = self._seq[min(self._i, len(self._seq) - 1)]
            self._i += 1
            return item

    svc = RAGService(llm=_SequenceLLM(scripted))
    svc.build_session_index(
        candidate_id="c2", resume_text=RESUME, job_description="", role="backend_engineer"
    )

    asked: list[str] = []
    seen: set[str] = set()
    for _ in range(3):
        result = svc.generate_question(
            candidate_id="c2", role="backend_engineer", asked_questions=asked
        )
        q = result["question"]
        assert q not in seen, f"duplicate question generated: {q!r}"
        seen.add(q)
        asked.append(q)

    # From the 2nd turn on, the prompt must carry the prior questions as avoid-list.
    assert "Explain cursor pagination." in svc._llm.prompts[1]
    assert len(seen) == 3  # all distinct across the simulated session
