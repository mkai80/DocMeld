"""Extract structured elements from PDF pages using PyMuPDF."""
from __future__ import annotations

import base64
import glob
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz
import pymupdf4llm


def extract_elements(pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:
    """Extract all elements from a PDF file.

    Opens the PDF with PyMuPDF, extracts text via pymupdf4llm per page,
    parses markdown into structured elements, and discovers images.

    Returns:
        Ordered list of element dicts with type and page_no.
    """
    doc = fitz.open(pdf_path)
    all_elements: List[Dict[str, Any]] = []

    for page_num in range(len(doc)):
        page_no = page_num + 1

        # Extract markdown from page
        try:
            md_content = pymupdf4llm.to_markdown(doc, pages=[page_num])
        except Exception:
            md_content = ""

        if md_content:
            page_elements = parse_markdown_to_elements(md_content, page_no)
            all_elements.extend(page_elements)

        # Discover pre-extracted images
        image_elements = _discover_images(output_dir, page_num)
        all_elements.extend(image_elements)

    doc.close()

    # Generate table summaries
    for elem in all_elements:
        if elem["type"] == "table":
            elem["summary"] = generate_table_summary(elem["content"])

    return all_elements


def parse_markdown_to_elements(
    md_content: str, page_no: int
) -> List[Dict[str, Any]]:
    """Parse markdown content into structured elements.

    Identifies titles (# lines), tables (| lines), and text blocks.
    """
    elements: List[Dict[str, Any]] = []
    lines = md_content.split("\n")
    text_buffer: List[str] = []
    table_buffer: List[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Empty line: flush text buffer, preserve as newline
            text_buffer.append("\n")

            # Flush table buffer on empty line
            if table_buffer:
                content = "\n".join(table_buffer).strip()
                if content:
                    elements.append(
                        {"type": "table", "summary": "", "content": content, "page_no": page_no}
                    )
                table_buffer = []
            continue

        if stripped.startswith("#"):
            # Flush text buffer
            if text_buffer:
                content = "\n".join(text_buffer).strip()
                if content:
                    elements.append({"type": "text", "content": content, "page_no": page_no})
                text_buffer = []

            # Flush table buffer
            if table_buffer:
                content = "\n".join(table_buffer).strip()
                if content:
                    elements.append(
                        {"type": "table", "summary": "", "content": content, "page_no": page_no}
                    )
                table_buffer = []

            # Count heading level
            level = 0
            for ch in stripped:
                if ch == "#":
                    level += 1
                else:
                    break

            title = stripped[level:].strip()
            if title:
                elements.append(
                    {"type": "title", "level": level - 1, "content": title, "page_no": page_no}
                )

        elif stripped.startswith("|"):
            # Flush text buffer before table
            if text_buffer:
                content = "\n".join(text_buffer).strip()
                if content:
                    elements.append({"type": "text", "content": content, "page_no": page_no})
                text_buffer = []

            table_buffer.append(stripped)

        else:
            # Flush table buffer before text
            if table_buffer:
                content = "\n".join(table_buffer).strip()
                if content:
                    elements.append(
                        {"type": "table", "summary": "", "content": content, "page_no": page_no}
                    )
                table_buffer = []

            text_buffer.append(stripped)

    # Flush remaining buffers
    if text_buffer:
        content = "\n".join(text_buffer).strip()
        if content:
            elements.append({"type": "text", "content": content, "page_no": page_no})

    if table_buffer:
        content = "\n".join(table_buffer).strip()
        if content:
            elements.append(
                {"type": "table", "summary": "", "content": content, "page_no": page_no}
            )

    return elements


def generate_table_summary(table_md: str) -> str:
    """Generate a summary from a markdown table's first column values.

    Returns: 'Items: val1, val2, ...' or empty string.
    """
    if not table_md.strip():
        return ""

    lines = [line.strip() for line in table_md.strip().split("\n") if line.strip()]
    items: List[str] = []

    for i, line in enumerate(lines):
        if i == 0:
            continue  # Skip header row
        # Skip separator lines
        if all(c in "-|: " for c in line):
            continue
        # Extract first column value
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if parts:
            items.append(parts[0])

    if not items:
        return ""

    if len(items) <= 5:
        return f"Items: {', '.join(items)}"
    return f"Items: {', '.join(items[:5])} (+{len(items) - 5} more)"


def _discover_images(
    output_dir: str, page_num: int
) -> List[Dict[str, Any]]:
    """Discover pre-extracted image files for a page."""
    elements: List[Dict[str, Any]] = []
    page_prefix = f"page{page_num + 1:03d}"
    search_pattern = str(Path(output_dir) / f"{page_prefix}_*.png")
    image_files = sorted(glob.glob(search_pattern))

    for image_path_str in image_files:
        image_path = Path(image_path_str)
        image_id = image_path.stem

        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            base64_content = base64.b64encode(image_bytes).decode("utf-8")

            # Check for markdown description file
            md_path = Path(output_dir) / f"{image_id}.md"
            md_content = ""
            if md_path.exists():
                md_content = md_path.read_text(encoding="utf-8")

            elements.append(
                {
                    "type": "image",
                    "image_name": image_path.name,
                    "content": md_content,
                    "image": base64_content,
                    "page_no": page_num + 1,
                    "image_id": image_id,
                    "bbox": (0.0, 0.0, 0.0, 0.0),
                }
            )
        except Exception:
            pass

    return elements
