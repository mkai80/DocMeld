"""Integration tests for CLI interface."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest


class TestCLI:
    def test_help_output(self) -> None:
        from docmeld.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_no_command_returns_1(self) -> None:
        from docmeld.cli import main

        result = main([])
        assert result == 1

    def test_invalid_path_returns_1(self) -> None:
        from docmeld.cli import main

        result = main(["bronze", "/nonexistent/path.pdf"])
        assert result == 1

    def test_bronze_single_file(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.cli import main

        shutil.copy(sample_simple_pdf, tmp_path / "test.pdf")
        result = main(["bronze", str(tmp_path / "test.pdf")])
        assert result == 0

    def test_bronze_folder(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.cli import main

        shutil.copy(sample_simple_pdf, tmp_path / "doc1.pdf")
        shutil.copy(sample_simple_pdf, tmp_path / "doc2.pdf")
        result = main(["bronze", str(tmp_path)])
        assert result == 0

    def test_silver_from_bronze(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.cli import main
        from docmeld.bronze.processor import BronzeProcessor

        shutil.copy(sample_simple_pdf, tmp_path / "test.pdf")
        processor = BronzeProcessor()
        bronze_result = processor.process_file(str(tmp_path / "test.pdf"))

        result = main(["silver", bronze_result.output_path])
        assert result == 0
