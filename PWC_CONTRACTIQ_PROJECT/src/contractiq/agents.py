"""
ContractIQ — Phase 4/5: evidence-grounded specialist agents (Legal, Financial,
Operational).

Roadmap reference: 04_Legal_Risk_Agent.ipynb, 05_Multi_Agent_Orchestration.ipynb
All three specialists share one evidence-retrieval + LLM + verification
engine (_analyze_topic / _verify_and_build_finding / analyze_dimension) —
only the topic list, model, and system prompt differ per dimension. Phase 5's
parallel orchestration/consensus lives in orchestration.py, not here.

Guiding rule carried over from every earlier phase: a finding is only as
good as the evidence it cites. No agent lets the LLM invent a clause —
every Finding's quoted excerpt is independently re-checked against the
actual chunk text retrieved from ChromaDB (Phase 3's index) before being
marked VERIFIED. A finding whose quote doesn't genuinely appear in the
cited chunk is downgraded to FAILED_VERIFICATION and its confidence is
capped, never silently kept as if it were trustworthy.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from .config import FINANCIAL_AGENT_MODEL, LEGAL_AGENT_MODEL, OPENAI_API_KEY, OPERATIONAL_AGENT_MODEL, REPORTS_ROOT
from .models import DimensionResult, Finding, RiskDimension, Severity, VerificationStatus
from .retrieval import search

try:
    from langfuse.decorators import observe
except ImportError:  # Langfuse not configured — tracing becomes a no-op, not a crash
    def observe(*_args, **_kwargs):
        def decorator(fn):
            return fn
        return decorator


_openai_client: Optional[OpenAI] = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


# ---------------------------------------------------------------------------
# The specific legal topics this agent probes for in every contract. Each
# maps to a concrete retrieval query — the same "ask a real question, then
# read the real excerpt" approach Phase 3 used to build its test set,
# applied here at analysis time instead of evaluation time.
# ---------------------------------------------------------------------------

LEGAL_RISK_TOPICS: Dict[str, str] = {
    "liability_cap": "Is there a cap or limitation on total liability under this agreement?",
    "indemnification": "What indemnification obligations does each party have under this agreement?",
    "termination_for_cause": "Under what conditions can this agreement be terminated for cause or material breach?",
    "termination_for_convenience": "What notice period or terms apply to termination without cause?",
    "confidentiality_survival": "How long do confidentiality obligations survive after this agreement ends?",
    "ip_ownership": "Who owns intellectual property or work product created under this agreement?",
    "governing_law_disputes": "What governing law applies and how are disputes resolved (arbitration, litigation, venue)?",
    "assignment_change_of_control": "Can this agreement be assigned, or what happens on a change of control?",
}

# Phase 5 — payment terms, financial exposure, penalties, pricing, escalation,
# renewal comparisons (roadmap Phase 5, item 1).
FINANCIAL_RISK_TOPICS: Dict[str, str] = {
    "payment_terms": "What are the payment terms, due dates, or payment schedule under this agreement?",
    "late_payment_penalties": "What late fees, interest, or penalties apply if payment is not made on time?",
    "pricing_structure": "What is the pricing structure, rate card, or fee schedule described in this agreement?",
    "price_escalation": "Are there price escalation, adjustment, or index-linked (e.g. CPI) clauses in this agreement?",
    "renewal_pricing": "What are the renewal terms, and how does renewal pricing compare to the original term?",
    "financial_exposure_cap": "Is there a cap on financial exposure, penalties, or total fees payable under this agreement?",
}

# Phase 5 — scope, deliverables, acceptance criteria, SLAs, dependencies,
# performance metrics, remedies (roadmap Phase 5, item 2).
OPERATIONAL_RISK_TOPICS: Dict[str, str] = {
    "scope_of_work": "What is the scope of work or deliverables under this agreement?",
    "acceptance_criteria": "What are the acceptance criteria for deliverables under this agreement?",
    "sla_commitments": "What service level or performance commitments does the vendor make under this agreement?",
    "sla_remedies": "What remedy or service credit applies if a service level target is missed?",
    "dependencies_obligations": "What dependencies or client-side obligations does the vendor rely on for performance?",
    "performance_reporting": "How is service performance measured or reported under this agreement?",
}

# Central registry: dimension -> (topics, model). Used by analyze_dimension()
# so the three thin wrappers (analyze_legal_risk/_financial_/_operational_)
# stay one-liners instead of duplicating the engine.
_DIMENSION_TOPICS: Dict[RiskDimension, Dict[str, str]] = {
    RiskDimension.LEGAL: LEGAL_RISK_TOPICS,
    RiskDimension.FINANCIAL: FINANCIAL_RISK_TOPICS,
    RiskDimension.OPERATIONAL: OPERATIONAL_RISK_TOPICS,
}
_DIMENSION_MODELS: Dict[RiskDimension, str] = {
    RiskDimension.LEGAL: LEGAL_AGENT_MODEL,
    RiskDimension.FINANCIAL: FINANCIAL_AGENT_MODEL,
    RiskDimension.OPERATIONAL: OPERATIONAL_AGENT_MODEL,
}


class _LLMFinding(BaseModel):
    """What we ask the LLM to produce for one topic — a subset of Finding's
    fields. severity/confidence/quote come from the model; everything else
    (finding_id, dimension, verification_status) is decided afterward by
    code that re-checks the model's claim, not by the model itself."""
    title: str
    rationale: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    recommendation: Optional[str] = None
    cited_chunk_ids: List[str] = Field(
        default_factory=list,
        description="chunk_id value(s) copied verbatim from the evidence block this finding is based on",
    )
    quoted_excerpt: Optional[str] = Field(
        default=None,
        description="A short verbatim quote (<= 300 chars) copied EXACTLY, character-for-character, "
                     "from the evidence text above — not paraphrased, not summarized",
    )


