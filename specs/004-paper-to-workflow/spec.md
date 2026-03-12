# Feature Specification: Research Paper to Workflow

**Feature Branch**: `004-paper-to-workflow`
**Created**: 2026-03-12
**Status**: Draft
**Input**: "Research Paper to Workflow - Given a research paper PDF describing a process or algorithm, extract a step-by-step workflow document with prerequisites, numbered steps, decision points, expected outputs, and validation criteria."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Workflow from Single Paper (Priority: P1)

A developer reads a research paper describing an algorithm or process. They want a structured, actionable workflow they can follow to reproduce or apply the paper's approach. They run `docmeld workflow paper.pdf` and get a markdown workflow file.

**Why this priority**: This is the entire feature.

**Independent Test**: Run `docmeld workflow` on a sample PDF and verify a `_workflow.md` file is created with all required sections.

**Acceptance Scenarios**:

1. **Given** a single research paper PDF, **When** the user runs `docmeld workflow paper.pdf`, **Then** a `_workflow.md` file is created in the paper's output directory with five sections: Prerequisites, Steps, Decision Points, Expected Outputs, Validation Criteria.
2. **Given** a paper already processed through bronze/silver, **When** the user runs the command, **Then** bronze/silver are skipped and only workflow generation runs.
3. **Given** a generated workflow, **When** the user reads it, **Then** the steps are numbered, ordered, and actionable.

---

### Edge Cases

- Non-algorithmic paper (survey/review): generate a workflow for "how to conduct this type of survey" based on the paper's methodology section.
- Paper with zero extractable text: report error, no partial file.
- DeepSeek API unavailable: report error, no partial file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a single PDF and generate a workflow markdown file.
- **FR-002**: System MUST process through bronze and silver before workflow generation.
- **FR-003**: System MUST skip bronze/silver if outputs exist (idempotency).
- **FR-004**: System MUST generate a workflow with five sections: Prerequisites, Steps, Decision Points, Expected Outputs, Validation Criteria.
- **FR-005**: System MUST derive all content from the paper.
- **FR-006**: System MUST output as `_workflow.md` in the paper's output directory.
- **FR-007**: System MUST be invocable via CLI: `docmeld workflow <path>`.
- **FR-008**: System MUST be invocable via Python API: `DocMeldParser(path).process_workflow()`.
- **FR-009**: System MUST not create partial files on failure.

### Key Entities

- **WorkflowResult**: output_path (str), sections (int), source_pdf (str), skipped (bool).

## Success Criteria *(mandatory)*

- **SC-001**: `docmeld workflow paper.pdf` produces a `_workflow.md` with all five sections.
- **SC-002**: Steps are numbered and actionable.
- **SC-003**: Deterministic output (temperature=0).
