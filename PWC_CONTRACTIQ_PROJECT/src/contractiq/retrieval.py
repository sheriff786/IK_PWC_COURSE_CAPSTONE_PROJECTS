"""
ContractIQ — Phase 3: Build evaluated semantic retrieval.

Roadmap reference: 03_Retrieval_and_ChromaDB.ipynb

Guiding rules this module follows literally:
- Chunks preserve clause boundaries — a clause is never split mid-way.
- Start at 600-800 words / 80-120 word overlap, then MEASURE before trusting
  those numbers (see compare_chunk_configs below) — not assumed optimal.
- Idempotent indexing: unchanged content (same text_hash) is not re-embedded.
- Search returns text, score, document metadata, AND source locations —
  every result is traceable back to an exact spot in the original document.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from openai import OpenAI

from .config import CHROMA_PERSIST_DIR, CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS, EMBEDDING_MODEL, \
    EVALUATIONS_ROOT, OPENAI_API_KEY, REPORTS_ROOT
from .models import Chunk, DocumentRecord
from .parsing import load_parsed_document

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


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Chunking — clause-boundary aware, configurable so Phase 3's own guiding
# rule ("measure, don't assume") can actually be followed.
# ---------------------------------------------------------------------------

def chunk_document(doc_id: str, category_key: str, clauses: List[Dict[str, Any]],
                    doc_version: str = "1",
                    target_words: int = CHUNK_SIZE_WORDS,
                    overlap_words: int = CHUNK_OVERLAP_WORDS) -> List[Chunk]:
    """
    Groups whole clauses into chunks near target_words, never splitting a
    clause across two chunks. Overlap is achieved by carrying trailing
    clauses from the previous chunk into the next, up to overlap_words.
    """
    groups: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    current_words = 0

    for clause in clauses:
        clause_words = len(clause["text"].split())
        if current and current_words + clause_words > target_words:
            groups.append(current)
            overlap: List[Dict[str, Any]] = []
            overlap_count = 0
            for c in reversed(current):
                c_words = len(c["text"].split())
                if overlap_count + c_words > overlap_words:
                    break
                overlap.insert(0, c)
                overlap_count += c_words
            current = overlap.copy()
            current_words = overlap_count
        current.append(clause)
        current_words += clause_words

    if current:
        groups.append(current)

    chunks: List[Chunk] = []
    for idx, group in enumerate(groups):
        text = "\n".join(c["text"] for c in group)
        start_locator = group[0]["source_location"]["locator"]
        end_locator = group[-1]["source_location"]["locator"]
        location_range = start_locator if start_locator == end_locator else f"{start_locator}-{end_locator}"

        chunks.append(Chunk(
            chunk_id=f"{doc_id}-c{idx}",
            doc_id=doc_id,
            doc_version=doc_version,
            category_key=category_key,
            text=text,
            text_hash=_text_hash(text),
            source_location_range=location_range,
            chunk_index=idx,
            total_chunks=len(groups),
        ))
    return chunks


def chunk_all_documents(manifest: List[DocumentRecord],
                         target_words: int = CHUNK_SIZE_WORDS,
                         overlap_words: int = CHUNK_OVERLAP_WORDS) -> Dict[str, List[Chunk]]:
    """Chunks every successfully-parsed document. Skips (and reports) any
    document Phase 1 couldn't parse — you can't chunk what wasn't extracted."""
    chunks_by_doc: Dict[str, List[Chunk]] = {}
    skipped: List[str] = []

    for record in manifest:
        try:
            parsed = load_parsed_document(record.doc_id)
        except FileNotFoundError:
            skipped.append(record.doc_id)
            continue
        if parsed["parse_status"] != "parsed":
            skipped.append(record.doc_id)
            continue

        chunks_by_doc[record.doc_id] = chunk_document(
            record.doc_id, record.category_key, parsed["clauses"],
            target_words=target_words, overlap_words=overlap_words,
        )

    total_chunks = sum(len(c) for c in chunks_by_doc.values())
    print(f"Chunked {len(chunks_by_doc)} documents into {total_chunks} chunks "
          f"(target={target_words}w, overlap={overlap_words}w).")
    if skipped:
        print(f"Skipped {len(skipped)} document(s) with no successful Phase 1 parse: {skipped}")

    return chunks_by_doc


