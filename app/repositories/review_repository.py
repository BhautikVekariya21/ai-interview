"""Data-access layer for app reviews (feedback forum).

All SQL touching the `app_reviews` table lives here so route handlers stay
thin controllers. Rows are returned as the attribute-accessible `_Row`
objects the MySQL/SQLite session wrapper produces.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List

from app.services.mysql_service import MySQLService


class ReviewRepository:
    def __init__(self, db: MySQLService):
        self._db = db

    def insert(
        self,
        review_id: str,
        user_id: Any,
        author_name: str,
        rating: int,
        title: str,
        review: str,
        created_at: datetime,
    ) -> None:
        s = self._db.get_session()
        s.execute(
            """
            INSERT INTO app_reviews (id, user_id, author_name, rating, title, review, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (review_id, user_id, author_name, rating, title, review, created_at),
        )

    def list_recent(self, limit: int = 50) -> List[Any]:
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM app_reviews ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        return list(rows)

    def stats(self) -> dict:
        s = self._db.get_session()
        row = list(s.execute("SELECT COUNT(*) AS total, AVG(rating) AS average FROM app_reviews", ()))[0]
        total = row.total or 0
        average = float(row.average) if row.average is not None else 0.0
        return {"total": total, "average": round(average, 2)}
