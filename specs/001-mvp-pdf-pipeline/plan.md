# Implementation Plan: MVP PDF Data Pipeline

**Branch**: `001-mvp-pdf-pipeline` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mvp-pdf-pipeline/spec.md`

## Summary

Build a three-stage PDF processing pipeline (Bronze → Silver → Gold) that converts PDF documents into agent-ready knowledge artifacts. Bronze stage extracts structured elements (text, tables, titles, images) from PDFs using PyMuPDF. Silver stage transforms element lists into page-by-page JSONL with markdown formatting and title hierarchy tracking. Gold stage enriches pages with AI-generated descriptions and keywords using DeepSeek-chat. The pipeline is lightweight (no OCR/VLM), idempotent, and designed for batch processing with fail-fast disabled.

## Technical Context

**Language/Version**: Python 3.9+ (minimum supported per constitution)
**Primary Dependencies**: PyMuPDF (fitz), pandas, openpyxl, pydantic, python-dotenv, langchain-deepseek
**Storage**: Local filesystem (JSON, JSONL, log files)
**Testing**: pytest with pytest-cov (90%+ coverage target, 100% for core parser)
**Target Platform**: macOS, Linux, Windows (cross-platform)
**Project Type**: Single library project with CLI interface
**Performance Goals**: <5 min for 10-50 page PDF through all stages; <500MB memory for 100-page PDFs
**Constraints**: No OCR/VLM/multimodal models (lightweight by default); offline-capable for bronze/silver; API-dependent for gold
**Scale/Scope**: MVP handles digital-native PDFs; batch processing of 100+ files; 95% success rate target

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development (NON-NEGOTIABLE)
- ✅ **PASS**: Plan includes comprehensive test strategy with unit, integration, and contract tests
- ✅ **PASS**: TDD workflow enforced: tests written before implementation
- ✅ **PASS**: 90%+ coverage target specified; 100% for core parser logic

### Principle II: Library-First, PyPI-Ready
- ✅ **PASS**: Core designed as importable library (`from docmeld import DocMeldParser`)
- ✅ **PASS**: CLI built on top of library API
- ✅ **PASS**: Type hints and docstrings required throughout
- ✅ **PASS**: Semantic versioning planned (0.1.0 for MVP)

### Principle III: Lightweight by Default
- ✅ **PASS**: Only PyMuPDF (fitz) for PDF parsing - no OCR/VLM
- ✅ **PASS**: Core dependencies under 10 packages
- ✅ **PASS**: Offline-capable for bronze/silver stages
- ✅ **PASS**: Memory constraint: <500MB for 100-page PDFs

### Principle IV: Unified Element Format
- ✅ **PASS**: JSON element structure defined with 4 types: text, table, title, image
- ✅ **PASS**: All elements include `type` and `page_no` fields
- ✅ **PASS**: Element order preserves document reading order
- ⚠️ **ACTION REQUIRED**: JSON Schema validation to be added in Phase 1

### Principle V: Agent-Ready Outputs
- ✅ **PASS**: Three output formats: JSON (structured), JSONL (page-based), Gold JSONL (enriched)
- ✅ **PASS**: Table summaries and metadata for agent consumption
- ✅ **PASS**: Source attribution preserved (page numbers, filenames)

### Principle VI: Production-Grade Quality
- ✅ **PASS**: Ruff linting, black formatting, mypy type checking planned
- ✅ **PASS**: Explicit error handling with context logging
- ✅ **PASS**: Graceful handling of malformed PDFs (partial results + warnings)
- ✅ **PASS**: CI/CD with GitHub Actions planned

### Principle VII: Open-Source Excellence
- ✅ **PASS**: MIT license confirmed
- ✅ **PASS**: README, CONTRIBUTING.md, CHANGELOG.md planned
- ✅ **PASS**: Automated releases to PyPI via CI/CD

**Gate Status**: ✅ **PASSED** (1 action item: add JSON Schema validation in Phase 1)

## Project Structure

### Documentation (this feature)

```text
specs/001-mvp-pdf-pipeline/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0 output (to be generated)
├── data-model.md        # Phase 1 output (to be generated)
├── quickstart.md        # Phase 1 output (to be generated)
└── contracts/           # Phase 1 output (to be generated)
    └── element-schema.json
