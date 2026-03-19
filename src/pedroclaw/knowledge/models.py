"""Database models for knowledge base — SQLAlchemy + pgvector."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class KnowledgeEntry(Base):
    """A chunk of knowledge from a past issue, MR, or comment."""

    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(20))  # "issue" | "mr" | "comment"
    source_id: Mapped[int] = mapped_column(Integer)  # GitLab IID
    project_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    labels: Mapped[str] = mapped_column(Text, default="")  # JSON array as string
    resolution: Mapped[str] = mapped_column(Text, default="")
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))  # text-embedding-3-small dim
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
