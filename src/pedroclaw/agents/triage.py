"""Triage agent — classifies issues, suggests labels, finds similar past issues.

Uses agno.Agent with structured output (TriageOutput) for reliable parsing.
"""

from typing import Any

import structlog
from agno.agent import Agent

from pedroclaw.agents.llm import get_model
from pedroclaw.agents.models import TriageOutput
from pedroclaw.config import settings
from pedroclaw.knowledge.agno_kb import get_knowledge_base, search_knowledge

logger = structlog.get_logger()


class TriageResult:
    """Public interface — kept for backward compatibility with tasks/worker.py."""

    def __init__(
        self,
        suggested_labels: list[str],
        nature: str,
        priority: str,
        summary: str,
        similar_issues: list[dict[str, Any]],
    ) -> None:
        self.suggested_labels = suggested_labels
        self.nature = nature
        self.priority = priority
        self.summary = summary
        self.similar_issues = similar_issues


def _build_system_prompt() -> str:
    nature_labels = settings.labels.get("nature", [])
    priority_labels = settings.labels.get("priority", [])

    return (
        "You are a triage agent for a legal tech SaaS project (Soft Suite).\n"
        "Your job is to classify incoming issues and suggest labels.\n\n"
        f"Available nature labels: {nature_labels}\n"
        f"Available priority labels: {priority_labels}\n"
    )


def _build_user_prompt(
    title: str, description: str, labels: list[str], kb_context: str
) -> str:
    parts = [
        f"## Issue: {title}",
        f"**Description:**\n{description}",
    ]
    if labels:
        parts.append(f"**Existing labels:** {labels}")
    if kb_context:
        parts.append(f"**Similar past issues (from knowledge base):**\n{kb_context}")
    parts.append("Classify this issue and suggest labels.")
    return "\n\n".join(parts)


def _format_similar_issues(issues: list[dict[str, Any]]) -> str:
    lines = []
    for i, issue in enumerate(issues, 1):
        score = issue.get("score", 0)
        title = issue.get("title", "")
        issue_labels = issue.get("labels", [])
        lines.append(f"{i}. [{score:.2f}] {title} -- labels: {issue_labels}")
    return "\n".join(lines)


def _create_triage_agent() -> Agent:
    """Create the Agno triage agent with structured output."""
    model_id = settings.triage.get("model")
    return Agent(
        name="Triage",
        model=get_model(model_id=model_id),
        instructions=[_build_system_prompt()],
        output_schema=TriageOutput,
        markdown=False,
    )


class TriageAgent:
    """AI-powered issue triage using Agno Agent + knowledge base."""

    def __init__(self) -> None:
        self._config = settings.triage
        self._kb_enabled = self._config.get("kb_lookup", True)
        self._kb_top_k = self._config.get("kb_top_k", 5)
        self._agent = _create_triage_agent()

    async def triage(self, issue: dict[str, Any]) -> TriageResult:
        title = issue.get("title", "")
        description = issue.get("description", "") or ""
        labels = issue.get("labels", [])

        # Step 1: KB lookup for similar issues
        similar: list[dict[str, Any]] = []
        kb_context = ""
        if self._kb_enabled:
            similar = await search_knowledge(
                query=f"{title}\n{description}",
                limit=self._kb_top_k,
            )
            if similar:
                kb_context = _format_similar_issues(similar)

        # Step 2: Agno agent with structured output
        user_prompt = _build_user_prompt(title, description, labels, kb_context)
        response = await self._agent.arun(user_prompt)

        output = response.content
        if isinstance(output, TriageOutput):
            logger.info("triage_complete", issue_title=title)
            return TriageResult(
                suggested_labels=output.suggested_labels,
                nature=output.nature,
                priority=output.priority,
                summary=output.summary,
                similar_issues=similar,
            )

        # Fallback if structured output failed
        logger.warning("triage_structured_output_failed", issue_title=title, content_type=type(output).__name__)
        return TriageResult(
            suggested_labels=[],
            nature="type::chore",
            priority="priority::medium",
            summary="Could not parse triage response",
            similar_issues=similar,
        )


triage_agent = TriageAgent()
