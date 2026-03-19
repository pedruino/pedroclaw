"""Reviewer agent — orchestrates code review using the pluggable engine + KB context."""

from typing import Any

import structlog

from pedroclaw.agents.engine import ReviewResult, get_review_engine
from pedroclaw.config import settings
from pedroclaw.knowledge.retrieval import kb_retrieval

logger = structlog.get_logger()


class ReviewerAgent:
    """Orchestrates MR review: fetches diff, enriches with KB context, delegates to engine."""

    def __init__(self) -> None:
        self._engine = get_review_engine()
        self._kb_enabled = settings.triage.get("kb_lookup", True)

    async def review_mr(
        self, diff: str, mr_info: dict[str, Any], existing_comments: list[dict[str, Any]] | None = None
    ) -> ReviewResult:
        # Enrich with knowledge base context
        context = ""
        if self._kb_enabled:
            title = mr_info.get("title", "")
            description = mr_info.get("description", "") or ""
            query = f"{title}\n{description}"

            similar = await kb_retrieval.find_similar(query=query, top_k=3)
            if similar:
                context = "\n".join(
                    f"- [{s.get('score', 0):.2f}] {s.get('title', '')}: {s.get('resolution', '')}"
                    for s in similar
                )

        return await self._engine.review(diff, mr_info, context, existing_comments)


reviewer_agent = ReviewerAgent()
