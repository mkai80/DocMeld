# DocMeld - Product Requirements Document

**Version:** 1.0 MVP
**Date:** 2026-03-12
**License:** MIT
**Repository:** github.com/[username]/DocMeld
**Package:** `pip install docmeld`

---

## 1. Executive Summary

### 1.1 Vision
DocMeld is an open-source Python library that transforms complex documents (PDFs, DOCX, etc.) into agent-ready knowledge artifacts. In the age of AI agents, enterprise knowledge trapped in PDFs, research papers, and corporate documents needs to be converted into formats that LLMs can efficiently consume and act upon.

### 1.2 Market Position
Unlike existing solutions (MarkItDown, MinerU, Docling, Marker) that stop at format conversion (PDF → Markdown/JSON), DocMeld adds a critical second layer:

```
Document → [Parse] → Unified JSON → [Transform] → Agent Artifacts
                                                   (Prompts, Workflows, Claude Skills)
```

### 1.3 MVP Differentiation
- **No expensive models required**: MVP uses only PyMuPDF (fitz) - no OCR, VLM, or multimodal models
- **Lightweight & local-first**: Runs entirely locally without API costs
- **Agent-ready outputs**: Generates prompts, workflows, and Claude skills from documents
- **Unified format**: All documents convert to a standardized JSON element structure

---

## 2. Problem Statement

### 2.1 Current Challenges
1. **Knowledge Accessibility Gap**: Enterprise knowledge lives in formats LLMs can't efficiently consume
2. **Expensive Solutions**: Existing tools require OCR/VLM models that are costly and hard to run locally
3. **Format Conversion Only**: Most tools stop at Markdown/JSON without semantic transformation
4. **No Agent Integration**: No direct path from documents to agent prompts/workflows/skills

### 2.2 Target Users
- AI/ML engineers building agent systems
- Researchers processing academic papers
- Enterprise teams converting internal documentation
- Developers building RAG pipelines
- Teams using Claude Code and Claude skills

---

## 3. MVP Scope

### 3.1 In Scope
**Core Parsing (Phase 1 - MVP)**
- PDF parsing using PyMuPDF (fitz)
- Text extraction with layout preservation
- Table extraction to DataFrame/JSON
- Title/heading detection
- Image placeholder extraction (base64 encoding)
- Unified JSON element output format

**Output Formats**
- JSON (structured elements with page numbers)
- Markdown (human-readable)
- Excel (tables with metadata)

**Document Types**
- Digital-native PDFs (text-selectable)
- Simple DOCX files (future)

### 3.2 Out of Scope (MVP)
- OCR for scanned documents
- Vision Language Models (VLM)
- Multimodal AI models
- Complex layout analysis with ML models
- Real-time processing
- Cloud/API services
- GUI interface

### 3.3 Future Roadmap (Post-MVP)
- Agent artifact generation (prompts, workflows, Claude skills)
- OCR support for scanned documents
- Advanced table detection with ML
- DOCX, PPTX, XLSX support
- Batch processing pipeline
- CLI tool with rich output
- Integration with LangChain/LlamaIndex

---

## 4. Technical Architecture

### 4.1 Core Components

```
┌─────────────────────────────────────────────────────────┐
│                     DocMeld Core                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Document   │──────▶│   Parser     │               │
│  │   Loader     │      │   Engine     │               │
│  └──────────────┘      └──────┬───────┘               │
│                               │                         │
│                               ▼                         │
│                    ┌──────────────────┐                │
│                    │  Unified JSON    │                │
│                    │  Element Store   │                │
│                    └────────┬─────────┘                │
│                             │                           │
│              ┌──────────────┼──────────────┐           │
│              ▼              ▼              ▼           │
│         ┌────────┐    ┌─────────┐   ┌─────────┐      │
│         │  JSON  │    │Markdown │   │  Excel  │      │
│         │ Output │    │ Output  │   │ Output  │      │
│         └────────┘    └─────────┘   └─────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Unified JSON Element Format

Based on `reference_code.py`, the core data structure is a list of elements:

```json
[
  {
    "type": "title",
    "level": 0,
    "content": "Section Title",
    "page_no": 1
  },
  {
    "type": "text",
    "content": "Paragraph content...",
    "page_no": 1
  },
  {
    "type": "table",
    "summary": "Items: Revenue, Gross Margin, ...",
    "content": "| Header1 | Header2 |\n|---------|---------|...",
    "page_no": 2
  },
  {
    "type": "image",
    "image_name": "page001_image_001.png",
    "content": "Image description (optional)",
    "image": "base64_encoded_string",
    "page_no": 3,
    "image_id": "page001_image_001",
    "bbox": [x0, y0, x1, y1]
  }
]
```

**Element Types:**
- `title`: Headings with hierarchy level (0-5)
- `text`: Paragraph content
- `table`: Markdown tables with optional summary
- `image`: Images with base64 encoding and metadata

---

## 5. Functional Requirements

### 5.1 Document Parsing

**FR-1.1: PDF Loading**
- Load PDF files using PyMuPDF (fitz)
- Extract document metadata (page count, title, author)
- Handle multi-page documents

**FR-1.2: Text Extraction**
- Extract text while preserving layout structure
- Detect reading order (top-to-bottom, left-to-right)
- Preserve paragraph boundaries
- Handle multi-column layouts (basic)

**FR-1.3: Title Detection**
- Detect headings using markdown syntax (`#`, `##`, etc.)
- Assign hierarchy levels (0-5)
- Extract title content

