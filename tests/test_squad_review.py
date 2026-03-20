"""Tests for Squad XI review and Triage — real LLM calls, GitLab/KB mocked.

Langfuse tracking é habilitado automaticamente via conftest.py quando
LANGFUSE_ENABLED=true e as env vars estão configuradas.

Requires LLM_REVIEW_API_KEY set in the environment (or .env).
Run via: make test
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pedroclaw.agents.engine import ReviewResult
from pedroclaw.agents.triage import TriageAgent, TriageResult
from pedroclaw.squad.xi import (
    _deduplicate_findings,
    _extract_files_from_diff,
    _parse_comments_json,
    aratu_analyze,
    baiacu_challenge,
    coral_research,
    nautilo_validate,
    squad_review,
)


# ============================================================
# Fixtures
# ============================================================

SAMPLE_DIFF = """\
diff --git a/src/app/users/page.tsx b/src/app/users/page.tsx
--- a/src/app/users/page.tsx
+++ b/src/app/users/page.tsx
@@ -1,5 +1,8 @@
+'use client'
 import { serverFetch } from '@/lib/fetch'
+import { useState } from 'react'

 export default function UsersPage() {
-  const users = await serverFetch('/api/users')
+  const [users, setUsers] = useState<any>([])
+  const color = '#ff0000'
   return <div>{users.map(u => <span>{u.name}</span>)}</div>
 }
"""

SAMPLE_MR_INFO = {
    "iid": 42,
    "title": "feat: refactor users page",
    "description": "Refactored users page to use client component",
    "project_id": 1,
    "labels": ["workflow::in-review"],
    "source_branch": "feat/users",
    "author": {"username": "dev1"},
}


# ============================================================
# Unit tests — helpers (sem LLM, rapidos)
# ============================================================


class TestHelpers:
    def test_extract_files_from_diff(self) -> None:
        files = _extract_files_from_diff(SAMPLE_DIFF)
        assert files == ["src/app/users/page.tsx"]

    def test_parse_comments_json_valid(self) -> None:
        raw = '```json\n[{"file": "a.tsx", "line": 1, "severity": "warning", "body": "bad"}]\n```'
        result = _parse_comments_json(raw)
        assert len(result) == 1
        assert result[0]["file"] == "a.tsx"

    def test_parse_comments_json_empty(self) -> None:
        assert _parse_comments_json("```json\n[]\n```") == []

    def test_parse_comments_json_invalid(self) -> None:
        assert _parse_comments_json("not json at all") == []

    def test_deduplicate_findings(self) -> None:
        findings = [
            {"file": "a.tsx", "line": 10, "body": "issue 1"},
            {"file": "a.tsx", "line": 10, "body": "duplicate"},
            {"file": "b.tsx", "line": 5, "body": "other"},
        ]
        result = _deduplicate_findings(findings)
        assert len(result) == 2


# ============================================================
# Agent tests — LLM real, Langfuse real (quando habilitado)
# ============================================================


@pytest.mark.asyncio
class TestAratu:
    async def test_aratu_returns_valid_risk_analysis(self) -> None:
        result = await aratu_analyze(SAMPLE_DIFF, SAMPLE_MR_INFO)

        assert "overall_risk" in result
        assert result["overall_risk"] in ("low", "medium", "high")
        assert "risk_areas" in result
        assert isinstance(result["risk_areas"], list)


@pytest.mark.asyncio
class TestCoral:
    async def test_coral_returns_findings_list(self) -> None:
        result = await coral_research(SAMPLE_DIFF, "Regra: NUNCA use `any` em TypeScript.")

        assert isinstance(result, list)
        for item in result:
            assert "file" in item
            assert "line" in item
            assert "body" in item


@pytest.mark.asyncio
class TestNautilo:
    async def test_nautilo_validates_and_returns_subset(self) -> None:
        input_findings = [
            {"file": "src/app/users/page.tsx", "line": 5, "severity": "warning", "body": "Uso de `any` proibido."},
            {"file": "src/app/users/page.tsx", "line": 99, "severity": "warning", "body": "Linha 99 nao existe no diff."},
        ]
        result = await nautilo_validate(SAMPLE_DIFF, input_findings)

        assert isinstance(result, list)
        assert len(result) <= len(input_findings)


@pytest.mark.asyncio
class TestBaiacu:
    async def test_baiacu_returns_findings_list(self) -> None:
        result = await baiacu_challenge(SAMPLE_DIFF, [])

        assert isinstance(result, list)


# ============================================================
# Integration — pipeline completo com LLM real
# ============================================================


@pytest.mark.asyncio
class TestSquadReview:
    @patch("pedroclaw.squad.skills.discover_project_rules", return_value={})
    async def test_full_review_pipeline(self, _rules: MagicMock) -> None:
        """Pipeline completo: Aratu -> Coral -> Nautilo -> Baiacu com LLM real."""
        result = await squad_review(SAMPLE_DIFF, SAMPLE_MR_INFO)

        assert isinstance(result, ReviewResult)
        assert result.engine == "squad-xi"
        assert isinstance(result.inline_comments, list)
        assert isinstance(result.approved, bool)


# ============================================================
# Triage — LLM real, KB mockada
# ============================================================


@pytest.mark.asyncio
class TestTriageAgent:
    @patch("pedroclaw.agents.triage.kb_retrieval")
    async def test_triage_classifies_issue(self, mock_kb: MagicMock) -> None:
        mock_kb.find_similar = AsyncMock(return_value=[])

        agent = TriageAgent()
        result = await agent.triage({
            "iid": 99,
            "title": "Login SSO nao funciona",
            "description": "Ao tentar logar via SSO, recebo erro 500. Apenas usuarios com dominio @empresa.com sao afetados.",
            "labels": [],
        })

        assert isinstance(result, TriageResult)
        assert result.nature != ""
        assert result.priority != ""
        assert isinstance(result.suggested_labels, list)
