"""Schema for the service expansion: notifications, analytics, JD matching,
scheduler, negotiation, public API keys/webhooks, refresh tokens, LLM usage.

Kept separate from ``mysql_service._ensure_schema`` so the core schema stays
readable. Every statement is idempotent (``CREATE TABLE IF NOT EXISTS``) and
runs on both MySQL and the SQLite fallback. Dialect differences are handled by
small helpers rather than duplicating each table twice.
"""

from __future__ import annotations

from typing import Any

from loguru import logger


def _engine(is_sqlite: bool) -> str:
    return "" if is_sqlite else " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"


def _bool(is_sqlite: bool) -> str:
    return "INTEGER DEFAULT 0" if is_sqlite else "TINYINT(1) DEFAULT 0"


def _dt6(is_sqlite: bool) -> str:
    return "DATETIME" if is_sqlite else "DATETIME(6)"


def _index(cur: Any, is_sqlite: bool, name: str, table: str, cols: str, database: str | None) -> None:
    if is_sqlite:
        cur.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})")
        return
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.statistics "
        "WHERE table_schema=%s AND table_name=%s AND index_name=%s",
        (database, table, name),
    )
    if cur.fetchone()[0] == 0:
        cur.execute(f"CREATE INDEX {name} ON {table} ({cols})")


