"""Unit tests for markdown renderer."""
from __future__ import annotations


class TestRenderPage:
    def test_title_rendering(self) -> None:
        from docmeld.silver.markdown_renderer import render_page
        from docmeld.silver.title_tracker import TitleTracker

        elements = [{"type": "title", "level": 0, "content": "Main", "page_no": 1}]
        tracker = TitleTracker()
        content, counter = render_page(elements, tracker, table_counter=0)
        assert "# Main" in content

    def test_title_level_mapping(self) -> None:
        from docmeld.silver.markdown_renderer import render_page
        from docmeld.silver.title_tracker import TitleTracker

        elements = [
            {"type": "title", "level": 0, "content": "H1", "page_no": 1},
            {"type": "title", "level": 1, "content": "H2", "page_no": 1},
            {"type": "title", "level": 2, "content": "H3", "page_no": 1},
        ]
        tracker = TitleTracker()
        content, _ = render_page(elements, tracker, table_counter=0)
        assert "# H1" in content
        assert "## H2" in content
        assert "### H3" in content

    def test_text_rendering(self) -> None:
        from docmeld.silver.markdown_renderer import render_page
        from docmeld.silver.title_tracker import TitleTracker

        elements = [{"type": "text", "content": "Hello world.", "page_no": 1}]
        tracker = TitleTracker()
        content, _ = render_page(elements, tracker, table_counter=0)
        assert "Hello world." in content

    def test_table_markers_with_global_numbering(self) -> None:
        from docmeld.silver.markdown_renderer import render_page
        from docmeld.silver.title_tracker import TitleTracker

        table_content = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
        elements = [
            {"type": "table", "content": table_content, "summary": "Items: A", "page_no": 1}
        ]
        tracker = TitleTracker()
        content, counter = render_page(elements, tracker, table_counter=0)
        assert "[[Table1]]" in content
        assert "[/Table1]" in content
        assert counter == 1

    def test_global_numbering_across_pages(self) -> None:
        from docmeld.silver.markdown_renderer import render_page
        from docmeld.silver.title_tracker import TitleTracker

        table = "| X |\n|---|\n| 1 |\n| 2 |"
        elements1 = [{"type": "table", "content": table, "summary": "", "page_no": 1}]
        elements2 = [{"type": "table", "content": table, "summary": "", "page_no": 2}]

        tracker = TitleTracker()
        _, counter = render_page(elements1, tracker, table_counter=0)
        assert counter == 1

        content2, counter2 = render_page(elements2, tracker, table_counter=counter)
        assert "[[Table2]]" in content2
        assert counter2 == 2

    def test_small_table_no_number(self) -> None:
        from docmeld.silver.markdown_renderer import render_page
        from docmeld.silver.title_tracker import TitleTracker

        # Table with only 1 data row (header + separator + 1 row)
        small_table = "| A |\n|---|\n| 1 |"
        elements = [
            {"type": "table", "content": small_table, "summary": "", "page_no": 1}
        ]
        tracker = TitleTracker()
        content, counter = render_page(elements, tracker, table_counter=0)
        assert "[[Table]]" in content
        assert counter == 0  # Small tables don't increment counter
