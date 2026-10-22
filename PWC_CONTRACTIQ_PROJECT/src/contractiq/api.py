"""
ContractIQ — FastAPI deployment surface.

Every endpoint is a thin adapter over app_service.py — the SAME facade the
Gradio UI uses. No analysis logic lives here, so the API and the UI can
never drift apart or disagree about what the system found.

Run locally:
    uvicorn contractiq.api:app --reload --port 8000
Interactive docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import app_service as svc

app = FastAPI(
    title="ContractIQ API",
    version="1.0.0",
    description="Multi-agent contract risk intelligence. Every finding is "
                 "evidence-grounded and independently verified against source text.",
)


# ---------------------------------------------------------------------------
# Request/response contracts
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    query: str = Field(min_length=2, description="Natural-language question")
    doc_id: Optional[str] = Field(default=None, description="Scope search to one document")
    top_k: int = Field(default=5, ge=1, le=20)


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="Prior turns. Sent by the client so the API stays stateless — "
                    "follow-ups like 'and when is it due?' are resolved against this.")
    doc_id: Optional[str] = Field(default=None)


class TaskRequest(BaseModel):
    doc_id: str
    finding_title: str
    note: str = ""


class TaskStatusRequest(BaseModel):
    status: str = Field(pattern="^(open|in_progress|done)$")


# ---------------------------------------------------------------------------
# Health & overview
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
def health() -> Dict[str, Any]:
    overview = svc.get_overview()
    return {
        "status": "ok",
        "documents": overview["total_documents"],
        "assessed": overview["assessed_documents"],
        "graph_nodes": overview["graph_nodes"],
    }


@app.get("/api/overview", tags=["system"])
def overview() -> Dict[str, Any]:
    return svc.get_overview()


# ---------------------------------------------------------------------------
# Library & sources
# ---------------------------------------------------------------------------

@app.get("/api/documents", tags=["library"])
def list_documents() -> List[Dict[str, Any]]:
    return svc.list_documents()


@app.get("/api/documents/{doc_id}/chunks", tags=["library"])
def document_chunks(doc_id: str) -> List[Dict[str, Any]]:
    chunks = svc.get_document_chunks(doc_id)
    if not chunks:
        raise HTTPException(404, f"No indexed chunks found for {doc_id}")
    return chunks


# ---------------------------------------------------------------------------
# Risk analysis
# ---------------------------------------------------------------------------

@app.get("/api/assessments", tags=["risk"])
def list_assessments() -> List[str]:
    return svc.list_assessed_doc_ids()


@app.get("/api/assessments/{doc_id}", tags=["risk"])
def get_assessment(doc_id: str) -> Dict[str, Any]:
    review = svc.get_risk_review(doc_id)
    if not review["available"]:
        raise HTTPException(404, f"No saved assessment for {doc_id}")
    return review


@app.post("/api/assessments/{doc_id}/analyze", tags=["risk"])
def analyze(doc_id: str) -> Dict[str, Any]:
    """Runs the full pipeline (triage routing -> specialists -> consensus).
    Slow by nature — this is real multi-agent analysis, not a cached read."""
    try:
        return svc.analyze_uploaded_document(doc_id)
    except Exception as exc:  # noqa: BLE001 - surfaced to the client as a 500 with context
        raise HTTPException(500, f"Analysis failed: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Citation drill-down — the endpoint that proves a finding's provenance
# ---------------------------------------------------------------------------

@app.get("/api/citations/{doc_id}/{chunk_id}", tags=["evidence"])
def citation(doc_id: str, chunk_id: str,
              quote: Optional[str] = Query(default=None, description="Excerpt to locate")) -> Dict[str, Any]:
    result = svc.resolve_citation(doc_id, chunk_id, quote)
    if not result["found"]:
        raise HTTPException(404, result.get("reason", "citation not resolvable"))
    return result


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@app.post("/api/ask", tags=["search"])
def ask(payload: AskRequest) -> Dict[str, Any]:
    results = svc.ask(payload.query, doc_id=payload.doc_id, top_k=payload.top_k)
    return {"query": payload.query, "count": len(results), "results": results}


@app.post("/api/ask/passages", tags=["search"])
def ask_passages(payload: AskRequest) -> Dict[str, Any]:
    """Paragraph-level search — precise locators even for short documents that
    are stored as one whole-file chunk."""
    results = svc.ask_passages(payload.query, doc_id=payload.doc_id, top_k=payload.top_k)
    return {"query": payload.query, "count": len(results), "results": results}


@app.post("/api/chat", tags=["search"])
def chat(payload: ChatRequest) -> Dict[str, Any]:
    """One grounded conversational turn. Resolves follow-ups against the
    supplied history, answers only from retrieved passages, and reports a
    status of answered / no_evidence / unverified_quotes / error."""
    history = [m.model_dump() for m in payload.history]
    return svc.chat(payload.message, history=history, doc_id=payload.doc_id)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@app.post("/api/upload", tags=["library"])
async def upload(file: UploadFile = File(...),
                  category_key: str = Query(default="master_agreements")) -> Dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Only .docx is supported by the Phase 1 parser")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        result = svc.upload_document(tmp_path, category_key)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not result["success"]:
        raise HTTPException(422, result.get("error", "Parse failed"))
    return result


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@app.get("/api/reports/{doc_id}", tags=["reports"])
def report(doc_id: str) -> Dict[str, Any]:
    try:
        return {"doc_id": doc_id, "markdown": svc.get_report_markdown(doc_id)}
    except FileNotFoundError:
        raise HTTPException(404, f"No saved assessment for {doc_id}")


@app.get("/api/reports/{doc_id}/download", tags=["reports"])
def download_report(doc_id: str) -> FileResponse:
    path = svc.export_report_file(doc_id)
    if path is None:
        raise HTTPException(404, f"No saved assessment for {doc_id}")
    return FileResponse(path, media_type="text/markdown", filename=f"ContractIQ_{doc_id}.md")


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------

@app.get("/api/graph/categories/{category_key}", tags=["relationships"])
def documents_by_category(category_key: str) -> Dict[str, Any]:
    return {"category_key": category_key,
            "documents": svc.get_graph().get_documents_by_category(category_key)}


@app.get("/api/graph/parties/{party}", tags=["relationships"])
def documents_by_party(party: str) -> Dict[str, Any]:
    return {"party": party, "documents": svc.get_graph().get_documents_by_party(party)}


@app.get("/api/graph/external-references/{doc_id}", tags=["relationships"])
def external_references(doc_id: str) -> Dict[str, Any]:
    return {"doc_id": doc_id, "references": svc.get_graph().get_external_references(doc_id)}


# ---------------------------------------------------------------------------
# Review tasks
# ---------------------------------------------------------------------------

@app.get("/api/tasks", tags=["tasks"])
def list_tasks(doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return svc.list_tasks(doc_id)


@app.post("/api/tasks", tags=["tasks"], status_code=201)
def create_task(payload: TaskRequest) -> Dict[str, Any]:
    return svc.add_task(payload.doc_id, payload.finding_title, payload.note)


@app.patch("/api/tasks/{task_id}", tags=["tasks"])
def update_task(task_id: str, payload: TaskStatusRequest) -> Dict[str, Any]:
    if not svc.set_task_status(task_id, payload.status):
        raise HTTPException(404, f"No task {task_id}")
    return {"task_id": task_id, "status": payload.status}


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

@app.get("/api/activity", tags=["observability"])
def activity(limit: int = Query(default=50, ge=1, le=500)) -> List[Dict[str, Any]]:
    return svc.get_recent_activity(limit)


@app.get("/api/recovery-events", tags=["observability"])
def recovery_events(limit: int = Query(default=50, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Closed-loop recovery audit trail: what failed, how it was classified,
    which different strategy was selected, and whether that worked."""
    return svc.get_recovery_events(limit)
