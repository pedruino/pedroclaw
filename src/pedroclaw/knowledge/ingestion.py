"""Knowledge base ingestion — syncs closed issues and merged MRs from GitLab."""

import structlog

from pedroclaw.gitlab.client import gitlab_client
from pedroclaw.knowledge.store import upsert_entry

logger = structlog.get_logger()


async def ingest_closed_issues(project_id: int) -> int:
    """Ingest closed issues into the knowledge base."""
    issues = gitlab_client.list_closed_issues(project_id)
    count = 0

    for issue in issues:
        title = issue.get("title", "")
        description = issue.get("description", "") or ""
        labels = issue.get("labels", [])
        iid = issue.get("iid")

        # Use the last comment or description as "resolution"
        resolution = description[:500] if description else ""

        await upsert_entry(
            source_type="issue",
            source_id=iid,
            project_id=project_id,
            title=title,
            content=description,
            labels=labels,
            resolution=resolution,
        )
        count += 1

    logger.info("issues_ingested", project_id=project_id, count=count)
    return count


async def ingest_merged_mrs(project_id: int) -> int:
    """Ingest merged MRs into the knowledge base."""
    mrs = gitlab_client.list_merged_mrs(project_id)
    count = 0

    for mr in mrs:
        title = mr.get("title", "")
        description = mr.get("description", "") or ""
        labels = mr.get("labels", [])
        iid = mr.get("iid")

        await upsert_entry(
            source_type="mr",
            source_id=iid,
            project_id=project_id,
            title=title,
            content=description,
            labels=labels,
        )
        count += 1

    logger.info("mrs_ingested", project_id=project_id, count=count)
    return count


async def sync_knowledge_base(project_id: int) -> dict[str, int]:
    """Full sync: ingest all closed issues and merged MRs."""
    issues_count = await ingest_closed_issues(project_id)
    mrs_count = await ingest_merged_mrs(project_id)
    return {"issues": issues_count, "mrs": mrs_count}
