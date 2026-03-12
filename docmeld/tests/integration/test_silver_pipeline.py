"""Integration tests for silver pipeline."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest


class TestSilverPipeline:
    def _create_bronze_json(self, tmp_path: Path) -> Path:
        """Helper to create a bronze JSON file for testing."""
        elements = [
            {"type": "title", "level": 0, "content": "Report Title", "page_no": 1},
            {"type": "text", "content": "Introduction paragraph.", "page_no": 1},
            {"type": "title", "level": 1, "content": "Section A", "page_no": 1},
            {"type": "text", "content": "Section A content.", "page_no": 1},
            {"type": "table", "content": "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |", "summary": "Items: A", "page_no": 2},
            {"type": "text", "content": "After table text.", "page_no": 2},
            {"type": "title", "level": 1, "content": "Section B", "page_no": 3},
            {"type": "text", "content": "Section B content.", "page_no": 3},
        ]
        output_dir = tmp_path / "test_doc_abc123"
        output_dir.mkdir()
        json_path = output_dir / "test_doc_abc123.json"
        with open(json_path, "w") as f:
            json.dump(elements, f)
        return json_path

    def test_creates_jsonl_with_one_line_per_page(self, tmp_path: Path) -> None:
        from docmeld.silver.processor import SilverProcessor

        json_path = self._create_bronze_json(tmp_path)
        processor = SilverProcessor()
        result = processor.process(str(json_path))

        assert result.page_count == 3
        assert Path(result.output_path).exists()

        with open(result.output_path) as f:
            lines = [line for line in f if line.strip()]
        assert len(lines) == 3

    def test_each_page_has_metadata(self, tmp_path: Path) -> None:
        from docmeld.silver.processor import SilverProcessor

        json_path = self._create_bronze_json(tmp_path)
        processor = SilverProcessor()
        result = processor.process(str(json_path))

        with open(result.output_path) as f:
            for line in f:
                if not line.strip():
                    continue
                page = json.loads(line)
                assert "metadata" in page
                assert "page_content" in page
                assert "uuid" in page["metadata"]
                assert "source" in page["metadata"]
                assert "page_no" in page["metadata"]
                assert "session_title" in page["metadata"]

    def test_title_hierarchy_across_pages(self, tmp_path: Path) -> None:
        from docmeld.silver.processor import SilverProcessor

        json_path = self._create_bronze_json(tmp_path)
        processor = SilverProcessor()
        result = processor.process(str(json_path))

        with open(result.output_path) as f:
            pages = [json.loads(line) for line in f if line.strip()]

        # Page 2 should include title hierarchy from page 1
        page2_content = pages[1]["page_content"]
        assert "Report Title" in pages[1]["metadata"]["session_title"]

    def test_global_table_numbering(self, tmp_path: Path) -> None:
        from docmeld.silver.processor import SilverProcessor

        json_path = self._create_bronze_json(tmp_path)
        processor = SilverProcessor()
        result = processor.process(str(json_path))

        with open(result.output_path) as f:
            pages = [json.loads(line) for line in f if line.strip()]

        # Page 2 has a table — should be Table1
        page2_content = pages[1]["page_content"]
        assert "[[Table1]]" in page2_content

    def test_idempotency(self, tmp_path: Path) -> None:
        from docmeld.silver.processor import SilverProcessor

        json_path = self._create_bronze_json(tmp_path)
        processor = SilverProcessor()
        result1 = processor.process(str(json_path))
        assert not result1.skipped

        result2 = processor.process(str(json_path))
        assert result2.skipped

    def test_page_no_format(self, tmp_path: Path) -> None:
        from docmeld.silver.processor import SilverProcessor

        json_path = self._create_bronze_json(tmp_path)
        processor = SilverProcessor()
        result = processor.process(str(json_path))

        with open(result.output_path) as f:
            pages = [json.loads(line) for line in f if line.strip()]

        assert pages[0]["metadata"]["page_no"] == "page1"
        assert pages[1]["metadata"]["page_no"] == "page2"
        assert pages[2]["metadata"]["page_no"] == "page3"
