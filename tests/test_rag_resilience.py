"""RAG resilience tests (failure-mode audit remediation).

Covers the four confirmed risks fixed in the audit follow-up:

  1. Concurrency — concurrent save()/record_answer() on one namespace never
     corrupts the index (atomic replace) and never loses appended answers
     (process-safe namespace lock serializes the load-modify-save cycle).
  2. Seed staleness — changing the seed file's content changes its sha256, so
     the _reference_bank / _canned indices auto-rebuild instead of serving stale
     rubric data (no manual cache clear).
  3. Model versioning — an index stamped with a different embedding model name is
     rejected on load() (like a dimension mismatch) and rebuilt, so a
     same-dimension model swap can't silently score garbage.
  4. Unscored aggregation — an LLM-outage answer is returned as unscored (score
     None), and generate_report excludes it from the average instead of counting
     it as 0, surfacing the count.

Tests 2/4 exercise the real embedder (skipped if sentence_transformers is
absent); tests 1/3 use mock embeddings and run without it.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import numpy as np
import pytest

faiss = pytest.importorskip("faiss")

from app.services.rag.faiss_store import FaissVectorStore, namespace_lock  # noqa: E402
from app.services.rag.vector_store import Chunk  # noqa: E402


def _chunk(cid: str) -> Chunk:
    return Chunk(chunk_id=cid, source_text=f"text-{cid}", source_type="past_answer")


# ───────────────────────────── 1. Concurrency ───────────────────────────────


def test_atomic_save_leaves_no_temp_files(tmp_path):
    """save() writes via temp+os.replace — no .tmp residue, both files present."""
    d = tmp_path / "idx"
    store = FaissVectorStore(session_dir=d, dim=3)
    store.add([[1, 0, 0], [0, 1, 0]], [_chunk("a"), _chunk("b")])
    store.save()

    files = {p.name for p in d.iterdir()}
    assert "index.faiss" in files
    assert "metadata.json" in files
    assert not [f for f in files if f.endswith(".tmp")], f"temp files leaked: {files}"


def test_concurrent_reads_during_repeated_saves_never_tear(tmp_path):
    """A reader loading while a writer repeatedly re-saves must always see a
    consistent index/metadata pair — never a half-written index (which would
    raise) or a chunk/metadata length mismatch."""
    d = tmp_path / "idx"
    writer_store = FaissVectorStore(session_dir=d, dim=3)
    writer_store.add([[1, 0, 0], [0, 1, 0]], [_chunk("a"), _chunk("b")])
    writer_store.save()  # ensure an initial valid pair exists

    errors: list[str] = []
    stop = threading.Event()

    def writer():
        for i in range(40):
            s = FaissVectorStore(session_dir=d, dim=3)
            s.add(
                [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                [_chunk("a"), _chunk("b"), _chunk(f"c{i}")],
            )
            with namespace_lock(d):
                s.save()
        stop.set()

    def reader():
        while not stop.is_set():
            r = FaissVectorStore(session_dir=d, dim=3)
            if r.load():
                # index row count must equal metadata chunk count — the invariant
                # a torn write would break.
                if r._index.ntotal != len(r._chunks):
                    errors.append(f"torn: ntotal={r._index.ntotal} chunks={len(r._chunks)}")

    threads = [threading.Thread(target=writer)] + [
        threading.Thread(target=reader) for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, errors[:5]


def test_concurrent_record_answer_does_not_lose_updates(tmp_path, monkeypatch):
    """Many threads appending answers for the same role must all be persisted —
    the namespace lock serializes the load-modify-save so none are lost."""
    pytest.importorskip("sentence_transformers")
    from app.core import config

    monkeypatch.setattr(config.settings, "RAG_INDEX_DIR", str(tmp_path / "rag_index"))
    monkeypatch.setattr(config.settings, "RAG_AUDIT_ENABLED", False)

    from app.services.rag_service import RAGService

    svc = RAGService(llm=object())  # llm unused by record_answer
    role = "backend_engineer"
    n = 16

    def append(i: int):
        svc.record_answer(
            role=role,
            question=f"q{i}",
            answer=f"This is a sufficiently long unique candidate answer number {i} about systems.",
            candidate_id=f"cand-{i}",
        )

    threads = [threading.Thread(target=append, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    # Reload the persisted answer index and count — all n appends must survive.
    store = FaissVectorStore(
        session_dir=Path(config.settings.RAG_INDEX_DIR) / "_answers" / role,
        dim=svc.dim,
        metric="cosine",
    )
    assert store.load() is True
    assert len(store) == n, f"expected {n} answers persisted, found {len(store)}"


# ─────────────────────────── 2. Seed staleness ──────────────────────────────


def test_seed_hash_change_triggers_reference_rebuild(tmp_path, monkeypatch):
    pytest.importorskip("sentence_transformers")
    from app.core import config

    seed_path = tmp_path / "seed.json"
    seed_v1 = {
        "backend_engineer": [
            {
                "topic": "caching",
                "question": "What is a cache?",
                "reference_answer": "A fast store for hot data.",
                "rubric": "10: correct. 3: wrong.",
            }
        ]
    }
    seed_path.write_text(json.dumps(seed_v1), encoding="utf-8")

    monkeypatch.setattr(config.settings, "RAG_INDEX_DIR", str(tmp_path / "rag_index"))
    monkeypatch.setattr(config.settings, "RAG_SEED_DATA_PATH", str(seed_path))
    monkeypatch.setattr(config.settings, "RAG_AUDIT_ENABLED", False)

    from app.services.rag_service import RAGService

    svc1 = RAGService(llm=object())
    store1 = svc1._reference_bank_store()
    count_v1 = len(store1)
    assert count_v1 == 1

    # Expand the seed and confirm the stamped hash reflects the new content.
    seed_v2 = {
        "backend_engineer": seed_v1["backend_engineer"]
        + [
            {
                "topic": "concurrency",
                "question": "What is a race condition?",
                "reference_answer": "Two operations interleaving unsafely.",
                "rubric": "10: locking. 3: none.",
            },
            {
                "topic": "apis",
                "question": "What is idempotency?",
                "reference_answer": "Same result on repeat.",
                "rubric": "10: keys. 3: none.",
            },
        ]
    }
    seed_path.write_text(json.dumps(seed_v2), encoding="utf-8")

    # Fresh service (no in-memory cache) must detect the hash mismatch on load and
    # rebuild from the new seed rather than serving the stale 1-entry index.
    svc2 = RAGService(llm=object())
    store2 = svc2._reference_bank_store()
    assert len(store2) == 3, "reference bank did not auto-rebuild after seed change"

    meta = json.loads(
        (Path(config.settings.RAG_INDEX_DIR) / "_reference_bank" / "metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["extra"]["seed_hash"] == svc2._seed_hash()


# ───────────────────────── 3. Model version stamp ───────────────────────────


def test_model_name_mismatch_rejects_load(tmp_path):
    """An index built by a different (same-dim) model is rejected → caller rebuilds."""
    d = tmp_path / "idx"
    built = FaissVectorStore(session_dir=d, dim=3, model_name="old-model-v1")
    built.add([[1, 0, 0], [0, 1, 0]], [_chunk("a"), _chunk("b")])
    built.save()

    # Same dimension, different model name — must NOT load (returns False, empty).
    reopened = FaissVectorStore(session_dir=d, dim=3, model_name="new-model-v2")
    assert reopened.load() is False
    assert len(reopened) == 0

    # Same model name — loads normally.
    same = FaissVectorStore(session_dir=d, dim=3, model_name="old-model-v1")
    assert same.load() is True
    assert len(same) == 2


def test_model_name_stamped_in_metadata(tmp_path):
    d = tmp_path / "idx"
    store = FaissVectorStore(session_dir=d, dim=3, model_name="all-MiniLM-L6-v2")
    store.add([[1, 0, 0]], [_chunk("a")])
    store.save()
    meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
    assert meta["model_name"] == "all-MiniLM-L6-v2"


def test_dim_mismatch_rejects_load(tmp_path):
    """A stored index of a different dimension must be rejected, not adopted.

    load() used to do `self._dim = int(meta.get("dim", self._dim))`, silently
    adopting the stored dimension. A 768-dim index read into a 384-configured
    store would then take a 384-dim query into a 768-dim index and trip a FAISS
    assertion, so the mismatch has to fail closed and let the caller rebuild.
    """
    d = tmp_path / "idx"
    built = FaissVectorStore(session_dir=d, dim=4, model_name="m")
    built.add([[1, 0, 0, 0]], [_chunk("a")])
    built.save()

    reopened = FaissVectorStore(session_dir=d, dim=3, model_name="m")
    assert reopened.load() is False
    assert len(reopened) == 0

    same = FaissVectorStore(session_dir=d, dim=4, model_name="m")
    assert same.load() is True
    assert len(same) == 1


def test_metric_mismatch_rejects_load(tmp_path):
    """A metric change must be rejected, not adopted from metadata.

    load() used to do `self._metric = meta.get("metric", self._metric)`, so an
    index persisted as "l2" reopened as a cosine store silently reverted to l2
    and returned L2-derived scores the caller would read as native cosine.
    """
    d = tmp_path / "idx"
    built = FaissVectorStore(session_dir=d, dim=3, model_name="m", metric="l2")
    built.add([[1, 0, 0], [0, 1, 0]], [_chunk("a"), _chunk("b")])
    built.save()

    reopened = FaissVectorStore(session_dir=d, dim=3, model_name="m", metric="cosine")
    assert reopened.load() is False
    assert len(reopened) == 0

    same = FaissVectorStore(session_dir=d, dim=3, model_name="m", metric="l2")
    assert same.load() is True
    assert len(same) == 2


def test_metric_and_format_version_stamped_in_metadata(tmp_path):
    d = tmp_path / "idx"
    store = FaissVectorStore(session_dir=d, dim=3, model_name="m", metric="cosine")
    store.add([[1, 0, 0]], [_chunk("a")])
    store.save()
    meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
    assert meta["metric"] == "cosine"
    assert meta["format_version"] == 2


# ─────────────────────── 4. Unscored aggregation ────────────────────────────


class _FailLLM:
    """Simulates all providers down — generate_json always returns None."""

    def generate_json(self, prompt, system_prompt=None, max_tokens=None):
        return None


@pytest.fixture
def rag_env(tmp_path, monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "RAG_INDEX_DIR", str(tmp_path / "rag_index"))
    monkeypatch.setattr(config.settings, "RAG_AUDIT_ENABLED", False)
    from app.services.rag_service import RAGService

    def make(llm):
        return RAGService(llm=llm)

    return make


def test_evaluate_answer_outage_returns_unscored_not_zero(rag_env):
    pytest.importorskip("sentence_transformers")
    svc = rag_env(_FailLLM())
    result = svc.evaluate_answer(
        question="Explain idempotency.",
        candidate_answer="It means repeating an operation has the same effect as doing it once.",
        role="backend_engineer",
        candidate_id="c-outage",
    )
    assert result["score"] is None
    assert result["unscored"] is True
    assert "manual review" in result["justification"].lower()


def test_report_excludes_unscored_from_average(rag_env):
    pytest.importorskip("sentence_transformers")
    svc = rag_env(_FailLLM())  # report LLM also down → falls back, aggregation still runs

    qa_pairs = [
        {"question": "q1", "answer": "a1", "score": 8},
        {"question": "q2", "answer": "a2", "score": 6},
        # LLM-outage answer: explicitly unscored — must NOT count as 0.
        {"question": "q3", "answer": "a3", "score": None, "unscored": True},
    ]
    report = svc.generate_report(
        session_id="s1", role="backend_engineer", qa_pairs=qa_pairs, candidate_name="Test"
    )
    # Average of 8 and 6 only → 7.0, NOT (8+6+0)/3 ≈ 4.67.
    assert report["overall_score"] == pytest.approx(7.0)
    assert report["scored_count"] == 2
    assert report["unscored_count"] == 1


def test_report_all_unscored_yields_none_overall(rag_env):
    pytest.importorskip("sentence_transformers")
    svc = rag_env(_FailLLM())
    qa_pairs = [
        {"question": "q1", "answer": "a1", "score": None, "unscored": True},
        {"question": "q2", "answer": "a2", "score": None, "unscored": True},
    ]
    report = svc.generate_report(session_id="s2", role="backend_engineer", qa_pairs=qa_pairs)
    assert report["overall_score"] is None
    assert report["scored_count"] == 0
    assert report["unscored_count"] == 2
