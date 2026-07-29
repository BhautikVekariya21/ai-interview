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

Scoring note: both index types operate on unit-normalized vectors (see
FaissVectorStore._prepare), so L2 ranking is identical to cosine ranking and
`similarity` is a true cosine in [0, 1] under either metric.
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
    """Nearest vector must rank first; ordering by cosine (L2 on unit vectors)."""
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


# ─────────── 1b. Score correctness: similarity must be a true cosine ─────────
#
# Regression tests for the squared-L2 bug: FAISS IndexFlatL2 returns d², not d,
# and similarity was computed as 1/(1+d²). That gave a floor of 0.2, scored an
# orthogonal chunk 0.333, and made the value impossible to threshold.


def _cosine(u, v) -> float:
    u, v = np.asarray(u, dtype="float64"), np.asarray(v, dtype="float64")
    return float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)))


def test_l2_similarity_equals_true_cosine(tmp_path):
    """similarity from an l2 store must equal the true cosine, not 1/(1+d²)."""
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=3)
    vectors = [[1.0, 0.5, 0.0], [0.2, 1.0, 0.3], [0.0, 0.1, 1.0]]
    store.add(vectors, [_chunk(c) for c in "abc"])

    query = [0.9, 0.4, 0.1]
    for hit in store.search(query, top_k=3):
        expected = _cosine(vectors["abc".index(hit.chunk.chunk_id)], query)
        assert hit.similarity == pytest.approx(expected, abs=1e-4)


def test_l2_and_cosine_stores_agree_on_similarity(tmp_path):
    """The same vectors indexed under either metric must score identically."""
    vectors = [[1.0, 0.5, 0.0], [0.2, 1.0, 0.3], [0.0, 0.1, 1.0]]
    query = [0.9, 0.4, 0.1]

    l2 = FaissVectorStore(session_dir=tmp_path / "l2", dim=3, metric="l2")
    cos = FaissVectorStore(session_dir=tmp_path / "cos", dim=3, metric="cosine")
    for store in (l2, cos):
        store.add(vectors, [_chunk(c) for c in "abc"])

    l2_scores = {h.chunk.chunk_id: h.similarity for h in l2.search(query, top_k=3)}
    cos_scores = {h.chunk.chunk_id: h.similarity for h in cos.search(query, top_k=3)}
    for cid, score in l2_scores.items():
        assert score == pytest.approx(cos_scores[cid], abs=1e-4)


def test_orthogonal_chunk_scores_zero(tmp_path):
    """An unrelated (orthogonal) chunk must score 0.0 — it scored 0.333 before."""
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=3)
    store.add([[0.0, 1.0, 0.0]], [_chunk("orthogonal")])
    hit = store.search([1.0, 0.0, 0.0], top_k=1)[0]
    assert hit.similarity == pytest.approx(0.0, abs=1e-4)


def test_antipodal_chunk_clamps_to_zero(tmp_path):
    """cosine keeps the raw -1 for ordering; similarity clamps to the 0-1 API contract."""
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=3)
    store.add([[-1.0, 0.0, 0.0]], [_chunk("opposite")])
    hit = store.search([1.0, 0.0, 0.0], top_k=1)[0]
    assert hit.cosine == pytest.approx(-1.0, abs=1e-4)
    assert hit.similarity == 0.0


def test_distance_is_true_euclidean_not_squared(tmp_path):
    """distance must be the true Euclidean distance; it used to be its square."""
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=3)
    store.add([[0.0, 1.0, 0.0]], [_chunk("orthogonal")])
    hit = store.search([1.0, 0.0, 0.0], top_k=1)[0]
    # Unit-norm orthogonal vectors are sqrt(2) apart; the squared value was 2.0.
    assert hit.distance == pytest.approx(np.sqrt(2.0), abs=1e-4)


