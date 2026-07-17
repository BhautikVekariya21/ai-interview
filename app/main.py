"""
Main FastAPI Application — AI Interview System.
Complete version with all modules.
"""

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.api.auth_routes import auth_router
from app.api.routes import router as main_router
from app.api.user_data_routes import user_data_router
from app.core.config import settings
from app.services.mysql_service import get_mysql_health
from app.services.tracing_service import get_tracing_service


# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT DETECTION
# ═══════════════════════════════════════════════════════════════

IS_HUGGINGFACE = bool(os.getenv("SPACE_ID") and os.getenv("SPACE_ID").strip())
ENVIRONMENT = "huggingface-spaces" if IS_HUGGINGFACE else "local"
DEFAULT_PORT = 7860 if IS_HUGGINGFACE else 8000

_INSECURE_DEFAULT_JWT_SECRET = "super-secret-jwt-key!123"
if not settings.DEBUG and settings.JWT_SECRET_KEY == _INSECURE_DEFAULT_JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET_KEY is still set to the insecure default. "
        "Set a unique, random JWT_SECRET_KEY via environment variable before running with DEBUG=false."
    )

STATIC_DIR = Path("app/static")

from app.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS


# ═══════════════════════════════════════════════════════════════
# OPTIONAL MODULE IMPORTS
# ═══════════════════════════════════════════════════════════════

HAS_TTS = False
HAS_ASR = False
HAS_EVAL = False

tts_router = None
asr_router = None
evaluation_router = None
history_router = None

# ASR Details
BROWSER_ASR_AVAILABLE = True
SERVER_ASR_AVAILABLE = False
SERVER_ASR_PROVIDERS = []
SERVER_ASR_ACTIVE = None

# TTS
try:
    from app.api.tts_routes import tts_router

    HAS_TTS = True
    logger.debug("TTS module loaded")
except ImportError as e:
    logger.debug(f"TTS module not available: {e}")
except Exception as e:
    logger.warning(f"TTS module error: {e}")

# ASR
try:
    from app.api.asr_routes import asr_router

    HAS_ASR = True
    logger.debug("ASR module loaded")

    try:
        from app.services.asr_service import get_asr

        _asr_service = get_asr()
        if _asr_service:
            SERVER_ASR_PROVIDERS = [p for p in _asr_service.available_providers if p != "browser"]
            SERVER_ASR_AVAILABLE = len(SERVER_ASR_PROVIDERS) > 0
            SERVER_ASR_ACTIVE = SERVER_ASR_PROVIDERS[0] if SERVER_ASR_PROVIDERS else None
    except Exception as e:
        logger.debug(f"Server-side ASR check: {e}")

except ImportError as e:
    logger.debug(f"ASR module not available: {e}")
except Exception as e:
    logger.warning(f"ASR module error: {e}")

# Evaluation
try:
    from app.api.evaluation_routes import evaluation_router

    HAS_EVAL = True
    logger.debug("Evaluation module loaded")
except ImportError as e:
    logger.debug(f"Evaluation module not available: {e}")
except Exception as e:
    logger.warning(f"Evaluation module error: {e}")

# History
try:
    from app.api.history_routes import history_router

    HAS_HISTORY = True
    logger.debug("History module loaded")
except Exception as e:
    logger.warning(f"History module error: {e}")
    HAS_HISTORY = False

# Confidence Pulse
HAS_CONFIDENCE = False
try:
    from app.api.confidence_routes import confidence_router

    HAS_CONFIDENCE = True
    logger.debug("Confidence Pulse module loaded")
except Exception as e:
    logger.warning(f"Confidence Pulse module error: {e}")
    confidence_router = None

# Contact Form
HAS_CONTACT = False
try:
    from app.api.contact_routes import contact_router

    HAS_CONTACT = True
    logger.debug("Contact module loaded")
except Exception as e:
    logger.warning(f"Contact module error: {e}")
    contact_router = None

# Community Blog
HAS_BLOG = False
try:
    from app.api.blog_routes import blog_router

    HAS_BLOG = True
    logger.debug("Blog module loaded")
except Exception as e:
    logger.warning(f"Blog module error: {e}")
    blog_router = None

# App Reviews (feedback forum)
HAS_REVIEWS = False
try:
    from app.api.review_routes import review_router

    HAS_REVIEWS = True
    logger.debug("Reviews module loaded")
except Exception as e:
    logger.warning(f"Reviews module error: {e}")
    review_router = None

