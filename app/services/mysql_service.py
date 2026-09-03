from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Graceful import — mirrors the pattern used by tracing_service
try:
    import mysql.connector
    from mysql.connector import errorcode

    _HAS_MYSQL_DRIVER = True
except Exception:  # pragma: no cover - runtime env dependent
    mysql = None  # type: ignore[assignment]
    errorcode = None  # type: ignore[assignment]
    _HAS_MYSQL_DRIVER = False
    logger.warning("mysql-connector-python not installed — MySQL features will be unavailable")


_DATETIME_COLUMNS = {
    "created_at",
    "updated_at",
    "expires_at",
    "reset_token_expires_at",
    "verification_expires_at",
    "lockout_until",
<<<<<<< HEAD
    # extension tables
    "revoked_at",
    "read_at",
    "sent_at",
    "next_attempt_at",
    "starts_at",
    "recurrence_until",
    "reminder_sent_at",
    "last_used_at",
    "delivered_at",
=======
>>>>>>> origin/main
}


class _Row:
    """Attribute-accessible row wrapper.

    Timezone-aware datetimes are attached for DATETIME/DATETIME(6) columns so
    comparisons against aware datetimes (e.g. datetime.now(timezone.utc)) keep working,
    matching the tz-aware timestamps expected by the rest of the codebase.
    """

    def __init__(self, columns: list[str], values: tuple[Any, ...]):
        for col, val in zip(columns, values):
            if isinstance(val, datetime) and val.tzinfo is None and col in _DATETIME_COLUMNS:
                val = val.replace(tzinfo=timezone.utc)
            object.__setattr__(self, col, val)
        object.__setattr__(self, "_columns", columns)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        cols = object.__getattribute__(self, "_columns")
        vals = {c: getattr(self, c) for c in cols}
        return f"_Row({vals!r})"


class _ResultSet:
    def __init__(self, rows: list[_Row], rowcount: int = 0):
        self._rows = rows
        self.rowcount = rowcount

    def one(self) -> Optional[_Row]:
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)


class _SessionWrapper:
    """Thin wrapper around a connection exposing a Session-like `.execute()` API."""

    def __init__(self, conn: Any, is_sqlite: bool = False):
        self._conn = conn
        self.is_sqlite = is_sqlite

    def execute(self, sql: str, params: Any = ()) -> _ResultSet:
        if params is None:
            params = ()
        # Normalize a bare scalar/UUID into a 1-tuple for parameterized queries.
        if not isinstance(params, (list, tuple)):
            params = (params,)

        # Normalize parameters (e.g. UUID to string)
        params = tuple(str(p) if _is_uuid(p) else p for p in params)

        if self.is_sqlite:
            # SQLite uses '?' placeholder instead of '%s'
            sql = sql.replace("%s", "?")
            
            # Map tz-aware datetime objects to native naive datetime or ISO strings
            new_params = []
            for p in params:
                if isinstance(p, datetime):
                    if p.tzinfo is not None:
                        p = p.astimezone(timezone.utc).replace(tzinfo=None)
                new_params.append(p)
            params = tuple(new_params)

        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            if cursor.description:
                columns = [d[0] for d in cursor.description]
                rows = []
                for row in cursor.fetchall():
                    if self.is_sqlite:
                        # SQLite returns dates as string; parse them if matching a datetime column
                        parsed_row = []
                        for col, val in zip(columns, row):
                            if col in _DATETIME_COLUMNS and isinstance(val, str):
                                try:
                                    if "." in val:
                                        val = datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
                                    else:
                                        val = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                                except Exception:
                                    pass
                            parsed_row.append(val)
                        rows.append(_Row(columns, tuple(parsed_row)))
                    else:
                        rows.append(_Row(columns, row))
                result = _ResultSet(rows, rowcount=cursor.rowcount)
            else:
                self._conn.commit()
                result = _ResultSet([], rowcount=cursor.rowcount)
            return result
        finally:
            cursor.close()


def _is_uuid(value: Any) -> bool:
    return type(value).__name__ == "UUID"


