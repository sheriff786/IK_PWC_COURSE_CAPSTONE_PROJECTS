"""
ContractIQ — Phase 2: Extract entities, normalize terms, analyze the corpus.

Roadmap reference: 02_Entity_Clause_and_EDA.ipynb

Guiding rule this module follows literally: "Keep semantic distinctions
separate: effective date, expiry date, renewal date, notice deadline,
invoice amount, and agreement value are not interchangeable." When the
surrounding text doesn't give enough context to tell them apart, the entity
is typed as the generic/unclassified form rather than guessed — ambiguous
stays ambiguous.
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import ENTITIES_ROOT, EVALUATIONS_ROOT, REPORTS_ROOT
from .ingestion import load_manifest
from .models import DocumentRecord, Entity, ParseStatus, SourceLocation
from .parsing import load_parsed_document

# ---------------------------------------------------------------------------
# Regex primitives (raw pattern matches — not yet semantically typed)
# ---------------------------------------------------------------------------

_DATE_PATTERN = re.compile(
    r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+)?"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    re.IGNORECASE,
)

_MONEY_PATTERN = re.compile(
    r"(?:US\$|USD|₹|INR|£|GBP|€|EUR|\$)\s?[\d,]+(?:\.\d{1,2})?(?:\s?(?:million|billion|k|K))?",
)

_PERCENT_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%")

_DURATION_PATTERN = re.compile(
    r"\b\d+\s*(?:calendar\s+)?(?:day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Context keywords used to disambiguate WHICH kind of date/amount was found.
# A match with no nearby keyword stays "unclassified_*" — never guessed.
# ---------------------------------------------------------------------------

_DATE_CONTEXT: Dict[str, List[str]] = {
    "effective_date": ["effective date", "commencement date", "shall commence"],
    "expiry_date": ["expiration date", "expiry date", "end date", "shall expire", "shall terminate on"],
    "renewal_date": ["renewal date", "renewed on", "automatically renew"],
    "notice_deadline": ["notice period", "written notice", "days notice", "days' notice", "prior notice"],
}

_MONEY_CONTEXT: Dict[str, List[str]] = {
    "invoice_amount": ["invoice", "amount due", "total due", "amount payable"],
    "agreement_value": ["contract value", "total contract value", "agreement value", "not to exceed"],
    "penalty_amount": ["penalty", "liquidated damages", "late fee"],
}

# Contract-specific term categories (rubric: "domain-specific entities beyond
# generic NER"). Each list is matched case-insensitively against clause text.
_CLAUSE_TERM_KEYWORDS: Dict[str, List[str]] = {
    "liability_terms": ["limitation of liability", "unlimited liability", "consequential damages",
                         "punitive damages", "liability cap", "aggregate liability"],
    "termination_language": ["terminate for convenience", "terminate for cause", "material breach",
                              "termination without cause", "right to terminate"],
    "sla_terms": ["service level agreement", "uptime", "response time", "resolution time",
                  "sla credit", "performance metric"],
    "confidentiality": ["confidential information", "non-disclosure", "nda", "trade secret"],
    "indemnification": ["indemnify", "indemnification", "hold harmless", "defend"],
    "ip_terms": ["intellectual property", "work product", "license grant", "patent", "copyright",
                 "trademark", "background ip", "foreground ip"],
}

# Rule-based risk indicators — preliminary signals only, NOT a final legal
# conclusion (roadmap guiding rule). Reused/extended from the risk-indicator
# concept, but now resolved to a specific clause's SourceLocation.
_RISK_INDICATORS: Dict[str, List[str]] = {
    "high_risk": ["unlimited liability", "sole discretion", "no cure period",
                  "automatic renewal", "perpetual license", "unilateral amendment"],
    "medium_risk": ["net 60", "net 90", "non-compete", "exclusivity", "most favored"],
    "favorable": ["mutual indemnification", "liability cap", "cure period", "termination for convenience"],
}


def _find_context_type(text: str, context_map: Dict[str, List[str]], window: str) -> str:
    """Returns the matching semantic type if a context keyword appears in
    `window` (usually the clause text itself, plus its heading), else
    'unclassified' — never a guess."""
    lowered = window.lower()
    for semantic_type, keywords in context_map.items():
        if any(kw in lowered for kw in keywords):
            return semantic_type
    text_lower = text.lower()
    for semantic_type, keywords in context_map.items():
        if any(kw in text_lower for kw in keywords):
            return semantic_type
    return "unclassified"


def extract_entities_from_clause(clause: Dict[str, Any]) -> List[Entity]:
    """Pulls typed entities and risk-indicator mentions out of one clause,
    every one linked back to that clause's exact SourceLocation."""
    text = clause["text"]
    heading = clause.get("heading") or ""
    context_window = f"{heading} {text}"
    loc = SourceLocation(**clause["source_location"])
    entities: List[Entity] = []

    for match in _DATE_PATTERN.finditer(text):
        entity_type = f"date:{_find_context_type(text, _DATE_CONTEXT, context_window)}"
        entities.append(Entity(entity_type=entity_type, raw_text=match.group(0),
                                normalized_value=None, source_location=loc))

    for match in _MONEY_PATTERN.finditer(text):
        entity_type = f"money:{_find_context_type(text, _MONEY_CONTEXT, context_window)}"
        entities.append(Entity(entity_type=entity_type, raw_text=match.group(0),
                                normalized_value=None, source_location=loc))

    for match in _PERCENT_PATTERN.finditer(text):
        entities.append(Entity(entity_type="percentage", raw_text=match.group(0),
                                normalized_value=None, source_location=loc))

    for match in _DURATION_PATTERN.finditer(text):
        entities.append(Entity(entity_type="duration_or_notice_period", raw_text=match.group(0),
                                normalized_value=None, source_location=loc))

    lowered = text.lower()
    for term_type, keywords in _CLAUSE_TERM_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                entities.append(Entity(entity_type=f"clause_term:{term_type}", raw_text=kw,
                                        normalized_value=None, source_location=loc))

    for level, phrases in _RISK_INDICATORS.items():
        for phrase in phrases:
            if phrase in lowered:
                entities.append(Entity(entity_type=f"risk_indicator:{level}", raw_text=phrase,
                                        normalized_value=None, source_location=loc))

    return entities


