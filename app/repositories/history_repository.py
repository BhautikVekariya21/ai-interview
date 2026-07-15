"""Data-access layer for interview history.

All SQL touching the `history` table lives here so route handlers stay thin
controllers. Rows are returned as the attribute-accessible `_Row` objects the
MySQL/SQLite session wrapper produces (candidate_name, created_at,
overall_score, completion_rate, final_grade, total_questions, details_json).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from app.services.mysql_service import MySQLService


class HistoryRepository:
    def __init__(self, db: MySQLService):
        self._db = db

    def find_recent(self, user_id: Any, limit: int = 5) -> List[Any]:
        """Most recent entries for a user, newest first (used for dedup checks)."""
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM history WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit),
        )
        return list(rows)

    def find_duplicate(self, user_id: Any, candidate_name: str, cutoff: datetime) -> Optional[Any]:
        """Return an entry for the same candidate created at/after `cutoff`, if any."""
        for row in self.find_recent(user_id, limit=5):
            if row.candidate_name == candidate_name and row.created_at >= cutoff:
                return row
        return None

    def insert(
        self,
        user_id: Any,
        created_at: datetime,
        candidate_name: str,
        overall_score: int,
        completion_rate: int,
        final_grade: str,
        total_questions: int,
        details_json: Optional[str],
    ) -> None:
        s = self._db.get_session()
        s.execute(
            """
            INSERT INTO history (user_id, created_at, candidate_name, overall_score, completion_rate, final_grade, total_questions, details_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, created_at, candidate_name, overall_score, completion_rate, final_grade, total_questions, details_json),
        )

    def list_for_user(self, user_id: Any, limit: int = 50) -> List[Any]:
        """Entries for a user, newest first."""
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM history WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit),
        )
        return list(rows)

    def delete_for_user(self, user_id: Any) -> None:
        s = self._db.get_session()
        s.execute("DELETE FROM history WHERE user_id=%s", (user_id,))
