"""Triage agent — classifies issues, suggests labels, finds similar past issues."""

from typing import Any

import structlog

from pedroclaw.config import settings
from pedroclaw.knowledge.retrieval import kb_retrieval
from pedroclaw.observability import create_trace, litellm_metadata

logger = structlog.get_logger()


class TriageResult:
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


class TriageAgent:
    """AI-powered issue triage using LLM + knowledge base."""

    def __init__(self) -> None:
        self._config = settings.triage
        self._model = self._config.get("model", settings.llm_review_model)
        self._kb_enabled = self._config.get("kb_lookup", True)
        self._kb_top_k = self._config.get("kb_top_k", 5)

    async def triage(self, issue: dict[str, Any]) -> TriageResult:
        title = issue.get("title", "")
        description = issue.get("description", "") or ""
        labels = issue.get("labels", [])
        issue_id = issue.get("iid") or issue.get("id")

        trace_id = create_trace("triage")

        # Step 1: KB lookup for similar issues
        similar: list[dict[str, Any]] = []
        kb_context = ""
        if self._kb_enabled:
            similar = await kb_retrieval.find_similar(
                query=f"{title}\n{description}",
                top_k=self._kb_top_k,
            )
            if similar:
                kb_context = self._format_similar_issues(similar)

        # Step 2: LLM classification
        import litellm

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(title, description, labels, kb_context)

        response = await litellm.acompletion(
            model=self._model,
            api_key=settings.llm_review_api_key,
            api_base=settings.llm_review_api_base,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            metadata=litellm_metadata(trace_id, None, "triage_classify"),
        )

        content = response.choices[0].message.content or ""
        logger.info(
            "triage_complete",
            issue_title=title,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )

        result = self._parse_response(content, similar)
        return result

    def _build_system_prompt(self) -> str:
        nature_labels = settings.labels.get("nature", [])
        priority_labels = settings.labels.get("priority", [])

        return (
            "You are a triage agent for a legal tech SaaS project (Soft Suite).\n"
            "Your job is to classify incoming issues and suggest labels.\n\n"
            "Respond ONLY in this exact JSON format:\n"
            "```json\n"
            '{"nature": "<label>", "priority": "<label>", "summary": "<1-2 sentence summary>", '
            '"suggested_labels": ["<label1>", "<label2>"]}\n'
            "```\n\n"
            f"Available nature labels: {nature_labels}\n"
            f"Available priority labels: {priority_labels}\n"
        )

    def _build_user_prompt(
        self, title: str, description: str, labels: list[str], kb_context: str
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

    def _format_similar_issues(self, issues: list[dict[str, Any]]) -> str:
        lines = []
        for i, issue in enumerate(issues, 1):
            score = issue.get("score", 0)
            title = issue.get("title", "")
            labels = issue.get("labels", [])
            lines.append(f"{i}. [{score:.2f}] {title} — labels: {labels}")
        return "\n".join(lines)

    def _parse_response(self, content: str, similar: list[dict[str, Any]]) -> TriageResult:
        import json

        # Extract JSON from response (may be wrapped in ```json ... ```)
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("triage_parse_failed", content=content[:200])
            return TriageResult(
                suggested_labels=[],
                nature="type::chore",
                priority="priority::medium",
                summary="Could not parse triage response",
                similar_issues=similar,
            )

        return TriageResult(
            suggested_labels=data.get("suggested_labels", []),
            nature=data.get("nature", "type::chore"),
            priority=data.get("priority", "priority::medium"),
            summary=data.get("summary", ""),
            similar_issues=similar,
        )


triage_agent = TriageAgent()
