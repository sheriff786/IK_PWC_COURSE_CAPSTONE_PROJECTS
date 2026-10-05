"""Conditional routing must fail OPEN: a skipped dimension is only ever a
deliberate decision, never the silent result of a classification failure."""

from unittest.mock import patch

from contractiq.models import RiskDimension
from contractiq.orchestration import _skipped_result, route_dimensions

_ALL = {RiskDimension.LEGAL, RiskDimension.FINANCIAL, RiskDimension.OPERATIONAL}


class _Triage:
    def __init__(self, legal, financial, operational):
        self.has_legal_content = legal
        self.has_financial_content = financial
        self.has_operational_content = operational
        self.rationale = "test"


def test_routing_disabled_runs_everything():
    plan = route_dimensions("ANY", enabled=False)
    assert set(plan["dimensions"]) == _ALL
    assert plan["routed"] is False


def test_triage_failure_fails_open():
    """A failed classification must never cause analysis to be skipped."""
    with patch("contractiq.orchestration.triage_document", return_value=None):
        plan = route_dimensions("ANY", enabled=True)
    assert set(plan["dimensions"]) == _ALL
    assert plan["routed"] is False


def test_empty_triage_result_fails_open():
    with patch("contractiq.orchestration.triage_document",
               return_value=_Triage(False, False, False)):
        plan = route_dimensions("ANY", enabled=True)
    assert set(plan["dimensions"]) == _ALL, "an empty plan would analyze nothing"


def test_triage_narrows_to_relevant_dimensions_only():
    with patch("contractiq.orchestration.triage_document",
               return_value=_Triage(False, False, True)):
        plan = route_dimensions("OPS-003", enabled=True)
    assert plan["dimensions"] == [RiskDimension.OPERATIONAL]
    assert plan["routed"] is True


def test_skipped_dimension_is_recorded_as_a_decision_not_a_failure():
    result = _skipped_result(RiskDimension.FINANCIAL)
    assert result.success is True, "a deliberate skip is not a failure"
    assert result.findings == []
    assert "skipped by routing" in result.error
