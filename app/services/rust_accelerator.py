"""
Optional Rust acceleration bridge for hot text-processing paths.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from loguru import logger

from app.core.config import settings


@lru_cache(maxsize=1)
def get_rust_accelerator() -> Optional[object]:
    """Return the optional Rust extension module if enabled and installed."""
    if not settings.RUST_ACCELERATION_ENABLED:
        return None

    try:
        import ai_interview_accel as rust_module
    except ImportError:
        logger.debug("Rust acceleration module not available; using Python fallback")
        return None

    logger.info("Rust acceleration module loaded")
    return rust_module
