"""Models pra persistir historico de reviews no banco."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from pedroclaw.knowledge.models import Base


class ReviewLog(Base):
    """Log de cada review executado pelo Pedroclaw."""

    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    mr_iid: Mapped[int] = mapped_column(Integer)
    mr_title: Mapped[str] = mapped_column(String(500), default="")
    source_branch: Mapped[str] = mapped_column(String(300), default="")
    author: Mapped[str] = mapped_column(String(200), default="")
    engine: Mapped[str] = mapped_column(String(50), default="builtin")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | running | completed | failed
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    suggestion_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    squad_details: Mapped[str] = mapped_column(Text, default="{}")  # JSON com detalhes dos agentes
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TriageLog(Base):
    """Log de cada triage executado pelo Pedroclaw."""

    __tablename__ = "triage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    issue_iid: Mapped[int] = mapped_column(Integer)
    issue_title: Mapped[str] = mapped_column(String(500), default="")
    nature: Mapped[str] = mapped_column(String(50), default="")
    priority: Mapped[str] = mapped_column(String(50), default="")
    labels_applied: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    similar_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
