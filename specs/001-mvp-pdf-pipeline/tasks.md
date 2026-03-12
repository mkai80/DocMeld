# Tasks: MVP PDF Data Pipeline

**Input**: Design documents from `/specs/001-mvp-pdf-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: TDD is NON-NEGOTIABLE per constitution Principle I. All test tasks are included and MUST be written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `docmeld/`, `tests/` at repository root
- Python venv: always `source venv/bin/activate` before running commands

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, packaging, and dev tooling

- [ ] T001 Create project directory structure per plan.md: `docmeld/docmeld/`, `docmeld/tests/`, `docmeld/examples/`, `docmeld/docs/`
- [ ] T002 Initialize Python project with `pyproject.toml` (PEP 621): name=docmeld, version=0.1.0, python>=3.9, dependencies=[PyMuPDF, pymupdf4llm, pandas, openpyxl, pydantic, python-dotenv, langchain-deepseek], dev-dependencies=[pytest, pytest-cov, ruff, black, mypy]
- [ ] T003 Create virtual environment and install: `python3 -m venv venv && source venv/bin/activate && pip install -e ".[dev]"`
- [ ] T004 [P] Configure ruff, black (line-length=100), and mypy (strict mode) in `pyproject.toml`
- [ ] T005 [P] Create `.gitignore` with Python defaults, venv/, .env.local, *.pyc, __pycache__/, dist/, *.egg-info/
- [ ] T006 [P] Create `.env.local.example` with `DEEPSEEK_API_KEY=your_key_here` and `DEEPSEEK_API_ENDPOINT=https://api.deepseek.com` placeholders
- [ ] T007 [P] Create `LICENSE` file with MIT license text
- [ ] T008 Create `docmeld/docmeld/__init__.py` with public API exports: `from docmeld.parser import DocMeldParser` and `__version__ = "0.1.0"`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] Write unit tests for Pydantic element models (TitleElement, TextElement, TableElement, ImageElement) in `tests/unit/test_element_types.py`: test field validation, type discriminator, page_no >= 1, title level 0-5, content non-empty
- [ ] T010 [P] Write unit tests for logging utility in `tests/unit/test_logging.py`: test timestamped filename format `docmeld_YYYYMMDD_HHMMSS.log`, test log file creation in cwd, test log levels (ERROR, WARNING, INFO, DEBUG)
- [ ] T011 [P] Write unit tests for env loader in `tests/unit/test_env_loader.py`: test loading DEEPSEEK_API_KEY from .env.local, test missing key raises error, test optional DEEPSEEK_API_ENDPOINT
- [ ] T012 [P] Write unit tests for progress utility in `tests/unit/test_progress.py`: test progress message format "Processing 3/10 files...", test stage progress "Bronze stage: 5/10 pages"
- [ ] T013 [P] Write contract test for element JSON Schema validation in `tests/contract/test_element_schema.py`: validate sample bronze JSON against `specs/001-mvp-pdf-pipeline/contracts/element-schema.json`

### Implementation for Foundational

- [ ] T014 [P] Implement Pydantic element models in `docmeld/docmeld/bronze/element_types.py`: BronzeElement base, TitleElement, TextElement, TableElement, ImageElement per data-model.md
- [ ] T015 [P] Implement SilverPage and GoldPage Pydantic models in `docmeld/docmeld/silver/page_models.py`: SilverMetadata, SilverPage, GoldMetadata, GoldPage, ProcessingResult per data-model.md
- [ ] T016 [P] Implement timestamped logging utility in `docmeld/docmeld/utils/logging.py`: setup_logging() returns logger, creates `docmeld_YYYYMMDD_HHMMSS.log` in cwd, configures file + console handlers
- [ ] T017 [P] Implement env loader in `docmeld/docmeld/utils/env_loader.py`: load_env() loads `.env.local` from repo root using python-dotenv, validates DEEPSEEK_API_KEY presence
- [ ] T018 [P] Implement progress indicator utility in `docmeld/docmeld/utils/progress.py`: ProgressTracker class with update(current, total, message) method, prints to stderr
- [ ] T019 Create `tests/conftest.py` with shared pytest fixtures: tmp_dir, sample PDF paths, mock .env.local
- [ ] T020 [P] Create test fixture `tests/fixtures/sample_simple.pdf`: programmatically generate a 3-page PDF with text, one title, and one table using PyMuPDF
- [ ] T021 [P] Create test fixture `tests/fixtures/sample_complex.pdf`: programmatically generate a 5-page PDF with multi-level titles, multiple tables, images, and mixed content
- [ ] T022 Run `pytest tests/unit/test_element_types.py tests/unit/test_logging.py tests/unit/test_env_loader.py tests/unit/test_progress.py tests/contract/test_element_schema.py` — all tests MUST pass

