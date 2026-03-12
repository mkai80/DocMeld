"""Unit tests for progress indicator utility."""
import io
import sys


class TestProgressTracker:
    def test_update_format(self) -> None:
        from docmeld.utils.progress import ProgressTracker

        tracker = ProgressTracker()
        captured = io.StringIO()
        tracker.update(3, 10, "Processing PDFs", output=captured)
        output = captured.getvalue()
        assert "3/10" in output
        assert "Processing PDFs" in output

    def test_stage_progress(self) -> None:
        from docmeld.utils.progress import ProgressTracker

        tracker = ProgressTracker()
        captured = io.StringIO()
        tracker.update(5, 10, "Bronze stage", output=captured)
        output = captured.getvalue()
        assert "5/10" in output
        assert "Bronze stage" in output

    def test_complete_shows_done(self) -> None:
        from docmeld.utils.progress import ProgressTracker

        tracker = ProgressTracker()
        captured = io.StringIO()
        tracker.update(10, 10, "Processing", output=captured)
        output = captured.getvalue()
        assert "10/10" in output
