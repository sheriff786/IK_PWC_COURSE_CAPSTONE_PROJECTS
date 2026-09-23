"""
ContractIQ — Phase 1: Parse documents and preserve evidence.

Roadmap reference: 01_Data_Manifest_and_Parsing.ipynb

Guiding rules this module follows literally:
- Retain a stable location for every extract ('paragraph:14', 'table:2,row:4,cell:3').
- Handle malformed, empty, and unsupported documents without failing the whole batch.
- Save parsed JSON artifacts outside the original dataset directory.
- Run the parser across the full manifest only after initial docs are verified
  (see run_phase1_sample vs run_phase1_full below).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from .config import PARSED_DOCS_ROOT
from .models import ClauseRecord, DocumentRecord, ParseStatus, SourceLocation, TableRecord

# Heuristic only — flags a likely section marker so later phases can weight
# it, but never asserted as a legally meaningful boundary on its own.
_HEADING_KEYWORD_PATTERN = re.compile(
    r"^\s*(article|section|schedule|exhibit|appendix|clause)\s+([ivxlcdm]+|\d+(\.\d+)*)\b",
    re.IGNORECASE,
)


def _heading_hint(paragraph_style_name: str, text: str) -> Optional[str]:
    if paragraph_style_name and paragraph_style_name.lower().startswith("heading"):
        match = _HEADING_KEYWORD_PATTERN.match(text)
        return match.group(1).lower() if match else "heading"
    match = _HEADING_KEYWORD_PATTERN.match(text)
    return match.group(1).lower() if match else None


def parse_docx_document(record: DocumentRecord) -> Dict[str, Any]:
    """
    Parse one DOCX file into clause and table records.

    Never raises for a malformed/corrupt/unsupported file — returns a result
    dict with parse_status=FAILED/UNSUPPORTED_FORMAT and an empty
    clauses/tables list instead, so a batch run can continue past it.
    """
    filepath = Path(record.filepath)
    result: Dict[str, Any] = {
        "doc_id": record.doc_id,
        "clauses": [],
        "tables": [],
        "parse_status": ParseStatus.PENDING,
        "parse_error": None,
    }

    if filepath.suffix.lower() != ".docx":
        result["parse_status"] = ParseStatus.UNSUPPORTED_FORMAT
        result["parse_error"] = f"Phase 1 parser handles .docx only, got {filepath.suffix}"
        return result

    try:
        doc = Document(str(filepath))
    except (PackageNotFoundError, KeyError, ValueError, OSError) as exc:
        result["parse_status"] = ParseStatus.FAILED
        result["parse_error"] = f"Could not open as DOCX: {exc}"
        return result

    current_heading: Optional[str] = None
    clauses: List[ClauseRecord] = []

    try:
        for idx, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue  # empty paragraphs carry no evidence; skip, don't fabricate a clause

            hint = _heading_hint(paragraph.style.name if paragraph.style else "", text)
            is_heading = bool(paragraph.style and paragraph.style.name.lower().startswith("heading"))
            if is_heading:
                current_heading = text

            clauses.append(ClauseRecord(
                clause_id=f"{record.doc_id}-p{idx}",
                doc_id=record.doc_id,
                heading=current_heading if not is_heading else None,
                heading_hint=hint,
                is_heading=is_heading,
                text=text,
                source_location=SourceLocation(
                    doc_id=record.doc_id,
                    kind="paragraph",
                    locator=f"paragraph:{idx}",
                    excerpt=text,
                ),
            ))

        tables: List[TableRecord] = []
        for t_idx, table in enumerate(doc.tables):
            rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            tables.append(TableRecord(
                table_id=f"{record.doc_id}-t{t_idx}",
                doc_id=record.doc_id,
                table_index=t_idx,
                rows=rows,
                source_location=SourceLocation(
                    doc_id=record.doc_id,
                    kind="table",
                    locator=f"table:{t_idx}",
                    excerpt=None,  # a whole table has no single excerpt; use table_cell_location() below
                ),
            ))

    except Exception as exc:  # noqa: BLE001 - deliberately broad: a partial parse
        # failure must not crash the batch. Whatever was extracted before the
        # failure is kept; nothing after it is fabricated.
        result["parse_status"] = ParseStatus.FAILED
        result["parse_error"] = f"Parsing failed partway through: {exc}"
        result["clauses"] = [json.loads(c.model_dump_json()) for c in clauses]
        return result

    result["clauses"] = [json.loads(c.model_dump_json()) for c in clauses]
    result["tables"] = [json.loads(t.model_dump_json()) for t in tables]
    result["parse_status"] = ParseStatus.PARSED
    return result


def table_cell_location(table_record: TableRecord, row: int, col: int) -> SourceLocation:
    """A precise, citable pointer to one cell — e.g. for an agent quoting a
    specific payment amount. Built on demand rather than pre-generated for
    every cell, since most cells in a large table are never cited."""
    cell_text = table_record.rows[row][col]
    return SourceLocation(
        doc_id=table_record.doc_id,
        kind="table",
        locator=f"table:{table_record.table_index},row:{row},cell:{col}",
        excerpt=cell_text,
    )


def save_parsed_document(result: Dict[str, Any]) -> Path:
    out_path = PARSED_DOCS_ROOT / f"{result['doc_id']}.json"
    payload = dict(result)
    payload["parse_status"] = (
        payload["parse_status"].value
        if hasattr(payload["parse_status"], "value")
        else payload["parse_status"]
    )
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def load_parsed_document(doc_id: str) -> Dict[str, Any]:
    path = PARSED_DOCS_ROOT / f"{doc_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify_source_locations(result: Dict[str, Any], original_filepath: str) -> List[str]:
    """
    Completion-gate check: re-open the ORIGINAL document and confirm every
    clause's recorded text still matches what's actually at that paragraph
    index. Returns a list of mismatch descriptions — empty list means every
    extracted example is genuinely locatable in the source, as required.
    """
    mismatches: List[str] = []
    try:
        doc = Document(original_filepath)
    except Exception as exc:  # noqa: BLE001
        return [f"Could not re-open original document for verification: {exc}"]

    for clause in result["clauses"]:
        locator = clause["source_location"]["locator"]
        idx = int(locator.split(":")[1])
        if idx >= len(doc.paragraphs):
            mismatches.append(f"{clause['clause_id']}: paragraph {idx} no longer exists")
            continue
        actual_text = doc.paragraphs[idx].text.strip()
        if actual_text != clause["text"]:
            mismatches.append(
                f"{clause['clause_id']}: recorded text does not match paragraph {idx} "
                f"(recorded={clause['text'][:40]!r}, actual={actual_text[:40]!r})"
            )
    return mismatches


def run_phase1_sample(manifest: List[DocumentRecord], doc_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Parse only the given doc_ids — the roadmap's required first step before
    touching the full corpus. Verifies and prints a report for manual review."""
    by_id = {r.doc_id: r for r in manifest}
    results: Dict[str, Dict[str, Any]] = {}

    for doc_id in doc_ids:
        record = by_id.get(doc_id)
        if record is None:
            print(f"  {doc_id}: not found in manifest, skipping")
            continue

        result = parse_docx_document(record)
        results[doc_id] = result
        save_parsed_document(result)

        status = result["parse_status"]
        print(f"  {doc_id} ({record.filename}): {status} — "
              f"{len(result['clauses'])} clauses, {len(result['tables'])} tables")
        if result["parse_error"]:
            print(f"      note: {result['parse_error']}")

        if status == ParseStatus.PARSED:
            mismatches = verify_source_locations(result, record.filepath)
            if mismatches:
                print(f"      ⚠ {len(mismatches)} location mismatch(es):")
                for m in mismatches[:5]:
                    print(f"        - {m}")
            else:
                print("      ✓ every clause location verified against the source")

    return results