**FR-1.4: Table Extraction**
- Detect markdown tables in content
- Parse tables to pandas DataFrame
- Generate table summaries (first column items)
- Filter small tables (≤1 data row)
- Output tables in multiple formats:
  - Markdown with `[[Table1]]` markers
  - Excel with multiple sheets
  - JSON with structured data

**FR-1.5: Image Handling**
- Extract images from PDF pages
- Save images as PNG files
- Encode images to base64
- Store image metadata (filename, page_no, bbox)
- Support pre-extracted images from directory

### 5.2 Output Generation

**FR-2.1: JSON Output**
- Generate unified JSON element list
- Include all element types with page numbers
- Preserve element order
- Save to `{filename}.json`

**FR-2.2: Markdown Output**
- Generate human-readable markdown
- Include page separators (`---`)
- Format tables with `[[Table1]]` markers
- Embed image references
- Save to `{filename}.md`

**FR-2.3: Excel Output**
- Create multi-sheet workbook
- Overview sheet with metadata and table summaries
- Individual sheets per table
- Apply formatting (column widths)
- Save to `{filename}.xlsx`

**FR-2.4: Table-Specific Outputs**
- Generate `{filename}_[tables].md` with only tables
- Include content overview with metadata
- Number valid tables only (>1 data row)
- Preserve table structure and formatting

### 5.3 Metadata Extraction

**FR-3.1: Document Metadata**
- Extract filename and path
- Generate unique UUID per document
- Track processing date
- Store output directory structure

**FR-3.2: Table Metadata**
- Generate table summaries (first column items)
- Count data rows
- Validate table structure
- Track table numbers

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **NFR-1.1**: Process typical PDF (10-50 pages) in <30 seconds
- **NFR-1.2**: Memory usage <500MB for documents up to 100 pages
- **NFR-1.3**: Support batch processing of multiple documents

### 6.2 Reliability
- **NFR-2.1**: Gracefully handle malformed PDFs
- **NFR-2.2**: Provide clear error messages
- **NFR-2.3**: Resume from existing outputs (skip re-processing)

### 6.3 Usability
- **NFR-3.1**: Simple API: `parser = DocMeldParser(pdf_path); parser.parse()`
- **NFR-3.2**: CLI tool: `docmeld parse input.pdf`
- **NFR-3.3**: Clear documentation with examples

### 6.4 Maintainability
- **NFR-4.1**: Modular architecture (parser, extractors, exporters)
- **NFR-4.2**: Comprehensive unit tests (>80% coverage)
- **NFR-4.3**: Type hints throughout codebase
- **NFR-4.4**: Follow PEP 8 style guidelines

### 6.5 Compatibility
- **NFR-5.1**: Python 3.8+
- **NFR-5.2**: Cross-platform (Windows, macOS, Linux)
- **NFR-5.3**: Minimal dependencies (PyMuPDF, pandas, openpyxl)

---

## 7. API Design

### 7.1 Core Parser Class

```python
from docmeld import DocMeldParser

# Initialize parser
parser = DocMeldParser(
    pdf_path="document.pdf",
    output_dir=None,  # Auto-create: {pdf_path_stem}/
)

# Parse document
result = parser.parse()

# Access parsed data
elements = parser.parsed_data  # List[Dict]
summary = parser.get_summary()  # Dict with stats

# Generate outputs
parser.save_json()      # {filename}.json
parser.save_markdown()  # {filename}.md
parser.save_excel()     # {filename}.xlsx
parser.save_tables()    # {filename}_[tables].md
```

### 7.2 Element Access

