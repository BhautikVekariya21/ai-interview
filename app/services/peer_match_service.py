"""
Peer Match Service — head-to-head friend interview matches (Service).

Two candidates run the same interview format against each other, submit
their interview scores, and get an Elo-style verdict with rating deltas for
both sides. Matches live in the `peer_matches` MySQL table (SQLite fallback
in dev), keyed by a short human-sharable join code (e.g. "K7X2QM").

Flow:

1. A creates a match (POST /peer/match) → gets {code, player_token, secret}.
2. B joins with the code (POST /peer/match/{code}/join) → gets their token.
3. Each side submits their interview score with their `player_token`.
4. When both scores are in, the verdict (winner, margin, rating deltas) is
   computed and stored; GET /peer/match/{code} publishes it publicly.

The verdict math (`compute_match_verdict`) is a pure function so it is
unit-testable without the database layer.
"""

from __future__ import annotations

import json
import math
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from loguru import logger

if TYPE_CHECKING:  # pragma: no cover - type-only dependency
    from app.services.mysql_service import MySQLService

# Unambiguous code alphabet (no I/L/O/0/1/5/S so codes read cleanly aloud).
_CODE_ALPHABET = "ABCDEFGHJKMNPQRTUVWXYZ2346789"
CODE_LENGTH = 6
MATCH_EXPIRY_HOURS = 6

VALID_MODES = ("behavioral", "coding", "mixed")

MAX_SCORE = 100


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_code(rng: Optional[Any] = None) -> str:
    """Generate a CODE_LENGTH-char join code from the unambiguous alphabet."""
    source = rng or secrets
    return "".join(source.choice(_CODE_ALPHABET) for _ in range(CODE_LENGTH))


def compute_match_verdict(
    score_1: int,
    score_2: int,
) -> Dict[str, Any]:
    """Compute winner, margin, and Elo-style rating deltas for both players.

    Pure function of the two submitted scores (0-100):

    * A player wins on the higher interview score; exact ties are draws.
    * The margin decides the payout: a 3-point squeaker pays far less than a
      20-point rout, so results reflect how convincingly someone won.
    * Deltas are symmetric and always in +Δ/−Δ pairs.
    """
    s1 = max(0, min(MAX_SCORE, int(score_1)))
    s2 = max(0, min(MAX_SCORE, int(score_2)))
    margin = abs(s1 - s2)

    # Base K and a margin factor that saturates at a 25-point blowout.
    base_k = 24.0
    margin_factor = min(1.0, margin / 25.0)
    swing = base_k * (0.35 + 0.65 * margin_factor)

    if s1 > s2:
        outcome_1, outcome_2 = 1.0, 0.0
        winner = "p1"
    elif s2 > s1:
        outcome_1, outcome_2 = 0.0, 1.0
        winner = "p2"
    else:
        outcome_1, outcome_2 = 0.5, 0.5
        winner = "tie"
        swing *= 0.35  # draws move ratings much less

    # Expected score by margin (like a real Elo prior); big gaps move more.
    implied_rating_gap = margin * 12.0
    expected_1 = 1.0 / (1.0 + math.pow(10, implied_rating_gap / 400.0))
    delta_1 = round(swing * (outcome_1 - expected_1))
    delta_2 = -delta_1

    if winner == "p1":
        headline = f"Player 1 wins by {margin} points"
    elif winner == "p2":
        headline = f"Player 2 wins by {margin} points"
    else:
        headline = "It's a draw"

    return {
        "winner": winner,
        "margin": margin,
        "headline": headline,
        "p1_delta": delta_1,
        "p2_delta": delta_2,
        "p1_score": s1,
        "p2_score": s2,
    }