def run_phase1_full(manifest: List[DocumentRecord]) -> Dict[str, Dict[str, Any]]:
    """
    Parse the entire manifest. Only call this after run_phase1_sample has
    been manually reviewed and looks correct — per the roadmap's own gate.
    Failures are recorded per file and do not stop the batch.
    """
    results: Dict[str, Dict[str, Any]] = {}
    failed: List[str] = []
    unsupported: List[str] = []

    for record in manifest:
        result = parse_docx_document(record)
        results[record.doc_id] = result
        save_parsed_document(result)

        if result["parse_status"] == ParseStatus.FAILED:
            failed.append(f"{record.doc_id} ({record.filename}): {result['parse_error']}")
        elif result["parse_status"] == ParseStatus.UNSUPPORTED_FORMAT:
            unsupported.append(f"{record.doc_id} ({record.filename})")

    total_clauses = sum(len(r["clauses"]) for r in results.values())
    total_tables = sum(len(r["tables"]) for r in results.values())

    print(f"Parsed {len(results)} document(s): "
          f"{total_clauses} clauses, {total_tables} tables total.")
    if failed:
        print(f"\n{len(failed)} file(s) failed to parse:")
        for line in failed:
            print(f"  - {line}")
    if unsupported:
        print(f"\n{len(unsupported)} file(s) skipped (unsupported format, not .docx):")
        for line in unsupported:
            print(f"  - {line}")

    return results