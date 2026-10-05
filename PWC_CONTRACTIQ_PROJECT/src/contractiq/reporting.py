"""
ContractIQ — Phase 7: evidence-linked, versioned report generation.

Roadmap reference: 07_Evaluation_and_Observability.ipynb
Builds one human-readable report per document from the already-saved,
already-verified Phase 5 Assessment — it does not re-run any specialist or
add new findings. Every finding keeps its evidence_ids/verification_status;
every report carries document/model/prompt/policy version + run_id.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import REPORTS_ROOT

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INSUFFICIENT_EVIDENCE": 4}


def load_assessment(doc_id: str) -> Dict[str, Any]:
    path = REPORTS_ROOT / f"phase5_assessment_{doc_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No Phase 5 assessment found for {doc_id} at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _render_finding(f: Dict[str, Any]) -> str:
    status = f["verification_status"]
    uncertainty = "" if status == "verified" else f"  ⚠ uncertainty: {status}"
    excerpt = f["evidence_excerpts"][0] if f["evidence_excerpts"] else "(no excerpt)"
    lines = [
        f"- **[{f['severity']}] {f['title']}** (confidence={f['confidence']}){uncertainty}",
        f"  - rationale: {f['rationale']}",
        f"  - evidence: `{f['evidence_ids']}` — \"{excerpt[:200]}{'...' if len(excerpt) > 200 else ''}\"",
    ]
    if f.get("recommendation"):
        lines.append(f"  - recommendation: {f['recommendation']}")
    return "\n".join(lines)


def generate_document_report(doc_id: str) -> str:
    """Builds one Markdown report: overall risk, per-dimension status,
    every finding with its evidence and uncertainty flag, unresolved
    issues, consensus actions, and version/date metadata — all pulled
    from the real saved Assessment, nothing re-derived or invented here."""
    a = load_assessment(doc_id)

    lines: List[str] = [
        f"# ContractIQ Risk Report — {doc_id}",
        "",
        f"**Overall risk:** {a['overall_risk']}  ",
        f"**Assessment ID:** {a['assessment_id']}  ",
        f"**Run ID:** {a['run_id']}  ",
        f"**Document version:** {a['document_version']}  ",
        f"**Model version:** {a['model_version']}  ",
        f"**Prompt version:** {a['prompt_version']}  ",
        f"**Policy version:** {a['policy_version']}  ",
        f"**Created at:** {a['created_at']}  ",
        f"**Report generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Specialist statuses",
    ]
    for dim_result in a["dimension_results"]:
        status = "OK" if dim_result["success"] else f"FAILED ({dim_result.get('error')})"
        lines.append(f"- **{dim_result['dimension']}**: {status}, "
                     f"{len(dim_result['findings'])} finding(s), retry_count={dim_result.get('retry_count', 0)}")

    lines.append("")
    lines.append("## Findings (by severity)")
    all_findings = [f for dim_result in a["dimension_results"] for f in dim_result["findings"]]
    all_findings.sort(key=lambda f: _SEVERITY_ORDER.get(f["severity"], 99))
    if not all_findings:
        lines.append("_No findings produced by any specialist for this document._")
    for f in all_findings:
        lines.append(_render_finding(f))

    lines.append("")
    lines.append("## Uncertainty / unresolved issues")
    if a["unresolved_issues"]:
        lines.extend(f"- {issue}" for issue in a["unresolved_issues"])
    else:
        lines.append("_None reported._")

    lines.append("")
    lines.append("## Recommendations (consensus actions)")
    if a["consensus_actions"]:
        lines.extend(f"- {action}" for action in a["consensus_actions"])
    else:
        lines.append("_None — no HIGH/CRITICAL findings to flag._")

    return "\n".join(lines)


def save_document_report(doc_id: str) -> Path:
    report_text = generate_document_report(doc_id)
    out_path = REPORTS_ROOT / f"phase7_report_{doc_id}.md"
    out_path.write_text(report_text, encoding="utf-8")
    return out_path


def generate_all_reports(doc_ids: Optional[List[str]] = None) -> List[Path]:
    """Builds a report for every doc_id that has a saved Phase 5 Assessment
    (or the given subset), skipping and reporting (not hiding) any doc_id
    that doesn't have one yet."""
    if doc_ids is None:
        doc_ids = sorted(p.stem.replace("phase5_assessment_", "")
                          for p in REPORTS_ROOT.glob("phase5_assessment_*.json"))
    saved: List[Path] = []
    skipped: List[str] = []
    for doc_id in doc_ids:
        try:
            saved.append(save_document_report(doc_id))
        except FileNotFoundError:
            skipped.append(doc_id)
    print(f"Generated {len(saved)} report(s).")
    if skipped:
        print(f"Skipped {len(skipped)} doc_id(s) with no saved Assessment: {skipped}")
    return saved