```

### Source Code (repository root)

```text
docmeld/
├── docmeld/
│   ├── __init__.py                 # Public API exports
│   ├── parser.py                   # DocMeldParser main class
│   ├── bronze/
│   │   ├── __init__.py
│   │   ├── processor.py            # Bronze stage orchestrator
│   │   ├── filename_sanitizer.py   # Filename sanitization + MD5 hashing
│   │   ├── element_extractor.py    # PyMuPDF element extraction
│   │   └── element_types.py        # Pydantic models for elements
│   ├── silver/
│   │   ├── __init__.py
│   │   ├── processor.py            # Silver stage orchestrator
│   │   ├── page_aggregator.py      # Group elements by page
│   │   ├── title_tracker.py        # Title hierarchy tracking
│   │   └── markdown_renderer.py    # Render elements to markdown
│   ├── gold/
│   │   ├── __init__.py
│   │   ├── processor.py            # Gold stage orchestrator
│   │   ├── deepseek_client.py      # DeepSeek API wrapper
│   │   └── metadata_extractor.py   # Extract description + keywords
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py              # Timestamped log file setup
│   │   ├── progress.py             # Progress indicators
│   │   └── env_loader.py           # .env.local loading
│   └── cli.py                      # CLI interface (argparse)
├── tests/
│   ├── conftest.py                 # Pytest fixtures
│   ├── fixtures/
│   │   ├── sample_simple.pdf       # Simple test PDF
│   │   ├── sample_complex.pdf      # Complex test PDF (tables, images)
│   │   └── expected_outputs/       # Expected JSON/JSONL outputs
│   ├── unit/
│   │   ├── test_filename_sanitizer.py
│   │   ├── test_element_extractor.py
│   │   ├── test_title_tracker.py
│   │   ├── test_markdown_renderer.py
│   │   └── test_deepseek_client.py
│   ├── integration/
│   │   ├── test_bronze_pipeline.py
│   │   ├── test_silver_pipeline.py
│   │   ├── test_gold_pipeline.py
│   │   └── test_end_to_end.py
│   └── contract/
│       └── test_element_schema.py  # Validate JSON Schema compliance
├── examples/
│   ├── basic_usage.py
│   ├── batch_processing.py
│   └── custom_pipeline.py
├── docs/
│   ├── installation.md
│   ├── quickstart.md
│   └── api_reference.md
├── .github/
│   └── workflows/
│       ├── test.yml                # Run tests on push/PR
│       ├── lint.yml                # Ruff + black + mypy
│       └── publish.yml             # Publish to PyPI on tag
├── pyproject.toml                  # PEP 621 project metadata
├── setup.py                        # Fallback for older pip
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE                         # MIT
├── .gitignore
├── .env.local.example              # Example env file
└── venv/                           # Python virtual environment (gitignored)
```

**Structure Decision**: Single library project (Option 1) selected. This is a pure Python library with CLI, no web/mobile components. The three-stage pipeline (bronze/silver/gold) is organized as subpackages under `docmeld/` for clear separation of concerns.

## Complexity Tracking

> **No violations detected** - all constitution principles satisfied.

---

# Phase 0: Research & Technology Decisions

## Research Tasks

### R1: PyMuPDF (fitz) Best Practices for Element Extraction
**Question**: What are the best practices for extracting text, tables, and images from PDFs using PyMuPDF while preserving reading order?

**Findings** (from reference_code.py analysis):
- Use `pymupdf4llm.to_markdown()` for text extraction with layout preservation
- Markdown output naturally includes title detection (`#` headers) and table detection (`|` pipes)
- Parse markdown line-by-line to identify element types (title, text, table)
- Images must be extracted separately using `glob` pattern matching for pre-extracted PNG files
- Base64 encode images for JSON storage
- Reading order is preserved by pymupdf4llm's markdown output

**Decision**: Use `pymupdf4llm.to_markdown()` as primary extraction method, supplemented with image file discovery.

**Rationale**: Reference code demonstrates this approach successfully extracts structured content while maintaining reading order. Avoids complex layout analysis algorithms.

**Alternatives Considered**:
- Direct fitz text extraction: Loses layout structure and table formatting
- Custom layout analysis: Too complex for MVP, violates lightweight principle

