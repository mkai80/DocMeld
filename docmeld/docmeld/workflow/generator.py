"""Workflow generator - extract step-by-step workflows from paper content."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, List

from docmeld.workflow.models import WorkflowResult

logger = logging.getLogger("docmeld")

WORKFLOW_SECTIONS = [
    "Prerequisites",
    "Steps",
    "Decision Points",
    "Expected Outputs",
    "Validation Criteria",
]


def generate_workflow(
    silver_jsonl_path: str, client: Any, source_pdf: str = ""
) -> WorkflowResult:
    """Generate a workflow markdown file from a silver JSONL file.

    Args:
        silver_jsonl_path: Path to the silver JSONL file.
        client: DeepSeekClient instance with generate_prd() method (reused for API calls).
        source_pdf: Original PDF filename for metadata.

    Returns:
        WorkflowResult with output path and section count.
    """
    jsonl_path = Path(silver_jsonl_path)
    output_dir = jsonl_path.parent
    wf_path = output_dir / (jsonl_path.stem.replace("_gold", "") + "_workflow.md")

    # Idempotency check
    if wf_path.exists():
        content = wf_path.read_text(encoding="utf-8")
        section_count = sum(1 for s in WORKFLOW_SECTIONS if f"## {s}" in content)
        return WorkflowResult(
            output_path=str(wf_path),
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

    # Generate workflow via API
    prompt = _build_workflow_prompt(aggregated, source_pdf)
    logger.info(f"Generating workflow for {source_pdf or jsonl_path.name}...")

    response_text = client.generate_prd(prompt)  # Reuses same API method
    wf_content = _parse_workflow_response(response_text, source_pdf)

    # Atomic write
    wf_path.write_text(wf_content, encoding="utf-8")

    section_count = sum(1 for s in WORKFLOW_SECTIONS if f"## {s}" in wf_content)
    logger.info(f"Workflow written to {wf_path} ({section_count} sections)")

    return WorkflowResult(
        output_path=str(wf_path),
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
    """Aggregate page content, truncating if too long."""
    full_content = "\n\n---\n\n".join(pages)

    if len(full_content) <= max_chars:
        return full_content

    first_budget = int(max_chars * 0.6)
    last_budget = max_chars - first_budget

    return (
        full_content[:first_budget]
        + "\n\n[... content truncated for length ...]\n\n"
        + full_content[-last_budget:]
    )


def _build_workflow_prompt(content: str, source_name: str = "") -> str:
    """Build the prompt for workflow generation."""
    source_label = f' "{source_name}"' if source_name else ""

    return (
        f"You are a technical analyst extracting a reproducible workflow from a research paper{source_label}. "
        "Based on the paper content below, generate a step-by-step workflow document.\n\n"
        "The workflow MUST have exactly these five sections as markdown H2 headers:\n"
        "## Prerequisites\n"
        "## Steps\n"
        "## Decision Points\n"
        "## Expected Outputs\n"
        "## Validation Criteria\n\n"
        "Rules:\n"
        "- Prerequisites: list required tools, data, knowledge, and environment setup\n"
        "- Steps: numbered, ordered, actionable steps to reproduce the paper's approach\n"
        "- Decision Points: branching logic or choices the practitioner must make\n"
        "- Expected Outputs: what each major step should produce\n"
        "- Validation Criteria: how to verify the workflow was executed correctly\n"
        "- All content must be derived from the paper\n"
        "- Steps must be concrete and actionable, not vague\n"
        "- Use numbered lists for Steps, bullet points for other sections\n\n"
        f"Paper content:\n\n{content}"
    )


def _parse_workflow_response(response_text: str, source_name: str = "") -> str:
    """Parse the API response into a formatted workflow markdown document."""
    text = response_text.strip()

    # Strip code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Add title header if not present
    if not text.startswith("# "):
        title = "# Workflow"
        if source_name:
            title += f": {source_name}"
        text = f"{title}\n\n{text}"

    return text
