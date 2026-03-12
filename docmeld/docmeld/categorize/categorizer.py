"""Categorize papers into topic clusters via DeepSeek API."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from docmeld.categorize.models import PaperMetadata

logger = logging.getLogger("docmeld")


def categorize_papers(
    papers: List[PaperMetadata], client: Any
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Send aggregated paper content to DeepSeek for topic clustering.

    Args:
        papers: List of PaperMetadata from the aggregator.
        client: DeepSeekClient instance with categorize_papers() method.

    Returns:
        Tuple of (categories, paper_descriptions).
    """
    if not papers:
        return [], []

    prompt = _build_categorization_prompt(papers)
    logger.info(f"Categorizing {len(papers)} papers via API...")

    response_text = client.categorize_papers(prompt)
    categories, paper_descs = _parse_categorization_response(response_text)

    logger.info(f"Identified {len(categories)} categories")
    return categories, paper_descs


def _build_categorization_prompt(papers: List[PaperMetadata]) -> str:
    """Build the prompt for categorization using truncated paper content."""
    sorted_papers = sorted(papers, key=lambda p: p.filename)

    paper_sections = []
    for p in sorted_papers:
        # Truncate content to keep total prompt manageable
        content_preview = p.content[:3000] if p.content else "(no content)"
        paper_sections.append(
            f"=== Paper: {p.filename} ===\n{content_preview}\n"
        )

    papers_text = "\n".join(paper_sections)

    return (
        "You are a research paper categorization assistant. "
        "Given the following research papers with their content excerpts, "
        "group them into topic categories.\n\n"
        "Rules:\n"
        "- Each paper must be assigned to exactly one category\n"
        "- Determine the number of categories automatically based on content similarity\n"
        "- Category names should be concise and descriptive (e.g., 'Natural Language Processing', 'Computer Vision')\n"
        "- If all papers are on similar topics, use a single category\n"
        "- Include representative keywords for each category\n"
        "- Also return a one-line description for each paper\n\n"
        "Return ONLY valid JSON with this exact structure:\n"
        '{"categories": [{"name": "Category Name", "papers": ["filename1.jsonl", "filename2.jsonl"], "keywords": ["kw1", "kw2"]}], '
        '"paper_descriptions": [{"filename": "filename1.jsonl", "description": "one-line summary", "keywords": ["kw1", "kw2"]}]}\n\n'
        f"Papers:\n{papers_text}"
    )


def _parse_categorization_response(
    response_text: str,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse the API response into category assignments and paper descriptions.

    Returns:
        Tuple of (categories, paper_descriptions).
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

    categories = data["categories"]
    paper_descs = data.get("paper_descriptions", [])
    return categories, paper_descs
