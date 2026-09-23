# ContractIQ Backend Implementation Roadmap

> Notebook-first learning plan in simple Hinglish. Implementation aap likhenge; assistant concepts, design review, hints, debugging aur verification mein help karega.
>
> Created: 09 September 2026. Yeh roadmap hai, completed implementation ka status report nahi. All checkboxes intentionally unchecked hain.

## 1. Goal and Working Approach

Goal hai actual enterprise DOCX files se evidence-backed contract intelligence backend banana: document processing, semantic retrieval, specialist risk agents, consensus, relationships, observability aur usable integration.

Pehle **one real document par correct flow**, phir related documents aur complete corpus par scale karein. Existing UI ke fictional findings ko real dataset ke expected answers ki tarah use nahi karna hai.

Reference documents:

- [Original problem statement](../Contract_Intelligence_Detailed_Problem_Statement.docx.pdf)
- [Current product and UI overview](../design/ContractIQ_Product_Overview.md)
- [Dataset directory](../ContractIQ_data/)

### Main Processing Flow

```text
DOCX files
  -> validated document manifest
  -> extracted text, tables and stable source locations
  -> clauses and normalized entities
  -> source-linked chunks
  -> embeddings and persistent ChromaDB index
  -> relevant evidence and policy context
  -> Legal / Financial / Operational specialist agents
  -> structured output and source validation
  -> consensus with explicit uncertainty and failure status
  -> human review, reports and application integration

Knowledge graph: verified relationships and dependency context
Langfuse: traces from early development through final evaluation
```

Har query ko har stage ya teenon agents se pass karna zaroori nahi. Expiry queries structured dates use karengi; dependency queries graph use karengi; semantic clause questions retrieval use karengi.

## 2. Scope and Milestones

### Initial Scope

- Start with DOCX and one representative real agreement.
- Use the actual eight-category taxonomy; distinguish agreements from supporting documents.
- Keep source references from parsing onward, not only when building UI.
- Start with one Legal agent before adding other specialists.
- Establish basic Langfuse tracing in Week 1; deepen evaluation in Week 7.
- Use Gradio to validate the assignment workflow before adapting the existing HTML prototype.

Initially defer PDF/OCR, autonomous emails, reminders, authentication, collaboration, Docker/cloud deployment and HTML UI integration. Ingestion and assessment correctness pehle verify karein.

| Milestone | Target outcome | Relevant phases |
|---|---|---|
| M1 | One real DOCX -> verified text, entities and source locations | 1-2 |
| M2 | One question -> relevant evidence -> one validated Legal finding | 3-4 |
| M3 | One agreement -> three specialists -> combined assessment | 5 |
| M4 | Related-document context, measured quality and working application | 6-8 |

Weeks ko strict calendar deadline ki tarah treat na karein. Har phase ka completion gate pass hone ke baad next phase par move karein.

## 3. Phase 1: Environment and Foundations

Notebook: [Week-1 Assignment.ipynb](Week-1%20Assignment.ipynb)

**Purpose:** Repeatable environment, secure configuration aur verified dataset inventory banana.

Assignment sections: package installation, environment configuration, Langfuse initialization, traced wrappers, contract taxonomy and data discovery.

### Implement in This Order

1. Confirm notebook kernel/interpreter and install mutually compatible dependencies.
2. Record the tested dependency versions so environment reproduce ho sake.
3. Configure model and Langfuse credentials securely; never print keys or save them in notebook outputs.
4. Initialize one small model request and basic tracing; use a synthetic prompt first.
5. Define the eight document categories and discover actual DOCX paths.
6. Build a manifest with document ID, path, filename, category, size and content hash/version.

**Deliverables:** Environment notes, manifest, traced smoke-test result and clear configuration-error messages.

### Completion Gate

- [ ] Expected 36 DOCX files discovered; any missing/extra files investigated.
- [ ] Every discovered file has a category or explicit unresolved classification.
- [ ] One small model request succeeds and its trace is visible.
- [ ] Missing configuration fails clearly without revealing secrets.
- [ ] Restart kernel and Run All succeeds without hidden variables.

**Common mistake:** Relative paths work from one directory only. Resolve and verify the project/data root explicitly.

## 4. Phase 2: Document Processing and EDA

Notebook: [Week-2 Assignment.ipynb](Week-2%20Assignment.ipynb)

**Purpose:** Documents ko usable text, structured facts aur traceable locations mein convert karna.

Assignment sections: document processor, process all documents, exploratory data analysis and entity extraction.

### Implement in This Order

