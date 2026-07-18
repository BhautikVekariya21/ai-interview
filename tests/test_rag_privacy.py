"""RAG privacy, isolation, and quality-eval tests (Module 14, items 12 & 13).

Covers:
  - Company FAISS namespaces are isolated per company_id — one company's docs can
    never surface in another company's retrieval (item 13, explicit isolation test).
  - Session (resume/JD) indices are scoped per candidate_id, not shared.
  - The audit log redacts raw query text to a hash + never persists source_text.
  - rag_eval metric helpers (precision@k, groundedness overlap, percentiles).
"""

from __future__ import annotations

import pytest

faiss = pytest.importorskip("faiss")

from app.services.rag import audit_log  # noqa: E402
from app.services.rag.rag_eval import (  # noqa: E402
    groundedness_overlap,
    percentiles,
    precision_at_k,
)


class _StubLLM:
    def __init__(self, payload):
        self._payload = payload

    def generate_json(self, prompt, system_prompt=None, max_tokens=None):
        return self._payload


RESUME = (
    "Sam Lee\nSkills\nPython, FastAPI, Kafka.\n"
    "Experience\nBuilt a streaming pipeline.\nProjects\nEvent-consumer service.\n"
)


@pytest.fixture
def svc_factory(tmp_path, monkeypatch):
    pytest.importorskip("sentence_transformers")
    from app.core import config
    from app.services.rag_service import RAGService

    monkeypatch.setattr(config.settings, "RAG_INDEX_DIR", str(tmp_path / "rag_index"))
    monkeypatch.setattr(config.settings, "RAG_AUDIT_ENABLED", False)

    def make(payload):
        return RAGService(llm=_StubLLM(payload))

    return make


# ─────────────────────── company namespace isolation ────────────────────────


def test_company_namespaces_are_isolated(svc_factory):
    """A doc uploaded under company 'acme' must never be retrievable through
    company 'globex' — the core multi-tenant leakage guard."""
    svc = svc_factory({"question": "q", "grounded_on": "x", "topic": "t"})

    svc.add_company_docs("acme", ["ACME uses a proprietary Rust trading core."], role="backend_engineer")
    svc.add_company_docs("globex", ["Globex runs a Java Spring monolith."], role="backend_engineer")

    acme_store = svc._load_company_store("acme")
    globex_store = svc._load_company_store("globex")
    assert acme_store is not None and globex_store is not None

    # Query with ACME's own secret term against Globex's store — must not match ACME.
    q = svc._embedder.embed_one("proprietary Rust trading core")
    globex_hits = globex_store.search(q, top_k=5)
    texts = " ".join(h.chunk.source_text for h in globex_hits).lower()
    assert "rust" not in texts and "acme" not in texts
    for h in globex_hits:
        assert h.chunk.metadata.get("company_id") == "globex"


def test_company_store_absent_for_unknown_id(svc_factory):
    svc = svc_factory({"question": "q"})
    svc.add_company_docs("acme", ["ACME internal standards doc."])
    assert svc._load_company_store("never_uploaded") is None


def test_generated_question_only_grounds_on_matching_company(svc_factory):
    """generate_question(company_id=...) must fold in only that company's docs."""
    svc = svc_factory({"question": "How do you use Kafka here?", "grounded_on": "Kafka", "topic": "streaming"})
    svc.build_session_index(candidate_id="cand", resume_text=RESUME, job_description="", role="backend_engineer")
    svc.add_company_docs("acme", ["ACME_SECRET_TOKEN: uses Flink for streaming joins."], role="backend_engineer")
    svc.add_company_docs("globex", ["GLOBEX_SECRET_TOKEN: uses Spark."], role="backend_engineer")

    out = svc.generate_question(candidate_id="cand", role="backend_engineer", company_id="globex")
    retrieved_text = " ".join(c["text"] for c in out["retrieved_chunks"])
    assert "ACME_SECRET_TOKEN" not in retrieved_text


# ─────────────────────── session (candidate) isolation ──────────────────────


def test_session_indices_are_per_candidate(svc_factory):
    svc = svc_factory({"question": "q", "grounded_on": "x", "topic": "t"})
    svc.build_session_index(candidate_id="cand_a", resume_text=RESUME, job_description="", role="backend_engineer")
    # cand_b was never indexed → retrieval path must refuse, not read cand_a's data.
    with pytest.raises(ValueError):
        svc.generate_question(candidate_id="cand_b", role="backend_engineer")


# ─────────────────────────── audit log PII redaction ────────────────────────


def test_audit_query_is_redacted_to_hash():
    raw = "John Smith, john@example.com, prior employer: Acme Corp"
    redacted = audit_log._redact_query(raw)
    assert redacted.startswith("sha256:")
    assert "John Smith" not in redacted
    assert "example.com" not in redacted
    assert f"len={len(raw)}" in redacted
    # Deterministic: same input → same hash (lets us correlate without plaintext).
    assert redacted == audit_log._redact_query(raw)


# ─────────────────────────── eval metric helpers ────────────────────────────


def test_precision_at_k():
    retrieved = ["a", "b", "c"]
    relevant = frozenset({"a", "c"})
    assert precision_at_k(retrieved, relevant, k=3) == pytest.approx(2 / 3)
    assert precision_at_k(retrieved, relevant, k=1) == 1.0  # top hit is relevant
    assert precision_at_k([], relevant, k=3) == 0.0


def test_groundedness_overlap():
    ctx = ["cursor pagination keeps the feed stable under concurrent writes"]
    grounded = "Explain your cursor pagination strategy for the feed."
    ignored = "What is your favorite programming philosophy overall?"
    assert groundedness_overlap(ctx, grounded) > groundedness_overlap(ctx, ignored)
    assert groundedness_overlap(ctx, "") == 0.0


def test_percentiles_monotonic():
    p = percentiles([0.1, 0.2, 0.3, 0.4, 1.0])
    assert p["p50"] <= p["p95"] <= p["p99"]
    assert percentiles([])["p50"] == 0.0