def ensure_extension_tables(conn: Any, *, is_sqlite: bool, database: str | None = None) -> None:
    """Create all extension tables. Safe to call on every startup."""
    if conn is None:
        return

    e = _engine(is_sqlite)
    b = _bool(is_sqlite)
    dt6 = _dt6(is_sqlite)

    cur = conn.cursor()
    try:
        # ── Auth: refresh tokens (rotating, revocable) ─────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token_hash VARCHAR(64) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                session_token_hash VARCHAR(64),
                family_id CHAR(36) NOT NULL,
                created_at {dt6},
                expires_at {dt6},
                revoked_at {dt6},
                replaced_by VARCHAR(64),
                user_agent VARCHAR(400),
                ip VARCHAR(64)
            ){e}
            """
        )
        _index(cur, is_sqlite, "refresh_tokens_user_idx", "refresh_tokens", "user_id", database)
        _index(cur, is_sqlite, "refresh_tokens_family_idx", "refresh_tokens", "family_id", database)

        # ── Auth: user plans (quotas) ──────────────────────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS user_plans (
                user_id CHAR(36) PRIMARY KEY,
                plan VARCHAR(32) NOT NULL DEFAULT 'free',
                updated_at {dt6}
            ){e}
            """
        )

        # ── LLM usage / cost tracking ──────────────────────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS llm_usage (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36),
                feature VARCHAR(64),
                provider VARCHAR(64),
                model VARCHAR(160),
                prompt_tokens INT,
                completion_tokens INT,
                latency_ms INT,
                cache_hit {b},
                cost_usd DOUBLE,
                created_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "llm_usage_created_idx", "llm_usage", "created_at", database)
        _index(cur, is_sqlite, "llm_usage_user_idx", "llm_usage", "user_id, created_at", database)

        # ── Notifications ──────────────────────────────────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS notifications (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                type VARCHAR(64) NOT NULL,
                title VARCHAR(300) NOT NULL,
                body VARCHAR(2000),
                action_url VARCHAR(600),
                data_json LONGTEXT,
                read_at {dt6},
                created_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "notifications_user_created_idx", "notifications", "user_id, created_at", database)

        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                user_id CHAR(36) PRIMARY KEY,
                email_enabled {b.replace('DEFAULT 0', 'DEFAULT 1')},
                in_app_enabled {b.replace('DEFAULT 0', 'DEFAULT 1')},
                reminders_enabled {b.replace('DEFAULT 0', 'DEFAULT 1')},
                weekly_digest_enabled {b.replace('DEFAULT 0', 'DEFAULT 1')},
                quiet_hours_start INT,
                quiet_hours_end INT,
                timezone VARCHAR(64),
                updated_at {dt6}
            ){e}
            """
        )

        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS notification_deliveries (
                id CHAR(36) PRIMARY KEY,
                notification_id CHAR(36),
                channel VARCHAR(16) NOT NULL,
                status VARCHAR(16) NOT NULL,
                attempts INT DEFAULT 0,
                last_error VARCHAR(1000),
                next_attempt_at {dt6},
                sent_at {dt6},
                created_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "notif_deliv_status_idx", "notification_deliveries", "status, next_attempt_at", database)

        # ── Job description matcher ────────────────────────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS jd_matches (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                job_title VARCHAR(300),
                company VARCHAR(200),
                jd_text LONGTEXT,
                resume_hash VARCHAR(64),
                match_score INT,
                result_json LONGTEXT,
                created_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "jd_matches_user_idx", "jd_matches", "user_id, created_at", database)

        # ── Scheduler ──────────────────────────────────────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS scheduled_sessions (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                title VARCHAR(300) NOT NULL,
                mode VARCHAR(48) NOT NULL,
                config_json LONGTEXT,
                starts_at {dt6} NOT NULL,
                duration_minutes INT DEFAULT 45,
                timezone VARCHAR(64),
                recurrence VARCHAR(16) DEFAULT 'none',
                recurrence_until {dt6},
                reminder_minutes_before INT DEFAULT 30,
                reminder_sent_at {dt6},
                status VARCHAR(16) DEFAULT 'scheduled',
                completed_history_id VARCHAR(120),
                created_at {dt6},
                updated_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "sched_user_starts_idx", "scheduled_sessions", "user_id, starts_at", database)
        _index(cur, is_sqlite, "sched_reminder_idx", "scheduled_sessions", "status, starts_at", database)

        # ── Public API keys + webhooks ─────────────────────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS api_keys (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                name VARCHAR(120) NOT NULL,
                key_prefix VARCHAR(16) NOT NULL,
                key_hash VARCHAR(64) NOT NULL,
                scopes VARCHAR(600),
                rate_limit_per_minute INT DEFAULT 60,
                last_used_at {dt6},
                revoked_at {dt6},
                created_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "api_keys_hash_idx", "api_keys", "key_hash", database)
        _index(cur, is_sqlite, "api_keys_user_idx", "api_keys", "user_id", database)

        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS webhook_endpoints (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                url VARCHAR(1000) NOT NULL,
                description VARCHAR(300),
                secret_hash VARCHAR(64) NOT NULL,
                secret_hint VARCHAR(12),
                events VARCHAR(600),
                active {b.replace('DEFAULT 0', 'DEFAULT 1')},
                created_at {dt6},
                updated_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "webhook_endpoints_user_idx", "webhook_endpoints", "user_id", database)

        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS webhook_deliveries (
                id CHAR(36) PRIMARY KEY,
                endpoint_id CHAR(36) NOT NULL,
                user_id CHAR(36) NOT NULL,
                event VARCHAR(64) NOT NULL,
                payload_json LONGTEXT,
                status VARCHAR(16) NOT NULL,
                attempts INT DEFAULT 0,
                response_status INT,
                last_error VARCHAR(1000),
                next_attempt_at {dt6},
                delivered_at {dt6},
                created_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "webhook_deliv_status_idx", "webhook_deliveries", "status, next_attempt_at", database)
        _index(cur, is_sqlite, "webhook_deliv_endpoint_idx", "webhook_deliveries", "endpoint_id, created_at", database)

        # ── Salary negotiation sessions ────────────────────────────────────
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS negotiation_sessions (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                role VARCHAR(200),
                level VARCHAR(80),
                location VARCHAR(160),
                initial_offer_json LONGTEXT,
                target_json LONGTEXT,
                market_estimate_json LONGTEXT,
                transcript_json LONGTEXT,
                status VARCHAR(16) DEFAULT 'active',
                outcome_json LONGTEXT,
                created_at {dt6},
                updated_at {dt6}
            ){e}
            """
        )
        _index(cur, is_sqlite, "negotiation_user_idx", "negotiation_sessions", "user_id, created_at", database)

        conn.commit()
    except Exception as exc:  # pragma: no cover - best-effort
        logger.warning(f"extension schema setup failed: {exc}")
    finally:
        cur.close()