1. Parse one DOCX and inspect paragraphs plus tables against the original.
2. Preserve meaningful reading order and attach stable source locations.
3. Add headings/clause boundaries where supported; uncertain boundaries explicit rakhein.
4. Extract parties, dates, amounts and terms with raw values plus normalized values.
5. Preserve distinctions such as effective date, expiry date and notice deadline.
6. Run batch processing with per-file success/failure records.
7. Inspect category counts, empty documents, text lengths, extraction failures and missing entities.

**Deliverables:** Parsed document records, source-location records, entity records, failure list and EDA summary.

### Completion Gate

- [ ] One agreement and one table-heavy/supporting document manually checked.
- [ ] Every entity can resolve back to supporting source text.
- [ ] Missing or ambiguous values remain unknown instead of guessed.
- [ ] Invalid/empty input does not crash the entire batch.
- [ ] Original files remain unchanged.
- [ ] Saved artifacts can be loaded after a kernel restart.

**Example:** An amount in an invoice should not automatically become the MSA annual value. Entity meaning depends on document type and surrounding wording.

**Common mistake:** Labeling a generated DOCX paragraph index as an original page number. Use honest locations such as paragraph/table/cell identifiers.

## 5. Phase 3: Embeddings and Retrieval

Notebook: [Week-3 Assignment.ipynb](Week-3%20Assignment.ipynb)

**Purpose:** Exact keywords ke beyond relevant evidence locate karna, without losing source identity.

Assignment focus: ChromaDB vector store, indexing, semantic search and optional metadata filters.

### Implement in This Order

1. Define chunk boundaries and overlap; avoid splitting an exception away from its main clause where practical.
2. Attach chunk IDs, document/version IDs, category and source references.
3. Generate embeddings and write a persistent ChromaDB collection.
4. Implement repeatable indexing: unchanged documents should not create duplicate chunks.
5. Add document/category filters and return text, metadata and retrieval scores.
6. Build 10-15 questions with manually identified expected evidence.
7. Compare chunking/retrieval configurations against that fixed question set.

**Deliverables:** Persistent index, reusable retrieval function, evaluation questions and retrieval report.

### Completion Gate

- [ ] Relevant evidence appears in retrieved results for the labeled questions; misses documented.
- [ ] Scoped queries do not leak results from excluded documents.
- [ ] Every returned chunk resolves to its original source locations.
- [ ] Reopening the index works without re-embedding everything.
- [ ] Re-indexing unchanged files does not increase the chunk count.

**Common mistake:** Treating a similarity score as answer confidence. Notebook example thresholds need empirical checking with the configured distance metric, model and dataset.

## 6. Phase 4: Individual Risk Agents

Notebook: [Week-4 Assignment.ipynb](Week-4%20Assignment.ipynb)

**Purpose:** Evidence se structured, reviewable specialist findings generate karna.

Assignment focus: Pydantic output models, Langfuse callbacks, specialist agent chains and individual tests.

### Implement in This Order

1. Define input/output schemas before writing the prompts.
2. Implement Legal agent first using one verified evidence example.
3. Use LCEL and supported structured-output integration; validate schema and source references separately.
4. Add Financial and Operational agents using the same evidence conventions.
5. Include policy context, uncertainty and insufficient-evidence behavior.
6. Evaluate each agent independently before orchestration.

| Agent | Responsibility | Example assessment question |
|---|---|---|
| Legal | Liability, indemnity, IP, confidentiality and compliance | Is general liability capped, and what exceptions apply? |
| Financial | Payment, penalties, pricing and financial exposure | What late-payment charges apply and under which conditions? |
| Operational | Scope, acceptance, delivery, SLA and remedies | Are acceptance criteria measurable and remedies defined? |

**Deliverables:** Three independently callable agents, structured outputs and small labeled test cases.

### Completion Gate

- [ ] Outputs conform to schema and supported severity values.
- [ ] Each finding has real supporting evidence and an appropriate rationale.
- [ ] Missing evidence does not produce fabricated clause numbers or quotations.
- [ ] Invalid model output is captured as a validation failure, not silently accepted.
- [ ] Document instructions cannot override the agent's system/task instructions.
- [ ] Full-review claims are limited to the actual document coverage.

**Common mistake:** Pydantic validates structure, not legal truth. A valid JSON object can still contain an unsupported conclusion.

## 7. Phase 5: Multi-Agent Orchestration

Notebook: [Week-5 Assignment.ipynb](Week-5%20Assignment.ipynb)

**Purpose:** Specialist outputs ko reliable combined workflow mein integrate karna.

