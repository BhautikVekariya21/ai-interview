"""Smoke tests for the RAG service.

Exercises real embedding + FAISS retrieval end-to-end, with the LLM router
stubbed so no network/provider calls are made. Skips automatically if the heavy
optional deps (faiss, sentence-transformers) aren't installed.
"""

from __future__ import annotations

import pytest

faiss = pytest.importorskip("faiss")
pytest.importorskip("sentence_transformers")

from app.services.rag_service import RAGService  # noqa: E402


class _StubLLM:
    """Deterministic stand-in for the multi-provider router."""

    def __init__(self, payload):
        self._payload = payload

    def generate_json(self, prompt, system_prompt=None, max_tokens=None):
        return self._payload


RESUME = (
    "Bhautik Vekariya\n"
    "Summary\nBackend engineer focused on high-throughput APIs.\n"
    "Skills\nPython, FastAPI, PostgreSQL, Kafka, Docker.\n"
    "Experience\nBuilt a payments API handling 10k requests/sec, cut p99 latency 40%.\n"
    "Projects\nDesigned a cursor-paginated feed service.\n"
)


@pytest.fixture(scope="module")
def service_factory(tmp_path_factory, monkeypatch_module):
    # Point the index dir at a temp location so tests don't touch real rag_index/.
    from app.core import config

    tmp = tmp_path_factory.mktemp("rag_index")
    monkeypatch_module.setattr(config.settings, "RAG_INDEX_DIR", str(tmp))
    # Disable audit writes so the test never touches the DB.
    monkeypatch_module.setattr(config.settings, "RAG_AUDIT_ENABLED", False)

    def make(payload):
        return RAGService(llm=_StubLLM(payload))

    return make


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    yield mp
    mp.undo()


def test_build_and_generate_question(service_factory):
    svc = service_factory(
        {"question": "Explain your cursor pagination design.", "grounded_on": "feed service", "topic": "api_design"}
    )
    count = svc.build_session_index(
        candidate_id="cand_test",
        resume_text=RESUME,
        job_description="Seeking a Python backend engineer with Kafka experience.",
        role="backend_engineer",
    )
    assert count >= 4  # preamble + skills + experience + projects + jd

    result = svc.generate_question(
        candidate_id="cand_test", role="backend_engineer", asked_questions=[]
    )
    assert result["question"] == "Explain your cursor pagination design."
    assert result["retrieved_chunks"]  # retrieval actually returned grounding
    assert len(result["retrieved_chunks"]) <= 3  # top_k respected


def test_generate_question_without_index_raises(service_factory):
    svc = service_factory({"question": "x"})
    with pytest.raises(ValueError):
        svc.generate_question(candidate_id="never_indexed", role="backend_engineer")


def test_evaluate_answer_uses_rubric(service_factory):
    svc = service_factory(
        {
            "score": 8,
            "justification": "Covered cursor pagination and consistency.",
            "criteria_met": ["cursor pagination"],
            "criteria_missed": ["page-size caps"],
        }
    )
    result = svc.evaluate_answer(
        question="How do you paginate a large dataset?",
        candidate_answer="Use keyset pagination with a stable cursor to avoid drift.",
        role="backend_engineer",
        candidate_id="cand_test",
    )
    assert result["score"] == 8
    assert 0 <= result["score"] <= 10
    assert result["rubric_snippets"]  # retrieved rubric context for justification


def test_score_is_clamped(service_factory):
    svc = service_factory({"score": 99, "justification": "", "criteria_met": [], "criteria_missed": []})
    result = svc.evaluate_answer(
        question="q", candidate_answer="a", role="backend_engineer"
    )
    assert result["score"] == 10  # clamped into 0-10


def test_detect_similarity_flags_near_duplicate(service_factory):
    svc = service_factory({"score": 5})
    answer = "Use keyset pagination with a stable cursor to avoid page drift under concurrent writes."
    # Record the same answer under a different candidate, then check a copy.
    svc.record_answer("backend_engineer", "How do you paginate?", answer, candidate_id="other_cand")
    result = svc.detect_similarity(
        answer=answer, role="backend_engineer", candidate_id="new_cand", threshold=0.9
    )
    assert result["flagged"] is True
    assert result["max_similarity"] >= 0.9
    assert result["violation"] is not None
    assert result["violation"]["type"] == "answer_similarity"


def test_detect_similarity_passes_original_answer(service_factory):
    svc = service_factory({"score": 5})
    result = svc.detect_similarity(
        answer="I once debugged a race condition in our billing worker by adding idempotency keys.",
        role="ml_engineer",
        candidate_id="unique_cand",
        threshold=0.9,
    )
    assert result["flagged"] is False
    assert result["violation"] is None


def test_adjust_difficulty_returns_valid_tier(service_factory):
    svc = service_factory({"recommended_difficulty": "hard", "reason": "Strong, complete answers."})
    result = svc.adjust_difficulty(
        role="backend_engineer",
        recent_answers=["Detailed answer about cursor pagination and consistency trade-offs."],
        current_difficulty="medium",
    )
    assert result["recommended_difficulty"] in ("easy", "medium", "hard", "expert")


def test_adjust_difficulty_defaults_when_llm_bad(service_factory):
    svc = service_factory({"recommended_difficulty": "impossible-tier"})
    result = svc.adjust_difficulty(
        role="backend_engineer", recent_answers=["something"], current_difficulty="medium"
    )
    assert result["recommended_difficulty"] == "medium"  # invalid tier falls back


def test_company_context_and_grounded_question(service_factory):
    svc = service_factory(
        {"question": "How would you use Kafka in our event pipeline?", "grounded_on": "Kafka", "topic": "streaming"}
    )
    svc.build_session_index(
        candidate_id="cand_co", resume_text=RESUME, job_description="", role="backend_engineer"
    )
    count = svc.add_company_docs(
        "acme", ["We run Kafka + Flink for streaming and require idempotent consumers."], role="backend_engineer"
    )
    assert count >= 1
    result = svc.generate_question(
        candidate_id="cand_co", role="backend_engineer", company_id="acme", difficulty="hard"
    )
    assert result["difficulty"] == "hard"
    assert result["question"]


def test_generate_report_grounds_on_qa(service_factory):
    svc = service_factory(
        {
            "summary": "Solid backend candidate.",
            "strengths": ["pagination"],
            "weaknesses": ["concurrency depth"],
            "per_question_notes": [{"question_number": 1, "note": "cited answer"}],
            "recommendation": "hire",
        }
    )
    result = svc.generate_report(
        session_id="sess_1",
        role="backend_engineer",
        qa_pairs=[
            {"question": "How do you paginate?", "answer": "Keyset pagination.", "score": 8},
            {"question": "Prevent a race condition?", "answer": "Row locks.", "score": 6},
        ],
        candidate_name="Test Candidate",
    )
    assert result["overall_score"] == 7.0  # (8 + 6) / 2
    assert result["recommendation"] == "hire"
    assert len(result["evidence"]) == 2  # per-question retrieved rubric evidence

