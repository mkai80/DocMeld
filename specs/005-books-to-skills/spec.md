# Feature Specification: Books to Claude Skills

**Feature Branch**: `005-books-to-skills`
**Created**: 2026-03-12
**Status**: Draft
**Input**: "Books to Claude Skills - Given a technical book PDF, extract knowledge into structured Claude Code skill files that encode the book's methodology as reusable agent skills."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Skills from a Technical Book (Priority: P1)

A developer has a technical book PDF (e.g., "Clean Code", "Designing Data-Intensive Applications"). They want to extract the book's key methodologies and techniques into Claude Code skill files they can drop into `.claude/commands/`. They run `docmeld skills book.pdf` and get a directory of `.md` skill files.

**Why this priority**: This is the core feature — without skill extraction there is nothing to deliver.

**Independent Test**: Run `docmeld skills` on a sample PDF and verify a `_skills/` directory is created containing at least one valid skill `.md` file.

**Acceptance Scenarios**:

1. **Given** a technical book PDF, **When** the user runs `docmeld skills book.pdf`, **Then** a `_skills/` directory is created in the book's output directory containing one or more `.md` skill files.
2. **Given** a book already processed through bronze/silver, **When** the user runs the command, **Then** bronze/silver are skipped and only skill extraction runs.
3. **Given** a generated skill file, **When** the user reads it, **Then** it contains a description header, step-by-step instructions, and is self-contained.

---

### Edge Cases

- Very short PDF (< 5 pages): generate fewer skills, possibly just one.
- Non-technical PDF: generate skills based on whatever methodology is present.
- DeepSeek API unavailable: report error, no partial output.
- Very long book (500+ pages): process in chunks, summarize before skill extraction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a single PDF and generate skill markdown files.
- **FR-002**: System MUST process through bronze and silver before skill extraction.
- **FR-003**: System MUST skip bronze/silver if outputs exist (idempotency).
- **FR-004**: Each skill file MUST contain: a description line, step-by-step instructions, and at least one example or edge case note.
- **FR-005**: System MUST derive all skill content from the book's actual content.
- **FR-006**: System MUST output skills into a `_skills/` subdirectory in the book's output directory.
- **FR-007**: System MUST be invocable via CLI: `docmeld skills <path>`.
- **FR-008**: System MUST be invocable via Python API: `DocMeldParser(path).process_skills()`.
- **FR-009**: System MUST handle long books by chunking content before sending to the API.
- **FR-010**: System MUST not create partial skill files on failure.
- **FR-011**: Skill filenames MUST be kebab-case derived from the skill title.

### Key Entities

- **SkillsResult**: output_dir (str), skill_count (int), source_pdf (str), skipped (bool).
- **Skill File**: A markdown file with description, instructions, and examples.

## Success Criteria *(mandatory)*

- **SC-001**: `docmeld skills book.pdf` produces a `_skills/` directory with at least one skill file.
- **SC-002**: Each skill file is self-contained and actionable.
- **SC-003**: Skill filenames are kebab-case and filesystem-safe.
- **SC-004**: Deterministic output (temperature=0).