### Implement in This Order

1. Integrate all three agents sequentially for easier debugging.
2. Add parallel execution after the sequential path is correct.
3. Handle timeouts, rate limits and transient errors with bounded retries/backoff.
4. Preserve individual specialist success/failure status and valid partial results.
5. Deduplicate equivalent findings while keeping contributing evidence.
6. Define severity aggregation, disagreement handling and human-review escalation.
7. Trace the overall run and each specialist invocation.

**Deliverables:** One orchestrator result with specialist outputs, validated combined findings, run metadata and unresolved issues.

### Completion Gate

- [ ] One real agreement completes all three specialist paths.
- [ ] A simulated specialist failure preserves the other valid outputs.
- [ ] Retries are bounded and limited to appropriate errors.
- [ ] Incomplete analysis is visible rather than labeled Complete.
- [ ] A Critical finding remains visible even when a composite average is low.
- [ ] Conflicting findings are preserved or explicitly resolved, not silently discarded.

**Common mistake:** Calling weighted averaging "consensus." A score summary and evidence-based conflict resolution are different responsibilities.

## 8. Phase 6: Contract Knowledge Graph

Notebook: [Week-6 Assignment.ipynb](Week-6%20Assignment.ipynb)

**Purpose:** Contract hierarchies aur document dependencies ko evidence ke saath represent karna.

### Implement in This Order

1. Define node types and directed relationship types before adding edges.
2. Select a small group of genuinely related documents from the dataset.
3. Create NetworkX nodes with stable IDs and metadata.
4. Add relationships with provenance and verification status.
5. Implement dependency queries, then add visualization.
6. Keep document-level relationships distinct from clause-level references.

**Deliverables:** Graph-building function, serialized graph artifact, evidence-backed query results and visualization.

### Completion Gate

- [ ] One verified related-document group is represented correctly.
- [ ] Every asserted contractual relationship has supporting evidence.
- [ ] Direction is correct: for example, MSA governs SOW rather than the reverse.
- [ ] Missing/ambiguous relationships are not fabricated from filename similarity alone.
- [ ] Queries return source references, not only graph labels.

**Common mistake:** Copying the current UI's illustrative graph edges into the real backend as contractual facts.

## 9. Phase 7: Advanced Observability and Evaluation

Notebook: [Week-7 Assignment.ipynb](Week-7%20Assignment.ipynb)

**Purpose:** System ki quality, failures aur cost ko repeatably inspect aur improve karna.

Tracing Week 1 se start hona chahiye. Is phase mein custom scores, quality metrics aur deeper diagnosis add honge.

### Implement in This Order

1. Freeze a small manually reviewed evaluation set covering all three dimensions.
2. Measure retrieval relevance and source/citation validity separately.
3. Evaluate finding correctness, important missed risks and recommendation support.
4. Track schema failures, latency, tokens, costs and retry counts.
5. Attach run, document, prompt, model and policy versions to results.
6. Review regressions after changes rather than only successful examples.

**Deliverables:** Evaluation dataset, run-level metric table, custom trace scores and known-failure report.

### Completion Gate

- [ ] A failed answer can be traced to extraction, retrieval, agent or validation behavior.
- [ ] Metrics use explicit definitions and denominators.
- [ ] Quality is checked against human-reviewed evidence, not only model self-rating.
- [ ] Cost reporting distinguishes measured usage from estimates/unavailable values.
- [ ] Trace payloads follow an approved sensitive-data/redaction policy.

**Common mistake:** A successful API call or a high model confidence score does not establish answer accuracy.

## 10. Phase 8: Application Integration

Notebook: [Week-8 Assignment.ipynb](Week-8%20Assignment.ipynb)

**Purpose:** Tested notebook components ko ek usable, repeatable end-to-end application banana.

The assignment includes Gradio integration and further FastAPI/Docker/cloud deployment guidance. Core correctness aur local integration verify hone se pehle deployment ko priority na dein.

### Implement in This Order

1. Define an application-service boundary for ingest, retrieve, analyze and report operations.
2. Move stable notebook functions/classes into reusable Python modules; notebooks experiments and demonstrations ke liye rakhein.
3. Load persisted artifacts rather than depending on notebook global state.
4. Build Gradio upload, risk analysis, source evidence, graph and report workflows.
5. Validate source references end to end and expose partial/failure statuses.
6. Test a clean local start and a complete real-document workflow.
7. Only then add an API adapter for the existing HTML UI if needed.
8. Treat containerization/cloud hosting as a later deployment gate, not proof of production readiness.

