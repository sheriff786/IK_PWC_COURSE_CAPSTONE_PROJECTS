"""
ContractIQ — Phase 8: service facade the Gradio (and later FastAPI) layer
calls. Every function here wraps ALREADY-BUILT, ALREADY-VERIFIED code from
Phases 0-7 — it does not re-implement risk analysis, retrieval, or the
knowledge graph. The one genuinely new piece is the lightweight Review
Tasks store: no earlier phase produced that, so it's a real (not fake)
local JSON-backed CRUD store, not a stub.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .chat import answer_question
from .config import ARTIFACTS_ROOT, DATA_ROOT, REPORTS_ROOT
from .graph import ContractKnowledgeGraph
from .ingestion import load_manifest, save_manifest
from .models import DocumentRecord, DocumentRole, ParseStatus
from .parsing import load_parsed_document, parse_docx_document, save_parsed_document
from .reporting import generate_document_report, load_assessment
from .resilience import read_recovery_events
from .retrieval import (
    build_index,
    chunk_document,
    expand_locator_range,
    get_chroma_collection,
    normalize_for_match,
    search,
    search_passages,
)

_TASKS_PATH = ARTIFACTS_ROOT / "app_review_tasks.json"
_UPLOADS_ROOT = ARTIFACTS_ROOT / "uploads"
_UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INSUFFICIENT_EVIDENCE": 4}


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r[key]] = counts.get(r[key], 0) + 1
    return counts


def _assessed_risks() -> List[Dict[str, str]]:
    rows = []
    for p in sorted(REPORTS_ROOT.glob("phase5_assessment_*.json")):
        a = json.loads(p.read_text(encoding="utf-8"))
        rows.append({"doc_id": a["doc_id"], "overall_risk": a["overall_risk"]})
    return rows


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def get_overview() -> Dict[str, Any]:
    manifest = load_manifest()
    assessed = _assessed_risks()

    eval_path = REPORTS_ROOT / "phase7_evaluation_report.json"
    eval_report = json.loads(eval_path.read_text(encoding="utf-8")) if eval_path.exists() else {}

    kg = get_graph()

    return {
        "total_documents": len(manifest),
        "assessed_documents": len(assessed),
        "risk_distribution": _count_by(assessed, "overall_risk"),
        "graph_nodes": kg.graph.number_of_nodes(),
        "graph_edges": kg.graph.number_of_edges(),
        "citation_validity_rate": eval_report.get("citation_validity_and_finding_support", {}).get("citation_validity_rate"),
        "retrieval_relevance_rate": eval_report.get("retrieval_relevance", {}).get("rate"),
        "assessed_docs": assessed,
    }


# ---------------------------------------------------------------------------
# Contract Library
# ---------------------------------------------------------------------------

def list_documents() -> List[Dict[str, Any]]:
    manifest = load_manifest()
    risk_by_doc = {row["doc_id"]: row["overall_risk"] for row in _assessed_risks()}
    return [{
        "doc_id": r.doc_id, "filename": r.filename, "category_key": r.category_key,
        "document_role": r.document_role.value, "overall_risk": risk_by_doc.get(r.doc_id, "not assessed"),
    } for r in manifest]


# ---------------------------------------------------------------------------
# Risk Review (Phase 5 Assessments — reused, not rebuilt)
# ---------------------------------------------------------------------------

def list_assessed_doc_ids() -> List[str]:
    return sorted(p.stem.replace("phase5_assessment_", "") for p in REPORTS_ROOT.glob("phase5_assessment_*.json"))


def get_risk_review(doc_id: str) -> Dict[str, Any]:
    try:
        a = load_assessment(doc_id)
    except FileNotFoundError:
        return {"doc_id": doc_id, "available": False}
    all_findings = [f for d in a["dimension_results"] for f in d["findings"]]
    all_findings.sort(key=lambda f: _SEVERITY_ORDER.get(f["severity"], 99))
    return {
        "doc_id": doc_id, "available": True, "overall_risk": a["overall_risk"],
        "findings": all_findings, "unresolved_issues": a["unresolved_issues"],
        "consensus_actions": a["consensus_actions"], "dimension_results": a["dimension_results"],
    }


# ---------------------------------------------------------------------------
# Ask ContractIQ (Phase 3 retrieval — reused, not rebuilt)
# ---------------------------------------------------------------------------

def ask(query: str, doc_id: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """Chunk-level search. Kept for callers that want whole retrieved chunks;
    the chat agent uses passage-level search instead."""
    if not query or not query.strip():
        return []
    return search(query, top_k=top_k, doc_id=doc_id or None)


def ask_passages(query: str, doc_id: Optional[str] = None,
                  top_k: int = 5) -> List[Dict[str, Any]]:
    """Paragraph-level search — precise citations even for the 17 documents
    that are a single whole-file chunk."""
    if not query or not query.strip():
        return []
    return search_passages(query, top_k=top_k, doc_id=doc_id or None)


def chat(message: str, history: Optional[List[Dict[str, str]]] = None,
          doc_id: Optional[str] = None) -> Dict[str, Any]:
    """One conversational turn: resolves follow-ups against history, retrieves
    passages, answers only from them, and verifies every quote."""
    if not message or not message.strip():
        return {"status": "empty", "answer": "Ask a question to get started.",
                "passages": [], "citations": [], "unverified_quotes": []}
    return answer_question(message, history=history, doc_id=doc_id or None)


# ---------------------------------------------------------------------------
# Document Sources — one new facade method (listing chunks by doc_id),
# everything underneath it is Phase 3's real ChromaDB index.
# ---------------------------------------------------------------------------

def get_document_chunks(doc_id: str) -> List[Dict[str, Any]]:
    collection = get_chroma_collection()
    result = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    rows = [
        {"chunk_id": cid, "text": doc, "source_location_range": meta.get("source_location_range"),
         "chunk_index": meta.get("chunk_index"), "total_chunks": meta.get("total_chunks")}
        for cid, doc, meta in zip(result["ids"], result["documents"], result["metadatas"])
    ]
    rows.sort(key=lambda r: r.get("chunk_index") or 0)
    return rows


# ---------------------------------------------------------------------------
# Citation drill-down — resolve a finding's evidence back to the REAL
# paragraphs in the source document, not just a chunk id.
# ---------------------------------------------------------------------------

def _parse_locator_range(source_location_range: str) -> List[str]:
    """Kept as a thin alias so existing callers/tests keep working; the real
    implementation lives in retrieval.py next to the index that emits these
    ranges, so chat/agents/app_service all share one copy."""
    return expand_locator_range(source_location_range)


def resolve_citation(doc_id: str, chunk_id: str,
                      quoted_excerpt: Optional[str] = None) -> Dict[str, Any]:
    """Opens the actual parsed document and returns the real paragraphs the
    cited chunk covers — so a reviewer sees the clause in its own document,
    in context, rather than an opaque chunk id.

    Marks which paragraph physically contains the quote (`is_quote_source`),
    using the same case/whitespace-insensitive match the verification step
    uses, so UI highlighting agrees with the verification verdict."""
    collection = get_chroma_collection()
    got = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
    if not got["ids"]:
        return {"found": False, "reason": f"chunk {chunk_id} is not in the index"}

    meta = got["metadatas"][0] or {}
    location_range = meta.get("source_location_range", "")
    wanted = set(_parse_locator_range(location_range))

    try:
        parsed = load_parsed_document(doc_id)
    except FileNotFoundError:
        return {"found": False, "reason": f"no parsed artifact for {doc_id}"}

    def _norm(text: str) -> str:
        return normalize_for_match(text)

    needle = _norm(quoted_excerpt) if quoted_excerpt else None

    covered = [c for c in parsed["clauses"]
               if c["source_location"]["locator"] in wanted]

    # A quote frequently spans a paragraph boundary, because the chunk the
    # agent verified against joins paragraphs together. Checking paragraphs
    # one at a time would then find nothing and wrongly report a verified
    # finding as unlocatable, so the search runs over the joined text and
    # maps the match back to every paragraph it overlaps.
    quote_locators: set = set()
    if needle:
        normalized = [_norm(c["text"]) for c in covered]
        joined = " ".join(normalized)
        spans, cursor = [], 0
        for text in normalized:
            spans.append((cursor, cursor + len(text)))
            cursor += len(text) + 1  # +1 for the joining space

        start = joined.find(needle)
        if start >= 0:
            end = start + len(needle)
            for clause, (span_start, span_end) in zip(covered, spans):
                if span_start < end and span_end > start:
                    quote_locators.add(clause["source_location"]["locator"])

    paragraphs = [{
        "locator": c["source_location"]["locator"],
        "heading": c.get("heading"),
        "text": c["text"],
        "is_quote_source": c["source_location"]["locator"] in quote_locators,
    } for c in covered]

    return {
        "found": True,
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "source_location_range": location_range,
        "filename": next((r.filename for r in load_manifest() if r.doc_id == doc_id), doc_id),
        "paragraphs": paragraphs,
        "quote_located": any(p["is_quote_source"] for p in paragraphs),
    }


def resolve_finding_citations(doc_id: str, finding: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every evidence chunk behind one finding, resolved to real paragraphs."""
    excerpt = (finding.get("evidence_excerpts") or [None])[0]
    return [resolve_citation(doc_id, cid, excerpt) for cid in finding.get("evidence_ids", [])]


