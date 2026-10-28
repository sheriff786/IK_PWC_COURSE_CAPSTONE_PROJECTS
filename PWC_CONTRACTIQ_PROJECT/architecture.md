# ContractIQ – End‑to‑End Architecture

> **Goal** – Multi‑agent contract risk intelligence.  
> Every finding is **evidence‑grounded**, **independently verified** against source text, and **traceable** from UI/API back to the original clause.

---

## 1. High‑level Flow (Mermaid)

```mermaid
flowchart TD
    %% Data ingestion
    A[Data Corpus (ContractIQ_data/)] --> B[Ingestion (manifest builder)]
    B --> C[Manifest JSON (doc_id, category, hash, parse_status)]

    %% Parsing
    C --> D[Parsing (Phase 1) – DOCX → Clause / Table records + source locators]
    D --> E[Parsed artifacts (JSON per doc) stored under artifacts/parsed_documents/]

    %% Extraction & EDA
    E --> F[Extraction (Phase 2) – regex + context → Typed Entities, Clause‑terms, Corpus EDA]
    F --> G[Entity fixtures & EDA reports (JSON, PNG)]

    %% Retrieval index
    E --> H[Retrieval (Phase 3) – clause‑aware chunking → ChromaDB + BM25 hybrid index]
    H --> I[Search API (semantic + keyword) returning text, score, metadata, source_location]

    %% Specialist agents
    I --> J[Agents (Phase 4/5) – Legal / Financial / Operational]
    J --> K[Each agent:
            • Retrieves top‑k passages per risk topic
            • Calls LLM (with resilience retries)
            • Verifies quoted excerpt against source chunk
            • Emits Finding (severity, confidence, verification_status)]
    K --> L[Orchestration (Phase 5) – Routing (triage), Parallel/Sequential run, Consensus building]
    L --> M[Assessment object (overall_risk, dimension_results, unresolved_issues, consensus_actions)]

    %% Persistence
    M --> N[Reports Root – phase5_assessment_<doc_id>.json]
    N --> O[Reporting (Phase 7) – Markdown risk report per doc]
    O --> P[phase7_report_<doc_id>.md]

    %% Evaluation & Observability
    N --> Q[Evaluation (Phase 7) – parse_success, entity_accuracy, retrieval_relevance,
            citation_validity, finding_support, partial_run_freq, schema_failure, api_failure,
            cost/latency, missed‑risk rate]
    Q --> R[phase7_evaluation_report.json]

    %% API & UI façade
    subgraph Facade
        S[app_service.py] --> T[FastAPI (api.py) – REST endpoints]
        S --> U[Gradio UI (ui.py) – 10‑section workspace]
    end

    T --> V[External consumers (scripts, CI, other services)]
    U --> W[Human analysts / reviewers]

    %% Resilience & Graph
    J -.-> X[Resilience (call_with_recovery – backoff, model escalation, fail‑fast)]
    M -.-> Y[Graph (relationships – categories, parties, external refs)]

    style A fill:#f9f,stroke:#333
    style V fill:#bbf,stroke:#333
    style W fill:#bbf,stroke:#333
```

## 2. Component Catalogue (part 1)

