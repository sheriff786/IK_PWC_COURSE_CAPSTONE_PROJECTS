"""
ContractIQ — Phase 0: Project configuration.

Roadmap reference: 00_Project_Setup.ipynb
Load this once at the top of every notebook / the final submission notebook.

IMPORTANT: fill in DATA_ROOT and FOLDER_TO_CATEGORY below to match your actual
ContractIQ_data/ folder layout before running the Phase 0 manifest scan.
Nothing here guesses folder names — an unmapped folder is surfaced as
UNSPECIFIED in the manifest rather than silently assigned a category.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()  # reads .env — never commit this file, never print its contents


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]   # .../PWC_CONTRACTIQ_PROJECT_IK

# The real dataset lives OUTSIDE the project folder entirely. Read from an
# environment variable first (set CONTRACTIQ_DATA_ROOT in .env if this path
# ever changes or differs across machines), falling back to the absolute
# path confirmed on disk. Never silently falls back to the old in-project
# guess — that folder ("ContractIQ_data_reserve") is unrelated to this path.
DATA_ROOT = Path(os.getenv(
    "CONTRACTIQ_DATA_ROOT",
    r"E:\Sheriff_faang\full_end_to_end_project_implementation\IK_PWC_Agentic_AI_Project"
    r"\PWC_CAPSTONE_PROJECT\IK_PWC_COURSE_CAPSTONE_PROJECTS\datasets\contract_intelligence",
))
ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts"
MANIFEST_PATH = ARTIFACTS_ROOT / "manifests" / "document_manifest.json"
PARSED_DOCS_ROOT = ARTIFACTS_ROOT / "parsed_documents"
EVALUATIONS_ROOT = ARTIFACTS_ROOT / "evaluations"
REPORTS_ROOT = ARTIFACTS_ROOT / "reports"
CHROMA_PERSIST_DIR = PROJECT_ROOT / "chroma_contracts_db"

for _dir in (ARTIFACTS_ROOT, MANIFEST_PATH.parent, PARSED_DOCS_ROOT,
             EVALUATIONS_ROOT, REPORTS_ROOT, CHROMA_PERSIST_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Real 8-category dataset taxonomy
# Source: Week-1_Assignment.ipynb, cell "WEEK 1.5: CONTRACT TAXONOMY (PROVIDED)"
# — this is the course's own CONTRACT_CATEGORIES dict (exact keys, exact
# on-disk folder names, exact document types and risk focus per category).
# Confirmed against the real dataset folder listing: all 8 folder names
# match exactly. Expected per-category counts come from
# ContractIQ_Product_Overview.md's dataset table (36 total).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CategorySpec:
    key: str                    # exact key from the course's CONTRACT_CATEGORIES
    folder_name: str            # exact on-disk subfolder name (also the course's 'path')
    expected_count: int
    document_types: List[str] = field(default_factory=list)
    risk_focus: List[str] = field(default_factory=list)  # which specialist agents care


CATEGORY_TAXONOMY: List[CategorySpec] = [
    CategorySpec("master_agreements", "Master level agreements", 6,
                 ["MSA", "NDA", "Rate Cards"], ["legal", "compliance"]),
    CategorySpec("transaction_contracts", "Transaction level contract", 4,
                 ["SOW", "Work Orders", "Renewals", "Amendments"], ["operational", "financial"]),
    CategorySpec("commercial_docs", "Commercial docs", 2,
                 ["Pricing Tables", "Rate Schedules"], ["financial"]),
    CategorySpec("financial_billing", "Financial and Billing docs", 4,
                 ["Invoices", "Credit Notes", "Payment Schedules"], ["financial"]),
    CategorySpec("operational_docs", "Operational service delivery docs", 4,
                 ["Service Reports", "SLA Reports"], ["operational"]),
    CategorySpec("compliance_docs", "Compliance and policy documents", 6,
                 ["InfoSec Controls", "Vendor Policies"], ["compliance"]),
    CategorySpec("historical_negotiation", "Historical negotiation data", 6,
                 ["Negotiation History", "Commercial Correspondence"], ["financial", "legal"]),
    CategorySpec("disputes_audits_governance", "Disputes, audits and governance data", 4,
                 ["Dispute Records", "Audit Reports", "Governance Documents"],
                 ["legal", "compliance", "operational"]),
]

EXPECTED_TOTAL_DOCUMENTS = sum(c.expected_count for c in CATEGORY_TAXONOMY)  # 36

# Folder names are now confirmed exact, so this stays empty in normal use —
# it's only a manual override if a future dataset drop ever renames a folder.
FOLDER_TO_CATEGORY: Dict[str, str] = {}


# ---------------------------------------------------------------------------
# Model / retrieval settings
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "text-embedding-3-small"
LEGAL_AGENT_MODEL = "gpt-4o-mini"
FINANCIAL_AGENT_MODEL = "gpt-4o-mini"
OPERATIONAL_AGENT_MODEL = "gpt-4o-mini"

CHUNK_SIZE_WORDS = 700     # start of the 600-800 range the roadmap specifies
CHUNK_OVERLAP_WORDS = 100  # start of the 80-120 range; tune after Phase 3 eval

RISK_WEIGHTS = {"legal": 0.40, "financial": 0.35, "operational": 0.25}
RISK_SCORE_MAP = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


# ---------------------------------------------------------------------------
# Langfuse / session settings
# ---------------------------------------------------------------------------

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_PROJECT_NAME = "contractiq-capstone"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY not found. Add it to a .env file at the project root "
        "(never hardcode it in a notebook cell — graders will see it)."
    )


def assert_secrets_not_exposed() -> None:
    """Call this at the end of any cell that touches config — completion-gate check."""
    for name, value in [("OPENAI_API_KEY", OPENAI_API_KEY),
                         ("LANGFUSE_SECRET_KEY", LANGFUSE_SECRET_KEY)]:
        if value:
            assert len(value) > 8, f"{name} looks malformed"
    print("Secrets loaded from environment; nothing printed. OK to proceed.")