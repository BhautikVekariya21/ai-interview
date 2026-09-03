"""Tests for the Company Lens service.

Hermetic by design: the LLM is replaced with a fake and the scorecard fallback
is exercised with ``evaluator=None``, so every expectation below is exact and
deterministic.
"""

from __future__ import annotations

from unittest.mock import patch

from app.services.company_lens_service import (
    CATEGORY_LABELS,
    clamp_question_count,
    generate_exam_questions,
    grade_for,
    hire_decision_for,
    is_valid_token,
    mint_share_token,
    recommendation_for,
)

JD = (
    "We are hiring a Senior Platform Engineer to own our Kubernetes and "
    "Terraform infrastructure. You will build Postgres-backed services in "
    "Golang, design CI/CD pipelines, and mentor junior engineers on the "
    "observability stack."
)


class FakeLLM:
    """Stands in for LLMService — availability and canned JSON."""

    def __init__(self, available: bool, result=None):
        self._available = available
        self._result = result

    @property
    def is_available(self) -> bool:
        return self._available

    def generate_json(self, prompt, system_prompt=None, max_tokens=None):
        return self._result


# ── Token helpers ─────────────────────────────────────────────────────────


def test_tokens_are_url_safe_and_validated():
    token = mint_share_token()
    assert is_valid_token(token)
    assert all(c.isalnum() or c in "-_" for c in token)
    assert not is_valid_token("")
    assert not is_valid_token("short")
    assert not is_valid_token("has space!")
    assert not is_valid_token("a" * 65)


# ── Question count / difficulty clamping ──────────────────────────────────


def test_question_count_is_clamped():
    assert clamp_question_count(5) == 5
    assert clamp_question_count(999) == 20
    assert clamp_question_count(1) == 3
    assert clamp_question_count("junk") == 3
    assert clamp_question_count(None) == 3


# ── LLM generation path ───────────────────────────────────────────────────


def test_llm_generation_parses_list_output():
    fake = FakeLLM(
        available=True,
        result=[
            {
                "question": "Describe how you would migrate a StatefulSet to a new storage class in production.",
                "category": "T",
                "difficulty": "hard",
                "ideal_answer": "Drain nodes, data migration plan, rollback.",
            },
            {
                "question": "Walk me through a Terraform refactor you led.",
                "category": "P",
                "difficulty": "medium",
                "ideal_answer": "State management, module boundaries.",
            },
        ],
    )
    with patch("app.services.company_lens_service.get_llm", return_value=fake):
        questions = generate_exam_questions(
            job_description=JD, target_role="Platform Engineer", question_count=2
        )
    # question_count=2 clamps to the minimum of 3; the LLM delivered 2 and the
    # deterministic fallback pads the missing one, with the LLM's questions
    # kept at the front of the set.
    assert len(questions) == 3
    assert questions[0]["category"] == "T"
    assert questions[0]["difficulty"] == "hard"
    assert questions[0]["ideal_answer"] == "Drain nodes, data migration plan, rollback."
    assert questions[1]["category"] == "P"
    assert questions[2]["ideal_answer"]  # the padded fallback question


def test_llm_generation_handles_wrapped_dict():
    fake = FakeLLM(
        available=True,
        result={
            "questions": [
                {"question": "How do you size a Postgres cluster?  ", "category": "C"},
            ]
        },
    )
    with patch("app.services.company_lens_service.get_llm", return_value=fake):
        questions = generate_exam_questions(job_description=JD, question_count=4)
    # The LLM delivered one question; the fallback pads the set to the
    # requested four, with the LLM's question kept first.
    assert len(questions) == 4
    assert questions[0]["category"] == "C"
    assert questions[0]["question"] == "How do you size a Postgres cluster?"
    assert len({question["question"] for question in questions}) == 4  # no duplicates


# ── Deterministic fallback path ───────────────────────────────────────────


