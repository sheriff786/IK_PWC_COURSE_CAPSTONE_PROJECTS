"""FastAPI endpoints must stay a thin adapter over app_service — same data
as the UI, correct status codes, no analysis logic of its own."""

from fastapi.testclient import TestClient

from contractiq import app_service as svc
from contractiq.api import app

client = TestClient(app)


def test_health_reports_real_corpus_state():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["documents"] == len(svc.list_documents())


def test_documents_endpoint_matches_the_service_facade():
    """The API must not maintain its own view of the corpus."""
    assert client.get("/api/documents").json() == svc.list_documents()


def test_missing_assessment_is_404_not_an_empty_success():
    response = client.get("/api/assessments/DOES-NOT-EXIST")
    assert response.status_code == 404


def test_citation_endpoint_returns_source_paragraphs():
    doc_ids = svc.list_assessed_doc_ids()
    if not doc_ids:
        return
    doc_id = doc_ids[0]
    chunks = svc.get_document_chunks(doc_id)
    if not chunks:
        return
    body = client.get(f"/api/citations/{doc_id}/{chunks[0]['chunk_id']}").json()
    assert body["found"] is True
    assert body["paragraphs"], "citation endpoint must expose real paragraphs"


def test_unresolvable_citation_is_404():
    assert client.get("/api/citations/MLA-001/NOPE-c99").status_code == 404


def test_upload_rejects_non_docx():
    response = client.post("/api/upload",
                            files={"file": ("notes.txt", b"not a contract", "text/plain")})
    assert response.status_code == 400


def test_task_lifecycle_create_then_update():
    created = client.post("/api/tasks", json={"doc_id": "TEST-API",
                                               "finding_title": "pytest task",
                                               "note": ""})
    assert created.status_code == 201
    task_id = created.json()["task_id"]

    assert client.patch(f"/api/tasks/{task_id}", json={"status": "done"}).status_code == 200
    assert client.patch("/api/tasks/nope", json={"status": "done"}).status_code == 404

    # leave the store as we found it
    remaining = [t for t in svc.list_tasks() if t["task_id"] != task_id]
    svc._save_tasks(remaining)
