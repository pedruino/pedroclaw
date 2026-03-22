"""Langfuse observability — Agno Agent tracing via OpenInference.

Uses AgnoInstrumentor to automatically trace Agent runs, Workflow steps,
and tool calls to Langfuse via OpenTelemetry OTLP.

Replaces the old LiteLLM callback approach with richer Agent-level spans.
"""

from __future__ import annotations

import base64
import os
from typing import Any

import structlog
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

logger = structlog.get_logger()

_enabled: bool = False


def setup_langfuse() -> None:
    """Configure AgnoInstrumentor for Langfuse tracing.

    Called during application startup. No-op if LANGFUSE_ENABLED=false.
    """
    from pedroclaw.config import settings

    global _enabled

    if not settings.langfuse_enabled:
        logger.info("langfuse_disabled")
        return

    try:
        from openinference.instrumentation.agno import AgnoInstrumentor

        # Configure OTLP endpoint and auth for Langfuse
        LANGFUSE_AUTH = base64.b64encode(
            f"{settings.langfuse_public_key}:{settings.langfuse_secret_key}".encode()
        ).decode()
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{settings.langfuse_otel_host}/api/public/otel"
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

        # Setup tracer provider
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))

        # Instrument Agno agents
        AgnoInstrumentor().instrument(tracer_provider=tracer_provider)

        _enabled = True
        logger.info("agno_langfuse_ready", otel_host=settings.langfuse_otel_host)
    except Exception as exc:
        logger.warning("agno_langfuse_setup_failed", error=str(exc))
        _enabled = False


def get_langfuse() -> bool:
    """Returns True if tracing is enabled."""
    return _enabled
