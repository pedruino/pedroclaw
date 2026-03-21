"""Agno Knowledge Base — pgvector + Agno ``Knowledge`` search."""

from __future__ import annotations

from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType

from pedroclaw.config import settings


def create_knowledge_base(table_name: str = "knowledge_items") -> Knowledge:
    """Create an Agno Knowledge instance backed by PgVector.
    
    Uses the existing database connection and LiteLLM for embeddings.
    """
    # Use LiteLLM model for embeddings via OpenAI embedder
    embedder = OpenAIEmbedder(
        id=settings.llm_kb_model,
        api_key=settings.llm_kb_api_key,
    )
    
    vector_db = PgVector(
        table_name=table_name,
        db_url=settings.database_url.replace("+asyncpg", ""),  # Agno uses sync psycopg
        search_type=SearchType.hybrid,  # semantic + keyword search
        embedder=embedder,
    )
    
    return Knowledge(vector_db=vector_db)


# Singleton instances
_kb_instance: Knowledge | None = None


def get_knowledge_base() -> Knowledge:
    """Get or create the singleton knowledge base instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = create_knowledge_base()
    return _kb_instance


def create_knowledge_base_if_needed() -> Knowledge:
    """Create knowledge base only when actually needed (lazy initialization)."""
    return get_knowledge_base()


async def search_knowledge(query: str, limit: int = 5) -> list[dict[str, any]]:
    """Search the knowledge base for similar items.
    
    Returns a list of dicts (id, title, content, score, meta_data) for triage and tooling.
    """
    kb = get_knowledge_base()
    
    # Use Agno's search method
    results = await kb.asearch(query, limit=limit)
    
    # Convert to old interface format for backward compatibility
    formatted_results = []
    for result in results:
        formatted_results.append({
            "id": result.get("id", ""),
            "title": result.get("name", ""),
            "content": result.get("content", ""),
            "score": result.get("reranking_score", 0.0),
            "meta_data": result.get("meta_data", {}),
        })
    
    return formatted_results
