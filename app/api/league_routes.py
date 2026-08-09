"""Interview League API routes.

The league computes ELO ratings over the graded coding corpus. Ratings are
derived entirely from the existing `coding_submissions` log (problem, pass
status, timestamp) plus each problem's difficulty — no new tables, no hidden
state.

* GET /league/rating      — the signed-in user's rating, tier, and stats
* GET /league/leaderboard — top players by rating with tier badges
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.api.auth_routes import get_current_user
from app.services.elo_service import (
    compute_rating,
    is_provisional,
    session_stats,
    tier_for_rating,
)
from app.services.mysql_service import MySQLService, get_mysql, get_mysql_health

league_router = APIRouter(
    prefix="/league",
    tags=["Interview League"],
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _difficulty_resolver_factory(db: MySQLService):
    """Memoised resolver: problem_id -> difficulty label.

    `get_problem_by_id` walks every problem source, so leaderboard scans cache
    each lookup in a plain dict instead of re-walking the corpus per row.
    """
    cache: Dict[str, Optional[str]] = {}

    def resolve(problem_id: Optional[str]) -> Optional[str]:
        if not problem_id:
            return None
        if problem_id in cache:
            return cache[problem_id]
        try:
            from app.services.code_executor_service import get_code_executor_service

            problem = get_code_executor_service().get_problem_by_id(problem_id)
            difficulty = (
                str(problem.get("difficulty") or "") if problem else ""
            )
        except Exception:  # pragma: no cover - best-effort lookup
            difficulty = ""
        cache[problem_id] = difficulty or None
        return cache[problem_id]

    return resolve


def _submissions_for_user(db: MySQLService, user_id: Any) -> List[Any]:
    s = db.get_session()
    rows = s.execute(
        "SELECT problem_id, passed, created_at FROM coding_submissions "
        "WHERE user_id=%s ORDER BY created_at ASC",
        (user_id,),
    )
    return list(rows)


def _load_leaderboard(db: MySQLService, limit: int) -> List[Dict[str, Any]]:
    s = db.get_session()
    rows = list(
        s.execute(
            "SELECT DISTINCT user_id FROM coding_submissions "
            "WHERE user_id IS NOT NULL AND user_id <> ''"
        )
    )
    if not rows:
        return []

    user_ids = [row.user_id for row in rows]
    name_by_id: Dict[str, str] = {}
    for user_id in user_ids:
        name_by_id[str(user_id)] = ""

    # Resolve display names from the users table in one query.
    try:
        user_rows = list(
            s.execute(
                "SELECT id, full_name FROM users WHERE id IN (%s)"
                % ",".join(["%s"] * len(user_ids)),
                tuple(user_ids),
            )
        )
        for row in user_rows:
            name_by_id[str(row.id)] = str(row.full_name or "")
    except Exception as exc:  # pragma: no cover - names are cosmetic
        logger.warning(f"Leaderboard name lookup failed: {exc}")

    resolve = _difficulty_resolver_factory(db)
    entries: List[Dict[str, Any]] = []
    for user_id in user_ids:
        try:
            submissions = _submissions_for_user(db, user_id)
        except Exception as exc:  # pragma: no cover - skip broken rows
            logger.warning(f"Leaderboard submission load failed for {user_id}: {exc}")
            continue
        if not submissions:
            continue
        rating, _ = compute_rating(submissions, resolve)
        stats = session_stats(submissions)
        entries.append({
            "user_id": str(user_id),
            "name": name_by_id.get(str(user_id)) or "Anonymous",
            "rating": rating,
            "tier": tier_for_rating(rating),
            "games": stats["games"],
            "wins": stats["wins"],
            "win_rate": stats["win_rate"],
            "provisional": is_provisional(stats["games"]),
        })

    entries.sort(key=lambda entry: entry["rating"], reverse=True)
    for rank, entry in enumerate(entries[:limit], start=1):
        entry["rank"] = rank
    return entries[:limit]


@league_router.get("/health", summary="Health check")
def health() -> Dict[str, str]:
    db = get_mysql_health()
    return {
        "status": "healthy" if db["status"] == "healthy" else "degraded",
        "module": "interview_league",
        "mysql": db,
    }


@league_router.get("/rating", summary="Your league rating")
def my_rating(
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """The signed-in user's rating, tier, and submission stats."""
    user_id = current["user"].id
    try:
        submissions = _submissions_for_user(db, user_id)
    except Exception as exc:
        logger.warning(f"League rating load failed: {exc}")
        raise HTTPException(
            status_code=503,
            detail="League data is unavailable right now.",
        )
    rating, deltas = compute_rating(submissions, _difficulty_resolver_factory(db))
    return {
        "rating": rating,
        "tier": tier_for_rating(rating),
        "games": len(submissions),
        "wins": session_stats(submissions)["wins"],
        "win_rate": session_stats(submissions)["win_rate"],
        "provisional": is_provisional(len(submissions)),
        "last_deltas": deltas[-10:],
    }


@league_router.get("/leaderboard", summary="Top players by rating")
def leaderboard(
    limit: int = Query(20, ge=1, le=100),
    current=Depends(get_current_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """Rank players by ELO rating computed from their graded submissions."""
    try:
        entries = _load_leaderboard(db, limit)
    except Exception as exc:
        logger.warning(f"Leaderboard load failed: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Leaderboard is unavailable right now.",
        )
    return {
        "entries": entries,
        "generated_at": _now_iso(),
    }