# ---------------------------------------------------------------------------
# Upload — the full real pipeline for a newly provided .docx:
# parse (Phase 1) -> chunk + index (Phase 3) -> optionally analyze (Phase 5).
# ---------------------------------------------------------------------------

def _next_upload_doc_id() -> str:
    existing = {r.doc_id for r in load_manifest()}
    n = 1
    while f"UPL-{n:03d}" in existing:
        n += 1
    return f"UPL-{n:03d}"


def upload_document(file_path: str, category_key: str = "master_agreements") -> Dict[str, Any]:
    """Ingests a user-provided .docx through the SAME Phase 1 parser and
    Phase 3 indexer the rest of the corpus went through — no separate
    'demo' path. Returns the real parse result so the reviewer can inspect
    clauses and source locations BEFORE deciding to analyze it."""
    src = Path(file_path)
    if src.suffix.lower() != ".docx":
        return {"success": False, "error": f"Only .docx is supported by the Phase 1 parser, got {src.suffix}"}

    doc_id = _next_upload_doc_id()
    stored = _UPLOADS_ROOT / f"{doc_id}{src.suffix}"
    stored.write_bytes(src.read_bytes())

    record = DocumentRecord(
        doc_id=doc_id,
        filename=src.name,
        filepath=str(stored),
        category_key=category_key,
        document_role=DocumentRole.ASSESSED_AGREEMENT,
        file_size_bytes=stored.stat().st_size,
        content_hash=hashlib.sha256(stored.read_bytes()).hexdigest(),
    )

    parsed = parse_docx_document(record)
    if parsed["parse_status"] != ParseStatus.PARSED:
        return {"success": False, "doc_id": doc_id, "error": parsed.get("parse_error"),
                "parse_status": str(parsed["parse_status"])}

    save_parsed_document(parsed)
    record.parse_status = ParseStatus.PARSED

    manifest = load_manifest()
    manifest.append(record)
    save_manifest(manifest)

    chunks = chunk_document(doc_id, category_key, parsed["clauses"])
    build_index(manifest, {doc_id: chunks})

    global _kg_cache
    _kg_cache = None  # manifest changed — rebuild the graph on next access

    return {
        "success": True,
        "doc_id": doc_id,
        "filename": src.name,
        "category_key": category_key,
        "clause_count": len(parsed["clauses"]),
        "table_count": len(parsed["tables"]),
        "chunk_count": len(chunks),
        "preview_clauses": [
            {"locator": c["source_location"]["locator"], "heading": c.get("heading"),
             "text": c["text"][:300]}
            for c in parsed["clauses"][:10]
        ],
    }


