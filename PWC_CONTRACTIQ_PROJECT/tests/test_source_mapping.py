"""
Phase 7, roadmap item 7: source-mapping test.

Every Finding's evidence_ids must resolve back to real chunks in the
persisted ChromaDB index, with a real source_location_range — and for a
VERIFIED finding, its quoted excerpt must genuinely appear in that chunk's
text. This runs against the REAL saved Phase 5 artifacts and the REAL
local ChromaDB index (no OpenAI calls needed — chunk lookup by id doesn't
require embedding anything).
"""

import json

import pytest

from contractiq.config import REPORTS_ROOT
from contractiq.retrieval import get_chroma_collection


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def _load_all_findings():
    findings = []
    for path in sorted(REPORTS_ROOT.glob("phase5_assessment_*.json")):
        assessment = json.loads(path.read_text(encoding="utf-8"))
        for dim_result in assessment["dimension_results"]:
            findings.extend(dim_result["findings"])
    return findings


@pytest.fixture(scope="module")
def saved_findings():
    findings = _load_all_findings()
    if not findings:
        pytest.skip("no saved phase5_assessment_*.json artifacts found — run Phase 5 first")
    return findings


def test_every_evidence_id_resolves_to_a_real_chunk(saved_findings):
    collection = get_chroma_collection()
    all_ids = {cid for f in saved_findings for cid in f["evidence_ids"]}
    assert all_ids, "no evidence_ids found across any saved finding"

    result = collection.get(ids=list(all_ids), include=["metadatas", "documents"])
    resolved_ids = set(result["ids"])
    missing = all_ids - resolved_ids
    assert not missing, f"evidence_ids that do NOT resolve to a real chunk in the index: {missing}"


def test_resolved_chunks_carry_a_source_location(saved_findings):
    collection = get_chroma_collection()
    all_ids = list({cid for f in saved_findings for cid in f["evidence_ids"]})
    result = collection.get(ids=all_ids, include=["metadatas"])
    for cid, meta in zip(result["ids"], result["metadatas"]):
        assert meta.get("source_location_range"), f"{cid} is missing its source_location_range"
        assert meta.get("doc_id"), f"{cid} is missing its doc_id"


def test_verified_findings_quote_genuinely_appears_in_its_chunk(saved_findings):
    collection = get_chroma_collection()
    verified = [f for f in saved_findings
                if f["verification_status"] == "verified" and f["evidence_excerpts"]]
    assert verified, "no VERIFIED findings with an excerpt found to check"

    checked = 0
    for f in verified:
        result = collection.get(ids=f["evidence_ids"], include=["documents"])
        quote = _normalize(f["evidence_excerpts"][0])
        found_in_any_chunk = any(quote in _normalize(doc) for doc in result["documents"])
        assert found_in_any_chunk, (
            f"finding {f['finding_id']} is marked VERIFIED but its excerpt does not "
            f"genuinely appear in chunk(s) {f['evidence_ids']}"
        )
        checked += 1
    assert checked == len(verified)
