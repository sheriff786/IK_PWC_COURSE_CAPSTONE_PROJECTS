"""
ContractIQ — Phase 7: evaluation set, metrics, and Langfuse scoring.

Roadmap reference: 07_Evaluation_and_Observability.ipynb
Every function here aggregates metrics from artifacts ALREADY produced and
already verified by earlier phases (Phase 3's retrieval eval, Phase 2's
human-reviewed entity fixture, Phase 4/5's saved findings/assessments,
Phase 7's own per-call instrumentation log) — it does not re-run
specialists, re-embed anything, or invent ground truth that was never
actually reviewed.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from .config import EVALUATIONS_ROOT, REPORTS_ROOT
from .ingestion import load_manifest
from .models import DocumentRecord, ParseStatus
from .parsing import load_parsed_document

_LLM_CALL_LOG = REPORTS_ROOT / "phase7_llm_calls.jsonl"


def parse_success_rate(manifest: Optional[List[DocumentRecord]] = None) -> Dict[str, Any]:
    """Checks the REAL per-document parse output (artifacts/parsed_documents/),
    not the manifest's own parse_status field — that field is a Phase 0 scan
    snapshot ('pending') that is never updated after Phase 1 actually parses
    each document, so it would silently under-report this metric as 0%."""
    manifest = manifest if manifest is not None else load_manifest()
    total = len(manifest)
    parsed = 0
    for record in manifest:
        try:
            result = load_parsed_document(record.doc_id)
        except FileNotFoundError:
            continue
        if result.get("parse_status") == "parsed":
            parsed += 1
    return {"metric": "parse_success_rate", "parsed": parsed, "total": total,
            "rate": round(parsed / total, 3) if total else None}


def entity_accuracy(fixture_path: Optional[Path] = None) -> Dict[str, Any]:
    """Reads the HUMAN-reviewed Phase 2 fixture. Reports a null rate with an
    explicit note if the fixture hasn't actually been reviewed yet — never
    computes a number from unfilled (null) reviewer_verdict rows."""
    fixture_path = fixture_path or (EVALUATIONS_ROOT / "phase2_extraction_fixture.json")
    if not fixture_path.exists():
        return {"metric": "entity_accuracy", "reviewed": 0, "total": 0, "rate": None,
                "note": "fixture not found"}
    rows = json.loads(fixture_path.read_text(encoding="utf-8"))
    reviewed = [r for r in rows if r.get("reviewer_verdict") is not None]
    if not reviewed:
        return {"metric": "entity_accuracy", "reviewed": 0, "total": len(rows), "rate": None,
                "note": "fixture exists but has not been human-reviewed — fill reviewer_verdict first"}
    correct = sum(1 for r in reviewed if r["reviewer_verdict"] == "correct")
    return {"metric": "entity_accuracy", "reviewed": len(reviewed), "total": len(rows),
            "correct": correct, "rate": round(correct / len(reviewed), 3)}


def retrieval_relevance(eval_report_path: Optional[Path] = None) -> Dict[str, Any]:
    eval_report_path = eval_report_path or (REPORTS_ROOT / "phase3_retrieval_eval.json")
    if not eval_report_path.exists():
        return {"metric": "retrieval_relevance", "rate": None, "note": "phase3 eval report not found"}
    report = json.loads(eval_report_path.read_text(encoding="utf-8"))
    return {"metric": "retrieval_relevance", "evaluated": report["evaluated"],
            "top_k": report["top_k"], "rate": report["recall_at_k"]}


def _load_assessments() -> List[Dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(REPORTS_ROOT.glob("phase5_assessment_*.json"))]


def citation_validity_and_finding_support() -> Dict[str, Any]:
    """Across every saved Assessment's dimension_results: what fraction of
    findings are VERIFIED. This IS the citation-validity signal (code-checked
    against source text), used instead of the model's own confidence."""
    assessments = _load_assessments()
    total = verified = failed = unverified = 0
    for a in assessments:
        for dim_result in a["dimension_results"]:
            for f in dim_result["findings"]:
                total += 1
                status = f["verification_status"]
                if status == "verified":
                    verified += 1
                elif status == "failed_verification":
                    failed += 1
                else:
                    unverified += 1
    return {
        "metric": "citation_validity_and_finding_support",
        "documents": len(assessments), "total_findings": total,
        "verified": verified, "failed_verification": failed, "unverified": unverified,
        "citation_validity_rate": round(verified / total, 3) if total else None,
    }


