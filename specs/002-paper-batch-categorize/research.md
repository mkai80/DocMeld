# Research: Research Papers Batch Categorize

**Feature**: 002-paper-batch-categorize
**Date**: 2026-03-12

## Decision 1: Categorization Approach

**Decision**: Use a single DeepSeek-chat API call with all paper metadata aggregated into one prompt, asking the model to return category assignments as structured JSON.

**Rationale**:
- Calling the API once with all papers gives the model full context to identify natural topic clusters across the collection.
- Per-paper categorization would require a predefined taxonomy or a second pass to reconcile categories.
- A single call is cheaper (one API round-trip vs N) and produces more coherent groupings.

**Alternatives considered**:
- Local clustering (TF-IDF + k-means on keywords): Rejected — adds scipy/sklearn dependency, violates Principle III (Lightweight by Default), and keyword-only clustering is less accurate than LLM-based semantic grouping.
- Per-paper API call with predefined categories: Rejected — requires the user to define categories upfront, which contradicts the spec requirement for automatic category discovery.
- Two-pass approach (first call discovers categories, second assigns): Rejected — unnecessary complexity; a single well-structured prompt handles both discovery and assignment.

## Decision 2: Determinism Strategy

**Decision**: Use `temperature=0` for the categorization API call and sort paper metadata alphabetically by filename before sending to the model.

**Rationale**:
- `temperature=0` makes the model's output deterministic for identical input.
- Sorting by filename ensures the prompt is identical regardless of filesystem ordering (which varies across OS).
- Together, these guarantee SC-003 (deterministic category assignments).

**Alternatives considered**:
- Caching previous results and reusing: Rejected — adds complexity; temperature=0 + sorted input achieves the same goal more simply.
- Using a seed parameter: Not available in DeepSeek API.

## Decision 3: Prompt Design for Categorization

**Decision**: Send a JSON array of `{filename, description, keywords}` objects and ask for a JSON response with `{categories: [{name, papers: [filename]}]}`.

**Rationale**:
- Structured input (JSON) is unambiguous and easy to construct programmatically.
- Structured output (JSON) is easy to parse and validate.
- Including both description and keywords gives the model rich context for clustering.
- The model determines the number and names of categories — no hardcoded taxonomy.

**Alternatives considered**:
- Markdown-formatted prompt: Rejected — harder to parse reliably; JSON-in/JSON-out is cleaner.
- Sending full page content: Rejected — too much data for 20+ papers; descriptions + keywords are sufficient for topic clustering.

## Decision 4: Reorganization Safety

**Decision**: Reorganization uses `shutil.move()` with pre-validation (check source exists, target doesn't conflict) and writes a `_reorganized.json` manifest before moving files, enabling undo.

**Rationale**:
- File moves are destructive — if interrupted, the folder could be in an inconsistent state.
- Writing a manifest first means the operation can be verified or rolled back.
- Pre-validation catches conflicts (e.g., two papers with the same name in different categories) before any files are moved.

**Alternatives considered**:
- Copy instead of move: Rejected — doubles disk usage for large PDF collections.
- Symlinks: Rejected — not portable across all platforms (Windows limitations).

## Decision 5: Where categories.json Lives

**Decision**: `categories.json` is written to the input folder root (same level as the PDFs).

**Rationale**:
- It's a folder-level artifact that describes the entire collection.
- Placing it alongside the PDFs makes it easy to find and doesn't require a separate output directory.
- After reorganization, it stays at the root level above the category subdirectories.

**Alternatives considered**:
- Separate output directory: Rejected — adds a `--output` flag and complicates the mental model.
- Inside each paper's output folder: Rejected — categories are a cross-paper concept, not per-paper.
