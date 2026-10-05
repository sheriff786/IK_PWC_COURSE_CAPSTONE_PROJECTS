"""
ContractIQ — Phase 5: parallel execution and consensus building.

Roadmap reference: 05_Multi_Agent_Orchestration.ipynb
Runs the three specialist agents (Legal, Financial, Operational) over one
contract — sequentially first (so a single agent's failure and the result
shape are easy to debug in isolation), then concurrently only once the
sequential path is proven correct, in that order per the roadmap.

Guiding rule: consensus never lets an average hide real risk. A
Severity.CRITICAL finding anywhere in any dimension always forces
overall_risk to CRITICAL, regardless of what the weighted score says.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agents import (
    analyze_financial_risk,
    analyze_legal_risk,
    analyze_operational_risk,
    save_financial_assessment,
    save_legal_assessment,
    save_operational_assessment,
    triage_document,
)
from .config import FINANCIAL_AGENT_MODEL, HITL_CONFIDENCE_THRESHOLD, LEGAL_AGENT_MODEL, \
    OPERATIONAL_AGENT_MODEL, REPORTS_ROOT, RISK_SCORE_MAP, RISK_WEIGHTS, ROUTING_ENABLED_BY_DEFAULT
from .models import Assessment, DimensionResult, Finding, RiskDimension, Severity, VerificationStatus

try:
    from langfuse.decorators import observe
except ImportError:  # Langfuse not configured — tracing becomes a no-op, not a crash
    def observe(*_args, **_kwargs):
        def decorator(fn):
            return fn
        return decorator


_ANALYZERS = {
    RiskDimension.LEGAL: analyze_legal_risk,
    RiskDimension.FINANCIAL: analyze_financial_risk,
    RiskDimension.OPERATIONAL: analyze_operational_risk,
}
_SAVERS = {
    RiskDimension.LEGAL: save_legal_assessment,
    RiskDimension.FINANCIAL: save_financial_assessment,
    RiskDimension.OPERATIONAL: save_operational_assessment,
}
_ALL_DIMENSIONS = (RiskDimension.LEGAL, RiskDimension.FINANCIAL, RiskDimension.OPERATIONAL)


def _run_with_retries(dimension: RiskDimension, doc_id: str, max_retries: int = 1) -> DimensionResult:
    """analyze_*() already applies closed-loop recovery per LLM call
    (resilience.call_with_recovery: backoff / model escalation / fail-fast).
    This is the OUTER loop for a whole-dimension failure, and records how
    many attempts it took so partial runs stay visible in the Assessment."""
    analyzer = _ANALYZERS[dimension]
    attempt = 0
    result = analyzer(doc_id)
    while not result.success and attempt < max_retries:
        attempt += 1
        result = analyzer(doc_id)
    result.retry_count = attempt
    return result


def route_dimensions(doc_id: str, enabled: bool = ROUTING_ENABLED_BY_DEFAULT) -> Dict[str, Any]:
    """Conditional routing: one cheap triage call decides which specialists
    actually run for this document. A service report with no pricing clauses
    shouldn't pay for a full financial sweep.

    Fails OPEN by design — if triage errors or is disabled, every dimension
    runs. Skipping analysis on a failed classification would silently lose
    real risk, which is strictly worse than spending a few extra cheap calls."""
    if not enabled:
        return {"dimensions": list(_ALL_DIMENSIONS), "routed": False,
                "rationale": "routing disabled — all dimensions run"}

    triage = triage_document(doc_id)
    if triage is None:
        return {"dimensions": list(_ALL_DIMENSIONS), "routed": False,
                "rationale": "triage unavailable — failing open, all dimensions run"}

    selected = [d for d, keep in (
        (RiskDimension.LEGAL, triage.has_legal_content),
        (RiskDimension.FINANCIAL, triage.has_financial_content),
        (RiskDimension.OPERATIONAL, triage.has_operational_content),
    ) if keep]

    if not selected:  # never return an empty plan — that would analyze nothing
        return {"dimensions": list(_ALL_DIMENSIONS), "routed": False,
                "rationale": f"triage selected nothing — failing open. {triage.rationale}"}

    return {"dimensions": selected, "routed": True, "rationale": triage.rationale}


def _skipped_result(dimension: RiskDimension) -> DimensionResult:
    """A dimension that routing deliberately skipped is recorded explicitly
    (success=True, zero findings, reason noted) rather than being silently
    absent — the report must show it was a decision, not a failure."""
    return DimensionResult(dimension=dimension, success=True, findings=[],
                            error="skipped by routing: triage found no content for this dimension")


@observe(name="orchestrate_sequential")
def run_sequential(doc_id: str, max_retries: int = 1,
                    routing: bool = ROUTING_ENABLED_BY_DEFAULT) -> Dict[RiskDimension, DimensionResult]:
    """Roadmap-mandated first step: run specialists one after another.
    Simple to debug — if something's wrong, it's obvious which dimension
    and which attempt caused it. Honors conditional routing."""
    plan = route_dimensions(doc_id, routing)
    selected = set(plan["dimensions"])
    results: Dict[RiskDimension, DimensionResult] = {}
    for dimension in _ALL_DIMENSIONS:
        results[dimension] = (_run_with_retries(dimension, doc_id, max_retries)
                               if dimension in selected else _skipped_result(dimension))
        _SAVERS[dimension](doc_id, results[dimension])
    return results


@observe(name="orchestrate_parallel")
def run_parallel(doc_id: str, max_retries: int = 1,
                  routing: bool = ROUTING_ENABLED_BY_DEFAULT) -> Dict[RiskDimension, DimensionResult]:
    """Same specialists, run concurrently (I/O-bound OpenAI calls, so threads
    are sufficient — no multiprocessing needed). Added only after
    run_sequential() was validated correct, per the roadmap's ordering.
    Honors conditional routing."""
    plan = route_dimensions(doc_id, routing)
    selected = [d for d in _ALL_DIMENSIONS if d in set(plan["dimensions"])]
    results: Dict[RiskDimension, DimensionResult] = {
        d: _skipped_result(d) for d in _ALL_DIMENSIONS if d not in selected
    }
    with ThreadPoolExecutor(max_workers=max(1, len(selected))) as executor:
        future_to_dimension = {
            executor.submit(_run_with_retries, dimension, doc_id, max_retries): dimension
            for dimension in selected
        }
        for future in as_completed(future_to_dimension):
            dimension = future_to_dimension[future]
            results[dimension] = future.result()
    for dimension in _ALL_DIMENSIONS:
        _SAVERS[dimension](doc_id, results[dimension])
    return results


def _numeric_severity(severity: Severity) -> int | None:
    return RISK_SCORE_MAP.get(severity.value)


def _dedupe_findings(findings: List[Finding]) -> List[Finding]:
    """Removes only genuinely equivalent findings: same dimension, same
    title (case-insensitive), AND at least one shared evidence chunk id.
    Findings that merely share a title but cite different evidence are
    kept — that's a disagreement worth preserving, not a duplicate."""
    kept: List[Finding] = []
    for finding in findings:
        is_duplicate = any(
            existing.dimension == finding.dimension
            and existing.title.strip().casefold() == finding.title.strip().casefold()
            and set(existing.evidence_ids) & set(finding.evidence_ids)
            for existing in kept
        )
        if not is_duplicate:
            kept.append(finding)
    return kept