| Module | Phase | Primary Responsibility | Key Public Functions / Classes |
|--------|-------|------------------------|--------------------------------|
| **config.py** | 0 | Centralised constants (paths, taxonomy, model names, thresholds) | `CATEGORY_TAXONOMY`, `CHUNK_SIZE_WORDS`, `LEGAL_AGENT_MODEL`, … |
| **models.py** | 0 | Pydantic data models used everywhere | `DocumentRecord`, `ClauseRecord`, `Entity`, `Finding`, `Assessment`, `VerificationStatus`, `Severity`, `RiskDimension` |
| **ingestion.py** | 0‑1 | Walk `ContractIQ_data/`, fuzzy‑match folder → taxonomy, produce **manifest** (list of `DocumentRecord`) | `build_manifest()`, `save_manifest()`, `load_manifest()`, `print_manifest_report()` |
| **parsing.py** | 1 | Parse **.docx** only – keep paragraph & table boundaries, emit stable `source_location` (`paragraph:14`, `table:2,row:4,cell:3`). Never crashes batch; records `ParseStatus`. | `parse_docx_document()`, `save_parsed_document()`, `load_parsed_document()`, `run_phase1_sample()`, `run_phase1_full()` |
| **extraction.py** | 2 | Regex‑based entity extraction (dates, money, %, durations) + context‑keyword disambiguation → typed `Entity`. Clause‑term taxonomy (liability, termination, SLA, confidentiality …). Corpus‑level EDA + dashboard. | `extract_entities()`, `run_phase2_sample()`, `run_phase2_full()`, `plot_eda_dashboard()`, `build_evaluation_fixture()` |
| **retrieval.py** | 3 | Clause‑aware chunking → ChromaDB (OpenAI embeddings) + BM25 hybrid. Idempotent indexing (hash‑dedup). Search returns **text, score, doc metadata, source_location_range**. Evaluation helpers (recall@k). | `chunk_document()`, `embed_chunks()`, `upsert_chunks()`, `search()`, `search_hybrid()`, `evaluate_retrieval()` |
| **agents.py** | 4‑5 | Three specialist agents (Legal, Financial, Operational). Shared engine: `_analyze_topic → retrieve → LLM → _verify_and_build_finding`. Verification re‑checks quoted excerpt against source chunk → `VerificationStatus`. Persist per‑dimension `DimensionResult`. | `analyze_legal_risk()`, `analyze_financial_risk()`, `analyze_operational_risk()`, `save_*_assessment()`, `run_phase4_sample()`, `run_phase4_batch()` |
| **orchestration.py** | 5 | **Routing** (cheap triage decides which dimensions to run). **Parallel / sequential** execution with outer retry loop. **Consensus** – weighted severity, critical‑overrides, HITL flags, `Assessment` creation & persistence. | `route_dimensions()`, `run_sequential()`, `run_parallel()`, `build_consensus()`, `save_assessment()`, `run_phase5_sample()` |

---

## 3. Data‑flow Details

| Stage | Input | Output | Storage |
|-------|-------|--------|---------|
| **Ingestion** | Raw files (docx/pdf/xlsx) under `ContractIQ_data/` | `manifest.json` (list of `DocumentRecord`) | `artifacts/manifest.json` |
| **Parsing** | `DocumentRecord` | `parsed_<doc_id>.json` (clauses, tables, `ParseStatus`) | `artifacts/parsed_documents/` |
| **Extraction** | Parsed clauses | `extraction_<doc_id>.json` (entities, clause‑terms) + EDA aggregates | `artifacts/extractions/`, `reports/phase2_eda_dashboard.png` |
| **Retrieval** | Parsed clauses | ChromaDB collection `contractiq_chunks` + BM25 index (pickle) | `chroma_db/`, `artifacts/bm25_index.pkl` |
| **Agents** | Retrieval search results per risk topic | `DimensionResult` (findings with verification) | `reports/phase4_legal_<doc_id>.json` (similarly financial/operational) |
| **Orchestration** | Three `DimensionResult`s | `Assessment` (overall risk, consensus) | `reports/phase5_assessment_<doc_id>.json` |
| **Reporting** | `Assessment` | `phase7_report_<doc_id>.md` | `reports/` |
| **Evaluation** | All persisted artefacts | `phase7_evaluation_report.json` | `reports/` |
| **API / UI** | `app_service` calls | JSON / Markdown / UI widgets | Served at runtime (no extra persistence) |

## 2. Component Catalogue (part 2)

