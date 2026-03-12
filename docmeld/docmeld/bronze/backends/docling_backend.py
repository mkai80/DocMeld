"""Docling backend for PDF element extraction."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List


class DoclingBackend:
    """Extract elements using Docling's DocumentConverter."""

    def extract_elements(self, pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """Extract all elements from a PDF file using Docling.

        Maps Docling document items to DocMeld element format.
        """
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as e:
            raise ImportError(
                "Docling is not installed. Install with: pip install docmeld[docling]"
            ) from e

        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        doc = result.document

        elements: List[Dict[str, Any]] = []

        for item, _level in doc.iterate_items():
            item_type = type(item).__name__
            page_no = self._get_page_no(item)

            if item_type == "SectionHeaderItem":
                level = getattr(item, "level", 1)
                # Docling levels are 1-based, DocMeld uses 0-based
                elements.append({
                    "type": "title",
                    "level": max(0, level - 1),
                    "content": item.text,
                    "page_no": page_no,
                })

            elif item_type == "TextItem":
                if item.text.strip():
                    elements.append({
                        "type": "text",
                        "content": item.text.strip(),
                        "page_no": page_no,
                    })

            elif item_type == "ListItem":
                if item.text.strip():
                    elements.append({
                        "type": "text",
                        "content": f"- {item.text.strip()}",
                        "page_no": page_no,
                    })

            elif item_type == "TableItem":
                md_content = self._table_to_markdown(item)
                table_data = self._table_to_structured(item)
                elements.append({
                    "type": "table",
                    "summary": "",
                    "content": md_content,
                    "page_no": page_no,
                    "table_data": table_data,
                })

            elif item_type == "PictureItem":
                image_data = self._extract_picture(item, output_dir, page_no)
                if image_data:
                    elements.append(image_data)

        return elements

    @staticmethod
    def _get_page_no(item: Any) -> int:
        """Extract page number from a Docling item (1-indexed)."""
        prov = getattr(item, "prov", None)
        if prov and len(prov) > 0:
            page = getattr(prov[0], "page_no", None) or getattr(prov[0], "page", None)
            if page is not None:
                return int(page)
        return 1

    @staticmethod
    def _table_to_markdown(item: Any) -> str:
        """Convert a Docling TableItem to markdown string."""
        export_fn = getattr(item, "export_to_markdown", None)
        if export_fn:
            return export_fn()

        # Fallback: build from grid data
        data = getattr(item, "data", None)
        if not data:
            return getattr(item, "text", "") or ""

        grid = data.grid
        if not grid:
            return ""

        lines = []
        for row_idx, row in enumerate(grid):
            cells = [cell.text for cell in row]
            lines.append("| " + " | ".join(cells) + " |")
            if row_idx == 0:
                lines.append("| " + " | ".join("---" for _ in cells) + " |")

        return "\n".join(lines)

    @staticmethod
    def _table_to_structured(item: Any) -> Dict[str, Any]:
        """Extract structured table data from a Docling TableItem."""
        data = getattr(item, "data", None)
        if not data:
            return {"headers": [], "rows": [], "num_rows": 0, "num_cols": 0}

        grid = data.grid
        if not grid:
            return {"headers": [], "rows": [], "num_rows": 0, "num_cols": 0}

        headers = [cell.text for cell in grid[0]]
        rows = [[cell.text for cell in row] for row in grid[1:]]

        return {
            "headers": headers,
            "rows": rows,
            "num_rows": len(rows),
            "num_cols": len(headers),
        }

    @staticmethod
    def _extract_picture(
        item: Any, output_dir: str, page_no: int
    ) -> Dict[str, Any] | None:
        """Extract image data from a Docling PictureItem."""
        image = getattr(item, "image", None)
        if not image:
            return None

        pil_image = getattr(image, "pil_image", None)
        if not pil_image:
            return None

        import io

        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        image_id = f"page{page_no:03d}_docling_{id(item)}"
        return {
            "type": "image",
            "image_name": f"{image_id}.png",
            "content": "",
            "image": b64,
            "page_no": page_no,
            "image_id": image_id,
            "bbox": (0.0, 0.0, 0.0, 0.0),
        }
