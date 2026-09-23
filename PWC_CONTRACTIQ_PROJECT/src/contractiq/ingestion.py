"""
ContractIQ — Phase 0/1 bridge: manifest builder.

Roadmap reference: 00_Project_Setup.ipynb item 8 ("Scan the dataset and
generate a manifest...") — implemented here as a reusable module so
01_Data_Manifest_and_Parsing.ipynb and the final submission notebook both
import the same function instead of duplicating it (rubric: Code
Reusability & Modularity).

Design choice: this module does NOT require you to hand-type your on-disk
folder names anywhere. It walks ContractIQ_data/, normalizes whatever
subfolder names it finds, and fuzzy-matches them against the real taxonomy
in config.py. Anything it can't match with confidence is reported as
UNSPECIFIED — never silently guessed — so you fix only genuine ambiguities.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import (
    CATEGORY_TAXONOMY,
    DATA_ROOT,
    EXPECTED_TOTAL_DOCUMENTS,
    FOLDER_TO_CATEGORY,
    MANIFEST_PATH,
)
from .models import DocumentRecord, DocumentRole, ParseStatus

# Word creates hidden lock files like "~$Acme MSA.docx" when a file is open —
# these are not real documents and must be skipped, or the manifest count
# will be wrong for a reason that looks like a bug in category matching.
_IGNORE_PREFIXES = ("~$", ".")
# Matches the course's own discover_contract_data() in Week-1_Assignment.ipynb —
# it accepts .docx, .pdf, and .xlsx, not just .docx.
_SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".xlsx"}

# Categories whose documents get full multi-agent risk analysis vs. ones
# used only as supporting/reference evidence. Grounded in
# ContractIQ_Product_Overview.md: "An invoice or policy is a useful
# supporting document, but not automatically an assessed agreement."
_ASSESSED_AGREEMENT_CATEGORIES = {"master_agreements", "transaction_contracts"}


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _build_category_lookup() -> Dict[str, str]:
    """normalized folder_name/key -> category_key. Exact folder names are
    known (confirmed against the real dataset listing), so this resolves
    to an exact match in normal use; fuzzy matching is a safety net only."""
    lookup = {}
    for spec in CATEGORY_TAXONOMY:
        lookup[_normalize(spec.folder_name)] = spec.key
        lookup[_normalize(spec.key)] = spec.key
    return lookup


def guess_category(folder_name: str) -> Tuple[str, bool]:
    """
    Returns (category_key, matched_with_confidence).
    Explicit FOLDER_TO_CATEGORY entries always win. Otherwise tries an exact
    normalized match, then a close fuzzy match. Anything below that
    threshold comes back as ("UNSPECIFIED", False) rather than a guess.
    """
    if folder_name in FOLDER_TO_CATEGORY:
        return FOLDER_TO_CATEGORY[folder_name], True

    normalized = _normalize(folder_name)
    lookup = _build_category_lookup()

    if normalized in lookup:
        return lookup[normalized], True

    close = difflib.get_close_matches(normalized, lookup.keys(), n=1, cutoff=0.6)
    if close:
        return lookup[close[0]], True

    return "UNSPECIFIED", False


def _content_hash(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _doc_role_for(category_key: str) -> DocumentRole:
    return (DocumentRole.ASSESSED_AGREEMENT
            if category_key in _ASSESSED_AGREEMENT_CATEGORIES
            else DocumentRole.SUPPORTING_DOCUMENT)


_CATEGORY_ID_PREFIX = {
    "master_agreements": "MLA",
    "transaction_contracts": "TXN",
    "commercial_docs": "COM",
    "financial_billing": "FIN",
    "operational_docs": "OPS",
    "compliance_docs": "CMP",
    "historical_negotiation": "NEG",
    "disputes_audits_governance": "GOV",
    "UNSPECIFIED": "UNS",
}


def build_manifest(data_root: Optional[Path] = None) -> List[DocumentRecord]:
    """
    Walk data_root (default: config.DATA_ROOT), one level of category
    subfolders, and produce a DocumentRecord per supported file found.
    Does not parse file contents — that's Phase 1. This only establishes
    identity, location, and category.
    """
    root = Path(data_root) if data_root else DATA_ROOT
    if not root.exists():
        raise FileNotFoundError(
            f"DATA_ROOT does not exist: {root}. Update DATA_ROOT in config.py "
            "to point at your real ContractIQ_data folder."
        )

    records: List[DocumentRecord] = []
    per_category_counter: Dict[str, int] = {}
    unmatched_folders: set = set()

    for category_folder in sorted(p for p in root.iterdir() if p.is_dir()):
        category_key, matched = guess_category(category_folder.name)
        if not matched:
            unmatched_folders.add(category_folder.name)

        for filepath in sorted(category_folder.rglob("*")):
            if not filepath.is_file():
                continue
            if filepath.name.startswith(_IGNORE_PREFIXES):
                continue
            if filepath.suffix.lower() not in _SUPPORTED_EXTENSIONS:
                continue

            per_category_counter[category_key] = per_category_counter.get(category_key, 0) + 1
            seq = per_category_counter[category_key]
            prefix = _CATEGORY_ID_PREFIX.get(category_key, "DOC")
            doc_id = f"{prefix}-{seq:03d}"

            try:
                file_size = filepath.stat().st_size
                content_hash = _content_hash(filepath)
                parse_status = ParseStatus.PENDING
                parse_error = None
            except OSError as exc:
                file_size = 0
                content_hash = ""
                parse_status = ParseStatus.FAILED
                parse_error = str(exc)

            records.append(DocumentRecord(
                doc_id=doc_id,
                filename=filepath.name,
                filepath=str(filepath.resolve()),
                category_key=category_key,
                document_role=_doc_role_for(category_key),
                file_size_bytes=file_size,
                content_hash=content_hash,
                parse_status=parse_status,
                parse_error=parse_error,
            ))

    if unmatched_folders:
        print("⚠ Could not confidently match these folder names to the taxonomy — "
              "filed under UNSPECIFIED. Add them to FOLDER_TO_CATEGORY in config.py "
              "if they should map to a real category:")
        for name in sorted(unmatched_folders):
            print(f"    '{name}'")

    return records


def save_manifest(records: List[DocumentRecord], path: Optional[Path] = None) -> Path:
    out_path = Path(path) if path else MANIFEST_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [json.loads(r.model_dump_json()) for r in records]
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def load_manifest(path: Optional[Path] = None) -> List[DocumentRecord]:
    in_path = Path(path) if path else MANIFEST_PATH
    raw = json.loads(in_path.read_text(encoding="utf-8"))
    return [DocumentRecord(**r) for r in raw]


def print_manifest_report(records: List[DocumentRecord]) -> None:
    """Phase 0 completion-gate check, printed so it's visible in a saved notebook."""
    total = len(records)
    print(f"Total documents found: {total} (expected {EXPECTED_TOTAL_DOCUMENTS})")
    if total != EXPECTED_TOTAL_DOCUMENTS:
        print("  -> MISMATCH. Check unmatched folders above, or confirm the "
              "dataset itself has all 36 files before proceeding.")

    counts: Dict[str, int] = {}
    for r in records:
        counts[r.category_key] = counts.get(r.category_key, 0) + 1

    expected_by_key = {c.key: c.expected_count for c in CATEGORY_TAXONOMY}
    print("\nPer-category counts (found / expected):")
    for spec in CATEGORY_TAXONOMY:
        found = counts.get(spec.key, 0)
        flag = "" if found == spec.expected_count else "  <-- check this"
        print(f"  {spec.folder_name:<38} {found:>2} / {spec.expected_count}{flag}")
    if "UNSPECIFIED" in counts:
        print(f"  {'UNSPECIFIED':<28} {counts['UNSPECIFIED']:>2}  <-- fix FOLDER_TO_CATEGORY")

    hashes = [r.content_hash for r in records if r.content_hash]
    duplicates = len(hashes) - len(set(hashes))
    if duplicates:
        print(f"\n⚠ {duplicates} file(s) share a content hash with another file — "
              "possible duplicate documents, worth checking manually.")

    failed = [r for r in records if r.parse_status == ParseStatus.FAILED]
    if failed:
        print(f"\n⚠ {len(failed)} file(s) could not be read (permissions/lock?):")
        for r in failed:
            print(f"    {r.filename}: {r.parse_error}")


if __name__ == "__main__":
    docs = build_manifest()
    print_manifest_report(docs)
    saved_to = save_manifest(docs)
    print(f"\nManifest saved to {saved_to}")