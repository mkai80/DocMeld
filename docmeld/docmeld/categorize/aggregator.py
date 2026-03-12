"""Aggregate gold-stage metadata across all papers in a folder."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from docmeld.categorize.models import PaperMetadata

logger = logging.getLogger("docmeld")


def aggregate_paper_metadata(folder_path: str) -> List[PaperMetadata]:
    """Scan a folder for gold JSONL files and collect per-paper metadata.

    Looks for *_gold.jsonl files in subdirectories of the given folder.
    For each file, aggregates descriptions and deduplicates keywords
    across all pages.

    Args:
        folder_path: Path to the folder containing paper output directories.

    Returns:
        List of PaperMetadata, one per paper, sorted by filename.
    """
    folder = Path(folder_path)
    results: List[PaperMetadata] = []

    gold_files = sorted(folder.rglob("*_gold.jsonl"))

    for gold_path in gold_files:
        try:
            metadata = _parse_gold_file(gold_path)
            if metadata:
                results.append(metadata)
        except Exception as e:
            logger.warning(f"Failed to parse {gold_path}: {e}")

    results.sort(key=lambda p: p.filename)
    return results


def _parse_gold_file(gold_path: Path) -> PaperMetadata | None:
    """Parse a single gold JSONL file into PaperMetadata."""
    pages: List[Dict[str, Any]] = []
    with open(gold_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pages.append(json.loads(line))

    if not pages:
        return None

    all_keywords: List[str] = []
    descriptions: List[str] = []

    for page in pages:
        meta = page.get("metadata", {})
        desc = meta.get("description", "")
        kws = meta.get("keywords", [])

        if desc:
            descriptions.append(desc)
        all_keywords.extend(kws)

    # Deduplicate keywords preserving order
    seen = set()
    unique_keywords: List[str] = []
    for kw in all_keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique_keywords.append(kw)

    # Combine descriptions into a single summary
    combined_desc = " ".join(descriptions[:5])  # First 5 page descriptions

    return PaperMetadata(
        filename=gold_path.name,
        file_path=str(gold_path.parent.parent / gold_path.name),
        output_dir=str(gold_path.parent),
        description=combined_desc,
        keywords=unique_keywords,
        page_count=len(pages),
        gold_path=str(gold_path),
    )
