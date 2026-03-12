# Quickstart: DocMeld MVP PDF Pipeline

**Feature Branch**: `001-mvp-pdf-pipeline`
**Date**: 2026-03-12

## Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install docmeld
pip install docmeld
```

## Setup

Create a `.env.local` file in your project root (required for gold stage only):

```bash
DEEPSEEK_API_KEY=your_api_key_here
# Optional: custom endpoint
# DEEPSEEK_API_ENDPOINT=https://api.deepseek.com
```

## Usage: Python API

### Process a single PDF (all stages)

```python
from docmeld import DocMeldParser

parser = DocMeldParser("document.pdf")
result = parser.process_all()
print(f"Processed {result.total_files} files, {result.successful} successful")
```

### Process a folder of PDFs

```python
from docmeld import DocMeldParser

parser = DocMeldParser("/path/to/pdf/folder/")
result = parser.process_all()
print(f"{result.successful}/{result.total_files} files processed")
```

### Run individual stages

```python
from docmeld import DocMeldParser

parser = DocMeldParser("document.pdf")

# Bronze: PDF → JSON (elements list)
bronze = parser.process_bronze()
print(f"Bronze: {bronze.output_path}")

# Silver: JSON → JSONL (page-by-page)
silver = parser.process_silver(bronze.output_path)
print(f"Silver: {silver.output_path}")

# Gold: JSONL → enriched JSONL (descriptions + keywords)
gold = parser.process_gold(silver.output_path)
print(f"Gold: {gold.output_path}")
```

## Usage: CLI

```bash
# Process single PDF (all stages)
docmeld process document.pdf

# Process folder
docmeld process /path/to/pdfs/

# Run specific stage
docmeld bronze document.pdf
docmeld silver document_a3f5c2/document_a3f5c2.json
docmeld gold document_a3f5c2/document_a3f5c2.jsonl
```

## Output Structure

After processing `research_report.pdf`:

```
research_report.pdf                          # Original PDF
research_report_a3f5c2/                      # Output folder
├── research_report_a3f5c2.json              # Bronze: element list
├── research_report_a3f5c2.jsonl             # Silver: page-by-page
└── research_report_a3f5c2_gold.jsonl        # Gold: enriched with AI metadata
docmeld_20260312_143022.log                  # Processing log
```

## Verification

```python
import json

# Check bronze output
with open("research_report_a3f5c2/research_report_a3f5c2.json") as f:
    elements = json.load(f)
print(f"Bronze: {len(elements)} elements extracted")

# Check silver output
with open("research_report_a3f5c2/research_report_a3f5c2.jsonl") as f:
    pages = [json.loads(line) for line in f]
print(f"Silver: {len(pages)} pages")

# Check gold output
with open("research_report_a3f5c2/research_report_a3f5c2_gold.jsonl") as f:
    gold_pages = [json.loads(line) for line in f]
    first = gold_pages[0]
print(f"Gold: description='{first['metadata']['description']}'")
print(f"Gold: keywords={first['metadata']['keywords']}")
```