class PeerMatchService:
    """DB-backed peer head-to-head match store."""

    def __init__(self, db: MySQLService):
        self.db = db

    def _session(self):
        return self.db.get_session()

    # ─── Lifecycle ───────────────────────────────────────────────────────

    def create_match(
        self,
        player_name: str,
        mode: str = "mixed",
    ) -> Dict[str, Any]:
        """Create a waiting match and put player 1 in it."""
        name = self._sanitize_name(player_name, "Player 1")
        if mode not in VALID_MODES:
            raise ValueError(f"mode must be one of: {', '.join(VALID_MODES)}")

        s = self._session()
        now_iso = _utcnow().isoformat()
        token = secrets.token_urlsafe(16)
        secret = secrets.token_urlsafe(16)

        for _ in range(12):
            code = generate_code()
            existing = s.execute(
                "SELECT code FROM peer_matches WHERE code=%s", (code,)
            ).one()
            if not existing:
                s.execute(
                    "INSERT INTO peer_matches (code, status, mode, p1_name, p1_token, "
                    "p1_secret, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (code, "waiting", mode, name, token, secret, now_iso, now_iso),
                )
                return {
                    "code": code,
                    "mode": mode,
                    "player": "p1",
                    "player_token": token,
                    "secret": secret,
                    "display_name": name,
                }
        raise RuntimeError("Could not allocate a unique match code")  # pragma: no cover

    def join_match(
        self,
        code: str,
        player_name: str,
    ) -> Dict[str, Any]:
        """Join a waiting match as player 2."""
        name = self._sanitize_name(player_name, "Player 2")
        s = self._session()
        match = s.execute(
            "SELECT * FROM peer_matches WHERE code=%s", (code.upper(),)
        ).one()
        if not match:
            raise LookupError("Match code not found")
        if getattr(match, "p2_token", None):
            raise ValueError("Match already has two players")

        now_iso = _utcnow().isoformat()
        token = secrets.token_urlsafe(16)
        secret = secrets.token_urlsafe(16)
        s.execute(
            "UPDATE peer_matches SET p2_name=%s, p2_token=%s, p2_secret=%s, "
            "status='active', updated_at=%s WHERE code=%s",
            (name, token, secret, now_iso, code.upper()),
        )
        return {
            "code": match.code,
            "mode": match.mode,
            "player": "p2",
            "player_token": token,
            "display_name": name,
        }

    def submit_score(
        self,
        code: str,
        player_token: str,
        score: int,
    ) -> Dict[str, Any]:
        """Submit one player's interview score; finalize the verdict when both are in."""
        s = self._session()
        match = self._get_raw(code)
        token = str(player_token or "")
        side = self._side_for_token(match, token)
        if side is None:
            raise PermissionError("This player token does not belong to the match")

        value = max(0, min(MAX_SCORE, int(score)))
        col = f"{side}_score"
        now_iso = _utcnow().isoformat()
        s.execute(
            f"UPDATE peer_matches SET {col}=%s, updated_at=%s WHERE code=%s",
            (value, now_iso, match.code),
        )

        fresh = self._get_raw(code)
        if fresh.p1_score is not None and fresh.p2_score is not None:
            verdict = compute_match_verdict(
                int(fresh.p1_score), int(fresh.p2_score)
            )
            s.execute(
                "UPDATE peer_matches SET verdict=%s, status='complete', "
                "updated_at=%s WHERE code=%s",
                (json.dumps(verdict), now_iso, match.code),
            )
            return {
                "submitted": True,
                "finalized": True,
                "verdict": verdict,
            }
        return {
            "submitted": True,
            "finalized": False,
            "verdict": None,
        }

    def get_match(self, code: str) -> Dict[str, Any]:
        """Public view of a match (names/status/verdict — no tokens or secrets)."""
        match = self._get_raw(code)
        p1, p2, status = match.p1_name, getattr(match, "p2_name", None), match.status
        mode = match.mode
        verdict = None
        if match.verdict:
            try:
                verdict = json.loads(match.verdict)
            except Exception:  # pragma: no cover - defensive
                verdict = None

        scores = {
            "p1": match.p1_score,
            "p2": match.p2_score,
        }
        return {
            "code": match.code,
            "status": status,
            "mode": mode,
            "players": {
                "p1": p1,
                "p2": p2,
            },
            "joined": bool(getattr(match, "p2_token", None)),
            "scores": scores,
            "verdict": verdict,
            "expires_hours": MATCH_EXPIRY_HOURS,
            "created_at": str(match.created_at) if match.created_at else None,
        }

    # ─── Internals ───────────────────────────────────────────────────────

    def _get_raw(self, code: str) -> Any:
        s = self._session()
        match = s.execute(
            "SELECT * FROM peer_matches WHERE code=%s", (str(code).upper(),)
        ).one()
        if not match:
            raise LookupError("Match code not found")
        created = getattr(match, "created_at", None)
        if created:
            if datetime.fromisoformat(str(created).replace("Z", "+00:00")) < (
                _utcnow() - timedelta(hours=MATCH_EXPIRY_HOURS)
            ):
                s.execute(
                    "DELETE FROM peer_matches WHERE code=%s", (match.code,)
                )
                raise LookupError("Match code not found")
        return match

    @staticmethod
    def _side_for_token(match: Any, token: str) -> Optional[str]:
        if token and token == getattr(match, "p1_token", None):
            return "p1"
        if token and token == getattr(match, "p2_token", None):
            return "p2"
        return None

    @staticmethod
    def _sanitize_name(value: Any, fallback: str) -> str:
        cleaned = str(value or "").strip()
        return cleaned[:64] or fallback
