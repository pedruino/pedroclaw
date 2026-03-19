"""Tests for the workflow state machine."""

import pytest

from pedroclaw.workflow.states import InvalidTransitionError, WorkflowEngine


@pytest.fixture
def engine() -> WorkflowEngine:
    return WorkflowEngine()


class TestWorkflowEngine:
    def test_initial_state(self, engine: WorkflowEngine) -> None:
        assert engine.initial_state == "triagem"

    def test_feature_flow(self, engine: WorkflowEngine) -> None:
        assert engine.can_transition("triagem", "conceito")
        assert engine.can_transition("conceito", "especificacao")
        assert engine.can_transition("especificacao", "revisao-spec")
        assert engine.can_transition("revisao-spec", "ready-for-dev")
        assert engine.can_transition("ready-for-dev", "in-dev")
        assert engine.can_transition("in-dev", "in-review")
        assert engine.can_transition("in-review", "done")

    def test_bug_flow(self, engine: WorkflowEngine) -> None:
        assert engine.can_transition("triagem", "in-dev")

    def test_duvida_flow(self, engine: WorkflowEngine) -> None:
        assert engine.can_transition("triagem", "done")

    def test_backward_transitions(self, engine: WorkflowEngine) -> None:
        assert engine.can_transition("especificacao", "conceito")
        assert engine.can_transition("revisao-spec", "especificacao")
        assert engine.can_transition("in-dev", "ready-for-dev")
        assert engine.can_transition("in-review", "in-dev")

    def test_invalid_transitions(self, engine: WorkflowEngine) -> None:
        assert not engine.can_transition("conceito", "done")
        assert not engine.can_transition("triagem", "in-review")
        assert not engine.can_transition("done", "conceito")

    def test_validate_raises_on_invalid(self, engine: WorkflowEngine) -> None:
        with pytest.raises(InvalidTransitionError):
            engine.validate_transition("conceito", "done")

    def test_is_done(self, engine: WorkflowEngine) -> None:
        assert engine.is_done("done")
        assert not engine.is_done("in-review")

    def test_infer_state_from_mr_open(self, engine: WorkflowEngine) -> None:
        assert engine.infer_state_from_mr({"action": "open"}) == "in-review"

    def test_infer_state_from_mr_merge(self, engine: WorkflowEngine) -> None:
        assert engine.infer_state_from_mr({"state": "merged"}) == "done"

    def test_get_state_label(self, engine: WorkflowEngine) -> None:
        assert engine.get_state_label("in-dev") == "workflow::in-dev"
        assert engine.get_state_label("in-review") == "workflow::in-review"
