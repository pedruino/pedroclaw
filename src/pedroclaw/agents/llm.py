"""LLM model factory — creates agno.models.litellm.LiteLLM instances from settings."""

from __future__ import annotations

from agno.models.litellm import LiteLLM

from pedroclaw.config import settings


def get_model(model_id: str | None = None, temperature: float = 0.1) -> LiteLLM:
    """Create a LiteLLM model instance configured from application settings.

    Args:
        model_id: Override the model ID (defaults to settings.llm_review_model).
        temperature: LLM temperature (defaults to 0.1 for deterministic output).
    """
    return LiteLLM(
        id=model_id or settings.llm_review_model,
        api_key=settings.llm_review_api_key,
        api_base=settings.llm_review_api_base,
        temperature=temperature,
    )
