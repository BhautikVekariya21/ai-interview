"""Tests for the evidence coaching service.

Pure-function tests — no DB, no LLM. The gap-report tests exercise the
deterministic fallback path (no provider is configured in CI).
"""

from __future__ import annotations

from unittest.mock import patch

from app.services.evidence_service import (
    generate_coach_tip,
    generate_gap_report,
)


# ── Gap report (deterministic fallback) ───────────────────────────────────


def test_gap_report_fallback_shape_with_fragile_and_untested_claims():
    class _NoLLM:
        """Stand-in for LLMService that reports unavailable — keeps the test
        hermetic even on machines where a provider IS configured."""

        is_available = False

        def generate_json(self, *args, **kwargs):
            return None

    # generate_gap_report routes through _llm_gap_report whenever gaps exist,
    # and that does a lazy `from app.services.llm_service import get_llm`, so
    # the patch target is the llm_service attribute (not evidence_service's).
    with patch("app.services.llm_service.get_llm", return_value=_NoLLM()):
        result = generate_gap_report(
            candidate_name="Ada",
            ats_report={"keyword_match": {"missing": ["kubernetes", "grpc"]}},
            assessments=[
                {"label": "Kafka", "status": "fragile", "kind": "skill"},
                {"label": "OpenTrace", "status": "untested", "kind": "project"},
                {"label": "React", "status": "validated", "kind": "skill"},
            ],
        )
    assert result["generated_by"] == "rules"
    assert result["overview"]
    assert len(result["focus_areas"]) == 2
    assert any(area["claim"] == "Kafka" for area in result["focus_areas"])
    assert all(area["actions"] for area in result["focus_areas"])
    assert [gap["keyword"] for gap in result["ats_gaps"]] == [
        "kubernetes",
        "grpc",
    ]
    assert "OpenTrace" in result["next_round_probes"]


def test_gap_report_empty_assessments_still_returns_plan():
    result = generate_gap_report(candidate_name="")
    assert result["generated_by"] == "rules"
    assert result["focus_areas"] == []
    assert result["ats_gaps"] == []


# ── Coach whisper ─────────────────────────────────────────────────────────


def test_coach_tip_filler_spike():
    tip = generate_coach_tip(
        answer_text="um, I think, like, it depends, um",
        filler_count=4,
        filler_percentage=40,
    )
    assert tip["category"] == "fillers"
    assert "um" in tip["tip"].lower() or "filler" in tip["tip"].lower()


def test_coach_tip_filler_count_without_percentage_does_not_crash():
    # The fillers branch is entered via filler_count alone (filler_percentage
    # is optional on the request) — the tip must not format a None percentage.
    tip = generate_coach_tip(
        answer_text="um, I mean, like, you know",
        filler_count=4,
    )
    assert tip["category"] == "fillers"
    assert tip["tip"]
    assert "% of words" not in tip["tip"]


def test_coach_tip_too_fast():
    tip = generate_coach_tip(answer_text="x", wpm=210)
    assert tip["category"] == "pace"


def test_coach_tip_low_confidence():
    tip = generate_coach_tip(
        answer_text="I guess maybe probably it could be fine",
        confidence_score=25,
    )
    assert tip["category"] == "confidence"


def test_coach_tip_too_short():
    tip = generate_coach_tip(answer_text="Yes.")
    assert tip["category"] == "depth"


def test_coach_tip_reinforcement_default():
    tip = generate_coach_tip(
        answer_text="I built a distributed cache that cut p99 latency by 40 percent across three regions.",
        word_count=16,
        filler_percentage=1,
        wpm=140,
        confidence_score=85,
    )
    assert tip["category"] == "reinforcement"
