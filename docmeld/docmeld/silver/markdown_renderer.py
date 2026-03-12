"""Markdown renderer for silver stage - converts elements to page content."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from docmeld.silver.title_tracker import TitleTracker


def _count_data_rows(table_content: str) -> int:
    """Count data rows in a markdown table (excluding header and separator)."""
    lines = [line.strip() for line in table_content.strip().split("\n") if line.strip()]
    data_rows = 0
    for i, line in enumerate(lines):
        if i == 0:
            continue  # header
        if all(c in "-|: " for c in line):
            continue  # separator
        data_rows += 1
    return data_rows


def render_page(
    elements: List[Dict[str, Any]],
    title_tracker: TitleTracker,
    table_counter: int,
) -> Tuple[str, int]:
    """Render a list of elements into markdown page content.

    Args:
        elements: List of element dicts for this page.
        title_tracker: TitleTracker instance (mutated with new titles).
        table_counter: Current global table counter.

    Returns:
        Tuple of (page_content_string, updated_table_counter).
    """
    parts: List[str] = []

    for elem in elements:
        elem_type = elem["type"]

        if elem_type == "title":
            level = elem["level"]
            content = elem["content"]
            title_tracker.update(level, content)
            heading = "#" * (level + 1)
            parts.append(f"{heading} {content}")

        elif elem_type == "text":
            parts.append(elem["content"])

        elif elem_type == "table":
            table_content = elem["content"]
            data_rows = _count_data_rows(table_content)

            if data_rows > 1:
                table_counter += 1
                parts.append(f"[[Table{table_counter}]]")
                parts.append(table_content)
                parts.append(f"[/Table{table_counter}]")
            else:
                parts.append("[[Table]]")
                parts.append(table_content)
                parts.append("[/Table]")

        elif elem_type == "image":
            image_name = elem.get("image_name", "image")
            parts.append(f"![{image_name}]")

    page_content = "\n\n".join(parts)
    return page_content, table_counter
