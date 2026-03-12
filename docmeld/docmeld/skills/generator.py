"""Skills generator - extract Claude Code skills from book content."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from docmeld.skills.models import SkillsResult

logger = logging.getLogger("docmeld")


def generate_skills(
    silver_jsonl_path: str, client: Any, source_pdf: str = ""
) -> SkillsResult:
    """Generate Claude Code skill files from a silver JSONL file.

    Args:
        silver_jsonl_path: Path to the silver JSONL file.
        client: DeepSeekClient instance.
        source_pdf: Original PDF filename for metadata.

    Returns:
        SkillsResult with output directory and skill count.
    """
    jsonl_path = Path(silver_jsonl_path)
    output_dir = jsonl_path.parent
    skills_dir = output_dir / "_skills"

    # Idempotency check
    if skills_dir.exists() and any(skills_dir.glob("*.md")):
        skill_count = len(list(skills_dir.glob("*.md")))
        return SkillsResult(
            output_dir=str(skills_dir),
            skill_count=skill_count,
            source_pdf=source_pdf,
            skipped=True,
        )

    # Load silver pages
    pages = _load_silver_content(str(jsonl_path))
    if not pages:
        raise ValueError(f"No content found in {silver_jsonl_path}")

    # Aggregate content (chunked for long books)
    aggregated = _aggregate_content(pages)

    # Generate skills via API
    prompt = _build_skills_prompt(aggregated, source_pdf)
    logger.info(f"Extracting skills from {source_pdf or jsonl_path.name}...")

    response_text = client.generate_prd(prompt)  # Reuses same API method
    skills = _parse_skills_response(response_text)

    if not skills:
        raise ValueError("No skills could be extracted from the content")

    # Write skill files atomically
    skills_dir.mkdir(exist_ok=True)
    for skill in skills:
        filename = _to_kebab_case(skill["title"]) + ".md"
        filepath = skills_dir / filename
        filepath.write_text(skill["content"], encoding="utf-8")

    logger.info(f"Wrote {len(skills)} skills to {skills_dir}")

    return SkillsResult(
        output_dir=str(skills_dir),
        skill_count=len(skills),
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


def _build_skills_prompt(content: str, source_name: str = "") -> str:
    """Build the prompt for skills extraction."""
    source_label = f' "{source_name}"' if source_name else ""

    return (
        f"You are a technical knowledge extractor analyzing a book{source_label}. "
        "Extract the key methodologies, techniques, and practices from this book "
        "as discrete, reusable skills.\n\n"
        "For each skill, output a JSON object in this format:\n"
        '{"skills": [\n'
        '  {"title": "Skill Title", "description": "One-line description", '
        '"steps": ["Step 1...", "Step 2..."], '
        '"examples": ["Example or edge case note"]}\n'
        "]}\n\n"
        "Rules:\n"
        "- Extract 3-10 skills depending on the book's breadth\n"
        "- Each skill must be self-contained and actionable\n"
        "- Steps must be concrete and ordered\n"
        "- Include at least one example or edge case per skill\n"
        "- Skill titles should be concise action phrases (e.g., 'Apply Single Responsibility Principle')\n"
        "- All content must be derived from the book\n"
        "- Return ONLY valid JSON, no other text\n\n"
        f"Book content:\n\n{content}"
    )


def _parse_skills_response(response_text: str) -> List[Dict[str, Any]]:
    """Parse the API response into a list of skill dicts."""
    text = response_text.strip()

    # Strip code fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse skills response: {e}") from e

    raw_skills = data.get("skills", [])
    result = []

    for skill in raw_skills:
        title = skill.get("title", "").strip()
        if not title:
            continue

        description = skill.get("description", "")
        steps = skill.get("steps", [])
        examples = skill.get("examples", [])

        # Build markdown content
        lines = [f"# {title}\n"]
        if description:
            lines.append(f"{description}\n")

        lines.append("\n## Instructions\n")
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {step}")

        if examples:
            lines.append("\n\n## Examples & Edge Cases\n")
            for ex in examples:
                lines.append(f"- {ex}")

        result.append({
            "title": title,
            "content": "\n".join(lines) + "\n",
        })

    return result


def _to_kebab_case(text: str) -> str:
    """Convert a title to kebab-case for filenames."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    if len(text) > 80:
        text = text[:80].rstrip("-")
    return text or "skill"
