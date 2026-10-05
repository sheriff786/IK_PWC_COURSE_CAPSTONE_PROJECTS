"""Citation drill-down must resolve a finding's evidence back to the REAL
paragraphs of the source document, and agree with the verification verdict.
Runs against saved artifacts + the existing index (no LLM calls)."""

import pytest

from contractiq import app_service as svc
from contractiq.app_service import _parse_locator_range


def test_locator_range_expands_to_every_paragraph_it_covers():
    assert _parse_locator_range("paragraph:3-paragraph:6") == [
        "paragraph:3", "paragraph:4", "paragraph:5", "paragraph:6"]
    assert _parse_locator_range("paragraph:7") == ["paragraph:7"]
    assert _parse_locator_range("") == []


def _first_verified_finding():
    for doc_id in svc.list_assessed_doc_ids():
        review = svc.get_risk_review(doc_id)
        for finding in review.get("findings", []):
            if finding["verification_status"] == "verified" and finding["evidence_ids"]:
                return doc_id, finding
    return None, None


def test_verified_finding_resolves_to_real_source_paragraphs():
    doc_id, finding = _first_verified_finding()
    if finding is None:
        pytest.skip("no saved verified findings to resolve")

    citations = svc.resolve_finding_citations(doc_id, finding)
    assert citations, "a finding with evidence_ids must resolve to at least one citation"

    for citation in citations:
        assert citation["found"], citation.get("reason")
        assert citation["paragraphs"], "citation must open real paragraphs, not just a chunk id"
        assert citation["filename"], "reviewer needs the real filename, not only a doc_id"


def test_verified_quote_is_physically_located_in_the_source():
    """The UI highlights the paragraph containing the quote. If a finding is
    marked verified, that highlight must actually have something to point at —
    otherwise the UI would claim provenance it cannot show."""
    doc_id, finding = _first_verified_finding()
    if finding is None:
        pytest.skip("no saved verified findings to resolve")

    citations = svc.resolve_finding_citations(doc_id, finding)
    assert any(c["quote_located"] for c in citations), (
        "a VERIFIED finding must have its quote locatable in the resolved paragraphs")


def test_unknown_chunk_is_reported_not_faked():
    result = svc.resolve_citation("MLA-001", "MLA-001-does-not-exist")
    assert result["found"] is False
    assert "reason" in result
