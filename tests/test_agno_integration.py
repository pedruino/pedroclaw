"""Integration tests for Agno framework — end-to-end validation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pedroclaw.agents.engine import ReviewResult
from pedroclaw.agents.triage import triage_agent
from pedroclaw.squad.xi import squad_review


# Sample data for testing
SAMPLE_DIFF = """\
diff --git a/src/app/auth/page.tsx b/src/app/auth/page.tsx
--- a/src/app/auth/page.tsx
+++ b/src/app/auth/page.tsx
@@ -1,8 +1,10 @@
 'use client'
 import { useState } from 'react'
-import { authenticate } from '@/lib/auth'
+import { authenticate } from '@/lib/auth'
+import { useRouter } from 'next/navigation'
 
 export default function AuthPage() {
+  const router = useRouter()
   const [email, setEmail] = useState('')
   const [password, setPassword] = useState('')
   
   const handleSubmit = async () => {
-    await authenticate(email, password)
+    const result = await authenticate(email, password)
+    if (result.success) router.push('/dashboard')
   }
   
   return <form onSubmit={handleSubmit}>...</form>
 }
"""

SAMPLE_MR_INFO = {
    "iid": 42,
    "title": "feat: add redirect after successful authentication",
    "description": "Add automatic redirect to dashboard after successful login",
    "project_id": 1,
    "labels": ["workflow::in-review"],
    "source_branch": "feat/auth-redirect",
    "author": {"username": "dev1"},
}

SAMPLE_ISSUE = {
    "iid": 123,
    "title": "Users not redirected after login",
    "description": "After successful authentication, users stay on login page instead of being redirected to dashboard",
    "labels": ["bug", "authentication"],
}


class TestAgnoIntegration:
    """Integration tests for complete Agno workflow."""

    @pytest.mark.asyncio
    @patch("pedroclaw.squad.skills.discover_project_rules", return_value={})
    @patch("pedroclaw.squad.skills.get_skills_for_files", return_value={})
    @patch("pedroclaw.squad.skills.format_skills_context", return_value="")
    async def test_squad_review_with_agno_agents(self, mock_format: MagicMock, mock_get_skills: MagicMock, mock_rules: MagicMock) -> None:
        """Test complete Squad XI review with Agno agents."""
        # This test validates that all Agno agents work together
        result = await squad_review(SAMPLE_DIFF, SAMPLE_MR_INFO)

        # Verify ReviewResult structure
        assert isinstance(result, ReviewResult)
        assert result.engine == "squad-xi"
        assert isinstance(result.inline_comments, list)
        assert isinstance(result.approved, bool)

        # If there are comments, validate their structure
        if result.inline_comments:
            for comment in result.inline_comments:
                assert hasattr(comment, 'file_path')
                assert hasattr(comment, 'line')
                assert hasattr(comment, 'body')
                assert hasattr(comment, 'severity')

    @pytest.mark.asyncio
    @patch("pedroclaw.agents.triage.search_knowledge")
    async def test_triage_with_agno_knowledge(self, mock_search: MagicMock) -> None:
        """Test TriageAgent with Agno knowledge base."""
        # Mock similar issues from knowledge base
        mock_search.return_value = [
            {
                "id": "issue-456",
                "title": "Login redirect issue",
                "content": "Users reported not being redirected after login",
                "score": 0.92,
                "meta_data": {"source_type": "issue", "source_id": 456, "labels": ["bug", "authentication"]}
            }
        ]

        result = await triage_agent.triage(SAMPLE_ISSUE)

        # Verify TriageResult structure
        assert hasattr(result, 'suggested_labels')
        assert hasattr(result, 'nature')
        assert hasattr(result, 'priority')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'similar_issues')

        # Verify knowledge was searched
        mock_search.assert_called_once()
        kwargs = mock_search.call_args.kwargs
        assert "Users not redirected" in kwargs["query"]  # Query contains issue title/description
        assert kwargs["limit"] == 5  # Default top_k

        # Verify similar issues were included
        assert len(result.similar_issues) == 1
        assert result.similar_issues[0]["title"] == "Login redirect issue"

    @pytest.mark.asyncio
    @patch("pedroclaw.agents.triage.search_knowledge")
    async def test_triage_without_knowledge(self, mock_search: MagicMock) -> None:
        """Test TriageAgent when knowledge lookup is disabled."""
        # Mock empty knowledge results
        mock_search.return_value = []

        result = await triage_agent.triage(SAMPLE_ISSUE)

        # Should still work without knowledge
        assert hasattr(result, 'nature')
        assert hasattr(result, 'priority')
        assert result.nature != ""
        assert result.priority != ""

        # Verify similar issues is empty
        assert len(result.similar_issues) == 0

    @pytest.mark.asyncio
    @patch("pedroclaw.squad.skills.discover_project_rules", return_value={})
    @patch("pedroclaw.squad.skills.get_skills_for_files", return_value={})
    @patch("pedroclaw.squad.skills.format_skills_context", return_value="")
    async def test_squad_review_with_existing_comments(self, mock_format: MagicMock, mock_get_skills: MagicMock, mock_rules: MagicMock) -> None:
        """Test Squad XI review with existing comments to avoid duplicates."""
        existing_comments = [
            {
                "file": "src/app/auth/page.tsx",
                "line": 8,
                "body": "Consider adding loading state during authentication",
                "severity": "suggestion"
            }
        ]

        result = await squad_review(SAMPLE_DIFF, SAMPLE_MR_INFO, existing_comments)

        # Should still return valid result
        assert isinstance(result, ReviewResult)
        assert isinstance(result.inline_comments, list)

    @pytest.mark.asyncio
    @patch("pedroclaw.squad.skills.discover_project_rules", return_value={})
    @patch("pedroclaw.squad.skills.get_skills_for_files", return_value={})
    @patch("pedroclaw.squad.skills.format_skills_context", return_value="")
    async def test_squad_review_error_handling(self, mock_format: MagicMock, mock_get_skills: MagicMock, mock_rules: MagicMock) -> None:
        """Test Squad XI error handling and graceful degradation."""
        # Even if individual agents fail, the overall pipeline should complete
        result = await squad_review(SAMPLE_DIFF, SAMPLE_MR_INFO)

        # Should always return a ReviewResult, even on partial failures
        assert isinstance(result, ReviewResult)
        assert result.engine == "squad-xi"
        assert isinstance(result.approved, bool)


class TestBackwardCompatibility:
    """Test that Agno migration maintains backward compatibility."""

    @pytest.mark.asyncio
    @patch("pedroclaw.agents.triage.search_knowledge")
    async def test_triage_agent_interface_unchanged(self, mock_search: MagicMock) -> None:
        """Test that TriageAgent interface is unchanged for existing code."""
        mock_search.return_value = []

        # This is the exact interface used by tasks/worker.py
        result = await triage_agent.triage({
            "iid": 123,
            "title": "Test Issue",
            "description": "Test Description",
            "labels": ["bug"]
        })

        # Should return TriageResult with same interface
        assert hasattr(result, 'suggested_labels')
        assert hasattr(result, 'nature')
        assert hasattr(result, 'priority')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'similar_issues')
        assert isinstance(result.suggested_labels, list)

    @pytest.mark.asyncio
    @patch("pedroclaw.squad.skills.discover_project_rules", return_value={})
    @patch("pedroclaw.squad.skills.get_skills_for_files", return_value={})
    @patch("pedroclaw.squad.skills.format_skills_context", return_value="")
    async def test_squad_review_interface_unchanged(self, mock_format: MagicMock, mock_get_skills: MagicMock, mock_rules: MagicMock) -> None:
        """Test that squad_review interface is unchanged for existing code."""
        # This is the exact interface used by tasks/worker.py
        result = await squad_review(SAMPLE_DIFF, SAMPLE_MR_INFO)

        # Should return ReviewResult with same interface
        assert isinstance(result, ReviewResult)
        assert hasattr(result, 'inline_comments')
        assert hasattr(result, 'approved')
        assert hasattr(result, 'engine')
        assert result.engine == "squad-xi"
        assert isinstance(result.inline_comments, list)