```python
# Filter by type
titles = [e for e in parser.parsed_data if e["type"] == "title"]
tables = [e for e in parser.parsed_data if e["type"] == "table"]
images = [e for e in parser.parsed_data if e["type"] == "image"]

# Filter by page
page_1_elements = [e for e in parser.parsed_data if e["page_no"] == 1]

# Access table data
for element in tables:
    markdown_table = element["content"]
    summary = element["summary"]
    page = element["page_no"]
```

### 7.3 CLI Interface

```bash
# Basic parsing
docmeld parse input.pdf

# Specify output directory
docmeld parse input.pdf --output-dir ./output

# Batch processing
docmeld parse *.pdf

# Output format selection
docmeld parse input.pdf --format json
docmeld parse input.pdf --format markdown
docmeld parse input.pdf --format excel
docmeld parse input.pdf --format all  # default
```

---

## 8. Data Models

### 8.1 Element Types

```python
from typing import Literal, Optional, Tuple
from pydantic import BaseModel

class BaseElement(BaseModel):
    type: str
    page_no: int

class TitleElement(BaseElement):
    type: Literal["title"]
    level: int  # 0-5
    content: str

class TextElement(BaseElement):
    type: Literal["text"]
    content: str

class TableElement(BaseElement):
    type: Literal["table"]
    content: str  # Markdown format
    summary: str  # "Items: Revenue, Margin, ..."

class ImageElement(BaseElement):
    type: Literal["image"]
    image_name: str
    content: str  # Optional description
    image: str  # base64 encoded
    image_id: str
    bbox: Tuple[float, float, float, float]

Element = TitleElement | TextElement | TableElement | ImageElement
```

### 8.2 Parser Result

```python
class ParseResult(BaseModel):
    total_pages: int
    total_elements: int
    text_blocks: int
    tables: int
    images: int
    charts: int
    output_dir: str
    files_generated: List[str]
```

---

## 9. File Structure

```
docmeld/
├── docmeld/
│   ├── __init__.py
│   ├── parser.py           # Core DocMeldParser class
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── text.py         # Text extraction
│   │   ├── tables.py       # Table extraction
│   │   ├── images.py       # Image extraction
│   │   └── titles.py       # Title detection
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── json.py         # JSON output
│   │   ├── markdown.py     # Markdown output
│   │   ├── excel.py        # Excel output
│   │   └── tables.py       # Table-specific output
│   ├── models.py           # Pydantic data models
│   ├── utils.py            # Helper functions
│   └── cli.py              # CLI interface
├── tests/
│   ├── test_parser.py
│   ├── test_extractors.py
│   ├── test_exporters.py
│   └── fixtures/
│       └── sample.pdf
├── examples/
│   ├── basic_usage.py
│   ├── batch_processing.py
│   └── custom_pipeline.py
├── docs/
│   ├── README.md
│   ├── installation.md
│   ├── quickstart.md
│   └── api_reference.md
├── pyproject.toml
├── setup.py
├── README.md
├── LICENSE (MIT)
└── .gitignore
```

---

## 10. Dependencies