class _LLMTopicResponse(BaseModel):
    addressed: bool = Field(
        description="False if the retrieved evidence does not actually discuss this topic for this contract"
    )
    finding: Optional[_LLMFinding] = None


def _system_prompt(dimension: RiskDimension) -> str:
    """One prompt per dimension, same discipline every time: ground strictly
    in retrieved evidence for THIS contract, never invent from general
    knowledge of what a typical contract says."""
    role = {
        RiskDimension.LEGAL: "contract legal-risk analyst",
        RiskDimension.FINANCIAL: "contract financial-risk analyst",
        RiskDimension.OPERATIONAL: "contract operational-risk analyst",
    }[dimension]
    topic_word = {
        RiskDimension.LEGAL: "legal",
        RiskDimension.FINANCIAL: "financial",
        RiskDimension.OPERATIONAL: "operational",
    }[dimension]
    return (
        f"You are a {role}. You will be given one {topic_word} topic and a "
        "set of retrieved evidence chunks (each labeled with a chunk_id) from a SINGLE "
        "contract. Decide whether the evidence actually addresses the topic for THIS "
        f"contract. If it does not, set addressed=false and leave finding null — never "
        f"invent a finding from general {topic_word} knowledge or from what a typical "
        "contract usually says. If it does, produce exactly one finding grounded ONLY in "
        "the provided evidence: quoted_excerpt must be copied verbatim (not paraphrased) "
        "from the evidence text, and cited_chunk_ids must reference the chunk_id(s) the "
        "quote came from."
    )


@observe(name="specialist_agent_analyze_topic")
def _analyze_topic(doc_id: str, topic_key: str, question: str, dimension: RiskDimension,
                    model: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
    """Retrieves evidence for one topic scoped to this doc_id only (so the
    agent can never accidentally cite a different contract), then asks the
    LLM to ground a single finding in it, or say the topic isn't addressed."""
    evidence = search(question, top_k=top_k, doc_id=doc_id)
    if not evidence:
        return None

    evidence_block = "\n\n".join(
        f"[chunk_id={e['chunk_id']} @ {e['source_location_range']}]\n{e['text']}"
        for e in evidence
    )
    user_prompt = f"Topic: {topic_key}\nQuestion: {question}\n\nEvidence:\n{evidence_block}"

    client = _get_openai_client()
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": _system_prompt(dimension)},
            {"role": "user", "content": user_prompt},
        ],
        response_format=_LLMTopicResponse,
        temperature=0,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None or not parsed.addressed or parsed.finding is None:
        return None

    return {"llm_finding": parsed.finding, "evidence_by_id": {e["chunk_id"]: e for e in evidence}}


