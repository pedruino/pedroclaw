"""Webhook event handlers — dispatch to Celery tasks for async processing."""

from typing import Any

import structlog

from pedroclaw.tasks.worker import task_review_mr, task_triage_issue

logger = structlog.get_logger()


def handle_issue_event(payload: dict[str, Any]) -> None:
    """Handle GitLab Issue Hook events."""
    attrs = payload.get("object_attributes", {})
    action = attrs.get("action")
    issue_iid = attrs.get("iid")
    project_id = payload.get("project", {}).get("id")

    if action in ("open", "reopen"):
        logger.info("issue_opened", issue_iid=issue_iid, project_id=project_id)
        task_triage_issue.delay(project_id=project_id, issue_iid=issue_iid)
    else:
        logger.debug("issue_action_ignored", action=action, issue_iid=issue_iid)


def handle_merge_request_event(payload: dict[str, Any]) -> None:
    """Handle GitLab Merge Request Hook events."""
    attrs = payload.get("object_attributes", {})
    action = attrs.get("action")
    mr_iid = attrs.get("iid")
    project_id = payload.get("project", {}).get("id")

    if action in ("open", "reopen", "update"):
        logger.info("mr_opened", mr_iid=mr_iid, project_id=project_id, action=action)
        task_review_mr.delay(project_id=project_id, mr_iid=mr_iid)
    else:
        logger.debug("mr_action_ignored", action=action, mr_iid=mr_iid)


def handle_note_event(payload: dict[str, Any]) -> None:
    """Handle GitLab Note (comment) Hook events.

    Enables interactive commands like '@pedroclaw review' or '@pedroclaw triage'.
    """
    attrs = payload.get("object_attributes", {})
    note_body: str = attrs.get("note", "")
    noteable_type = attrs.get("noteable_type")
    project_id = payload.get("project", {}).get("id")

    if "@pedroclaw" not in note_body:
        return

    command = note_body.split("@pedroclaw", 1)[1].strip().split()[0].lower() if "@pedroclaw" in note_body else ""

    if command == "review" and noteable_type == "MergeRequest":
        mr_iid = payload.get("merge_request", {}).get("iid")
        if mr_iid:
            logger.info("command_review", mr_iid=mr_iid)
            task_review_mr.delay(project_id=project_id, mr_iid=mr_iid)

    elif command == "triage" and noteable_type == "Issue":
        issue_iid = payload.get("issue", {}).get("iid")
        if issue_iid:
            logger.info("command_triage", issue_iid=issue_iid)
            task_triage_issue.delay(project_id=project_id, issue_iid=issue_iid)

    else:
        logger.debug("command_unknown", command=command)
