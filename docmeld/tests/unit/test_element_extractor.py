"""Unit tests for element extractor."""
from __future__ import annotations

from pathlib import Path
from typing import List

import pytest


class TestParseMarkdownToElements:
    def test_title_detection(self) -> None:
        from docmeld.bronze.element_extractor import parse_markdown_to_elements

        md = "# Main Title\n\nSome text here."
        elements = parse_markdown_to_elements(md, page_no=1)
        titles = [e for e in elements if e["type"] == "title"]
        assert len(titles) == 1
        assert titles[0]["content"] == "Main Title"
        assert titles[0]["level"] == 0  # H1 = level 0

    def test_title_level_counting(self) -> None:
        from docmeld.bronze.element_extractor import parse_markdown_to_elements

        md = "## Sub Title\n\n### Sub Sub"
        elements = parse_markdown_to_elements(md, page_no=1)
        titles = [e for e in elements if e["type"] == "title"]
        assert titles[0]["level"] == 1  # H2 = level 1
        assert titles[1]["level"] == 2  # H3 = level 2

    def test_table_detection(self) -> None:
        from docmeld.bronze.element_extractor import parse_markdown_to_elements

        md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\nAfter table."
        elements = parse_markdown_to_elements(md, page_no=1)
        tables = [e for e in elements if e["type"] == "table"]
        assert len(tables) == 1
        assert "| A | B |" in tables[0]["content"]

    def test_text_extraction(self) -> None:
        from docmeld.bronze.element_extractor import parse_markdown_to_elements

        md = "Just a paragraph of text.\nWith two lines."
        elements = parse_markdown_to_elements(md, page_no=1)
        texts = [e for e in elements if e["type"] == "text"]
        assert len(texts) >= 1
        assert "Just a paragraph" in texts[0]["content"]

    def test_element_ordering(self) -> None:
        from docmeld.bronze.element_extractor import parse_markdown_to_elements

        md = "# Title\n\nParagraph text.\n\n| A |\n|---|\n| 1 |\n\nMore text."
        elements = parse_markdown_to_elements(md, page_no=1)
        types = [e["type"] for e in elements]
        assert types[0] == "title"
        assert "text" in types
        assert "table" in types

    def test_page_no_assigned(self) -> None:
        from docmeld.bronze.element_extractor import parse_markdown_to_elements

        md = "# Title\n\nText."
        elements = parse_markdown_to_elements(md, page_no=5)
        for elem in elements:
            assert elem["page_no"] == 5

    def test_empty_content_skipped(self) -> None:
        from docmeld.bronze.element_extractor import parse_markdown_to_elements

        md = "\n\n\n"
        elements = parse_markdown_to_elements(md, page_no=1)
        assert len(elements) == 0


class TestTableSummary:
    def test_generates_summary_from_first_column(self) -> None:
        from docmeld.bronze.element_extractor import generate_table_summary

        table_md = "| Metric | Value |\n|--------|-------|\n| Revenue | $100 |\n| EBITDA | $50 |"
        summary = generate_table_summary(table_md)
        assert "Revenue" in summary
        assert "EBITDA" in summary

    def test_empty_table_returns_empty(self) -> None:
        from docmeld.bronze.element_extractor import generate_table_summary

        summary = generate_table_summary("")
        assert summary == ""

    def test_items_prefix(self) -> None:
        from docmeld.bronze.element_extractor import generate_table_summary

        table_md = "| Name | Val |\n|------|-----|\n| A | 1 |\n| B | 2 |"
        summary = generate_table_summary(table_md)
        assert summary.startswith("Items: ")
