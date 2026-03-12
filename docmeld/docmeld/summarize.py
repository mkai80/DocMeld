"""Batch summarize papers using silver JSONL content via DeepSeek-chat.

Supports concurrent API calls for faster processing.

Usage:
    cd /Users/frank/A/DocMeld
    source docmeld/venv/bin/activate
    python -m docmeld.summarize "/path/to/folder" --workers 10
"""
from __future__ import annotations

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

from docmeld.gold.deepseek_client import DeepSeekClient, call_with_retry
from docmeld.utils.env_loader import load_env

logger = logging.getLogger("docmeld")

MAX_CONTENT_CHARS = 30000
DEFAULT_WORKERS = 10

SUMMARIZE_PROMPT = """你是一位资深AI研究员，擅长解读前沿论文并输出结构化中文总结。

请解读以下论文内容，输出格式清晰的中文总结Markdown文章。

要求：
1. 第一行：论文原始文件名
2. 第二行空行
3. 第三行：论文中文标题 + 一段话概括（100-200字，涵盖核心贡献、方法、结果）
4. 正文按以下结构组织（根据论文实际内容灵活调整）：
   - 一、研究背景与现存问题
   - 二、模型/方法核心贡献（列出3-5个要点）
   - 三、核心技术体系（分小节详细展开，每个技术点说清楚原理和作用）
   - 四、实验验证（实验设置、核心结果、消融实验）
   - 五、应用场景
   - 六、局限性与未来工作
   - 七、整体结论（一段话总结）

格式要求：
- 使用中文，技术术语保留英文原文并用括号标注
- 用Markdown格式，标题用中文数字（一、二、三...），小节用（一）（二）...
- 关键数字、指标、模型名称要准确引用
- 不要输出```markdown代码块标记，直接输出Markdown内容

论文内容：
"""


def assemble_paper_content(jsonl_path: Path) -> str:
    """Read silver JSONL and concatenate page_content into full markdown."""
    pages: List[str] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            content = page.get("page_content", "")
            if content:
                pages.append(content)
    return "\n\n---\n\n".join(pages)


def _call_summarize_api(client: DeepSeekClient, prompt: str) -> str:
    """Make the API call for summarization."""
    from langchain_deepseek import ChatDeepSeek

    kwargs: Dict = {
        "model": "deepseek-chat",
        "temperature": 1.2,
        "api_key": client.api_key,
    }
    if client.endpoint:
        kwargs["base_url"] = client.endpoint

    llm = ChatDeepSeek(**kwargs)
    response = llm.invoke(prompt)
    text = str(response.content).strip()

    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    return text


def summarize_one(client: DeepSeekClient, task: Dict) -> Dict:
    """Summarize a single paper. Returns task dict with 'ok' field."""
    jsonl_path = task["jsonl"]
    pdf_name = task["pdf_name"]
    output_path = task["output"]

    if output_path.exists():
        return {**task, "ok": True, "skipped": True}

    full_content = assemble_paper_content(jsonl_path)
    if not full_content:
        return {**task, "ok": False, "error": "empty content"}

    truncated = full_content[:MAX_CONTENT_CHARS]
    prompt = SUMMARIZE_PROMPT + truncated

    try:
        response = call_with_retry(
            lambda: _call_summarize_api(client, prompt),
            max_retries=3,
            base_delay=2.0,
        )

        if not response.startswith(pdf_name):
            response = f"{pdf_name}\n\n{response}"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response)
            if not response.endswith("\n"):
                f.write("\n")

        return {**task, "ok": True, "skipped": False}

    except Exception as e:
        return {**task, "ok": False, "error": str(e)}


def collect_papers(folder: Path) -> List[Dict]:
    """Scan folder for papers needing summarization."""
    papers = []
    for cat_dir in sorted(folder.iterdir()):
        if not cat_dir.is_dir():
            continue
        # Skip non-category dirs (files, hidden dirs)
        if cat_dir.name.startswith(".") or cat_dir.name.startswith("_"):
            continue

        for subdir in sorted(cat_dir.iterdir()):
            if not subdir.is_dir():
                continue
            jsonl_files = [
                f for f in subdir.glob("*.jsonl")
                if not f.name.endswith("_gold.jsonl")
            ]
            if not jsonl_files:
                continue
            jsonl_path = jsonl_files[0]

            # Match PDF by hash suffix
            hash6 = subdir.name.rsplit("_", 1)[-1] if "_" in subdir.name else ""
            pdfs = list(cat_dir.glob("*.pdf")) + list(cat_dir.glob("*.PDF"))
            matched_pdf = None
            for pdf in pdfs:
                from docmeld.bronze.filename_sanitizer import calculate_hash
                if calculate_hash(str(pdf)) == hash6:
                    matched_pdf = pdf
                    break

            pdf_name = matched_pdf.name if matched_pdf else f"{subdir.name}.pdf"
            md_name = Path(pdf_name).stem + "_summary.md"
            output_path = cat_dir / md_name

            papers.append({
                "jsonl": jsonl_path,
                "pdf_name": pdf_name,
                "output": output_path,
                "category": cat_dir.name,
            })

    return papers


def batch_summarize(folder_path: str, workers: int = DEFAULT_WORKERS) -> None:
    """Summarize all papers with concurrent API calls."""
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Error: folder not found: {folder_path}")
        sys.exit(1)

    env = load_env(require_api_key=True)
    client = DeepSeekClient(
        api_key=env["DEEPSEEK_API_KEY"],
        endpoint=env.get("DEEPSEEK_API_ENDPOINT"),
    )

    papers = collect_papers(folder)
    total = len(papers)
    pending = [p for p in papers if not p["output"].exists()]
    done = total - len(pending)

    print(f"Found {total} papers, {done} already done, {len(pending)} remaining")
    print(f"Workers: {workers}")

    if not pending:
        print("All papers already summarized.")
        return

    success = 0
    failed = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(summarize_one, client, task): task
            for task in pending
        }

        for future in as_completed(futures):
            result = future.result()
            idx = done + success + failed + 1
            name = result["pdf_name"][:65]

            if result.get("ok"):
                success += 1
                print(f"[{idx}/{total}] ✓ {name}")
            else:
                failed += 1
                err = result.get("error", "unknown")
                print(f"[{idx}/{total}] ✗ {name} — {err}")

    elapsed = time.time() - start
    print(f"\nDone: {success} summarized, {failed} failed, {elapsed:.0f}s")
    print(f"Avg: {elapsed / max(success + failed, 1):.1f}s per paper")


if __name__ == "__main__":
    import argparse

    from docmeld.utils.logging import setup_logging
    setup_logging()

    parser = argparse.ArgumentParser(description="Batch summarize papers via DeepSeek")
    parser.add_argument("folder", help="Path to categorized folder")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"Concurrent API calls (default: {DEFAULT_WORKERS})")
    args = parser.parse_args()

    batch_summarize(args.folder, workers=args.workers)
