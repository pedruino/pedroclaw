"""Tests for webhook endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from pedroclaw.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestWebhooks:
    @patch("pedroclaw.webhooks.router.settings")
    def test_health(self, mock_settings: MagicMock, client: TestClient) -> None:
        mock_settings.gitlab_webhook_secret = "test-token"
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @patch("pedroclaw.webhooks.handlers.task_triage_issue")
    @patch("pedroclaw.webhooks.router.settings")
    def test_issue_open_triggers_triage(self, mock_settings: MagicMock, mock_triage: None, client: TestClient) -> None:
        mock_settings.gitlab_webhook_secret = "test-token"
        payload = {
            "object_kind": "issue",
            "object_attributes": {"action": "open", "iid": 42},
            "project": {"id": 1, "path_with_namespace": "soft-suite/frontend"},
        }
        response = client.post(
            "/webhooks/gitlab",
            json=payload,
            headers={"X-Gitlab-Event": "Issue Hook", "X-Gitlab-Token": "test-token"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    @patch("pedroclaw.webhooks.handlers.task_review_mr")
    @patch("pedroclaw.webhooks.router.settings")
    def test_mr_open_triggers_review(self, mock_settings: MagicMock, mock_review: None, client: TestClient) -> None:
        mock_settings.gitlab_webhook_secret = "test-token"
        payload = {
            "object_kind": "merge_request",
            "object_attributes": {"action": "open", "iid": 99},
            "project": {"id": 1, "path_with_namespace": "soft-suite/frontend"},
        }
        response = client.post(
            "/webhooks/gitlab",
            json=payload,
            headers={"X-Gitlab-Event": "Merge Request Hook", "X-Gitlab-Token": "test-token"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    @patch("pedroclaw.webhooks.router.settings")
    def test_unknown_event_ignored(self, mock_settings: MagicMock, client: TestClient) -> None:
        mock_settings.gitlab_webhook_secret = "test-token"
        response = client.post(
            "/webhooks/gitlab",
            json={"object_kind": "pipeline"},
            headers={"X-Gitlab-Event": "Pipeline Hook", "X-Gitlab-Token": "test-token"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    def test_invalid_token_rejected(self, client: TestClient) -> None:
        with patch("pedroclaw.webhooks.router.settings") as mock_settings:
            mock_settings.gitlab_webhook_secret = "correct-token"
            response = client.post(
                "/webhooks/gitlab",
                json={},
                headers={"X-Gitlab-Event": "Issue Hook", "X-Gitlab-Token": "wrong-token"},
            )
            assert response.status_code == 401
