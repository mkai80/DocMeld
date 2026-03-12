"""Integration tests for batch bronze processing."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest


class TestBronzeBatchProcessing:
    def test_processes_folder_of_pdfs(
        self, sample_simple_pdf: Path, sample_complex_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.bronze.processor import BronzeProcessor

        shutil.copy(sample_simple_pdf, tmp_path / "doc1.pdf")
        shutil.copy(sample_complex_pdf, tmp_path / "doc2.pdf")
        shutil.copy(sample_simple_pdf, tmp_path / "doc3.pdf")

        processor = BronzeProcessor()
        result = processor.process_folder(str(tmp_path))

        assert result.total_files == 3
        assert result.successful == 3
        assert result.failed == 0

    def test_ignores_non_pdf_files(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.bronze.processor import BronzeProcessor

        shutil.copy(sample_simple_pdf, tmp_path / "doc.pdf")
        (tmp_path / "readme.txt").write_text("not a pdf")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")

        processor = BronzeProcessor()
        result = processor.process_folder(str(tmp_path))

        assert result.total_files == 1
        assert result.successful == 1

    def test_skips_already_processed(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.bronze.processor import BronzeProcessor

        shutil.copy(sample_simple_pdf, tmp_path / "doc.pdf")

        processor = BronzeProcessor()
        result1 = processor.process_folder(str(tmp_path))
        assert result1.successful == 1

        # Second run should skip
        result2 = processor.process_folder(str(tmp_path))
        assert result2.total_files == 1
        assert result2.successful == 1  # Still counts as successful (skipped)

    def test_continues_on_failure(self, sample_simple_pdf: Path, tmp_path: Path) -> None:
        from docmeld.bronze.processor import BronzeProcessor

        shutil.copy(sample_simple_pdf, tmp_path / "good.pdf")
        (tmp_path / "bad.pdf").write_bytes(b"not a real pdf")

        processor = BronzeProcessor()
        result = processor.process_folder(str(tmp_path))

        assert result.total_files == 2
        assert result.successful == 1
        assert result.failed == 1
        assert len(result.failures) == 1
        assert "bad.pdf" in result.failures[0].filename

    def test_empty_folder(self, tmp_path: Path) -> None:
        from docmeld.bronze.processor import BronzeProcessor

        processor = BronzeProcessor()
        result = processor.process_folder(str(tmp_path))

        assert result.total_files == 0
        assert result.successful == 0
        assert result.failed == 0

    def test_summary_includes_timing(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.bronze.processor import BronzeProcessor

        shutil.copy(sample_simple_pdf, tmp_path / "doc.pdf")

        processor = BronzeProcessor()
        result = processor.process_folder(str(tmp_path))

        assert result.processing_time_seconds >= 0
