"""Workflow state machine — manages issue lifecycle transitions.

States (matching GitLab workflow::* labels):
  triagem → conceito → especificacao → revisao-spec → ready-for-dev → in-dev → in-review → done
"""

from enum import StrEnum
from typing import Any

from pedroclaw.config import settings


class WorkflowState(StrEnum):
    TRIAGEM = "triagem"
    CONCEITO = "conceito"
    ESPECIFICACAO = "especificacao"
    REVISAO_SPEC = "revisao-spec"
    READY_FOR_DEV = "ready-for-dev"
    IN_DEV = "in-dev"
    IN_REVIEW = "in-review"
    DONE = "done"


def _load_transitions() -> dict[str, list[str]]:
    return settings.workflow.get("transitions", {})


class WorkflowEngine:
    """Manages workflow state transitions with validation."""

    def __init__(self) -> None:
        self._transitions = _load_transitions()
        self._initial = settings.workflow.get("initial_state", "triagem")
        self._done_states = set(settings.workflow.get("done_states", ["done"]))

    def can_transition(self, from_state: str, to_state: str) -> bool:
        allowed = self._transitions.get(from_state, [])
        return to_state in allowed

    def validate_transition(self, from_state: str, to_state: str) -> None:
        if not self.can_transition(from_state, to_state):
            allowed = self._transitions.get(from_state, [])
            raise InvalidTransitionError(
                f"Cannot transition from '{from_state}' to '{to_state}'. "
                f"Allowed transitions: {allowed}"
            )

    def get_allowed_transitions(self, from_state: str) -> list[str]:
        return self._transitions.get(from_state, [])

    def is_done(self, state: str) -> bool:
        return state in self._done_states

    @property
    def initial_state(self) -> str:
        return self._initial

    def infer_state_from_mr(self, mr_attrs: dict[str, Any]) -> str | None:
        """Infer workflow state from MR attributes.

        - MR merged → done
        - MR opened/reopened → in-review
        """
        state = mr_attrs.get("state")
        action = mr_attrs.get("action")

        if state == "merged" or action == "merge":
            return WorkflowState.DONE
        if action in ("open", "reopen"):
            return WorkflowState.IN_REVIEW
        return None

    def get_state_label(self, state: str) -> str:
        prefix = settings.labels.get("state_prefix", "workflow::")
        return f"{prefix}{state}"


class InvalidTransitionError(Exception):
    pass


workflow_engine = WorkflowEngine()
