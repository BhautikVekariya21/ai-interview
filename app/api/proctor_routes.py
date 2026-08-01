"""
Proctoring API routes — screen recording and integrity events.

The candidate's screen is captured in the browser (`getDisplayMedia`) and
streamed here in short chunks while the interview or the coding round is open.
Chunks are appended to a single file per recording so a reviewer can play the
sitting back end to end, and integrity events (share denied, share stopped, only
a tab shared instead of the whole screen, tab switches) are appended to a JSONL
log beside it.

Nothing here decides whether a candidate cheated. It records what happened so a
human can judge, which is the only defensible thing an automated proctor can do.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings


proctor_router = APIRouter(
    prefix="/proctor",
    tags=["Module 17: Proctoring"],
)

# Ids arrive from the browser and are used to build paths, so they are matched
# against an allowlist rather than merely escaped.
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_SURFACES = {"interview", "coding"}
_ALLOWED_SUFFIXES = {".webm", ".mp4"}
_EVENTS_FILE = "events.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(value: str, label: str) -> str:
    if not value or not _SAFE_ID.match(value) or value in {".", ".."}:
        raise HTTPException(400, detail=f"Invalid {label}")
    return value


def _safe_surface(value: str) -> str:
    if value not in _SURFACES:
        raise HTTPException(
            400, detail=f"Invalid surface — expected one of {sorted(_SURFACES)}"
        )
    return value


def _session_dir(session_id: str, create: bool = True) -> Path:
    """Resolve the per-session directory, refusing anything outside the root."""
    root = Path(settings.PROCTOR_RECORDINGS_DIR).resolve()
    target = (root / _safe_id(session_id, "session_id")).resolve()
    if target != root and root not in target.parents:
        raise HTTPException(400, detail="Invalid session_id")
    if create:
        target.mkdir(parents=True, exist_ok=True)
    return target


def _append_event(session_id: str, payload: Dict[str, Any]) -> None:
    """Append one integrity event to the session's JSONL log."""
    path = _session_dir(session_id) / _EVENTS_FILE
    line = json.dumps(payload, ensure_ascii=False, default=str)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


# ─── SCHEMAS ──────────────────────────────────────────────────


class ProctorEvent(BaseModel):
    """An integrity-relevant thing that happened in the candidate's browser."""

    session_id: str
    surface: str = Field(default="interview", description="interview | coding")
    kind: str = Field(
        ...,
        max_length=64,
        description=(
            "screen_share_granted | screen_share_denied | screen_share_stopped | "
            "screen_share_wrong_surface | recorder_error | upload_failed | "
            "tab_switch | window_blur | fullscreen_exit | devtools_blocked | "
            "copy_blocked | paste_blocked"
        ),
    )
    detail: Optional[str] = Field(default=None, max_length=2000)
    question_index: Optional[int] = None
    occurred_at: Optional[str] = Field(
        default=None, description="Client ISO timestamp; the server records its own too."
    )


class ProctorEventResponse(BaseModel):
    success: bool
    recorded_at: str


class ChunkUploadResponse(BaseModel):
    success: bool
    filename: str
    chunk_index: int
    total_bytes: int


class RecordingInfo(BaseModel):
    filename: str
    surface: str
    size_bytes: int
    created_at: str
    modified_at: str


class SessionRecordingsResponse(BaseModel):
    session_id: str
    recordings: List[RecordingInfo]
    events: List[Dict[str, Any]]
    total_bytes: int


# ─── SCREEN RECORDING UPLOAD ──────────────────────────────────


