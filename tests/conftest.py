"""Shared fixtures for all tests."""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _setup_observability() -> None:
    """Inicializa Langfuse no início da sessão de testes.

    No-op se LANGFUSE_ENABLED != true ou se as env vars não estiverem configuradas.
    """
    from pedroclaw.observability import get_langfuse, setup_langfuse

    setup_langfuse()

    enabled = get_langfuse()
    print(f"\n[langfuse] enabled={enabled}, otel_host={os.environ.get('LANGFUSE_OTEL_HOST', 'n/a')}")