**Deliverables:** Reusable backend modules, local Gradio workflow, reports, integration tests and reproducible startup instructions.

### Completion Gate

- [ ] Fresh kernel/process can run the workflow from documented setup.
- [ ] Real document -> analysis -> evidence inspection -> export works.
- [ ] Results are not sourced from the prototype's fictional findings.
- [ ] Restart behavior and persistence boundaries are explicit.
- [ ] Invalid input, empty evidence and partial specialist failures have usable responses.
- [ ] Credentials remain outside frontend code and exported reports.

**Common mistake:** Connecting buttons to functions before those functions have stable input/output contracts and reliable failure behavior.

## 11. Shared Data Contracts

Define these records early and evolve them deliberately. Full implementations ek saath likhna necessary nahi.

| Record | Minimum useful fields |
|---|---|
| Document | ID, content hash/version, path, filename, category, parse status |
| Source / clause | Document/version ID, location ID, text, paragraph/table location |
| Entity | Type, raw value, normalized value, supporting source reference |
| Chunk | Chunk ID, document/version ID, text, source references, category |
| Finding | Dimension, severity, evidence references, rationale, recommendation, verification status |
| Assessment | Run ID, document/version ID, specialist outputs/statuses, consensus, unresolved issues |
| Graph edge | Source node, target node, relationship type, evidence, verification status |

**Identity rule:** Finding -> source reference -> correct document version -> stored passage should remain resolvable after saving/loading artifacts.

**Date rule:** Effective date, expiry date, renewal date and notice deadline are distinct fields. Define timezone, reference date and window boundaries when implementing date filters.

**Persistence rule:** ChromaDB is a retrieval index, not the sole source of truth for original documents, normalized records, findings and human review history.

## 12. Repeatable Notebook Working Pattern

Use this structure inside each major section:

1. **Objective:** Function kya karega aur kya scope ke bahar hai?
2. **Input/output contract:** Required fields, return type and failure result.
3. **Small implementation:** One document, one question or one finding.
4. **Manual inspection:** Original evidence ke saath output compare karein.
5. **Focused tests:** Normal case, empty/missing case and failure case.
6. **Checkpoint:** Artifacts save karein, known limitations note karein, restart and Run All verify karein.

Later notebooks include provided foundation material. Apne tested implementation se differences samajhkar reuse karein. A markdown summary saying "Complete" does not establish that the code was run successfully or that its outputs are correct.

Before expensive full-corpus runs, test on a small subset, inspect traces and estimate cost. Full retries or embeddings reruns ko accidental duplicate work na banne dein.

## 13. Query Routing Rules

| User need | Appropriate backend path |
|---|---|
| Contracts expiring within 90 days | Structured date filtering across all eligible records |
| Similar indemnity wording | Semantic retrieval with metadata filters |
| Vendor payment comparison | Normalized terms plus supporting clauses and exceptions |
| MSA/SOW dependencies | Verified relationship graph |
| Complete agreement risk review | Sufficient whole-document coverage plus specialist analysis |
| Negotiation draft | Verified findings -> draft -> human review; no automatic sending |

Top-k retrieval alone cannot reliably enumerate every expiring document or prove a clause is absent. Retrieval failure, missing extraction and true contractual absence need different statuses.

## 14. How to Ask for Help

When stuck, share:

```text
Notebook and section:
What I am trying to implement:
Input example, sanitized:
Expected output:
Actual output or complete relevant error:
Smallest relevant code:
Interpreter/package versions, if relevant:
What I already tried:
Help needed: concept / hint / debugging / code review
```

Default collaboration mode: pehle explanation, diagnosis aur hints; full implementation only when explicitly requested. API keys, tokens aur confidential document text redact karein.

## 15. Progress Tracker

- [ ] Phase 1: Reproducible environment, verified manifest and traced smoke test.
- [ ] Phase 2: Verified extraction, entities and source locations.
- [ ] Phase 3: Persistent, evaluated retrieval.
- [ ] Phase 4: Independently validated specialist agents.
- [ ] Phase 5: Reliable orchestration and explicit consensus policy.
- [ ] Phase 6: Evidence-backed relationship graph.
- [ ] Phase 7: Repeatable quality/cost evaluation and traceability.
- [ ] Phase 8: Real-document end-to-end application and exports.

## First Action

Start with **Week 1, sections 1.1-1.6**. Pehla checkpoint: selected notebook environment works, dataset manifest matches the actual files, aur one small model call ka trace visible hai. Is gate ke baad Week 2 parsing start karein.