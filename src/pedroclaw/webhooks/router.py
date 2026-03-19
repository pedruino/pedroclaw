"""GitLab webhook receiver — validates token, routes events to handlers."""

import hmac

import structlog
from fastapi import APIRouter, Header, HTTPException, Request

from pedroclaw.config import settings
from pedroclaw.webhooks.handlers import handle_issue_event, handle_merge_request_event, handle_note_event

logger = structlog.get_logger()
router = APIRouter()

EVENT_HANDLERS = {
    "Issue Hook": handle_issue_event,
    "Merge Request Hook": handle_merge_request_event,
    "Note Hook": handle_note_event,
}


def _verify_token(token: str | None) -> None:
    expected = settings.gitlab_webhook_secret
    if not expected:
        return
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid webhook token")


@router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str | None = Header(None),
    x_gitlab_event: str | None = Header(None),
) -> dict[str, str]:
    """Receive GitLab webhook events.

    Responds immediately (< 10s GitLab timeout) and dispatches
    processing to Celery background tasks.
    """
    _verify_token(x_gitlab_token)

    body = await request.json()
    event_type = x_gitlab_event or body.get("object_kind", "unknown")

    logger.info("webhook_received", event_type=event_type, project=body.get("project", {}).get("path_with_namespace"))

    handler = EVENT_HANDLERS.get(event_type)
    if handler:
        handler(body)
        return {"status": "accepted", "event": event_type}

    logger.debug("webhook_ignored", event_type=event_type)
    return {"status": "ignored", "event": event_type}
