# Feature Specification: MVP PDF Data Pipeline

**Feature Branch**: `001-mvp-pdf-pipeline`
**Created**: 2026-03-12
**Status**: Draft
**Input**: User description: "MVP PDF data pipeline with bronze, silver, and gold processing stages"

## Clarifications

### Session 2026-03-12

- Q: When processing a folder of PDFs and one file fails at the bronze stage, should the pipeline continue processing remaining files or stop immediately? → A: Continue processing all files, log errors, report failures in summary (fail-fast disabled)
- Q: Should gold output overwrite the silver JSONL in-place, or write to a separate file? → A: Write to separate file with `_gold` suffix (e.g., `filename_hash6_gold.jsonl`)
- Q: Where should the log file be created and what naming convention should be used? → A: Timestamped log file `docmeld_YYYYMMDD_HHMMSS.log` in current working directory
- Q: How should the DeepSeek API key and endpoint be configured? → A: Environment variable `DEEPSEEK_API_KEY` (required), optional `DEEPSEEK_API_ENDPOINT` for custom endpoints, with support for `.env.local` file at repo root
- Q: Should table numbering in silver JSONL reset per page or remain global across the document? → A: Global numbering across entire document (Table1, Table2, ... TableN)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process Single PDF to Bronze Format (Priority: P1)

As a developer, I want to process a single PDF file into a structured JSON format so that I can extract and analyze document elements programmatically.

**Why this priority**: This is the foundation of the entire pipeline. Without bronze-level processing, no downstream stages can function. It delivers immediate value by converting unstructured PDFs into structured, machine-readable JSON.

**Independent Test**: Can be fully tested by providing a PDF file path, running the bronze processor, and verifying that a sanitized filename with hash suffix is created along with a JSON file containing all document elements (text, tables, titles, images) with correct page numbers.

**Acceptance Scenarios**:

1. **Given** a PDF file at path `/documents/research_report.pdf`, **When** I run the bronze processor, **Then** the system creates a sanitized filename `research_report_a3f5c2.pdf` (where `a3f5c2` is the last 6 digits of MD5 hash), creates a folder `research_report_a3f5c2/`, and generates `research_report_a3f5c2.json` containing all document elements in reading order.

2. **Given** a PDF with special characters in filename like `Report (2024) - Final!.pdf`, **When** I run the bronze processor, **Then** the system sanitizes the filename to `report_2024_final_b7e9d1.pdf` (removing dangerous path characters) and processes it successfully.

3. **Given** a multi-page PDF with tables, images, and text, **When** I run the bronze processor, **Then** the JSON output contains elements with types "text", "table", "title", "image" in document order, each with correct `page_no` starting from 1.

4. **Given** a PDF that has already been processed (hash exists), **When** I run the bronze processor again, **Then** the system skips re-processing and uses the existing JSON file.

---

### User Story 2 - Process Folder of PDFs to Bronze Format (Priority: P1)

As a developer, I want to process an entire folder of PDF files in batch so that I can efficiently convert large document collections without manual intervention.

**Why this priority**: Batch processing is essential for real-world use cases where users have dozens or hundreds of documents. This is still P1 because it's a natural extension of single-file processing and critical for MVP adoption.

**Independent Test**: Can be fully tested by providing a folder path containing multiple PDFs, running the bronze processor, and verifying that all PDFs are processed with sanitized filenames, hash suffixes, and corresponding JSON files.

**Acceptance Scenarios**:

1. **Given** a folder `/documents/` containing 10 PDF files, **When** I run the bronze processor on the folder, **Then** all 10 PDFs are processed, each with sanitized filename, hash suffix, output folder, and JSON file.

2. **Given** a folder with mixed file types (PDFs, DOCX, images), **When** I run the bronze processor, **Then** only PDF files are processed and other file types are ignored with a warning message.

3. **Given** a folder where some PDFs have already been processed, **When** I run the bronze processor, **Then** only unprocessed PDFs are converted, and existing processed files are skipped.

---

### User Story 3 - Convert Bronze JSON to Silver JSONL (Priority: P2)

As a developer, I want to convert bronze JSON files into page-by-page JSONL format so that each page becomes a standalone document suitable for agent consumption.

**Why this priority**: Silver processing transforms the element-based structure into page-based documents, which is the format agents need. This is P2 because it depends on bronze processing but is essential for the agent-ready output goal.

**Independent Test**: Can be fully tested by providing a bronze JSON file, running the silver processor, and verifying that a JSONL file is created where each line represents one page with metadata and markdown-formatted content including title hierarchy.

**Acceptance Scenarios**:

1. **Given** a bronze JSON file `research_report_a3f5c2.json` with elements across 5 pages, **When** I run the silver processor, **Then** a JSONL file `research_report_a3f5c2.jsonl` is created with exactly 5 lines (one per page).

