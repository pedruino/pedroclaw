"""Dashboard API endpoints."""

from typing import Any

from celery.app.control import Inspect
from fastapi import APIRouter

from pedroclaw.dashboard.store import cleanup_stale_reviews, delete_review_log, get_review_stats, list_review_logs
from pedroclaw.tasks.worker import celery_app

router = APIRouter()


@router.get("/reviews")
async def get_reviews(limit: int = 50) -> list[dict[str, Any]]:
    """Lista reviews recentes."""
    # Limpa reviews travados automaticamente
    await cleanup_stale_reviews(max_age_minutes=15)
    return await list_review_logs(limit)


@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    """Estatisticas gerais de reviews."""
    return await get_review_stats()


@router.get("/queue")
async def get_queue_status() -> dict[str, Any]:
    """Status da fila do Celery."""
    inspect: Inspect = celery_app.control.inspect()

    active = inspect.active() or {}
    reserved = inspect.reserved() or {}
    scheduled = inspect.scheduled() or {}

    active_tasks = []
    for worker_name, tasks in active.items():
        for task in tasks:
            active_tasks.append({
                "id": task.get("id"),
                "name": task.get("name", "").replace("pedroclaw.", ""),
                "worker": worker_name,
                "args": task.get("kwargs", {}),
                "started": task.get("time_start"),
            })

    queued_count = sum(len(tasks) for tasks in reserved.values())
    scheduled_count = sum(len(tasks) for tasks in scheduled.values())

    return {
        "active": active_tasks,
        "queued": queued_count,
        "scheduled": scheduled_count,
    }


@router.post("/cleanup")
async def cleanup() -> dict[str, Any]:
    """Limpa reviews travados manualmente."""
    cleaned = await cleanup_stale_reviews(max_age_minutes=0)
    return {"cleaned": cleaned}


@router.delete("/reviews/{review_id}")
async def delete_review(review_id: int) -> dict[str, Any]:
    """Remove um review log."""
    deleted = await delete_review_log(review_id)
    return {"deleted": deleted}