| Module | Phase | Primary Responsibility | Key Public Functions / Classes |
|--------|-------|------------------------|--------------------------------|
| **resilience.py** | 4‑5 | `call_with_recovery()` – classifies LLM errors (transient, schema, quota) and applies **back‑off**, **model escalation**, **fail‑fast**. Logs every call to `phase7_llm_calls.jsonl`. | `call_with_recovery()`, `SchemaFailure` |
| **evaluation.py** | 7 | Pure‑metric aggregation from **already‑saved artifacts** – no re‑execution. Computes parse success, entity accuracy (human‑reviewed fixture), retrieval relevance, citation validity, finding support, partial‑run frequency, schema‑failure rate, API failure rate, cost/latency per stage, missed‑risk rate (documented limitation). | `parse_success_rate()`, `entity_accuracy()`, `retrieval_relevance()`, `citation_validity_and_finding_support()`, `partial_run_frequency()`, `schema_failure_rate()`, `api_call_failure_rate()`, `cost_and_latency_by_stage()`, `important_missed_risk_rate()`, `build_evaluation_report()` |
| **reporting.py** | 7 | Turns a saved `Assessment` into a **human‑readable Markdown** risk report (overall risk, per‑dimension status, findings with evidence excerpts, unresolved issues, consensus actions, version metadata). | `load_assessment()`, `generate_document_report()`, `save_document_report()`, `generate_all_reports()` |
| **graph.py** | 5‑7 | Lightweight relationship layer built from parsed clauses – categories, parties, external references. Exposed via API/UI. | `get_documents_by_category()`, `get_documents_by_party()`, `get_external_references()` |
| **app_service.py** | 8 | **Facade** – thin wrappers around all phases so **API** and **UI** share *exact same* logic (no drift). | `get_overview()`, `list_documents()`, `get_document_chunks()`, `ask_question()`, `chat()`, `run_risk_analysis()`, `get_report_markdown()`, `export_report_file()`, `add_task()`, `set_task_status()`, `list_tasks()`, `get_recent_activity()`, `get_recovery_events()` |
| **api.py** | 8 | **FastAPI** surface – REST endpoints (`/health`, `/api/overview`, `/api/documents`, `/api/ask`, `/api/chat`, `/api/risk-analysis`, `/api/reports/{doc_id}`, `/api/graph/...`, `/api/tasks`, `/api/activity`, `/api/recovery-events`). Stateless; delegates to `app_service`. | `app = FastAPI(...)` |
| **ui.py** | 8 | **Gradio** 10‑section workspace (Overview, Upload, Contract Library, Risk Review, Ask ContractIQ, Document Sources, Relationships, Review Tasks, Reports, Activity & Traces). All widgets call `app_service`. Custom CSS/HTML mirrors design mock‑up. | `build_app()`, `launch_app()` |

---

## 4. Cross‑cutting Concerns

| Concern | Implementation |
|---------|----------------|
| **Observability** | Langfuse decorators (no‑op if not installed) + `phase7_llm_calls.jsonl` (latency, tokens, schema failures, errors). |
| **Resilience** | `call_with_recovery` – automatic back‑off, model escalation, fail‑fast; outer retry in orchestration. |
| **Human‑in‑the‑Loop** | Low‑confidence / failed‑verification / CRITICAL findings → `unresolved_issues` → Review Tasks UI. |
| **Versioning** | Every `Assessment` stores `document_version`, `model_version`, `prompt_version`, `policy_version`, `run_id`, `created_at`. Reports embed same metadata. |
| **Idempotency** | Retrieval indexing skips unchanged chunks (`text_hash`). Parsing & extraction write once per `doc_id`. |
| **Security / Secrets** | `OPENAI_API_KEY` read from `config.py` (expected to be sourced from env). No secrets in code. |
| **Testing / Sample‑first Gates** | Each phase exposes `run_phaseX_sample()` → manual verification → `run_phaseX_full()`. |

## 5. Deployment Sketch