def partial_run_frequency() -> Dict[str, Any]:
    """Fraction of (document, dimension) runs that did NOT succeed cleanly
    on the first attempt, across every saved Assessment — real
    retry_count/success data from Phase 5's orchestrator, not simulated."""
    assessments = _load_assessments()
    total_runs = partial = 0
    for a in assessments:
        for dim_result in a["dimension_results"]:
            total_runs += 1
            if not dim_result["success"] or dim_result.get("retry_count", 0) > 0:
                partial += 1
    return {"metric": "partial_run_frequency", "total_runs": total_runs, "partial_runs": partial,
            "rate": round(partial / total_runs, 3) if total_runs else None}


def _read_llm_call_log() -> List[Dict[str, Any]]:
    if not _LLM_CALL_LOG.exists():
        return []
    return [json.loads(line) for line in _LLM_CALL_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def schema_failure_rate() -> Dict[str, Any]:
    """Reads the real per-call log written by agents.py/retrieval.py as
    calls actually happen (schema_failure=True only when the call SUCCEEDED
    but structured-output parsing failed) — not estimated after the fact."""
    records = _read_llm_call_log()
    if not records:
        return {"metric": "schema_failure_rate", "total_calls": 0, "schema_failures": 0, "rate": None,
                "note": "no LLM calls logged yet — run specialists/embeddings at least once"}
    failures = sum(1 for r in records if r.get("schema_failure"))
    return {"metric": "schema_failure_rate", "total_calls": len(records), "schema_failures": failures,
            "rate": round(failures / len(records), 4)}


def api_call_failure_rate() -> Dict[str, Any]:
    """Separate from schema_failure_rate: counts calls that raised an
    exception before returning (network/billing/rate-limit errors), e.g.
    OpenAI quota exhaustion — a real operational signal, not a model
    quality issue."""
    records = _read_llm_call_log()
    if not records:
        return {"metric": "api_call_failure_rate", "total_calls": 0, "api_failures": 0, "rate": None,
                "note": "no LLM calls logged yet"}
    failures = [r for r in records if r.get("error")]
    return {"metric": "api_call_failure_rate", "total_calls": len(records), "api_failures": len(failures),
            "rate": round(len(failures) / len(records), 4),
            "sample_errors": [r["error"] for r in failures[:3]]}


def cost_and_latency_by_stage() -> Dict[str, Any]:
    """Real latency/token numbers from the same log, grouped by stage
    (embedding / legal_specialist / financial_specialist / operational_specialist)."""
    records = _read_llm_call_log()
    if not records:
        return {"metric": "cost_and_latency_by_stage", "stages": {}, "note": "no LLM calls logged yet"}

    by_stage: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        by_stage.setdefault(r["stage"], []).append(r)

    stages = {}
    for stage, recs in by_stage.items():
        latencies = [r["latency_ms"] for r in recs]
        tokens = [r["total_tokens"] for r in recs if r.get("total_tokens") is not None]
        stages[stage] = {
            "calls": len(recs),
            "avg_latency_ms": round(mean(latencies), 1) if latencies else None,
            "total_tokens": sum(tokens) if tokens else None,
            "avg_tokens_per_call": round(mean(tokens), 1) if tokens else None,
        }
    return {"metric": "cost_and_latency_by_stage", "stages": stages}


def important_missed_risk_rate() -> Dict[str, Any]:
    """HONEST limitation, reported rather than fabricated: measuring this
    properly needs a hand-authored 'expected risks per document' checklist
    — the same kind of manually source-verified ground truth Phase 3 built
    for retrieval — which does not exist yet for the specialist agents."""
    return {
        "metric": "important_missed_risk_rate", "rate": None,
        "note": ("Not independently measurable without a hand-reviewed expected-risk "
                 "checklist per document (not yet built for Legal/Financial/Operational "
                 "the way Phase 3 built one for retrieval). One concretely documented gap "
                 "exists: Phase 3's confidentiality-definition retrieval miss would "
                 "propagate to the Legal agent for any topic relying on that chunk."),
    }


def build_evaluation_report(manifest: Optional[List[DocumentRecord]] = None) -> Dict[str, Any]:
    """Assembles every metric above into one frozen, versioned report —
    the roadmap's 'measure parse success, entity accuracy, retrieval
    relevance, citation validity, finding support, missed-risk rate,
    schema failures, partial-run frequency' in one place."""
    report = {
        "parse_success": parse_success_rate(manifest),
        "entity_accuracy": entity_accuracy(),
        "retrieval_relevance": retrieval_relevance(),
        "citation_validity_and_finding_support": citation_validity_and_finding_support(),
        "partial_run_frequency": partial_run_frequency(),
        "schema_failure_rate": schema_failure_rate(),
        "api_call_failure_rate": api_call_failure_rate(),
        "cost_and_latency_by_stage": cost_and_latency_by_stage(),
        "important_missed_risk_rate": important_missed_risk_rate(),
    }
    out_path = REPORTS_ROOT / "phase7_evaluation_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Evaluation report saved to: {out_path}")
    return report
