"""Role vocabulary normalization (rag/roles.py).

The parser and the reference bank use disjoint role vocabularies — the parser
emits domains like "backend"/"ml_ai", the seed bank is keyed
"backend_engineer"/"ml_engineer". Comparing them directly matched nothing, so
every answer was graded against an arbitrary role's rubric instead of its own.
These tests pin the mapping that closes that gap.
"""

from __future__ import annotations

import pytest

from app.services.rag.roles import CANONICAL_ROLES, normalize_role


@pytest.mark.parametrize(
    "domain,expected",
    [
        # Every domain ResumeParser._infer_domain can return.
        ("backend", "backend_engineer"),
        ("frontend", "frontend_engineer"),
        ("devops", "devops_engineer"),
        ("ml_ai", "ml_engineer"),
        ("data_science", "data_scientist"),
        # No dedicated bank section — mapped to the nearest available rubric.
        ("fullstack", "backend_engineer"),
        ("mobile", "frontend_engineer"),
    ],
)
def test_parser_domains_map_to_bank_roles(domain, expected):
    assert normalize_role(domain) == expected


@pytest.mark.parametrize("canonical", sorted(CANONICAL_ROLES))
def test_canonical_roles_pass_through(canonical):
    """Values already in the bank's vocabulary must survive unchanged."""
    assert normalize_role(canonical) == canonical


@pytest.mark.parametrize(
    "spelling,expected",
    [
        ("Backend", "backend_engineer"),
        ("  BACKEND  ", "backend_engineer"),
        ("data-science", "data_scientist"),
        ("Data Science", "data_scientist"),
        ("ML/AI".replace("/", "_"), "ml_engineer"),
        ("Senior Backend Engineer", "backend_engineer"),
        ("full-stack", "backend_engineer"),
    ],
)
def test_spelling_and_separator_variants(spelling, expected):
    assert normalize_role(spelling) == expected


def test_data_science_wins_over_data_substring():
    """Longest-alias-first: 'data_science' must not be shadowed by 'data'."""
    assert normalize_role("data_science") == "data_scientist"
    assert normalize_role("data science engineer") == "data_scientist"


@pytest.mark.parametrize("decorated", ["html_developer", "xml_specialist", "html"])
def test_short_aliases_do_not_match_mid_token(decorated):
    """The 'ml' alias must not fire on words that merely contain 'ml'.

    Matching is on underscore token boundaries; a raw substring test would map
    "html_developer" to ml_engineer.
    """
    assert normalize_role(decorated) != "ml_engineer"


@pytest.mark.parametrize("unmappable", ["", "   ", None, "software engineering", "chef", "sales"])
def test_unmappable_roles_return_none(unmappable):
    """None means 'do not filter by role' — a deliberate, logged decision.

    "software engineering" is the app-wide default when the parser infers no
    domain; it names no particular rubric, so guessing one would be worse than
    retrieving across all of them.
    """
    assert normalize_role(unmappable) is None


def test_every_mapping_target_exists_in_the_bank():
    """Guard against a mapping pointing at a role the seed bank does not define."""
    import json
    from pathlib import Path

    from app.core.config import settings

    bank = json.loads(Path(settings.RAG_SEED_DATA_PATH).read_text(encoding="utf-8"))
    assert CANONICAL_ROLES == frozenset(bank), "CANONICAL_ROLES drifted from the seed bank keys"


def test_role_filter_selects_matching_rubrics():
    """_role_filtered must narrow to the normalized role rather than no-op."""
    from app.services.rag.vector_store import Chunk, RetrievedChunk
    from app.services.rag_service import _role_filtered

    def hit(role: str) -> RetrievedChunk:
        return RetrievedChunk(
            chunk=Chunk(
                chunk_id=f"ref:{role}",
                source_text=f"{role} rubric",
                source_type="reference_qa",
                metadata={"role": role},
            ),
            distance=0.0,
            score=0.5,
        )

    retrieved = [hit("data_scientist"), hit("backend_engineer"), hit("ml_engineer")]

    # Parser emits "backend"; the bank stores "backend_engineer".
    kept = _role_filtered(retrieved, "backend")
    assert [rc.chunk.metadata["role"] for rc in kept] == ["backend_engineer"]

    # Unmappable role keeps the full cross-role set rather than dropping to empty.
    assert _role_filtered(retrieved, "software engineering") == retrieved

    # Mappable role with no matching rubric among the hits falls back cross-role
    # rather than returning nothing.
    only_ds = [hit("data_scientist")]
    assert _role_filtered(only_ds, "backend") == only_ds


def test_evaluate_answer_retrieves_role_correct_rubrics(tmp_path, monkeypatch):
    """End-to-end: a parser domain must reach the matching reference-bank rubrics.

    Covers the whole chain — over-fetch a wider pool, normalize "backend" to
    "backend_engineer", narrow to it, trim to RAG_TOP_K. Before the fix every
    rubric snippet came from an arbitrary role.
    """
    pytest.importorskip("sentence_transformers")
    from app.core import config

    monkeypatch.setattr(config.settings, "RAG_INDEX_DIR", str(tmp_path / "rag_index"))
    monkeypatch.setattr(config.settings, "RAG_AUDIT_ENABLED", False)

    from app.services.rag_service import RAGService

    class _StubLLM:
        def generate_json(self, prompt, system_prompt=None, max_tokens=None):
            return {"score": 7, "justification": "ok", "criteria_met": [], "criteria_missed": []}

    svc = RAGService(llm=_StubLLM())
    result = svc.evaluate_answer(
        question="How would you design an idempotent payment API?",
        candidate_answer="Use an idempotency key stored with the request hash.",
        role="backend",  # parser vocabulary, NOT the bank's "backend_engineer"
        candidate_id="role-test",
    )

    snippets = result["rubric_snippets"]
    assert snippets, "expected rubric grounding"
    roles = {s["chunk_id"].split(":")[1] for s in snippets}
    assert roles == {"backend_engineer"}, f"expected only backend_engineer rubrics, got {roles}"
