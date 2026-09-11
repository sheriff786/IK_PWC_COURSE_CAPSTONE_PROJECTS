# ContractIQ Capstone: Notebook Analysis

## What the notebooks are trying to build

The eight notebooks describe a production-oriented **Contract Intelligence Multi-Agent System**. Its purpose is to ingest enterprise contract documents, find relevant clauses, identify risks, and present a combined legal, financial, and operational assessment.

The course builds the system incrementally. Each weekly notebook includes the prior weeks' work and adds one new capability. The intended end-to-end flow is:

```text
Contract repository or uploaded contract
        |
        v
Discover and parse documents
        |
        v
Extract sections, tables, entities, and rule-based risk indicators
        |
        +--------------------------+
        |                          |
        v                          v
Chunk and index content       Build contract knowledge graph
in ChromaDB                   (types, clauses, risks, mitigations)
        |
        v
Retrieve semantically relevant clauses
        |
        v
Run legal, financial, and operational agents in parallel
        |
        v
Build consensus, calculate overall risk, and recommend actions
        |
        v
Expose the workflow through a UI/API while tracing it in Langfuse
```

Langfuse is a cross-cutting concern: every meaningful action should be traced for auditability, latency, token/cost tracking, debugging, and quality evaluation.

## Step-by-Step Weekly Plan

### Week 1: Environment, observability, and data discovery

**Goal:** Build the operational foundation before implementing contract intelligence.

1. Install and verify the Python dependencies: OpenAI, LangChain, Langfuse, ChromaDB, NetworkX, PyVis, `python-docx`, Gradio, FastAPI-related packages, and data-analysis libraries.
2. Detect whether the notebook is running in Google Colab or locally.
3. Load `OPENAI_API_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_PUBLIC_KEY` securely from Colab Secrets or a local `.env` file.
4. Obtain the course dataset and configure the root data directory.
5. Initialize Langfuse and create a unique `SESSION_ID` so every trace from one run can be viewed together.
6. Create traced wrappers around OpenAI embedding and chat-completion calls. These wrappers capture inputs, outputs, model usage, and token counts.
7. Define the eight contract-data categories, including master agreements, transaction contracts, commercial documents, financial/billing documents, operational documents, compliance documents, negotiation history, and governance/audit materials.
8. Recursively scan each category for `.docx`, `.pdf`, and `.xlsx` files and log the discovery results.

**Output:** a verified environment, a Langfuse session, discovered document paths, and reusable traced LLM helpers.

### Week 2: Document processing and exploratory analysis

**Goal:** Turn raw contract files into structured, analyzable records.

1. Implement a `ContractDocumentProcessor` for DOCX files.
2. Read non-empty paragraphs from each document.
3. Extract table cells and transform tables into LLM-readable text, preserving rows with separators.
4. Detect common contract headings, such as numbered sections, articles, schedules, exhibits, and appendices, using regular expressions.
5. Create a normalized document record containing a document ID, file metadata, complete text, table text, sections, and structural counts.
6. Process every discovered document by category and create `all_docs_flat`, the single list consumed by later steps.
7. Create a DataFrame and analyze corpus size, category distribution, document length, tables, paragraphs, and sections.
8. Save EDA visuals to `contract_eda.png`; the results inform chunk sizing and retrieval design.
9. Use regex-based entity extraction to detect parties, dates, monetary values, percentages, durations, notice periods, liability caps, termination clauses, indemnification, confidentiality, and intellectual-property language.
10. Flag linguistic risk indicators as high, medium, or favorable and store per-document extraction results.

**Output:** processed contract records, EDA charts, extracted entities, and baseline rule-based risk signals.

### Week 3: Embeddings, vector storage, and semantic retrieval

**Goal:** Make the contract corpus searchable by meaning, not only exact keywords.

1. Initialize a persistent ChromaDB client and create a `contracts_all` collection configured for cosine similarity.
2. Combine each document's body and table text.
3. Split long documents into overlapping chunks. The completed Week 8 reference uses 800-word chunks with a 100-word overlap.
4. Generate an OpenAI `text-embedding-3-small` embedding for every chunk using the traced embedding wrapper.
5. Store each chunk in ChromaDB with its embedding and provenance metadata: document ID, filename, category, chunk index, and total chunks.
6. Embed a natural-language user query and use it to retrieve the nearest contract chunks.
7. Convert Chroma cosine distances into similarity values using $similarity = 1 - distance$.
8. Display the retrieved text, source document, category, and score. The assignment also proposes a bonus metadata-filtered search.

**Output:** a persistent, metadata-rich semantic search layer that later agents and UI workflows can use as RAG context.

### Week 4: Specialized contract risk agents

**Goal:** Replace a single generic analysis with domain-specific assessments that return reliable structured data.

1. Define Pydantic schemas for legal, financial, and operational assessments.
2. Require each schema to provide a risk level, confidence value in the $[0, 1]$ range, findings, and actionable recommendations.
3. Create a Langfuse callback handler for LangChain chains.
4. Create a legal agent that reviews liability exposure, intellectual-property risks, indemnification, compliance gaps, negotiation leverage, and recommended changes.
5. Create a financial agent that reviews contract value, payment terms, pricing and escalation risks, penalties, cash-flow impact, exposure, and recommended caps.
6. Create an operational agent that reviews service scope, SLAs, delivery and dependency risks, resource requirements, performance measures, gaps, and mitigations.
7. For every agent, construct the chain as `prompt -> ChatOpenAI -> PydanticOutputParser`.
8. Invoke agents with a bounded contract-text length and return validated Pydantic objects instead of unstructured prose.