### R2: Filename Sanitization Strategy
**Question**: What characters must be removed/replaced to ensure cross-platform filesystem compatibility?

**Findings**:
- Dangerous characters: `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`
- Unicode normalization recommended for cross-platform compatibility
- Filename length limits: 255 bytes on most filesystems; spec requires 200 char truncation
- MD5 hash provides collision-resistant uniqueness (6-digit suffix = 16M combinations)

**Decision**: Replace dangerous characters with underscores, normalize unicode, truncate to 200 chars, append 6-digit MD5 suffix.

**Rationale**: Balances safety (cross-platform), uniqueness (MD5), and readability (truncation preserves meaningful prefix).

**Alternatives Considered**:
- Full MD5 hash as filename: Loses human readability
- No truncation: Risk of filesystem errors on long filenames

### R3: Title Hierarchy Tracking Across Pages
**Question**: How should title hierarchy be maintained when titles span multiple pages?

**Findings** (from reference_code2.py analysis):
- Maintain a "title stack" that tracks current hierarchy (H1, H2, H3, etc.)
- When a new title is encountered, pop stack to appropriate level, then push new title
- At page boundaries, include full title stack at beginning of page content
- This ensures each page is self-contained with context

**Decision**: Implement `TitleTracker` class with stack-based hierarchy management.

**Rationale**: Reference code demonstrates this pattern successfully. Each page becomes independently understandable for agents.

**Alternatives Considered**:
- No hierarchy tracking: Pages lose context when titles span boundaries
- Reference-based linking: Requires agents to follow references, breaks self-containment

### R4: DeepSeek API Integration for Gold Stage
**Question**: What are best practices for DeepSeek API integration with retry logic and rate limiting?

**Findings**:
- Use `langchain-deepseek` library for structured output (Pydantic models)
- Temperature=1.0 recommended for data pipelines (per user requirement)
- Exponential backoff: 1s, 2s, 4s for 3 retries
- Rate limiting: DeepSeek has per-minute limits; batch processing should include delays
- API key via environment variable (DEEPSEEK_API_KEY) is standard practice

**Decision**: Use `langchain-deepseek` with `ChatDeepSeek` model, implement exponential backoff wrapper, load API key from `.env.local`.

**Rationale**: Langchain integration provides structured output parsing. Exponential backoff handles transient failures. Environment variables prevent credential leakage.

**Alternatives Considered**:
- Direct HTTP requests: More complex, loses structured output benefits
- Fixed retry delays: Less efficient than exponential backoff

### R5: Idempotency Strategy for Pipeline Stages
**Question**: How should the pipeline detect and skip already-processed files?

**Findings**:
- Bronze: Check for existence of `{filename_hash6}.json` file
- Silver: Check for existence of `{filename_hash6}.jsonl` file
- Gold: Check for presence of `description` and `keywords` fields in JSONL metadata
- File-based detection is simple and reliable for local filesystem

**Decision**: Each stage checks for output file existence before processing. Gold stage additionally validates metadata fields.

**Rationale**: Simple, fast, and reliable. Avoids re-processing overhead. Supports incremental pipeline execution.

**Alternatives Considered**:
- Database tracking: Overkill for MVP, adds dependency
- Timestamp comparison: Fragile, doesn't handle partial failures

---

# Phase 1: Design & Contracts

## Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Key Entities**:
1. **BronzeElement** (base class with 4 subtypes: TitleElement, TextElement, TableElement, ImageElement)
2. **SilverPage** (metadata + page_content)
3. **GoldPage** (SilverPage + description + keywords)
4. **ProcessingResult** (summary statistics)

## API Contracts

See [contracts/element-schema.json](./contracts/element-schema.json) for JSON Schema.

**Public API Surface**:

```python
# Main entry point
class DocMeldParser:
    def __init__(self, pdf_path: str, output_dir: Optional[str] = None)
    def process_bronze(self) -> BronzeResult
    def process_silver(self, bronze_json_path: str) -> SilverResult
    def process_gold(self, silver_jsonl_path: str) -> GoldResult
    def process_all(self) -> ProcessingResult

# CLI interface
def main(args: List[str]) -> int
```

## Quickstart

See [quickstart.md](./quickstart.md) for complete getting started guide.

**5-line example**:
```python
from docmeld import DocMeldParser

parser = DocMeldParser("document.pdf")
result = parser.process_all()
print(f"Processed {result.total_pages} pages")
```