# ═══════════════════════════════════════════════════════════════
# LIFESPAN
# ═══════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""

    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"  Environment: {ENVIRONMENT}")
    logger.info("=" * 60)

    # Create directories
    for directory in [settings.UPLOAD_DIR, settings.ASR_RECORDINGS_DIR, "app/static"]:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Log modules
    logger.info("  📦 Modules:")
    modules = [
        ("Module 1: Resume Parser", True),
        ("Module 2: Question Generator", True),
        ("Module 3: Text-to-Speech", HAS_TTS),
        ("Module 4: Speech Recognition", HAS_ASR),
        ("Module 5: Answer Evaluation", HAS_EVAL),
        ("Module 6: DB History Tracking", HAS_HISTORY),
        ("Module 10: OpenTelemetry Tracing", True),
        ("Module 12: AI Confidence Pulse", HAS_CONFIDENCE),
    ]
    for name, available in modules:
        status = "✓" if available else "✗"
        logger.info(f"    {status} {name}")

    logger.info("=" * 60)
    logger.info("  🚀 Application ready!")

    tracing_service = get_tracing_service()
    tracing_service.instrument_app(app)
    tracing_status = tracing_service.get_status()
    logger.info(
        "  Tracing: "
        f"{'otel' if tracing_status['enabled'] else 'disabled'} "
        f"(endpoint={tracing_status['exporter_endpoint']})"
    )
    port = int(os.getenv("PORT", DEFAULT_PORT))
    logger.info(f"  📍 API: http://localhost:{port}/docs")
    logger.info(f"  📍 Streamlit: streamlit run streamlit_app.py")
    logger.info("=" * 60)

    yield

    logger.info("Shutting down...")


# ═══════════════════════════════════════════════════════════════
# APP CONFIGURATION
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Interview System with voice interface",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Hardening
allowed_origins = list(settings.ALLOWED_ORIGINS)
allow_credentials = True
if IS_HUGGINGFACE:
    # HF Spaces serves the frontend from a dynamic, per-Space origin. A
    # wildcard origin cannot be combined with credentialed requests, so
    # credentials are disabled for this deployment path instead of
    # widening the origin whitelist with "*".
    allowed_origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Intercept all unhandled exceptions to prevent stack trace leaks and log securely."""
    error_type = type(exc).__name__
    logger.error(f"Unhandled Server Error [{error_type}]: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An internal server error occurred",
            "type": error_type,
        },
    )


@app.middleware("http")
async def add_headers(request, call_next):
    """Add processing time header."""
    start = time.time()
    method = request.method
    path = request.url.path
    try:
        response = await call_next(request)
    except Exception:
        duration = time.time() - start
        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status_code="500").inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
        raise

    duration = time.time() - start
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status_code=str(response.status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
    response.headers["X-Processing-Time"] = f"{duration:.4f}s"
    return response


# ═══════════════════════════════════════════════════════════════
# ROUTERS
# ═══════════════════════════════════════════════════════════════

app.include_router(main_router)
app.include_router(auth_router)
app.include_router(user_data_router)

if HAS_TTS and tts_router:
    app.include_router(tts_router)
    logger.debug("✓ TTS router registered")

if HAS_ASR and asr_router:
    app.include_router(asr_router)
    logger.debug("✓ ASR router registered")

if HAS_EVAL and evaluation_router:
    app.include_router(evaluation_router)
    logger.debug("✓ Evaluation router registered")

if HAS_HISTORY and history_router:
    app.include_router(history_router)
    logger.debug("✓ Database History router registered")

if HAS_CONFIDENCE and confidence_router:
    app.include_router(confidence_router)
    logger.debug("✓ Confidence Pulse router registered")

if HAS_CONTACT and contact_router:
    app.include_router(contact_router)
    logger.debug("✓ Contact router registered")

if HAS_BLOG and blog_router:
    app.include_router(blog_router)
    logger.debug("✓ Blog router registered")

if HAS_REVIEWS and review_router:
    app.include_router(review_router)
    logger.debug("✓ Reviews router registered")


# ═══════════════════════════════════════════════════════════════
# STATIC FILES
# ═══════════════════════════════════════════════════════════════

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ═══════════════════════════════════════════════════════════════
# HEALTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "streamlit": "Run: streamlit run streamlit_app.py",
    }


@app.get("/metrics", tags=["Observability"], include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", DEFAULT_PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=not IS_HUGGINGFACE)