def _verify_and_build_finding(topic_key: str, raw: Dict[str, Any], dimension: RiskDimension) -> Finding:
    """Re-checks the LLM's quoted_excerpt against the ACTUAL retrieved chunk
    text before trusting it — the step that stops a plausible-sounding but
    fabricated quote from ever being marked verified.

    Verification searches every chunk that was actually shown to the model
    for this topic (not just the chunk_id(s) it claimed), because the model
    sometimes quotes real text but mislabels which chunk_id it came from —
    that's a citation-labeling error, not fabrication, and evidence_ids is
    corrected to the chunk(s) where the quote genuinely appears. A quote
    that appears in none of the evidence is fabrication and is still
    flagged FAILED_VERIFICATION."""
    llm_finding: _LLMFinding = raw["llm_finding"]
    evidence_by_id: Dict[str, Dict[str, Any]] = raw["evidence_by_id"]

    # case/whitespace-insensitive containment: models lowercase the first word of a
    # quote taken mid-sentence, and collapse the "\n" that joins separate clauses
    # inside a chunk into a plain space when quoting across a clause boundary —
    # neither is fabrication, so they must not trip FAILED_VERIFICATION. Wording
    # and punctuation otherwise still has to match exactly.
    def _normalize(text: str) -> str:
        return " ".join(text.split()).casefold()

    found_in_ids = [cid for cid, chunk in evidence_by_id.items()
                    if llm_finding.quoted_excerpt
                    and _normalize(llm_finding.quoted_excerpt) in _normalize(chunk["text"])]

    status = VerificationStatus.UNVERIFIED
    confidence = llm_finding.confidence
    evidence_ids = llm_finding.cited_chunk_ids

    if llm_finding.quoted_excerpt:
        if found_in_ids:
            status = VerificationStatus.VERIFIED
            evidence_ids = found_in_ids  # use the chunk(s) actually containing the quote
        else:
            status = VerificationStatus.FAILED_VERIFICATION
            confidence = min(confidence, 0.3)  # a failed quote can't support high confidence

    return Finding(
        finding_id=f"{dimension.value}-{topic_key}-{uuid.uuid4().hex[:8]}",
        dimension=dimension,
        severity=llm_finding.severity,
        title=llm_finding.title,
        rationale=llm_finding.rationale,
        recommendation=llm_finding.recommendation,
        evidence_ids=evidence_ids,
        evidence_excerpts=[llm_finding.quoted_excerpt] if llm_finding.quoted_excerpt else [],
        verification_status=status,
        confidence=confidence,
    )


@observe(name="specialist_agent_analyze")
def analyze_dimension(doc_id: str, dimension: RiskDimension,
                       topics: Optional[Dict[str, str]] = None,
                       model: Optional[str] = None) -> DimensionResult:
    """Runs every topic for one dimension against one contract's indexed
    chunks and returns a DimensionResult — a finding only for topics the
    evidence actually supports, each independently verified against its
    source text. The shared engine behind all three specialists."""
    topics = topics or _DIMENSION_TOPICS[dimension]
    model = model or _DIMENSION_MODELS[dimension]
    findings: List[Finding] = []

    try:
        for topic_key, question in topics.items():
            raw = _analyze_topic(doc_id, topic_key, question, dimension, model)
            if raw is not None:
                findings.append(_verify_and_build_finding(topic_key, raw, dimension))
    except Exception as exc:  # noqa: BLE001 - one bad topic must not silently drop the whole run
        return DimensionResult(dimension=dimension, success=False,
                                findings=findings, error=str(exc))

    return DimensionResult(dimension=dimension, success=True, findings=findings)


def analyze_legal_risk(doc_id: str, topics: Optional[Dict[str, str]] = None) -> DimensionResult:
    """Phase 4 legal specialist — 8 fixed legal-risk topics."""
    return analyze_dimension(doc_id, RiskDimension.LEGAL, topics, LEGAL_AGENT_MODEL)


def analyze_financial_risk(doc_id: str, topics: Optional[Dict[str, str]] = None) -> DimensionResult:
    """Phase 5 financial specialist — payment/pricing/penalty/renewal topics."""
    return analyze_dimension(doc_id, RiskDimension.FINANCIAL, topics, FINANCIAL_AGENT_MODEL)


