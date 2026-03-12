"""PRD generator - create Product Requirements Documents from paper content."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from docmeld.prd.models import PrdResult

logger = logging.getLogger("docmeld")

PRD_SECTIONS = [
    "Problem Statement",
    "Proposed Solution",
    "Key Features",
    "Technical Requirements",
    "Target Users",
    "Success Metrics",
]


def generate_prd(
    silver_jsonl_path: str, client: Any, source_pdf: str = ""
) -> PrdResult:
    """Generate a PRD markdown file from a silver JSONL file.

    Args:
        silver_jsonl_path: Path to the silver JSONL file.
        client: DeepSeekClient instance.
        source_pdf: Original PDF filename for metadata.

    Returns:
        PrdResult with output path and section count.
    """
    jsonl_path = Path(silver_jsonl_path)
    output_dir = jsonl_path.parent
    prd_path = output_dir / (jsonl_path.stem.replace("_gold", "") + "_prd.md")

    # Idempotency check
    if prd_path.exists():
        content = prd_path.read_text(encoding="utf-8")
        section_count = sum(1 for s in PRD_SECTIONS if f"## {s}" in content)
        return PrdResult(
            output_path=str(prd_path),
            sections=section_count,
            source_pdf=source_pdf,
            skipped=True,
        )

    # Load silver pages
    pages = _load_silver_content(str(jsonl_path))
    if not pages:
        raise ValueError(f"No content found in {silver_jsonl_path}")

    # Aggregate content (truncate for long papers)
    aggregated = _aggregate_content(pages)

    # Generate PRD via API
    prompt = _build_prd_prompt(aggregated, source_pdf)
    logger.info(f"Generating PRD for {source_pdf or jsonl_path.name}...")

    response_text = client.generate_prd(prompt)
    prd_content = _parse_prd_response(response_text, source_pdf)

    # Atomic write — only create file if generation succeeded
    prd_path.write_text(prd_content, encoding="utf-8")

    section_count = sum(1 for s in PRD_SECTIONS if f"## {s}" in prd_content)
    logger.info(f"PRD written to {prd_path} ({section_count} sections)")

    return PrdResult(
        output_path=str(prd_path),
        sections=section_count,
        source_pdf=source_pdf,
    )


def _load_silver_content(jsonl_path: str) -> List[str]:
    """Load page content from a silver JSONL file."""
    pages: List[str] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                page = json.loads(line)
                content = page.get("page_content", "")
                if content.strip():
                    pages.append(content)
    return pages


def _aggregate_content(pages: List[str], max_chars: int = 30000) -> str:
    """Aggregate page content, truncating if too long.

    Prioritizes first and last pages (abstract + conclusion) for long papers.
    """
    full_content = "\n\n---\n\n".join(pages)

    if len(full_content) <= max_chars:
        return full_content

    # For long papers: take first 60% and last 40% of budget
    first_budget = int(max_chars * 0.6)
    last_budget = max_chars - first_budget

    first_part = full_content[:first_budget]
    last_part = full_content[-last_budget:]

    return first_part + "\n\n[... content truncated for length ...]\n\n" + last_part


def _build_prd_prompt(content: str, source_name: str = "") -> str:
    """Build the prompt for PRD generation."""
    source_label = f' "{source_name}"' if source_name else ""

    return (
        f"You are a product manager analyzing a research paper{source_label}. "
        "Based on the paper content below, generate a Product Requirements Document (PRD) "
        "that describes how this research could be turned into a product.\n\n"
        "The PRD MUST have exactly these six sections as markdown H2 headers:\n"
        "## Problem Statement\n"
        "## Proposed Solution\n"
        "## Key Features\n"
        "## Technical Requirements\n"
        "## Target Users\n"
        "## Success Metrics\n\n"
        "Rules:\n"
        "- All content must be derived from the paper — do not invent features not described\n"
        "- Problem Statement: extract from abstract/introduction\n"
        "- Proposed Solution: extract from methodology/approach sections\n"
        "- Key Features: list 3-8 concrete capabilities described in the paper\n"
        "- Technical Requirements: extract from implementation/system design sections\n"
        "- Target Users: infer from the paper's application domain\n"
        "- Success Metrics: extract from evaluation/results sections\n"
        "- Write in clear, concise product language (not academic)\n"
        "- Use bullet points for Key Features and Technical Requirements\n\n"
        f"Paper content:\n\n{content}"
    )


def _parse_prd_response(response_text: str, source_name: str = "") -> str:
    """Parse the API response into a formatted PRD markdown document."""
    text = response_text.strip()

    # Strip code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Add title header if not present
    if not text.startswith("# "):
        title = f"# Product Requirements Document"
        if source_name:
            title += f": {source_name}"
        text = f"{title}\n\n{text}"

    return text