**Checkpoint**: Foundation ready — element models validated, logging/env/progress utilities working, test fixtures created. User story implementation can now begin.

---

## Phase 3: User Story 1 — Process Single PDF to Bronze Format (Priority: P1) 🎯 MVP

**Goal**: Convert a single PDF file into a structured JSON element list with sanitized filename and MD5 hash suffix.

**Independent Test**: Provide a PDF file path → run bronze processor → verify sanitized filename with hash, output folder created, JSON file with all elements in reading order with correct page_no.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US1] Write unit tests for filename sanitizer in `tests/unit/test_filename_sanitizer.py`: test dangerous char replacement (`/\:*?"<>|` → `_`), test unicode normalization, test truncation at 200 chars, test MD5 hash calculation (last 6 digits), test full sanitized name format `{stem}_{hash6}`, test collision resistance (different files same name)
- [ ] T024 [P] [US1] Write unit tests for element extractor in `tests/unit/test_element_extractor.py`: test title detection from `#` lines (level counting), test table detection from `|` lines (buffer flush), test text extraction (non-title non-table), test image file discovery and base64 encoding, test element ordering preservation, test empty page handling, test table summary generation (first column items)
- [ ] T025 [P] [US1] Write integration test for bronze pipeline in `tests/integration/test_bronze_pipeline.py`: test single PDF end-to-end with sample_simple.pdf (verify folder creation, JSON output, element types), test with sample_complex.pdf (verify tables, titles, images), test idempotency (re-run skips existing), test malformed PDF handling (graceful error), test special character filename sanitization

### Implementation for User Story 1

