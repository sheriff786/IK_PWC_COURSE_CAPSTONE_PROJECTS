"""The conversational agent must resolve follow-ups, answer only from
retrieved passages, and verify every quote. LLM calls are mocked so these
run offline and deterministically."""

from unittest.mock import patch

import pytest

from contractiq import chat
from contractiq.chat import _GroundedAnswer, _verify_quotes, answer_question, condense_question
from contractiq.retrieval import _looks_like_heading, expand_locator_range, normalize_for_match

_PASSAGES = [
    {"passage_id": "FIN-001@paragraph:11", "doc_id": "FIN-001", "locator": "paragraph:11",
     "heading": None, "score": 0.59,
     "text": "Late payments will attract an interest of 1.5% per month on the outstanding amount."},
    {"passage_id": "FIN-001@paragraph:10", "doc_id": "FIN-001", "locator": "paragraph:10",
     "heading": None, "score": 0.37,
     "text": "Payment is due within 30 calendar days from the date of invoice receipt."},
]


# --- stage 1: condensing follow-ups -----------------------------------------

def test_first_turn_makes_no_llm_call():
    """No history means nothing to resolve — paying for a rewrite would be
    pure cost with no possible benefit."""
    with patch("contractiq.chat._get_openai_client") as client:
        assert condense_question("what are the payment terms?", history=None) == \
            "what are the payment terms?"
        client.assert_not_called()


def test_condense_failure_degrades_to_the_raw_question():
    history = [{"role": "user", "content": "late payment interest?"}]
    with patch("contractiq.chat.call_with_recovery", side_effect=lambda fn, **kw: kw["on_give_up"]("s", Exception())):
        assert condense_question("and when is it due?", history) == "and when is it due?"


# --- stage 3: grounding and verification ------------------------------------

def test_quote_found_in_passage_is_verified():
    answer = _GroundedAnswer(sufficient_evidence=True, answer="1.5% per month.",
                             cited_passage_ids=["FIN-001@paragraph:11"],
                             quoted_excerpts=["interest of 1.5% per month"])
    checked = _verify_quotes(answer, _PASSAGES)
    assert not checked["unverified"]
    assert checked["verified"][0]["found_in"] == ["FIN-001@paragraph:11"]


def test_fabricated_quote_is_flagged_not_trusted():
    answer = _GroundedAnswer(sufficient_evidence=True, answer="It is 9% per month.",
                             cited_passage_ids=["FIN-001@paragraph:11"],
                             quoted_excerpts=["interest of 9% per month"])
    checked = _verify_quotes(answer, _PASSAGES)
    assert checked["unverified"], "a quote that isn't in the source must be flagged"


def test_quote_matching_tolerates_case_and_whitespace_only_differences():
    answer = _GroundedAnswer(sufficient_evidence=True, answer="x",
                             cited_passage_ids=[],
                             quoted_excerpts=["LATE   payments  will attract an interest"])
    assert not _verify_quotes(answer, _PASSAGES)["unverified"]


def test_no_passages_means_no_answer_is_invented():
    with patch("contractiq.chat.search_passages", return_value=[]):
        result = answer_question("what is the insurance limit?", doc_id="FIN-001")
    assert result["status"] == "no_evidence"
    assert result["citations"] == []


def test_insufficient_evidence_is_reported_not_papered_over():
    weak = _GroundedAnswer(sufficient_evidence=False,
                           answer="The passages do not discuss insurance.",
                           cited_passage_ids=[], quoted_excerpts=[])
    with patch("contractiq.chat.search_passages", return_value=_PASSAGES), \
         patch("contractiq.chat.call_with_recovery", return_value=weak):
        result = answer_question("what is the insurance limit?")
    assert result["status"] == "no_evidence"
    assert result["citations"] == []


def test_answer_status_flags_unverified_quotes():
    bad = _GroundedAnswer(sufficient_evidence=True, answer="It is 9%.",
                          cited_passage_ids=["FIN-001@paragraph:11"],
                          quoted_excerpts=["interest of 9% per month"])
    with patch("contractiq.chat.search_passages", return_value=_PASSAGES), \
         patch("contractiq.chat.call_with_recovery", return_value=bad):
        result = answer_question("late payment interest?")
    assert result["status"] == "unverified_quotes"


def test_citations_recovered_from_quotes_when_model_cites_nothing():
    """A verbatim quote proves provenance better than a self-reported id."""
    answer = _GroundedAnswer(sufficient_evidence=True, answer="1.5% per month.",
                             cited_passage_ids=[],
                             quoted_excerpts=["interest of 1.5% per month"])
    with patch("contractiq.chat.search_passages", return_value=_PASSAGES), \
         patch("contractiq.chat.call_with_recovery", return_value=answer):
        result = answer_question("late payment interest?")
    assert [c["locator"] for c in result["citations"]] == ["paragraph:11"]


def test_generation_failure_still_returns_the_evidence():
    with patch("contractiq.chat.search_passages", return_value=_PASSAGES), \
         patch("contractiq.chat.call_with_recovery", return_value=None):
        result = answer_question("late payment interest?")
    assert result["status"] == "error"
    assert result["passages"], "evidence must survive a generation failure"


# --- passage-stage helpers ---------------------------------------------------

@pytest.mark.parametrize("text", [
    "5. Mutual Obligations and Risk Management",
    "8. DURATION OF OBLIGATIONS AND SURVIVAL CLAUSE",
    "3.2 Payment Terms:",
    "DEFINITIONS",
])
def test_section_titles_are_not_treated_as_evidence(text):
    """Headings are short, so they score deceptively well on short queries and
    would produce confident citations containing no actual content."""
    assert _looks_like_heading(text)


@pytest.mark.parametrize("text", [
    "Late payments will attract an interest of 1.5% per month on the outstanding amount.",
    "Payment is due within 30 calendar days from the date of invoice receipt.",
    'Between:\nPrimevolta Hardware Solutions ("Vendor")\nAnd\nFinSecure Services ("Client")',
])
def test_real_clauses_are_kept_as_evidence(text):
    assert not _looks_like_heading(text)


def test_locator_range_expansion():
    assert expand_locator_range("paragraph:3-paragraph:5") == [
        "paragraph:3", "paragraph:4", "paragraph:5"]
    assert expand_locator_range("paragraph:7") == ["paragraph:7"]
    assert expand_locator_range("") == []


def test_normalize_is_shared_and_consistent():
    assert normalize_for_match("The  Vendor\nshall") == normalize_for_match("the vendor shall")
