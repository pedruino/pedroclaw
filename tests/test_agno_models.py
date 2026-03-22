"""Tests for Agno Pydantic models — structured output validation."""

import pytest

from pedroclaw.agents.models import AratuAnalysis, Finding, FindingsList, RiskArea, TriageOutput


class TestPydanticModels:
    """Test that Pydantic models work correctly for structured output."""

    def test_triage_output_model(self) -> None:
        """Test TriageOutput model validation."""
        output = TriageOutput(
            nature="type::bug",
            priority="priority::high",
            summary="Login authentication fails for SSO users",
            suggested_labels=["bug", "authentication", "sso"]
        )

        assert output.nature == "type::bug"
        assert output.priority == "priority::high"
        assert "authentication" in output.summary
        assert len(output.suggested_labels) == 3

    def test_triage_output_defaults(self) -> None:
        """Test TriageOutput default values."""
        output = TriageOutput()

        assert output.nature == "type::chore"
        assert output.priority == "priority::medium"
        assert output.summary == ""
        assert output.suggested_labels == []

    def test_finding_model(self) -> None:
        """Test Finding model validation."""
        finding = Finding(
            file="src/app/users/page.tsx",
            line=15,
            severity="warning",
            body="Avoid using 'any' type in TypeScript"
        )

        assert finding.file == "src/app/users/page.tsx"
        assert finding.line == 15
        assert finding.severity == "warning"
        assert "any" in finding.body

    def test_finding_model_defaults(self) -> None:
        """Test Finding model default values."""
        finding = Finding(
            file="src/test.ts",
            line=1,
            body="Test issue"
        )

        assert finding.severity == "warning"  # default

    def test_findings_list_model(self) -> None:
        """Test FindingsList model with multiple findings."""
        findings = [
            Finding(file="a.tsx", line=10, body="Issue 1"),
            Finding(file="b.tsx", line=20, severity="critical", body="Issue 2"),
        ]
        findings_list = FindingsList(findings=findings)

        assert len(findings_list.findings) == 2
        assert findings_list.findings[0].file == "a.tsx"
        assert findings_list.findings[1].severity == "critical"

    def test_findings_list_empty(self) -> None:
        """Test FindingsList with empty findings."""
        findings_list = FindingsList()

        assert len(findings_list.findings) == 0

    def test_aratu_analysis_model(self) -> None:
        """Test AratuAnalysis model validation."""
        risk_areas = [
            RiskArea(
                file="src/app/users/page.tsx",
                lines=[10, 15, 20],
                concerns=["security", "performance"],
                needs_specialist=True
            )
        ]
        analysis = AratuAnalysis(
            risk_areas=risk_areas,
            specialists_needed=["security-specialist"],
            overall_risk="high"
        )

        assert len(analysis.risk_areas) == 1
        assert analysis.risk_areas[0].file == "src/app/users/page.tsx"
        assert "security" in analysis.risk_areas[0].concerns
        assert analysis.specialists_needed == ["security-specialist"]
        assert analysis.overall_risk == "high"

    def test_aratu_analysis_defaults(self) -> None:
        """Test AratuAnalysis default values."""
        analysis = AratuAnalysis()

        assert len(analysis.risk_areas) == 0
        assert len(analysis.specialists_needed) == 0
        assert analysis.overall_risk == "medium"

    def test_risk_area_model(self) -> None:
        """Test RiskArea model validation."""
        risk_area = RiskArea(
            file="src/components/Button.tsx",
            lines=[5, 10, 15],
            concerns=["accessibility", "performance"],
            needs_specialist=False
        )

        assert risk_area.file == "src/components/Button.tsx"
        assert len(risk_area.lines) == 3
        assert len(risk_area.concerns) == 2
        assert risk_area.needs_specialist is False

    def test_model_serialization(self) -> None:
        """Test that models can be serialized to dict."""
        finding = Finding(
            file="test.ts",
            line=42,
            severity="critical",
            body="Critical issue found"
        )

        # Test model_dump method
        data = finding.model_dump()
        assert data["file"] == "test.ts"
        assert data["line"] == 42
        assert data["severity"] == "critical"
        assert data["body"] == "Critical issue found"

        # Test JSON serialization
        import json
        json_str = finding.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["file"] == "test.ts"
