"""Tests for the Interview League ELO engine.

The league recomputes ratings deterministically from a submission log, so the
core maths is a set of pure functions — this file pins them down.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.services.elo_service import (
    DIFFICULTY_RATING,
    START_RATING,
    compute_rating,
    difficulty_rating,
    expected_score,
    is_provisional,
    session_stats,
    tier_for_rating,
    update_rating,
)


class FakeSubmission:
    def __init__(self, problem_id: str, passed: bool, created_at: datetime):
        self.problem_id = problem_id
        self.passed = passed
        self.created_at = created_at


def _at(day: int) -> datetime:
    return datetime(2026, 1, day, tzinfo=timezone.utc)


# ── Core ELO maths ────────────────────────────────────────────────────────


def test_expected_score_midpoint_is_half():
    assert expected_score(1200, 1200) == 0.5


def test_expected_score_favours_higher_rating():
    assert expected_score(1600, 1200) > 0.8
    assert expected_score(1200, 1600) < 0.2


def test_update_rating_moves_toward_result():
    # Beating a much weaker opponent costs almost nothing.
    after_win = update_rating(1500, 1000, 1.0)
    assert 1500 <= after_win < 1533
    # Losing to a much weaker opponent costs a lot.
    after_loss = update_rating(1500, 1000, 0.0)
    assert after_loss < 1475


# ── Difficulty mapping ────────────────────────────────────────────────────


def test_difficulty_rating_maps_labels():
    assert difficulty_rating("Easy") == DIFFICULTY_RATING["easy"]
    assert difficulty_rating("hard") == DIFFICULTY_RATING["hard"]
    assert difficulty_rating("Expert") == DIFFICULTY_RATING["expert"]
    assert difficulty_rating("UnknownTier") == DIFFICULTY_RATING["medium"]
    assert difficulty_rating(None) == DIFFICULTY_RATING["medium"]


# ── Rating recomputation over a submission log ────────────────────────────


def test_no_submissions_returns_start_rating():
    rating, deltas = compute_rating([])
    assert rating == START_RATING
    assert deltas == []


def test_winning_problems_raises_rating():
    submissions = [
        FakeSubmission("p-easy", passed=True, created_at=_at(1)),
        FakeSubmission("p-easy", passed=True, created_at=_at(2)),
        FakeSubmission("p-easy", passed=True, created_at=_at(3)),
    ]
    rating, deltas = compute_rating(submissions)
    assert rating > START_RATING
    assert len(deltas) == 3
    assert all(delta >= 0 for delta in deltas)


def test_losing_problems_lowers_rating():
    submissions = [
        FakeSubmission("p-hard", passed=False, created_at=_at(1)),
        FakeSubmission("p-hard", passed=False, created_at=_at(2)),
    ]
    rating, _ = compute_rating(submissions)
    assert rating < START_RATING


def test_difficulty_resolver_is_used():
    resolver_calls: list = []

    def resolver(problem_id):
        resolver_calls.append(problem_id)
        return "Easy" if problem_id == "p-1" else "Expert"

    # In isolation, beating an Expert problem earns far more than an Easy one.
    easy_win, _ = compute_rating(
        [FakeSubmission("p-1", passed=True, created_at=_at(1))], resolver
    )
    expert_win, _ = compute_rating(
        [FakeSubmission("p-2", passed=True, created_at=_at(1))], resolver
    )
    assert easy_win > START_RATING
    assert expert_win > easy_win
    assert resolver_calls == ["p-1", "p-2"]


def test_rating_is_chronological_and_deterministic():
    log = [
        FakeSubmission("p-a", passed=False, created_at=_at(1)),
        FakeSubmission("p-b", passed=True, created_at=_at(2)),
        FakeSubmission("p-c", passed=False, created_at=_at(3)),
        FakeSubmission("p-d", passed=True, created_at=_at(4)),
    ]
    first, _ = compute_rating(list(log))
    second, _ = compute_rating(list(reversed(log)))  # sorted internally
    assert first == second


# ── Tiers & stats ─────────────────────────────────────────────────────────


def test_tier_thresholds():
    # New players start at the bottom of the table — the league is a climb.
    assert tier_for_rating(START_RATING)["tier"] == "Bronze"
    assert tier_for_rating(1150)["tier"] == "Bronze"
    assert tier_for_rating(1250)["tier"] == "Silver"
    assert tier_for_rating(1450)["tier"] == "Gold"
    assert tier_for_rating(1650)["tier"] == "Platinum"
    assert tier_for_rating(1850)["tier"] == "Diamond"


def test_provisional_until_three_graded_submissions():
    assert is_provisional(0) is True
    assert is_provisional(1) is True
    assert is_provisional(2) is True
    assert is_provisional(3) is False
    assert is_provisional(12) is False
    assert is_provisional(None) is True


def test_session_stats():
    submissions = [
        FakeSubmission("p-a", passed=True, created_at=_at(1)),
        FakeSubmission("p-b", passed=False, created_at=_at(2)),
        FakeSubmission("p-c", passed=True, created_at=_at(3)),
    ]
    stats = session_stats(submissions)
    assert stats["games"] == 3
    assert stats["wins"] == 2
    assert stats["losses"] == 1
    assert stats["win_rate"] == round(2 / 3 * 100, 1)
