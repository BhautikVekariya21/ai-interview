"""Data-access layer for Company Lens.

Exams, their generated questions, and candidate attempts live in four tables.
All SQL is isolated here so route handlers stay thin. JSON columns (category
breakdown, plagiarism summary, authenticity) are stored as text and parsed by
the caller.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional

from app.services.mysql_service import MySQLService


def _dumps(value: Any) -> Optional[str]:
    return json.dumps(value, ensure_ascii=False, default=str) if value is not None else None


def loads(raw: Optional[str]) -> Any:
    """Parse a stored JSON column safely."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


class CompanyLensRepository:
    def __init__(self, db: MySQLService):
        self._db = db

    # ── Exams ────────────────────────────────────────────────────────────

    def create_exam(
        self,
        *,
        exam_id: str,
        employer_id: Any,
        title: str,
        target_role: str,
        job_description: str,
        question_count: int,
        difficulty: str,
        status: str,
        created_at: datetime,
    ) -> None:
        s = self._db.get_session()
        s.execute(
            """
            INSERT INTO company_exams
                (id, employer_id, title, target_role, job_description,
                 question_count, difficulty, status, share_token, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                exam_id, employer_id, title, target_role, job_description,
                question_count, difficulty, status, None, created_at,
            ),
        )

    def list_exams_for_employer(self, employer_id: Any) -> List[Any]:
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM company_exams WHERE employer_id=%s ORDER BY created_at DESC",
            (employer_id,),
        )
        return list(rows)

    def get_exam(self, exam_id: str) -> Optional[Any]:
        s = self._db.get_session()
        row = s.execute(
            "SELECT * FROM company_exams WHERE id=%s LIMIT 1", (exam_id,)
        ).one()
        return row

    def get_exam_by_share_token(self, token: str) -> Optional[Any]:
        s = self._db.get_session()
        row = s.execute(
            "SELECT * FROM company_exams WHERE share_token=%s LIMIT 1", (token,)
        ).one()
        return row

    def list_published_exams(self, search: str = "") -> List[Any]:
        """Published exams for the public directory, newest first.

        When ``search`` is given, exams whose title, target role, or job
        description mention the term are matched — the directory search box
        filters on role phrases like "platform engineer".
        """
        s = self._db.get_session()
        if search:
            # LIKE treats % and _ as wildcards and \ as an escape, so a search
            # term containing them would silently match unintended rows. Escape
            # them and declare the escape character (works on SQLite and MySQL
            # alike — the session wrapper only rewrites %s placeholders).
            escaped = (
                search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            term = f"%{escaped}%"
            rows = s.execute(
                """
                SELECT * FROM company_exams
                WHERE status='published'
                  AND (title LIKE %s ESCAPE '\\' OR target_role LIKE %s ESCAPE '\\'
                       OR job_description LIKE %s ESCAPE '\\')
                ORDER BY created_at DESC
                """,
                (term, term, term),
            )
        else:
            rows = s.execute(
                "SELECT * FROM company_exams WHERE status='published' "
                "ORDER BY created_at DESC"
            )
        return list(rows)

    def publish_exam(self, exam_id: str, share_token: str) -> None:
        s = self._db.get_session()
        s.execute(
            "UPDATE company_exams SET status='published', share_token=%s WHERE id=%s",
            (share_token, exam_id),
        )

    def delete_exam(self, exam_id: str) -> None:
        s = self._db.get_session()
        s.execute("DELETE FROM company_exam_answers WHERE attempt_id IN "
                  "(SELECT id FROM company_exam_attempts WHERE exam_id=%s)", (exam_id,))
        s.execute("DELETE FROM company_exam_attempts WHERE exam_id=%s", (exam_id,))
        s.execute("DELETE FROM company_exam_questions WHERE exam_id=%s", (exam_id,))
        s.execute("DELETE FROM company_exams WHERE id=%s", (exam_id,))

    # ── Questions ────────────────────────────────────────────────────────

    def save_questions(self, exam_id: str, questions: List[dict]) -> None:
        s = self._db.get_session()
        for index, question in enumerate(questions, start=1):
            s.execute(
                """
                INSERT INTO company_exam_questions
                    (id, exam_id, question_number, question, category, difficulty, ideal_answer)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    f"{exam_id}-q{index}",
                    exam_id,
                    index,
                    question.get("question", ""),
                    question.get("category", "T"),
                    question.get("difficulty", "medium"),
                    question.get("ideal_answer") or "",
                ),
            )

    def get_questions(self, exam_id: str) -> List[Any]:
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM company_exam_questions WHERE exam_id=%s "
            "ORDER BY question_number ASC",
            (exam_id,),
        )
        return list(rows)

    # ── Attempts ─────────────────────────────────────────────────────────

    def create_attempt(
        self,
        *,
        attempt_id: str,
        exam_id: str,
        candidate_name: str,
        attempt_token: str,
        scorecard: dict,
        created_at: datetime,
    ) -> None:
        s = self._db.get_session()
        s.execute(
            """
            INSERT INTO company_exam_attempts
                (id, exam_id, candidate_name, attempt_token, overall_score,
                 overall_grade, recommendation, hire_decision, summary,
                 category_breakdown, plagiarism_summary, generated_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                attempt_id, exam_id, candidate_name, attempt_token,
                scorecard.get("overall_score", 0),
                scorecard.get("overall_grade", "C"),
                scorecard.get("recommendation", "Neutral"),
                scorecard.get("hire_decision", "consider"),
                scorecard.get("summary", ""),
                _dumps(scorecard.get("category_breakdown")),
                _dumps(scorecard.get("plagiarism_summary")),
                scorecard.get("generated_by") or "evaluator",
                created_at,
            ),
        )

    def save_answers(self, attempt_id: str, answers: List[dict]) -> None:
        s = self._db.get_session()
        for index, answer in enumerate(answers, start=1):
            s.execute(
                """
                INSERT INTO company_exam_answers
                    (id, attempt_id, question_number, question, category, answer,
                     score, grade, feedback, authenticity, strengths, improvements)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    f"{attempt_id}-a{index}",
                    attempt_id,
                    answer.get("question_number", index),
                    answer.get("question", ""),
                    answer.get("category", "T"),
                    answer.get("answer", ""),
                    answer.get("score", 0),
                    answer.get("grade", "Insufficient"),
                    answer.get("feedback", ""),
                    _dumps(answer.get("authenticity")),
                    _dumps(answer.get("strengths")),
                    _dumps(answer.get("improvements")),
                ),
            )

    def get_attempt(self, attempt_id: str) -> Optional[Any]:
        s = self._db.get_session()
        row = s.execute(
            "SELECT * FROM company_exam_attempts WHERE id=%s LIMIT 1", (attempt_id,)
        ).one()
        return row

    def get_attempt_by_token(self, attempt_token: str) -> Optional[Any]:
        s = self._db.get_session()
        row = s.execute(
            "SELECT * FROM company_exam_attempts WHERE attempt_token=%s LIMIT 1",
            (attempt_token,),
        ).one()
        return row

    def count_attempts_for_exam(self, exam_id: str) -> int:
        s = self._db.get_session()
        row = s.execute(
            "SELECT COUNT(*) AS n FROM company_exam_attempts WHERE exam_id=%s",
            (exam_id,),
        ).one()
        return int(getattr(row, "n", 0) or 0)

    def list_attempts_for_exam(self, exam_id: str, limit: int = 50) -> List[Any]:
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM company_exam_attempts WHERE exam_id=%s "
            "ORDER BY created_at DESC LIMIT %s",
            (exam_id, limit),
        )
        return list(rows)

    def get_answers(self, attempt_id: str) -> List[Any]:
        s = self._db.get_session()
        rows = s.execute(
            "SELECT * FROM company_exam_answers WHERE attempt_id=%s "
            "ORDER BY question_number ASC",
            (attempt_id,),
        )
        return list(rows)
