"""Vector store operations — now using Agno Knowledge backend."""

import structlog

from pedroclaw.knowledge.agno_store import embed_text, search_similar, upsert_entry

logger = structlog.get_logger()


async def init_db() -> None:
    """Initialize Agno Knowledge base.
    
    Agno handles table creation automatically when the knowledge base is first used.
    """
    from pedroclaw.knowledge.agno_kb import get_knowledge_base
    
    # Initialize the knowledge base to ensure tables are created
    kb = get_knowledge_base()
    logger.info("agno_knowledge_initialized")
    
    # Note: Agno handles pgvector extension and table creation automatically
