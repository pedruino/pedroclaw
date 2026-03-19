"""Vector store operations — embedding, storage, similarity search via pgvector."""

import json
from typing import Any

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pedroclaw.config import settings
from pedroclaw.knowledge.models import Base, KnowledgeEntry

logger = structlog.get_logger()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create tables and enable pgvector extension."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def embed_text(text_content: str) -> list[float]:
    """Generate embedding for a text chunk using the configured model."""
    import litellm

    response = await litellm.aembedding(
        model=settings.llm_kb_model,
        api_key=settings.llm_kb_api_key,
        input=[text_content],
    )
    return response.data[0]["embedding"]


async def upsert_entry(
    source_type: str,
    source_id: int,
    project_id: int,
    title: str,
    content: str,
    labels: list[str],
    resolution: str = "",
) -> None:
    """Insert or update a knowledge entry with its embedding."""
    embedding = await embed_text(f"{title}\n{content}")

    async with async_session() as session:
        # Check if entry already exists
        stmt = select(KnowledgeEntry).where(
            KnowledgeEntry.source_type == source_type,
            KnowledgeEntry.source_id == source_id,
            KnowledgeEntry.project_id == project_id,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.title = title
            existing.content = content
            existing.labels = json.dumps(labels)
            existing.resolution = resolution
            existing.embedding = embedding
        else:
            entry = KnowledgeEntry(
                source_type=source_type,
                source_id=source_id,
                project_id=project_id,
                title=title,
                content=content,
                labels=json.dumps(labels),
                resolution=resolution,
                embedding=embedding,
            )
            session.add(entry)

        await session.commit()
        logger.info("kb_entry_upserted", source_type=source_type, source_id=source_id)


async def search_similar(query_embedding: list[float], top_k: int = 5, threshold: float = 0.75) -> list[dict[str, Any]]:
    """Find similar entries using cosine distance."""
    async with async_session() as session:
        # pgvector cosine distance: <=> operator (lower = more similar)
        stmt = (
            select(
                KnowledgeEntry,
                KnowledgeEntry.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .where(KnowledgeEntry.embedding.cosine_distance(query_embedding) < (1 - threshold))
            .order_by("distance")
            .limit(top_k)
        )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            {
                "id": row.KnowledgeEntry.id,
                "source_type": row.KnowledgeEntry.source_type,
                "source_id": row.KnowledgeEntry.source_id,
                "title": row.KnowledgeEntry.title,
                "content": row.KnowledgeEntry.content,
                "labels": json.loads(row.KnowledgeEntry.labels) if row.KnowledgeEntry.labels else [],
                "resolution": row.KnowledgeEntry.resolution,
                "score": 1 - row.distance,  # Convert distance to similarity
            }
            for row in rows
        ]
