"""Unit tests for the categorize aggregator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestAggregator:
    def _write_silver_jsonl(self, path: Path, pages: list) -> None:
        with open(path, "w") as f:
            for page in pages:
                f.write(json.dumps(page) + "\n")

    def test_collects_content_from_silver_files(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        silver_path = paper_dir / "paper1_abc123.jsonl"
        self._write_silver_jsonl(silver_path, [
            {"metadata": {"uuid": "1", "source": "paper1.pdf", "page_no": "page1", "session_title": ""}, "page_content": "Page about NLP transformers"},
            {"metadata": {"uuid": "2", "source": "paper1.pdf", "page_no": "page2", "session_title": ""}, "page_content": "Page about attention mechanisms"},
        ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 1
        assert results[0].filename == "paper1_abc123.jsonl"
        assert "NLP transformers" in results[0].content
        assert "attention mechanisms" in results[0].content
        assert results[0].page_count == 2

    def test_truncates_content_at_limit(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import MAX_CONTENT_CHARS, aggregate_paper_metadata

        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        silver_path = paper_dir / "paper1_abc123.jsonl"
        # Create content that exceeds the limit
        long_content = "x" * (MAX_CONTENT_CHARS + 5000)
        self._write_silver_jsonl(silver_path, [
            {"metadata": {"uuid": "1", "source": "p.pdf", "page_no": "page1", "session_title": ""}, "page_content": long_content},
        ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 1
        assert len(results[0].content) <= MAX_CONTENT_CHARS

    def test_handles_empty_folder(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        results = aggregate_paper_metadata(str(tmp_path))
        assert results == []

    def test_handles_empty_page_content(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        silver_path = paper_dir / "paper1_abc123.jsonl"
        self._write_silver_jsonl(silver_path, [
            {"metadata": {"uuid": "1", "source": "p.pdf", "page_no": "page1", "session_title": ""}, "page_content": ""},
        ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 1
        assert results[0].content == ""

    def test_skips_gold_files(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        # Silver file
        silver_path = paper_dir / "paper1_abc123.jsonl"
        self._write_silver_jsonl(silver_path, [
            {"metadata": {"uuid": "1", "source": "p.pdf", "page_no": "page1", "session_title": ""}, "page_content": "real content"},
        ])
        # Gold file should be ignored
        gold_path = paper_dir / "paper1_abc123_gold.jsonl"
        self._write_silver_jsonl(gold_path, [
            {"metadata": {"uuid": "1", "source": "p.pdf", "page_no": "page1", "session_title": "", "description": "gold desc", "keywords": ["gold"]}, "page_content": "gold content"},
        ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 1
        assert results[0].filename == "paper1_abc123.jsonl"

    def test_multiple_papers(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        for name in ["paper1_aaa", "paper2_bbb"]:
            d = tmp_path / name
            d.mkdir()
            silver = d / f"{name}.jsonl"
            self._write_silver_jsonl(silver, [
                {"metadata": {"uuid": "1", "source": f"{name}.pdf", "page_no": "page1", "session_title": ""}, "page_content": f"About {name}"},
            ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 2
