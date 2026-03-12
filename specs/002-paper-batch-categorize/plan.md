# Implementation Plan: Research Papers Batch Categorize

**Branch**: `002-paper-batch-categorize` | **Date**: 2026-03-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-paper-batch-categorize/spec.md`

## Summary

Add a `categorize` command that batch-processes a folder of PDFs through the full Bronze→Silver→Gold pipeline, then aggregates gold-stage metadata (keywords + descriptions) across all papers, sends them to DeepSeek-chat for topic clustering, and produces a `categories.json` index. An optional `--reorganize` flag physically moves files into category subdirectories.

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**: PyMuPDF (fitz), pymupdf4llm, pydantic, langchain-deepseek (all existing)
**Storage**: Filesystem (JSON files) — no database
**Testing**: pytest with pytest-cov; TDD per constitution
**Target Platform**: macOS, Linux, Windows (cross-platform)
**Project Type**: Single Python package (`docmeld/`)
**Performance Goals**: Process 20+ PDFs in a single invocation; categorization step completes in under 30 seconds for 50 papers
**Constraints**: Gold stage requires DeepSeek API key; categorization must be deterministic for same input
**Scale/Scope**: Folders of 5–100 PDFs typical; categories.json under 1MB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | All new modules get tests before implementation |
| II. Library-First, PyPI-Ready | PASS | New `categorize()` method on DocMeldParser; CLI wraps it |
| III. Lightweight by Default | PASS | No new dependencies; reuses existing DeepSeek client |
| IV. Unified Element Format | PASS | Bronze/silver/gold formats unchanged; categories.json is a new output alongside |
| V. Agent-Ready Outputs | PASS | categories.json is machine-readable, designed for agent consumption |
| VI. Production-Grade Quality | PASS | Ruff, black, mypy, 90%+ coverage gates apply |
| VII. Open-Source Excellence | NOTE | Constitution says MIT; project is now AGPL-3.0 — documented deviation |

## Project Structure

### Documentation (this feature)

```text
specs/002-paper-batch-categorize/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── categories-schema.json
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
docmeld/
├── docmeld/
│   ├── bronze/          # Existing — no changes needed
│   ├── silver/          # Existing — no changes needed
│   ├── gold/
│   │   ├── processor.py          # Existing — no changes
│   │   ├── deepseek_client.py    # Existing — add categorize_papers() method
│   │   └── metadata_extractor.py # Existing — no changes
│   ├── categorize/               # NEW module
│   │   ├── __init__.py
│   │   ├── aggregator.py         # Collect gold metadata across papers
│   │   ├── categorizer.py        # Send aggregated data to DeepSeek for clustering
│   │   ├── index_writer.py       # Write categories.json
│   │   └── reorganizer.py        # Move files into category subdirectories
│   ├── parser.py                 # Add process_categorize() method
│   └── cli.py                    # Add 'categorize' subcommand
├── tests/
│   ├── unit/
│   │   ├── test_aggregator.py        # NEW
│   │   ├── test_categorizer.py       # NEW
│   │   ├── test_index_writer.py      # NEW
│   │   └── test_reorganizer.py       # NEW
│   ├── integration/
│   │   ├── test_categorize_pipeline.py  # NEW
│   │   └── test_cli.py                 # Update with categorize tests
│   └── contract/
│       └── test_categories_schema.py    # NEW
```

**Structure Decision**: New `categorize/` module under `docmeld/` following the existing pattern (bronze/, silver/, gold/ are each a module). This keeps categorization logic isolated and testable independently.

## Architecture

### Data Flow

```
Folder of PDFs
    │
    ▼
[1] process_all() — existing Bronze→Silver→Gold per PDF
    │
    ▼
[2] aggregator.py — scan all *_gold.jsonl files, collect {filename, description, keywords}
    │
    ▼
[3] categorizer.py — send aggregated metadata to DeepSeek, get back category assignments
    │
    ▼
[4] index_writer.py — write categories.json to folder root
    │
    ▼ (optional)
[5] reorganizer.py — move PDFs + output folders into category subdirectories
```

### Key Design Decisions

1. **Categorization is a post-gold step**, not embedded in the gold processor. This keeps the existing pipeline untouched and makes categorization independently testable.

2. **Single DeepSeek call for categorization**. Rather than calling the API per-paper, we aggregate all paper metadata into one prompt and ask DeepSeek to cluster them. This is cheaper, faster, and produces more coherent categories.

3. **Determinism via temperature=0**. The categorization call uses `temperature=0` to ensure deterministic output for the same input.

4. **categories.json lives in the input folder root**, not inside any paper's output directory. It's a folder-level artifact.

5. **Reorganization is destructive and opt-in**. The `--reorganize` flag moves files. Without it, only `categories.json` is written. Reorganization is idempotent — if files are already in category folders, it's a no-op.

## Complexity Tracking

No constitution violations requiring justification.
