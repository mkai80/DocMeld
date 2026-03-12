# Research: MVP PDF Data Pipeline

**Feature Branch**: `001-mvp-pdf-pipeline`
**Date**: 2026-03-12

## R1: PyMuPDF Element Extraction

**Decision**: Use `pymupdf4llm.to_markdown()` as primary extraction, parse markdown line-by-line to identify element types.

**Rationale**: Reference code (`reference_code.py`) demonstrates this approach successfully. `pymupdf4llm` preserves reading order, detects headers via `#` syntax, and formats tables as markdown pipes. This avoids complex layout analysis while meeting the lightweight constraint.

**Alternatives Considered**:
- Direct `fitz` text blocks: Loses table structure and heading hierarchy
- Custom ML layout detection: Violates Principle III (Lightweight by Default)
- `pdfplumber`: Additional dependency, less markdown-native output

## R2: Filename Sanitization

**Decision**: Replace dangerous path characters with underscores, normalize unicode to NFC, lowercase, truncate stem to 200 chars, append `_{hash6}` suffix from MD5.

**Rationale**: Cross-platform safety (Windows/macOS/Linux), human-readable filenames, collision resistance via MD5 (16M combinations with 6 hex digits).

**Alternatives Considered**:
- SHA256 instead of MD5: Overkill for filename uniqueness; MD5 is faster and sufficient
- Full hash as filename: Loses human readability
- No hash: Risk of collisions with same-named files

## R3: Title Hierarchy Tracking

**Decision**: Stack-based `TitleTracker` class. When a new title at level N is encountered, pop all titles at level >= N, then push. Render full stack as markdown headers at page start.

**Rationale**: Reference code (`reference_code2.py`) uses this pattern for `session_title`. Each silver page becomes self-contained with full context, which is critical for agent consumption.

**Alternatives Considered**:
- Flat title (last title only): Loses hierarchical context
- Breadcrumb string: Less structured than markdown headers
- No tracking: Pages lose context when titles span boundaries

## R4: DeepSeek API Integration

**Decision**: Use `langchain-deepseek` with `ChatDeepSeek(model="deepseek-chat", temperature=1.0)`. Structured output via Pydantic model. Exponential backoff (1s, 2s, 4s) for retries. Load API key from `DEEPSEEK_API_KEY` env var via `.env.local`.

**Rationale**: Reference code uses `langchain-deepseek` with structured output successfully. Temperature=1.0 per user requirement for data pipelines. Exponential backoff is industry standard for transient API failures.

**Alternatives Considered**:
- Direct HTTP/OpenAI SDK: Loses structured output parsing convenience
- Fixed retry delays: Less efficient than exponential backoff
- No retry: Unacceptable for production pipeline

## R5: Idempotency Strategy

**Decision**: File-existence checks per stage. Bronze checks for `.json`, Silver checks for `.jsonl`, Gold checks for `_gold.jsonl` with `description`/`keywords` fields in metadata.

**Rationale**: Simple, fast, reliable. No external state management needed. Supports incremental pipeline execution (run only stages that haven't completed).

**Alternatives Considered**:
- SQLite tracking database: Adds dependency, overkill for MVP
- Timestamp comparison: Fragile across filesystems
- Content hashing of outputs: Expensive for large files

## R6: Dependency Selection

**Decision**: Core dependencies for MVP:

| Package | Purpose | Version |
|---------|---------|---------|
| PyMuPDF | PDF parsing | >=1.23.0 |
| pymupdf4llm | Markdown extraction | >=0.0.10 |
| pandas | Table processing | >=2.0.0 |
| openpyxl | Excel output | >=3.1.0 |
| pydantic | Data models & validation | >=2.0.0 |
| python-dotenv | .env.local loading | >=1.0.0 |
| langchain-deepseek | DeepSeek API (gold stage) | >=0.1.0 |

**Dev dependencies**: pytest, pytest-cov, ruff, black, mypy

**Rationale**: Total core deps = 7 (under 10 limit per constitution). All are well-maintained, widely-used packages. `langchain-deepseek` is only needed for gold stage.

**Alternatives Considered**:
- `openai` SDK for DeepSeek: Less structured output support
- `tabulate` for tables: Unnecessary, markdown tables handled natively
- `click` for CLI: Extra dependency; `argparse` (stdlib) preferred
