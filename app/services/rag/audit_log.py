"""Retrieval audit logging for RAG.

Persists every retrieval (query, retrieved chunk ids, similarity scores) via the
existing MySQLService — MySQL in prod, SQLite fallback locally — so the audit
trail rides the same durable store as the rest of the app. Failures here never
break a retrieval: auditing is best-effort and logged, not raised.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Sequence

from loguru import logger

from app.core.config import settings
from app.services.rag.vector_store import RetrievedChunk


_SCHEMA_READY = False


def _redact_query(query_text: str) -> str:
    """PII-safe representation of a retrieval query.

    Resume/JD/answer queries can carry names, contact info, and employers. We must
    never persist that raw text to the audit trail. Instead we store a stable
    SHA-256 hash (lets us correlate identical queries and detect replays) plus the
    length — enough for debugging, zero plaintext PII.
    """
    text = query_text or ""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}:len={len(text)}"



def _ensure_table() -> bool:
    """Create the audit table once per process. Returns False if the DB is down."""
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return True
    try:
        from app.services.mysql_service import get_mysql

        session = get_mysql().get_session()
        session.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_retrieval_audit (
                id CHAR(36) PRIMARY KEY,
                created_at DATETIME,
                candidate_id VARCHAR(255),
                role VARCHAR(255),
                operation VARCHAR(64),
                query_text LONGTEXT,
                retrieved_json LONGTEXT
            )
            """
        )
        _SCHEMA_READY = True
        return True
    except Exception as exc:
        logger.warning(f"RAG audit table unavailable, skipping audit: {exc}")
        return False


def log_retrieval(
    candidate_id: str,
    role: str,
    operation: str,
    query_text: str,
    retrieved: Sequence[RetrievedChunk],
) -> None:
    """Best-effort audit write. Never raises into the retrieval path."""
    if not settings.RAG_AUDIT_ENABLED:
        return
    if not _ensure_table():
        return
    try:
        from app.services.mysql_service import get_mysql

        retrieved_payload: List[dict] = [
            {
                "chunk_id": rc.chunk.chunk_id,
                "source_type": rc.chunk.source_type,
                "distance": rc.distance,
                "similarity": rc.similarity,
            }
            for rc in retrieved
        ]
        session = get_mysql().get_session()
        session.execute(
            """
            INSERT INTO rag_retrieval_audit
                (id, created_at, candidate_id, role, operation, query_text, retrieved_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                datetime.now(timezone.utc),
                candidate_id[:255],
                role[:255],
                operation[:64],
                # PII redaction (item 13): store a hash of the query, not the raw
                # resume/answer text. Chunk provenance is retained as ids below.
                _redact_query(query_text),
                json.dumps(retrieved_payload, ensure_ascii=False),
            ),
        )
    except Exception as exc:
        logger.warning(f"RAG audit write failed (non-fatal): {exc}")
