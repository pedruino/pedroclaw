"""Celery worker tasks — background processing for reviews, triage, KB sync."""

import asyncio
from typing import Any

import structlog
from celery import Celery

from pedroclaw.config import settings

logger = structlog.get_logger()

celery_app = Celery(
    "pedroclaw",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    task_soft_time_limit=300,  # 5 min soft limit
    task_time_limit=360,  # 6 min hard limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time (LLM calls are slow)
)


_loop: asyncio.AbstractEventLoop | None = None


def _run_async(coro: Any) -> Any:
    """Run async function in sync Celery task. Reuses event loop to avoid SQLAlchemy conflicts."""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
    return _loop.run_until_complete(coro)


@celery_app.task(name="pedroclaw.review_mr", bind=True, max_retries=2)
def task_review_mr(self: Any, project_id: int, mr_iid: int) -> dict[str, Any]:
    """Review a merge request using the configured engine."""
    from pedroclaw.agents.reviewer import reviewer_agent
    from pedroclaw.gitlab.client import gitlab_client
    from pedroclaw.workflow.states import workflow_engine

    try:
        import time as _time

        import redis as _redis

        from pedroclaw.dashboard.store import check_review_exists, complete_review_log, create_review_log

        logger.info("task_review_mr_start", project_id=project_id, mr_iid=mr_iid)

        # Lock por project+mr pra evitar reviews duplicados
        r = _redis.from_url(settings.redis_url)
        lock_key = f"pedroclaw:review_lock:{project_id}:{mr_iid}"
        lock_acquired = r.set(lock_key, "1", nx=True, ex=600)  # expira em 10min
        if not lock_acquired:
            logger.info("review_skipped_locked", mr_iid=mr_iid, project_id=project_id)
            return {"status": "skipped", "reason": "review already in progress", "mr_iid": mr_iid}

        start_time = _time.time()

        # Fetch MR info and diff
        mr_info = gitlab_client.get_mr(project_id, mr_iid)
        diff = gitlab_client.get_mr_diff(project_id, mr_iid)

        # Only review if MR has label workflow::in-review
        mr_labels = mr_info.get("labels", [])
        if "workflow::in-review" not in mr_labels:
            r.delete(lock_key)
            logger.info("review_skipped_no_label", mr_iid=mr_iid, labels=mr_labels)
            return {"status": "skipped", "reason": "missing workflow::in-review label", "mr_iid": mr_iid}

        # Checa se ja existe review completed pra esse MR (evita re-review no mesmo push)
        already_reviewed = _run_async(check_review_exists(project_id, mr_iid))
        if already_reviewed:
            r.delete(lock_key)
            logger.info("review_skipped_already_done", mr_iid=mr_iid)
            return {"status": "skipped", "reason": "already reviewed", "mr_iid": mr_iid}

        # Registra no dashboard
        log_id = _run_async(create_review_log(
            project_id=project_id,
            mr_iid=mr_iid,
            mr_title=mr_info.get("title", ""),
            source_branch=mr_info.get("source_branch", ""),
            author=mr_info.get("author", {}).get("username", ""),
            engine=settings.review_engine,
        ))

        # Busca comentarios existentes do Pedroclaw
        existing_comments = gitlab_client.get_mr_pedroclaw_comments(project_id, mr_iid)

        # Run review (passa comentarios existentes pra evitar duplicatas)
        result = _run_async(reviewer_agent.review_mr(diff, mr_info, existing_comments))

        # Post inline comments on specific diff lines
        if result.inline_comments:
            mr_details = gitlab_client.get_mr(project_id, mr_iid)
            base_sha = mr_details.get("diff_refs", {}).get("base_sha", "")
            head_sha = mr_details.get("diff_refs", {}).get("head_sha", "")
            start_sha = mr_details.get("diff_refs", {}).get("start_sha", "")

            # Get valid diff lines to avoid posting on non-visible lines
            valid_lines = gitlab_client.get_mr_valid_diff_lines(project_id, mr_iid)

            # Busca comentarios existentes do Pedroclaw pra evitar duplicatas
            existing = gitlab_client.get_mr_pedroclaw_comments(project_id, mr_iid)
            existing_keys = {f"{c['file']}:{c['line']}" for c in existing if c["file"]}

            posted = 0
            skipped = 0
            duplicated = 0
            for comment in result.inline_comments:
                # Checa se ja existe comentario nesse arquivo+linha
                comment_key = f"{comment.file_path}:{comment.line}"
                if comment_key in existing_keys:
                    duplicated += 1
                    continue
                severity_icon = {"critical": "🔴", "warning": "🟡", "suggestion": "💡"}.get(
                    comment.severity, "💬"
                )
                body = f"🦀{severity_icon}: {comment.body}"

                # Check if the line is in the diff, or find nearest valid line
                file_valid_lines = valid_lines.get(comment.file_path, set())
                target_line = gitlab_client.find_nearest_valid_line(comment.line, file_valid_lines)

                if target_line:
                    try:
                        gitlab_client.add_mr_inline_comment(
                            project_id=project_id,
                            mr_iid=mr_iid,
                            body=body,
                            file_path=comment.file_path,
                            new_line=target_line,
                            base_sha=base_sha,
                            head_sha=head_sha,
                            start_sha=start_sha,
                        )
                        posted += 1
                    except Exception as e:
                        logger.warning("inline_comment_failed", file=comment.file_path, line=target_line, error=str(e))
                        gitlab_client.add_mr_comment(
                            project_id, mr_iid,
                            f"🦀{severity_icon} **{comment.file_path}:{comment.line}** {comment.body}",
                        )
                        posted += 1
                else:
                    gitlab_client.add_mr_comment(
                        project_id, mr_iid,
                        f"🦀{severity_icon} **{comment.file_path}:{comment.line}** {comment.body}",
                    )
                    skipped += 1

            logger.info("review_comments_posted", posted=posted, skipped=skipped, duplicated=duplicated, total=len(result.inline_comments))
        else:
            gitlab_client.add_mr_comment(project_id, mr_iid, "🦀 **Pedroclaw Review** Nenhuma violacao encontrada. ✅")

        # Update workflow state on linked issues
        linked_issues = gitlab_client.get_mr_linked_issues(project_id, mr_iid)
        new_state = workflow_engine.infer_state_from_mr(mr_info)
        if new_state:
            for issue_iid in linked_issues:
                try:
                    gitlab_client.set_issue_state_label(project_id, issue_iid, new_state)
                except Exception as e:
                    logger.warning("state_update_failed", issue_iid=issue_iid, error=str(e))

        # Salva no dashboard
        duration = _time.time() - start_time
        findings = result.inline_comments or []
        _run_async(complete_review_log(
            log_id=log_id,
            total_findings=len(findings),
            critical_count=sum(1 for c in findings if c.severity == "critical"),
            warning_count=sum(1 for c in findings if c.severity == "warning"),
            suggestion_count=sum(1 for c in findings if c.severity == "suggestion"),
            duration_seconds=duration,
        ))

        # Libera lock
        r.delete(lock_key)

        logger.info("task_review_mr_done", project_id=project_id, mr_iid=mr_iid, engine=result.engine, duration=f"{duration:.1f}s")
        return {"status": "reviewed", "engine": result.engine, "mr_iid": mr_iid}

    except Exception as exc:
        logger.error("task_review_mr_failed", error=str(exc), project_id=project_id, mr_iid=mr_iid)
        # Libera lock e registra falha
        try:
            r = _redis.from_url(settings.redis_url)
            r.delete(f"pedroclaw:review_lock:{project_id}:{mr_iid}")
        except Exception:
            pass
        if 'log_id' in locals():
            _run_async(complete_review_log(log_id=log_id, status="failed", error_message=str(exc)))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="pedroclaw.triage_issue", bind=True, max_retries=2)
