"""Dashboard store — CRUD pra review/triage logs."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from pedroclaw.dashboard.models import ReviewLog, TriageLog
from pedroclaw.knowledge.store import async_session


async def create_review_log(
    project_id: int,
    mr_iid: int,
    mr_title: str = "",
    source_branch: str = "",
    author: str = "",
    engine: str = "builtin",
) -> int:
    async with async_session() as session:
        log = ReviewLog(
            project_id=project_id,
            mr_iid=mr_iid,
            mr_title=mr_title,
            source_branch=source_branch,
            author=author,
            engine=engine,
            status="running",
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log.id


async def cleanup_stale_reviews(max_age_minutes: int = 15) -> int:
    """Marca reviews travados em 'running' ha mais de X minutos como 'failed'."""
    from datetime import timedelta
    async with async_session() as session:
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        stmt = select(ReviewLog).where(
            ReviewLog.status == "running",
            ReviewLog.created_at < cutoff,
        )
        result = await session.execute(stmt)
        stale = result.scalars().all()
        for log in stale:
            log.status = "failed"
            log.error_message = "Timeout: review travado"
            log.completed_at = datetime.utcnow()
        await session.commit()
        return len(stale)


async def delete_review_log(log_id: int) -> bool:
    """Remove um review log pelo id."""
    async with async_session() as session:
        stmt = select(ReviewLog).where(ReviewLog.id == log_id)
        result = await session.execute(stmt)
        log = result.scalar_one_or_none()
        if log:
            await session.delete(log)
            await session.commit()
            return True
        return False


async def check_review_exists(project_id: int, mr_iid: int) -> bool:
    """Checa se ja existe um review completed ou running pra esse MR."""
    async with async_session() as session:
        stmt = select(ReviewLog).where(
            ReviewLog.project_id == project_id,
            ReviewLog.mr_iid == mr_iid,
            ReviewLog.status.in_(["completed", "running"]),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None


async def complete_review_log(
    log_id: int,
    total_findings: int = 0,
    critical_count: int = 0,
    warning_count: int = 0,
    suggestion_count: int = 0,
    duration_seconds: float = 0.0,
    squad_details: dict[str, Any] | None = None,
    status: str = "completed",
    error_message: str = "",
) -> None:
    async with async_session() as session:
        stmt = select(ReviewLog).where(ReviewLog.id == log_id)
        result = await session.execute(stmt)
        log = result.scalar_one_or_none()
        if log:
            log.status = status
            log.total_findings = total_findings
            log.critical_count = critical_count
            log.warning_count = warning_count
            log.suggestion_count = suggestion_count
            log.duration_seconds = duration_seconds
            log.squad_details = json.dumps(squad_details or {})
            log.error_message = error_message
            log.completed_at = datetime.utcnow()
            await session.commit()


async def list_review_logs(limit: int = 50) -> list[dict[str, Any]]:
    async with async_session() as session:
        stmt = select(ReviewLog).order_by(desc(ReviewLog.created_at)).limit(limit)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "project_id": r.project_id,
                "mr_iid": r.mr_iid,
                "mr_title": r.mr_title,
                "source_branch": r.source_branch,
                "author": r.author,
                "engine": r.engine,
                "status": r.status,
                "total_findings": r.total_findings,
                "critical_count": r.critical_count,
                "warning_count": r.warning_count,
                "suggestion_count": r.suggestion_count,
                "duration_seconds": r.duration_seconds,
                "squad_details": json.loads(r.squad_details) if r.squad_details else {},
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in rows
        ]


async def get_review_stats() -> dict[str, Any]:
    async with async_session() as session:
        stmt = select(ReviewLog)
        result = await session.execute(stmt)
        rows = result.scalars().all()

        total = len(rows)
        completed = sum(1 for r in rows if r.status == "completed")
        failed = sum(1 for r in rows if r.status == "failed")
        running = sum(1 for r in rows if r.status == "running")
        total_findings = sum(r.total_findings for r in rows)
        total_critical = sum(r.critical_count for r in rows)
        avg_duration = sum(r.duration_seconds for r in rows if r.status == "completed") / max(completed, 1)

        return {
            "total_reviews": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "total_findings": total_findings,
            "total_critical": total_critical,
            "avg_duration_seconds": round(avg_duration, 1),
        }


async def create_triage_log(project_id: int, issue_iid: int, issue_title: str = "") -> int:
    async with async_session() as session:
        log = TriageLog(
            project_id=project_id,
            issue_iid=issue_iid,
            issue_title=issue_title,
            status="running",
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log.id


async def complete_triage_log(
    log_id: int,
    nature: str = "",
    priority: str = "",
    labels_applied: list[str] | None = None,
    similar_count: int = 0,
    duration_seconds: float = 0.0,
    status: str = "completed",
) -> None:
    async with async_session() as session:
        stmt = select(TriageLog).where(TriageLog.id == log_id)
        result = await session.execute(stmt)
        log = result.scalar_one_or_none()
        if log:
            log.status = status
            log.nature = nature
            log.priority = priority
            log.labels_applied = json.dumps(labels_applied or [])
            log.similar_count = similar_count
            log.duration_seconds = duration_seconds
            await session.commit()
