"""Unit tests for PyMuPDF backend."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest


class TestPyMuPDFBackend:
    def test_extract_elements_returns_list(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.bronze.backends.pymupdf_backend import PyMuPDFBackend

        shutil.copy(sample_simple_pdf, tmp_path / "test.pdf")
        backend = PyMuPDFBackend()
        elements = backend.extract_elements(str(tmp_path / "test.pdf"), str(tmp_path))
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_elements_have_required_fields(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        from docmeld.bronze.backends.pymupdf_backend import PyMuPDFBackend

        shutil.copy(sample_simple_pdf, tmp_path / "test.pdf")
        backend = PyMuPDFBackend()
        elements = backend.extract_elements(str(tmp_path / "test.pdf"), str(tmp_path))
        for elem in elements:
            assert "type" in elem
            assert "page_no" in elem
            assert elem["type"] in ("title", "text", "table", "image")
            assert elem["page_no"] >= 1

    def test_elements_do_not_have_element_id(
        self, sample_simple_pdf: Path, tmp_path: Path
    ) -> None:
        """Backend returns raw elements; IDs are assigned by post-processing."""
        from docmeld.bronze.backends.pymupdf_backend import PyMuPDFBackend

        shutil.copy(sample_simple_pdf, tmp_path / "test.pdf")
        backend = PyMuPDFBackend()
        elements = backend.extract_elements(str(tmp_path / "test.pdf"), str(tmp_path))
        for elem in elements:
            assert "element_id" not in elem
