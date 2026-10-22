"""
ContractIQ — conversational retrieval agent behind "Ask ContractIQ".

Three stages, each with a reason to exist:

1. CONDENSE — a follow-up like "what about termination?" or "tell me more
   about it" is meaningless to a vector search, because "it" has no referent
   in the embedding. The question is first rewritten into a standalone one
   using recent history. Skipped entirely on the first turn, so a simple
   question never pays for an extra LLM call.

2. RETRIEVE — passage-level search (retrieval.search_passages), so citations
   land on a paragraph rather than "somewhere in this 637-word document".

3. ANSWER + VERIFY — the model may only answer from the retrieved passages,
   must cite them, and must quote verbatim. Every quote is then re-checked
   against the passage text in code. A quote that isn't really there is
   flagged, never silently presented as fact — the same discipline the risk
   agents use for findings.

If the evidence does not answer the question, the agent says so. "I didn't
find it" is a valid, useful answer; a confident answer from weak evidence
is not.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Reused, not re-implemented: one OpenAI client and one call-logging format
# across the whole package, so Phase 7's cost/latency metrics stay complete.
from .agents import _get_openai_client, _log_llm_call
from .config import CHAT_HISTORY_TURNS, CHAT_MODEL, PASSAGE_TOP_K
from .resilience import SchemaFailure, call_with_recovery
from .retrieval import normalize_for_match, search_passages

try:
    from langfuse.decorators import observe
except ImportError:  # Langfuse not configured — tracing becomes a no-op
    def observe(*_args, **_kwargs):
        def decorator(fn):
            return fn
        return decorator


# ---------------------------------------------------------------------------
# Stage 1 — condense a follow-up into a standalone question
# ---------------------------------------------------------------------------

class _CondensedQuestion(BaseModel):
    standalone_question: str = Field(
        description="The user's latest message rewritten so it can be understood "
                    "with no conversation history. Resolve pronouns like 'it', "
                    "'that', 'they' using the history. If the latest message is "
                    "already self-contained, return it unchanged."
    )


_CONDENSE_PROMPT = (
    "You rewrite the latest user message into a standalone search question for a "
    "contract-document search engine. Resolve any pronoun or implicit reference "
    "using the conversation history. Keep the user's intent and wording as much as "
    "possible — do not answer the question, do not add information, and do not "
    "invent contract terms that were never mentioned."
)


def _format_history(history: List[Dict[str, str]], turns: int = CHAT_HISTORY_TURNS) -> str:
    recent = [m for m in history if m.get("role") in ("user", "assistant")][-turns * 2:]
    return "\n".join(f'{m["role"]}: {m["content"]}' for m in recent)


@observe(name="chat_condense_question")
def condense_question(question: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """Rewrites a follow-up into a standalone question. Returns the question
    unchanged (and makes NO api call) when there's no history to resolve
    against — the common case shouldn't pay for a capability it can't use."""
    if not history:
        return question

    client = _get_openai_client()
    transcript = _format_history(history)

    def _attempt(active_model: str) -> str:
        t0 = time.perf_counter()
        completion = client.beta.chat.completions.parse(
            model=active_model,
            messages=[
                {"role": "system", "content": _CONDENSE_PROMPT},
                {"role": "user", "content": f"Conversation so far:\n{transcript}\n\n"
                                             f"Latest user message:\n{question}"},
            ],
            response_format=_CondensedQuestion,
            temperature=0,
        )
        usage = completion.usage.model_dump() if completion.usage else None
        parsed = completion.choices[0].message.parsed
        _log_llm_call("chat_condense", active_model, (time.perf_counter() - t0) * 1000,
                       usage, schema_failure=parsed is None)
        if parsed is None:
            raise SchemaFailure("condense: unparseable output")
        return parsed.standalone_question.strip() or question

    # Degrade to the raw question rather than failing the whole turn.
    return call_with_recovery(_attempt, stage="chat_condense", model=CHAT_MODEL,
                               on_give_up=lambda _s, _e: question)


# ---------------------------------------------------------------------------
# Stage 3 — answer strictly from retrieved passages
# ---------------------------------------------------------------------------

class _GroundedAnswer(BaseModel):
    sufficient_evidence: bool = Field(
        description="False if the provided passages do not actually answer the question. "
                    "Be strict: related-but-not-answering counts as False."
    )
    answer: str = Field(
        description="A concise answer built ONLY from the passages. If "
                    "sufficient_evidence is false, explain what is missing instead."
    )
    cited_passage_ids: List[str] = Field(
        default_factory=list,
        description="passage_id values copied verbatim from the passages used.")
    quoted_excerpts: List[str] = Field(
        default_factory=list,
        description="Short verbatim quotes copied EXACTLY from the passage text "
                    "that support the answer. Never paraphrase inside a quote.")


_ANSWER_PROMPT = (
    "You answer questions about contracts using ONLY the numbered passages provided. "
    "Never use outside legal knowledge and never state what a typical contract usually "
    "says. If the passages do not answer the question, set sufficient_evidence=false and "
    "say plainly what is missing — that is a correct and useful response, not a failure. "
    "When you do answer: keep it concise, cite the passage_id(s) you used, and include "
    "short quotes copied character-for-character from the passage text."
)


def _format_passages(passages: List[Dict[str, Any]]) -> str:
    blocks = []
    for p in passages:
        heading = f' — section: {p["heading"]}' if p.get("heading") else ""
        blocks.append(f'[passage_id={p["passage_id"]}] ({p["doc_id"]} @ {p["locator"]}{heading})\n'
                       f'{p["text"]}')
    return "\n\n".join(blocks)


def _verify_quotes(answer: _GroundedAnswer, passages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Re-checks every quote against the real passage text. Searches all
    passages shown to the model, not only the ones it claimed to cite — a
    model that quotes real text but mislabels its source made a citation
    error, not a fabrication, and those are worth telling apart."""
    corpus = {p["passage_id"]: normalize_for_match(p["text"]) for p in passages}
    verified, unverified = [], []
    for quote in answer.quoted_excerpts:
        needle = normalize_for_match(quote)
        found_in = [pid for pid, text in corpus.items() if needle and needle in text]
        (verified if found_in else unverified).append({"quote": quote, "found_in": found_in})
    return {"verified": verified, "unverified": unverified}