def task_triage_issue(self: Any, project_id: int, issue_iid: int) -> dict[str, Any]:
    """Triage an issue: classify, label, find similar past issues."""
    from pedroclaw.agents.triage import triage_agent
    from pedroclaw.gitlab.client import gitlab_client

    try:
        logger.info("task_triage_start", project_id=project_id, issue_iid=issue_iid)

        # Fetch issue
        issue = gitlab_client.get_issue(project_id, issue_iid)

        # Run triage
        result = _run_async(triage_agent.triage(issue))

        # Apply labels
        if settings.triage.get("auto_label", True) and result.suggested_labels:
            all_labels = result.suggested_labels + [result.nature, result.priority]
            all_labels = [l for l in all_labels if l]  # filter empty
            gitlab_client.ensure_labels_exist(project_id, all_labels)
            gitlab_client.add_issue_labels(project_id, issue_iid, all_labels)

        # Post triage summary as comment
        comment_parts = [f"🦀 **Pedroclaw Triagem**\n\n**Classificacao:** {result.nature} | {result.priority}"]
        if result.summary:
            comment_parts.append(f"**Resumo:** {result.summary}")
        if result.similar_issues:
            comment_parts.append("**Issues similares:**")
            for s in result.similar_issues[:3]:
                comment_parts.append(f"- [{s.get('score', 0):.0%}] #{s.get('source_id')} {s.get('title', '')}")

        gitlab_client.add_issue_comment(project_id, issue_iid, "\n\n".join(comment_parts))

        logger.info("task_triage_done", project_id=project_id, issue_iid=issue_iid)
        return {"status": "triaged", "issue_iid": issue_iid, "labels": result.suggested_labels}

    except Exception as exc:
        logger.error("task_triage_failed", error=str(exc), project_id=project_id, issue_iid=issue_iid)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="pedroclaw.sync_kb")
def task_sync_kb(project_id: int) -> dict[str, int]:
    """Sync knowledge base from GitLab closed issues and merged MRs."""
    from pedroclaw.knowledge.ingestion import sync_knowledge_base

    logger.info("task_sync_kb_start", project_id=project_id)
    result = _run_async(sync_knowledge_base(project_id))
    logger.info("task_sync_kb_done", **result)
    return result


# Periodic task: sync KB every N hours
celery_app.conf.beat_schedule = {
    "sync-knowledge-base": {
        "task": "pedroclaw.sync_kb",
        "schedule": settings.knowledge_base.get("sync_interval_hours", 6) * 3600,
        "kwargs": {"project_id": 0},  # Override via config
    },
}
