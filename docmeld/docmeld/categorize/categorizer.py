"""Categorize papers into topic clusters via DeepSeek API."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from docmeld.categorize.models import PaperMetadata

logger = logging.getLogger("docmeld")

# Max papers per API call to avoid response truncation
BATCH_SIZE = 30


def categorize_papers(
    papers: List[PaperMetadata], client: Any
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Send aggregated paper content to DeepSeek for topic clustering.

    For large collections, batches papers into groups and merges results.

    Args:
        papers: List of PaperMetadata from the aggregator.
        client: DeepSeekClient instance with categorize_papers() method.

    Returns:
        Tuple of (categories, paper_descriptions).
    """
    if not papers:
        return [], []

    sorted_papers = sorted(papers, key=lambda p: p.filename)

    if len(sorted_papers) <= BATCH_SIZE:
        return _categorize_batch(sorted_papers, client)

    # Batch processing for large collections
    all_categories: List[Dict[str, Any]] = []
    all_descs: List[Dict[str, Any]] = []

    for i in range(0, len(sorted_papers), BATCH_SIZE):
        batch = sorted_papers[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(sorted_papers) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"Categorizing batch {batch_num}/{total_batches} ({len(batch)} papers)...")

        cats, descs = _categorize_batch(batch, client)
        all_categories.extend(cats)
        all_descs.extend(descs)

    # Merge categories with the same name across batches
    merged = _merge_categories(all_categories)
    logger.info(f"Identified {len(merged)} categories across {total_batches} batches")
    return merged, all_descs


def _categorize_batch(
    papers: List[PaperMetadata], client: Any
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Categorize a single batch of papers."""
    prompt = _build_categorization_prompt(papers)
    logger.info(f"Categorizing {len(papers)} papers via API...")

    response_text = client.categorize_papers(prompt)
    return _parse_categorization_response(response_text)


def _merge_categories(categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge categories with the same name from different batches."""
    merged: Dict[str, Dict[str, Any]] = {}
    for cat in categories:
        name = cat.get("name", "Uncategorized")
        if name in merged:
            merged[name]["papers"].extend(cat.get("papers", []))
            # Deduplicate keywords
            existing_kws = set(k.lower() for k in merged[name]["keywords"])
            for kw in cat.get("keywords", []):
                if kw.lower() not in existing_kws:
                    merged[name]["keywords"].append(kw)
                    existing_kws.add(kw.lower())
        else:
            merged[name] = {
                "name": name,
                "papers": list(cat.get("papers", [])),
                "keywords": list(cat.get("keywords", [])),
            }
    return list(merged.values())


def _build_categorization_prompt(papers: List[PaperMetadata]) -> str:
    """Build the prompt for categorization using truncated paper content."""
    sorted_papers = sorted(papers, key=lambda p: p.filename)

    paper_sections = []
    for p in sorted_papers:
        # Use first 500 chars — enough for title + abstract
        content_preview = p.content[:500] if p.content else "(no content)"
        paper_sections.append(
            f"=== {p.filename} ===\n{content_preview}\n"
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
        "- Include 3-5 representative keywords for each category\n"
        "- Return a one-line description and 3-5 keywords for each paper\n\n"
        "Return ONLY valid JSON with this exact structure:\n"
        '{"categories": [{"name": "Category Name", "papers": ["filename1.jsonl"], "keywords": ["kw1", "kw2"]}], '
        '"paper_descriptions": [{"filename": "filename1.jsonl", "description": "one-line summary", "keywords": ["kw1"]}]}\n\n'
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
