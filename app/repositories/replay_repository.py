"""Data-access layer for Game Tape replay shares.

Replays are persisted as a JSON document under an unguessable token so a share
link stays valid after the session, the proctor files, or the account are gone.
The document is opaque to the repository — merge/normalise logic lives in
``app.services.replay_service``; this layer only stores and retrieves blobs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.services.mysql_service import MySQLService


class ReplayRepository:
    def __init__(self, db: MySQLService):
        self._db = db

    def find_by_token(self, token: str) -> Optional[str]:
        """The stored replay JSON for a token, or None when it does not exist."""
        s = self._db.get_session()
        rows = s.execute(
            "SELECT payload FROM interview_replays WHERE token=%s LIMIT 1",
            (token,),
        )
        row = rows.one()
        return row.payload if row else None

    def find_token_by_session(self, session_id: str) -> Optional[str]:
        """An existing share token for a sitting, so re-sharing returns the same link."""
        s = self._db.get_session()
        rows = s.execute(
            "SELECT token FROM interview_replays WHERE session_id=%s "
            "ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
        row = rows.one()
        return row.token if row else None

    def save(
        self,
        token: str,
        session_id: Optional[str],
        user_id: Any,
        candidate_name: Optional[str],
        payload_json: str,
        created_at: datetime,
    ) -> None:
        """Persist (or refresh) the document under its token.

        The same sitting is re-shared with the same token, so this must be an
        update-or-insert — a bare INSERT would trip the primary key on the
        second share. Kept portable across MySQL and the SQLite fallback by
        avoiding ``ON DUPLICATE KEY`` / ``INSERT OR REPLACE``.
        """
        s = self._db.get_session()
        updated = s.execute(
            """
            UPDATE interview_replays
            SET session_id=%s, user_id=%s, candidate_name=%s, payload=%s, created_at=%s
            WHERE token=%s
            """,
            (session_id, user_id, candidate_name, payload_json, created_at, token),
        )
        if updated.rowcount == 0:
            s.execute(
                """
                INSERT INTO interview_replays
                    (token, session_id, user_id, candidate_name, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    token,
                    session_id,
                    user_id,
                    candidate_name,
                    payload_json,
                    created_at,
                ),
            )
