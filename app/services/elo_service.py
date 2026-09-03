"""Interview League — ELO ratings over the graded coding corpus.

Rating model: every submitted problem is treated as an *opponent* whose
strength is the problem's difficulty rating (Easy 1000 / Medium 1300 / Hard
1600 / Expert 1900). A pass scores 1.0 against that opponent, a fail scores
0.0, and the standard ELO update is applied.

Ratings are recomputed deterministically from the submission log in
chronological order — there is no hidden state, no extra table, and no job
queue. The league is therefore exactly as truthful as the graded corpus it
sits on, and trivially testable.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

# Base strength of each problem difficulty tier, used as the opponent rating.
DIFFICULTY_RATING = {
    "easy": 1000,
    "medium": 1300,
    "hard": 1600,
    "expert": 1900,
}

# New players begin at the bottom of the table (Bronze) so every match is
# a climb — matching the "only room to go up" feel the tiers are meant to
# reward.
START_RATING = 1000
K_FACTOR = 32

# A rating is provisional until the player has this many graded submissions —
# mirroring chess, where a rating carries a "?" until it is backed by enough
# games to be reliable. Until then, a couple of lucky (or unlucky) swings can
# move the number a lot.
PROVISIONAL_GAMES = 3

# Tier thresholds (rating >= threshold). Ordered strongest last.
TIERS: List[Tuple[int, str, str, str]] = [
    (1800, "Diamond", "Elite", "#7DD3FC"),
    (1600, "Platinum", "Advanced", "#E2E8F0"),
    (1400, "Gold", "Strong", "#FBBF24"),
    (1200, "Silver", "Solid", "#CBD5E1"),
    (0, "Bronze", "Getting started", "#D97757"),
]


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that player A (rating_a) beats player B (rating_b)."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def update_rating(
    rating: float,
    opponent_rating: float,
    actual: float,
    k: float = K_FACTOR,
) -> int:
    """Standard ELO update: rating + K * (actual - expected)."""
    expected = expected_score(rating, opponent_rating)
    return int(round(rating + k * (actual - expected)))


def difficulty_rating(difficulty: Optional[str]) -> int:
    """Map a problem difficulty label to an opponent rating.

    Accepts the capitalised bank labels ("Easy") and interview labels
    ("easy"); anything unknown falls back to Medium.
    """
    if not difficulty:
        return DIFFICULTY_RATING["medium"]
    key = str(difficulty).strip().lower()
    return DIFFICULTY_RATING.get(key, DIFFICULTY_RATING["medium"])


def tier_for_rating(rating: float) -> Dict[str, Any]:
    """Tier metadata for a rating (tier name, label, badge color)."""
    for threshold, tier, label, color in TIERS:
        if rating >= threshold:
            return {"tier": tier, "label": label, "color": color}
    return {"tier": "Bronze", "label": "Getting started", "color": "#D97757"}


def is_provisional(games: int) -> bool:
    """True until the player has enough graded submissions to be reliable."""
    return int(games or 0) < PROVISIONAL_GAMES


def compute_rating(
    submissions: List[Any],
    difficulty_resolver: Optional[Callable[[Any], Optional[str]]] = None,
) -> Tuple[int, List[int]]:
    """Recompute a player's rating from their submissions (oldest first).

    `submissions` are rows with `.problem_id`, `.passed`, `.created_at`.
    `difficulty_resolver(problem_id)` returns the problem's difficulty label;
    when omitted or unknown, problems default to Medium.
    """
    if not submissions:
        return START_RATING, []

    ordered = sorted(submissions, key=lambda s: _sort_key(s))
    rating = float(START_RATING)
    deltas: List[int] = []

    for submission in ordered:
        problem_id = getattr(submission, "problem_id", None)
        difficulty = (
            difficulty_resolver(problem_id) if difficulty_resolver else None
        )
        opponent = difficulty_rating(difficulty)
        actual = 1.0 if bool(getattr(submission, "passed", False)) else 0.0
        new_rating = update_rating(rating, opponent, actual)
        deltas.append(new_rating - int(round(rating)))
        rating = float(new_rating)

    return int(round(rating)), deltas


def _sort_key(submission: Any):
    created_at = getattr(submission, "created_at", None)
    if created_at is None:
        return ""
    return created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)


def session_stats(submissions: List[Any]) -> Dict[str, Any]:
    """Games played, wins, and win rate for a player's submission log."""
    total = len(submissions)
    wins = sum(1 for s in submissions if bool(getattr(s, "passed", False)))
    return {
        "games": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": round(wins / total * 100, 1) if total else 0.0,
    }