def compare_chunk_configs(manifest: List[DocumentRecord],
                           configs: List[Dict[str, int]]) -> Dict[str, Any]:
    """
    Measures chunk-count and size distribution for several (target_words,
    overlap_words) settings, so the 600-800/80-120 starting point can be
    compared rather than assumed. Does NOT judge retrieval quality by
    itself — pair this with evaluate_retrieval() on the actual test set
    once an index is built for each candidate config.
    """
    report = []
    for cfg in configs:
        chunks_by_doc = chunk_all_documents(manifest, cfg["target_words"], cfg["overlap_words"])
        all_chunks = [c for chunks in chunks_by_doc.values() for c in chunks]
        word_counts = [len(c.text.split()) for c in all_chunks]
        report.append({
            "target_words": cfg["target_words"],
            "overlap_words": cfg["overlap_words"],
            "total_chunks": len(all_chunks),
            "avg_chunk_words": round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
            "min_chunk_words": min(word_counts) if word_counts else 0,
            "max_chunk_words": max(word_counts) if word_counts else 0,
        })
    for row in report:
        print(f"  target={row['target_words']:<4} overlap={row['overlap_words']:<4} "
              f"-> {row['total_chunks']:>4} chunks, avg {row['avg_chunk_words']:>5} words "
              f"(min {row['min_chunk_words']}, max {row['max_chunk_words']})")
    return report


# ---------------------------------------------------------------------------
# Embeddings — traced so cost/latency is attributed, not a black box
# ---------------------------------------------------------------------------

@observe(name="embed_texts")
def embed_texts(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    client = _get_openai_client()
    embeddings: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        embeddings.extend([d.embedding for d in response.data])
    return embeddings


# ---------------------------------------------------------------------------
# ChromaDB — persistent, cosine distance, idempotent upserts
# ---------------------------------------------------------------------------

_collection = None


def get_chroma_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        _collection = client.get_or_create_collection(
            name="contracts", metadata={"hnsw:space": "cosine"}
        )
    return _collection


def build_index(manifest: List[DocumentRecord], chunks_by_doc: Dict[str, List[Chunk]],
                 batch_size: int = 100) -> Any:
    """
    Idempotent: re-running this with unchanged documents costs zero
    embedding calls, because each chunk's text_hash is compared against
    what's already stored before deciding to (re)embed it.
    """
    collection = get_chroma_collection()
    record_by_id = {r.doc_id: r for r in manifest}
    all_chunks = [c for chunks in chunks_by_doc.values() for c in chunks]
    all_ids = [c.chunk_id for c in all_chunks]

    existing_hashes: Dict[str, str] = {}
    if all_ids:
        try:
            existing = collection.get(ids=all_ids, include=["metadatas"])
            for cid, meta in zip(existing["ids"], existing["metadatas"]):
                if meta:
                    existing_hashes[cid] = meta.get("text_hash", "")
        except Exception:  # noqa: BLE001 - a fresh/empty collection has nothing to compare against
            pass

    to_embed = [c for c in all_chunks if existing_hashes.get(c.chunk_id) != c.text_hash]
    unchanged = len(all_chunks) - len(to_embed)
    print(f"{len(to_embed)} of {len(all_chunks)} chunk(s) need (re)embedding; "
          f"{unchanged} unchanged and skipped.")

    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i:i + batch_size]
        embeddings = embed_texts([c.text for c in batch])
        metadatas = []
        for c in batch:
            record = record_by_id.get(c.doc_id)
            metadatas.append({
                "doc_id": c.doc_id,
                "doc_version": c.doc_version,
                "category_key": c.category_key,
                "document_role": record.document_role.value if record else "unknown",
                "source_location_range": c.source_location_range,
                "chunk_index": c.chunk_index,
                "total_chunks": c.total_chunks,
                "text_hash": c.text_hash,
            })
        collection.upsert(
            ids=[c.chunk_id for c in batch],
            embeddings=embeddings,
            documents=[c.text for c in batch],
            metadatas=metadatas,
        )

    print(f"Index now has {collection.count()} chunk(s) total.")
    return collection


