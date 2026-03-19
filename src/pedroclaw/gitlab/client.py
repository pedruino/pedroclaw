"""GitLab API client — wraps python-gitlab for issues, MRs, labels, comments."""

from typing import Any

import gitlab
import structlog

from pedroclaw.config import settings
from pedroclaw.workflow.states import workflow_engine

logger = structlog.get_logger()


class GitLabClient:
    """High-level GitLab operations for Pedroclaw."""

    def __init__(self) -> None:
        self._gl = gitlab.Gitlab(url=settings.gitlab_url, private_token=settings.gitlab_token)

    def _project(self, project_id: int) -> Any:
        return self._gl.projects.get(project_id)

    # --- Issues ---

    def get_issue(self, project_id: int, issue_iid: int) -> dict[str, Any]:
        project = self._project(project_id)
        issue = project.issues.get(issue_iid)
        return issue.attributes

    def add_issue_labels(self, project_id: int, issue_iid: int, labels: list[str]) -> None:
        project = self._project(project_id)
        issue = project.issues.get(issue_iid)
        current = set(issue.labels)
        updated = list(current | set(labels))
        issue.labels = updated
        issue.save()
        logger.info("labels_added", issue_iid=issue_iid, labels=labels)

    def set_issue_state_label(self, project_id: int, issue_iid: int, new_state: str) -> None:
        """Replace workflow state label on an issue."""
        project = self._project(project_id)
        issue = project.issues.get(issue_iid)
        prefix = settings.labels.get("state_prefix", "state::")

        current_labels = [l for l in issue.labels if not l.startswith(prefix)]
        current_labels.append(workflow_engine.get_state_label(new_state))
        issue.labels = current_labels
        issue.save()
        logger.info("state_label_set", issue_iid=issue_iid, state=new_state)

    def add_issue_comment(self, project_id: int, issue_iid: int, body: str) -> None:
        project = self._project(project_id)
        issue = project.issues.get(issue_iid)
        issue.notes.create({"body": body})

    # --- Merge Requests ---

    def get_mr(self, project_id: int, mr_iid: int) -> dict[str, Any]:
        project = self._project(project_id)
        mr = project.mergerequests.get(mr_iid)
        return mr.attributes

    def get_mr_diff(self, project_id: int, mr_iid: int) -> str:
        """Get the full diff of a merge request as a unified string."""
        project = self._project(project_id)
        mr = project.mergerequests.get(mr_iid)
        changes = mr.changes()
        diffs: list[str] = []
        for change in changes.get("changes", []):
            header = f"--- a/{change['old_path']}\n+++ b/{change['new_path']}"
            diffs.append(f"{header}\n{change.get('diff', '')}")
        return "\n".join(diffs)

    def get_mr_valid_diff_lines(self, project_id: int, mr_iid: int) -> dict[str, set[int]]:
        """Extract valid new-side line numbers per file from MR diff.

        Returns a dict like {"path/to/file.tsx": {10, 11, 15, 20}} with
        only the lines that actually appear in the diff (added/modified).
        """
        import re

        project = self._project(project_id)
        mr = project.mergerequests.get(mr_iid)
        changes = mr.changes()

        valid_lines: dict[str, set[int]] = {}
        for change in changes.get("changes", []):
            file_path = change.get("new_path", "")
            diff_text = change.get("diff", "")
            lines: set[int] = set()
            current_line = 0

            for line in diff_text.split("\n"):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if hunk_match:
                    current_line = int(hunk_match.group(1))
                    continue

                if line.startswith("+") and not line.startswith("+++"):
                    lines.add(current_line)
                    current_line += 1
                elif line.startswith("-") and not line.startswith("---"):
                    # Deleted lines don't advance new-side line counter
                    pass
                else:
                    # Context line
                    current_line += 1

            if lines:
                valid_lines[file_path] = lines

        return valid_lines

    def find_nearest_valid_line(self, target_line: int, valid_lines: set[int]) -> int | None:
        """Find the nearest valid diff line to the target, within 5 lines."""
        if target_line in valid_lines:
            return target_line
        for offset in range(1, 6):
            if target_line + offset in valid_lines:
                return target_line + offset
            if target_line - offset in valid_lines:
                return target_line - offset
        return None

    def get_mr_pedroclaw_comments(self, project_id: int, mr_iid: int) -> list[dict[str, Any]]:
        """Busca comentarios existentes do Pedroclaw numa MR.

        Retorna lista com file_path + line dos comentarios inline ja postados,
        pra evitar duplicacao.
        """
        project = self._project(project_id)
        mr = project.mergerequests.get(mr_iid)

        existing: list[dict[str, Any]] = []
        for discussion in mr.discussions.list(per_page=100, iterator=True):
            for note in discussion.attributes.get("notes", []):
                body = note.get("body", "")
                # So considera comentarios do Pedroclaw (comecam com 🦀)
                if not body.startswith("🦀"):
                    continue

                position = note.get("position")
                if position:
                    existing.append({
                        "file": position.get("new_path", ""),
                        "line": position.get("new_line", 0),
                        "body": body,
                    })
                else:
                    # Comentario geral (nao inline)
                    existing.append({
                        "file": "",
                        "line": 0,
                        "body": body,
                    })

        logger.info("existing_comments_found", count=len(existing), mr_iid=mr_iid)
        return existing

    def add_mr_comment(self, project_id: int, mr_iid: int, body: str) -> None:
        project = self._project(project_id)
        mr = project.mergerequests.get(mr_iid)
        mr.notes.create({"body": body})

    def add_mr_inline_comment(
        self,
        project_id: int,
        mr_iid: int,
        body: str,
        file_path: str,
        new_line: int,
        base_sha: str,
        head_sha: str,
        start_sha: str,
    ) -> None:
        """Add an inline comment on a specific line of a MR diff."""
        project = self._project(project_id)
        mr = project.mergerequests.get(mr_iid)
        mr.discussions.create({
            "body": body,
            "position": {
                "base_sha": base_sha,
                "head_sha": head_sha,
                "start_sha": start_sha,
                "position_type": "text",
                "new_path": file_path,
                "new_line": new_line,
            },
        })

    def get_mr_linked_issues(self, project_id: int, mr_iid: int) -> list[int]:
        """Extract linked issue IIDs from MR description (e.g., Closes #123)."""
        mr = self.get_mr(project_id, mr_iid)
        description = mr.get("description", "") or ""
        import re

        pattern = r"(?:closes|fixes|resolves)\s+#(\d+)"
        return [int(m) for m in re.findall(pattern, description, re.IGNORECASE)]

    # --- Labels ---

    def ensure_labels_exist(self, project_id: int, labels: list[str]) -> None:
        """Create labels in the project if they don't exist yet."""
        project = self._project(project_id)
        existing = {l.name for l in project.labels.list(per_page=100, iterator=True)}
        for label_name in labels:
            if label_name not in existing:
                project.labels.create({"name": label_name, "color": "#428BCA"})
                logger.info("label_created", label=label_name)

    # --- Project Issues (for KB sync) ---

    def list_closed_issues(self, project_id: int, per_page: int = 100) -> list[dict[str, Any]]:
        """List closed issues for knowledge base ingestion."""
        project = self._project(project_id)
        issues = project.issues.list(state="closed", per_page=per_page, order_by="updated_at", iterator=True)
        return [i.attributes for i in issues]

    def list_merged_mrs(self, project_id: int, per_page: int = 100) -> list[dict[str, Any]]:
        """List merged MRs for knowledge base ingestion."""
        project = self._project(project_id)
        mrs = project.mergerequests.list(state="merged", per_page=per_page, order_by="updated_at", iterator=True)
        return [m.attributes for m in mrs]


gitlab_client = GitLabClient()
