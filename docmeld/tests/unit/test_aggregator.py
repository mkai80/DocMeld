"""Unit tests for the categorize aggregator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestAggregator:
    def _write_gold_jsonl(self, path: Path, pages: list) -> None:
        with open(path, "w") as f:
            for page in pages:
                f.write(json.dumps(page) + "\n")

    def test_collects_metadata_from_gold_files(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        # Create a fake gold JSONL
        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        gold_path = paper_dir / "paper1_abc123_gold.jsonl"
        self._write_gold_jsonl(gold_path, [
            {"metadata": {"description": "Page about NLP", "keywords": ["nlp", "transformers"]}, "page_content": "..."},
            {"metadata": {"description": "Page about attention", "keywords": ["attention", "nlp"]}, "page_content": "..."},
        ])
        # Create the corresponding PDF
        (tmp_path / "paper1.pdf").write_bytes(b"%PDF-fake")

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 1
        assert results[0].filename == "paper1_abc123_gold.jsonl"
        assert "nlp" in results[0].keywords
        assert "transformers" in results[0].keywords
        assert "attention" in results[0].keywords
        assert results[0].page_count == 2

    def test_deduplicates_keywords(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        gold_path = paper_dir / "paper1_abc123_gold.jsonl"
        self._write_gold_jsonl(gold_path, [
            {"metadata": {"description": "Desc A", "keywords": ["ml", "deep-learning"]}, "page_content": "..."},
            {"metadata": {"description": "Desc B", "keywords": ["ml", "cnn"]}, "page_content": "..."},
        ])

        results = aggregate_paper_metadata(str(tmp_path))
        keyword_counts = {}
        for kw in results[0].keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        assert keyword_counts.get("ml", 0) == 1  # deduplicated

    def test_handles_empty_folder(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        results = aggregate_paper_metadata(str(tmp_path))
        assert results == []

    def test_handles_missing_metadata_fields(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        gold_path = paper_dir / "paper1_abc123_gold.jsonl"
        self._write_gold_jsonl(gold_path, [
            {"metadata": {}, "page_content": "some content"},
        ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 1
        assert results[0].description == ""
        assert results[0].keywords == []

    def test_skips_failed_gold_pages(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        paper_dir = tmp_path / "paper1_abc123"
        paper_dir.mkdir()
        gold_path = paper_dir / "paper1_abc123_gold.jsonl"
        self._write_gold_jsonl(gold_path, [
            {"metadata": {"description": "Good page", "keywords": ["ml"], "gold_processing_failed": True}, "page_content": "..."},
            {"metadata": {"description": "Also good", "keywords": ["dl"]}, "page_content": "..."},
        ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 1
        # Failed pages should still contribute keywords but description comes from non-failed
        assert results[0].page_count == 2

    def test_multiple_papers(self, tmp_path: Path) -> None:
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        for name in ["paper1_aaa", "paper2_bbb"]:
            d = tmp_path / name
            d.mkdir()
            gold = d / f"{name}_gold.jsonl"
            self._write_gold_jsonl(gold, [
                {"metadata": {"description": f"About {name}", "keywords": [name]}, "page_content": "..."},
            ])

        results = aggregate_paper_metadata(str(tmp_path))
        assert len(results) == 2
