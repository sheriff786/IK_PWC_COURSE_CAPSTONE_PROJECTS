"""
Phase 7, roadmap item 7: consensus-behavior test.

Formalizes the synthetic checks already run manually in the Phase 5
notebook: a CRITICAL finding anywhere must never be averaged away, a
failed dimension must show up in unresolved_issues, and only genuinely
equivalent findings (same dimension + title + shared evidence) get
deduplicated.
"""

from contractiq.models import DimensionResult, Finding, RiskDimension, Severity, VerificationStatus
from contractiq.orchestration import build_consensus


def _finding(dimension, severity, title, evidence_ids, finding_id=None):
    return Finding(
        finding_id=finding_id or f"{dimension.value}-test-{title[:8]}",
        dimension=dimension, severity=severity, title=title, rationale="test",
        confidence=0.9, evidence_ids=evidence_ids,
        verification_status=VerificationStatus.VERIFIED,
    )


def test_critical_finding_is_never_averaged_away():
    legal = DimensionResult(dimension=RiskDimension.LEGAL, success=True,
                             findings=[_finding(RiskDimension.LEGAL, Severity.LOW, "Minor clause", ["c1"])])
    financial = DimensionResult(dimension=RiskDimension.FINANCIAL, success=True,
                                 findings=[_finding(RiskDimension.FINANCIAL, Severity.CRITICAL,
                                                     "Uncapped exposure", ["c2"])])
    operational = DimensionResult(dimension=RiskDimension.OPERATIONAL, success=True, findings=[])

    assessment = build_consensus("TEST-001", {
        RiskDimension.LEGAL: legal, RiskDimension.FINANCIAL: financial, RiskDimension.OPERATIONAL: operational,
    })
    assert assessment.overall_risk == Severity.CRITICAL


def test_failed_dimension_appears_in_unresolved_issues():
    legal = DimensionResult(dimension=RiskDimension.LEGAL, success=True, findings=[])
    financial = DimensionResult(dimension=RiskDimension.FINANCIAL, success=True, findings=[])
    operational = DimensionResult(dimension=RiskDimension.OPERATIONAL, success=False, findings=[],
                                   error="simulated timeout")

    assessment = build_consensus("TEST-002", {
        RiskDimension.LEGAL: legal, RiskDimension.FINANCIAL: financial, RiskDimension.OPERATIONAL: operational,
    })
    assert len(assessment.unresolved_issues) == 1
    assert "operational" in assessment.unresolved_issues[0]
    assert "simulated timeout" in assessment.unresolved_issues[0]


def test_only_genuinely_equivalent_findings_are_deduplicated():
    # Dedup only affects the merged list used for consensus_actions
    # (per-dimension findings in dimension_results are kept untouched, so
    # the original per-specialist record stays intact) — use HIGH severity
    # so both cases actually show up in consensus_actions.
    same_title_different_evidence = [
        _finding(RiskDimension.LEGAL, Severity.HIGH, "Termination clause", ["c1"], "legal-a"),
        _finding(RiskDimension.LEGAL, Severity.HIGH, "Termination clause", ["c2"], "legal-b"),
    ]
    exact_duplicate = [
        _finding(RiskDimension.LEGAL, Severity.HIGH, "Termination clause", ["c1"], "legal-a"),
        _finding(RiskDimension.LEGAL, Severity.HIGH, "Termination clause", ["c1"], "legal-a-retry"),
    ]

    legal_disagreement = DimensionResult(dimension=RiskDimension.LEGAL, success=True,
                                          findings=same_title_different_evidence)
    assessment = build_consensus("TEST-003", {
        RiskDimension.LEGAL: legal_disagreement,
        RiskDimension.FINANCIAL: DimensionResult(dimension=RiskDimension.FINANCIAL, success=True, findings=[]),
        RiskDimension.OPERATIONAL: DimensionResult(dimension=RiskDimension.OPERATIONAL, success=True, findings=[]),
    })
    assert len(assessment.consensus_actions) == 2, "different evidence for the same title must be kept, not deduplicated"

    legal_duplicate = DimensionResult(dimension=RiskDimension.LEGAL, success=True, findings=exact_duplicate)
    assessment2 = build_consensus("TEST-004", {
        RiskDimension.LEGAL: legal_duplicate,
        RiskDimension.FINANCIAL: DimensionResult(dimension=RiskDimension.FINANCIAL, success=True, findings=[]),
        RiskDimension.OPERATIONAL: DimensionResult(dimension=RiskDimension.OPERATIONAL, success=True, findings=[]),
    })
    assert len(assessment2.consensus_actions) == 1, "same dimension+title+evidence must be deduplicated"