def analyze_uploaded_document(doc_id: str) -> Dict[str, Any]:
    """Runs the full Phase 5 pipeline (routing -> specialists -> consensus)
    on an already-uploaded, already-indexed document."""
    from .orchestration import build_consensus, run_parallel, save_assessment

    results = run_parallel(doc_id)
    assessment = build_consensus(doc_id, results)
    save_assessment(assessment)
    return {"doc_id": doc_id, "overall_risk": assessment.overall_risk.value,
            "finding_count": sum(len(r.findings) for r in results.values()),
            "unresolved_issues": assessment.unresolved_issues}


# ---------------------------------------------------------------------------
# Relationships (Phase 6 knowledge graph — reused, not rebuilt)
# ---------------------------------------------------------------------------

_kg_cache: Optional[ContractKnowledgeGraph] = None


def get_graph() -> ContractKnowledgeGraph:
    global _kg_cache
    if _kg_cache is None:
        _kg_cache = ContractKnowledgeGraph()
        _kg_cache.build_from_manifest(load_manifest())
    return _kg_cache


def list_categories() -> List[str]:
    return sorted({n for n, d in get_graph().graph.nodes(data=True) if d.get("type") == "category"})


def list_parties() -> List[str]:
    return sorted({n for n, d in get_graph().graph.nodes(data=True) if d.get("type") == "party"})


