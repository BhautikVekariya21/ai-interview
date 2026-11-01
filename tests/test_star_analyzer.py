"""Tests for the STAR behavioral answer analyzer (service + route layer)."""

import pytest

from app.services.star_analyzer import STARAnalyzer, get_star_analyzer


@pytest.fixture(scope="module")
def analyzer() -> STARAnalyzer:
    return STARAnalyzer()


def test_full_star_answer_scores_high(analyzer: STARAnalyzer):
    """A textbook STAR answer should score strongly on all four dimensions."""
    answer = (
        "At my last job, our payment service was failing intermittently during "
        "peak usage and customers were seeing timeouts. I was responsible for "
        "leading the incident response, so my task was to find and fix the "
        "root cause within the sprint. First I instrumented the request path, "
        "then built a one-off profiler and identified a connection pool "
        "exhaustion bug. I rewrote the pool handling and shipped it behind a "
        "flag. As a result, we reduced timeout errors by 92% and got positive "
        "feedback from the affected accounts."
    )
    report = analyzer.analyze_answer(answer, "Tell me about a hard problem", 1)

    assert report["skipped"] is False
    for dim in ("S", "T", "A", "R"):
        assert report["star"][dim] > 50, f"{dim} should be recognized, got {report['star'][dim]}"
    assert report["structure_score"] >= 70
    assert report["grade"] in ("Solid", "Structured Pro")
    assert report["missing"] == []


def test_no_context_answer_penalizes_situation(analyzer: STARAnalyzer):
    """An answer that jumps straight to action without setup should flag S."""
    answer = "I built the tool. I wrote the parser, deployed it, and it worked."
    report = analyzer.analyze_answer(answer, "", 1)

    assert report["star"]["S"] < 50
    assert "S" in report["missing"]
    assert report["words"] < 40  # short answers score low by design


def test_skipped_answer_returns_empty_report(analyzer: STARAnalyzer):
    report = analyzer.analyze_answer("[SKIPPED]", "Q", 1)
    assert report["skipped"] is True
    assert report["coaching"]
    assert report["structure_score"] == 0


def test_empty_answer_is_skipped(analyzer: STARAnalyzer):
    report = analyzer.analyze_answer("", "", 1)
    assert report["skipped"] is True


def test_result_metrics_detected(analyzer: STARAnalyzer):
    answer = (
        "We had a billing bug that was overcharging some users. I owned the "
        "fix, wrote the patch, and tested it against production snapshots. We "
        "cut incorrect charges by 30%."
    )
    report = analyzer.analyze_answer(answer, "", 1)
    assert report["star"]["R"] > 50


def test_session_summary_aggregates(analyzer: STARAnalyzer):
    qa_pairs = [
        {"question": "Q1", "answer": "I built it fast and shipped it same day, no context given.", "question_number": 1},
        {"question": "Q2", "answer": (
            "At the time we were scaling the pipeline past 5,000 requests per "
            "second. I owned the migration plan. I led the rollout, migrated "
            "each shard, and we cut p99 latency by 40% with zero downtime."
        ), "question_number": 2},
    ]
    reports = analyzer.analyze_session(qa_pairs)
    assert len(reports) == 2

    summary = analyzer.summarize(reports)
    assert summary["answers_total"] == 2
    assert summary["answers_analyzed"] == 2
    assert 0 <= summary["avg_structure_score"] <= 100
    assert summary["weakest_dimension"] in ("S", "T", "A", "R")


def test_coaching_limits_and_words(analyzer: STARAnalyzer):
    long_answer = " ".join(
        "The situation escalated quickly and I owned the action to fix it. "
        "I led the fix, we shipped, and the result was measured and improved."
        for _ in range(40)
    )
    report = analyzer.analyze_answer(long_answer, "", 1)
    assert len(report["coaching"]) <= 5
    assert report["words"] > 450


def test_singleton_access():
    assert get_star_analyzer() is get_star_analyzer()
