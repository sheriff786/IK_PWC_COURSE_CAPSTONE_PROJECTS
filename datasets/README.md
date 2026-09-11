# PwC Agentic AI Capstone — Datasets

Datasets for the PwC Agentic AI Capstone projects. Each folder contains the domain-specific documents (DOCX, PDF, XLSX) used across all 8 weeks of the project.

## Projects

| Folder | Domain | Contents |
|--------|--------|----------|
| `contract_intelligence/` | Contract Intelligence | MSAs, NDAs, SOWs, billing docs, compliance policies, negotiation trails |
| `ecommerce/` | E-commerce Intelligence | Agent I/O samples, flow documentation |
| `healthcare/` | Healthcare Clinical AI | Patient records, lab reports, allergy docs, radiology reports, medical glossary |
| `regulatory_compliance/` | Regulatory Compliance | Company policies, insurance regulations, audit/governance documents |

## Quick Start

### Option 1: Clone the entire repo

```bash
git clone https://github.com/AI-Project-Lab/IK-pwc-agenticai-datasets.git
```

### Option 2: Download a specific project's data

Use the provided download script (requires Python 3.8+):

```bash
# Download all datasets
python download_data.py --all

# Download a specific project
python download_data.py --project healthcare

# Download to a custom directory
python download_data.py --project healthcare --dest ./my_data/healthcare
```

### Option 3: Use in your notebook

The notebooks detect the data directory automatically. Set the `DATASET_REPO_PATH` environment variable or place this repo alongside your project repo:

```
parent_directory/
├── ik-pwc-agenticai-datasets/    # this repo
│   ├── contract_intelligence/
│   ├── ecommerce/
│   ├── healthcare/
│   └── regulatory_compliance/
└── ik-work-pwc-agenticai-projects/
    └── prod/weekwise_split/
```

## Data Format

All datasets are **unstructured documents** — primarily `.docx`, `.pdf`, and `.xlsx` files. The notebooks use `python-docx`, `pdfplumber`, and `openpyxl` to parse them at runtime.

## Versioning

Dataset versions are tagged (e.g., `v1.0`). Pin to a specific version if you need reproducibility:

```bash
git clone --branch v1.0 https://github.com/AI-Project-Lab/IK-pwc-agenticai-datasets.git
```