def verify_index_reload() -> int:
    """Completion-gate check: open a FRESH client (not the cached global) and
    confirm the persisted index survives a restart, as required."""
    global _collection
    _collection = None  # force a fresh PersistentClient, not the cached handle
    collection = get_chroma_collection()
    count = collection.count()
    print(f"Reopened index from disk: {count} chunk(s) found.")
    return count


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search(query: str, top_k: int = 5, category_key: Optional[str] = None,
           doc_id: Optional[str] = None, document_role: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns text, similarity score, document metadata, and the exact
    source_location_range for every result — nothing is returned without
    a way to trace it back to the original document."""
    collection = get_chroma_collection()
    query_embedding = embed_texts([query])[0]

    filters = {k: v for k, v in {
        "category_key": category_key, "doc_id": doc_id, "document_role": document_role,
    }.items() if v is not None}
    where = None
    if len(filters) == 1:
        where = filters
    elif len(filters) > 1:
        where = {"$and": [{k: v} for k, v in filters.items()]}

    kwargs: Dict[str, Any] = {"query_embeddings": [query_embedding], "n_results": top_k}
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)
    output = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        output.append({
            "chunk_id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "score": round(1 - results["distances"][0][i], 4),  # cosine distance -> similarity
            "doc_id": meta["doc_id"],
            "category_key": meta["category_key"],
            "document_role": meta["document_role"],
            "source_location_range": meta["source_location_range"],
        })
    return output


# ---------------------------------------------------------------------------
# Retrieval evaluation — a labeled test set, not spot-checks
# ---------------------------------------------------------------------------

_TEST_SET_TEMPLATE = [
    {"question": "", "category_focus": "liability", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "liability", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "liability", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "payment", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "payment", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "payment", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "termination", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "termination", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "termination", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "sla", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "sla", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "sla", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "confidentiality", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "confidentiality", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
    {"question": "", "category_focus": "confidentiality", "expected_doc_id": None, "expected_locator_contains": None, "notes": None},
]


def save_retrieval_test_set_template() -> Path:
    """
    Writes an EMPTY template for the 10-15 question test set the roadmap
    requires. You must fill 'question', 'expected_doc_id', and
    'expected_locator_contains' yourself by reading real documents — this
    can't be generated, or it isn't a real evaluation.
    """
    out_path = EVALUATIONS_ROOT / "phase3_retrieval_test_set.json"
    if out_path.exists():
        print(f"Already exists, not overwriting: {out_path}")
        return out_path
    out_path.write_text(json.dumps(_TEST_SET_TEMPLATE, indent=2), encoding="utf-8")
    print(f"Empty test-set template saved to: {out_path}")
    print("Fill in question/expected_doc_id/expected_locator_contains for each row "
          "by reading real documents before running evaluate_retrieval().")
    return out_path


# Draft questions only — plain text, not evidence. The doc_id/locator for
# each one still has to come from a human looking at the actual retrieved
# excerpt below and confirming it genuinely answers the question.
_DRAFT_QUESTIONS = {
    "liability": [
        "Is there a cap on the vendor's total liability under this agreement?",
        "What happens if the vendor's negligence causes damage to the client's property?",
        "Are consequential or indirect damages excluded under this contract?",
    ],
    "payment": [
        "What is the payment due date or payment term (e.g. net 30) under this agreement?",
        "What happens if an invoice is not paid on time — is there a late fee or interest charge?",
        "What is the total contract value or pricing structure described in this agreement?",
    ],
    "termination": [
        "Under what conditions can either party terminate this agreement for cause?",
        "What notice period is required to terminate the agreement without cause?",
        "What happens to outstanding obligations or fees upon termination?",
    ],
    "sla": [
        "What service level or uptime commitment does the vendor make?",
        "What remedy or credit applies if the vendor misses a service level target?",
        "How is service performance measured or reported under this agreement?",
    ],
    "confidentiality": [
        "How is confidential information defined under this agreement?",
        "How long do confidentiality obligations survive after the agreement ends?",
        "What exceptions exist to the confidentiality obligations (e.g. legally required disclosure)?",
    ],
}


def suggest_test_set_candidates(manifest: List[DocumentRecord], top_k: int = 3,
                                 excerpt_chars: int = 280) -> None:
    """
    For each draft question, runs real semantic search and prints the top
    candidates with a readable excerpt AND the actual filename (not just the
    doc_id code) so you can immediately tell which real file it is. You read
    the excerpt, decide whether it genuinely answers the question, and copy
    that result's doc_id/source_location_range into the test-set JSON
    yourself. This does not fill the file for you — it makes the manual
    step fast instead of a blind read of 36 documents.
    """
    filename_by_doc_id = {r.doc_id: r.filename for r in manifest}

    for category, questions in _DRAFT_QUESTIONS.items():
        print(f"\n{'=' * 70}\n{category.upper()}\n{'=' * 70}")
        for question in questions:
            print(f"\nQ: {question}")
            results = search(question, top_k=top_k)
            for r in results:
                excerpt = r["text"][:excerpt_chars].replace("\n", " ")
                filename = filename_by_doc_id.get(r["doc_id"], "unknown file")
                print(f"  [{r['score']:.3f}] {r['doc_id']:<10} ({filename}) "
                      f"@ {r['source_location_range']}")
                print(f"      {excerpt}...")


def load_retrieval_test_set() -> List[Dict[str, Any]]:
    path = EVALUATIONS_ROOT / "phase3_retrieval_test_set.json"
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_retrieval(test_set: List[Dict[str, Any]], top_k: int = 5) -> Dict[str, Any]:
    """Recall@k against the labeled test set: does the expected document
    (and, loosely, the expected clause locator) show up in the top-k results?"""
    filled = [q for q in test_set if q.get("question") and q.get("expected_doc_id")]
    if not filled:
        print("No filled-in test questions found — fill the template before evaluating.")
        return {"evaluated": 0}

    hits = 0
    rows = []
    for q in filled:
        results = search(q["question"], top_k=top_k)
        result_doc_ids = [r["doc_id"] for r in results]
        doc_hit = q["expected_doc_id"] in result_doc_ids
        locator_hit = None
        if doc_hit and q.get("expected_locator_contains"):
            matching = [r for r in results if r["doc_id"] == q["expected_doc_id"]]
            locator_hit = any(q["expected_locator_contains"] in r["source_location_range"] for r in matching)
        if doc_hit:
            hits += 1
        rows.append({
            "question": q["question"], "category_focus": q["category_focus"],
            "expected_doc_id": q["expected_doc_id"], "doc_hit": doc_hit, "locator_hit": locator_hit,
            "top_result_doc_ids": result_doc_ids,
        })

    recall_at_k = hits / len(filled)
    report = {"evaluated": len(filled), "top_k": top_k, "recall_at_k": round(recall_at_k, 3), "rows": rows}

    out_path = REPORTS_ROOT / "phase3_retrieval_eval.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Recall@{top_k}: {recall_at_k:.1%} ({hits}/{len(filled)})")
    for row in rows:
        mark = "✓" if row["doc_hit"] else "✗"
        print(f"  {mark} [{row['category_focus']}] {row['question'][:60]}")
    print(f"\nFull report saved to: {out_path}")
    return report
