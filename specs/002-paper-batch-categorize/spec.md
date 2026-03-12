# Feature Specification: Research Papers Batch Categorize

**Feature Branch**: `002-paper-batch-categorize`
**Created**: 2026-03-12
**Status**: Draft
**Input**: User description: "Research Papers General Reading - Given a folder path containing many PDFs downloaded from arXiv and Google Scholar, batch-process all papers through the Bronze-Silver-Gold pipeline, extract topics and keywords per paper via DeepSeek-chat, aggregate gold metadata across all papers to identify topic clusters, generate a category index (categories.json) mapping each paper to its assigned category, and optionally reorganize files by moving each PDF and its output folder into a category subfolder."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Batch Process Research Papers (Priority: P1)

A researcher has a folder of 20+ PDF papers downloaded from arXiv and Google Scholar. They want to process all papers through DocMeld's full pipeline (Bronze → Silver → Gold) in a single command, producing structured elements, page-by-page content, and AI-enriched metadata (description + keywords) for every paper.

**Why this priority**: This is the foundation — without batch processing through all three stages, no categorization or indexing is possible. It also validates that the existing pipeline scales to real-world folder sizes.

**Independent Test**: Can be fully tested by pointing the command at a folder of 3+ sample PDFs and verifying that each PDF produces a bronze JSON, silver JSONL, and gold JSONL output.

**Acceptance Scenarios**:

1. **Given** a folder containing 5 PDF files, **When** the user runs the batch categorize command, **Then** all 5 PDFs are processed through bronze, silver, and gold stages with output files created for each.
2. **Given** a folder where 2 of 5 PDFs have already been processed, **When** the user runs the command again, **Then** the 2 already-processed PDFs are skipped (idempotency) and only the 3 new ones are processed.
3. **Given** a folder containing non-PDF files mixed with PDFs, **When** the user runs the command, **Then** only PDF files are processed and non-PDF files are ignored.

---

### User Story 2 - Topic Categorization and Index Generation (Priority: P2)

After all papers are processed through the gold stage, the system aggregates the keywords and descriptions across all papers, identifies topic clusters, and produces a machine-readable category index (`categories.json`) that maps each paper to its assigned category.

**Why this priority**: This is the core differentiator of this use case — turning individual paper metadata into a structured overview of the entire collection. Without this, the user just has per-paper metadata (which the MVP already provides).

**Independent Test**: Can be tested by providing a set of pre-existing gold JSONL files (no need to re-run bronze/silver) and verifying that a `categories.json` is produced with sensible groupings.

**Acceptance Scenarios**:

1. **Given** a folder where all PDFs have been processed through gold stage, **When** the categorization step runs, **Then** a `categories.json` file is created in the folder root listing each paper with its assigned category and keywords.
2. **Given** 10 papers spanning 3 distinct topics (e.g., NLP, computer vision, reinforcement learning), **When** categorization runs, **Then** the system identifies at least 2 distinct categories and assigns each paper to exactly one category.
3. **Given** the same folder processed twice with no changes, **When** categorization runs both times, **Then** the category assignments are identical (deterministic).

---

### User Story 3 - File Reorganization by Category (Priority: P3)

After categorization, the user can optionally reorganize the folder so that each PDF and its output subfolder are moved into a category-named directory. This makes it easy to browse papers by topic in a file manager.

**Why this priority**: This is a convenience feature that builds on top of categorization. The category index alone is useful; physical file reorganization is a nice-to-have.

**Independent Test**: Can be tested by running the reorganize step on a folder with an existing `categories.json` and verifying that files are moved into the correct subdirectories.

**Acceptance Scenarios**:

1. **Given** a folder with `categories.json` and 5 processed PDFs, **When** the user runs the command with the reorganize option, **Then** each PDF and its output folder are moved into a subdirectory named after its category.
2. **Given** a folder that has already been reorganized, **When** the user runs the command again, **Then** no files are moved (idempotent) and no errors occur.
3. **Given** a paper whose category name contains special characters, **When** reorganization runs, **Then** the directory name is sanitized to be filesystem-safe.

---

### Edge Cases

- What happens when the folder contains zero PDF files? The system should report "no PDFs found" and exit gracefully.
- What happens when a single PDF fails during gold stage (e.g., API timeout)? The system should continue processing remaining papers and report the failure, then exclude the failed paper from categorization.
- What happens when all papers have very similar content and no clear topic boundaries? The system should assign all papers to a single category rather than forcing artificial splits.
- What happens when the folder path does not exist? The system should report a clear error message.
- What happens when a PDF is corrupted or has zero extractable text? The system should skip it, log a warning, and continue with the remaining papers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a folder path and process all PDF files within it through the full Bronze → Silver → Gold pipeline.
- **FR-002**: System MUST skip already-processed PDFs (idempotency) based on existing output files.
- **FR-003**: System MUST extract keywords and a description for each paper during the gold stage using the existing DeepSeek-chat integration.
- **FR-004**: System MUST aggregate gold-stage metadata (keywords, descriptions) across all successfully processed papers to identify topic clusters.
- **FR-005**: System MUST generate a `categories.json` file in the input folder containing: each paper's filename, assigned category name, keywords, and description.
- **FR-006**: System MUST assign exactly one category to each paper.
- **FR-007**: System MUST produce deterministic category assignments for the same input (same papers, same metadata → same categories).
- **FR-008**: System MUST support an optional reorganize mode that moves each PDF and its output folder into a category-named subdirectory.
- **FR-009**: System MUST sanitize category names for filesystem safety (no special characters, reasonable length).
- **FR-010**: System MUST continue processing remaining papers when an individual paper fails, and report all failures at the end.
- **FR-011**: System MUST be invocable via both CLI command and Python API.
- **FR-012**: System MUST log progress (e.g., "Processing 3/10: paper_name.pdf") during batch operations.

### Key Entities

- **Paper**: A single PDF file with its associated bronze JSON, silver JSONL, and gold JSONL outputs. Key attributes: filename, file path, output directory, processing status, keywords, description, assigned category.
- **Category**: A topic cluster derived from aggregating paper keywords. Key attributes: category name, list of member papers, representative keywords.
- **Category Index**: A single JSON file (`categories.json`) that maps all papers to their categories. Serves as the machine-readable output of the categorization step.

## Assumptions

- The existing Bronze → Silver → Gold pipeline from the MVP (001) is stable and handles individual PDF processing correctly.
- DeepSeek-chat API is available and configured via `.env.local` for the gold stage.
- Category identification is performed by the AI model (DeepSeek-chat) in a single aggregation call after all papers are processed, not by a local clustering algorithm.
- The number of categories is determined automatically by the AI model based on the content — the user does not specify a target number of categories.
- Papers in the folder are independent documents (not chapters of a single book).
- The folder structure is flat (PDFs are directly in the given folder, not in nested subdirectories).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A folder of 10 PDFs is fully processed (bronze + silver + gold + categorization) in a single command invocation.
- **SC-002**: The `categories.json` output is valid, parseable, and contains an entry for every successfully processed paper.
- **SC-003**: Running the same command twice on the same folder produces identical `categories.json` content (deterministic).
- **SC-004**: When 1 out of 10 papers fails during processing, the remaining 9 are still categorized successfully.
- **SC-005**: File reorganization correctly places all PDFs and their output folders into category subdirectories with no data loss.
- **SC-006**: The user can understand the categorization results by reading `categories.json` without needing additional tools.