```
+-------------------+          +-------------------+
|  FastAPI (uvicorn) | <--->  |  Gradio (launch)  |
|  port 8000         |          |  port 7860        |
+--------+----------+          +--------+----------+
         |                               |
         v                               v
   app_service.py  (single source of truth for business logic)
         |
   -------------------------------------------------
   |               |               |               |
   v               v               v               v
Ingestion   Parsing   Extraction   Retrieval   Agents/Orchestration
   |               |               |               |
   v               v               v               v
Manifest   Parsed JSON   Entities   ChromaDB   Assessments
   |               |               |               |
   +---------------+---------------+---------------+
                           |
                     Reporting / Evaluation
                           |
                     Markdown Reports + JSON metrics
```

*Both API and UI are **stateless** – they only call `app_service`. Scaling is therefore horizontal (multiple uvicorn workers / Gradio processes) sharing the same file‑based artefact store (or a mounted volume).*

---

## 6. How to Run the Whole Pipeline (CLI)

```bash
# 0️⃣  Build manifest
python -m contractiq.ingestion

# 1️⃣  Parse a few docs, verify, then full
python -c "from contractiq.parsing import run_phase1_sample, run_phase1_full; \
           from contractiq.ingestion import load_manifest; \
           m=load_manifest(); run_phase1_sample(m, ['doc-001','doc-002'])"
# after review:
python -c "from contractiq.parsing import run_phase1_full; \
           from contractiq.ingestion import load_manifest; \
           run_phase1_full(load_manifest())"

# 2️⃣  Extraction (sample → full)
python -c "from contractiq.extraction import run_phase2_sample, run_phase2_full; \
           from contractiq.ingestion import load_manifest; \
           m=load_manifest(); run_phase2_sample(m, ['doc-001'])"
python -c "from contractiq.extraction import run_phase2_full; \
           from contractiq.ingestion import load_manifest; \
           run_phase2_full(load_manifest())"

# 3️⃣  Build retrieval index
python -c "from contractiq.retrieval import build_index; build_index()"

# 4️⃣  Run specialist agents (sample → batch)
python -c "from contractiq.agents import run_phase4_sample; run_phase4_sample(['doc-001'])"
python -c "from contractiq.agents import run_phase4_batch; run_phase4_batch(['doc-001','doc-002'])"

# 5️⃣  Orchestration + consensus
python -c "from contractiq.orchestration import run_phase5_sample; run_phase5_sample(['doc-001'])"

# 7️⃣  Generate reports & evaluation
python -c "from contractiq.reporting import generate_all_reports; generate_all_reports()"
python -c "from contractiq.evaluation import build_evaluation_report; build_evaluation_report()"

# 8️⃣  Launch services
uvicorn contractiq.api:app --reload --port 8000   # API
python -m contractiq.ui                         # Gradio UI
```

---

## 7. Extending the System

| Want to add … | Where to touch |
|---------------|----------------|
| New risk dimension (e.g., **Regulatory**) | `models.py` → new `RiskDimension`; `agents.py` → new topic list & system prompt; `orchestration.py` → add to `_ANALYZERS/_SAVERS/_ALL_DIMENSIONS`; update consensus weights in `config.py`. |
| Alternative embedding model | `config.py` → `EMBEDDING_MODEL`; `retrieval.py` → `_get_openai_client()` (or swap client). |
| Different vector DB | Replace Chroma calls in `retrieval.py` (upsert / query) – façade stays same. |
| Additional UI tab | Add builder in `ui.py` `_SECTIONS` and wire to `app_service`. |
| New evaluation metric | Add function in `evaluation.py` and call from `build_evaluation_report()`. |

---

## 8. TL;DR – One‑Sentence Summary

> **ContractIQ** ingests a contract corpus, parses it into clause‑level evidence, extracts typed entities, builds a traceable hybrid retrieval index, runs three verified specialist LLM agents (Legal, Financial, Operational) under a resilient orchestration layer that produces a consensus `Assessment`, and finally surfaces versioned, evidence‑linked Markdown reports through a shared FastAPI + Gradio façade while continuously logging observability data for automated evaluation.

--- 

*Generated from the source tree under `src/contractiq/` (2026‑10‑29).*