@observe(name="chat_answer")
def answer_question(question: str,
                     history: Optional[List[Dict[str, str]]] = None,
                     doc_id: Optional[str] = None,
                     top_k: int = PASSAGE_TOP_K) -> Dict[str, Any]:
    """Full conversational turn: condense -> retrieve -> answer -> verify.

    Always returns a dict (never raises) so one bad turn cannot kill the
    chat session. `status` tells the caller what actually happened:
    answered / no_evidence / unverified_quotes / error.
    """
    standalone = condense_question(question, history)
    passages = search_passages(standalone, top_k=top_k, doc_id=doc_id)

    if not passages:
        return {
            "status": "no_evidence",
            "question": question,
            "standalone_question": standalone,
            "answer": ("I couldn't find anything relevant to that"
                        + (f" in {doc_id}." if doc_id else " in the indexed documents.")
                        + " Try rephrasing, or widen the scope."),
            "passages": [], "citations": [], "unverified_quotes": [],
        }

    client = _get_openai_client()
    passage_block = _format_passages(passages)

    def _attempt(active_model: str) -> _GroundedAnswer:
        t0 = time.perf_counter()
        completion = client.beta.chat.completions.parse(
            model=active_model,
            messages=[
                {"role": "system", "content": _ANSWER_PROMPT},
                {"role": "user", "content": f"Question: {standalone}\n\nPassages:\n{passage_block}"},
            ],
            response_format=_GroundedAnswer,
            temperature=0,
        )
        usage = completion.usage.model_dump() if completion.usage else None
        parsed = completion.choices[0].message.parsed
        _log_llm_call("chat_answer", active_model, (time.perf_counter() - t0) * 1000,
                       usage, schema_failure=parsed is None)
        if parsed is None:
            raise SchemaFailure("chat_answer: unparseable output")
        return parsed

    result = call_with_recovery(_attempt, stage="chat_answer", model=CHAT_MODEL,
                                 on_give_up=lambda _s, _e: None)

    if result is None:
        return {
            "status": "error",
            "question": question, "standalone_question": standalone,
            "answer": ("I retrieved the relevant passages but couldn't generate an answer "
                        "just now. The evidence below is still accurate — please read it directly."),
            "passages": passages, "citations": [], "unverified_quotes": [],
        }

    if not result.sufficient_evidence:
        return {
            "status": "no_evidence",
            "question": question, "standalone_question": standalone,
            "answer": result.answer,
            "passages": passages, "citations": [], "unverified_quotes": [],
        }

    checked = _verify_quotes(result, passages)
    by_id = {p["passage_id"]: p for p in passages}
    cited_ids = [pid for pid in result.cited_passage_ids if pid in by_id]
    # A quote proves provenance better than a self-reported id, so trust it
    # when the model's citation list is wrong or empty.
    for item in checked["verified"]:
        cited_ids.extend(pid for pid in item["found_in"] if pid not in cited_ids)

    return {
        "status": "unverified_quotes" if checked["unverified"] else "answered",
        "question": question,
        "standalone_question": standalone,
        "answer": result.answer,
        "passages": passages,
        "citations": [by_id[pid] for pid in cited_ids if pid in by_id],
        "verified_quotes": checked["verified"],
        "unverified_quotes": checked["unverified"],
    }
