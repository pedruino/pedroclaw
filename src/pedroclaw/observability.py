"""Langfuse observability — tracking de LLM calls via OpenTelemetry.

Usa o callback ``langfuse_otel`` do LiteLLM que envia spans OTEL
diretamente para o endpoint ``{LANGFUSE_OTEL_HOST}/api/public/otel``.

Todas as chamadas ``litellm.acompletion()`` são rastreadas automaticamente.
Para agrupar chamadas numa mesma trace, passe ``metadata`` com ``trace_id``.

Ref: https://langfuse.com/integrations/frameworks/litellm-sdk
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import structlog

logger = structlog.get_logger()

_enabled: bool = False


def setup_langfuse() -> None:
    """Registra o callback ``langfuse_otel`` no LiteLLM.

    Chamado no startup da aplicação. No-op se LANGFUSE_ENABLED=false.
    """
    from pedroclaw.config import settings

    global _enabled

    if not settings.langfuse_enabled:
        logger.info("langfuse_disabled")
        return

    try:
        import litellm

        # Env vars que o callback langfuse_otel do LiteLLM lê
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
        os.environ.setdefault("LANGFUSE_OTEL_HOST", settings.langfuse_otel_host)

        # Registra callback OTEL
        litellm.callbacks = list(litellm.callbacks or [])
        if "langfuse_otel" not in litellm.callbacks:
            litellm.callbacks.append("langfuse_otel")

        _enabled = True
        logger.info("langfuse_ready", otel_host=settings.langfuse_otel_host)
    except Exception as exc:
        logger.warning("langfuse_setup_failed", error=str(exc))
        _enabled = False


def get_langfuse() -> bool:
    """Retorna True se o tracking está habilitado."""
    return _enabled


def create_trace(name: str, **kwargs: Any) -> str | None:
    """Gera um trace_id único para agrupar chamadas LLM numa mesma trace.

    Retorna o trace_id (str) ou None se o tracking está desabilitado.
    O trace_id deve ser passado via ``litellm_metadata()`` em cada chamada.
    """
    if not _enabled:
        return None
    trace_id = str(uuid.uuid4())
    logger.debug("langfuse_trace_created", name=name, trace_id=trace_id)
    return trace_id


def litellm_metadata(
    trace_id: str | None,
    parent_observation_id: str | None,
    generation_name: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Monta o dict de metadata para passar ao litellm.acompletion().

    O callback langfuse_otel lê essas chaves para criar a generation
    aninhada sob a trace correta.
    """
    if trace_id is None:
        return {}
    meta: dict[str, Any] = {
        "trace_id": trace_id,
        "generation_name": generation_name,
    }
    if parent_observation_id:
        meta["parent_observation_id"] = parent_observation_id
    if extra:
        meta.update(extra)
    return meta
