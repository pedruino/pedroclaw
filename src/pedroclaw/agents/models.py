"""Pydantic response models for Agno agents — structured output schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================
# Triage Agent
# ============================================================

class TriageOutput(BaseModel):
    """Structured output for the triage agent."""

    nature: str = Field(default="type::chore", description="Nature label (e.g. type::bug, type::feature)")
    priority: str = Field(default="priority::medium", description="Priority label (e.g. priority::high)")
    summary: str = Field(default="", description="1-2 sentence summary of the issue")
    suggested_labels: list[str] = Field(default_factory=list, description="List of suggested labels")


# ============================================================
# Squad XI — Aratu (Captain)
# ============================================================

class RiskArea(BaseModel):
    """A single risk area identified by Aratu."""

    file: str = Field(description="Path to the file")
    lines: list[int] = Field(default_factory=list, description="Line numbers of concern")
    concerns: list[str] = Field(default_factory=list, description="Types of concern")
    needs_specialist: bool = Field(default=False, description="Whether a specialist should review this")


class AratuAnalysis(BaseModel):
    """Structured output for Aratu — risk analysis of an MR."""

    risk_areas: list[RiskArea] = Field(default_factory=list, description="List of identified risk areas")
    specialists_needed: list[str] = Field(default_factory=list, description="Specialist agent IDs to invoke")
    overall_risk: str = Field(default="medium", description="Overall risk level: low, medium, high")


# ============================================================
# Squad XI — Coral, Nautilo, Baiacu, Specialists
# ============================================================

class Finding(BaseModel):
    """A single code review finding tied to a file and line."""

    file: str = Field(description="Path to the file")
    line: int = Field(description="Line number")
    severity: str = Field(default="warning", description="Severity: critical, warning, suggestion")
    body: str = Field(description="Concise description of the issue")


class FindingsList(BaseModel):
    """Structured output for agents that produce a list of findings."""

    findings: list[Finding] = Field(default_factory=list, description="List of code review findings")
