"""Application configuration via environment variables and YAML."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_yaml_config() -> dict[str, Any]:
    config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml_config()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # GitLab
    gitlab_url: str = "https://gitlab.com"
    gitlab_token: str = ""
    gitlab_webhook_secret: str = ""

    # IA pra Review de Código e Triage de Issues
    llm_review_model: str = "gpt-4o"
    llm_review_api_key: str = ""
    llm_review_api_base: str | None = None

    # Motor de review: builtin | squad-xi | coderabbit | pr_agent
    review_engine: str = "squad-xi"
    coderabbit_api_key: str | None = None

    # Path do projeto frontend (pra carregar skills/rules)
    frontend_path: str = "/workspace/frontend"

    # Banco de Dados
    database_url: str = "postgresql+asyncpg://pedroclaw:pedroclaw@localhost:5432/pedroclaw"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # IA pra Base de Conhecimento (embeddings)
    llm_kb_model: str = "text-embedding-3-small"
    llm_kb_api_key: str = ""

    # Workflow config from YAML
    workflow: dict[str, Any] = Field(default_factory=lambda: _yaml.get("workflow", {}))

    # Labels config from YAML
    labels: dict[str, Any] = Field(default_factory=lambda: _yaml.get("labels", {}))

    # Review config from YAML
    review: dict[str, Any] = Field(default_factory=lambda: _yaml.get("review", {}))

    # Triage config from YAML
    triage: dict[str, Any] = Field(default_factory=lambda: _yaml.get("triage", {}))

    # Knowledge base config from YAML
    knowledge_base: dict[str, Any] = Field(default_factory=lambda: _yaml.get("knowledge_base", {}))


settings = Settings()
