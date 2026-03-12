# Tasks: Research Papers Batch Categorize

**Input**: Design documents from `/specs/002-paper-batch-categorize/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: TDD is NON-NEGOTIABLE per constitution Principle I. All test tasks are included and MUST be written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `docmeld/`, `tests/` at repository root (`/Users/frank/A/DocMeld/docmeld/`)
- Python venv: always `source venv/bin/activate` before running commands

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the categorize module structure and shared models

- [x] T001 Create categorize module directory and `__init__.py` at `docmeld/docmeld/categorize/__init__.py`
- [x] T002 Add Pydantic models for PaperMetadata, Category, PaperEntry, CategoryIndex in `docmeld/docmeld/categorize/models.py` per data-model.md
- [x] T003 [P] Add CategorizeResult model to `docmeld/docmeld/silver/page_models.py` with fields: index_path, total_papers, total_categories, papers_failed, reorganized

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Aggregator and DeepSeek categorization client — these are needed by all user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Write unit tests for aggregator in `docmeld/tests/unit/test_aggregator.py`: test scanning gold JSONL files, collecting metadata, handling missing/empty files, deduplicating keywords
- [x] T005 [P] Write unit tests for categorizer in `docmeld/tests/unit/test_categorizer.py`: test prompt construction, response parsing, deterministic sorting, error handling for malformed API responses
- [x] T006 Implement aggregator in `docmeld/docmeld/categorize/aggregator.py`: scan a folder for `*_gold.jsonl` files, parse each file to collect per-paper description + keywords, return list of PaperMetadata
- [x] T007 Implement categorizer in `docmeld/docmeld/categorize/categorizer.py`: accept list of PaperMetadata, sort by filename, build JSON prompt, call DeepSeek with temperature=0, parse response into list of Category assignments
- [x] T008 Add `categorize_papers()` method to `docmeld/docmeld/gold/deepseek_client.py`: accepts aggregated paper metadata JSON string, returns category assignments JSON, uses temperature=0 for determinism

**Checkpoint**: Aggregator can collect metadata, categorizer can cluster papers via API

---

## Phase 3: User Story 1 - Batch Process Research Papers (Priority: P1) 🎯 MVP

**Goal**: Process all PDFs in a folder through full Bronze→Silver→Gold pipeline in a single command

**Independent Test**: Point command at folder of 3+ sample PDFs, verify bronze JSON + silver JSONL + gold JSONL created for each

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Integration test for batch full-pipeline in `docmeld/tests/integration/test_categorize_pipeline.py`: test that `process_categorize()` on a folder of 3 sample PDFs produces bronze+silver+gold outputs for each
- [x] T010 [P] [US1] Integration test for idempotency in `docmeld/tests/integration/test_categorize_pipeline.py`: test that running twice skips already-processed PDFs
- [x] T011 [P] [US1] Integration test for error resilience in `docmeld/tests/integration/test_categorize_pipeline.py`: test that one corrupted PDF doesn't block processing of others

### Implementation for User Story 1

- [x] T012 [US1] Add `process_categorize(reorganize=False)` method to `docmeld/docmeld/parser.py`: orchestrates full pipeline (process_all + aggregate + categorize + write index), returns CategorizeResult
- [x] T013 [US1] Add `categorize` subcommand to `docmeld/docmeld/cli.py`: accepts folder path, `--reorganize` flag, `--backend` flag, calls `DocMeldParser.process_categorize()`
- [x] T014 [US1] Update `docmeld/docmeld/__init__.py` to export categorize module

**Checkpoint**: `docmeld categorize /path/to/papers/` processes all PDFs through bronze→silver→gold

---

## Phase 4: User Story 2 - Topic Categorization and Index Generation (Priority: P2)

**Goal**: Aggregate gold metadata across papers, identify topic clusters, produce `categories.json`

**Independent Test**: Provide pre-existing gold JSONL files, verify `categories.json` is produced with sensible groupings

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T015 [P] [US2] Unit test for index_writer in `docmeld/tests/unit/test_index_writer.py`: test writing valid categories.json, test schema compliance, test deterministic output
- [x] T016 [P] [US2] Contract test for categories.json schema in `docmeld/tests/contract/test_categories_schema.py`: validate output against `specs/002-paper-batch-categorize/contracts/categories-schema.json`
- [x] T017 [P] [US2] Integration test for categorization in `docmeld/tests/integration/test_categorize_pipeline.py`: test that categories.json is created after gold processing, test determinism (same input → same output)

### Implementation for User Story 2

- [x] T018 [US2] Implement index_writer in `docmeld/docmeld/categorize/index_writer.py`: accept list of PaperMetadata + category assignments, build CategoryIndex, write `categories.json` to folder root
- [x] T019 [US2] Wire categorization into `process_categorize()` in `docmeld/docmeld/parser.py`: after process_all completes, call aggregator → categorizer → index_writer
- [x] T020 [US2] Add progress logging for categorization step in `docmeld/docmeld/categorize/categorizer.py`

**Checkpoint**: `docmeld categorize /path/` produces `categories.json` with topic clusters

---

## Phase 5: User Story 3 - File Reorganization by Category (Priority: P3)

**Goal**: Optionally move PDFs and output folders into category-named subdirectories

**Independent Test**: Run reorganize on folder with existing `categories.json`, verify files moved correctly

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US3] Unit test for reorganizer in `docmeld/tests/unit/test_reorganizer.py`: test file moving, test category name sanitization, test idempotency (already reorganized), test special characters in category names
- [x] T022 [P] [US3] Integration test for reorganize in `docmeld/tests/integration/test_categorize_pipeline.py`: test end-to-end with `--reorganize` flag

### Implementation for User Story 3

- [x] T023 [US3] Implement reorganizer in `docmeld/docmeld/categorize/reorganizer.py`: read categories.json, sanitize category names, create subdirectories, move PDFs + output folders, write `_reorganized.json` manifest
- [x] T024 [US3] Wire reorganize into `process_categorize(reorganize=True)` in `docmeld/docmeld/parser.py`
- [x] T025 [US3] Add `--reorganize` flag handling in `docmeld/docmeld/cli.py` categorize subcommand

**Checkpoint**: `docmeld categorize /path/ --reorganize` moves files into category subdirectories

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, documentation, final validation

- [x] T026 [P] Handle edge case: zero PDFs in folder — report "no PDFs found" and exit gracefully in `docmeld/docmeld/parser.py`
- [x] T027 [P] Handle edge case: folder path does not exist — clear error message in `docmeld/docmeld/cli.py`
- [x] T028 Update CHANGELOG.md with 002-paper-batch-categorize entries in `docmeld/CHANGELOG.md`
- [x] T029 Run full test suite: `pytest tests/ -v --cov=docmeld` — all tests must pass, coverage must not regress
- [ ] T030 Run linting: `ruff check docmeld/` and `black --check docmeld/` — zero errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (models must exist for aggregator/categorizer)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (needs aggregator + categorizer)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs full pipeline to produce gold files)
- **User Story 3 (Phase 5)**: Depends on Phase 4 (needs categories.json to reorganize)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational — batch pipeline orchestration
- **US2 (P2)**: Depends on US1 — needs gold outputs to aggregate and categorize
- **US3 (P3)**: Depends on US2 — needs categories.json to reorganize files

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before CLI integration
- Core implementation before edge cases

### Parallel Opportunities

- T004, T005 can run in parallel (different test files)
- T009, T010, T011 can run in parallel (same file but independent test classes)
- T015, T016, T017 can run in parallel (different test files)
- T021, T022 can run in parallel (different test files)
- T026, T027 can run in parallel (different files, independent edge cases)

---

## Parallel Example: Phase 2

```bash
# Launch foundational tests in parallel:
Task: "Unit test for aggregator in tests/unit/test_aggregator.py"
Task: "Unit test for categorizer in tests/unit/test_categorizer.py"

# Then implement sequentially:
Task: "Implement aggregator in docmeld/categorize/aggregator.py"
Task: "Implement categorizer in docmeld/categorize/categorizer.py"
Task: "Add categorize_papers() to gold/deepseek_client.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (models + module structure)
2. Complete Phase 2: Foundational (aggregator + categorizer)
3. Complete Phase 3: User Story 1 (batch pipeline + CLI)
4. **STOP and VALIDATE**: Test batch processing independently
5. Proceed to US2 for categorization

### Incremental Delivery

1. Setup + Foundational → Core infrastructure ready
2. Add US1 → Batch processing works → Validate
3. Add US2 → categories.json generated → Validate
4. Add US3 → File reorganization works → Validate
5. Polish → Edge cases, docs, final test run

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1→US2→US3 is sequential (each builds on the previous)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