---

# Implementation Notes

## Bronze Stage Implementation Details

**Filename Sanitization Algorithm**:
1. Extract stem from Path object
2. Replace dangerous chars (`/\:*?"<>|`) with underscores
3. Normalize unicode (NFC form)
4. Truncate to 200 characters
5. Calculate MD5 hash of original PDF bytes
6. Append last 6 digits of hash: `{sanitized_stem}_{hash6}`

**Element Extraction Flow**:
1. Open PDF with `fitz.open(pdf_path)`
2. For each page:
   - Call `pymupdf4llm.to_markdown(doc, pages=[page_num])`
   - Parse markdown line-by-line:
     - Lines starting with `#` → TitleElement (count `#` for level)
     - Lines starting with `|` → accumulate in table_buffer
     - Other lines → accumulate in text_buffer
     - Empty lines → flush buffers to elements list
   - Search for image files: `{output_dir}/page{N:03d}_*.png`
   - Base64 encode images, create ImageElement
3. Return ordered list of elements

**Table Summary Generation**:
- Parse markdown table to extract first column values
- Format as: `"Items: {item1}, {item2}, ... (+N more)"`
- Skip tables with ≤1 data row (small tables use `[[Table]]` without number)

## Silver Stage Implementation Details

**Page Aggregation Algorithm**:
1. Load bronze JSON (list of elements)
2. Group elements by `page_no` field
3. For each page:
   - Generate UUID for page
   - Initialize metadata dict
   - Process elements in order

**Title Hierarchy Tracking**:
```python
class TitleTracker:
    def __init__(self):
        self.stack = []  # [(level, content), ...]

    def update(self, level: int, content: str):
        # Pop stack until we find parent level
        while self.stack and self.stack[-1][0] >= level:
            self.stack.pop()
        self.stack.append((level, content))

    def get_hierarchy_markdown(self) -> str:
        # Render stack as markdown headers
        return "\n".join(f"{'#' * (lvl + 1)} {txt}" for lvl, txt in self.stack)
```

**Markdown Rendering**:
- Title elements: `{'#' * (level + 1)} {content}`
- Text elements: `{content}` (preserve newlines)
- Table elements: `[[Table{N}]]\n{content}\n[/Table{N}]` (global numbering)
- Image elements: `![{image_name}](data:image/png;base64,{image})`

**Global Table Numbering**:
- Maintain counter across all pages
- Only increment for tables with >1 data row
- Small tables use `[[Table]]` without number

## Gold Stage Implementation Details

**DeepSeek API Call**:
```python
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel

class PageMetadata(BaseModel):
    description: str
    keywords: List[str]

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=1.0,
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
structured_llm = llm.with_structured_output(PageMetadata)

prompt = f"Analyze this page and extract a one-line description and keywords:\n\n{page_content}"
metadata = structured_llm.invoke(prompt)
```

**Retry Logic with Exponential Backoff**:
```python
def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
```

**Batch Processing Strategy**:
- Process pages sequentially (not parallel) to avoid rate limits
- Add 0.5s delay between API calls
- Continue on failure, mark page with `"gold_processing_failed": true`

## Logging Strategy

**Log File Format**: `docmeld_YYYYMMDD_HHMMSS.log` in current working directory

**Log Levels**:
- ERROR: File processing failures, API errors
- WARNING: Skipped files, partial results
- INFO: Progress indicators, stage completion
- DEBUG: Detailed element extraction info

**Log Context**: Every log entry includes:
- Timestamp
- Level
- Filename (if applicable)
- Page number (if applicable)
- Error message with stack trace (for errors)

## Progress Indicators

**Batch Processing**:
```
Processing PDFs: 3/10 (30%) - current: research_report.pdf
Bronze stage: 5/10 pages processed
Silver stage: Converting page 3/5
Gold stage: Enriching page 2/5 (API call)
```

**Summary Report**:
```
=== DocMeld Processing Summary ===
Total files: 10
Successful: 9
Failed: 1
  - corrupted_file.pdf: PyMuPDF error (file unreadable)
Processing time: 4m 32s
Output directory: /path/to/documents/
Log file: docmeld_20260312_143022.log
```

---

# Testing Strategy

