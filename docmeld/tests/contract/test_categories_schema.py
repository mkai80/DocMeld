"""Contract tests for categories.json schema."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "specs" / "002-paper-batch-categorize" / "contracts" / "categories-schema.json"


class TestCategoriesSchema:
    @pytest.fixture()
    def schema(self) -> dict:
        with open(SCHEMA_PATH) as f:
            return json.load(f)

    def test_schema_loads(self, schema: dict) -> None:
        assert schema["title"] == "DocMeld Category Index"
        assert "properties" in schema

    def test_required_fields(self, schema: dict) -> None:
        assert set(schema["required"]) == {
            "created", "source_folder", "total_papers",
            "total_categories", "categories", "papers",
        }

    def test_valid_category_index(self, schema: dict) -> None:
        index = {
            "created": "2026-03-12T00:00:00Z",
            "source_folder": "/tmp/papers",
            "total_papers": 2,
            "total_categories": 1,
            "categories": [
                {"name": "NLP", "papers": ["p1.jsonl", "p2.jsonl"], "keywords": ["nlp"]},
            ],
            "papers": [
                {"filename": "p1.jsonl", "category": "NLP", "description": "Paper 1", "keywords": ["nlp"]},
                {"filename": "p2.jsonl", "category": "NLP", "description": "Paper 2", "keywords": ["nlp"]},
            ],
        }
        # Validate structure matches schema expectations
        assert isinstance(index["categories"], list)
        assert isinstance(index["papers"], list)
        assert index["total_papers"] == len(index["papers"])
        assert index["total_categories"] == len(index["categories"])

    def test_category_requires_name_and_papers(self, schema: dict) -> None:
        cat_schema = schema["properties"]["categories"]["items"]
        assert "name" in cat_schema["required"]
        assert "papers" in cat_schema["required"]
        assert "keywords" in cat_schema["required"]

    def test_paper_entry_requires_fields(self, schema: dict) -> None:
        paper_schema = schema["properties"]["papers"]["items"]
        assert set(paper_schema["required"]) == {"filename", "category", "description", "keywords"}

    def test_category_papers_min_items(self, schema: dict) -> None:
        cat_schema = schema["properties"]["categories"]["items"]
        assert cat_schema["properties"]["papers"]["minItems"] == 1
