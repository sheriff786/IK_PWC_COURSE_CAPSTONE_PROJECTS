"""
Phase 7, roadmap item 7: entity-normalization test.

Regression tests for the two real bugs found and fixed while building
Phase 7's evaluation report: (1) keyword matching without word boundaries
falsely matched inside unrelated words ("nda" inside "standard"), and
(2) context classification used the whole clause instead of a local
window, cross-contaminating multiple amounts/dates in one clause.
"""

from contractiq.extraction import (
    _find_context_type,
    _local_window,
    extract_entities_from_clause,
)
from contractiq.models import SourceLocation


def _clause(text: str, locator: str = "paragraph:1") -> dict:
    return {
        "clause_id": "TEST-c0",
        "text": text,
        "heading": None,
        "source_location": SourceLocation(doc_id="TEST", kind="paragraph", locator=locator).model_dump(),
    }


def test_short_keyword_does_not_match_inside_unrelated_words():
    # "nda" must not fire on "standard" / "mandatory" / "recommendations"
    clause = _clause("All hardware meets mandatory security standards and our recommendations follow best practice.")
    entities = extract_entities_from_clause(clause)
    confidentiality_hits = [e for e in entities if e.entity_type == "clause_term:confidentiality"]
    assert not confidentiality_hits, f"false positive 'nda' match(es): {confidentiality_hits}"


def test_short_keyword_still_matches_as_a_real_word():
    clause = _clause("This NDA governs confidential information shared between the parties.")
    entities = extract_entities_from_clause(clause)
    confidentiality_hits = [e for e in entities if e.entity_type == "clause_term:confidentiality"]
    assert confidentiality_hits, "genuine 'NDA'/'confidential information' mention was not matched"


def test_context_classification_uses_local_window_not_whole_clause():
    # Subtotal/GST/Total in one clause -- only the amount actually near the
    # word "Invoice" should be classified as invoice_amount.
    text = "Subtotal: INR 2,000,000\nGST @18%: INR 360,000\nTotal Invoice Amount: INR 2,360,000"
    gst_window = _local_window(text, text.index("360,000"), text.index("360,000") + len("360,000"))
    assert _find_context_type(gst_window, {"invoice_amount": ["invoice"]}) == "unclassified"

    total_window = _local_window(text, text.index("2,360,000"), text.index("2,360,000") + len("2,360,000"))
    assert _find_context_type(total_window, {"invoice_amount": ["invoice"]}) == "invoice_amount"
