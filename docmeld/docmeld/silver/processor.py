"""Silver stage processor - bronze JSON to page-by-page JSONL."""
from __future__ import annotations

import json
import logging
import uuid as uuid_mod
from pathlib import Path

from docmeld.silver.markdown_renderer import render_page
from docmeld.silver.page_aggregator import group_by_page
from docmeld.silver.page_models import SilverResult
from docmeld.silver.title_tracker import TitleTracker

logger = logging.getLogger("docmeld")


class SilverProcessor:
    """Orchestrates silver-level processing: JSON elements to page JSONL."""

    def process(self, bronze_json_path: str) -> SilverResult:
        """Convert a bronze JSON file into a silver JSONL file.

        Each line in the JSONL represents one page with metadata
        and markdown-formatted content including title hierarchy.

        Args:
            bronze_json_path: Path to the bronze JSON file.

        Returns:
            SilverResult with output path and page count.
        """
        json_path = Path(bronze_json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"Bronze JSON not found: {bronze_json_path}")

        # Output JSONL goes in the same directory
        jsonl_path = json_path.with_suffix(".jsonl")

        # Idempotency check
        if jsonl_path.exists():
            with open(jsonl_path) as f:
                page_count = sum(1 for line in f if line.strip())
            return SilverResult(
                output_path=str(jsonl_path),
                page_count=page_count,
                skipped=True,
            )

        # Load bronze elements
        with open(json_path, encoding="utf-8") as f:
            elements = json.load(f)

        # Group by page
        pages = group_by_page(elements)
        sorted_page_nos = sorted(pages.keys())

        # Source filename from JSON path
        source = json_path.stem + ".pdf"

        # Process pages
        title_tracker = TitleTracker()
        table_counter = 0

        with open(jsonl_path, "w", encoding="utf-8") as out:
            for page_no in sorted_page_nos:
                page_elements = pages[page_no]

                # Render page content
                page_content, table_counter = render_page(
                    page_elements, title_tracker, table_counter
                )

                # Build metadata
                metadata = {
                    "uuid": str(uuid_mod.uuid4()),
                    "source": source,
                    "page_no": f"page{page_no}",
                    "session_title": title_tracker.get_session_title(),
                }

                page_obj = {
                    "metadata": metadata,
                    "page_content": page_content,
                }

                out.write(json.dumps(page_obj, ensure_ascii=False) + "\n")

        logger.info(f"Silver: {json_path.name} → {len(sorted_page_nos)} pages")

        return SilverResult(
            output_path=str(jsonl_path),
            page_count=len(sorted_page_nos),
            skipped=False,
        )
