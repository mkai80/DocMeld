# Quickstart: Research Papers Batch Categorize

**Feature**: 002-paper-batch-categorize

## CLI Usage

```bash
# Process all PDFs in a folder and generate categories.json
docmeld categorize /path/to/papers/

# Process and reorganize files into category subdirectories
docmeld categorize /path/to/papers/ --reorganize

# Use docling backend instead of pymupdf
docmeld categorize /path/to/papers/ --backend docling
```

## Python API Usage

```python
from docmeld import DocMeldParser

# Basic categorization
parser = DocMeldParser("/path/to/papers/")
result = parser.process_categorize()
print(f"Found {result.total_categories} categories for {result.total_papers} papers")

# With file reorganization
result = parser.process_categorize(reorganize=True)

# Access the categories
import json
with open(result.index_path) as f:
    index = json.load(f)

for cat in index["categories"]:
    print(f"{cat['name']}: {len(cat['papers'])} papers")
```

## Expected Output

After running `docmeld categorize /path/to/papers/`, the folder will contain:

```
papers/
├── paper1.pdf
├── paper1_abc123/           # bronze/silver/gold outputs
│   ├── paper1_abc123.json
│   ├── paper1_abc123.jsonl
│   └── paper1_abc123_gold.jsonl
├── paper2.pdf
├── paper2_def456/
│   └── ...
└── categories.json          # NEW — the category index
```

With `--reorganize`:

```
papers/
├── Natural Language Processing/
│   ├── paper1.pdf
│   └── paper1_abc123/
├── Computer Vision/
│   ├── paper2.pdf
│   └── paper2_def456/
└── categories.json
```

## Prerequisites

- DeepSeek API key configured in `.env.local` (required for gold stage + categorization)
- PDFs in a flat folder (no nested subdirectories)
