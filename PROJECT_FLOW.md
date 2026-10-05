# ContractIQ Project Flow

This document outlines the complete flow of the ContractIQ agentic AI contract intelligence system, detailing how each component works together from raw document input to final risk assessment reports and knowledge graph generation.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Data Flow Overview](#data-flow-overview)
4. [Phase-by-Phase Breakdown](#phase-by-phase-breakdown)
   - [Phase 0: Project Setup & Manifest Generation](#phase-0-project-setup--manifest-generation)
   - [Phase 1: Document Parsing](#phase-1-document-parsing)
   - [Phase 2: Entity & Clause Extraction](#phase-2-entity--clause-extraction)
   - [Phase 3: Semantic Retrieval System](#phase-3-semantic-retrieval-system)
   - [Phase 4/5: Specialist Risk Agents](#phase-45-specialist-risk-agents)
   - [Phase 6: Knowledge Graph Construction](#phase-6-knowledge-graph-construction)
   - [Phase 7: Evaluation & Reporting](#phase-7-evaluation--reporting)
   - [Phase 8/9: Application Interface (Stubbed)](#phase-89-application-interface-stubbed)
5. [Key Components & Interactions](#key-components--interactions)
6. [Artifacts Generated](#artifacts-generated)
7. [How to Run the Project](#how-to-run-the-project)
8. [Dependencies](#dependencies)

---

## Project Overview
ContractIQ is an agentic AI system designed to analyze legal contracts for risk assessment. It processes DOCX files through a phased pipeline, incorporating:
- **Document understanding** (parsing, entity extraction)
- **Semantic search** (embeddings, ChromaDB, BM25)
- **Specialist AI agents** (Legal, Financial, Operational) that ground findings in retrieved evidence
- **Orchestration** for parallel agent execution and consensus building
- **Knowledge graph** to map contract relationships
- **Evaluation framework** with human-reviewed metrics and Langfuse tracing
- **Evidence-linked reporting** for transparency

The system follows a "show your evidence" paradigm: every finding must cite verifiable text from the source document.

## Directory Structure
```
IK_PWC_COURSE_CAPSTONE_PROJECTS/
│
├── .env                          # Environment variables (API keys)
├── .gitignore                    # Git ignore rules
├── LICENSE
├── README.md
├── requirements.txt              # Base requirements (ipykernel, rank_bm25)
├── temp_week5_validation.py      # Validation script
│
├── datasets/                     # Raw datasets (not modified by pipeline)
│   ├── contract_intelligence/    # Main dataset: 36 DOCX files in 8 categories
│   │   ├── Master level agreements/
│   │   ├── Transaction level contract/
│   │   ├── Commercial docs/
│   │   ├── Financial and Billing docs/
│   │   ├── Operational service delivery docs/
│   │   ├── Compliance and policy documents/
│   │   ├── Historical negotiation data/
│   │   └── Disputes, audits and governance data/
│   ├── ecommerce/
│   ├── healthcare/
│   └── regulatory_compliance/
│
├── PWC_CONTRACTIQ_PROJECT/       # Main project implementation
│   ├── src/
│   │   └── contractiq/           # Core Python package
│   │       ├── __init__.py
│   │       ├── config.py         # Configuration (paths, models, taxonomy)
│   │       ├── models.py         # Pydantic data models
│   │       ├── ingestion.py      # Manifest builder (Phase 0/1)
│   │       ├── parsing.py        # DOCX parser (Phase 1)
│   │       ├── extraction.py     # Entity/date/amount extractor (Phase 2)
│   │       ├── retrieval.py      # Chunking, embedding, search (Phase 3)
│   │       ├── agents.py         # Specialist risk agents (Phase 4/5)
│   │       ├── orchestration.py  # Parallel execution & consensus (Phase 5)
│   │       ├── graph.py          # Knowledge graph (Phase 6)
│   │       ├── evaluation.py     # Metrics aggregation (Phase 7)
│   │       ├── reporting.py      # Markdown report generation (Phase 7)
│   │       └── app_service.py    # Gradio/FastAPI adapter (stub, Phase 8/9)
│   │
│   ├── artifacts/                # Pipeline outputs (manifest, parsed docs, entities, reports)
│   │   ├── manifests/
│   │   ├── parsed_documents/
│   │   ├── entities/
│   │   ├── evaluations/
│   │   └── reports/
│   │
│   ├── chroma_contracts_db/      # ChromaDB vector store (Phase 3)
│   ├── tests/                    # Unit tests
│   └── setup_project_structure.py # One-time scaffolding script
│
└── PWC_CONTRACTIQ_PROJECT_IK/    # Course materials & assignments
    └── Research/
        ├── Week-1 Assignment.ipynb
        ├── Week-2 Assignment.ipynb
        ├── Week-3 Assignment.ipynb
        ├── Week-4 Assignment.ipynb
        ├── Week-5 Assignment.ipynb
        ├── Week-6 Assignment.ipynb
        ├── Week-7 Assignment.ipynb
        ├── Week-8 Assignment.ipynb
        ├── Backend_Implementation_Roadmap.md
        ├── ContractIQ_Notebook_Analysis.md
        ├── ContractIQ_Project_Execution_Roadmap.md
        ├── contract_eda.png
        ├── contract_knowledge_graph.html
        ├── contract_knowledge_graph.png
        └── Langfuse_Setup_Guide.docx.pdf
```
## Data Flow Overview
```mermaid
flowchart TD
    A[Raw DOCX Contracts] --> B[Phase 0/1: Manifest Builder]
    B --> C[Document Manifest JSON]
    C --> D[Phase 1: DOCX Parser]
    D --> E[Parsed Clause/Table Artifacts]
    E --> F[Phase 2: Entity Extractor]
    F --> G[Entity Extractions JSON]
    G --> H[Phase 3: Retrieval System]
    H --> I[Chunks & Embeddings]
    I --> J[ChromaDB Vector Store]
    J --> K[BM25 Index]
    K --> L[Hybrid Search Capability]
    L --> M[Phase 4/5: Specialist Agents]
    M --> N[Legal Agent Findings]
    M --> O[Financial Agent Findings]
    M --> P[Operational Agent Findings]
    N --> Q[Phase 5: Orchestration & Consensus]
    O --> Q
    P --> Q
    Q --> R[Assessment JSON (per document)]
    R --> S[Phase 6: Knowledge Graph Builder]
    R --> T[Phase 7: Evaluation & Reporting]
    S --> U[Knowledge Graph (NetworkX/PyVis)]
    T --> V[Evaluation Report JSON]
    T --> W[Evidence-Linked Markdown Reports]
    style A fill:#f9f,stroke:#333
    style W fill:#bbf,stroke:#333
```

---

## Phase-by-Phase Breakdown

### Phase 0: Project Setup & Manifest Generation
**Purpose:** Scan the dataset, create a manifest of all documents with metadata, and set up the project structure.

**Key Component:** `src/contractiq/ingestion.py`
- Walks `datasets/contract_intelligence/` to find supported files (.docx, .pdf, .xlsx)
- Normalizes folder names and matches against the predefined taxonomy in `config.py`
- Assigns each document a UUID-based `doc_id`, category, and role (assessed agreement vs. supporting)
- Computes file hashes for deduplication
- Outputs: `artifacts/manifests/document_manifest.json`

**Process:**
1. Execute `python src/contractiq/ingestion.py` (or run the relevant cell in Week-1 notebook)
2. Manifest includes: `doc_id`, `filename`, `filepath`, `category_key`, `document_role`, `file_size_bytes`, `content_hash`, `parse_status`, `parse_error`
- Completion gate: Verify 36 documents found, match expected counts per category
### Phase 1: Document Parsing
**Purpose:** Convert raw DOCX files into structured clause and table records while preserving evidence locations.

**Key Component:** `src/contractiq/parsing.py`
- Uses `python-docx` to parse DOCX files
- Extracts paragraphs as clauses and tables as table records
- Preserves source locations: `paragraph:X`, `table:Y,row:Z,cell:W`
- Handles malformed documents gracefully (doesn't fail the batch)
- Saves parsed JSON artifacts to `artifacts/parsed_documents/{doc_id}.json`

**Key Rules:**
- Retain stable location for every extract
- Never invent clauses from empty paragraphs
- Save artifacts outside original dataset

**Output Artifact Structure:**
```json
{
  "doc_id": "UUID",
  "clauses": [
    {
      "clause_id": "{doc_id}-p{index}",
      "doc_id": "...",
      "text": "clause text",
      "heading": "current section heading",
      "heading_hint": "detected heading keyword",
      "source_location": {
        "locator": "paragraph:14",
        "excerpt": "text snippet",
        "document_id": "..."
      }
    }
  ],
  "tables": [...],
  "parse_status": "PARSED|FAILED|UNSUPPORTED_FORMAT",
  "parse_error": null or error message
}
```

### Phase 2: Entity & Clause Extraction
**Purpose:** Extract typed entities (dates, amounts, parties, etc.) and analyze the corpus for EDA.

**Key Component:** `src/contractiq/extraction.py`
- Uses regex patterns for primitives (dates, money, percentages, durations)
- Applies context keywords to disambiguate types (e.g., "effective date" vs. "expiry date")
- Extracts contract-specific terms (liability, termination, SLA, confidentiality)
- Performs entity normalization (e.g., "Jan 5, 2023" → "2023-01-05")
- Builds entity fixture for human review (`artifacts/evaluations/phase2_extraction_fixture.json`)
- Generates EDA dashboard (`artifacts/reports/phase2_eda_dashboard.png`)

**Key Rules:**
- Keep semantic distinctions separate (effective vs. expiry date)
- Never guess ambiguous entities; leave as `unclassified_*`
- All extractions must be traceable to source location

**Output:**
- Entities JSON per document: `artifacts/entities/{doc_id}.json`
- Contains lists of entities with: `entity_type`, `raw_text`, `normalized_value`, `confidence`, `source_location`

### Phase 3: Semantic Retrieval System
**Purpose:** Build a hybrid search system (dense + sparse) over contract clauses for evidence retrieval.

**Key Component:** `src/contractiq/retrieval.py`
- **Chunking:** Groups whole clauses into chunks (600-800 words) without splitting clauses
- **Embedding:** Uses OpenAI `text-embedding-3-small` to create dense vectors
- **Storage:** 
  - Dense vectors in ChromaDB (persistent directory: `chroma_contracts_db/`)
  - Sparse vectors (BM25) pickled alongside ChromaDB
- **Idempotency:** Skips re-embedding if chunk hash unchanged
- **Search:** Returns text, score, document metadata, AND source locations
- **Hybrid Search:** Combines dense (ChromaDB) and sparse (BM25) scores with RRF

**Key Rules:**
- Chunks preserve clause boundaries
- Measure before trusting chunk size/overlap (guided by Phase 3 notebook)
- Every search result traceable to original document location

**Output:**
- ChromaDB collection: `contractiq_chunks`
- BM25 index: `artifacts/reports/bm25_index.pkl`
- Chunk records: stored in ChromaDB metadata
- Test set template: `artifacts/evaluations/phase3_retrieval_test_set.json` (for human labeling)

### Phase 4/5: Specialist Risk Agents
**Purpose:** Deploy three evidence-grounded AI agents (Legal, Financial, Operational) to identify risks in contracts.

**Key Components:** 
- `src/contractiq/agents.py` - Agent logic (shared retrieval + LLM engine)
- `src/contractiq/orchestration.py` - Parallel execution & consensus building

**Agent Architecture:**
- Each agent uses the same pipeline:
  1. **Retrieval:** Query ChromaDB with specialist-specific questions (see below)
  2. **LLM Analysis:** Prompt GPT-4o-mini with retrieved chunks and system prompt
  3. **Verification:** Re-check LLM-generated quotes against source chunk text
  4. **Finding Building:** Create `Finding` objects with evidence, confidence, verification status

**Specialist Topics:**
- **Legal:** Indemnification, liability cap, confidentiality, IP, audit rights, etc.
- **Financial:** Payment terms, late fees, invoicing, penalties, renewal fees
- **Operational:** Service levels, response times, penalties, reporting requirements

**Evidence Grounding Rule:**
- Every Finding must quote text that *verbatim appears* in the retrieved chunk
- If quote doesn't match → `FAILED_VERIFICATION` (confidence capped)
- Never let LLM invent clauses

**Output per Agent:**
- DimensionResult per document: `artifacts/evaluations/{dimension}_{doc_id}.json`
- Contains: findings, success flag, error, retry count
**Orchestration Details (Phase 5):**
- **Sequential Run:** Executes Legal → Financial → Operational agents one after another (for debugging)
- **Parallel Run:** Executes all three agents concurrently (thread pool for I/O-bound OpenAI calls)
- **Consensus Logic:**
  - Any `CRITICAL` finding in any dimension → overall risk = `CRITICAL`
  - Otherwise, weighted average of scores (Legal: 40%, Financial: 35%, Operational: 25%)
  - Consensus actions generated for HIGH/CRITICAL findings
- **Assessment Model:** Combines dimension results into a full `Assessment` with:
  - Assessment ID, run ID, document version
  - Model/prompt/policy versions
  - Dimension results, unresolved issues, consensus actions
  - Overall risk severity
- **Output:**
  - Assessment JSON per document: `artifacts/reports/phase5_assessment_{doc_id}.json`

### Phase 6: Knowledge Graph Construction
**Purpose:** Build a verified relationship graph between contracts based on textual evidence.

**Key Component:** `src/contractiq/graph.py`
- **Node Types:** 
  - `document` (each contract)
  - `category` (contract taxonomy)
  - `party` (organizations like "PrimeVolta Hardware Solutions")
  - `external_reference` (agreements not in corpus)
- **Edges:** Only added if evidence exists in a document's *own* parsed text
  - Examples: "This agreement renews [External Agreement]", "Per Section 5.2 of [Other Contract]"
  - Adversarial check: No edges from filename similarity or boilerplate party names alone
- **Evidence Tracking:** Every edge stores:
  - Relation type (e.g., RENEWS, AMENDS)
  - Evidence IDs (list of finding/assessment IDs that support it)
  - Verification status
  - Source locator (paragraph/table reference)
- **Visualization:** 
  - Static: `artifacts/reports/phase6_contract_knowledge_graph.png` (Matplotlib/NetworkX)
  - Interactive: `artifacts/reports/phase6_contract_knowledge_graph.html` (PyVis, if installed)

**Key Rule:** 
- Every edge must be backed by real evidence from a document's OWN parsed text
- Never inferred from metadata or superficial similarities

### Phase 7: Evaluation & Reporting
**Purpose:** Measure system performance with human-reviewed metrics and generate final reports.

**Key Components:**
- `src/contractiq/evaluation.py` - Aggregates metrics from earlier phases
- `src/contractiq/reporting.py` - Generates Markdown reports from Assessments

**Evaluation Metrics (human-reviewed where applicable):**
1. **Parse Success Rate** - % of documents parsed correctly (from parsed artifacts)
2. **Entity Accuracy** - From human-reviewed Phase 2 fixture (null if not reviewed)
3. **Retrieval Relevance** - Recall@k from human-labeled Phase 3 test set
4. **Citation Validity & Finding Support** - % of agent quotes that verify against source
5. **Partial Run Frequency** - How often phases re-run unnecessarily
6. **Schema Failure Rate** - % of LLM outputs that fail Pydantic validation
7. **API Call Failure Rate** - % of OpenAI/Langfuse calls that error
8. **Cost & Latency by Stage** - Real token/latency numbers from LLM call log
9. **Important Missed Risk Rate** - Limitation: requires hand-authored risk checklist (not yet built)

**Output:**
- Evaluation report: `artifacts/reports/phase7_evaluation_report.json`
- Per-document Markdown reports: `artifacts/reports/phase7_report_{doc_id}.md`
  - Includes: overall risk, assessment metadata, specialist statuses, findings (with evidence), unresolved issues, consensus actions

**Reporting Rules:**
- Builds reports *only* from already-saved, verified Assessments (no re-running agents)
- Every finding retains its `evidence_ids` and `verification_status`
- Reports carry document/model/prompt/policy version + run_id for reproducibility

### Phase 8/9: Application Interface (Stubbed)
**Purpose:** Provide a user interface for interacting with the ContractIQ system.

**Key Component:** `src/contractiq/app_service.py` (currently a stub)
- **Intended Functionality:**
  - Gradio interface for document upload/query
  - FastAPI backend for programmatic access
  - Would allow users to:
    1. Upload a contract
    2. Run the full pipeline (or selected phases)
    3. View risk assessment and knowledge graph
    4. Generate reports
- **Current State:** Contains only a docstring; implementation left as final course exercise
## Key Components & Interactions

### Core Data Flow
1. **Ingestion** → Manifest (document metadata)
2. **Parsing** → Clause/Table artifacts (structured DOCX)
3. **Extraction** → Entity artifacts (typed entities)
4. **Retrieval** → Chunks + Embeddings + Indexes (searchable knowledge base)
5. **Agents** → Findings (risk evidence with verification)
6. **Orchestration** → Assessments (consolidated risk per document)
7. **Graph** → Knowledge Graph (contract relationships)
8. **Evaluation** → Metrics report (system performance)
9. **Reporting** → Human-readable reports (per document)

### Critical Interactions
- **Agents ↔ Retrieval:** Agents call `search()` with specialist questions to get evidence chunks
- **Orchestration ↔ Agents:** Orchestration runs agents (sequential/parallel) and saves their outputs
- **Graph ↔ Agents/Assessments:** Graph uses Assessment evidence IDs to verify edges; may also ingest agent findings as evidence
- **Evaluation ↔ All Phases:** Pulls artifacts from each phase to compute metrics (no re-computation)
- **Reporting ↔ Orchestration:** Loads phase5_assessment_*.json files to generate Markdown reports

### Evidence Traceability
```
Raw Document 
    → Parsing (clause: "paragraph:14") 
    → Extraction (entity from that clause) 
    → Retrieval (chunk containing that clause) 
    → Agent (quotes text from chunk) 
    → Verification (check quote matches chunk text) 
    → Finding (evidence_ids point to chunk) 
    → Assessment (collects findings) 
    → Report (shows evidence excerpt with location)
```

## Artifacts Generated
| Artifact Location | Description |
|-------------------|-------------|
| `artifacts/manifests/document_manifest.json` | List of all documents with metadata |
| `artifacts/parsed_documents/{doc_id}.json` | Parsed clauses/tables per document |
| `artifacts/entities/{doc_id}.json` | Extracted entities per document |
| `artifacts/evaluations/phase2_extraction_fixture.json` | Human-reviewed entity fixture (for accuracy metric) |
| `artifacts/evaluations/phase3_retrieval_test_set.json` | Human-labeled retrieval test set (for relevance metric) |
| `chroma_contracts_db/` | ChromaDB vector store of contract chunks |
| `artifacts/reports/bm25_index.pkl` | BM25 sparse index for hybrid search |
| `artifacts/evaluations/{dimension}_{doc_id}.json` | Agent findings per dimension per document |
| `artifacts/reports/phase5_assessment_{doc_id}.json` | Full risk assessment per document |
| `artifacts/reports/phase6_contract_knowledge_graph.png/.html` | Knowledge graph visualizations |
| `artifacts/reports/phase7_evaluation_report.json` | System performance metrics |
| `artifacts/reports/phase7_report_{doc_id}.md` | Evidence-linked Markdown report per document |

## How to Run the Project
The project is designed to be run via Jupyter notebooks in order. Follow these steps:

1. **Setup Environment**
   ```bat
   cd E:\Sheriff_faang\full_end_to_end_project_implementation\IK_PWC_Agentic_AI_Project\PWC_CAPSTONE_PROJECT\IK_PWC_COURSE_CAPSTONE_PROJECTS
   .\.venv-1\Scripts\activate   # or .venv if using the other env
   ```

2. **Verify Environment Variables**
   - Edit `.env` (create if missing) with:
     ```
     OPENAI_API_KEY="your-openai-key"
     LANGFUSE_SECRET_KEY="your-langfuse-secret"
     LANGFUSE_PUBLIC_KEY="your-langfuse-public"
     LANGFUSE_HOST="https://us.cloud.langfuse.com"
     ```

3. **Initialize Project Structure** (run once)
   ```bat
   cd PWC_CONTRACTIQ_PROJECT
   python setup_project_structure.py
   ```
   - **Note:** The script will tell you to manually copy `config.py`, `models.py`, and `ingestion.py` if they already exist (to prevent overwriting). In a fresh clone, these files are created as stubs; you should replace them with the provided versions from the course materials (they are already present in the repository after cloning).

4. **Run the Notebooks Sequentially**
   - Open and execute all cells in:
     ```
     PWC_CONTRACTIQ_PROJECT_IK\Research\Week-1 Assignment.ipynb
     PWC_CONTRACTIQ_PROJECT_IK\Research\Week-2 Assignment.ipynb
     ...
     PWC_CONTRACTIQ_PROJECT_IK\Research\Week-8 Assignment.ipynb
     ```
   - Each notebook includes:
     - Explanation of the phase
     - Code to implement (often TODOs to fill)
     - Completion-gate checks (e.g., `assert_secrets_not_exposed()`, manifest validation)
     - Instructions to save outputs to correct locations

5. **Optional: Run Manifest Builder Standalone**
   ```bat
   python src/contractiq/ingestion.py
   ```
   - Useful for regenerating the manifest if dataset changes.

> **Important:** The system is designed to be incremental. Each phase builds on artifacts from the previous phase. Skipping phases or deleting intermediate artifacts will break later phases.

## Dependencies
While `requirements.txt` only lists `ipykernel` and `rank_bm25`, the full set of dependencies (installed in the virtual environment) includes:

- **Core:** 
  - `openai>=1.0.0`
  - `chromadb>=0.4.0`
  - `langfuse>=2.0.0`
  - `python-dotenv>=1.0.0`
  - `pydantic>=2.0.0`
- **NLP/ML:**
  - `rank-bm25>=0.2.0`
  - `scikit-learn>=1.0.0`
  - `tiktoken>=0.5.0`
- **Document Processing:**
  - `python-docx>=1.0.0`
- **Data Analysis:**
  - `pandas>=2.0.0`
  - `numpy>=1.24.0`
- **Visualization:**
  - `matplotlib>=3.7.0`
  - `seaborn>=0.12.0`
  - `networkx>=3.0`
  - `pyvis>=0.3.2` (optional, for interactive graph)
- **Testing/Utilities:**
  - `pytest>=7.0.0`
  - `pytest-cov>=4.0.0`

**Note:** Versions are approximate; the course environment likely uses specific pinned versions. The virtual environments (`.venv`, `.venv-1`) should already contain all necessary packages.

---
*This document reflects the structure and flow of the ContractIQ capstone project as implemented in the provided codebase.*