def test_l2_similarity_is_scale_invariant(tmp_path):
    """Proves _prepare normalizes for l2 too: query magnitude must not matter."""
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=3)
    store.add([[1.0, 0.0, 0.0]], [_chunk("a")])
    assert store.search([1.0, 0.0, 0.0], top_k=1)[0].similarity == pytest.approx(1.0, abs=1e-4)
    assert store.search([9.0, 0.0, 0.0], top_k=1)[0].similarity == pytest.approx(1.0, abs=1e-4)


def test_prepare_does_not_mutate_caller_array(tmp_path):
    """_prepare normalizes in place; it must copy first.

    np.ascontiguousarray returns a *view* for already-contiguous float32 input,
    so the old implementation rescaled the caller's buffer. Masked in production
    only because every caller happens to pass a Python list.
    """
    store = FaissVectorStore(session_dir=tmp_path / "idx", dim=3)
    vectors = np.array([[3.0, 4.0, 0.0]], dtype="float32", order="C")
    original = vectors.copy()

    store.add(vectors, [_chunk("a")])
    assert np.array_equal(vectors, original), "add() mutated the caller's array"

    query = np.array([3.0, 4.0, 0.0], dtype="float32", order="C")
    query_original = query.copy()
    store.search(query, top_k=1)
    assert np.array_equal(query, query_original), "search() mutated the caller's array"


def test_embedder_output_is_unit_norm():
    """Unit-norm output is a contract every score depends on, not a model accident."""
    pytest.importorskip("sentence_transformers")
    from app.services.rag.embedder import get_embedder

    vectors = np.asarray(get_embedder().embed(["hello world", "a much longer sentence here"]))
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)



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


# ───────────── 4. Relevance floor: drop noise, never return empty ───────────


def _floor_hits():
    """Three hits spanning the measured range: good (~0.40), weak, noise (~0.07)."""
    from app.services.rag.vector_store import RetrievedChunk

    return [
        RetrievedChunk(chunk=_chunk("good"), distance=0.0, score=0.42),
        RetrievedChunk(chunk=_chunk("weak"), distance=0.0, score=0.17),
        RetrievedChunk(chunk=_chunk("noise"), distance=0.0, score=0.07),
    ]


def test_relevance_floor_drops_low_similarity_chunks():
    from app.services.rag_service import _apply_relevance_floor

    kept = _apply_relevance_floor(_floor_hits(), 0.25, 1, "test")
    assert [rc.chunk.chunk_id for rc in kept] == ["good"]


def test_relevance_floor_keeps_best_hit_when_all_below():
    """Never return empty: losing grounding entirely is worse than a weak match."""
    from app.services.rag_service import _apply_relevance_floor

    kept = _apply_relevance_floor(_floor_hits(), 0.99, 1, "test")
    assert [rc.chunk.chunk_id for rc in kept] == ["good"]  # closest-first survivor


def test_relevance_floor_can_return_empty_when_min_results_zero():
    from app.services.rag_service import _apply_relevance_floor

    assert _apply_relevance_floor(_floor_hits(), 0.99, 0, "test") == []


def test_relevance_floor_disabled_at_zero():
    from app.services.rag_service import _apply_relevance_floor

    assert len(_apply_relevance_floor(_floor_hits(), 0.0, 1, "test")) == 3


def test_generate_question_still_grounded_under_floor(rag_env, monkeypatch):
    """An impossible floor must not collapse generate_question into its fallback."""
    pytest.importorskip("sentence_transformers")
    from app.core import config

    monkeypatch.setattr(config.settings, "RAG_MIN_SIMILARITY", 0.99)
    monkeypatch.setattr(config.settings, "RAG_MIN_RESULTS", 1)

    svc = rag_env({"question": "Explain your cursor pagination.", "topic": "api"})
    svc.build_session_index(candidate_id="c3", resume_text=RESUME, role="backend_engineer")
    result = svc.generate_question(candidate_id="c3", role="backend_engineer", asked_questions=[])

    assert len(result["retrieved_chunks"]) == 1  # floor applied, but not to zero
    assert result["question"] == "Explain your cursor pagination."  # LLM's, not the fallback

