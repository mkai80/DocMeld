"""Unit tests for the categorize categorizer."""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from docmeld.categorize.models import PaperMetadata


def _make_paper(filename: str, keywords: List[str], desc: str = "") -> PaperMetadata:
    return PaperMetadata(
        filename=filename,
        file_path=f"/tmp/{filename}",
        output_dir=f"/tmp/{filename}_out",
        description=desc or f"About {filename}",
        keywords=keywords,
        page_count=1,
        gold_path=f"/tmp/{filename}_out/{filename}_gold.jsonl",
    )


class TestCategorizer:
    def test_builds_sorted_prompt(self) -> None:
        from docmeld.categorize.categorizer import _build_categorization_prompt

        papers = [
            _make_paper("z_paper.pdf", ["ml"]),
            _make_paper("a_paper.pdf", ["nlp"]),
        ]
        prompt = _build_categorization_prompt(papers)
        # Should be sorted by filename for determinism
        assert prompt.index("a_paper.pdf") < prompt.index("z_paper.pdf")

    def test_parses_valid_response(self) -> None:
        from docmeld.categorize.categorizer import _parse_categorization_response

        response = '{"categories": [{"name": "NLP", "papers": ["a.pdf"], "keywords": ["nlp"]}]}'
        result = _parse_categorization_response(response)
        assert len(result) == 1
        assert result[0]["name"] == "NLP"
        assert result[0]["papers"] == ["a.pdf"]

    def test_parses_response_with_code_fences(self) -> None:
        from docmeld.categorize.categorizer import _parse_categorization_response

        response = '```json\n{"categories": [{"name": "CV", "papers": ["b.pdf"], "keywords": ["vision"]}]}\n```'
        result = _parse_categorization_response(response)
        assert len(result) == 1
        assert result[0]["name"] == "CV"

    def test_raises_on_malformed_response(self) -> None:
        from docmeld.categorize.categorizer import _parse_categorization_response

        with pytest.raises(ValueError, match="Failed to parse"):
            _parse_categorization_response("not json at all")

    def test_raises_on_missing_categories_key(self) -> None:
        from docmeld.categorize.categorizer import _parse_categorization_response

        with pytest.raises(ValueError, match="Missing 'categories'"):
            _parse_categorization_response('{"data": []}')

    def test_categorize_papers_calls_api(self) -> None:
        from docmeld.categorize.categorizer import categorize_papers

        papers = [
            _make_paper("paper1.pdf", ["nlp", "transformers"]),
            _make_paper("paper2.pdf", ["vision", "cnn"]),
        ]

        mock_response = '{"categories": [{"name": "NLP", "papers": ["paper1.pdf"], "keywords": ["nlp"]}, {"name": "CV", "papers": ["paper2.pdf"], "keywords": ["vision"]}]}'

        mock_client = MagicMock()
        mock_client.categorize_papers.return_value = mock_response

        result = categorize_papers(papers, mock_client)
        assert len(result) == 2
        mock_client.categorize_papers.assert_called_once()

    def test_deterministic_sorting(self) -> None:
        from docmeld.categorize.categorizer import _build_categorization_prompt

        papers_a = [_make_paper("c.pdf", ["x"]), _make_paper("a.pdf", ["y"]), _make_paper("b.pdf", ["z"])]
        papers_b = [_make_paper("b.pdf", ["z"]), _make_paper("a.pdf", ["y"]), _make_paper("c.pdf", ["x"])]

        prompt_a = _build_categorization_prompt(papers_a)
        prompt_b = _build_categorization_prompt(papers_b)
        assert prompt_a == prompt_b
