"""Categorize papers into topic clusters via DeepSeek API."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from docmeld.categorize.models import PaperMetadata

logger = logging.getLogger("docmeld")


def categorize_papers(
    papers: List[PaperMetadata], client: Any
) -> List[Dict[str, Any]]:
    """Send aggregated paper metadata to DeepSeek for topic clustering.

    Args:
        papers: List of PaperMetadata from the aggregator.
        client: DeepSeekClient instance with categorize_papers() method.

    Returns:
        List of category dicts: [{"name": str, "papers": [str], "keywords": [str]}]
    """
    if not papers:
        return []

    prompt = _build_categorization_prompt(papers)
    logger.info(f"Categorizing {len(papers)} papers via API...")

    response_text = client.categorize_papers(prompt)
    categories = _parse_categorization_response(response_text)

    logger.info(f"Identified {len(categories)} categories")
    return categories


def _build_categorization_prompt(papers: List[PaperMetadata]) -> str:
    """Build the JSON prompt for categorization, sorted by filename for determinism."""
    sorted_papers = sorted(papers, key=lambda p: p.filename)

    paper_data = []
    for p in sorted_papers:
        paper_data.append({
            "filename": p.filename,
            "description": p.description,
            "keywords": p.keywords,
        })

    prompt_json = json.dumps(paper_data, ensure_ascii=False, indent=2)

    return (
        "You are a research paper categorization assistant. "
        "Given the following list of research papers with their descriptions and keywords, "
        "group them into topic categories.\n\n"
        "Rules:\n"
        "- Each paper must be assigned to exactly one category\n"
        "- Determine the number of categories automatically based on content similarity\n"
        "- Category names should be concise and descriptive (e.g., 'Natural Language Processing', 'Computer Vision')\n"
        "- If all papers are on similar topics, use a single category\n"
        "- Include representative keywords for each category\n\n"
        "Return ONLY valid JSON with this exact structure:\n"
        '{"categories": [{"name": "Category Name", "papers": ["filename1.jsonl", "filename2.jsonl"], "keywords": ["kw1", "kw2"]}]}\n\n'
        f"Papers:\n{prompt_json}"
    )


def _parse_categorization_response(response_text: str) -> List[Dict[str, Any]]:
    """Parse the API response into category assignments.

    Args:
        response_text: Raw text from the API.

    Returns:
        List of category dicts.

    Raises:
        ValueError: If the response cannot be parsed.
    """
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse categorization response: {e}") from e

    if "categories" not in data:
        raise ValueError("Missing 'categories' key in categorization response")

    return data["categories"]
