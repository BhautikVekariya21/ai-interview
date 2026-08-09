"""Game Tape — replay share API.

* POST /api/v1/replay/build — normalise transcript + heatmap + proctor events
  into a replay document without persisting anything (studio preview).
* POST /api/v1/replay/save   — persist the same document and mint an
  unguessable share token. Re-saving the same session returns the same link.
* GET  /api/v1/replay/{token} — public fetch of a shared replay.

Saving is auth-optional (mirrors the sandbox's ``optional_user``): the app has
always allowed signed-out interviews, so a guest's replay share should work too
— the user id just attributes the row when present.
"""

from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.auth_routes import get_current_user
from app.repositories.replay_repository import ReplayRepository
from app.services.mysql_service import MySQLService, get_mysql
from app.services.replay_service import build_replay_document

replay_router = APIRouter(
    prefix="/api/v1/replay",
    tags=["Game Tape"],
)

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class ReplayBuildRequest(BaseModel):
    """The raw evidence a replay document is merged from."""

    meta: Dict[str, Any] = Field(default_factory=dict)
    qa_pairs: List[Dict[str, Any]] = Field(default_factory=list)
    heatmap: Optional[Dict[str, Any]] = None
    proctor_events: Optional[List[Dict[str, Any]]] = None


class ReplaySaveRequest(ReplayBuildRequest):
    """Build request plus the sitting id used to dedupe share links."""

    session_id: Optional[str] = Field(default=None, max_length=128)


def optional_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: MySQLService = Depends(get_mysql),
) -> Optional[Any]:
    """The signed-in user's id, or None — attribution, not a gate."""
    try:
        current = get_current_user(request=request, authorization=authorization, db=db)
    except Exception:
        return None
    user = (current or {}).get("user")
    return getattr(user, "id", None)


def _replay_repository(db: MySQLService) -> ReplayRepository:
    return ReplayRepository(db)


@replay_router.post(
    "/build",
    summary="Normalise interview evidence into a replay document",
)
def build_replay(payload: ReplayBuildRequest) -> Dict[str, Any]:
    """Return the typed timeline the Replay Studio renders. Stateless and cheap —
    the studio previews with this before deciding to share."""
    return build_replay_document(
        meta=payload.meta,
        qa_pairs=payload.qa_pairs,
        heatmap=payload.heatmap,
        proctor_events=payload.proctor_events,
    )


@replay_router.post(
    "/save",
    summary="Persist a replay and mint a share token",
)
def save_replay(
    payload: ReplaySaveRequest,
    user_id: Optional[Any] = Depends(optional_user),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, str]:
    """Persist the replay document and return its share token. Re-saving the
    same session reuses the existing token so sharing twice gives one link."""
    session_id = (payload.session_id or "").strip() or None
    repo = _replay_repository(db)

    token = repo.find_token_by_session(session_id) if session_id else None
    if not token:
        token = secrets.token_urlsafe(16)
        if not _SAFE_TOKEN.match(token):
            raise HTTPException(500, detail="Could not generate a share token")

    document = build_replay_document(
        meta=payload.meta,
        qa_pairs=payload.qa_pairs,
        heatmap=payload.heatmap,
        proctor_events=payload.proctor_events,
    )
    candidate_name = str(document["meta"].get("candidate_name") or "")[:255]

    repo.save(
        token=token,
        session_id=session_id,
        user_id=user_id,
        candidate_name=candidate_name,
        payload_json=json.dumps(document, ensure_ascii=False, default=str),
        created_at=datetime.now(timezone.utc),
    )
    return {"token": token}


@replay_router.get(
    "/{token}",
    summary="Fetch a shared replay by token",
)
def get_replay(token: str, db: MySQLService = Depends(get_mysql)) -> Dict[str, Any]:
    """The persisted replay document for a share token (public)."""
    if not _SAFE_TOKEN.match(token):
        raise HTTPException(404, detail="Replay not found")
    repo = _replay_repository(db)
    raw = repo.find_by_token(token)
    if not raw:
        raise HTTPException(404, detail="Replay not found or expired")
    try:
        document = json.loads(raw)
    except (TypeError, ValueError):
        raise HTTPException(500, detail="Stored replay is corrupt") from None
    return {"replay": document}
