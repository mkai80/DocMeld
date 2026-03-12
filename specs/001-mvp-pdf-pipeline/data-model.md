# Data Model: MVP PDF Data Pipeline

**Feature Branch**: `001-mvp-pdf-pipeline`
**Date**: 2026-03-12

## Entity Definitions

### 1. BronzeElement (Base Class)

**Purpose**: Represents a single structural component extracted from a PDF page.

**Base Fields**:
- `type`: str - Element type discriminator ("text", "table", "title", "image")
- `page_no`: int - Physical page number (1-indexed)

**Validation Rules**:
- `page_no` must be >= 1
- `type` must be one of the four supported types

**Relationships**: None (flat list structure)

**Lifecycle**: Created during bronze stage, immutable thereafter

---

### 2. TitleElement (extends BronzeElement)

**Purpose**: Represents a heading/title with hierarchical level.

**Fields**:
- `type`: Literal["title"]
- `level`: int - Hierarchy level (0-based: 0=H1, 1=H2, etc.)
- `content`: str - Title text
- `page_no`: int

**Validation Rules**:
- `level` must be >= 0 and <= 5 (H1 through H6)
- `content` must not be empty

**Example**:
```json
{
  "type": "title",
  "level": 0,
  "content": "Executive Summary",
  "page_no": 1
}
```

---

### 3. TextElement (extends BronzeElement)

**Purpose**: Represents a paragraph or text block.

**Fields**:
- `type`: Literal["text"]
- `content`: str - Text content (may include newlines)
- `page_no`: int

**Validation Rules**:
- `content` must not be empty (empty text blocks are discarded)

**Example**:
```json
{
  "type": "text",
  "content": "The company reported strong quarterly results...",
  "page_no": 1
}
```

---

### 4. TableElement (extends BronzeElement)

**Purpose**: Represents a table with markdown formatting.

**Fields**:
- `type`: Literal["table"]
- `content`: str - Markdown-formatted table
- `summary`: str - First column items summary
- `page_no`: int

**Validation Rules**:
- `content` must contain markdown table syntax (pipes and headers)
- `summary` format: "Items: {item1}, {item2}, ... (+N more)" or empty for small tables

**Example**:
```json
{
  "type": "table",
  "summary": "Items: Revenue, Gross Margin, EBITDA",
  "content": "| Metric | Q1 | Q2 |\n|--------|----|----|...",
  "page_no": 2
}
```

---

### 5. ImageElement (extends BronzeElement)

**Purpose**: Represents an image or chart with base64 encoding.

**Fields**:
- `type`: Literal["image"]
- `image_name`: str - Original filename (e.g., "page001_image_001.png")
- `content`: str - Optional description/caption
- `image`: str - Base64-encoded image data
- `image_id`: str - Unique identifier (filename stem)
- `bbox`: Tuple[float, float, float, float] - Bounding box (x0, y0, x1, y1)
- `page_no`: int

**Validation Rules**:
- `image` must be valid base64 string
- `bbox` coordinates must be non-negative

**Example**:
```json
{
  "type": "image",
  "image_name": "page003_image_001.png",
  "content": "Revenue growth chart",
  "image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "image_id": "page003_image_001",
  "bbox": [0, 0, 0, 0],
  "page_no": 3
}
```

---

### 6. SilverPage

**Purpose**: Represents a single page with metadata and markdown-formatted content.

**Fields**:
- `metadata`: dict
  - `uuid`: str - Unique page identifier (UUID4)
  - `source`: str - Source filename (e.g., "research_report_a3f5c2.pdf")
  - `page_no`: str - Page identifier (e.g., "page1")
  - `session_title`: str - Markdown title hierarchy
- `page_content`: str - Markdown-formatted page content

**Validation Rules**:
- `uuid` must be valid UUID4 format
- `page_no` format: "page{N}" where N >= 1
- `session_title` must contain valid markdown headers

**Relationships**: Aggregates multiple BronzeElements from same page

**Lifecycle**: Created during silver stage from bronze JSON

**Example**:
```json
{
  "metadata": {
    "uuid": "52e2bd3a-2d57-4a18-94a6-91e9314c7a67",
    "source": "research_report_a3f5c2.pdf",
    "page_no": "page1",
    "session_title": "# Executive Summary\n"
  },
  "page_content": "# Executive Summary\n\nThe company reported...\n\n[[Table1]]\n| Metric | Value |\n..."
}
```

---

### 7. GoldPage (extends SilverPage)

**Purpose**: Enriched silver page with AI-generated semantic metadata.

**Additional Fields**:
- `metadata.description`: str - One-line page summary
- `metadata.keywords`: List[str] - Extracted keywords
- `metadata.gold_processing_failed`: bool (optional) - True if enrichment failed