2. **Given** a bronze JSON with title elements at different levels, **When** I run the silver processor, **Then** each page in the JSONL starts with the complete title hierarchy (all parent titles) in markdown format.

3. **Given** a bronze JSON with tables marked as `[[Table1]]`, **When** I run the silver processor, **Then** the silver JSONL preserves table markers and formatting in the `page_content` field.

4. **Given** a page with multiple title levels (e.g., H1, H2, H3), **When** I run the silver processor, **Then** the page content includes all title levels in proper markdown hierarchy (# Title, ## Subtitle, ### Section).

---

### User Story 4 - Enrich Silver JSONL with Gold Metadata (Priority: P3)

As a developer, I want to analyze each page's content and extract descriptions and keywords so that agents can quickly understand and search document content.

**Why this priority**: Gold processing adds semantic metadata that makes documents more discoverable and useful for agents. This is P3 because it's an enhancement that requires external API calls (DeepSeek) and can be added after core pipeline functionality is working.

**Independent Test**: Can be fully tested by providing a silver JSONL file, running the gold processor with DeepSeek API, and verifying that each page now includes `description` and `keywords` fields in the metadata.

**Acceptance Scenarios**:

1. **Given** a silver JSONL file with 5 pages, **When** I run the gold processor, **Then** each page's metadata is enriched with a one-line `description` and a list of `keywords` extracted by DeepSeek-chat.

2. **Given** a page about financial earnings, **When** I run the gold processor, **Then** the description summarizes the key financial metrics and keywords include relevant terms like "revenue", "EBITDA", "quarterly results".

3. **Given** a silver JSONL file that has already been processed to gold, **When** I run the gold processor again, **Then** the system skips re-processing and uses the existing gold JSONL file.

---

### Edge Cases

- **What happens when a PDF file is corrupted or unreadable?** The system logs an error with the filename and continues processing other files in batch mode. The corrupted file is skipped and reported in the summary.

- **What happens when a PDF has no extractable text (scanned image)?** The bronze processor extracts what it can (images, page structure) and creates a JSON with image elements. Text elements will be empty or minimal. A warning is logged indicating OCR may be needed.

- **What happens when a filename is extremely long (>200 characters)?** The system truncates the sanitized filename to 200 characters before adding the hash suffix, ensuring filesystem compatibility.

- **What happens when two different PDFs have the same filename?** The MD5 hash suffix ensures uniqueness. Even if filenames are identical, different content produces different hashes, so `report_a3f5c2.pdf` and `report_b7e9d1.pdf` are distinct.

- **What happens when DeepSeek API is unavailable during gold processing?** The system retries up to 3 times with exponential backoff. If all retries fail, the page is marked with `"gold_processing_failed": true` in metadata and processing continues for other pages.

- **What happens when a page has no meaningful content (blank page)?** The silver processor creates a JSONL entry with empty `page_content` and the gold processor generates a description like "Blank page" with no keywords.

## Requirements *(mandatory)*

### Functional Requirements

**Bronze Level Processing:**

- **FR-001**: System MUST accept a local file path to a single PDF or a folder containing multiple PDFs as input.

- **FR-002**: System MUST sanitize PDF filenames by removing or replacing characters that are dangerous in file paths (e.g., `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`).

- **FR-003**: System MUST calculate the MD5 hash of each PDF file and append the last 6 digits of the hash to the sanitized filename (e.g., `filename_stem_a3f5c2.pdf`).

- **FR-004**: System MUST create an output folder with the same name as the hashed filename (e.g., `filename_stem_a3f5c2/`) in the same directory as the source PDF.

- **FR-005**: System MUST extract document elements from the PDF using PyMuPDF (fitz) and store them in a JSON file named `filename_stem_hash6.json`.

- **FR-006**: System MUST support the following element types in the JSON output: "text", "table", "title", "image".

- **FR-007**: Each element in the JSON MUST include a `type` field (string) and a `page_no` field (integer starting from 1).

- **FR-008**: Title elements MUST include a `level` field (integer, 0-based) and a `content` field (string).

- **FR-009**: Text elements MUST include a `content` field (string) containing the extracted text.

- **FR-010**: Table elements MUST include a `content` field (markdown-formatted table string) and a `summary` field (string describing table contents).

- **FR-011**: Image elements MUST include `image_name`, `content` (optional description), `image` (base64-encoded), `image_id`, and `bbox` (bounding box coordinates) fields.

- **FR-012**: Elements in the JSON MUST be ordered according to the document's reading order (top-to-bottom, left-to-right).

- **FR-013**: System MUST skip re-processing if a bronze JSON file already exists for a given PDF hash.

**Silver Level Processing:**

- **FR-014**: System MUST accept a bronze JSON file path as input and produce a JSONL file with the same base name (e.g., `filename_stem_hash6.jsonl`).

- **FR-015**: Each line in the JSONL file MUST represent one page of the PDF document.

- **FR-016**: Each JSONL line MUST be a valid JSON object with `metadata` and `page_content` fields.

- **FR-017**: The `metadata` field MUST include: `uuid` (unique identifier), `source` (filename), `page_no` (e.g., "page1"), and `session_title` (markdown title hierarchy).

- **FR-018**: System MUST track title hierarchy across elements and include all parent titles at the beginning of each page's content.

- **FR-019**: The `page_content` field MUST render all elements from that page in markdown format, preserving table markers like `[[Table1]]` and `[/Table1]`. Table numbering MUST be global across the entire document (not reset per page), and only tables with more than 1 data row receive a numbered marker; small tables use `[[Table]]` without a number.

- **FR-020**: Title elements MUST be rendered as markdown headings (e.g., `#`, `##`, `###`) based on their level.

- **FR-021**: When a new page starts, the system MUST include the complete title hierarchy from previous pages if titles span multiple pages.

- **FR-022**: System MUST skip re-processing if a silver JSONL file already exists for a given bronze JSON.

**Gold Level Processing:**

- **FR-023**: System MUST accept a silver JSONL file path as input and produce an enriched JSONL file with a `_gold` suffix (e.g., `filename_hash6_gold.jsonl`) in the same output folder, preserving the original silver JSONL file.

- **FR-024**: System MUST use DeepSeek-chat API to analyze each page's `page_content` and extract semantic metadata. API credentials MUST be provided via the `DEEPSEEK_API_KEY` environment variable (required). An optional `DEEPSEEK_API_ENDPOINT` environment variable MAY be used to specify custom API endpoints. The system MUST support loading these variables from a `.env.local` file at the repository root.

- **FR-025**: For each page, the system MUST add a `description` field (string, one-line summary) to the metadata.

- **FR-026**: For each page, the system MUST add a `keywords` field (list of strings) to the metadata.

- **FR-027**: System MUST handle API rate limiting by implementing exponential backoff with up to 3 retry attempts.

- **FR-028**: System MUST continue processing remaining pages if one page fails gold enrichment, marking failed pages with `"gold_processing_failed": true`.

- **FR-029**: System MUST skip re-processing if a gold JSONL file already exists (determined by presence of `description` and `keywords` fields in metadata).

**General Requirements:**

- **FR-030**: System MUST provide progress indicators when processing multiple files (e.g., "Processing 3/10 files...").

- **FR-031**: System MUST log all errors with sufficient context (filename, page number, error message) to a timestamped log file named `docmeld_YYYYMMDD_HHMMSS.log` in the current working directory. A new log file is created per pipeline invocation.

- **FR-032**: System MUST generate a summary report after processing showing: total files processed, successful conversions, failed conversions, and processing time.

- **FR-033**: System MUST be idempotent - running the same processing step multiple times produces the same result without duplicating work.

- **FR-034**: When processing multiple files in batch mode, the system MUST continue processing all remaining files even if one file fails, logging each error and including all failures in the final summary report (fail-fast disabled).

### Key Entities

- **PDF Document**: The source file to be processed. Attributes: original filename, sanitized filename, MD5 hash, file size, page count.

- **Document Element**: A structural component extracted from the PDF. Attributes: type (text/table/title/image), page_no, content, additional type-specific fields.

- **Bronze JSON**: The intermediate structured representation of a PDF. Contains an ordered list of document elements.

- **Silver Page**: A single page from a document represented as a standalone JSON object. Attributes: metadata (uuid, source, page_no, session_title), page_content (markdown-formatted).

- **Gold Page**: An enriched silver page with semantic metadata. Additional attributes: description (string), keywords (list of strings).

- **Processing Pipeline**: The three-stage transformation process. Stages: Bronze (PDF → JSON), Silver (JSON → JSONL by page), Gold (JSONL → enriched JSONL with AI metadata).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A single PDF file (10-50 pages) can be processed through all three pipeline stages (bronze → silver → gold) in under 5 minutes on standard hardware.

- **SC-002**: The system successfully processes 95% of digital-native PDF files without errors or data loss.

- **SC-003**: Bronze JSON output preserves 100% of extractable text content from the source PDF in correct reading order.

- **SC-004**: Silver JSONL output contains exactly one line per page, with each page including complete title hierarchy context.

- **SC-005**: Gold metadata extraction produces relevant descriptions and keywords for 90% of pages as validated by manual review of sample outputs.

- **SC-006**: Batch processing of 100 PDF files completes without manual intervention, with a detailed summary report of successes and failures.

- **SC-007**: Re-running the pipeline on already-processed files completes in under 10 seconds (skipping existing outputs).

- **SC-008**: The system handles filenames with special characters, spaces, and unicode without errors or data corruption.

- **SC-009**: Memory usage stays under 500MB when processing PDFs up to 100 pages.

- **SC-010**: The pipeline produces outputs that are directly consumable by downstream agent systems without additional transformation.
