"""Unit tests for title tracker."""
from __future__ import annotations


class TestTitleTracker:
    def test_push_single_title(self) -> None:
        from docmeld.silver.title_tracker import TitleTracker

        tracker = TitleTracker()
        tracker.update(0, "Main Title")
        md = tracker.get_hierarchy_markdown()
        assert "# Main Title" in md

    def test_push_nested_titles(self) -> None:
        from docmeld.silver.title_tracker import TitleTracker

        tracker = TitleTracker()
        tracker.update(0, "H1")
        tracker.update(1, "H2")
        md = tracker.get_hierarchy_markdown()
        assert "# H1" in md
        assert "## H2" in md

    def test_same_level_replaces(self) -> None:
        from docmeld.silver.title_tracker import TitleTracker

        tracker = TitleTracker()
        tracker.update(0, "First H1")
        tracker.update(0, "Second H1")
        md = tracker.get_hierarchy_markdown()
        assert "First H1" not in md
        assert "# Second H1" in md

    def test_higher_level_pops_children(self) -> None:
        from docmeld.silver.title_tracker import TitleTracker

        tracker = TitleTracker()
        tracker.update(0, "H1")
        tracker.update(1, "H2")
        tracker.update(2, "H3")
        tracker.update(0, "New H1")
        md = tracker.get_hierarchy_markdown()
        assert "H2" not in md
        assert "H3" not in md
        assert "# New H1" in md

    def test_deep_nesting(self) -> None:
        from docmeld.silver.title_tracker import TitleTracker

        tracker = TitleTracker()
        tracker.update(0, "L0")
        tracker.update(1, "L1")
        tracker.update(2, "L2")
        tracker.update(3, "L3")
        md = tracker.get_hierarchy_markdown()
        assert "# L0" in md
        assert "## L1" in md
        assert "### L2" in md
        assert "#### L3" in md

    def test_empty_stack(self) -> None:
        from docmeld.silver.title_tracker import TitleTracker

        tracker = TitleTracker()
        assert tracker.get_hierarchy_markdown() == ""

    def test_get_session_title(self) -> None:
        from docmeld.silver.title_tracker import TitleTracker

        tracker = TitleTracker()
        tracker.update(0, "Report")
        tracker.update(1, "Section A")
        title = tracker.get_session_title()
        assert "Report" in title
        assert "Section A" in title
