"""
ContractIQ — one-time project scaffolding script.

Run this ONCE from the PWC_CONTRACTIQ_PROJECT_IK root:

    python setup_project_structure.py

Safety guarantees:
- Never touches ContractIQ_data_reserve/, design/, or anything already
  inside Research/ (Week-1..8 Assignment.ipynb, chroma_contracts_db/,
  deployment/, lib/, Backend_Implementation_Roadmap.md,
  ContractIQ_Notebook_Analysis.md, ContractIQ_Project_Execution_Roadmap.md,
  Langfuse_Setup_Guide.docx.pdf, contract_eda.png, contract_knowledge_graph.*).
- Every directory/file below is existence-checked first — nothing is ever
  overwritten. Safe to re-run any time; a second run just reports
  "exists" for everything and creates nothing new.
- Does NOT create config.py / models.py / ingestion.py inside
  src/contractiq/ — those already have real content (from earlier in this
  build) and must be copied in by hand so this script can never clobber
  them. It only creates the __init__.py files and the modules that don't
  exist anywhere yet.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Plain directories to create if missing.
NEW_DIRECTORIES = [
    "src/contractiq",
    "artifacts/manifests",
    "artifacts/parsed_documents",
    "artifacts/evaluations",
    "artifacts/reports",
    "chroma_contracts_db",   # fresh store for the new pipeline — kept
                              # separate from Research/chroma_contracts_db (legacy)
    "tests",
]

# src/contractiq modules with no real implementation yet — created as
# minimal, import-safe stubs so `from src.contractiq import agents` etc.
# never breaks a notebook while later phases are still being written.
PENDING_MODULES = {
    "src/contractiq/extraction.py": "Phase 2 - entity, clause, and date/amount extraction.",
    "src/contractiq/retrieval.py": "Phase 3 - chunking, embeddings, and ChromaDB retrieval.",
    "src/contractiq/agents.py": "Phase 4-5 - Legal, Financial, and Operational specialist agents.",
    "src/contractiq/orchestration.py": "Phase 5 - parallel execution and consensus building.",
    "src/contractiq/graph.py": "Phase 6 - NetworkX relationship graph and PyVis rendering.",
    "src/contractiq/evaluation.py": "Phase 7 - evaluation set, metrics, and Langfuse scoring.",
    "src/contractiq/reporting.py": "Phase 7 - evidence-linked, versioned report generation.",
    "src/contractiq/app_service.py": "Phase 8-9 - Gradio wiring and FastAPI adapter.",
}

# Our own phase notebooks in Research/ — distinct 00_.. 08_.. naming so
# there is zero collision with the existing Week-1..8 Assignment.ipynb files.
PENDING_NOTEBOOKS = {
    "Research/00_Project_Setup.ipynb": "Phase 0 - environment, config, manifest",
    "Research/01_Data_Manifest_and_Parsing.ipynb": "Phase 1 - DOCX parsing, evidence locations",
    "Research/02_Entity_Clause_and_EDA.ipynb": "Phase 2 - entities, normalization, corpus EDA",
    "Research/03_Retrieval_and_ChromaDB.ipynb": "Phase 3 - chunking, embeddings, retrieval eval",
    "Research/04_Legal_Risk_Agent.ipynb": "Phase 4 - first evidence-grounded legal agent",
    "Research/05_Multi_Agent_Orchestration.ipynb": "Phase 5 - financial + operational agents, consensus",
    "Research/06_Knowledge_Graph.ipynb": "Phase 6 - verified contract relationship graph",
    "Research/07_Evaluation_and_Observability.ipynb": "Phase 7 - eval set, Langfuse scores, reports",
    "Research/08_Gradio_Integration.ipynb": "Phase 8 - complete tab-based ContractIQ application",
}


def _minimal_notebook(title: str) -> dict:
    """A valid, empty .ipynb (nbformat 4) with one markdown title cell."""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# {title}\n", "\n", "_Scaffolded placeholder — not yet implemented._"],
            }
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _module_stub(description: str) -> str:
    return f'"""\nContractIQ - {description}\n\nNot yet implemented.\n"""\n'


def create_directories() -> None:
    for rel_path in NEW_DIRECTORIES:
        path = PROJECT_ROOT / rel_path
        if path.exists():
            print(f"  exists   {rel_path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"  created  {rel_path}")


def create_init_files() -> None:
    for rel_path in ["src/__init__.py", "src/contractiq/__init__.py", "tests/__init__.py"]:
        path = PROJECT_ROOT / rel_path
        if path.exists():
            print(f"  exists   {rel_path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
            print(f"  created  {rel_path}")


def create_module_stubs() -> None:
    for rel_path, description in PENDING_MODULES.items():
        path = PROJECT_ROOT / rel_path
        if path.exists():
            print(f"  exists   {rel_path}   (already has real content — left alone)")
        else:
            path.write_text(_module_stub(description), encoding="utf-8")
            print(f"  created  {rel_path}   (stub)")


def create_notebook_stubs() -> None:
    for rel_path, title in PENDING_NOTEBOOKS.items():
        path = PROJECT_ROOT / rel_path
        if path.exists():
            print(f"  exists   {rel_path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(_minimal_notebook(title), indent=1), encoding="utf-8")
            print(f"  created  {rel_path}")


def main() -> None:
    print(f"Scaffolding ContractIQ project at: {PROJECT_ROOT}\n")

    print("Directories:")
    create_directories()

    print("\nPackage __init__.py files:")
    create_init_files()

    print("\nsrc/contractiq module stubs (Phase 2-9, only if missing):")
    create_module_stubs()

    print("\nResearch/ phase notebooks (00-08, only if missing):")
    create_notebook_stubs()

    print(
        "\nDone. Nothing under ContractIQ_data_reserve/, design/, or your existing "
        "Research/ files (Week-1..8 Assignment.ipynb, chroma_contracts_db/, "
        "deployment/, lib/, the two roadmap/analysis docs) was touched.\n"
        "\nNext manual step: copy config.py, models.py, and ingestion.py "
        "(already built) into src/contractiq/ — this script deliberately "
        "does not write those so it can never overwrite real work."
    )


if __name__ == "__main__":
    main()