def test_fallback_generation_is_deterministic_and_jd_grounded():
    fake = FakeLLM(available=False)
    with patch("app.services.company_lens_service.get_llm", return_value=fake):
        first = generate_exam_questions(
            job_description=JD, target_role="Platform Engineer", question_count=6
        )
        second = generate_exam_questions(
            job_description=JD, target_role="Platform Engineer", question_count=6
        )
    assert first == second
    assert len(first) == 6

    categories = {question["category"] for question in first}
    assert categories == set(CATEGORY_LABELS)  # every category is covered

    for question in first:
        assert question["question"]
        assert question["difficulty"] in {"easy", "medium", "hard", "expert"}
        assert question["ideal_answer"]

    # Questions reference the JD (keywords extracted from it).
    joined = " ".join(question["question"].lower() for question in first)
    assert any(kw in joined for kw in ("kubernetes", "terraform", "postgres", "golang"))


# ── Scorecard fallback ────────────────────────────────────────────────────


def _sample_qa():
    return [
        {
            "question_number": 1,
            "question": "Technical question?",
            "category": "T",
            "answer": " ".join(["word"] * 120),  # 120 words → 82
        },
        {
            "question_number": 2,
            "question": "Behavioral question?",
            "category": "B",
            "answer": "",
        },
        {
            "question_number": 3,
            "question": "Conceptual question?",
            "category": "C",
            "answer": "short answer",  # 2 words → 35
        },
    ]


def test_fallback_scorecard_shape_and_math():
    scorecard = _build_fallback(_sample_qa())
    # T: 82 · B: 0 · C: 35 → overall round((82 + 0 + 35) / 3) = 39
    assert scorecard["overall_score"] == 39
    assert scorecard["overall_grade"] == grade_for(39) == "C"
    assert scorecard["recommendation"] == "Not recommended"
    assert scorecard["hire_decision"] == "no_hire"
    assert scorecard["category_breakdown"] == {"T": 82, "B": 0, "C": 35}
    assert scorecard["answered_questions"] == 3
    assert scorecard["total_questions"] == 3
    assert scorecard["generated_by"] == "fallback"
    assert scorecard["plagiarism_summary"] is None
    assert scorecard["summary"]


def test_fallback_scorecard_grades_empty_answers_as_insufficient():
    scorecard = _build_fallback(
        [{"question_number": 1, "question": "Q?", "category": "T", "answer": ""}]
    )
    assert scorecard["answers"][0]["score"] == 0
    assert scorecard["answers"][0]["grade"] == "Insufficient"
    assert scorecard["overall_score"] == 0
    assert scorecard["hire_decision"] == "no_hire"


def test_fallback_scorecard_detects_strong_answers():
    qa = [
        {
            "question_number": 1,
            "question": "Q?",
            "category": "T",
            "answer": " ".join(["word"] * 120),
        }
    ]
    scorecard = _build_fallback(qa)
    assert scorecard["answers"][0]["score"] == 82
    assert scorecard["answers"][0]["grade"] == "A"
    assert scorecard["hire_decision"] == "hire"
    assert scorecard["recommendation"] == "Strong recommend"


def _build_fallback(qa_pairs):
    from app.services.company_lens_service import build_scorecard

    return build_scorecard(
        qa_pairs=qa_pairs,
        candidate_name="Jordan Lee",
        exam_title="Platform Engineer Screening",
        evaluator=None,
    )


def test_grade_boundaries():
    assert grade_for(92) == "A+"
    assert grade_for(80) == "A"
    assert grade_for(72) == "B+"
    assert grade_for(60) == "B"
    assert grade_for(45) == "C"
    assert recommendation_for(85) == "Strong recommend"
    assert recommendation_for(70) == "Recommend"
    assert recommendation_for(55) == "Neutral"
    assert recommendation_for(30) == "Not recommended"
    assert hire_decision_for(80) == "hire"
    assert hire_decision_for(60) == "consider"
    assert hire_decision_for(40) == "no_hire"
