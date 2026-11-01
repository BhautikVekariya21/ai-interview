"""
Share Card API Routes (Module 19).

Renders a 1200×630 shareable scorecard PNG (open-graph size) for interview
results, so candidates can post a polished result card on LinkedIn / X /
Slack instead of a bare number. Rendered by `app/services/share_card_service`
from query parameters — no history lookup, no auth, no persistence, so it
works for demo links and for signed-in users alike.

* GET /share/card.png — render the image (query-param driven)
* GET /share/health  — health check
"""

from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from loguru import logger

from app.core.config import settings
from app.services.share_card_service import (
    level_for_score,
    make_embed_url,
    render_share_card,
)

share_router = APIRouter(
    prefix="/share",
    tags=["Module 19: Share Cards"],
)


@share_router.get(
    "/card.png",
    summary="Render a shareable interview scorecard PNG",
    responses={200: {"content": {"image/png": {}}}},
)
def card_png(
    name: str = "Candidate",
    score: int = 0,
    grade: str = "",
    tagline: str = "",
    brand: str = "interviewer.ai",
) -> Response:
    """Return a 1200×630 PNG ready for og:image / social sharing.

    All params are query-string based and sanitized — nothing is persisted,
    so cards work for anonymous links and signed-in sessions alike.
    """
    try:
        png = render_share_card(name, score, grade, tagline, brand)
    except Exception as exc:
        logger.error(f"Share-card render failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Card render failed")
    return Response(content=png, media_type="image/png")


@share_router.get(
    "/card-url",
    summary="Build the absolute URL for a shareable card image",
)
def card_url(
    name: str = "Candidate",
    score: int = 0,
    grade: str = "",
    tagline: str = "",
) -> Dict[str, str]:
    """Return the absolute card.png URL based on this deployment's host.

    Handy for the frontend to fetch meta tags without duplicating URL-building
    logic, and for signed-result pages that need an og:image.
    """
    if score < 0 or score > 100:
        raise HTTPException(status_code=400, detail="score must be 0-100")
    base = settings.FRONTEND_BASE_URL.rstrip("/") or "http://localhost:8000"
    # Cards are served by the backend, not the SPA host — use the API origin.
    try:
        from urllib.parse import urlparse

        parsed = urlparse(settings.FRONTEND_BASE_URL)
        api_base = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else base
    except Exception:  # pragma: no cover - defensive default
        api_base = base
    if not grade:
        grade = level_for_score(score)
    return {"image_url": make_embed_url(api_base, name, int(score), grade, tagline)}


@share_router.get("/health", summary="Health check")
def health() -> Dict[str, str]:
    """Check if the share-card renderer is ready."""
    return {"status": "healthy", "module": "19_share_cards"}
