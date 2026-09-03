"""Data-access layer for coding-sandbox submissions.

All SQL touching the `coding_submissions` table lives here so route handlers
stay thin controllers. Rows are returned as the attribute-accessible `_Row`
objects the MySQL/SQLite session wrapper produces.

Submissions are keyed by `session_id` — one interview sitting. Without it every
attempt at a problem would land in one undifferentiated pile, so a candidate's
second interview would read as a continuation of their first.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from app.services.mysql_service import MySQLService


class CodingSubmissionRepository:
    def __init__(self, db: MySQLService):
        self._db = db

    def insert(
        self,
        submission_id: str,
        session_id: str,
        user_id: Optional[Any],
        problem_id: str,
        problem_title: str,
        language: str,
        code: str,
        passed: bool,
        tests_passed: int,
        tests_total: int,
        runtime_ms: float,
        created_at: datetime,
    ) -> None:
        s = self._db.get_session()
        s.execute(
            """
            INSERT INTO coding_submissions
                (id, session_id, user_id, problem_id, problem_title, language,
                 code, passed, tests_passed, tests_total, runtime_ms, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                submission_id,
                session_id,
                user_id,
                problem_id,
                problem_title,
                language,
                code,
                1 if passed else 0,
                tests_passed,
                tests_total,
                runtime_ms,
                created_at,
            ),
        )

    def list_for_session(self, session_id: str, limit: int = 100) -> List[Any]:
        """Every submission in one interview sitting, newest first."""
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM coding_submissions WHERE session_id=%s "
            "ORDER BY created_at DESC LIMIT %s",
            (session_id, limit),
        )
        return list(rows)