## Unit Tests (tests/unit/)

**test_filename_sanitizer.py**:
- Test dangerous character replacement
- Test unicode normalization
- Test truncation at 200 chars
- Test MD5 hash calculation
- Test collision resistance (different files, same name)

**test_element_extractor.py**:
- Test title detection from markdown headers
- Test table detection from markdown pipes
- Test text extraction
- Test image file discovery and base64 encoding
- Test element ordering preservation

**test_title_tracker.py**:
- Test hierarchy stack management
- Test level transitions (H1 → H2 → H1)
- Test markdown rendering of hierarchy
- Test empty stack handling

**test_markdown_renderer.py**:
- Test title rendering with correct `#` count
- Test table marker formatting `[[Table1]]`
- Test global table numbering
- Test small table handling (no number)

**test_deepseek_client.py**:
- Test API call with mock responses
- Test retry logic with exponential backoff
- Test rate limiting delays
- Test error handling (API unavailable)

## Integration Tests (tests/integration/)

**test_bronze_pipeline.py**:
- Test single PDF processing end-to-end
- Test batch folder processing
- Test idempotency (re-run skips existing)
- Test malformed PDF handling (partial results)

**test_silver_pipeline.py**:
- Test bronze JSON → silver JSONL conversion
- Test page-by-page structure (one line per page)
- Test title hierarchy across pages
- Test global table numbering

**test_gold_pipeline.py**:
- Test silver JSONL → gold JSONL enrichment
- Test DeepSeek API integration (with mock)
- Test retry logic on failures
- Test partial failure handling (continue processing)

**test_end_to_end.py**:
- Test full pipeline: PDF → bronze → silver → gold
- Test batch processing with mixed success/failure
- Test summary report generation
- Test log file creation

## Contract Tests (tests/contract/)

**test_element_schema.py**:
- Validate bronze JSON against JSON Schema
- Validate silver JSONL against schema
- Validate gold JSONL against schema
- Test schema versioning (future-proofing)

## Test Fixtures

**sample_simple.pdf**: 3-page PDF with text and one table
**sample_complex.pdf**: 10-page PDF with tables, images, multi-level titles
**expected_outputs/**: Pre-generated JSON/JSONL for comparison

---

# Development Workflow

1. **Setup venv**: `python3 -m venv venv && source venv/bin/activate`
2. **Install deps**: `pip install -e ".[dev]"`
3. **Write tests**: Create failing tests for feature
4. **Implement**: Write minimum code to pass tests
5. **Lint**: `ruff check . && black --check . && mypy docmeld/`
6. **Test**: `pytest --cov=docmeld --cov-report=term-missing`
7. **Commit**: `git commit -m "feat: add bronze stage processor"`
8. **PR**: Open PR, wait for CI green, get review
9. **Merge**: Squash-merge to main

---

# Deployment & Release

**Version**: 0.1.0 (MVP)

**PyPI Release Checklist**:
1. Update CHANGELOG.md with release notes
2. Bump version in pyproject.toml
3. Tag release: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions automatically builds and publishes to PyPI

**CI/CD Pipeline** (.github/workflows/):
- **test.yml**: Run pytest on push/PR (Python 3.9, 3.10, 3.11, 3.12)
- **lint.yml**: Run ruff, black, mypy on push/PR
- **publish.yml**: Build wheel, publish to PyPI on tag push

---

# Open Questions & Risks

## Resolved in Clarification Session
- ✅ Batch error handling: Continue processing (fail-fast disabled)
- ✅ Gold output file: Separate `_gold` suffix file
- ✅ Log file location: Timestamped in current working directory
- ✅ DeepSeek API config: Environment variables with `.env.local` support
- ✅ Table numbering: Global across document

## Remaining Risks

**Risk**: PyMuPDF may not extract tables correctly from complex layouts
**Mitigation**: Document limitations in README; add ML-based table detection in future version

**Risk**: DeepSeek API rate limits may slow gold processing
**Mitigation**: Add configurable delay between API calls; support batch size limits

**Risk**: Large PDFs (>100 pages) may exceed memory constraints
**Mitigation**: Implement streaming/chunking if needed; document limits in README

---

**Plan Status**: Complete - Ready for Phase 2 (Task Generation)
**Next Command**: `/speckit.tasks`
