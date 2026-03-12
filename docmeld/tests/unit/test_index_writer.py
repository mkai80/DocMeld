"""Unit tests for the categorize index writer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from docmeld.categorize.models import PaperMetadata


class TestIndexWriter:
    def test_writes_valid_json(self, tmp_path: Path) -> None:
        from docmeld.categorize.index_writer import write_category_index

        papers = [
            PaperMetadata(filename="p1_gold.jsonl", file_path="/tmp/p1.pdf", output_dir="/tmp/p1_out", description="NLP paper", keywords=["nlp"]),
        ]
        categories = [{"name": "NLP", "papers": ["p1_gold.jsonl"], "keywords": ["nlp"]}]

        result_path = write_category_index(str(tmp_path), papers, categories)
        assert Path(result_path).exists()

        with open(result_path) as f:
            data = json.load(f)

        assert data["total_papers"] == 1
        assert data["total_categories"] == 1
        assert data["categories"][0]["name"] == "NLP"
        assert data["papers"][0]["filename"] == "p1_gold.jsonl"
        assert data["papers"][0]["category"] == "NLP"

    def test_deterministic_output(self, tmp_path: Path) -> None:
        from docmeld.categorize.index_writer import write_category_index

        papers = [
            PaperMetadata(filename="b.jsonl", file_path="/tmp/b.pdf", output_dir="/tmp/b_out", description="B", keywords=["b"]),
            PaperMetadata(filename="a.jsonl", file_path="/tmp/a.pdf", output_dir="/tmp/a_out", description="A", keywords=["a"]),
        ]
        categories = [{"name": "Cat", "papers": ["a.jsonl", "b.jsonl"], "keywords": ["a", "b"]}]

        path1 = tmp_path / "run1"
        path1.mkdir()
        write_category_index(str(path1), papers, categories)

        path2 = tmp_path / "run2"
        path2.mkdir()
        write_category_index(str(path2), papers, categories)

        with open(path1 / "categories.json") as f1, open(path2 / "categories.json") as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        # Remove timestamps and source_folder for comparison (path-dependent)
        del data1["created"]
        del data2["created"]
        del data1["source_folder"]
        del data2["source_folder"]
        assert data1 == data2

    def test_multiple_categories(self, tmp_path: Path) -> None:
        from docmeld.categorize.index_writer import write_category_index

        papers = [
            PaperMetadata(filename="p1.jsonl", file_path="/tmp/p1.pdf", output_dir="/tmp/p1_out", description="NLP", keywords=["nlp"]),
            PaperMetadata(filename="p2.jsonl", file_path="/tmp/p2.pdf", output_dir="/tmp/p2_out", description="CV", keywords=["vision"]),
        ]
        categories = [
            {"name": "NLP", "papers": ["p1.jsonl"], "keywords": ["nlp"]},
            {"name": "CV", "papers": ["p2.jsonl"], "keywords": ["vision"]},
        ]

        write_category_index(str(tmp_path), papers, categories)
        with open(tmp_path / "categories.json") as f:
            data = json.load(f)

        assert data["total_categories"] == 2
        assert data["total_papers"] == 2

    def test_empty_papers(self, tmp_path: Path) -> None:
        from docmeld.categorize.index_writer import write_category_index

        result_path = write_category_index(str(tmp_path), [], [])
        with open(result_path) as f:
            data = json.load(f)

        assert data["total_papers"] == 0
        assert data["total_categories"] == 0
