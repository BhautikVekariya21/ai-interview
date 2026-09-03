"""Refresh-token sessions, revocation, and plan lookup.

Design
------
* Access token: the existing short JWT stored in the ``sessions`` table (hashed).
* Refresh token: opaque 256-bit random string, stored hashed in ``refresh_tokens``.
  Tokens rotate on every use and belong to a *family*. Re-using an already
  rotated token is treated as theft and the whole family is revoked.
* Revocation: ``revoke_session`` deletes the access session row and marks all
  refresh tokens of its family revoked. ``revoke_all`` signs out every device.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings

REFRESH_TOKEN_DAYS = getattr(settings, "REFRESH_TOKEN_DAYS", 60)
PLANS: Dict[str, Dict[str, Any]] = {
    "free": {"label": "Free", "interviews_per_day": 5, "llm_calls_per_minute": 20, "code_runs_per_minute": 10},
    "pro": {"label": "Pro", "interviews_per_day": 50, "llm_calls_per_minute": 90, "code_runs_per_minute": 40},
    "team": {"label": "Team", "interviews_per_day": 500, "llm_calls_per_minute": 300, "code_runs_per_minute": 120},
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class RefreshResult:
    user_id: str
    refresh_token: str
    family_id: str


class SessionService:
    def __init__(self, db):
        self.db = db

    # ── refresh tokens ────────────────────────────────────────────────────
    def issue_refresh_token(
        self,
        user_id: str,
        session_token_hash: Optional[str],
        *,
        family_id: Optional[str] = None,
        user_agent: str = "",
        ip: str = "",
    ) -> str:
        raw = secrets.token_urlsafe(48)
        now = _utcnow()
        s = self.db.get_session()
        s.execute(
            """
            INSERT INTO refresh_tokens
                (token_hash, user_id, session_token_hash, family_id, created_at, expires_at, user_agent, ip)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                hash_token(raw),
                str(user_id),
                session_token_hash,
                family_id or str(uuid.uuid4()),
                now,
                now + timedelta(days=REFRESH_TOKEN_DAYS),
                (user_agent or "")[:400],
                (ip or "")[:64],
            ),
        )
        return raw

    def rotate(self, raw_refresh: str, *, user_agent: str = "", ip: str = "") -> Optional[RefreshResult]:
        """Validate and rotate a refresh token. Returns None when invalid.

        Detects replay: a token that was already replaced means the family is
        compromised and all tokens in that family are revoked.
        """
        s = self.db.get_session()
        th = hash_token(raw_refresh)
        row = s.execute(
            "SELECT user_id, family_id, expires_at, revoked_at, replaced_by, session_token_hash FROM refresh_tokens WHERE token_hash=%s",
            (th,),
        ).one()
        if not row:
            return None
        now = _utcnow()
        if row["revoked_at"] is not None or (row["replaced_by"] or ""):
            logger.warning(f"refresh token replay detected for family {row['family_id']}; revoking family")
            self.revoke_family(row["family_id"])
            return None
        expires = row["expires_at"]
        if expires and expires < now:
            return None

        new_raw = secrets.token_urlsafe(48)
        new_hash = hash_token(new_raw)
        s.execute(
            """
            INSERT INTO refresh_tokens
                (token_hash, user_id, session_token_hash, family_id, created_at, expires_at, user_agent, ip)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                new_hash,
                row["user_id"],
                row["session_token_hash"],
                row["family_id"],
                now,
                now + timedelta(days=REFRESH_TOKEN_DAYS),
                (user_agent or "")[:400],
                (ip or "")[:64],
            ),
        )
        s.execute(
            "UPDATE refresh_tokens SET replaced_by=%s, revoked_at=%s WHERE token_hash=%s",
            (new_hash, now, th),
        )
        return RefreshResult(user_id=str(row["user_id"]), refresh_token=new_raw, family_id=str(row["family_id"]))

    def attach_session_to_refresh(self, raw_refresh: str, session_token_hash: str) -> None:
        s = self.db.get_session()
        s.execute(
            "UPDATE refresh_tokens SET session_token_hash=%s WHERE token_hash=%s",
            (session_token_hash, hash_token(raw_refresh)),
        )

    def revoke_family(self, family_id: str) -> None:
        s = self.db.get_session()
        now = _utcnow()
        rows = s.execute(
            "SELECT DISTINCT session_token_hash FROM refresh_tokens WHERE family_id=%s AND session_token_hash IS NOT NULL",
            (family_id,),
        ).all()
        s.execute(
            "UPDATE refresh_tokens SET revoked_at=%s WHERE family_id=%s AND revoked_at IS NULL",
            (now, family_id),
        )
        for r in rows:
            s.execute("DELETE FROM sessions WHERE token=%s", (r["session_token_hash"],))

    # ── sessions (devices) ────────────────────────────────────────────────
    def list_sessions(self, user_id: str, current_token_hash: Optional[str]) -> List[Dict[str, Any]]:
        s = self.db.get_session()
        rows = s.execute(
            "SELECT token, created_at, expires_at FROM sessions WHERE user_id=%s ORDER BY created_at DESC",
            (str(user_id),),
        ).all()
        out: List[Dict[str, Any]] = []
        for r in rows:
            meta = s.execute(
                "SELECT user_agent, ip, created_at FROM refresh_tokens WHERE session_token_hash=%s ORDER BY created_at DESC LIMIT 1",
                (r["token"],),
            ).one()
            out.append(
                {
                    "id": r["token"][:16],
                    "created_at": r["created_at"],
                    "expires_at": r["expires_at"],
                    "user_agent": (meta or {}).get("user_agent") or "",
                    "ip": (meta or {}).get("ip") or "",
                    "current": r["token"] == current_token_hash,
                }
            )
        return out

    def revoke_session(self, user_id: str, session_id_prefix: str) -> bool:
        s = self.db.get_session()
        rows = s.execute("SELECT token FROM sessions WHERE user_id=%s", (str(user_id),)).all()
        target = next((r["token"] for r in rows if r["token"].startswith(session_id_prefix)), None)
        if not target:
            return False
        fam = s.execute(
            "SELECT family_id FROM refresh_tokens WHERE session_token_hash=%s LIMIT 1", (target,)
        ).one()
        if fam:
            self.revoke_family(fam["family_id"])
        s.execute("DELETE FROM sessions WHERE token=%s", (target,))
        return True

    def revoke_all(self, user_id: str, *, except_token_hash: Optional[str] = None) -> int:
        s = self.db.get_session()
        now = _utcnow()
        if except_token_hash:
            s.execute(
                "UPDATE refresh_tokens SET revoked_at=%s WHERE user_id=%s AND revoked_at IS NULL AND (session_token_hash IS NULL OR session_token_hash<>%s)",
                (now, str(user_id), except_token_hash),
            )
            res = s.execute(
                "DELETE FROM sessions WHERE user_id=%s AND token<>%s", (str(user_id), except_token_hash)
            )
        else:
            s.execute(
                "UPDATE refresh_tokens SET revoked_at=%s WHERE user_id=%s AND revoked_at IS NULL",
                (now, str(user_id)),
            )
            res = s.execute("DELETE FROM sessions WHERE user_id=%s", (str(user_id),))
        return getattr(res, "rowcount", 0) or 0

    def purge_expired(self) -> None:
        s = self.db.get_session()
        now = _utcnow()
        s.execute("DELETE FROM sessions WHERE expires_at < %s", (now,))
        s.execute("DELETE FROM refresh_tokens WHERE expires_at < %s", (now,))

    # ── plans ─────────────────────────────────────────────────────────────
    def get_plan(self, user_id: Optional[str]) -> str:
        if not user_id:
            return "free"
        try:
            row = self.db.get_session().execute(
                "SELECT plan FROM user_plans WHERE user_id=%s", (str(user_id),)
            ).one()
            plan = (row or {}).get("plan") or "free"
            return plan if plan in PLANS else "free"
        except Exception:
            return "free"

    def set_plan(self, user_id: str, plan: str) -> None:
        if plan not in PLANS:
            raise ValueError(f"unknown plan {plan}")
        s = self.db.get_session()
        now = _utcnow()
        existing = s.execute("SELECT user_id FROM user_plans WHERE user_id=%s", (str(user_id),)).one()
        if existing:
            s.execute("UPDATE user_plans SET plan=%s, updated_at=%s WHERE user_id=%s", (plan, now, str(user_id)))
        else:
            s.execute(
                "INSERT INTO user_plans (user_id, plan, updated_at) VALUES (%s, %s, %s)", (str(user_id), plan, now)
            )
