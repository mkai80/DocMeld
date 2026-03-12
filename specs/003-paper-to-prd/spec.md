# Feature Specification: Research Paper to PRD

**Feature Branch**: `003-paper-to-prd`
**Created**: 2026-03-12
**Status**: Draft
**Input**: User description: "Research Paper to PRD - Given a single research paper PDF (CS/engineering), extract text through Bronze and Silver stages, then generate a structured PRD containing problem statement, proposed solution, key features, technical requirements, target users, and success metrics derived from the paper content. Output as a _prd.md file alongside the gold JSONL. Invocable via CLI: docmeld prd paper.pdf"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate PRD from Single Paper (Priority: P1)

A developer reads a CS research paper describing a novel system. They want to quickly extract a structured PRD to evaluate whether the research could become a product. They run `docmeld prd paper.pdf` and get a markdown PRD file with six sections grounded in the paper's actual content.

**Why this priority**: This is the entire feature — without PRD generation there is nothing to deliver.

**Independent Test**: Run `docmeld prd` on a sample PDF and verify a `_prd.md` file is created with all required sections populated.

**Acceptance Scenarios**:

1. **Given** a single research paper PDF, **When** the user runs `docmeld prd paper.pdf`, **Then** the paper is processed through bronze and silver stages, and a `_prd.md` file is created in the paper's output directory.
2. **Given** a paper already processed through bronze/silver, **When** the user runs `docmeld prd paper.pdf`, **Then** bronze/silver are skipped and only PRD generation runs.
3. **Given** a generated PRD, **When** the user reads it, **Then** it contains all six sections: Problem Statement, Proposed Solution, Key Features, Technical Requirements, Target Users, Success Metrics.

---

### User Story 2 - PRD via Python API (Priority: P2)

A developer integrating DocMeld into their pipeline wants to generate PRDs programmatically using `DocMeldParser.process_prd()`.

**Why this priority**: Library-first per constitution. The CLI wraps the API.

**Independent Test**: Call `parser.process_prd()` in a test and verify the returned result contains the PRD path.

**Acceptance Scenarios**:

1. **Given** a DocMeldParser initialized with a PDF path, **When** `process_prd()` is called, **Then** it returns a PrdResult with the output path and section count.
2. **Given** a PDF that fails during bronze extraction, **When** `process_prd()` is called, **Then** it raises an appropriate error without leaving partial output.

---

### Edge Cases

- What happens when the PDF is not a research paper (e.g., a receipt)? The system should still generate a PRD with whatever content it can extract — sections may be sparse but the file should be valid.
- What happens when the PDF has zero extractable text? The system should report an error indicating no content was extracted.
- What happens when the DeepSeek API is unavailable? The system should report the error clearly and not create a partial PRD file.
- What happens when the paper is very long (100+ pages)? The system should truncate/summarize input to fit within API token limits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a single PDF file path and generate a PRD markdown file.
- **FR-002**: System MUST process the PDF through bronze and silver stages before PRD generation.
- **FR-003**: System MUST skip bronze/silver if outputs already exist (idempotency).
- **FR-004**: System MUST generate a PRD with exactly six sections: Problem Statement, Proposed Solution, Key Features, Technical Requirements, Target Users, Success Metrics.
- **FR-005**: System MUST derive all PRD content from the actual paper content.
- **FR-006**: System MUST output the PRD as a `_prd.md` file in the paper's output directory.
- **FR-007**: System MUST be invocable via CLI: `docmeld prd <path>`.
- **FR-008**: System MUST be invocable via Python API: `DocMeldParser(path).process_prd()`.
- **FR-009**: System MUST handle long papers by summarizing content before sending to the API.
- **FR-010**: System MUST not create partial PRD files on failure — either complete output or no file.

### Key Entities

- **PrdResult**: Output of PRD generation. Attributes: output_path (str), sections (int), source_pdf (str).
- **PRD Document**: A markdown file with six fixed sections containing content derived from the paper.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `docmeld prd paper.pdf` produces a `_prd.md` file with all six sections.
- **SC-002**: Each PRD section contains at least one sentence of content derived from the paper.
- **SC-003**: Running the command twice produces the same PRD (deterministic via temperature=0).
- **SC-004**: PRD generation completes in under 30 seconds for a typical 10-page paper.
- **SC-005**: The PRD file is valid markdown that renders correctly.
