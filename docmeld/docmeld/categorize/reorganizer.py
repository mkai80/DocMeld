"""Reorganize files into category subdirectories."""
from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger("docmeld")


def _find_source_pdf(output_dir: Path) -> str | None:
    """Read the silver JSONL in output_dir to find the original PDF filename."""
    for jsonl_file in output_dir.glob("*.jsonl"):
        if jsonl_file.name.endswith("_gold.jsonl"):
            continue
        try:
            with open(jsonl_file, encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line:
                    data = json.loads(first_line)
                    source = data.get("metadata", {}).get("source", "")
                    if source:
                        return source
        except Exception:
            continue
    return None


def reorganize_by_category(folder_path: str) -> None:
    """Move PDFs and their output folders into category-named subdirectories.

    Reads categories.json from the folder, creates subdirectories for each
    category, and moves both the output directory and the original PDF into them.

    Args:
        folder_path: Path to the folder containing categories.json.

    Raises:
        FileNotFoundError: If categories.json does not exist.
    """
    folder = Path(folder_path)
    index_path = folder / "categories.json"

    if not index_path.exists():
        raise FileNotFoundError(f"categories.json not found in {folder_path}")

    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    moves: List[Dict[str, str]] = []

    for paper_entry in index.get("papers", []):
        filename = paper_entry["filename"]
        category = paper_entry["category"]
        safe_category = _sanitize_category_name(category)

        # The filename is like paper1_abc123.jsonl (silver) or paper1_abc123_gold.jsonl (legacy)
        # The output dir is paper1_abc123
        stem = filename.replace("_gold.jsonl", "").replace(".jsonl", "")
        output_dir = folder / stem

        if not output_dir.exists():
            # Maybe already reorganized — check inside category dirs
            candidate = folder / safe_category / stem
            if candidate.exists():
                continue  # Already moved
            logger.warning(f"Output dir not found: {output_dir}")
            continue

        # Create category directory
        cat_dir = folder / safe_category
        cat_dir.mkdir(exist_ok=True)

        # Move output directory (bronze folder)
        dest = cat_dir / stem
        if not dest.exists():
            # Find and move the original PDF first
            source_pdf_name = _find_source_pdf(output_dir)
            if source_pdf_name:
                pdf_path = folder / source_pdf_name
                if pdf_path.exists():
                    pdf_dest = cat_dir / source_pdf_name
                    if not pdf_dest.exists():
                        shutil.move(str(pdf_path), str(pdf_dest))
                        moves.append({"source": str(pdf_path), "dest": str(pdf_dest), "type": "pdf"})
                        logger.info(f"Moved {source_pdf_name} → {safe_category}/")

            shutil.move(str(output_dir), str(dest))
            moves.append({"source": str(output_dir), "dest": str(dest), "type": "output_dir"})
            logger.info(f"Moved {output_dir.name} → {safe_category}/")

    # Write manifest
    manifest = {
        "reorganized_at": datetime.now(timezone.utc).isoformat(),
        "moves": moves,
    }
    manifest_path = folder / "_reorganized.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(f"Reorganized {len(moves)} items into category directories")


def _sanitize_category_name(name: str) -> str:
    """Sanitize a category name for use as a directory name.

    Replaces unsafe characters with underscores, strips whitespace.
    """
    name = name.strip()
    # Replace characters that are unsafe in filenames
    name = re.sub(r'[/\\:*?"<>|&;]', "_", name)
    # Collapse multiple underscores/spaces
    name = re.sub(r"[_ ]+", " ", name).strip()
    # Truncate to reasonable length
    if len(name) > 100:
        name = name[:100].rstrip()
    return name
