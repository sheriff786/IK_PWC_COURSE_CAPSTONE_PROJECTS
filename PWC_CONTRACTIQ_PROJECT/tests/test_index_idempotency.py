"""
Phase 7, roadmap item 7: index-idempotency test.

build_index() must compare each chunk's text_hash against what's already
stored before deciding to (re)embed it. Uses a fake in-memory collection
and a monkeypatched embed_texts, so this runs with NO OpenAI/ChromaDB
network calls and NO API credits required.
"""

from contractiq import retrieval
from contractiq.models import Chunk


class _FakeCollection:
    def __init__(self):
        self.store = {}  # id -> metadata dict

    def get(self, ids, include=None):
        found_ids, metadatas = [], []
        for cid in ids:
            if cid in self.store:
                found_ids.append(cid)
                metadatas.append(self.store[cid])
        return {"ids": found_ids, "metadatas": metadatas}

    def upsert(self, ids, embeddings, documents, metadatas):
        for cid, meta in zip(ids, metadatas):
            self.store[cid] = meta

    def count(self):
        return len(self.store)


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id="TEST", doc_version="1", category_key="test",
                 text=text, text_hash=retrieval._text_hash(text),
                 source_location_range="paragraph:1", chunk_index=0, total_chunks=1)


def test_unchanged_chunks_are_not_re_embedded(monkeypatch):
    fake = _FakeCollection()
    monkeypatch.setattr(retrieval, "get_chroma_collection", lambda: fake)

    embed_calls = []
    monkeypatch.setattr(retrieval, "embed_texts", lambda texts, **kw: embed_calls.append(texts) or [[0.0]] * len(texts))

    chunks_by_doc = {"TEST": [_chunk("TEST-c0", "Original text.")]}
    record = type("R", (), {"doc_id": "TEST", "document_role": type("D", (), {"value": "supporting_document"})()})()

    retrieval.build_index([record], chunks_by_doc)
    assert len(embed_calls) == 1, "first index build should embed the new chunk exactly once"

    # Re-run with the SAME text -- text_hash is unchanged, so no new embedding call.
    retrieval.build_index([record], chunks_by_doc)
    assert len(embed_calls) == 1, "unchanged chunk was re-embedded -- idempotency broken"


def test_changed_chunk_text_triggers_re_embedding(monkeypatch):
    fake = _FakeCollection()
    monkeypatch.setattr(retrieval, "get_chroma_collection", lambda: fake)

    embed_calls = []
    monkeypatch.setattr(retrieval, "embed_texts", lambda texts, **kw: embed_calls.append(texts) or [[0.0]] * len(texts))

    record = type("R", (), {"doc_id": "TEST", "document_role": type("D", (), {"value": "supporting_document"})()})()

    retrieval.build_index([record], {"TEST": [_chunk("TEST-c0", "Original text.")]})
    retrieval.build_index([record], {"TEST": [_chunk("TEST-c0", "Edited text — content actually changed.")]})

    assert len(embed_calls) == 2, "changed chunk text must trigger re-embedding"