def _dedupe(entities: List[Entity]) -> List[Entity]:
    """Drops exact duplicates (same type + text + location) — same keyword
    can legitimately appear at two different clauses, that's kept; the same
    match found twice at the same location is not (rubric: 'deduplicated')."""
    seen: set = set()
    unique: List[Entity] = []
    for e in entities:
        key = (e.entity_type, e.raw_text, e.source_location.locator)
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def process_document(doc_id: str) -> Dict[str, Any]:
    """Extracts every entity for one already-parsed document."""
    parsed = load_parsed_document(doc_id)
    if parsed["parse_status"] != ParseStatus.PARSED.value:
        return {"doc_id": doc_id, "entities": [], "status": "skipped",
                "reason": f"parse_status={parsed['parse_status']}"}

    all_entities: List[Entity] = []
    for clause in parsed["clauses"]:
        all_entities.extend(extract_entities_from_clause(clause))
    all_entities = _dedupe(all_entities)

    word_count = sum(len(c["text"].split()) for c in parsed["clauses"])
    heading_count = sum(1 for c in parsed["clauses"] if c["is_heading"])

    return {
        "doc_id": doc_id,
        "status": "extracted",
        "entities": [json.loads(e.model_dump_json()) for e in all_entities],
        "clause_count": len(parsed["clauses"]),
        "table_count": len(parsed["tables"]),
        "word_count": word_count,
        "heading_count": heading_count,
    }


def save_entities(result: Dict[str, Any]) -> Path:
    out_path = ENTITIES_ROOT / f"{result['doc_id']}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return out_path


