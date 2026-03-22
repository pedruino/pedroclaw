"""Reviewer agent — delegates code review to the configured pluggable engine.

KB context enrichment is now handled inside each agent (Squad XI uses skills
context, Triage uses KB directly). This module is a thin wrapper.
"""

from typing import Any

import structlog

from pedroclaw.agents.engine import ReviewResult, get_review_engine

logger = structlog.get_logger()


class ReviewerAgent:
    """Delegates MR review to the configured engine (builtin/coderabbit/pr_agent)."""

    def __init__(self) -> None:
        self._engine = get_review_engine()

    async def review_mr(
        self, diff: str, mr_info: dict[str, Any], existing_comments: list[dict[str, Any]] | None = None
    ) -> ReviewResult:
        return await self._engine.review(diff, mr_info, existing_comments=existing_comments)


reviewer_agent = ReviewerAgent()
