"""Unit tests for Docling backend (mocked — docling not installed)."""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


class TestDoclingBackend:
    def test_import_error_when_docling_missing(self) -> None:
        from docmeld.bronze.backends.docling_backend import DoclingBackend

        backend = DoclingBackend()
        with patch.dict("sys.modules", {"docling": None, "docling.document_converter": None}):
            with pytest.raises(ImportError, match="Docling is not installed"):
                backend.extract_elements("/fake.pdf", "/tmp/out")

    def test_extract_elements_with_mocked_docling(self) -> None:
        from docmeld.bronze.backends.docling_backend import DoclingBackend

        # Build mock Docling document with a section header and text item
        mock_header = MagicMock()
        mock_header.__class__ = type("SectionHeaderItem", (), {})
        type(mock_header).__name__ = "SectionHeaderItem"
        mock_header.text = "Introduction"
        mock_header.level = 1
        mock_header.prov = [MagicMock(page_no=1)]

        mock_text = MagicMock()
        mock_text.__class__ = type("TextItem", (), {})
        type(mock_text).__name__ = "TextItem"
        mock_text.text = "Hello world"
        mock_text.prov = [MagicMock(page_no=1)]

        mock_table = MagicMock()
        mock_table.__class__ = type("TableItem", (), {})
        type(mock_table).__name__ = "TableItem"
        mock_table.text = "table content"
        mock_table.prov = [MagicMock(page_no=2)]
        mock_table.export_to_markdown.return_value = "| A | B |\n|---|---|\n| 1 | 2 |"
        mock_table.data = None  # No grid data

        mock_list = MagicMock()
        mock_list.__class__ = type("ListItem", (), {})
        type(mock_list).__name__ = "ListItem"
        mock_list.text = "item one"
        mock_list.prov = [MagicMock(page_no=1)]

        mock_doc = MagicMock()
        mock_doc.iterate_items.return_value = [
            (mock_header, 1),
            (mock_text, 1),
            (mock_table, 1),
            (mock_list, 1),
        ]

        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_converter_cls = MagicMock()
        mock_converter_cls.return_value.convert.return_value = mock_result

        mock_module = MagicMock()
        mock_module.DocumentConverter = mock_converter_cls

        backend = DoclingBackend()
        with patch.dict("sys.modules", {"docling": MagicMock(), "docling.document_converter": mock_module}):
            elements = backend.extract_elements("/fake.pdf", "/tmp/out")

        assert len(elements) == 4

        # Section header -> title
        assert elements[0]["type"] == "title"
        assert elements[0]["content"] == "Introduction"
        assert elements[0]["level"] == 0  # docling level 1 -> docmeld level 0

        # Text item
        assert elements[1]["type"] == "text"
        assert elements[1]["content"] == "Hello world"

        # Table item
        assert elements[2]["type"] == "table"
        assert "| A | B |" in elements[2]["content"]

        # List item -> text with bullet
        assert elements[3]["type"] == "text"
        assert elements[3]["content"] == "- item one"

    def test_get_page_no_fallback(self) -> None:
        from docmeld.bronze.backends.docling_backend import DoclingBackend

        # Item with no prov attribute
        mock_item = MagicMock(spec=[])
        assert DoclingBackend._get_page_no(mock_item) == 1

    def test_get_page_no_from_prov(self) -> None:
        from docmeld.bronze.backends.docling_backend import DoclingBackend

        mock_item = MagicMock()
        mock_item.prov = [MagicMock(page_no=5)]
        assert DoclingBackend._get_page_no(mock_item) == 5

    def test_table_to_structured_no_data(self) -> None:
        from docmeld.bronze.backends.docling_backend import DoclingBackend

        mock_item = MagicMock()
        mock_item.data = None
        result = DoclingBackend._table_to_structured(mock_item)
        assert result == {"headers": [], "rows": [], "num_rows": 0, "num_cols": 0}