def run_phase2_full(manifest: List[DocumentRecord]) -> Dict[str, Dict[str, Any]]:
    """Runs entity extraction across every parsed document in the manifest."""
    results: Dict[str, Dict[str, Any]] = {}
    for record in manifest:
        result = process_document(record.doc_id)
        results[record.doc_id] = result
        if result["status"] == "extracted":
            save_entities(result)

    extracted = sum(1 for r in results.values() if r["status"] == "extracted")
    skipped = sum(1 for r in results.values() if r["status"] == "skipped")
    total_entities = sum(len(r["entities"]) for r in results.values())
    print(f"Phase 2 complete: {extracted} documents extracted, {skipped} skipped "
          f"(not successfully parsed in Phase 1), {total_entities} entities total.")
    if skipped:
        print("Skipped documents (fix in Phase 1 before relying on these for risk analysis):")
        for doc_id, r in results.items():
            if r["status"] == "skipped":
                print(f"  - {doc_id}: {r['reason']}")

    return results


# ---------------------------------------------------------------------------
# Corpus EDA
# ---------------------------------------------------------------------------

def _per_category_averages(manifest: List[DocumentRecord],
                            phase2_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Per-category averages for word/table/section/paragraph counts —
    the breakdown the single overall average hides."""
    category_of = {r.doc_id: r.category_key for r in manifest}
    buckets: Dict[str, Dict[str, List[float]]] = {}

    for doc_id, result in phase2_results.items():
        if result["status"] != "extracted":
            continue
        category = category_of.get(doc_id, "UNSPECIFIED")
        bucket = buckets.setdefault(category, {
            "word_count": [], "table_count": [], "section_count": [], "paragraph_count": [],
        })
        bucket["word_count"].append(result.get("word_count", 0))
        bucket["table_count"].append(result.get("table_count", 0))
        bucket["section_count"].append(result.get("heading_count", 0))
        bucket["paragraph_count"].append(result.get("clause_count", 0))

    return {
        category: {metric: round(sum(values) / len(values), 1) if values else 0.0
                   for metric, values in metrics.items()}
        for category, metrics in buckets.items()
    }


def build_eda_report(manifest: List[DocumentRecord],
                      phase2_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Category counts, parse success rate, entity distribution, per-category
    structure breakdown, and a 'missing key fields' check — every number here
    is counted directly from Phase 1/2 output, nothing estimated."""
    by_category: Counter = Counter(r.category_key for r in manifest)

    parsed_ok = sum(1 for r in phase2_results.values() if r["status"] == "extracted")
    parse_success_rate = parsed_ok / len(manifest) if manifest else 0.0

    entity_type_counts: Counter = Counter()
    for r in phase2_results.values():
        for e in r.get("entities", []):
            entity_type_counts[e["entity_type"]] += 1

    doc_lengths = {r["doc_id"]: r.get("word_count", 0) for r in phase2_results.values()
                   if r["status"] == "extracted"}
    table_counts = {r["doc_id"]: r.get("table_count", 0) for r in phase2_results.values()
                    if r["status"] == "extracted"}
    section_counts = {r["doc_id"]: r.get("heading_count", 0) for r in phase2_results.values()
                      if r["status"] == "extracted"}

    # Missing-field check: an assessed agreement with zero classified dates
    # is a real data-quality flag, not an error to hide.
    missing_effective_date = []
    for record in manifest:
        if record.document_role.value != "assessed_agreement":
            continue
        result = phase2_results.get(record.doc_id, {})
        has_effective_date = any(
            e["entity_type"] == "date:effective_date" for e in result.get("entities", [])
        )
        if not has_effective_date:
            missing_effective_date.append(record.doc_id)

    report = {
        "category_counts": dict(by_category),
        "parse_success_rate": round(parse_success_rate, 3),
        "documents_parsed_ok": parsed_ok,
        "documents_total": len(manifest),
        "entity_type_distribution": dict(entity_type_counts.most_common()),
        "avg_word_count": round(sum(doc_lengths.values()) / len(doc_lengths), 1) if doc_lengths else 0,
        "avg_table_count": round(sum(table_counts.values()) / len(table_counts), 1) if table_counts else 0,
        "avg_section_count": round(sum(section_counts.values()) / len(section_counts), 1) if section_counts else 0,
        "all_word_counts": list(doc_lengths.values()),
        "per_category_averages": _per_category_averages(manifest, phase2_results),
        "assessed_agreements_missing_effective_date": missing_effective_date,
    }

    out_path = REPORTS_ROOT / "phase2_eda_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"EDA report saved to: {out_path}")
    return report


def build_eda_dashboard(eda_report: Dict[str, Any], save_path: Optional[Path] = None) -> Path:
    """
    A 2x2 EDA dashboard: documents per category, word-count distribution,
    average document length by category, and average structure metrics
    (table/section/paragraph counts) by category — all pulled straight from
    build_eda_report()'s output, nothing recomputed or invented here.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Contract corpus exploratory data analysis", fontsize=15, fontweight="bold")

    # Panel 1: documents per category
    cat_counts = pd.Series(eda_report["category_counts"]).sort_values(ascending=True)
    axes[0, 0].barh(cat_counts.index, cat_counts.values, color="#4C72B0")
    axes[0, 0].set_title("Documents per category")
    axes[0, 0].set_xlabel("Number of documents")

    # Panel 2: word count distribution
    word_counts = eda_report.get("all_word_counts", [])
    if word_counts:
        axes[0, 1].hist(word_counts, bins=15, color="#F0997B", edgecolor="black")
        mean_wc = sum(word_counts) / len(word_counts)
        axes[0, 1].axvline(mean_wc, color="red", linestyle="--", label=f"Mean: {mean_wc:.0f}")
        axes[0, 1].legend()
    axes[0, 1].set_title("Word count distribution")
    axes[0, 1].set_xlabel("Word count")
    axes[0, 1].set_ylabel("Frequency")

    # Panel 3: average document length by category
    per_cat = eda_report.get("per_category_averages", {})
    avg_words = pd.Series({cat: metrics["word_count"] for cat, metrics in per_cat.items()}) \
        .sort_values(ascending=True)
    axes[1, 0].barh(avg_words.index, avg_words.values, color="#55A868")
    axes[1, 0].set_title("Average document length by category")
    axes[1, 0].set_xlabel("Average word count")

    # Panel 4: average structure metrics by category (heatmap)
    structure_df = pd.DataFrame({
        cat: {"table_count": m["table_count"], "section_count": m["section_count"],
              "paragraph_count": m["paragraph_count"]}
        for cat, m in per_cat.items()
    }).T
    if not structure_df.empty:
        sns.heatmap(structure_df, annot=True, fmt=".1f", cmap="YlOrRd", ax=axes[1, 1], cbar=True)
    axes[1, 1].set_title("Average structure metrics by category")

    plt.tight_layout()
    out_path = Path(save_path) if save_path else REPORTS_ROOT / "phase2_eda_dashboard.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Dashboard saved to: {out_path}")
    return out_path





def build_evaluation_fixture(phase2_results: Dict[str, Dict[str, Any]],
                              sample_size: int = 20, seed: int = 42) -> Path:
    """
    Samples entities across documents into a fixture for a human to review
    and mark correct/incorrect. This is a SCAFFOLD for the fixture, not a
    completed evaluation — 'reviewer_verdict' is left null for every row.
    Never fill this in programmatically; a fabricated verdict defeats the
    entire point of a human-reviewed evaluation set.
    """
    all_candidates: List[Dict[str, Any]] = []
    for doc_id, result in phase2_results.items():
        for e in result.get("entities", []):
            all_candidates.append({
                "doc_id": doc_id,
                "entity_type": e["entity_type"],
                "raw_text": e["raw_text"],
                "source_locator": e["source_location"]["locator"],
                "source_excerpt": e["source_location"].get("excerpt"),
                "reviewer_verdict": None,   # to be filled by a human: "correct" / "incorrect" / "ambiguous"
                "reviewer_notes": None,
            })

    random.seed(seed)
    sample = random.sample(all_candidates, min(sample_size, len(all_candidates)))

    out_path = EVALUATIONS_ROOT / "phase2_extraction_fixture.json"
    out_path.write_text(json.dumps(sample, indent=2), encoding="utf-8")
    print(f"Evaluation fixture ({len(sample)} rows, unreviewed) saved to: {out_path}")
    print("Open this file and fill in 'reviewer_verdict' for each row before Phase 7 uses it.")
    return out_path
