"""
Peer Play API Routes (Module 20) — head-to-head friend interview matches.

Two candidates run the same interview format, submit their interview scores
here, and get an Elo-style verdict with rating deltas. Matches are keyed by
a 6-char human-shareable code so players can send the match link like
`/vs?code=K7X2QM` in chat.

* POST /peer/match              — create a match (code + p1 token)
* POST /peer/match/{code}/join  — join with the code (p2 token)
* POST /peer/match/{code}/score — a player submits their interview score
* GET  /peer/match/{code}       — public view of the match + verdict
* GET  /peer/health             — health check
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from loguru import logger
from pydantic import BaseModel, Field

from app.services.mysql_service import MySQLService, get_mysql
from app.services.peer_match_service import (
    MATCH_EXPIRY_HOURS,
    VALID_MODES,
    PeerMatchService,
)

peer_router = APIRouter(
    prefix="/peer",
    tags=["Module 20: Peer Play"],
)


def _service(db: MySQLService) -> PeerMatchService:
    return PeerMatchService(db)


class PeerCreateRequest(BaseModel):
    player_name: str = Field(default="Player 1", max_length=64)
    mode: str = Field(default="mixed", description="behavioral | coding | mixed")


class PeerJoinRequest(BaseModel):
    player_name: str = Field(default="Player 2", max_length=64)


class PeerScoreRequest(BaseModel):
    player_token: str
    score: int = Field(..., ge=0, le=100)


@peer_router.post(
    "/match",
    summary="Create a head-to-head match",
)
def create_match(
    request: PeerCreateRequest,
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """Create a match, return the join code and player-1 secret token."""
    try:
        result = _service(db).create_match(request.player_name, request.mode)
        logger.info(f"Peer match created ({result['mode']}): code={result['code']}")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Peer match create failed: {exc}", exc_info=True)
        raise HTTPException(status_code=503, detail="Peer matches are unavailable right now")


@peer_router.post(
    "/match/{code}/join",
    summary="Join a match as player 2",
)
def join_match(
    code: str = Path(..., min_length=4, max_length=12),
    request: PeerJoinRequest = None,
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """Join a waiting match with its 6-char code."""
    if request is None:
        request = PeerJoinRequest()
    try:
        result = _service(db).join_match(code, request.player_name)
        logger.info(f"Peer match {code.upper()} joined by {result['display_name']}")
        return result
    except LookupError:
        raise HTTPException(status_code=404, detail="Match code not found or expired")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Peer match join failed: {exc}", exc_info=True)
        raise HTTPException(status_code=503, detail="Peer matches are unavailable right now")


@peer_router.post(
    "/match/{code}/score",
    summary="Submit your interview score for the match",
)
def submit_score(
    code: str = Path(..., min_length=4, max_length=12),
    request: PeerScoreRequest = None,
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """Submit a score (0-100) for one match player using their player_token.

    When both players have submitted, the verdict — winner, margin, and
    Elo-style rating deltas — is finalized and published at GET /peer/match/{code}.
    """
    if request is None:
        raise HTTPException(status_code=400, detail="Missing request body")
    try:
        return _service(db).submit_score(code, request.player_token, request.score)
    except PermissionError:
        raise HTTPException(status_code=403, detail="This player token is not in the match")
    except LookupError:
        raise HTTPException(status_code=404, detail="Match code not found or expired")
    except Exception as exc:
        logger.error(f"Peer match submit failed: {exc}", exc_info=True)
        raise HTTPException(status_code=503, detail="Peer matches are unavailable right now")


@peer_router.get(
    "/match/{code}",
    summary="Public view of a match",
)
def get_match(
    code: str = Path(..., min_length=4, max_length=12),
    db: MySQLService = Depends(get_mysql),
) -> Dict[str, Any]:
    """Match status, player names, submitted scores, and the verdict when ready."""
    try:
        return _service(db).get_match(code)
    except LookupError:
        raise HTTPException(status_code=404, detail="Match code not found or expired")
    except Exception as exc:
        logger.error(f"Peer match fetch failed: {exc}", exc_info=True)
        raise HTTPException(status_code=503, detail="Peer matches are unavailable right now")


@peer_router.get("/health", summary="Health check")
def health(db: MySQLService = Depends(get_mysql)) -> Dict[str, Any]:
    """Peer Play health (module + transport availability)."""
    return {"status": "healthy", "module": "20_peer_play", "expire_hours": MATCH_EXPIRY_HOURS, "modes": list(VALID_MODES)}