### 10.1 Core Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.8"
pymupdf = "^1.23.0"  # PyMuPDF (fitz)
pandas = "^2.0.0"
openpyxl = "^3.1.0"
pydantic = "^2.0.0"
```

### 10.2 Development Dependencies
```toml
[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.5.0"
```

---

## 11. Testing Strategy

### 11.1 Unit Tests
- Test each extractor independently
- Test each exporter with mock data
- Test element type detection
- Test table parsing edge cases

### 11.2 Integration Tests
- End-to-end parsing of sample PDFs
- Verify output file generation
- Validate JSON structure
- Check Markdown formatting

### 11.3 Test Coverage
- Minimum 80% code coverage
- 100% coverage for core parser logic
- Edge case handling (empty pages, malformed tables)

### 11.4 Test Fixtures
- Simple PDF (1-5 pages, text only)
- Complex PDF (tables, images, multi-column)
- Scientific paper (equations, references)
- Financial report (dense tables)

---

## 12. Documentation Requirements

### 12.1 README.md
- Project overview and vision
- Quick start guide
- Installation instructions
- Basic usage examples
- Link to full documentation

### 12.2 API Documentation
- Docstrings for all public methods
- Type hints throughout
- Usage examples in docstrings
- Auto-generated API reference (Sphinx)

### 12.3 User Guides
- Installation guide
- Quickstart tutorial
- Advanced usage patterns
- Troubleshooting guide
- FAQ

### 12.4 Developer Documentation
- Architecture overview
- Contributing guidelines
- Development setup
- Testing guidelines
- Release process

---

## 13. Success Metrics

### 13.1 MVP Launch Criteria
- [ ] Parse digital-native PDFs with 90%+ accuracy
- [ ] Extract tables to DataFrame with correct structure
- [ ] Generate all output formats (JSON, MD, Excel)
- [ ] CLI tool functional
- [ ] Published to PyPI as `docmeld`
- [ ] Documentation complete
- [ ] Test coverage >80%
- [ ] 5+ example notebooks

### 13.2 Adoption Metrics (3 months post-launch)
- 100+ GitHub stars
- 1,000+ PyPI downloads
- 10+ community contributions
- 5+ issues resolved
- Featured in 1+ blog post/tutorial

### 13.3 Quality Metrics
- <5% error rate on test corpus
- <10 open bugs at any time
- <48 hour response time on issues
- 90%+ user satisfaction (surveys)

---

## 14. Risks and Mitigations

### 14.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| PyMuPDF limitations on complex layouts | High | Medium | Document limitations clearly; add ML-based layout detection in v2 |
| Table parsing accuracy issues | High | High | Implement robust markdown table parser; add validation |
| Large file memory issues | Medium | Low | Implement streaming/chunking for large PDFs |
| Dependency conflicts | Low | Medium | Pin versions; use poetry for dependency management |

### 14.2 Market Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Existing tools dominate market | Medium | High | Focus on agent-ready outputs as differentiator |
| PyPI name `docmeld` taken | Low | Low | Have backup names ready: `doc-meld`, `docmeld-ai`, `pymeld` |
| Low adoption due to limited OCR | Medium | Medium | Clear messaging about MVP scope; roadmap for OCR |

---

## 15. Release Plan

### 15.1 Phase 1: MVP (Weeks 1-4)
**Week 1-2: Core Development**
- Implement DocMeldParser class
- Build text and title extractors
- Build table extractor
- Build image extractor

**Week 3: Output Generation**
- Implement JSON exporter
- Implement Markdown exporter
- Implement Excel exporter
- Implement table-specific outputs

**Week 4: Polish & Release**
- Build CLI interface
- Write documentation
- Create examples
- Set up CI/CD
- Publish to PyPI

### 15.2 Phase 2: Enhancement (Weeks 5-8)
- Add DOCX support
- Improve table detection
- Add batch processing
- Performance optimization
- Community feedback integration

### 15.3 Phase 3: Agent Integration (Weeks 9-12)
- Design agent artifact format
- Implement prompt generation
- Implement workflow generation
- Implement Claude skill generation
- Integration examples

---

## 16. Open Questions

### 16.1 Technical Decisions
- **Q1**: Should we support Python 3.7 or require 3.8+?
  - **Decision**: Require 3.8+ for better type hints and performance

- **Q2**: Should MVP include basic DOCX support?
  - **Decision**: PDF only for MVP; DOCX in Phase 2

- **Q3**: How to handle images without OCR?
  - **Decision**: Extract and encode as base64; add placeholder text

### 16.2 Product Decisions
- **Q4**: Should we include a web UI in MVP?
  - **Decision**: No; CLI and library only for MVP

- **Q5**: Should we support streaming/incremental parsing?
  - **Decision**: Not in MVP; add if performance issues arise

---

## 17. Appendix

### 17.1 Reference Implementation
The MVP is based on `reference_code.py` which includes:
- `PDFParserFitz` class with proven parsing logic
- Table extraction and DataFrame conversion
- Markdown and Excel output generation
- Image handling with base64 encoding
- Metadata extraction patterns

### 17.2 Competitive Analysis Summary
From `market-analysis.md`:
- **MarkItDown** (87.5k stars): Fast but 25% PDF success rate
- **MinerU** (55.2k stars): Strong on complex layouts, AGPL license
- **Docling** (28k stars): IBM's toolkit, MIT license, ML-based
- **Marker** (22k stars): High accuracy, GPL license, LLM-optional
- **Unstructured** (14k stars): Enterprise standard, Apache license

**DocMeld's Advantage**: Lightweight, no ML models required, agent-ready outputs, MIT license

### 17.3 Naming Alternatives
If `docmeld` is taken on PyPI:
- `doc-meld`
- `docmeld-ai`
- `pymeld`
- `meld-docs`
- `docweaver`
- `docforge`

---

**Document Status**: Draft v1.0
**Next Review**: After MVP implementation
**Owner**: [Your Name]
**Contributors**: [Team Members]
