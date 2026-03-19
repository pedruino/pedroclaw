"""Knowledge base retrieval — RAG queries for similar issues/MRs."""

from typing import Any

import structlog

from pedroclaw.config import settings
from pedroclaw.knowledge.store import embed_text, search_similar

logger = structlog.get_logger()


class KBRetrieval:
    """Retrieval interface for the knowledge base."""

    def __init__(self) -> None:
        self._threshold = settings.knowledge_base.get("similarity_threshold", 0.75)

    async def find_similar(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find similar past issues/MRs for a given query text."""
        try:
            embedding = await embed_text(query)
            results = await search_similar(
                query_embedding=embedding,
                top_k=top_k,
                threshold=self._threshold,
            )
            logger.info("kb_search", query_length=len(query), results_count=len(results))
            return results
        except Exception as e:
            logger.warning("kb_search_failed", error=str(e))
            return []


kb_retrieval = KBRetrieval()
