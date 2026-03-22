"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pedroclaw.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Initialize database tables."""
    from pedroclaw.dashboard.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