@proctor_router.post(
    "/screen/chunk",
    response_model=ChunkUploadResponse,
    summary="Upload one screen-recording chunk",
)
async def upload_screen_chunk(
    session_id: str = Query(..., description="Interview session id"),
    surface: str = Query(default="interview", description="interview | coding"),
    chunk_index: int = Query(default=0, ge=0),
    file: UploadFile = File(..., description="Video chunk from MediaRecorder"),
):
    """
    Append a screen-capture chunk to this session's recording.

    `MediaRecorder` with a timeslice emits a header-bearing first blob followed by
    continuation clusters, so appending the chunks in order reproduces a single
    playable file. Uploading during the sitting (rather than one blob at the end)
    means a candidate who kills the tab still leaves behind everything recorded up
    to that moment.
    """
    surface = _safe_surface(surface)
    directory = _session_dir(session_id)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        suffix = ".webm"

    data = await file.read()
    if not data:
        raise HTTPException(400, detail="Chunk is empty")
    if len(data) > settings.PROCTOR_MAX_CHUNK_BYTES:
        raise HTTPException(
            413,
            detail=(
                f"Chunk is {len(data):,} bytes, over the "
                f"{settings.PROCTOR_MAX_CHUNK_BYTES:,} byte limit"
            ),
        )

    target = directory / f"screen-{surface}{suffix}"
    # "ab" so an interrupted upload cannot truncate what is already stored, and a
    # reconnecting recorder continues the same file.
    with target.open("ab") as fh:
        fh.write(data)

    total = target.stat().st_size
    logger.debug(
        f"/proctor/screen/chunk: {session_id}/{surface} #{chunk_index} "
        f"+{len(data):,}B → {total:,}B"
    )
    return ChunkUploadResponse(
        success=True,
        filename=target.name,
        chunk_index=chunk_index,
        total_bytes=total,
    )


# ─── INTEGRITY EVENTS ─────────────────────────────────────────


@proctor_router.post(
    "/event",
    response_model=ProctorEventResponse,
    summary="Record an integrity event",
)
async def record_event(event: ProctorEvent):
    """Log a proctoring event (share denied/stopped, tab switch, blocked copy…)."""
    _safe_surface(event.surface)
    recorded_at = _now()
    _append_event(
        event.session_id,
        {
            "kind": event.kind,
            "surface": event.surface,
            "detail": event.detail,
            "question_index": event.question_index,
            "occurred_at": event.occurred_at or recorded_at,
            "recorded_at": recorded_at,
        },
    )
    if event.kind in {
        "screen_share_denied",
        "screen_share_stopped",
        "screen_share_wrong_surface",
    }:
        logger.warning(f"Proctor [{event.session_id}] {event.kind}: {event.detail or '-'}")
    return ProctorEventResponse(success=True, recorded_at=recorded_at)


# ─── REVIEW ───────────────────────────────────────────────────


@proctor_router.get(
    "/session/{session_id}",
    response_model=SessionRecordingsResponse,
    summary="List a session's recordings and events",
)
async def get_session_recordings(session_id: str):
    """What was captured for one sitting — for a human reviewer, after the fact."""
    directory = _session_dir(session_id, create=False)
    if not directory.exists():
        return SessionRecordingsResponse(
            session_id=session_id, recordings=[], events=[], total_bytes=0
        )

    recordings: List[RecordingInfo] = []
    total = 0
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name == _EVENTS_FILE:
            continue
        stat = path.stat()
        total += stat.st_size
        recordings.append(
            RecordingInfo(
                filename=path.name,
                surface="coding" if "coding" in path.stem else "interview",
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
                modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            )
        )

    events: List[Dict[str, Any]] = []
    events_path = directory / _EVENTS_FILE
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                # A torn last line from a killed process should not hide the rest.
                continue

    return SessionRecordingsResponse(
        session_id=session_id,
        recordings=recordings,
        events=events,
        total_bytes=total,
    )


@proctor_router.get("/config", summary="Screen-recording settings for the client")
async def get_proctor_config():
    """Let the browser read the chunk interval instead of hardcoding its own."""
    return {
        "enabled": settings.PROCTOR_SCREEN_RECORDING_ENABLED,
        "required": settings.PROCTOR_SCREEN_RECORDING_REQUIRED,
        "chunk_interval_ms": settings.PROCTOR_CHUNK_INTERVAL_MS,
        "max_chunk_bytes": settings.PROCTOR_MAX_CHUNK_BYTES,
    }