def build_consensus(doc_id: str, dimension_results: Dict[RiskDimension, DimensionResult],
                     document_version: str = "1") -> Assessment:
    """Merges the three specialists' findings into one Assessment. Overall
    risk is a weighted average of each dimension's worst scorable finding
    (RISK_WEIGHTS, renormalized over dimensions that actually produced a
    scorable finding) — EXCEPT a Severity.CRITICAL finding anywhere always
    forces overall_risk to CRITICAL; it is never averaged away."""
    all_findings: List[Finding] = []
    unresolved_issues: List[str] = []
    weighted_sum = 0.0
    weight_total = 0.0
    any_critical = False

    for dimension, result in dimension_results.items():
        all_findings.extend(result.findings)
        if not result.success:
            unresolved_issues.append(
                f"{dimension.value}: analysis did not succeed after "
                f"{result.retry_count + 1} attempt(s) — {result.error}"
            )
        if any(f.severity == Severity.CRITICAL for f in result.findings):
            any_critical = True

        scorable = [score for f in result.findings if (score := _numeric_severity(f.severity)) is not None]
        if scorable:
            weight = RISK_WEIGHTS.get(dimension.value, 0.0)
            weighted_sum += weight * max(scorable)
            weight_total += weight

    all_findings = _dedupe_findings(all_findings)

    # Risk-triggered human-in-the-loop: a finding is escalated for review when
    # the stakes or the uncertainty warrant it, not on a fixed schedule.
    for f in all_findings:
        if f.verification_status == VerificationStatus.FAILED_VERIFICATION:
            unresolved_issues.append(
                f"HITL [{f.dimension.value}] '{f.title}': quoted evidence could not be "
                f"verified against source text — needs human confirmation before use."
            )
        elif f.confidence <= HITL_CONFIDENCE_THRESHOLD:
            unresolved_issues.append(
                f"HITL [{f.dimension.value}] '{f.title}': low confidence "
                f"({f.confidence}) — flagged for human review."
            )
        elif f.severity == Severity.CRITICAL:
            unresolved_issues.append(
                f"HITL [{f.dimension.value}] '{f.title}': CRITICAL severity — "
                f"mandatory human sign-off before action."
            )

    if any_critical:
        overall_risk = Severity.CRITICAL
    elif weight_total > 0:
        avg_score = weighted_sum / weight_total
        overall_risk = min(
            (Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL),
            key=lambda s: abs(RISK_SCORE_MAP[s.value] - avg_score),
        )
    else:
        overall_risk = Severity.INSUFFICIENT_EVIDENCE

    consensus_actions = [
        f"Review: [{f.dimension.value}] {f.title}"
        for f in sorted(all_findings, key=lambda f: RISK_SCORE_MAP.get(f.severity.value, 0), reverse=True)
        if f.severity in (Severity.HIGH, Severity.CRITICAL)
    ]

    models_used = ",".join(sorted({LEGAL_AGENT_MODEL, FINANCIAL_AGENT_MODEL, OPERATIONAL_AGENT_MODEL}))

    return Assessment(
        assessment_id=f"assessment-{doc_id}-{uuid.uuid4().hex[:8]}",
        doc_id=doc_id,
        run_id=uuid.uuid4().hex[:12],
        document_version=document_version,
        model_version=models_used,
        prompt_version="phase5-specialist-prompts-v1",
        policy_version="risk-policy-v1",
        dimension_results=list(dimension_results.values()),
        unresolved_issues=unresolved_issues,
        consensus_actions=consensus_actions,
        overall_risk=overall_risk,
    )


def save_assessment(assessment: Assessment) -> Path:
    out_path = REPORTS_ROOT / f"phase5_assessment_{assessment.doc_id}.json"
    out_path.write_text(assessment.model_dump_json(indent=2), encoding="utf-8")
    return out_path


def run_phase5_sample(doc_ids: List[str], parallel: bool = True, max_retries: int = 1) -> Dict[str, Assessment]:
    """Runs the full three-specialist pipeline + consensus for a set of
    doc_ids, saves each Assessment, and prints a one-line summary per doc."""
    runner = run_parallel if parallel else run_sequential
    assessments: Dict[str, Assessment] = {}
    for doc_id in doc_ids:
        dimension_results = runner(doc_id, max_retries)
        assessment = build_consensus(doc_id, dimension_results)
        save_assessment(assessment)
        assessments[doc_id] = assessment

        total_findings = sum(len(r.findings) for r in dimension_results.values())
        print(f"{doc_id}: overall_risk={assessment.overall_risk.value}, "
              f"{total_findings} finding(s) across 3 dimensions, "
              f"{len(assessment.unresolved_issues)} unresolved issue(s), "
              f"{len(assessment.consensus_actions)} consensus action(s)")
    return assessments
