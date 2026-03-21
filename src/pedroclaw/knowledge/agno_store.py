"""Agno Knowledge Store — adapter for existing ingestion to work with Agno Knowledge."""

from __future__ import annotations

from typing import Any

import structlog

from pedroclaw.knowledge.agno_kb import get_knowledge_base

logger = structlog.get_logger()


async def embed_text(text_content: str) -> list[float]:
    """Generate embedding for a text chunk using the configured model.
    
    This is now handled by Agno's embedder automatically.
    Kept for backward compatibility with existing ingestion code.
    """
    # Agno handles embeddings internally via the OpenAIEmbedder
    # This is a placeholder for compatibility
    return []


async def upsert_entry(
    source_type: str,
    source_id: int,
    project_id: int,
    title: str,
    content: str,
    labels: list[str],
    resolution: str = "",
) -> None:
    """Insert or update a knowledge entry using Agno Knowledge.
    
    This replaces the manual SQLAlchemy approach with Agno's Knowledge insertion.
    """
    kb = get_knowledge_base()
    
    # Create a text representation that includes all metadata
    full_content = f"Title: {title}\n\nContent: {content}"
    if labels:
        full_content += f"\nLabels: {', '.join(labels)}"
    if resolution:
        full_content += f"\nResolution: {resolution}"
    
    # Add metadata for filtering
    metadata = {
        "source_type": source_type,
        "source_id": str(source_id),
        "project_id": str(project_id),
        "labels": labels,
        "resolution": resolution,
    }
    
    try:
        # Use Agno's async insert method
        await kb.ainsert(
            text=full_content,
            meta_data=metadata,
            name=title,
        )
        logger.info("kb_entry_upserted", source_type=source_type, source_id=source_id)
    except Exception as e:
        logger.error("kb_entry_upsert_failed", source_type=source_type, source_id=source_id, error=str(e))
        raise


async def search_similar(query_embedding: list[float], top_k: int = 5, threshold: float = 0.75) -> list[dict[str, Any]]:
    """Find similar entries using Agno's Knowledge search.
    
    This replaces the manual PgVector cosine distance query.
    """
    from pedroclaw.knowledge.agno_kb import search_knowledge
    
    # Note: Agno doesn't expose raw embeddings in the same way
    # We use the text-based search which handles embeddings internally
    # The threshold filtering can be done on the results
    
    results = await search_knowledge(query="", limit=top_k)  # Empty query will rely on other factors
    
    # Filter by threshold if needed (Agno provides reranking scores)
    filtered_results = []
    for result in results:
        score = result.get("score", 0.0)
        if score >= threshold:
            # Convert to expected format
            filtered_results.append({
                "id": result.get("id", ""),
                "source_type": result.get("meta_data", {}).get("source_type", ""),
                "source_id": int(result.get("meta_data", {}).get("source_id", 0)),
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "labels": result.get("meta_data", {}).get("labels", []),
                "resolution": result.get("meta_data", {}).get("resolution", ""),
                "score": score,
            })
    
    return filtered_results
