"""Optional OpenTelemetry tracing bootstrap."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

from loguru import logger

from app.core.config import settings

try:  # pragma: no cover - depends on runtime env
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
except Exception:  # pragma: no cover
    trace = None  # type: ignore[assignment]
    OTLPSpanExporter = None  # type: ignore[assignment]
    FastAPIInstrumentor = None  # type: ignore[assignment]
    Resource = None  # type: ignore[assignment]
    TracerProvider = None  # type: ignore[assignment]
    BatchSpanProcessor = None  # type: ignore[assignment]
    TraceIdRatioBased = None  # type: ignore[assignment]


class TracingService:
    def __init__(self) -> None:
        self._initialized = False
        self._init_error: Optional[str] = None

    def get_status(self) -> Dict[str, Any]:
        available = bool(
            settings.OTEL_ENABLED
            and trace is not None
            and FastAPIInstrumentor is not None
            and self._init_error is None
        )
        return {
            "enabled": settings.OTEL_ENABLED,
            "available": available,
            "service_name": settings.OTEL_SERVICE_NAME,
            "exporter_endpoint": settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        }

    def instrument_app(self, app) -> bool:
        if self._initialized:
            return True
        if not settings.OTEL_ENABLED:
            return False
        if (
            trace is None
            or OTLPSpanExporter is None
            or FastAPIInstrumentor is None
            or Resource is None
            or TracerProvider is None
            or BatchSpanProcessor is None
            or TraceIdRatioBased is None
        ):
            self._init_error = "OpenTelemetry packages not installed"
            logger.warning(self._init_error)
            return False
        if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            self._init_error = "OTEL exporter endpoint not configured"
            logger.warning(self._init_error)
            return False

        try:
            resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
            provider = TracerProvider(
                resource=resource,
                sampler=TraceIdRatioBased(settings.OTEL_SAMPLE_RATIO),
            )
            exporter = OTLPSpanExporter(
                endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
                insecure=settings.OTEL_EXPORTER_OTLP_INSECURE,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
            self._initialized = True
            self._init_error = None
            return True
        except Exception as exc:
            self._init_error = str(exc)
            logger.warning(f"Tracing initialization failed: {exc}")
            return False


@lru_cache
def get_tracing_service() -> TracingService:
    return TracingService()
