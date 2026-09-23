"""
ContractIQ — Phase 0: Shared Pydantic records.

Roadmap reference: 00_Project_Setup.ipynb, item 6.
Every later phase imports these instead of redefining ad-hoc dicts, so a
finding created in Phase 4 and a graph edge created in Phase 6 speak the
same schema.

Design rule carried through every model: a field that cannot be backed by
real evidence is Optional and defaults to None / "insufficient_evidence" —
never a placeholder value that looks like real data.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums shared across models
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"                    # evidence span checked against source text
    UNVERIFIED = "unverified"                # produced but not yet checked
    FAILED_VERIFICATION = "failed_verification"  # checked and evidence did NOT match


class ParseStatus(str, Enum):
    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"
    UNSUPPORTED_FORMAT = "unsupported_format"


class DocumentRole(str, Enum):
    ASSESSED_AGREEMENT = "assessed_agreement"   # MSA/SOW/NDA — gets full risk analysis
    SUPPORTING_DOCUMENT = "supporting_document"  # invoice, policy, etc. — reference only


class RiskDimension(str, Enum):
    LEGAL = "legal"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"


# ---------------------------------------------------------------------------
# Evidence primitives
# ---------------------------------------------------------------------------

class SourceLocation(BaseModel):
    """A stable, re-locatable pointer into the original document."""
    doc_id: str
    kind: str = Field(description="'paragraph', 'table', or 'section'")
    locator: str = Field(description="e.g. 'paragraph:14' or 'table:2,row:4,cell:3'")
    excerpt: Optional[str] = Field(
        default=None,
        description="The exact source text at this location, for verification"
    )


class Entity(BaseModel):
    entity_type: str = Field(description="e.g. 'monetary_value', 'party', 'effective_date'")
    raw_text: str
    normalized_value: Optional[str] = Field(
        default=None,
        description="Normalized form, e.g. ISO date. None if normalization is ambiguous."
    )
    source_location: SourceLocation

class ClauseRecord(BaseModel):
    """One paragraph-level unit of a parsed document, with the heading that
    governs it (if any) and its exact source location. Phase 1 output."""
    clause_id: str
    doc_id: str
    doc_version: str = "1"
    heading: Optional[str] = Field(
        default=None, description="Nearest preceding heading/section title, if detected"
    )
    heading_hint: Optional[str] = Field(
        default=None, description="'article', 'section', 'schedule', 'exhibit', 'appendix', "
                                   "or None — a heuristic guess, not an assertion"
    )
    is_heading: bool = False
    text: str
    source_location: SourceLocation


class TableRecord(BaseModel):
    """One table from a parsed document, rows preserved as-is (no flattening
    into prose) so meaningful cell values survive. Phase 1 output."""
    table_id: str
    doc_id: str
    doc_version: str = "1"
    table_index: int
    rows: List[List[str]]
    source_location: SourceLocation
    
class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_version: str = "1"
    category_key: str
    text: str
    text_hash: str
    source_location_range: str = Field(description="e.g. 'paragraph:10-paragraph:18'")
    chunk_index: int
    total_chunks: int


# ---------------------------------------------------------------------------
# Document manifest record (Phase 0 output)
# ---------------------------------------------------------------------------

class DocumentRecord(BaseModel):
    doc_id: str = Field(description="Stable ID, e.g. 'MLA-001'")
    filename: str
    filepath: str
    category_key: str = Field(description="Key from CATEGORY_TAXONOMY, or 'UNSPECIFIED'")
    document_role: DocumentRole = DocumentRole.SUPPORTING_DOCUMENT
    file_size_bytes: int
    content_hash: str
    parse_status: ParseStatus = ParseStatus.PENDING
    parse_error: Optional[str] = None
    scanned_at: datetime = Field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Findings and assessments (Phase 4-5 output)
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    finding_id: str
    dimension: RiskDimension
    severity: Severity
    title: str
    rationale: str
    recommendation: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list, description="Chunk/SourceLocation IDs cited")
    evidence_excerpts: List[str] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: float = Field(ge=0.0, le=1.0)


class DimensionResult(BaseModel):
    dimension: RiskDimension
    success: bool
    findings: List[Finding] = Field(default_factory=list)
    error: Optional[str] = None
    retry_count: int = 0


class Assessment(BaseModel):
    assessment_id: str
    doc_id: str
    run_id: str
    document_version: str = "1"
    model_version: str
    prompt_version: str
    policy_version: str
    dimension_results: List[DimensionResult]
    unresolved_issues: List[str] = Field(default_factory=list)
    consensus_actions: List[str] = Field(default_factory=list)
    overall_risk: Severity
    created_at: datetime = Field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Knowledge graph edge (Phase 6 output)
# ---------------------------------------------------------------------------

class GraphEdge(BaseModel):
    source: str
    relation: str = Field(description="GOVERNS, AMENDS, RENEWS, REFERENCES, BELONGS_TO, "
                                       "CONTAINS, ADDRESSES, or MITIGATES")
    target: str
    evidence_ids: List[str] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
