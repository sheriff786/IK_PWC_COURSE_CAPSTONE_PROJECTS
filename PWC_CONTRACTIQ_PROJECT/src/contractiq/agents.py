"""
ContractIQ — Phase 4: Legal Risk Agent — first evidence-grounded specialist agent.

Roadmap reference: 04_Legal_Risk_Agent.ipynb
Financial and Operational specialist agents (and Phase 5's parallel
orchestration/consensus) are a separate follow-on, not built here.

Guiding rule carried over from every earlier phase: a finding is only as
good as the evidence it cites. This agent never lets the LLM invent a
clause — every Finding's quoted excerpt is independently re-checked
against the actual chunk text retrieved from ChromaDB (Phase 3's index)
before being marked VERIFIED. A finding whose quote doesn't genuinely
appear in the cited chunk is downgraded to FAILED_VERIFICATION and its
confidence is capped, never silently kept as if it were trustworthy.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from .config import LEGAL_AGENT_MODEL, OPENAI_API_KEY, REPORTS_ROOT
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


_SYSTEM_PROMPT = (
    "You are a contract legal-risk analyst. You will be given one legal topic and a "
    "set of retrieved evidence chunks (each labeled with a chunk_id) from a SINGLE "
    "contract. Decide whether the evidence actually addresses the topic for THIS "
    "contract. If it does not, set addressed=false and leave finding null — never "
    "invent a finding from general legal knowledge or from what a typical contract "
    "usually says. If it does, produce exactly one finding grounded ONLY in the "
    "provided evidence: quoted_excerpt must be copied verbatim (not paraphrased) "
    "from the evidence text, and cited_chunk_ids must reference the chunk_id(s) the "
    "quote came from."
)


@observe(name="legal_agent_analyze_topic")
def _analyze_topic(doc_id: str, topic_key: str, question: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
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
        model=LEGAL_AGENT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=_LLMTopicResponse,
        temperature=0,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None or not parsed.addressed or parsed.finding is None:
        return None

    return {"llm_finding": parsed.finding, "evidence_by_id": {e["chunk_id"]: e for e in evidence}}


def _verify_and_build_finding(topic_key: str, raw: Dict[str, Any]) -> Finding:
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
        finding_id=f"legal-{topic_key}-{uuid.uuid4().hex[:8]}",
        dimension=RiskDimension.LEGAL,
        severity=llm_finding.severity,
        title=llm_finding.title,
        rationale=llm_finding.rationale,
        recommendation=llm_finding.recommendation,
        evidence_ids=evidence_ids,
        evidence_excerpts=[llm_finding.quoted_excerpt] if llm_finding.quoted_excerpt else [],
        verification_status=status,
        confidence=confidence,
    )


@observe(name="legal_risk_agent_analyze")
def analyze_legal_risk(doc_id: str, topics: Optional[Dict[str, str]] = None) -> DimensionResult:
    """Runs every legal-risk topic against one contract's indexed chunks and
    returns a DimensionResult — a finding only for topics the evidence
    actually supports, each independently verified against its source text."""
    topics = topics or LEGAL_RISK_TOPICS
    findings: List[Finding] = []

    try:
        for topic_key, question in topics.items():
            raw = _analyze_topic(doc_id, topic_key, question)
            if raw is not None:
                findings.append(_verify_and_build_finding(topic_key, raw))
    except Exception as exc:  # noqa: BLE001 - one bad topic must not silently drop the whole run
        return DimensionResult(dimension=RiskDimension.LEGAL, success=False,
                                findings=findings, error=str(exc))

    return DimensionResult(dimension=RiskDimension.LEGAL, success=True, findings=findings)


def save_legal_assessment(doc_id: str, result: DimensionResult) -> Path:
    out_path = REPORTS_ROOT / f"phase4_legal_risk_{doc_id}.json"
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return out_path


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