**Validation Rules**:
- `description` must be non-empty string (unless processing failed)
- `keywords` must be list of strings (may be empty)

**Relationships**: Extends SilverPage with additional metadata

**Lifecycle**: Created during gold stage from silver JSONL

**Example**:
```json
{
  "metadata": {
    "uuid": "52e2bd3a-2d57-4a18-94a6-91e9314c7a67",
    "source": "research_report_a3f5c2.pdf",
    "page_no": "page1",
    "session_title": "# Executive Summary\n",
    "description": "Company reports strong Q2 results with revenue growth and margin expansion",
    "keywords": ["revenue", "EBITDA", "quarterly results", "growth", "margins"]
  },
  "page_content": "# Executive Summary\n\nThe company reported..."
}
```

---

### 8. ProcessingResult

**Purpose**: Summary statistics for pipeline execution.

**Fields**:
- `total_files`: int - Total PDFs processed
- `successful`: int - Successfully processed files
- `failed`: int - Failed files
- `failures`: List[dict] - Failure details
  - `filename`: str
  - `error`: str
- `processing_time_seconds`: float
- `output_directory`: str
- `log_file`: str

**Validation Rules**:
- `successful + failed == total_files`
- `processing_time_seconds` must be >= 0

**Example**:
```json
{
  "total_files": 10,
  "successful": 9,
  "failed": 1,
  "failures": [
    {"filename": "corrupted.pdf", "error": "PyMuPDF: file unreadable"}
  ],
  "processing_time_seconds": 272.5,
  "output_directory": "/path/to/documents/",
  "log_file": "docmeld_20260312_143022.log"
}
```

---

## State Transitions

### Bronze Stage
```
PDF File → [Extract] → List[BronzeElement] → [Serialize] → {filename_hash6}.json
```

**State**: Immutable once written

### Silver Stage
```
{filename_hash6}.json → [Load] → List[BronzeElement] → [Group by page_no] → List[SilverPage] → [Serialize] → {filename_hash6}.jsonl
```

**State**: Immutable once written

### Gold Stage
```
{filename_hash6}.jsonl → [Load] → List[SilverPage] → [Enrich with AI] → List[GoldPage] → [Serialize] → {filename_hash6}_gold.jsonl
```

**State**: Immutable once written

---

## Data Volume Assumptions

**Bronze JSON**:
- Typical size: 100KB - 5MB per document
- Elements per page: 5-20 (average 10)
- 50-page document: ~500 elements, ~2MB JSON

**Silver JSONL**:
- Typical size: 150KB - 7MB per document
- One line per page
- 50-page document: 50 lines, ~3MB JSONL

**Gold JSONL**:
- Typical size: 160KB - 7.5MB per document
- Adds ~200 bytes per page (description + keywords)
- 50-page document: 50 lines, ~3.2MB JSONL

**Memory Constraints**:
- Bronze stage: Load entire PDF into memory (PyMuPDF requirement)
- Silver stage: Load entire bronze JSON into memory
- Gold stage: Process pages sequentially (streaming JSONL)
- Target: <500MB for 100-page PDFs (per constitution)

---

## Pydantic Models

```python
from pydantic import BaseModel, Field, validator
from typing import Literal, List, Tuple, Optional
from uuid import UUID

class BronzeElement(BaseModel):
    type: str
    page_no: int = Field(ge=1)

class TitleElement(BronzeElement):
    type: Literal["title"]
    level: int = Field(ge=0, le=5)
    content: str = Field(min_length=1)

class TextElement(BronzeElement):
    type: Literal["text"]
    content: str = Field(min_length=1)

class TableElement(BronzeElement):
    type: Literal["table"]
    content: str = Field(min_length=1)
    summary: str

class ImageElement(BronzeElement):
    type: Literal["image"]
    image_name: str
    content: str
    image: str  # base64
    image_id: str
    bbox: Tuple[float, float, float, float]

class SilverMetadata(BaseModel):
    uuid: UUID
    source: str
    page_no: str
    session_title: str

class SilverPage(BaseModel):
    metadata: SilverMetadata
    page_content: str

class GoldMetadata(SilverMetadata):
    description: str
    keywords: List[str]
    gold_processing_failed: Optional[bool] = None

class GoldPage(BaseModel):
    metadata: GoldMetadata
    page_content: str

class ProcessingFailure(BaseModel):
    filename: str
    error: str

class ProcessingResult(BaseModel):
    total_files: int
    successful: int
    failed: int
    failures: List[ProcessingFailure]
    processing_time_seconds: float = Field(ge=0)
    output_directory: str
    log_file: str
```