**Output:** three independently traced risk specialists producing predictable typed results.

### Week 5: Multi-agent orchestration and consensus

**Goal:** Produce one combined contract assessment from the three specialist perspectives.

1. Define three risk dimensions: legal, financial, and operational.
2. Create a `ContractRiskOrchestrator` holding the three agents and the vector-store dependency.
3. Execute the three agents concurrently with `ThreadPoolExecutor(max_workers=3)` to reduce end-to-end latency.
4. Apply retry handling with Tenacity and exponential backoff for transient failures.
5. Preserve individual agent results, success states, errors, risk levels, confidence scores, and recommendations.
6. Build a consensus object by collecting risk levels and merging recommendations from all agents.
7. Deduplicate and limit priority actions.
8. Convert levels to numbers: LOW = 1, MEDIUM = 2, HIGH = 3, and CRITICAL = 4.
9. Calculate the overall risk with weighted scoring: legal 40%, financial 35%, and operational 25%.
10. Map the resulting weighted score back to LOW, MEDIUM, HIGH, or CRITICAL and trace the completed orchestration.

**Output:** a single contract-risk result with per-dimension assessments, consensus actions, confidence data, and an overall risk decision.

### Week 6: Contract knowledge graph

**Goal:** Add relationship-aware reasoning that complements semantic search.

1. Create a directed NetworkX graph.
2. Add an ontology of contract types and hierarchy relationships, for example MSA `GOVERNS` SOW, NDA, and rate cards; SOW governs invoices, service reports, and change orders.
3. Add clause-type nodes, including indemnification, liability limitation, confidentiality, termination, IP rights, and payment terms.
4. Connect clauses to the concerns they `ADDRESSES`.
5. Add risk nodes such as unlimited liability, IP infringement, data breach, payment default, and scope creep.
6. Connect mitigating clauses to each risk using `MITIGATES` relationships.
7. Add each processed contract as a document node and link it to its category.
8. Implement graph queries that answer which clauses mitigate a risk and which concerns a clause addresses.
9. Produce a static graph image (`contract_knowledge_graph.png`) and interactive PyVis HTML visualization (`contract_knowledge_graph.html`).

**Output:** a visual and queryable contract ontology that can trace risks back to protections and document relationships.

### Week 7: Observability and quality metrics

**Goal:** Make the AI workflow measurable in a production setting.

1. Review the traces emitted by all earlier stages through the shared Langfuse session.
2. Convert overall contract risk into a quality-style score: LOW = 1.0, MEDIUM = 0.7, HIGH = 0.4, CRITICAL = 0.1, and UNKNOWN = 0.5.
3. Attach that score to a dedicated Langfuse trace using `langfuse.score()`.
4. Implement a `MetricsCollector` that records operation latency and success/failure counts.
5. Aggregate average latency, operation count, session duration, and success rate per operation.
6. Log the metrics summary to Langfuse.
7. Replace the notebook's simulated test metrics with real instrumentation when converting the prototype into an application.

**Output:** trace navigation, quality scores, reliability rates, latency summaries, and a baseline observability model.

### Week 8: Production integration and deployment

**Goal:** Turn the notebook prototype into an application users can interact with.

1. Implement `ContractIntelligenceSystem` as the integration facade around the document processor, entity extractor, vector store, risk orchestrator, knowledge graph, and metrics collector.
2. Add `analyze_contract(contract_text, contract_id)` to validate input, run analysis, trace the full workflow, and return a presentation-ready result.
3. Add `search_contracts(query, n_results)` to expose semantic retrieval with source metadata.
4. Add `get_system_status()` to report initialization state, indexed content, graph size, and health information.
5. Initialize one shared production-system instance.
6. Add Gradio functions to render contract-analysis and semantic-search results.
7. Create a Gradio interface with clear analysis and search flows, then launch it conditionally for notebook use.
8. Create a FastAPI service with health and query endpoints, Pydantic request/response models, configuration from environment variables, and container/deployment artifacts.
9. Deploy the generated application to AWS EC2 or another secured hosting platform. The included guide covers a virtual environment, environment variables, Uvicorn, optional systemd, and optional Docker.
10. Run a final integrated checkpoint covering the prior stages plus the production system and UI.

**Output:** a user-facing ContractIQ application with an interactive prototype, an API deployment path, and end-to-end traceability.

## Important implementation note

The Week 8 notebook contains placeholder cells that deliberately raise `NotImplementedError`; they are assignment tasks, not a complete implementation. In addition, the hints in the FastAPI placeholder mention price, catalog, and marketing agents, which belong to a different competitive-intelligence example and do not match ContractIQ. The production API should instead expose contract ingestion/analysis, semantic contract search, system status, and health endpoints.

## Final system capabilities

When completed, ContractIQ should let a user:

1. Load repository contracts or submit contract text.
2. Parse content, tables, sections, entities, and initial risk phrases.
3. Search the corpus for semantically related clauses with traceable source metadata.
4. Receive parallel legal, financial, and operational assessments.
5. See an overall weighted risk level and prioritized contract changes.
6. Inspect knowledge-graph relationships between documents, clauses, concerns, risks, and mitigations.
7. Monitor quality, latency, model usage, errors, and risk scores in Langfuse.
8. Use the capability through a Gradio interface and production FastAPI deployment.