class MySQLService:
    def __init__(self) -> None:
        self._conn: Optional[Any] = None
        self._init_error: Optional[str] = None
        self.is_sqlite = False

        # Attempt to initialize MySQL first
        try:
            if not _HAS_MYSQL_DRIVER:
                raise ImportError("mysql-connector-python package is not installed")
            self._connect()
            self._ensure_schema()
            logger.info("Successfully connected to MySQL database.")
        except Exception as exc:
            # Fallback to local SQLite database if MySQL connection fails
            logger.warning(f"MySQL connection failed: {exc}. Falling back to SQLite database.")
            try:
                import sqlite3
                self.is_sqlite = True
                self._conn = sqlite3.connect("ai_interview.db", check_same_thread=False)
                self._ensure_schema()
                self._init_error = None
                logger.info("Successfully initialized SQLite fallback database (ai_interview.db).")
            except Exception as sqlite_exc:
                self._init_error = f"MySQL connection failed ({exc}). SQLite fallback also failed ({sqlite_exc})."
                logger.error(f"Failed to initialize any database: {self._init_error}")

    def _connect(self) -> None:
        # Connect without a database first to create it if it doesn't exist
        bootstrap_conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
        )
        try:
            cur = bootstrap_conn.cursor()
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DATABASE}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            bootstrap_conn.commit()
            cur.close()
        finally:
            bootstrap_conn.close()

        self._conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            autocommit=True,
        )

    def _ensure_schema(self) -> None:
        if not self._conn:
            return

        cur = self._conn.cursor()
        try:
            if self.is_sqlite:
                # Schema for SQLite fallback
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id CHAR(36) PRIMARY KEY,
                        email VARCHAR(320) UNIQUE,
                        full_name VARCHAR(255),
                        password_hash VARCHAR(255),
                        auth_provider VARCHAR(50),
                        created_at DATETIME,
                        updated_at DATETIME,
                        reset_token_hash VARCHAR(64),
                        reset_token_expires_at DATETIME,
                        email_verified INTEGER DEFAULT 0,
                        verification_token_hash VARCHAR(64),
                        verification_expires_at DATETIME
                    )
                    """
                )


                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        token VARCHAR(512) PRIMARY KEY,
                        user_id CHAR(36),
                        created_at DATETIME,
                        expires_at DATETIME
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions (user_id)")

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS history (
                        user_id CHAR(36),
                        created_at DATETIME,
                        candidate_name VARCHAR(255),
                        overall_score INT,
                        completion_rate INT,
                        final_grade VARCHAR(50),
                        total_questions INT,
                        details_json LONGTEXT,
                        PRIMARY KEY (user_id, created_at)
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS history_user_created_idx ON history (user_id, created_at)")

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_data (
                        user_id CHAR(36) PRIMARY KEY,
                        profile LONGTEXT,
                        session_snapshot LONGTEXT,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                    """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blog_posts (
                        id CHAR(36) PRIMARY KEY,
                        user_id CHAR(36),
                        author_name VARCHAR(255),
                        title VARCHAR(300),
                        category VARCHAR(80),
                        excerpt VARCHAR(600),
                        content LONGTEXT,
                        created_at DATETIME
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS blog_posts_created_idx ON blog_posts (created_at)")

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blog_feedback (
                        id CHAR(36) PRIMARY KEY,
                        post_id CHAR(36),
                        user_id CHAR(36),
                        author_name VARCHAR(255),
                        rating INT,
                        comment VARCHAR(2000),
                        created_at DATETIME
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS blog_feedback_post_idx ON blog_feedback (post_id)")

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_reviews (
                        id CHAR(36) PRIMARY KEY,
                        user_id CHAR(36),
                        author_name VARCHAR(255),
                        rating INT,
                        title VARCHAR(200),
                        review VARCHAR(4000),
                        created_at DATETIME
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS app_reviews_created_idx ON app_reviews (created_at)")

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                        id CHAR(36) PRIMARY KEY,
                        email VARCHAR(320) UNIQUE,
                        created_at DATETIME
                    )
                    """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS coding_submissions (
                        id CHAR(36) PRIMARY KEY,
                        session_id VARCHAR(64),
                        user_id CHAR(36),
                        problem_id VARCHAR(120),
                        problem_title VARCHAR(255),
                        language VARCHAR(40),
                        code LONGTEXT,
                        passed INTEGER DEFAULT 0,
                        tests_passed INTEGER DEFAULT 0,
                        tests_total INTEGER DEFAULT 0,
                        runtime_ms REAL DEFAULT 0,
                        created_at DATETIME
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS coding_submissions_session_idx "
                    "ON coding_submissions (session_id, created_at)"
                )

                # Game Tape — persisted replay share documents keyed by an
                # unguessable token (SQLite fallback branch).
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS interview_replays (
                        token VARCHAR(64) PRIMARY KEY,
                        session_id VARCHAR(64),
                        user_id CHAR(36),
                        candidate_name VARCHAR(255),
                        payload LONGTEXT,
                        created_at DATETIME
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS interview_replays_session_idx "
                    "ON interview_replays (session_id)"
                )

                # Company Lens — employer-published exams, questions, attempts,
                # and per-attempt answers (SQLite fallback branch).
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exams (
                        id CHAR(36) PRIMARY KEY,
                        employer_id CHAR(36),
                        title VARCHAR(255),
                        target_role VARCHAR(160),
                        job_description LONGTEXT,
                        question_count INTEGER,
                        difficulty VARCHAR(20),
                        status VARCHAR(20),
                        share_token VARCHAR(64),
                        created_at DATETIME
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS company_exams_employer_idx "
                    "ON company_exams (employer_id)"
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exam_questions (
                        id CHAR(36) PRIMARY KEY,
                        exam_id CHAR(36),
                        question_number INTEGER,
                        question LONGTEXT,
                        category VARCHAR(10),
                        difficulty VARCHAR(20),
                        ideal_answer LONGTEXT
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS company_exam_questions_exam_idx "
                    "ON company_exam_questions (exam_id, question_number)"
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exam_attempts (
                        id CHAR(36) PRIMARY KEY,
                        exam_id CHAR(36),
                        candidate_name VARCHAR(255),
                        attempt_token VARCHAR(64),
                        overall_score INTEGER,
                        overall_grade VARCHAR(50),
                        recommendation VARCHAR(100),
                        hire_decision VARCHAR(50),
                        summary LONGTEXT,
                        category_breakdown LONGTEXT,
                        plagiarism_summary LONGTEXT,
                        generated_by VARCHAR(20),
                        created_at DATETIME
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS company_exam_attempts_exam_idx "
                    "ON company_exam_attempts (exam_id, created_at)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS company_exam_attempts_token_idx "
                    "ON company_exam_attempts (attempt_token)"
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exam_answers (
                        id CHAR(36) PRIMARY KEY,
                        attempt_id CHAR(36),
                        question_number INTEGER,
                        question LONGTEXT,
                        category VARCHAR(10),
                        answer LONGTEXT,
                        score INTEGER,
                        grade VARCHAR(50),
                        feedback LONGTEXT,
                        authenticity LONGTEXT,
                        strengths LONGTEXT,
                        improvements LONGTEXT
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS company_exam_answers_attempt_idx "
                    "ON company_exam_answers (attempt_id, question_number)"
                )
            else:
                # Schema for MySQL
                # Users table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id CHAR(36) PRIMARY KEY,
                        email VARCHAR(320) UNIQUE,
                        full_name VARCHAR(255),
                        password_hash VARCHAR(255),
                        auth_provider VARCHAR(50),
                        created_at DATETIME,
                        updated_at DATETIME,
                        reset_token_hash VARCHAR(64),
                        reset_token_expires_at DATETIME,
                        email_verified TINYINT(1) DEFAULT 0,
                        verification_token_hash VARCHAR(64),
                        verification_expires_at DATETIME,
                        INDEX users_reset_token_idx (reset_token_hash),
                        INDEX users_verification_idx (verification_token_hash)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # Sessions table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        token VARCHAR(512) PRIMARY KEY,
                        user_id CHAR(36),
                        created_at DATETIME,
                        expires_at DATETIME,
                        INDEX sessions_user_id_idx (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # History table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS history (
                        user_id CHAR(36),
                        created_at DATETIME(6),
                        candidate_name VARCHAR(255),
                        overall_score INT,
                        completion_rate INT,
                        final_grade VARCHAR(50),
                        total_questions INT,
                        details_json LONGTEXT,
                        PRIMARY KEY (user_id, created_at),
                        INDEX history_user_created_idx (user_id, created_at DESC)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # User Data table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_data (
                        user_id CHAR(36) PRIMARY KEY,
                        profile LONGTEXT,
                        session_snapshot LONGTEXT,
                        created_at DATETIME,
                        updated_at DATETIME
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # Blog posts table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blog_posts (
                        id CHAR(36) PRIMARY KEY,
                        user_id CHAR(36),
                        author_name VARCHAR(255),
                        title VARCHAR(300),
                        category VARCHAR(80),
                        excerpt VARCHAR(600),
                        content LONGTEXT,
                        created_at DATETIME(6),
                        INDEX blog_posts_created_idx (created_at DESC)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # Blog feedback table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blog_feedback (
                        id CHAR(36) PRIMARY KEY,
                        post_id CHAR(36),
                        user_id CHAR(36),
                        author_name VARCHAR(255),
                        rating INT,
                        comment VARCHAR(2000),
                        created_at DATETIME(6),
                        INDEX blog_feedback_post_idx (post_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # App reviews table (feedback forum)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_reviews (
                        id CHAR(36) PRIMARY KEY,
                        user_id CHAR(36),
                        author_name VARCHAR(255),
                        rating INT,
                        title VARCHAR(200),
                        review VARCHAR(4000),
                        created_at DATETIME(6),
                        INDEX app_reviews_created_idx (created_at DESC)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # Newsletter subscribers table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                        id CHAR(36) PRIMARY KEY,
                        email VARCHAR(320) UNIQUE,
                        created_at DATETIME(6)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # Coding submissions, scoped by interview session so two
                # interviews running against the same problem stay separate.
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS coding_submissions (
                        id CHAR(36) PRIMARY KEY,
                        session_id VARCHAR(64),
                        user_id CHAR(36),
                        problem_id VARCHAR(120),
                        problem_title VARCHAR(255),
                        language VARCHAR(40),
                        code LONGTEXT,
                        passed TINYINT(1) DEFAULT 0,
                        tests_passed INT DEFAULT 0,
                        tests_total INT DEFAULT 0,
                        runtime_ms DOUBLE DEFAULT 0,
                        created_at DATETIME(6),
                        INDEX coding_submissions_session_idx (session_id, created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # Game Tape — persisted replay share documents keyed by an
                # unguessable token (MySQL branch).
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS interview_replays (
                        token VARCHAR(64) PRIMARY KEY,
                        session_id VARCHAR(64),
                        user_id CHAR(36),
                        candidate_name VARCHAR(255),
                        payload LONGTEXT,
                        created_at DATETIME(6),
                        INDEX interview_replays_session_idx (session_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                # Company Lens — employer-published exams, questions, attempts,
                # and per-attempt answers (MySQL branch).
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exams (
                        id CHAR(36) PRIMARY KEY,
                        employer_id CHAR(36),
                        title VARCHAR(255),
                        target_role VARCHAR(160),
                        job_description LONGTEXT,
                        question_count INT,
                        difficulty VARCHAR(20),
                        status VARCHAR(20),
                        share_token VARCHAR(64),
                        created_at DATETIME(6),
                        INDEX company_exams_employer_idx (employer_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exam_questions (
                        id CHAR(36) PRIMARY KEY,
                        exam_id CHAR(36),
                        question_number INT,
                        question LONGTEXT,
                        category VARCHAR(10),
                        difficulty VARCHAR(20),
                        ideal_answer LONGTEXT,
                        INDEX company_exam_questions_exam_idx (exam_id, question_number)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exam_attempts (
                        id CHAR(36) PRIMARY KEY,
                        exam_id CHAR(36),
                        candidate_name VARCHAR(255),
                        attempt_token VARCHAR(64),
                        overall_score INT,
                        overall_grade VARCHAR(50),
                        recommendation VARCHAR(100),
                        hire_decision VARCHAR(50),
                        summary LONGTEXT,
                        category_breakdown LONGTEXT,
                        plagiarism_summary LONGTEXT,
                        generated_by VARCHAR(20),
                        created_at DATETIME(6),
                        INDEX company_exam_attempts_exam_idx (exam_id, created_at),
                        INDEX company_exam_attempts_token_idx (attempt_token)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS company_exam_answers (
                        id CHAR(36) PRIMARY KEY,
                        attempt_id CHAR(36),
                        question_number INT,
                        question LONGTEXT,
                        category VARCHAR(10),
                        answer LONGTEXT,
                        score INT,
                        grade VARCHAR(50),
                        feedback LONGTEXT,
                        authenticity LONGTEXT,
                        strengths LONGTEXT,
                        improvements LONGTEXT,
                        INDEX company_exam_answers_attempt_idx (attempt_id, question_number)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            self._conn.commit()
        finally:
            cur.close()

        self._migrate_users_columns()

<<<<<<< HEAD
        # Tables for the service expansion (notifications, scheduler, JD
        # matcher, API keys/webhooks, negotiation, refresh tokens, LLM usage).
        from app.services.schema_extensions import ensure_extension_tables

        ensure_extension_tables(
            self._conn,
            is_sqlite=self.is_sqlite,
            database=None if self.is_sqlite else settings.MYSQL_DATABASE,
        )

=======
>>>>>>> origin/main
    def _migrate_users_columns(self) -> None:
        """Idempotently add/rename auth-security columns on a pre-existing users table.

        CREATE TABLE IF NOT EXISTS won't alter a table that already exists, so
        installs that predate the email-verification / hashed-reset-token work
        need these columns backfilled. Safe to run on every startup.
        """
        if not self._conn:
            return

        desired = {
            "reset_token_hash": "VARCHAR(64)",
            "reset_token_expires_at": "DATETIME",
            "email_verified": "TINYINT(1) DEFAULT 0" if not self.is_sqlite else "INTEGER DEFAULT 0",
            "verification_token_hash": "VARCHAR(64)",
            "verification_expires_at": "DATETIME",
        }

        cur = self._conn.cursor()
        try:
            existing: set[str] = set()
            if self.is_sqlite:
                for row in cur.execute("PRAGMA table_info(users)").fetchall():
                    existing.add(row[1])
            else:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema=%s AND table_name='users'",
                    (settings.MYSQL_DATABASE,),
                )
                existing = {r[0] for r in cur.fetchall()}

            # Carry over data from a legacy plaintext reset_token column if present.
            has_legacy_reset = "reset_token" in existing

            for col, ddl in desired.items():
                if col not in existing:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")

            # Indexes created here (after columns are guaranteed present) so a
            # pre-existing table without these columns doesn't fail at CREATE INDEX.
            if self.is_sqlite:
                cur.execute("CREATE INDEX IF NOT EXISTS users_reset_token_idx ON users (reset_token_hash)")
                cur.execute("CREATE INDEX IF NOT EXISTS users_verification_idx ON users (verification_token_hash)")
            else:
                for idx_name, idx_col in (
                    ("users_reset_token_idx", "reset_token_hash"),
                    ("users_verification_idx", "verification_token_hash"),
                ):
                    cur.execute(
                        "SELECT COUNT(*) FROM information_schema.statistics "
                        "WHERE table_schema=%s AND table_name='users' AND index_name=%s",
                        (settings.MYSQL_DATABASE, idx_name),
                    )
                    if cur.fetchone()[0] == 0:
                        cur.execute(f"CREATE INDEX {idx_name} ON users ({idx_col})")

            # We intentionally do NOT copy legacy plaintext reset tokens into the
            # hashed column — they should simply be invalidated. Drop is optional
            # and skipped to avoid destructive migrations.
            _ = has_legacy_reset
            self._conn.commit()
        except Exception as exc:  # pragma: no cover - best-effort migration
            logger.warning(f"users column migration skipped/failed: {exc}")
        finally:
            cur.close()

    def get_session(self) -> _SessionWrapper:
        if not self._conn:
            raise RuntimeError(
                "MySQL connection is not initialized. "
                + (f"Reason: {self._init_error}" if self._init_error else "Check MySQL connectivity.")
            )
        return _SessionWrapper(self._conn, is_sqlite=self.is_sqlite)

    def ping(self) -> bool:
        if not self._conn:
            return False
        try:
            cur = self._conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchall()
            cur.close()
            return True
        except Exception as e:
            logger.error(f"MySQL ping failed: {e}")
            return False

    def close(self):
        if self._conn:
            self._conn.close()


@lru_cache
def get_mysql() -> MySQLService:
    return MySQLService()


def get_mysql_health() -> dict:
    try:
        db = get_mysql()
        is_healthy = db.ping()
        return {
            "status": "healthy" if is_healthy else "unavailable",
            "database": settings.MYSQL_DATABASE,
            "driver_installed": _HAS_MYSQL_DRIVER,
        }
    except Exception as exc:
        return {
            "status": "unavailable",
            "database": settings.MYSQL_DATABASE,
            "driver_installed": _HAS_MYSQL_DRIVER,
            "error": str(exc),
        }
