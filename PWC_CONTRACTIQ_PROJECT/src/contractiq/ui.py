"""
ContractIQ — Phase 8: Gradio UI.

Roadmap reference: 08_Gradio_Integration.ipynb
10 sections modeled on the design mockup (PWC_CONTRACTIQ_PROJECT_IK/design):
Overview, Upload, Contract Library, Risk Review, Ask ContractIQ, Document
Sources, Relationships, Review Tasks, Reports, Activity & Traces.

Every section is wired to app_service.py, which wraps already-verified
Phase 0-7 code. Styling approximates the mockup's teal/DM-Sans palette via
custom CSS; the information architecture (left sidebar + sectioned
workspace) is what's genuinely carried over — Gradio cannot render the
mockup's hand-written HTML/JS verbatim.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from . import app_service as svc
from .config import (
    DEFAULT_AGENT_MODEL,
    ESCALATION_AGENT_MODEL,
    HITL_CONFIDENCE_THRESHOLD,
    LANGFUSE_HOST,
    REPORTS_ROOT,
    TRIAGE_MODEL,
)

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INSUFFICIENT_EVIDENCE": 4}
_RISK_COLOR = {"CRITICAL": "#8b1f28", "HIGH": "#b7464d", "MEDIUM": "#ae6a29",
               "LOW": "#087f6d", "INSUFFICIENT_EVIDENCE": "#707c77", "not assessed": "#8c9691"}

# Fonts must be injected into <head> — Gradio builds its stylesheet as a
# constructed stylesheet, where @import is ignored by the browser.
_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap" '
    'rel="stylesheet">'
)

# Mirrors the mockup's palette (contractiq.css): teal primary, warm risk
# accents, Manrope headings over DM Sans body text.
_CSS = """
.gradio-container {
  font-family: 'DM Sans', system-ui, sans-serif !important;
  background: #fbfcfb !important;
  max-width: 100% !important;
}
h1, h2, h3, h4 { font-family: 'Manrope', sans-serif !important; color: #202b29 !important; }

.ciq-brand { padding: 4px 2px 14px 2px; border-bottom: 1px solid #e2e8e4; margin-bottom: 14px; }
.ciq-brand h2 { font-size: 21px !important; font-weight: 800 !important; letter-spacing: -0.3px; margin: 0 0 2px 0 !important; }
.ciq-brand h2 span { color: #087f6d; }
.ciq-brand p { font-size: 12.5px; color: #707c77; margin: 0 !important; line-height: 1.5; }
.ciq-sidenote { font-size: 11.5px; color: #8c9691; line-height: 1.6; }
.ciq-pill { display:inline-block; background:#e4f2ec; color:#076252; border-radius:999px;
            padding:3px 10px; font-size:11px; font-weight:600; margin:2px 4px 2px 0; }

.ciq-cards { display:flex; gap:14px; flex-wrap:wrap; margin: 6px 0 18px 0; }
.ciq-card { flex:1 1 170px; background:#fff; border:1px solid #e2e8e4; border-radius:14px;
            padding:16px 18px; box-shadow:0 2px 10px rgba(37,55,42,0.035); }
.ciq-card .label { font-size:11px; letter-spacing:0.07em; text-transform:uppercase;
                   color:#8c9691; font-weight:650; margin-bottom:7px; }
.ciq-card .value { font-family:'Manrope',sans-serif; font-size:29px; font-weight:750;
                   color:#202b29; line-height:1.05; }
.ciq-card .sub { font-size:12px; color:#707c77; margin-top:5px; }
.ciq-card.accent { background:#e4f2ec; border-color:#bfe0d4; }
.ciq-card.accent .value { color:#076252; }

.ciq-finding { background:#fff; border:1px solid #e2e8e4; border-left-width:4px;
               border-radius:11px; padding:14px 16px; margin-bottom:11px; }
.ciq-finding.sev-CRITICAL, .ciq-finding.sev-HIGH { border-left-color:#b7464d; }
.ciq-finding.sev-MEDIUM { border-left-color:#ae6a29; }
.ciq-finding.sev-LOW { border-left-color:#087f6d; }
.ciq-finding .title { font-family:'Manrope',sans-serif; font-weight:700; font-size:15px; color:#202b29; }
.ciq-finding .meta { font-size:11.5px; color:#8c9691; margin:4px 0 8px 0; }
.ciq-finding .rationale { font-size:13px; color:#434f4b; line-height:1.6; }
.ciq-finding blockquote { border-left:3px solid #e2e8e4; margin:9px 0 0 0; padding:4px 0 4px 12px;
                          font-size:12.5px; color:#5d6b66; font-style:italic; }
.ciq-badge { display:inline-block; border-radius:6px; padding:2px 8px; font-size:10.5px;
             font-weight:700; letter-spacing:0.04em; }
.ciq-badge.ok { background:#e4f2ec; color:#076252; }
.ciq-badge.warn { background:#fbeded; color:#b7464d; }
.ciq-badge.info { background:#ecf3fa; color:#487bad; }

.ciq-para { background:#fff; border:1px solid #e2e8e4; border-radius:10px;
            padding:12px 14px; margin-bottom:9px; font-size:13px; line-height:1.65; color:#434f4b; }
.ciq-para.hit { background:#fffdf3; border-color:#e8d9a6; box-shadow:0 0 0 2px #f6edd0 inset; }
.ciq-para .loc { font-size:10.5px; font-weight:700; letter-spacing:0.05em;
                 text-transform:uppercase; color:#8c9691; margin-bottom:5px; }
.ciq-para.hit .loc { color:#9a7a1f; }

.ciq-note { font-size:12.5px; color:#707c77; background:#f3f6f3; border:1px solid #e2e8e4;
            border-radius:10px; padding:11px 14px; line-height:1.6; }
"""


def _cards(items: List[Tuple[str, str, str]], accent_first: bool = True) -> str:
    html = ['<div class="ciq-cards">']
    for i, (label, value, sub) in enumerate(items):
        cls = "ciq-card accent" if (accent_first and i == 0) else "ciq-card"
        html.append(f'<div class="{cls}"><div class="label">{label}</div>'
                     f'<div class="value">{value}</div><div class="sub">{sub}</div></div>')
    html.append("</div>")
    return "".join(html)


def _risk_chip(risk: str) -> str:
    color = _RISK_COLOR.get(risk, "#333")
    return f'<span class="ciq-badge" style="background:{color}1a;color:{color}">{risk}</span>'


# ---------------------------------------------------------------------------
# 1. Overview
# ---------------------------------------------------------------------------

def _overview_cards() -> str:
    ov = svc.get_overview()
    dist = ov["risk_distribution"]
    high = dist.get("HIGH", 0) + dist.get("CRITICAL", 0)
    cv = ov["citation_validity_rate"]
    rr = ov["retrieval_relevance_rate"]
    return _cards([
        ("Documents", str(ov["total_documents"]), f"{ov['assessed_documents']} fully assessed"),
        ("Needs attention", str(high), "HIGH or CRITICAL overall risk"),
        ("Citation validity", f"{cv:.0%}" if cv is not None else "—", "evidence verified vs. source"),
        ("Retrieval recall", f"{rr:.0%}" if rr is not None else "—", "on the labeled test set"),
        ("Knowledge graph", str(ov["graph_nodes"]), f"{ov['graph_edges']} evidence-backed edges"),
    ])


def _risk_distribution_plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dist = svc.get_overview()["risk_distribution"]
    order = [r for r in ("CRITICAL", "HIGH", "MEDIUM", "LOW") if r in dist]
    fig, ax = plt.subplots(figsize=(5.2, 3.0), dpi=120)
    if order:
        ax.bar(order, [dist[r] for r in order],
               color=[_RISK_COLOR[r] for r in order], width=0.55)
        for i, r in enumerate(order):
            ax.text(i, dist[r] + 0.08, str(dist[r]), ha="center",
                    fontsize=10, fontweight="bold", color="#202b29")
    ax.set_ylabel("Documents", fontsize=9, color="#707c77")
    ax.set_title("Overall risk distribution", fontsize=11, fontweight="bold",
                  color="#202b29", loc="left", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#e2e8e4")
    ax.tick_params(colors="#707c77", labelsize=9)
    fig.patch.set_facecolor("#fff")
    fig.tight_layout()
    return fig


def _dimension_findings_plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    counts = {"legal": 0, "financial": 0, "operational": 0}
    verified = {"legal": 0, "financial": 0, "operational": 0}
    for doc_id in svc.list_assessed_doc_ids():
        for f in svc.get_risk_review(doc_id).get("findings", []):
            d = f["dimension"]
            if d in counts:
                counts[d] += 1
                if f["verification_status"] == "verified":
                    verified[d] += 1

    dims = list(counts)
    fig, ax = plt.subplots(figsize=(5.2, 3.0), dpi=120)
    ax.bar(dims, [counts[d] for d in dims], color="#cfe3da", width=0.55, label="total")
    ax.bar(dims, [verified[d] for d in dims], color="#087f6d", width=0.55, label="verified")
    ax.set_ylabel("Findings", fontsize=9, color="#707c77")
    ax.set_title("Findings by dimension (verified vs. total)", fontsize=11,
                  fontweight="bold", color="#202b29", loc="left", pad=10)
    ax.legend(frameon=False, fontsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#e2e8e4")
    ax.tick_params(colors="#707c77", labelsize=9)
    fig.patch.set_facecolor("#fff")
    fig.tight_layout()
    return fig


def build_overview_tab() -> None:
    gr.Markdown("## Portfolio overview")
    gr.HTML('<div class="ciq-note">Every number here is read from a real saved artifact — the Phase 0 '
             'manifest, Phase 5 assessments, the Phase 6 knowledge graph and the Phase 7 evaluation '
             'report. Nothing on this page is placeholder data.</div>')
    cards = gr.HTML(_overview_cards())
    with gr.Row():
        risk_plot = gr.Plot(_risk_distribution_plot(), label="Risk distribution")
        dim_plot = gr.Plot(_dimension_findings_plot(), label="Findings by dimension")
    refresh = gr.Button("Refresh", variant="secondary")
    refresh.click(fn=lambda: (_overview_cards(), _risk_distribution_plot(), _dimension_findings_plot()),
                   outputs=[cards, risk_plot, dim_plot])


# ---------------------------------------------------------------------------
# 2. Upload
# ---------------------------------------------------------------------------

_CATEGORIES = ["master_agreements", "transaction_contracts", "commercial_docs",
               "financial_billing", "operational_docs", "compliance_docs",
               "negotiation_history", "governance"]


def _do_upload(file_obj, category_key):
    if file_obj is None:
        return '<div class="ciq-note">Choose a <b>.docx</b> contract to begin.</div>', [], gr.update()

    path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
    result = svc.upload_document(path, category_key)
    if not result["success"]:
        return (f'<div class="ciq-note" style="border-color:#e8bcbc;background:#fbeded">'
                f'<b>Could not ingest this file.</b><br>{result.get("error")}</div>', [], gr.update())

    summary = _cards([
        ("Document ID", result["doc_id"], result["filename"]),
        ("Clauses parsed", str(result["clause_count"]), f"{result['table_count']} table(s)"),
        ("Chunks indexed", str(result["chunk_count"]), "searchable in ChromaDB now"),
    ])
    rows = [[c["locator"], c.get("heading") or "—", c["text"]] for c in result["preview_clauses"]]
    return summary, rows, gr.update(choices=[d["doc_id"] for d in svc.list_documents()],
                                     value=result["doc_id"])


def _do_analyze_upload(doc_id: str) -> str:
    if not doc_id:
        return '<div class="ciq-note">Upload a document first, then analyze it.</div>'
    result = svc.analyze_uploaded_document(doc_id)
    issues = result["unresolved_issues"]
    issue_html = "".join(f"<li>{i}</li>" for i in issues) or "<li>None flagged.</li>"
    return (_cards([
        ("Overall risk", result["overall_risk"], f"document {result['doc_id']}"),
        ("Findings", str(result["finding_count"]), "across routed dimensions"),
        ("Needs human review", str(len(issues)), "HITL-flagged items"),
    ]) + f"<h4>Review queue</h4><ul style='font-size:13px;color:#434f4b'>{issue_html}</ul>")


def build_upload_tab() -> None:
    gr.Markdown("## Upload a contract")
    gr.HTML('<div class="ciq-note">A new <b>.docx</b> goes through exactly the same pipeline as the rest '
             'of the corpus — Phase 1 parsing (with real source locations), then Phase 3 chunking and '
             'indexing. You can inspect the extracted clauses <i>before</i> spending money on a full '
             'multi-agent analysis.</div>')
    with gr.Row():
        file_in = gr.File(label="Contract (.docx)", file_types=[".docx"])
        category_in = gr.Dropdown(choices=_CATEGORIES, value="master_agreements", label="Category")
    upload_btn = gr.Button("Parse & index", variant="primary")
    upload_summary = gr.HTML()
    clause_table = gr.Dataframe(headers=["locator", "heading", "clause text"],
                                 label="Extracted clauses (first 10) — verify before analyzing",
                                 interactive=False, wrap=True)

    gr.Markdown("### Step 2 — run the multi-agent analysis")
    doc_pick = gr.Dropdown(choices=[d["doc_id"] for d in svc.list_documents()],
                            label="Document to analyze")
    analyze_btn = gr.Button("Run risk analysis", variant="primary")
    analyze_out = gr.HTML()

    upload_btn.click(fn=_do_upload, inputs=[file_in, category_in],
                      outputs=[upload_summary, clause_table, doc_pick])
    analyze_btn.click(fn=_do_analyze_upload, inputs=doc_pick, outputs=analyze_out)


# ---------------------------------------------------------------------------
# 3. Contract Library
# ---------------------------------------------------------------------------

_LIBRARY_HEADERS = ["doc_id", "filename", "category", "role", "overall risk"]


def _library_rows(query: str = "", risk_filter: str = "All") -> List[List[Any]]:
    docs = svc.list_documents()
    q = (query or "").strip().lower()
    if q:
        docs = [d for d in docs if q in d["filename"].lower() or q in d["doc_id"].lower()
                or q in d["category_key"].lower()]
    if risk_filter and risk_filter != "All":
        docs = [d for d in docs if d["overall_risk"] == risk_filter]
    docs.sort(key=lambda d: _SEVERITY_ORDER.get(d["overall_risk"], 99))
    return [[d["doc_id"], d["filename"], d["category_key"], d["document_role"], d["overall_risk"]]
            for d in docs]


def build_library_tab() -> None:
    gr.Markdown("## Contract library")
    gr.HTML('<div class="ciq-note">Every document in the manifest. <b>not assessed</b> is honest, not a '
             'gap — supporting evidence (invoices, policies, negotiation notes) is indexed for retrieval '
             'but is not itself a contract to risk-score.</div>')
    with gr.Row():
        search_box = gr.Textbox(label="Search", placeholder="doc_id, filename or category", scale=3)
        risk_filter = gr.Dropdown(choices=["All", "CRITICAL", "HIGH", "MEDIUM", "LOW", "not assessed"],
                                   value="All", label="Risk", scale=1)
    table = gr.Dataframe(headers=_LIBRARY_HEADERS, value=_library_rows(),
                          interactive=False, wrap=True)
    search_box.change(fn=_library_rows, inputs=[search_box, risk_filter], outputs=table)
    risk_filter.change(fn=_library_rows, inputs=[search_box, risk_filter], outputs=table)


# ---------------------------------------------------------------------------
# 4. Risk Review (with citation drill-down)
# ---------------------------------------------------------------------------

def _render_findings(doc_id: Optional[str]):
    if not doc_id:
        return '<div class="ciq-note">Select an assessed document.</div>', gr.update(choices=[])

    review = svc.get_risk_review(doc_id)
    if not review["available"]:
        return (f'<div class="ciq-note">No saved assessment for <b>{doc_id}</b>.</div>',
                gr.update(choices=[]))

    head = _cards([
        ("Overall risk", review["overall_risk"], doc_id),
        ("Findings", str(len(review["findings"])), "across all dimensions"),
        ("Needs human review", str(len(review["unresolved_issues"])), "HITL-flagged"),
    ])

    if review["unresolved_issues"]:
        head += ("<h4>Human review queue</h4>"
                 "<ul style='font-size:12.5px;color:#434f4b;line-height:1.7'>"
                 + "".join(f"<li>{i}</li>" for i in review["unresolved_issues"]) + "</ul>")

    blocks = ["<h4>Findings</h4>"]
    for f in review["findings"]:
        verified = f["verification_status"] == "verified"
        badge = ('<span class="ciq-badge ok">EVIDENCE VERIFIED</span>' if verified
                 else f'<span class="ciq-badge warn">{f["verification_status"].upper()}</span>')
        excerpt = (f["evidence_excerpts"] or ["(no excerpt)"])[0]
        blocks.append(
            f'<div class="ciq-finding sev-{f["severity"]}">'
            f'<div class="title">{f["title"]}</div>'
            f'<div class="meta">{_risk_chip(f["severity"])} &nbsp; {badge} &nbsp; '
            f'{f["dimension"]} · confidence {f["confidence"]} · '
            f'evidence {", ".join(f["evidence_ids"])}</div>'
            f'<div class="rationale">{f["rationale"]}</div>'
            f'<blockquote>"{excerpt[:320]}"</blockquote></div>'
        )

    choices = [f'{f["severity"]} · {f["title"]}' for f in review["findings"]]
    return head + "".join(blocks), gr.update(choices=choices, value=None)


def _render_citation(doc_id: Optional[str], finding_label: Optional[str]) -> str:
    if not doc_id or not finding_label:
        return ('<div class="ciq-note">Pick a finding above to open the exact paragraphs it came from, '
                'inside the original document.</div>')

    review = svc.get_risk_review(doc_id)
    finding = next((f for f in review.get("findings", [])
                    if f'{f["severity"]} · {f["title"]}' == finding_label), None)
    if finding is None:
        return '<div class="ciq-note">Finding not found — reselect the document.</div>'

    out = []
    for c in svc.resolve_finding_citations(doc_id, finding):
        if not c["found"]:
            out.append(f'<div class="ciq-note">Could not resolve: {c.get("reason")}</div>')
            continue
        located = ('<span class="ciq-badge ok">QUOTE LOCATED IN SOURCE</span>' if c["quote_located"]
                   else '<span class="ciq-badge warn">QUOTE NOT FOUND IN THESE PARAGRAPHS</span>')
        out.append(f'<div style="margin-bottom:8px"><b>{c["filename"]}</b> '
                   f'<span class="ciq-badge info">{c["source_location_range"]}</span> {located}</div>')
        for p in c["paragraphs"]:
            cls = "ciq-para hit" if p["is_quote_source"] else "ciq-para"
            heading = f' — {p["heading"]}' if p.get("heading") else ""
            out.append(f'<div class="{cls}"><div class="loc">{p["locator"]}{heading}</div>'
                       f'{p["text"]}</div>')
    return "".join(out)


def build_risk_review_tab() -> None:
    gr.Markdown("## Risk review")
    gr.HTML('<div class="ciq-note">Each finding carries its own evidence and a verification verdict. '
             '<b>Evidence verified</b> means the quoted text was independently re-found in the source '
             'document by code — not taken on the model\'s word.</div>')
    doc_dropdown = gr.Dropdown(label="Assessed document", choices=svc.list_assessed_doc_ids())
    findings_panel = gr.HTML('<div class="ciq-note">Select an assessed document.</div>')

    gr.Markdown("### Where did this come from?")
    finding_picker = gr.Dropdown(label="Open the source paragraphs for a finding", choices=[])
    citation_panel = gr.HTML('<div class="ciq-note">Pick a finding to open its source paragraphs.</div>')

    gr.Markdown("### Send to review queue")
    with gr.Row():
        task_title = gr.Textbox(label="Finding / topic", scale=2)
        task_note = gr.Textbox(label="Note", scale=3)
    add_btn = gr.Button("Add review task")
    add_status = gr.Markdown()

    doc_dropdown.change(fn=_render_findings, inputs=doc_dropdown,
                         outputs=[findings_panel, finding_picker])
    finding_picker.change(fn=_render_citation, inputs=[doc_dropdown, finding_picker],
                           outputs=citation_panel)

    def _add(doc_id, title, note):
        if not doc_id or not title:
            return "_Select a document and enter a finding title first._"
        task = svc.add_task(doc_id, title, note)
        return f"Added task `{task['task_id']}` for `{doc_id}`."

    add_btn.click(fn=_add, inputs=[doc_dropdown, task_title, task_note], outputs=add_status)


# ---------------------------------------------------------------------------
# 5. Ask ContractIQ
# ---------------------------------------------------------------------------

def _render_ask(query: str, doc_id: Optional[str]) -> str:
    if not query or not query.strip():
        return '<div class="ciq-note">Ask a question to search the indexed corpus.</div>'
    results = svc.ask(query, doc_id=doc_id or None)
    if not results:
        return '<div class="ciq-note">No results — try rephrasing, or clear the document filter.</div>'
    return "".join(
        f'<div class="ciq-finding sev-LOW"><div class="title">{r["doc_id"]} '
        f'<span class="ciq-badge info">score {r["score"]}</span></div>'
        f'<div class="meta">{r["category_key"]} · {r["source_location_range"]}</div>'
        f'<div class="rationale">{r["text"][:420]}{"…" if len(r["text"]) > 420 else ""}</div></div>'
        for r in results
    )


def build_ask_tab() -> None:
    gr.Markdown("## Ask ContractIQ")
    gr.HTML('<div class="ciq-note">Semantic search over the indexed corpus — the same retrieval the '
             'specialist agents use. This returns the real evidence passages with their source '
             'locations, rather than a generated answer you would then have to fact-check.</div>')
    with gr.Row():
        query_box = gr.Textbox(label="Question", scale=3,
                                placeholder="Is there a cap on total liability?")
        doc_filter = gr.Dropdown(label="Scope (optional)", scale=1,
                                  choices=[""] + [d["doc_id"] for d in svc.list_documents()])
    ask_btn = gr.Button("Search", variant="primary")
    results_panel = gr.HTML()
    ask_btn.click(fn=_render_ask, inputs=[query_box, doc_filter], outputs=results_panel)
    query_box.submit(fn=_render_ask, inputs=[query_box, doc_filter], outputs=results_panel)


# ---------------------------------------------------------------------------
# 6. Document Sources
# ---------------------------------------------------------------------------

def _chunk_rows(doc_id: Optional[str]) -> List[List[Any]]:
    if not doc_id:
        return []
    return [[c["chunk_id"], c["source_location_range"], c["chunk_index"], c["total_chunks"],
             c["text"][:260] + ("…" if len(c["text"]) > 260 else "")]
            for c in svc.get_document_chunks(doc_id)]


def build_sources_tab() -> None:
    gr.Markdown("## Document sources")
    gr.HTML('<div class="ciq-note">The exact indexed chunks behind a document, with the paragraph range '
             'each one covers — this is what retrieval actually searches.</div>')
    doc_dropdown = gr.Dropdown(label="Document", choices=[d["doc_id"] for d in svc.list_documents()])
    table = gr.Dataframe(headers=["chunk_id", "paragraph range", "#", "of", "text"],
                          interactive=False, wrap=True)
    doc_dropdown.change(fn=_chunk_rows, inputs=doc_dropdown, outputs=table)


# ---------------------------------------------------------------------------
# 7. Relationships
# ---------------------------------------------------------------------------

def _graph_image_path() -> Optional[str]:
    path = REPORTS_ROOT / "phase6_contract_knowledge_graph.png"
    return str(path) if path.exists() else None


def _bullets(items: List[str], empty: str) -> str:
    if not items:
        return f'<div class="ciq-note">{empty}</div>'
    return ("<ul style='font-size:13px;color:#434f4b;line-height:1.8'>"
            + "".join(f"<li><code>{i}</code></li>" for i in items) + "</ul>")


def build_relationships_tab() -> None:
    gr.Markdown("## Relationships")
    gr.HTML('<div class="ciq-note">Every edge in this graph carries its own evidence and a verification '
             'status. Nothing was inferred from filename similarity or from two documents merely sharing '
             'a party name — where this corpus could not prove a link, no edge was created.</div>')
    img = _graph_image_path()
    if img:
        gr.Image(value=img, label="Contract knowledge graph", show_label=True)

    with gr.Row():
        with gr.Column():
            gr.Markdown("#### By category")
            cat_dd = gr.Dropdown(choices=svc.list_categories(), label="Category")
            cat_out = gr.HTML()
            cat_dd.change(fn=lambda c: _bullets(svc.get_graph().get_documents_by_category(c) if c else [],
                                                 "Select a category."),
                           inputs=cat_dd, outputs=cat_out)
        with gr.Column():
            gr.Markdown("#### By party")
            party_dd = gr.Dropdown(choices=svc.list_parties(), label="Party")
            party_out = gr.HTML()
            party_dd.change(fn=lambda p: _bullets(svc.get_graph().get_documents_by_party(p) if p else [],
                                                   "Select a party."),
                             inputs=party_dd, outputs=party_out)

    gr.Markdown("#### External references cited by a document")
    ref_dd = gr.Dropdown(choices=[d["doc_id"] for d in svc.list_documents()], label="Document")
    ref_out = gr.HTML()

    def _refs(doc_id):
        if not doc_id:
            return '<div class="ciq-note">Select a document.</div>'
        refs = svc.get_graph().get_external_references(doc_id)
        if not refs:
            return '<div class="ciq-note">This document cites no external agreement in its own text.</div>'
        return "".join(
            f'<div class="ciq-finding sev-LOW"><div class="title">{r["relation"]}</div>'
            f'<div class="meta">evidence: {r["evidence_ids"]}</div>'
            f'<div class="rationale">{r["label"]}</div></div>' for r in refs)

    ref_dd.change(fn=_refs, inputs=ref_dd, outputs=ref_out)

    with gr.Row():
        with gr.Column():
            gr.Markdown("#### Possible duplicate external references")
            gr.HTML(_bullets([str(g) for g in svc.get_graph().find_potentially_same_external_reference()],
                              "None flagged.")
                     + '<div class="ciq-note">Flagged for a human to merge — never merged automatically '
                       'on this weak a signal.</div>')
        with gr.Column():
            gr.Markdown("#### Missing legal protections")
            gaps = svc.get_graph().find_missing_legal_protections()
            gr.HTML("".join(f'<div class="ciq-para"><div class="loc">{d}</div>{", ".join(t)}</div>'
                             for d, t in gaps.items())
                     or '<div class="ciq-note">No gaps found.</div>')


# ---------------------------------------------------------------------------
# 8. Review Tasks
# ---------------------------------------------------------------------------

_TASK_HEADERS = ["task_id", "doc_id", "finding_title", "note", "status", "created_at"]


def _task_rows(doc_id: Optional[str] = None) -> List[List[Any]]:
    return [[t[h] for h in _TASK_HEADERS] for t in svc.list_tasks(doc_id or None)]


def build_tasks_tab() -> None:
    gr.Markdown("## Review tasks")
    gr.HTML('<div class="ciq-note">The human-in-the-loop queue. Findings are escalated here '
             'automatically when evidence fails verification, when confidence drops to '
             f'{HITL_CONFIDENCE_THRESHOLD} or below, or when severity is CRITICAL — and you can add your '
             'own from the Risk review tab.</div>')
    table = gr.Dataframe(headers=_TASK_HEADERS, value=_task_rows(), interactive=False, wrap=True)
    refresh_btn = gr.Button("Refresh")
    refresh_btn.click(fn=lambda: _task_rows(), outputs=table)

    gr.Markdown("#### Update status")
    with gr.Row():
        task_id_box = gr.Textbox(label="Task ID")
        status_radio = gr.Radio(choices=["open", "in_progress", "done"], value="open", label="Status")
    update_btn = gr.Button("Update", variant="primary")
    update_btn.click(fn=lambda tid, s: (svc.set_task_status((tid or "").strip(), s), _task_rows())[1],
                      inputs=[task_id_box, status_radio], outputs=table)


# ---------------------------------------------------------------------------
# 9. Reports
# ---------------------------------------------------------------------------

def build_reports_tab() -> None:
    gr.Markdown("## Reports")
    gr.HTML('<div class="ciq-note">A versioned, evidence-linked report built live from the saved '
             'assessment — including document, model, prompt and policy versions plus the run ID, so any '
             'result can be traced back to exactly what produced it.</div>')
    doc_dropdown = gr.Dropdown(label="Document", choices=svc.list_assessed_doc_ids())
    with gr.Row():
        generate_btn = gr.Button("Generate report", variant="primary")
        export_btn = gr.Button("Export .md")
    report_panel = gr.Markdown()
    download = gr.File(label="Download", visible=False)

    def _generate(doc_id):
        if not doc_id:
            return "_Select an assessed document first._"
        try:
            return svc.get_report_markdown(doc_id)
        except FileNotFoundError:
            return f"_No saved assessment found for `{doc_id}`._"

    def _export(doc_id):
        path = svc.export_report_file(doc_id) if doc_id else None
        return gr.update(value=path, visible=path is not None)

    generate_btn.click(fn=_generate, inputs=doc_dropdown, outputs=report_panel)
    export_btn.click(fn=_export, inputs=doc_dropdown, outputs=download)


# ---------------------------------------------------------------------------
# 10. Activity & Traces
# ---------------------------------------------------------------------------

_ACTIVITY_HEADERS = ["timestamp", "stage", "model", "latency_ms", "total_tokens",
                     "schema_failure", "error"]
_RECOVERY_HEADERS = ["timestamp", "stage", "attempt", "failure_class", "strategy", "outcome", "detail"]


def _activity_rows(limit: int = 100) -> List[List[Any]]:
    return [[r.get(h) for h in _ACTIVITY_HEADERS] for r in svc.get_recent_activity(limit)]


def _recovery_rows(limit: int = 100) -> List[List[Any]]:
    return [[r.get(h) for h in _RECOVERY_HEADERS] for r in svc.get_recovery_events(limit)]


def build_activity_tab() -> None:
    gr.Markdown("## Activity & traces")
    gr.HTML(f'<div class="ciq-note"><b>Model tiering is deliberate.</b> Triage uses '
             f'<code>{TRIAGE_MODEL}</code> — one cheap call that decides which specialists are worth '
             f'running at all. Specialists default to <code>{DEFAULT_AGENT_MODEL}</code>, which Phase 7 '
             f'measured at 94.6% citation validity, so paying more by default would be cost without '
             f'evidence of benefit. <code>{ESCALATION_AGENT_MODEL}</code> is held in reserve and used '
             f'only when a cheap call fails in a way a retry cannot fix.<br>'
             f'Full traces: {LANGFUSE_HOST}</div>')

    gr.Markdown("#### LLM calls")
    table = gr.Dataframe(headers=_ACTIVITY_HEADERS, value=_activity_rows(),
                          interactive=False, wrap=True)

    gr.Markdown("#### Closed-loop recovery events")
    gr.HTML('<div class="ciq-note">Failures are classified before they are retried, and each class gets '
             'a <i>different</i> strategy — backoff for transient errors, model escalation for schema '
             'failures, and fail-fast for quota/auth problems a retry could never fix. An empty table '
             'means no failures have occurred.</div>')
    recovery = gr.Dataframe(headers=_RECOVERY_HEADERS, value=_recovery_rows(),
                             interactive=False, wrap=True)

    refresh_btn = gr.Button("Refresh")
    refresh_btn.click(fn=lambda: (_activity_rows(), _recovery_rows()), outputs=[table, recovery])


# ---------------------------------------------------------------------------
# App assembly
# ---------------------------------------------------------------------------

_SECTIONS = [
    ("Overview", build_overview_tab),
    ("Upload", build_upload_tab),
    ("Contract Library", build_library_tab),
    ("Risk Review", build_risk_review_tab),
    ("Ask ContractIQ", build_ask_tab),
    ("Document Sources", build_sources_tab),
    ("Relationships", build_relationships_tab),
    ("Review Tasks", build_tasks_tab),
    ("Reports", build_reports_tab),
    ("Activity & Traces", build_activity_tab),
]

_SIDEBAR_HTML = (
    '<div class="ciq-brand"><h2>Contract<span>IQ</span></h2>'
    '<p>Contract intelligence workspace</p></div>'
    '<p class="ciq-sidenote">Multi-agent risk analysis across <b>legal</b>, <b>financial</b> and '
    '<b>operational</b> dimensions. Every finding is grounded in retrieved evidence and independently '
    're-verified against the source document before you see it.</p>'
    '<div style="margin-top:14px">'
    '<span class="ciq-pill">Evidence-verified</span>'
    '<span class="ciq-pill">Traceable</span>'
    '<span class="ciq-pill">Human-in-the-loop</span></div>'
    '<p class="ciq-sidenote" style="margin-top:16px">Where this corpus cannot prove something, the app '
    'says so instead of guessing.</p>'
)


def build_app() -> gr.Blocks:
    """The full 10-section ContractIQ workspace: a left sidebar plus one tab
    per section, each backed by app_service.py — never a raw phase module."""
    with gr.Blocks(title="ContractIQ") as demo:
        with gr.Sidebar(label="ContractIQ", width=290):
            gr.HTML(_SIDEBAR_HTML)
        with gr.Tabs():
            for title, builder in _SECTIONS:
                with gr.Tab(title):
                    builder()
    return demo


def launch_app(**launch_kwargs):
    """Gradio 6 moved theme/css/head from the Blocks constructor to launch()."""
    theme = gr.themes.Soft(primary_hue="teal", secondary_hue="teal", neutral_hue="slate")
    return build_app().launch(theme=theme, css=_CSS, head=_HEAD, **launch_kwargs)
