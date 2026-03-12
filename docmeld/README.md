# DocMeld

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Lightweight PDF to agent-ready knowledge pipeline**

DocMeld converts PDF documents into structured, agent-consumable formats without requiring expensive OCR, VLM, or multimodal models. Built for the age of AI agents.

## Features

- **🪶 Lightweight**: Uses only PyMuPDF (fitz) — no OCR/VLM required
- **📄 Three-stage pipeline**: Bronze (elements) → Silver (pages) → Gold (AI metadata)
- **🤖 Agent-ready outputs**: JSON, JSONL, and AI-enriched metadata
- **⚡ Fast & local**: Runs entirely offline (except gold stage)
- **🔄 Idempotent**: Skip re-processing of existing outputs
- **📦 PyPI-ready**: `pip install docmeld`

## Installation

```bash
pip install docmeld
```

## Quick Start

### Python API

```python
from docmeld import DocMeldParser

# Process a single PDF through all stages
parser = DocMeldParser("document.pdf")
result = parser.process_all()
print(f"Processed {result.successful} files")
```

### CLI

```bash
# Full pipeline
docmeld process document.pdf

# Individual stages
docmeld bronze document.pdf
docmeld silver document_abc123/document_abc123.json
docmeld gold document_abc123/document_abc123.jsonl
```

## Pipeline Stages

### Bronze: PDF → Structured JSON

Extracts elements (text, tables, titles, images) from PDFs:

```json
[
  {"type": "title", "level": 0, "content": "Executive Summary", "page_no": 1},
  {"type": "text", "content": "The company reported...", "page_no": 1},
  {"type": "table", "content": "| Metric | Value |...", "summary": "Items: Revenue, EBITDA", "page_no": 2}
]
```

### Silver: JSON → Page-by-Page JSONL

Transforms elements into page-based documents with title hierarchy:

```json
{
  "metadata": {
    "uuid": "...",
    "source": "document.pdf",
    "page_no": "page1",
    "session_title": "# Executive Summary\n"
  },
  "page_content": "# Executive Summary\n\nThe company reported..."
}
```

### Gold: JSONL → AI-Enriched Metadata

Adds descriptions and keywords using DeepSeek-chat:

```json
{
  "metadata": {
    "description": "Company reports strong Q2 results with revenue growth",
    "keywords": ["revenue", "EBITDA", "quarterly results", "growth"]
  }
}
```

## Configuration

Create `.env.local` for gold stage (AI enrichment):

```bash
DEEPSEEK_API_KEY=your_key_here
# Optional: custom endpoint
# DEEPSEEK_API_ENDPOINT=https://api.deepseek.com
```

## Output Structure

After processing `research_report.pdf`:

```
research_report.pdf                          # Original PDF
research_report_a3f5c2/                      # Output folder
├── research_report_a3f5c2.json              # Bronze: element list
├── research_report_a3f5c2.jsonl             # Silver: page-by-page
└── research_report_a3f5c2_gold.jsonl        # Gold: AI-enriched
docmeld_20260312_143022.log                  # Processing log
```

## Roadmap

- [x] MVP: Bronze, Silver, Gold pipeline
- [x] CLI interface
- [x] PyPI package
- [ ] DOCX support
- [ ] OCR for scanned PDFs (optional extra)
- [ ] Agent prompt generation
- [ ] Claude skill generation

## Development

```bash
# Clone and setup
git clone https://github.com/[username]/docmeld.git
cd docmeld
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest --cov=docmeld

# Lint and format
ruff check docmeld/
black docmeld/
mypy docmeld/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{docmeld2026,
  title = {DocMeld: Lightweight PDF to Agent-Ready Knowledge Pipeline},
  year = {2026},
  url = {https://github.com/[username]/docmeld}
}
```