def analyze_operational_risk(doc_id: str, topics: Optional[Dict[str, str]] = None) -> DimensionResult:
    """Phase 5 operational specialist — scope/SLA/dependency/reporting topics."""
    return analyze_dimension(doc_id, RiskDimension.OPERATIONAL, topics, OPERATIONAL_AGENT_MODEL)


def _save_assessment(doc_id: str, filename_prefix: str, result: DimensionResult) -> Path:
    out_path = REPORTS_ROOT / f"{filename_prefix}_{doc_id}.json"
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return out_path


def save_legal_assessment(doc_id: str, result: DimensionResult) -> Path:
    return _save_assessment(doc_id, "phase4_legal_risk", result)


def save_financial_assessment(doc_id: str, result: DimensionResult) -> Path:
    return _save_assessment(doc_id, "phase5_financial_risk", result)


def save_operational_assessment(doc_id: str, result: DimensionResult) -> Path:
    return _save_assessment(doc_id, "phase5_operational_risk", result)


def run_phase4_sample(doc_ids: List[str]) -> Dict[str, DimensionResult]:
    """Runs the legal agent over a small set of doc_ids — the same
    'sample first, then scale' pattern Phase 1 used — and saves each
    result so it can be reviewed before running the full corpus."""
    results: Dict[str, DimensionResult] = {}
    for doc_id in doc_ids:
        result = analyze_legal_risk(doc_id)
        results[doc_id] = result
        save_legal_assessment(doc_id, result)
        verified = sum(1 for f in result.findings if f.verification_status == VerificationStatus.VERIFIED)
        failed = sum(1 for f in result.findings if f.verification_status == VerificationStatus.FAILED_VERIFICATION)
        status_msg = f", error={result.error}" if result.error else ""
        print(f"{doc_id}: success={result.success}, {len(result.findings)} finding(s) "
              f"({verified} verified, {failed} failed_verification){status_msg}")
    return results


def run_phase4_batch(doc_ids: List[str], summary_filename: str = "phase4_legal_risk_summary.json") -> Dict[str, Any]:
    """Scales the legal agent to a larger, fixed set of doc_ids (e.g. the
    same 15 documents already source-verified for Phase 3's retrieval test
    set) and writes one aggregate summary JSON alongside the existing
    per-doc reports, so results across documents/doc-types can be compared
    without opening 15 separate report files."""
    per_doc_summaries: List[Dict[str, Any]] = []
    totals = {"total_findings": 0, "verified": 0, "failed_verification": 0, "unverified": 0}

    for doc_id in doc_ids:
        result = analyze_legal_risk(doc_id)
        save_legal_assessment(doc_id, result)

        # finding_id is "legal-{topic_key}-{hex8}"; topic keys are underscore-only
        # (never hyphenated), so this split is unambiguous.
        topics_found = sorted({f.finding_id.split("-")[1] for f in result.findings})
        topics_not_addressed = sorted(set(LEGAL_RISK_TOPICS) - set(topics_found))

        verified = sum(1 for f in result.findings if f.verification_status == VerificationStatus.VERIFIED)
        failed = sum(1 for f in result.findings if f.verification_status == VerificationStatus.FAILED_VERIFICATION)
        unverified = sum(1 for f in result.findings if f.verification_status == VerificationStatus.UNVERIFIED)

        totals["total_findings"] += len(result.findings)
        totals["verified"] += verified
        totals["failed_verification"] += failed
        totals["unverified"] += unverified

        per_doc_summaries.append({
            "doc_id": doc_id,
            "success": result.success,
            "error": result.error,
            "total_findings": len(result.findings),
            "verified": verified,
            "failed_verification": failed,
            "unverified": unverified,
            "topics_found": topics_found,
            "topics_not_addressed": topics_not_addressed,
        })

        status_msg = f", error={result.error}" if result.error else ""
        print(f"{doc_id}: success={result.success}, {len(result.findings)} finding(s) "
              f"({verified} verified, {failed} failed_verification){status_msg}")

    summary = {
        "doc_count": len(doc_ids),
        "topics_probed": list(LEGAL_RISK_TOPICS),
        "totals": totals,
        "per_doc": per_doc_summaries,
    }
    out_path = REPORTS_ROOT / summary_filename
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary saved to: {out_path}")
    return summary