- [ ] T026 [US1] Implement filename sanitizer in `docmeld/docmeld/bronze/filename_sanitizer.py`: sanitize_filename(path) → replaces dangerous chars with `_`, normalizes unicode NFC, lowercases, truncates to 200 chars; calculate_hash(path) → MD5 of file bytes, returns last 6 hex digits; get_output_name(path) → returns `{sanitized_stem}_{hash6}`
- [ ] T027 [US1] Implement element extractor in `docmeld/docmeld/bronze/element_extractor.py`: extract_elements(pdf_path, output_dir) → opens PDF with fitz, iterates pages, calls pymupdf4llm.to_markdown() per page, parses markdown line-by-line (# → title, | → table buffer, else → text buffer, empty → flush), discovers images via glob `page{N:03d}_*.png`, base64 encodes, returns List[dict] in reading order. Include table summary generation: parse first column values, format as "Items: x, y, z (+N more)"
- [ ] T028 [US1] Implement bronze processor orchestrator in `docmeld/docmeld/bronze/processor.py`: BronzeProcessor class with process_file(pdf_path) → sanitizes filename, calculates hash, creates output folder, checks idempotency (skip if JSON exists), calls element_extractor, saves JSON to `{output_dir}/{name_hash6}.json`, returns BronzeResult with output_path and element count
- [ ] T029 [US1] Create `docmeld/docmeld/bronze/__init__.py` with exports: BronzeProcessor, sanitize_filename, extract_elements
- [ ] T030 [US1] Run `pytest tests/unit/test_filename_sanitizer.py tests/unit/test_element_extractor.py tests/integration/test_bronze_pipeline.py -v` — all tests MUST pass

**Checkpoint**: Single PDF → Bronze JSON works end-to-end. Can process any digital-native PDF into structured element JSON.

---

## Phase 4: User Story 2 — Process Folder of PDFs to Bronze Format (Priority: P1)

**Goal**: Batch process an entire folder of PDFs with progress indicators, error resilience (fail-fast disabled), and summary report.

**Independent Test**: Provide a folder with multiple PDFs (including non-PDF files) → run batch processor → verify all PDFs processed, non-PDFs skipped, already-processed skipped, summary report generated.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T031 [P] [US2] Write integration test for batch bronze processing in `tests/integration/test_bronze_batch.py`: test folder with 3 PDFs (all processed), test mixed file types (only PDFs processed, others skipped with warning), test partial re-run (skip already-processed), test one corrupted PDF (continues processing others, reports failure), test empty folder (no error, zero results), test progress indicator output, test summary report content (total, successful, failed, time)

### Implementation for User Story 2

- [ ] T032 [US2] Implement batch processor in `docmeld/docmeld/bronze/processor.py`: add process_folder(folder_path) method to BronzeProcessor — discovers all .pdf files in folder, iterates with progress tracking, calls process_file() for each, catches exceptions per file (fail-fast disabled per FR-034), collects results, returns ProcessingResult with total/successful/failed/failures list/processing_time
- [ ] T033 [US2] Implement summary report generation in `docmeld/docmeld/utils/report.py`: generate_summary(result: ProcessingResult) → formats and prints summary to console and log: total files, successful, failed (with filenames and errors), processing time
- [ ] T034 [US2] Update `docmeld/docmeld/parser.py`: create DocMeldParser class with `__init__(self, path: str)` that detects file vs folder, `process_bronze()` that delegates to BronzeProcessor.process_file() or process_folder()
- [ ] T035 [US2] Run `pytest tests/integration/test_bronze_batch.py -v` — all tests MUST pass

**Checkpoint**: Batch bronze processing works. Can process folders of PDFs with error resilience and summary reports.

---

## Phase 5: User Story 3 — Convert Bronze JSON to Silver JSONL (Priority: P2)

**Goal**: Transform bronze element JSON into page-by-page JSONL with title hierarchy tracking, global table numbering, and markdown rendering.

**Independent Test**: Provide a bronze JSON file → run silver processor → verify JSONL with one line per page, each page has metadata (uuid, source, page_no, session_title) and page_content with full title hierarchy and table markers.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T036 [P] [US3] Write unit tests for title tracker in `tests/unit/test_title_tracker.py`: test stack push/pop on level transitions (H1→H2→H1 pops H2), test get_hierarchy_markdown() renders full stack as `# Title\n## Subtitle`, test empty stack returns empty string, test same-level replacement, test deep nesting (H1→H2→H3→H4)
- [ ] T037 [P] [US3] Write unit tests for markdown renderer in `tests/unit/test_markdown_renderer.py`: test title rendering with correct `#` count (level 0 → `#`, level 1 → `##`), test text rendering preserves content, test table rendering with `[[Table1]]` and `[/Table1]` markers, test global table numbering across pages, test small table handling (≤1 data row → `[[Table]]` without number), test image rendering
- [ ] T038 [P] [US3] Write unit tests for page aggregator in `tests/unit/test_page_aggregator.py`: test grouping elements by page_no, test elements sorted within page, test empty page handling, test single-page document, test multi-page document
- [ ] T039 [P] [US3] Write integration test for silver pipeline in `tests/integration/test_silver_pipeline.py`: test bronze JSON → silver JSONL conversion with sample data, test one line per page, test title hierarchy across pages (page 2 starts with titles from page 1), test global table numbering, test JSONL metadata fields (uuid, source, page_no, session_title), test idempotency (skip if JSONL exists), test page_content markdown format

### Implementation for User Story 3

- [ ] T040 [US3] Implement title tracker in `docmeld/docmeld/silver/title_tracker.py`: TitleTracker class with stack list, update(level, content) pops stack to parent level then pushes, get_hierarchy_markdown() renders stack as markdown headers, get_session_title() returns compact title string
- [ ] T041 [US3] Implement markdown renderer in `docmeld/docmeld/silver/markdown_renderer.py`: render_page(elements, title_tracker, table_counter) → iterates elements, renders titles as `# heading`, text as-is, tables with `[[TableN]]`/`[/TableN]` markers (global numbering, skip small tables), images as markdown image syntax. Returns (page_content_str, updated_table_counter)
- [ ] T042 [US3] Implement page aggregator in `docmeld/docmeld/silver/page_aggregator.py`: group_by_page(elements) → returns dict[int, List[dict]] grouping elements by page_no, preserving order within each page
- [ ] T043 [US3] Implement silver processor in `docmeld/docmeld/silver/processor.py`: SilverProcessor class with process(bronze_json_path) → loads bronze JSON, groups by page, initializes TitleTracker and table_counter=0, for each page: generates UUID, builds metadata (uuid, source, page_no as "pageN", session_title from tracker), renders page_content via markdown_renderer, writes JSONL line. Checks idempotency (skip if .jsonl exists). Returns SilverResult with output_path and page_count
- [ ] T044 [US3] Create `docmeld/docmeld/silver/__init__.py` with exports: SilverProcessor, TitleTracker
- [ ] T045 [US3] Update `docmeld/docmeld/parser.py`: add process_silver(bronze_json_path) method to DocMeldParser that delegates to SilverProcessor
- [ ] T046 [US3] Run `pytest tests/unit/test_title_tracker.py tests/unit/test_markdown_renderer.py tests/unit/test_page_aggregator.py tests/integration/test_silver_pipeline.py -v` — all tests MUST pass

**Checkpoint**: Bronze JSON → Silver JSONL works. Each page is self-contained with title hierarchy and global table numbering.

---

## Phase 6: User Story 4 — Enrich Silver JSONL with Gold Metadata (Priority: P3)

**Goal**: Use DeepSeek-chat API to analyze each page and extract description + keywords, writing enriched output to `_gold.jsonl` file.

**Independent Test**: Provide a silver JSONL file → run gold processor → verify `_gold.jsonl` created with `description` and `keywords` fields in each page's metadata.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T047 [P] [US4] Write unit tests for DeepSeek client in `tests/unit/test_deepseek_client.py`: test API call with mocked response (returns description + keywords), test retry logic with exponential backoff (1s, 2s, 4s), test max retries exceeded raises exception, test rate limiting delay (0.5s between calls), test missing API key raises ValueError, test structured output parsing (Pydantic PageMetadata model)
- [ ] T048 [P] [US4] Write unit tests for metadata extractor in `tests/unit/test_metadata_extractor.py`: test extract_metadata(page_content) returns description and keywords, test empty page_content returns "Blank page" description, test gold_processing_failed flag on API failure
- [ ] T049 [P] [US4] Write integration test for gold pipeline in `tests/integration/test_gold_pipeline.py`: test silver JSONL → gold JSONL conversion (mock DeepSeek API), test `_gold` suffix in output filename, test original silver JSONL preserved, test each page has description and keywords in metadata, test idempotency (skip if gold JSONL exists with description/keywords), test partial failure (one page fails, others succeed, failed page marked with gold_processing_failed=true), test API retry on transient error

### Implementation for User Story 4

- [ ] T050 [US4] Implement DeepSeek client in `docmeld/docmeld/gold/deepseek_client.py`: DeepSeekClient class with `__init__(api_key, endpoint=None, temperature=1.0)`, loads from env via env_loader, creates ChatDeepSeek with structured output (PageMetadata Pydantic model: description str, keywords List[str]). Implement call_with_retry(func, max_retries=3) with exponential backoff (2^attempt seconds). Add 0.5s delay between calls for rate limiting
- [ ] T051 [US4] Implement metadata extractor in `docmeld/docmeld/gold/metadata_extractor.py`: MetadataExtractor class with extract(page_content) → calls DeepSeek client with prompt to analyze page and extract description + keywords, handles empty content ("Blank page"), catches API failures and returns gold_processing_failed=true
- [ ] T052 [US4] Implement gold processor in `docmeld/docmeld/gold/processor.py`: GoldProcessor class with process(silver_jsonl_path) → reads silver JSONL line by line, checks idempotency (skip if `_gold.jsonl` exists with description/keywords), for each page: calls metadata_extractor, merges description+keywords into metadata, writes to `{basename}_gold.jsonl`. Continues on per-page failure (FR-028). Returns GoldResult with output_path, pages_enriched, pages_failed
- [ ] T053 [US4] Create `docmeld/docmeld/gold/__init__.py` with exports: GoldProcessor, DeepSeekClient
- [ ] T054 [US4] Update `docmeld/docmeld/parser.py`: add process_gold(silver_jsonl_path) method and process_all() method that chains bronze → silver → gold, returns ProcessingResult
- [ ] T055 [US4] Run `pytest tests/unit/test_deepseek_client.py tests/unit/test_metadata_extractor.py tests/integration/test_gold_pipeline.py -v` — all tests MUST pass

**Checkpoint**: Full pipeline works: PDF → Bronze JSON → Silver JSONL → Gold JSONL with AI-generated descriptions and keywords.

---

## Phase 7: CLI & End-to-End Integration

**Purpose**: CLI interface and full pipeline integration testing

### Tests

- [ ] T056 [P] Write integration test for CLI in `tests/integration/test_cli.py`: test `docmeld process <file>` runs all stages, test `docmeld bronze <file>` runs bronze only, test `docmeld silver <json>` runs silver only, test `docmeld gold <jsonl>` runs gold only, test `docmeld process <folder>` batch mode, test `--help` output, test invalid path error message
- [ ] T057 [P] Write end-to-end integration test in `tests/integration/test_end_to_end.py`: test full pipeline PDF → bronze → silver → gold with sample_simple.pdf, test batch pipeline with folder of PDFs, test summary report generation, test log file creation, test idempotency across all stages

### Implementation

- [ ] T058 Implement CLI interface in `docmeld/docmeld/cli.py`: argparse-based CLI with subcommands: `process` (all stages), `bronze`, `silver`, `gold`. Accept positional path argument. Add `--output-dir` optional flag. Wire to DocMeldParser methods. Entry point: `docmeld = docmeld.cli:main` in pyproject.toml
- [ ] T059 Update `docmeld/docmeld/parser.py`: ensure process_all() chains all three stages, handles batch mode (folder input), generates summary report via utils/report.py, creates timestamped log file
- [ ] T060 Run `pytest tests/integration/test_cli.py tests/integration/test_end_to_end.py -v` — all tests MUST pass
- [ ] T061 Run full test suite: `pytest --cov=docmeld --cov-report=term-missing` — verify 90%+ coverage

**Checkpoint**: CLI works, full pipeline tested end-to-end, coverage target met.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI/CD, and release preparation

- [ ] T062 [P] Create `README.md` with: project overview, installation (`pip install docmeld`), 5-line quickstart, feature list, output format examples, roadmap, badges placeholders, MIT license badge
- [ ] T063 [P] Create `CONTRIBUTING.md` with: development setup (venv, install dev deps), TDD workflow, code style (ruff, black, mypy), PR process, issue templates
- [ ] T064 [P] Create `CHANGELOG.md` with initial v0.1.0 entry following Keep a Changelog format
- [ ] T065 [P] Create GitHub Actions workflow `docmeld/.github/workflows/test.yml`: run pytest on push/PR, matrix Python 3.9/3.10/3.11/3.12, macOS + Linux + Windows
- [ ] T066 [P] Create GitHub Actions workflow `docmeld/.github/workflows/lint.yml`: run ruff check, black --check, mypy on push/PR
- [ ] T067 [P] Create GitHub Actions workflow `docmeld/.github/workflows/publish.yml`: build wheel, publish to PyPI on tag push (v*)
- [ ] T068 Run `ruff check docmeld/ && black --check docmeld/ && mypy docmeld/` — all MUST pass with zero errors
- [ ] T069 Run quickstart.md validation: execute the 5-line example from quickstart.md against sample_simple.pdf, verify output matches expected structure
- [ ] T070 Final review: verify all JSON outputs match `specs/001-mvp-pdf-pipeline/contracts/element-schema.json`, verify silver/gold JSONL structure matches examples in `references/00-core/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — No dependencies on other stories
- **US2 (Phase 4)**: Depends on US1 (extends BronzeProcessor with batch mode)
- **US3 (Phase 5)**: Depends on Foundational — Can run in parallel with US1/US2 (different files)
- **US4 (Phase 6)**: Depends on Foundational — Can run in parallel with US1/US2/US3 (different files)
- **CLI (Phase 7)**: Depends on US1, US2, US3, US4 (integrates all stages)
- **Polish (Phase 8)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Foundational → US1 (no other story dependencies)
- **US2 (P1)**: US1 → US2 (extends BronzeProcessor)
- **US3 (P2)**: Foundational → US3 (independent of US1/US2, uses bronze JSON as input)
- **US4 (P3)**: Foundational → US4 (independent of US1/US2/US3, uses silver JSONL as input)

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Models/utilities before processors
3. Processor before integration
4. All tests MUST pass at checkpoint

### Parallel Opportunities

- **Phase 1**: T004, T005, T006, T007 can all run in parallel
- **Phase 2**: T009-T013 (tests) can all run in parallel; T014-T018 (implementation) can all run in parallel; T020-T021 (fixtures) can run in parallel
- **Phase 3-6**: US3 and US4 can run in parallel with US1/US2 (different subpackages, different files)
- **Phase 8**: T062-T067 can all run in parallel

---

## Parallel Example: User Story 3

```bash
# Launch all tests for US3 together (different files):
Task: "Write unit tests for title tracker in tests/unit/test_title_tracker.py"
Task: "Write unit tests for markdown renderer in tests/unit/test_markdown_renderer.py"
Task: "Write unit tests for page aggregator in tests/unit/test_page_aggregator.py"
Task: "Write integration test for silver pipeline in tests/integration/test_silver_pipeline.py"

# After tests written, launch parallel implementations:
Task: "Implement title tracker in docmeld/docmeld/silver/title_tracker.py"
Task: "Implement markdown renderer in docmeld/docmeld/silver/markdown_renderer.py"
Task: "Implement page aggregator in docmeld/docmeld/silver/page_aggregator.py"

# Then sequential: processor depends on all three above
Task: "Implement silver processor in docmeld/docmeld/silver/processor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (single PDF → bronze JSON)
4. **STOP and VALIDATE**: Test with real PDFs, verify element extraction quality
5. Demo: `from docmeld import DocMeldParser; DocMeldParser("doc.pdf").process_bronze()`

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Single PDF bronze processing → **MVP v0.1.0-alpha**
3. US2 → Batch bronze processing → **MVP v0.1.0-beta**
4. US3 → Silver JSONL (page-by-page) → **MVP v0.1.0-rc1**
5. US4 → Gold enrichment (AI metadata) → **MVP v0.1.0**
6. CLI + Polish → **Release v0.1.0 to PyPI**

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 → US2 (bronze pipeline, sequential dependency)
   - Developer B: US3 (silver pipeline, independent)
   - Developer C: US4 (gold pipeline, independent)
3. All converge for Phase 7 (CLI integration) and Phase 8 (polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD is NON-NEGOTIABLE: write tests first, verify they fail, then implement
- Always use venv: `source venv/bin/activate`
- DeepSeek temperature = 1.0 for all data pipeline API calls
- .env.local at repo root for API keys
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
