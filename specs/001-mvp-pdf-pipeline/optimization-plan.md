                                                                                                                        │
│ Plan: ParserBackend Abstraction, Docling Integration, Schema Enhancements & AGPL Relicensing                                                        │
│                                                                                                                                                     │
│ Context                                                                                                                                             │
│                                                                                                                                                     │
│ DocMeld v0.1.0 is complete with 109 tests and a working Bronze→Silver→Gold pipeline. Three issues need addressing:                                  │
│                                                                                                                                                     │
│ 1. License incompatibility: pymupdf4llm/PyMuPDF are AGPL-3.0 but DocMeld is MIT. User decided to relicense to AGPL.                                 │
│ 2. No parser abstraction: pymupdf4llm is hardcoded in element_extractor.py. Need a ParserBackend interface to swap engines.                         │
│ 3. Schema gaps: Missing element_id, parent_id, and structured table_data on elements (identified in evaluation.md).                                 │
│                                                                                                                                                     │
│ Docling (MIT, ~500MB, CPU-only, no OCR required) was chosen as the second parsing engine.                                                           │
│                                                                                                                                                     │
│ ---                                                                                                                                                 │
│ 1. Relicense to AGPL-3.0                                                                                                                            │
│                                                                                                                                                     │
│ Files to modify:                                                                                                                                    │
│ - /Users/frank/A/DocMeld/docmeld/LICENSE — Replace MIT text with AGPL-3.0 text                                                                      │
│ - /Users/frank/A/DocMeld/docmeld/pyproject.toml — Change license = {text = "MIT"} to {text = "AGPL-3.0"}, update classifier from MIT License to GNU │
│  Affero General Public License v3                                                                                                                   │
│ - /Users/frank/A/DocMeld/docmeld/README.md — Update badge from MIT to AGPL-3.0, update License section                                              │
│ - /Users/frank/A/DocMeld/docmeld/CONTRIBUTING.md — Line 221: change "MIT License" to "AGPL-3.0"                                                     │
│ - /Users/frank/A/DocMeld/docmeld/CHANGELOG.md — Add entry under [Unreleased]                                                                        │
│                                                                                                                                                     │
│ ---                                                                                                                                                 │
│ 2. Add element_id and parent_id to Element Schema                                                                                                   │
│                                                                                                                                                     │
│ 2a. Update Pydantic models (docmeld/docmeld/bronze/element_types.py)                                                                                │
│                                                                                                                                                     │
│ Add optional fields to each element model:                                                                                                          │
│ - element_id: str = "" on all four types (TitleElement, TextElement, TableElement, ImageElement)                                                    │
│ - parent_id: str = "" on all four types                                                                                                             │
│                                                                                                                                                     │
│ These are optional with empty-string defaults so existing JSON files remain valid (backward compatible).                                            │
│                                                                                                                                                     │
│ 2b. Update element extractor (docmeld/docmeld/bronze/element_extractor.py)                                                                          │
│                                                                                                                                                     │
│ In extract_elements(), after building the full element list, assign sequential element_id values:                                                   │
│ for i, elem in enumerate(all_elements):                                                                                                             │
│     elem["element_id"] = f"e_{i+1:03d}"                                                                                                             │
│                                                                                                                                                     │
│ For parent_id: assign based on the most recent title element at a higher level. Track the current title stack (similar to TitleTracker in silver)   │
│ and set parent_id to the element_id of the nearest ancestor title.                                                                                  │
│                                                                                                                                                     │
│ 2c. Add table_data to TableElement (docmeld/docmeld/bronze/element_types.py)                                                                        │
│                                                                                                                                                     │
│ Add to TableElement:                                                                                                                                │
│ table_data: Optional[Dict[str, Any]] = None                                                                                                         │
│                                                                                                                                                     │
│ 2d. Parse structured table data (docmeld/docmeld/bronze/element_extractor.py)                                                                       │
│                                                                                                                                                     │
│ Add a parse_table_data(table_md: str) -> dict function that extracts:                                                                               │
│ {"headers": ["Col1", "Col2"], "rows": [["val1", "val2"]], "num_rows": 1, "num_cols": 2}                                                             │
│                                                                                                                                                     │
│ Call it in extract_elements() alongside generate_table_summary():                                                                                   │
│ if elem["type"] == "table":                                                                                                                         │
│     elem["summary"] = generate_table_summary(elem["content"])                                                                                       │
│     elem["table_data"] = parse_table_data(elem["content"])                                                                                          │
│                                                                                                                                                     │
│ 2e. Update JSON Schema contract (specs/001-mvp-pdf-pipeline/contracts/element-schema.json)                                                          │
│                                                                                                                                                     │
│ Add element_id, parent_id as optional string properties to BaseElement. Add table_data as optional object to TableElement.                          │
│                                                                                                                                                     │
│ 2f. Update tests                                                                                                                                    │
│                                                                                                                                                     │
│ - tests/unit/test_element_types.py — Add tests for new optional fields on all element types                                                         │
│ - tests/unit/test_element_extractor.py — Add tests for element_id assignment, parent_id assignment, parse_table_data()                              │
│ - tests/contract/test_element_schema.py — Add tests validating new fields                                                                           │
│                                                                                                                                                     │
│ ---                                                                                                                                                 │
│ 3. ParserBackend Abstraction Layer                                                                                                                  │
│                                                                                                                                                     │
│ 3a. Create backend protocol (docmeld/docmeld/bronze/backends/__init__.py)                                                                           │
│                                                                                                                                                     │
│ from typing import Any, Dict, List, Protocol                                                                                                        │
│                                                                                                                                                     │
│ class ParserBackend(Protocol):                                                                                                                      │
│     """Protocol for PDF parsing backends."""                                                                                                        │
│     def extract_elements(self, pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:                                                             │
│         """Extract elements from a PDF file."""                                                                                                     │
│         ...                                                                                                                                         │
│                                                                                                                                                     │
│ 3b. Create PyMuPDF backend (docmeld/docmeld/bronze/backends/pymupdf_backend.py)                                                                     │
│                                                                                                                                                     │
│ Move the current extraction logic from element_extractor.py into a class:                                                                           │
│ class PyMuPDFBackend:                                                                                                                               │
│     def extract_elements(self, pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:                                                             │
│         # Current logic from element_extractor.extract_elements()                                                                                   │
│         ...                                                                                                                                         │
│                                                                                                                                                     │
│ Keep parse_markdown_to_elements(), generate_table_summary(), parse_table_data(), and _discover_images() as module-level helpers in                  │
│ element_extractor.py (they're reusable).                                                                                                            │
│                                                                                                                                                     │
│ 3c. Create Docling backend (docmeld/docmeld/bronze/backends/docling_backend.py)                                                                     │
│                                                                                                                                                     │
│ class DoclingBackend:                                                                                                                               │
│     def extract_elements(self, pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:                                                             │
│         from docling.document_converter import DocumentConverter                                                                                    │
│         converter = DocumentConverter()                                                                                                             │
│         result = converter.convert(pdf_path)                                                                                                        │
│         doc = result.document                                                                                                                       │
│         # Map Docling items to DocMeld element format                                                                                               │
│         ...                                                                                                                                         │
│                                                                                                                                                     │
│ Key mapping:                                                                                                                                        │
│ - SectionHeaderItem → {"type": "title", "level": ..., "content": ...}                                                                               │
│ - TextItem → {"type": "text", "content": ...}                                                                                                       │
│ - TableItem → {"type": "table", "content": md, "table_data": structured}                                                                            │
│ - PictureItem → {"type": "image", ...}                                                                                                              │
│ - ListItem → {"type": "text", "content": "- " + text} (flatten to text for now)                                                                     │
│                                                                                                                                                     │
│ 3d. Refactor element_extractor.py                                                                                                                   │
│                                                                                                                                                     │
│ The public extract_elements() function becomes a thin dispatcher:                                                                                   │
│ def extract_elements(pdf_path: str, output_dir: str, backend: str = "pymupdf") -> List[Dict[str, Any]]:                                             │
│     if backend == "docling":                                                                                                                        │
│         from docmeld.bronze.backends.docling_backend import DoclingBackend                                                                          │
│         b = DoclingBackend()                                                                                                                        │
│     else:                                                                                                                                           │
│         from docmeld.bronze.backends.pymupdf_backend import PyMuPDFBackend                                                                          │
│         b = PyMuPDFBackend()                                                                                                                        │
│                                                                                                                                                     │
│     elements = b.extract_elements(pdf_path, output_dir)                                                                                             │
│                                                                                                                                                     │
│     # Post-processing (shared across all backends)                                                                                                  │
│     _assign_element_ids(elements)                                                                                                                   │
│     _assign_parent_ids(elements)                                                                                                                    │
│     for elem in elements:                                                                                                                           │
│         if elem["type"] == "table":                                                                                                                 │
│             elem["summary"] = generate_table_summary(elem["content"])                                                                               │
│             elem["table_data"] = parse_table_data(elem["content"])                                                                                  │
│                                                                                                                                                     │
│     return elements                                                                                                                                 │
│                                                                                                                                                     │
│ 3e. Thread backend parameter through the stack                                                                                                      │
│                                                                                                                                                     │
│ - BronzeProcessor.process_file(pdf_path, backend="pymupdf") — pass to extract_elements()                                                            │
│ - DocMeldParser.__init__(path, output_dir=None, backend="pymupdf") — store and pass through                                                         │
│ - cli.py — Add --backend flag (choices: pymupdf, docling, default: pymupdf)                                                                         │
│                                                                                                                                                     │
│ 3f. Add Docling as optional dependency (pyproject.toml)                                                                                             │
│                                                                                                                                                     │
│ [project.optional-dependencies]                                                                                                                     │
│ docling = ["docling>=2.0.0"]                                                                                                                        │
│ dev = [...]                                                                                                                                         │
│                                                                                                                                                     │
│ Install: pip install docmeld[docling]                                                                                                               │
│                                                                                                                                                     │
│ 3g. Tests for backends                                                                                                                              │
│                                                                                                                                                     │
│ - tests/unit/test_pymupdf_backend.py — Test PyMuPDFBackend class directly                                                                           │
│ - tests/unit/test_docling_backend.py — Test DoclingBackend with mocked Docling imports                                                              │
│ - tests/unit/test_element_extractor.py — Update to test backend dispatch logic                                                                      │
│                                                                                                                                                     │
│ ---                                                                                                                                                 │
│ 4. File Change Summary                                                                                                                              │
│                                                                                                                                                     │
│ ┌────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────┐                                    │
│ │                        File                        │                         Action                          │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/LICENSE                                    │ Replace with AGPL-3.0                                   │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/pyproject.toml                             │ License, classifier, optional dep                       │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/README.md                                  │ Badge + license section                                 │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/CONTRIBUTING.md                            │ License reference                                       │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/CHANGELOG.md                               │ Unreleased entries                                      │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/bronze/element_types.py            │ Add element_id, parent_id, table_data                   │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/bronze/element_extractor.py        │ Add backend dispatch, id assignment, table_data parsing │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/bronze/backends/__init__.py        │ NEW: ParserBackend protocol                             │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/bronze/backends/pymupdf_backend.py │ NEW: Current logic extracted                            │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/bronze/backends/docling_backend.py │ NEW: Docling integration                                │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/bronze/processor.py                │ Pass backend param                                      │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/parser.py                          │ Accept + pass backend param                             │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ docmeld/docmeld/cli.py                             │ Add --backend flag                                      │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ specs/.../contracts/element-schema.json            │ Add new optional fields                                 │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ tests/unit/test_element_types.py                   │ Tests for new fields                                    │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ tests/unit/test_element_extractor.py               │ Tests for ids, table_data, dispatch                     │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ tests/unit/test_pymupdf_backend.py                 │ NEW: Backend unit tests                                 │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ tests/unit/test_docling_backend.py                 │ NEW: Mocked Docling tests                               │                                    │
│ ├────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┤                                    │
│ │ tests/contract/test_element_schema.py              │ Tests for new schema fields                             │                                    │
│ └────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────┘                                    │
│                                                                                                                                                     │
│ ---                                                                                                                                                 │
│ 5. Execution Order                                                                                                                                  │
│                                                                                                                                                     │
│ 1. Relicense to AGPL-3.0 (all license files)                                                                                                        │
│ 2. Add element_id, parent_id, table_data to element types + extractor                                                                               │
│ 3. Update element schema contract                                                                                                                   │
│ 4. Update existing tests for new fields                                                                                                             │
│ 5. Create backends/ package with ParserBackend protocol                                                                                             │
│ 6. Extract PyMuPDFBackend from current element_extractor                                                                                            │
│ 7. Implement DoclingBackend                                                                                                                         │
│ 8. Refactor element_extractor as dispatcher                                                                                                         │
│ 9. Thread backend param through processor → parser → CLI                                                                                            │
│ 10. Add Docling optional dependency to pyproject.toml                                                                                               │
│ 11. Write backend tests (pymupdf + docling with mocks)                                                                                              │
│ 12. Update CHANGELOG                                                                                                                                │
│ 13. Run full test suite to verify                                                                                                                   │
│                                                                                                                                                     │
│ ---                                                                                                                                                 │
│ 6. Verification                                                                                                                                     │
│                                                                                                                                                     │
│ cd /Users/frank/A/DocMeld/docmeld                                                                                                                   │
│ source venv/bin/activate                                                                                                                            │
│                                                                                                                                                     │
│ # Run all tests                                                                                                                                     │
│ pytest tests/ -v --cov=docmeld --cov-report=term-missing                                                                                            │
│                                                                                                                                                     │
│ # Verify license                                                                                                                                    │
│ head -1 LICENSE  # Should show "GNU AFFERO GENERAL PUBLIC LICENSE"                                                                                  │
│                                                                                                                                                     │
│ # Test CLI backend flag                                                                                                                             │
│ docmeld bronze --help  # Should show --backend option                                                                                               │
│                                                                                                                                                     │
│ # Test default backend (pymupdf) still works                                                                                                        │
│ docmeld bronze /path/to/test.pdf                                                                                                                    │
│                                                                                                                                                     │
│ # Test docling backend (requires: pip install docmeld[docling])                                                                                     │
│ docmeld bronze --backend docling /path/to/test.pdf                                                                                                  │
│                                                                                                                                                     │
│ # Lint + type check                                                                                                                                 │
│ ruff check docmeld/                                                                                                                                 │
│ black --check docmeld/                                                                                                                              │
│ mypy docmeld/                                                                                                                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯



