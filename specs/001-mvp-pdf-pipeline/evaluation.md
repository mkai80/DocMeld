# Evaluation: DocMeld PDF Pipeline — Parsing Engine & Element Schema

**Date**: 2026-03-12
**Scope**: Two areas evaluated:
1. PDF parsing engine (pymupdf4llm dependency)
2. Element type schema (title, text, table, image)

---

## Part 1: PDF Parsing Engine Evaluation

### Current Approach

DocMeld's bronze stage relies on `pymupdf4llm.to_markdown()` to convert each PDF page into markdown, then parses that markdown string line-by-line to identify elements (titles via `#`, tables via `|`, text as everything else). This is a two-step indirect extraction: PDF → markdown string → element parsing.

### How pymupdf4llm Works

pymupdf4llm is a thin wrapper around PyMuPDF (fitz) that calls `page.get_text("dict")` to get text blocks with font metadata, then heuristically converts them to markdown. It detects headings by font size, tables by geometric alignment of text spans, and preserves reading order.

**GitHub**: ~2,800 stars (pymupdf/RAG repo)
**License**: AGPL-3.0 (⚠️ this is a concern — see below)

### Benchmark Landscape (2025-2026)

Based on multiple independent benchmarks (Applied-AI PdfBench on 800+ documents, OmniDocBench CVPR 2025, Nicolas Brosse's qualitative comparison, and F22 Labs financial PDF tests):

| Tool | Stars | License | Accuracy (approx) | Speed | GPU Required | Notes |
|------|-------|---------|-------------------|-------|-------------|-------|
| **MinerU 2.5** | ~55k | AGPL-3.0 | 85-90% | Medium | Optional | Best open-source overall; 1.2B model beats Gemini 2.5 Pro on benchmarks |
| **Marker** | ~22k | GPL-3.0 | 80-85% | Fast (122 pg/s batch) | Optional | Strong on academic papers; surfer model for layout detection |
| **Docling** | ~28k | MIT | 75-85% | Medium | Optional | IBM; best structured output schema; DoclingDocument format |
| **pymupdf4llm** | ~2.8k | AGPL-3.0 | 65-75% | Very Fast | No | Good for simple digital PDFs; struggles with complex layouts |
| **PyMuPDF-Layout** | (new) | AGPL-3.0 | 78-82% | 10x faster than Docling | No | Newer PyMuPDF product; layout detection without ML models |
| **MarkItDown** | ~87k | MIT | 25-40% | Very Fast | No | Microsoft; broad format support but poor PDF accuracy |
| **pypdfium2** | ~1k | Apache-2.0 | 80.6% (PdfBench) | 10,000x faster than LLMs | No | Surprisingly strong on PdfBench; pure text extraction |

**Key finding from Applied-AI PdfBench**: On 800+ documents scored by 7 frontier LLMs, pypdfium2 (a simple text extractor) scored 80.6% — competitive with ML-based tools — while running 10,000x faster at zero cost. This suggests that for digital-native PDFs, simple extraction often beats complex ML pipelines.

### pymupdf4llm: Honest Assessment

**Strengths:**
- Zero GPU requirement (aligns with DocMeld's lightweight principle)
- Very fast (pure CPU, no model inference)
- Decent for digital-native PDFs with simple layouts
- Preserves reading order reasonably well
- Your reference_code.py proves it works for financial research reports

**Weaknesses:**
- Table detection is heuristic-based and fragile — merged cells, multi-line cells, and complex headers often break
- No layout detection model — relies on font size heuristics for headings, which fails on PDFs with non-standard fonts
- The markdown-then-parse approach loses structural information that fitz already has (font metadata, bounding boxes, text block coordinates)
- AGPL-3.0 license is problematic for an MIT-licensed project (see below)
- Lower accuracy than Marker, MinerU, and Docling on complex documents
- No formula/equation support
- No multi-column layout detection

### ⚠️ License Concern

**This is the most critical finding.** pymupdf4llm is licensed under AGPL-3.0. DocMeld is MIT-licensed. AGPL-3.0 is a copyleft license that requires any software that links to or uses AGPL code to also be distributed under AGPL-3.0. This creates a license incompatibility:

- If DocMeld ships with pymupdf4llm as a dependency, DocMeld may need to be relicensed to AGPL-3.0
- PyMuPDF itself recently moved to AGPL-3.0 (since version 1.24.0)
- This affects your goal of being an MIT-licensed open-source project

**Mitigation options:**
1. Use PyMuPDF < 1.24.0 (last Apache-2.0 version) — but you lose updates
2. Switch to pypdfium2 (Apache-2.0) for basic text extraction
3. Use Docling (MIT) as the parsing backend
4. Make pymupdf4llm an optional dependency behind an extras flag
5. Consult a lawyer about AGPL implications for your use case

### Recommendations: Parsing Engine

**Recommendation 1 (Immediate): Keep pymupdf4llm for MVP, but add abstraction layer**

Your current approach works for the MVP target (digital-native PDFs). But wrap it behind a `ParserBackend` interface so you can swap engines later:

```python
class ParserBackend(Protocol):
    def extract_page(self, doc: Any, page_num: int) -> str: ...

class PyMuPDF4LLMBackend:
    def extract_page(self, doc, page_num):
        return pymupdf4llm.to_markdown(doc, pages=[page_num])

class DoclingBackend:
    def extract_page(self, doc, page_num):
        # Future: use Docling's structured output
        ...
```

**Recommendation 2 (Short-term): Investigate PyMuPDF-Layout**

Artifex (PyMuPDF's company) released PyMuPDF-Layout in late 2025, which adds layout detection to PyMuPDF without requiring ML models. It claims 10x faster than Docling with competitive accuracy on DocLayNet benchmarks. Since you're already using PyMuPDF, this could be a drop-in upgrade. However, it's still AGPL-3.0.

**Recommendation 3 (Medium-term): Add Docling as alternative backend**

Docling is MIT-licensed, has 28k stars, and produces the richest structured output of any tool. Its `DoclingDocument` format is the gold standard for element schemas (more on this in Part 2). Adding it as an optional backend (`pip install docmeld[docling]`) would give users a higher-accuracy option while keeping the base install lightweight.

**Recommendation 4 (Address license): Consider pypdfium2 for MIT-clean base**

If MIT purity matters, pypdfium2 (Apache-2.0) scored 80.6% on PdfBench — surprisingly competitive. It's a pure text extractor without layout detection, but for digital-native PDFs it may be sufficient. You'd need to build your own heading detection (font size analysis) and table detection on top.

---

## Part 2: Element Type Schema Evaluation

### Current Schema

```json
{"type": "title", "level": 0, "content": "...", "page_no": 1}
{"type": "text", "content": "...", "page_no": 1}
{"type": "table", "content": "| ... |", "summary": "...", "page_no": 2}
{"type": "image", "image_name": "...", "image": "base64...", "page_no": 3}
```

Four types: `title`, `text`, `table`, `image`. Flat list ordered by reading position.

### Industry Comparison

Let me compare your schema against the three most mature element schemas in the ecosystem:

**Unstructured.io** (14k stars, Apache-2.0) defines 17+ element types:
- `Title`, `NarrativeText`, `ListItem`, `Table`, `Image`
- `Header`, `Footer`, `PageBreak`, `FigureCaption`
- `Address`, `EmailAddress`, `Formula`, `CodeSnippet`
- `PageNumber`, `UncategorizedText`
- Each element has: `element_id`, `type`, `text`, `metadata` (with `page_number`, `coordinates`, `parent_id`, `languages`, `filename`, etc.)

**Docling** (28k stars, MIT) defines a `DoclingDocument` with:
- `section_header` (with level), `text`, `table`, `picture`
- `list_item` (with nesting level and enumeration type)
- `caption`, `footnote`, `formula`, `code`
- `page_header`, `page_footer`, `page_number`
- Rich metadata: bounding boxes, confidence scores, parent-child relationships, provenance tracking
- Tables stored as structured `TableData` objects (not markdown strings) with row/column spans

**MinerU** (55k stars, AGPL-3.0) defines content blocks:
- `text`, `title`, `table`, `image`
- `interline_equation`, `inline_equation`
- `list` (with items)
- Each block has: `type`, `bbox`, `page_idx`, `lines` (with spans containing font info)
- Tables stored as both HTML and LaTeX

### What Your Schema Gets Right

1. **Simplicity** — Four types is easy to understand, implement, and consume. For an MVP targeting digital-native PDFs, this covers 80-90% of content.

2. **Page attribution** — `page_no` on every element is essential for citation and traceability. Many tools miss this.

3. **Reading order** — Flat list preserving document order is the right default. Agents process sequentially.

4. **Table summaries** — The `summary` field on tables is unique to DocMeld and genuinely useful for agents deciding relevance without parsing the full table.

### What's Missing (Ranked by Impact)

**High Impact — Should add in v0.2:**

1. **`list_item` type** — Lists are extremely common in documents (bullet points, numbered lists, nested lists). Currently they get lumped into `text`, losing structure. Every major schema (Unstructured, Docling, MinerU) has a dedicated list type. This is the single biggest gap.

2. **`element_id` field** — A unique identifier per element (e.g., `"e_001"`) enables cross-referencing, parent-child relationships, and targeted updates. Without it, elements are only addressable by position, which is fragile.

3. **`bbox` (bounding box) on all elements** — Currently only images have `bbox`. Adding coordinates to all elements enables spatial reasoning, layout analysis, and visual grounding. Docling and MinerU include this on every element.

4. **Structured table data** — Storing tables as markdown strings (`| A | B |`) loses cell-level structure. Merged cells, multi-row headers, and numeric data are hard to recover from markdown. Consider storing tables as both markdown (for display) and structured data (for programmatic access):

```json
{
  "type": "table",
  "content": "| A | B |\n|---|---|\n| 1 | 2 |",
  "summary": "Items: A, B",
  "table_data": {
    "headers": ["A", "B"],
    "rows": [["1", "2"]],
    "num_rows": 1,
    "num_cols": 2
  },
  "page_no": 2
}
```

**Medium Impact — Consider for v0.3:**

5. **`header` / `footer` types** — Page headers and footers (company name, page numbers, disclaimers) are noise for agents. Separating them from `text` lets consumers filter them out. Especially important for financial documents where headers repeat on every page.

6. **`caption` type** — Figure captions and table captions are semantically distinct from body text. They describe adjacent elements. Docling and Unstructured both separate these.

7. **`formula` / `equation` type** — For scientific papers and technical documents, equations are a distinct content type. MinerU distinguishes inline vs. block equations.

8. **Confidence score** — A `confidence` field (0.0-1.0) on each element indicating extraction quality. Useful for downstream systems to decide whether to trust the extraction or flag for human review.

**Lower Impact — Future consideration:**

9. **Parent-child relationships** — A `parent_id` field linking elements to their containing section. Enables tree-based document navigation. Docling does this well.

10. **`code` type** — For technical documents containing code snippets. Currently these would be `text` elements, losing syntax highlighting and formatting.

### Is a Flat Element List the Right Structure?

**Yes, for your use case.** Here's why:

The flat list is the right choice for a pipeline that feeds into page-based JSONL (silver stage). Your silver processor groups elements by `page_no` and renders them sequentially — a flat list is the natural input for this. Tree structures (like Docling's `DoclingDocument`) are more powerful but harder to serialize, harder to stream, and harder for agents to consume.

However, I'd recommend one structural enhancement: **add an optional `parent_id` field** that references another element's `element_id`. This keeps the list flat (easy to process) while enabling tree reconstruction when needed:

```json
[
  {"element_id": "e_001", "type": "title", "level": 0, "content": "Report", "page_no": 1},
  {"element_id": "e_002", "type": "text", "content": "Intro...", "page_no": 1, "parent_id": "e_001"},
  {"element_id": "e_003", "type": "title", "level": 1, "content": "Section A", "page_no": 1, "parent_id": "e_001"},
  {"element_id": "e_004", "type": "list_item", "content": "First point", "page_no": 1, "parent_id": "e_003", "list_level": 0}
]
```

This is the "flat list with optional hierarchy" pattern — used by Unstructured.io and it works well.

---

## Summary of Recommendations

### Parsing Engine (Priority Order)

| # | Action | Effort | Impact | Timeline |
|---|--------|--------|--------|----------|
| 1 | Add `ParserBackend` abstraction layer | Low | High | v0.1.1 |
| 2 | Resolve AGPL license concern (pymupdf4llm + PyMuPDF) | Low | Critical | v0.1.1 |
| 3 | Evaluate PyMuPDF-Layout as drop-in upgrade | Medium | Medium | v0.2.0 |
| 4 | Add Docling as optional backend (`docmeld[docling]`) | Medium | High | v0.2.0 |
| 5 | Consider pypdfium2 for MIT-clean base extraction | Medium | Medium | v0.2.0 |

### Element Schema (Priority Order)

| # | Action | Effort | Impact | Timeline |
|---|--------|--------|--------|----------|
| 1 | Add `list_item` element type | Low | High | v0.2.0 |
| 2 | Add `element_id` to all elements | Low | High | v0.2.0 |
| 3 | Add `bbox` to all elements (not just images) | Medium | Medium | v0.2.0 |
| 4 | Add structured `table_data` alongside markdown content | Medium | High | v0.2.0 |
| 5 | Add `header`/`footer` element types | Low | Medium | v0.3.0 |
| 6 | Add `caption` element type | Low | Medium | v0.3.0 |
| 7 | Add optional `parent_id` for hierarchy | Low | Medium | v0.3.0 |
| 8 | Add `confidence` score field | Low | Medium | v0.3.0 |

### Proposed v0.2.0 Element Schema

```json
[
  {
    "element_id": "e_001",
    "type": "title",
    "level": 0,
    "content": "Executive Summary",
    "page_no": 1,
    "bbox": [72, 72, 540, 92]
  },
  {
    "element_id": "e_002",
    "type": "text",
    "content": "The company reported strong results...",
    "page_no": 1,
    "bbox": [72, 100, 540, 200],
    "parent_id": "e_001"
  },
  {
    "element_id": "e_003",
    "type": "list_item",
    "content": "Revenue grew 25% YoY",
    "page_no": 1,
    "list_level": 0,
    "bbox": [90, 210, 540, 225],
    "parent_id": "e_001"
  },
  {
    "element_id": "e_004",
    "type": "table",
    "content": "| Metric | Q1 | Q2 |\n|--------|----|----|...",
    "summary": "Items: Revenue, EBITDA, Net Income",
    "table_data": {
      "headers": ["Metric", "Q1", "Q2"],
      "rows": [["Revenue", "$100M", "$120M"], ["EBITDA", "$30M", "$35M"]],
      "num_rows": 2,
      "num_cols": 3
    },
    "page_no": 2,
    "bbox": [72, 100, 540, 300]
  },
  {
    "element_id": "e_005",
    "type": "image",
    "image_name": "page003_chart_001.png",
    "content": "Revenue growth chart",
    "image": "base64...",
    "image_id": "page003_chart_001",
    "page_no": 3,
    "bbox": [72, 100, 540, 400]
  }
]
```

This schema is backward-compatible (new fields are additive), aligns with industry standards, and keeps the flat-list simplicity that makes DocMeld easy to use.

---

## Bottom Line

**Parsing engine**: pymupdf4llm is adequate for MVP but has a license problem and accuracy ceiling. Add an abstraction layer now, resolve the AGPL concern, and plan for Docling integration in v0.2.

**Element schema**: Your four types cover the basics well. The biggest wins are adding `list_item`, `element_id`, and structured `table_data`. The flat list structure is correct — don't switch to a tree. Just add optional `parent_id` for hierarchy when needed.

Sources:
- [Applied-AI PdfBench](https://www.applied-ai.com/open-source/pdfbench/) — 800+ document benchmark
- [OmniDocBench (CVPR 2025)](https://github.com/opendatalab/OmniDocBench) — Comprehensive parsing benchmark
- [MinerU GitHub](https://github.com/opendatalab/MinerU) — 55k stars, AGPL-3.0
- [Docling GitHub](https://github.com/docling-project/docling) — 28k stars, MIT
- [Marker GitHub](https://github.com/VikParuchuri/marker) — 22k stars, GPL-3.0
- [Unstructured Docs](https://docs.unstructured.io/open-source/concepts/document-elements) — Element type reference
- [PyMuPDF-Layout Blog](https://artifex.com/blog/pymupdf-layout-10-faster-pdf-parsing-without-gpus) — 10x faster claims
