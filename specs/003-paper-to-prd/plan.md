# Implementation Plan: Research Paper to PRD

**Branch**: `003-paper-to-prd` | **Date**: 2026-03-12 | **Spec**: [spec.md](spec.md)

## Summary

Add a `prd` command that processes a single PDF through Bronze→Silver, then sends the aggregated page content to DeepSeek-chat to generate a structured PRD with six sections. Output as `_prd.md` in the paper's output directory.

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**: Existing — no new deps
**Testing**: pytest, TDD per constitution
**Architecture**: New `prd/` module under `docmeld/`, following categorize/ pattern

## Source Code

```text
docmeld/docmeld/
├── prd/
│   ├── __init__.py
│   ├── generator.py      # PRD generation logic + prompt
│   └── models.py         # PrdResult model
├── parser.py             # Add process_prd()
└── cli.py                # Add 'prd' subcommand
tests/
├── unit/test_prd_generator.py
└── contract/test_prd_output.py
```
