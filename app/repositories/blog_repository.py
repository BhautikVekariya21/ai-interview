"""Data-access layer for community blog posts and feedback.

All SQL touching the `blog_posts` and `blog_feedback` tables lives here so route
handlers stay thin controllers. Rows are returned as the attribute-accessible
`_Row` objects the MySQL/SQLite session wrapper produces.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from app.services.mysql_service import MySQLService


class BlogRepository:
    def __init__(self, db: MySQLService):
        self._db = db

    def insert_post(
        self,
        post_id: str,
        user_id: Any,
        author_name: str,
        title: str,
        category: str,
        excerpt: str,
        content: str,
        created_at: datetime,
    ) -> None:
        s = self._db.get_session()
        s.execute(
            """
            INSERT INTO blog_posts (id, user_id, author_name, title, category, excerpt, content, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (post_id, user_id, author_name, title, category, excerpt, content, created_at),
        )

    def list_posts(self, limit: int = 50, category: Optional[str] = None) -> List[Any]:
        s = self._db.get_session()
        if category:
            rows = s.execute(
                "SELECT * FROM blog_posts WHERE category=%s ORDER BY created_at DESC LIMIT %s",
                (category, limit),
            )
        else:
            rows = s.execute(
                "SELECT * FROM blog_posts ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
        return list(rows)

    def get_post(self, post_id: str) -> Optional[Any]:
        s = self._db.get_session()
        rows = list(s.execute("SELECT * FROM blog_posts WHERE id=%s LIMIT 1", (post_id,)))
        return rows[0] if rows else None

    def insert_feedback(
        self,
        feedback_id: str,
        post_id: str,
        user_id: Any,
        author_name: str,
        rating: int,
        comment: str,
        created_at: datetime,
    ) -> None:
        s = self._db.get_session()
        s.execute(
            """
            INSERT INTO blog_feedback (id, post_id, user_id, author_name, rating, comment, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (feedback_id, post_id, user_id, author_name, rating, comment, created_at),
        )

    def list_feedback(self, post_id: str, limit: int = 100) -> List[Any]:
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM blog_feedback WHERE post_id=%s ORDER BY created_at DESC LIMIT %s",
            (post_id, limit),
        )
        return list(rows)

    def get_subscriber(self, email: str) -> Optional[Any]:
        s = self._db.get_session()
        rows = list(
            s.execute(
                "SELECT * FROM newsletter_subscribers WHERE email=%s LIMIT 1",
                (email,),
            )
        )
        return rows[0] if rows else None

    def insert_subscriber(self, sub_id: str, email: str, created_at: datetime) -> None:
        s = self._db.get_session()
        s.execute(
            "INSERT INTO newsletter_subscribers (id, email, created_at) VALUES (%s, %s, %s)",
            (sub_id, email, created_at),
        )
