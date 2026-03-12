# Data Model: Research Papers Batch Categorize

**Feature**: 002-paper-batch-categorize
**Date**: 2026-03-12

## Entities

### PaperMetadata

Represents the aggregated metadata for a single paper, collected from its gold JSONL output.

| Field | Type | Description |
|-------|------|-------------|
| filename | string | Original PDF filename (e.g., "attention_is_all_you_need.pdf") |
| file_path | string | Absolute path to the PDF file |
| output_dir | string | Path to the paper's output directory (bronze/silver/gold files) |
| description | string | Aggregated description from gold stage (combined across pages) |
| keywords | list[string] | Deduplicated keywords from all pages of the gold JSONL |
| page_count | integer | Number of pages in the paper |
| gold_path | string | Path to the gold JSONL file |

### Category

Represents a topic cluster identified by the AI model.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Human-readable category name (e.g., "Natural Language Processing") |
| papers | list[string] | List of filenames assigned to this category |
| keywords | list[string] | Representative keywords for this category |

### CategoryIndex

The top-level structure written to `categories.json`.

| Field | Type | Description |
|-------|------|-------------|
| created | string | ISO 8601 timestamp of when the index was generated |
| source_folder | string | Absolute path to the input folder |
| total_papers | integer | Number of papers in the index |
| total_categories | integer | Number of categories identified |
| categories | list[Category] | The category definitions |
| papers | list[PaperEntry] | Per-paper entries with category assignment |

### PaperEntry

A single paper's entry in the category index.

| Field | Type | Description |
|-------|------|-------------|
| filename | string | Original PDF filename |
| category | string | Assigned category name |
| description | string | Paper-level description |
| keywords | list[string] | Paper-level keywords |

## Relationships

```
CategoryIndex
├── categories: list[Category]
│   └── papers: list[filename] ──→ PaperEntry.filename
└── papers: list[PaperEntry]
    └── category: string ──→ Category.name
```

- Each PaperEntry belongs to exactly one Category (FR-006).
- Each Category contains one or more PaperEntries.
- The `categories` list and `papers` list are two views of the same data — categories grouped by topic, papers listed individually.

## State Transitions

### Paper Processing State

```
UNPROCESSED → BRONZE_DONE → SILVER_DONE → GOLD_DONE → CATEGORIZED
                                              │
                                              └→ GOLD_FAILED (excluded from categorization)
```

### Folder Processing State

```
RAW_FOLDER → PROCESSED (all papers through gold) → CATEGORIZED (categories.json written)
                                                        │
                                                        └→ REORGANIZED (files moved into category dirs)
```

## Validation Rules

- `filename` must be non-empty and end with `.pdf` (case-insensitive)
- `category` name must be non-empty, max 100 characters, filesystem-safe after sanitization
- `keywords` list must contain 1–20 items per paper
- `total_papers` must equal `len(papers)`
- `total_categories` must equal `len(categories)`
- Every paper in `papers` must reference a category that exists in `categories`
- Every category in `categories` must have at least one paper
