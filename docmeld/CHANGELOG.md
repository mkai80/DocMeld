# Changelog

All notable changes to DocMeld will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `element_id` and `parent_id` fields on all element types for cross-referencing and parent-child hierarchy
- `table_data` structured dict on TableElement with headers, rows, num_rows, num_cols
- `parse_table_data()` function to extract cell-level structure from markdown tables
- `ParserBackend` protocol for swappable PDF parsing engines
- `PyMuPDFBackend` — extracted from existing element_extractor logic
- `DoclingBackend` — optional second engine (`pip install docmeld[docling]`)
- `--backend` CLI flag on `bronze` and `process` commands (choices: pymupdf, docling)
- `backend` parameter threaded through `DocMeldParser`, `BronzeProcessor`, and `extract_elements`
- 35 new tests (144 total) covering new fields, backends, dispatch, and schema contract

## [0.1.0] - 2026-03-12

### Added

#### Bronze Stage
- PDF to structured JSON element extraction using PyMuPDF
- Filename sanitization with MD5 hash suffix for uniqueness
- Support for text, table, title, and image element types
- Automatic table summary generation from first column
- Idempotent processing (skip re-processing existing outputs)
- Batch folder processing with fail-fast disabled

#### Silver Stage
- JSON to page-by-page JSONL conversion
- Title hierarchy tracking across pages
- Markdown rendering with global table numbering
- Self-contained pages with full title context
- Small table handling (≤1 data row, no numbering)

#### Gold Stage
- AI-powered metadata extraction using DeepSeek-chat
- Description and keyword generation per page
- Exponential backoff retry logic (3 attempts)
- Error resilience (continue on per-page failures)
- Separate `_gold.jsonl` output preserving silver stage

#### CLI Interface
- `docmeld process` - Full pipeline (bronze → silver → gold)
- `docmeld bronze` - PDF to JSON only
- `docmeld silver` - JSON to JSONL only
- `docmeld gold` - JSONL enrichment only
- Support for single files and folders

#### Python API
- `DocMeldParser` main class
- `process_all()` - Full pipeline
- `process_bronze()` - Bronze stage only
- `process_silver()` - Silver stage only
- `process_gold()` - Gold stage only

#### Infrastructure
- Timestamped logging (`docmeld_YYYYMMDD_HHMMSS.log`)
- Environment variable support via `.env.local`
- Progress indicators for batch processing
- Cross-platform support (macOS, Linux, Windows)

#### Testing
- 109 tests with 82% code coverage
- Unit tests for all core modules
- Integration tests for full pipeline
- Contract tests for JSON schema validation
- Test fixtures (sample PDFs)

#### Documentation
- README with quickstart guide
- API documentation in docstrings
- Example usage patterns
- MIT license

### Technical Details

- **Dependencies**: PyMuPDF, pymupdf4llm, pandas, openpyxl, pydantic, python-dotenv, langchain-deepseek
- **Python**: 3.9+ required
- **Architecture**: Three-stage pipeline (Bronze → Silver → Gold)
- **Design**: Library-first with CLI wrapper
- **Quality**: Ruff linting, Black formatting, Mypy type checking

[Unreleased]: https://github.com/[username]/docmeld/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/[username]/docmeld/releases/tag/v0.1.0
