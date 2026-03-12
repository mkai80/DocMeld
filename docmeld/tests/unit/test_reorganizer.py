"""Unit tests for the categorize reorganizer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestReorganizer:
    def _setup_folder(self, tmp_path: Path) -> Path:
        """Create a folder with PDFs, output dirs, and categories.json."""
        (tmp_path / "paper1.pdf").write_bytes(b"%PDF-fake")
        (tmp_path / "paper2.pdf").write_bytes(b"%PDF-fake")

        out1 = tmp_path / "paper1_abc"
        out1.mkdir()
        (out1 / "paper1_abc.json").write_text("")
        (out1 / "paper1_abc_gold.jsonl").write_text("{}")

        out2 = tmp_path / "paper2_def"
        out2.mkdir()
        (out2 / "paper2_def.json").write_text("{}")
        (out2 / "paper2_def_gold.jsonl").write_text("{}")

        categories = {
            "created": "2026-03-12T00:00:00Z",
            "source_folder": str(tmp_path),
            "total_papers": 2,
            "total_categories": 2,
            "categories": [
                {"name": "NLP", "papers": ["paper1_abc_gold.jsonl"], "keywords": ["nlp"]},
                {"name": "Computer Vision", "papers": ["paper2_def_gold.jsonl"], "keywords": ["cv"]},
            ],
            "papers": [
                {"filename": "paper1_abc_gold.jsonl", "category": "NLP", "description": "NLP paper", "keywords": ["nlp"]},
                {"filename": "paper2_def_gold.jsonl", "category": "Computer Vision", "description": "CV paper", "keywords": ["cv"]},
            ],
        }
        (tmp_path / "categories.json").write_text(json.dumps(categories))
        return tmp_path

    def test_moves_files_into_category_dirs(self, tmp_path: Path) -> None:
        from docmeld.categorize.reorganizer import reorganize_by_category

        folder = self._setup_folder(tmp_path)
        reorganize_by_category(str(folder))

        assert (folder / "NLP" / "paper1_abc").is_dir()
        assert (folder / "Computer Vision" / "paper2_def").is_dir()

    def test_idempotent(self, tmp_path: Path) -> None:
        from docmeld.categorize.reorganizer import reorganize_by_category

        folder = self._setup_folder(tmp_path)
        reorganize_by_category(str(folder))
        # Run again — should not error
        reorganize_by_category(str(folder))

        assert (folder / "NLP" / "paper1_abc").is_dir()

    def test_sanitizes_category_names(self, tmp_path: Path) -> None:
        from docmeld.categorize.reorganizer import _sanitize_category_name

        assert _sanitize_category_name("NLP/Transformers") == "NLP Transformers"
        assert _sanitize_category_name("AI & ML: Models") == "AI ML Models"
        assert _sanitize_category_name("  Spaces  ") == "Spaces"

    def test_writes_manifest(self, tmp_path: Path) -> None:
        from docmeld.categorize.reorganizer import reorganize_by_category

        folder = self._setup_folder(tmp_path)
        reorganize_by_category(str(folder))

        manifest_path = folder / "_reorganized.json"
        assert manifest_path.exists()
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert len(manifest["moves"]) > 0

    def test_no_categories_json_raises(self, tmp_path: Path) -> None:
        from docmeld.categorize.reorganizer import reorganize_by_category

        with pytest.raises(FileNotFoundError):
            reorganize_by_category(str(tmp_path))