# ---------------------------------------------------------------------------
# Review Tasks — genuinely new, local JSON-backed state (not fake)
# ---------------------------------------------------------------------------

def _load_tasks() -> List[Dict[str, Any]]:
    if not _TASKS_PATH.exists():
        return []
    return json.loads(_TASKS_PATH.read_text(encoding="utf-8"))


def _save_tasks(tasks: List[Dict[str, Any]]) -> None:
    _TASKS_PATH.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def list_tasks(doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
    tasks = _load_tasks()
    return [t for t in tasks if doc_id is None or t["doc_id"] == doc_id]


def add_task(doc_id: str, finding_title: str, note: str = "") -> Dict[str, Any]:
    tasks = _load_tasks()
    task = {
        "task_id": uuid.uuid4().hex[:8], "doc_id": doc_id, "finding_title": finding_title,
        "note": note, "status": "open", "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tasks.append(task)
    _save_tasks(tasks)
    return task


def set_task_status(task_id: str, status: str) -> bool:
    tasks = _load_tasks()
    for t in tasks:
        if t["task_id"] == task_id:
            t["status"] = status
            _save_tasks(tasks)
            return True
    return False


# ---------------------------------------------------------------------------
# Reports (Phase 7 — reused, not rebuilt)
# ---------------------------------------------------------------------------

def get_report_markdown(doc_id: str) -> str:
    return generate_document_report(doc_id)


def export_report_file(doc_id: str) -> Optional[str]:
    """Writes the report to disk and returns its path so the UI/API can
    offer it as a real download."""
    try:
        text = generate_document_report(doc_id)
    except FileNotFoundError:
        return None
    out_path = REPORTS_ROOT / f"phase7_report_{doc_id}.md"
    out_path.write_text(text, encoding="utf-8")
    return str(out_path)


# ---------------------------------------------------------------------------
# Activity & Traces — reads the real per-call log Phase 7 writes; no
# fabricated "demo trace" placeholder.
# ---------------------------------------------------------------------------

def get_recent_activity(limit: int = 50) -> List[Dict[str, Any]]:
    log_path = REPORTS_ROOT / "phase7_llm_calls.jsonl"
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    return records[-limit:][::-1]  # most recent first


def get_recovery_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Real closed-loop recovery events (what failed, how it was classified,
    which different strategy was chosen, and whether it worked)."""
    return read_recovery_events()[-limit:][::-1]
