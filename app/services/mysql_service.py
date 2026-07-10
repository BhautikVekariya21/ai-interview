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
                        reset_token VARCHAR(255),
                        reset_token_expires_at DATETIME
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS users_reset_token_idx ON users (reset_token)")

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
                        reset_token VARCHAR(255),
                        reset_token_expires_at DATETIME,
                        INDEX users_reset_token_idx (reset_token)
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
            self._conn.commit()
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
