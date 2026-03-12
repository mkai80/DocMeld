"""Bronze stage processor - PDF to structured JSON elements."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional

from docmeld.bronze.element_extractor import extract_elements
from docmeld.bronze.filename_sanitizer import get_output_name
from docmeld.silver.page_models import BronzeResult, ProcessingFailure, ProcessingResult

logger = logging.getLogger("docmeld")


class BronzeProcessor:
    """Orchestrates bronze-level PDF processing."""

    def process_file(self, pdf_path: str) -> BronzeResult:
        """Process a single PDF file into structured JSON elements.

        Creates an output folder next to the PDF, extracts elements,
        and saves them as a JSON file.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            BronzeResult with output paths and statistics.
        """
        import fitz

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        output_name = get_output_name(pdf_path)
        output_dir = path.parent / output_name
        output_json = output_dir / f"{output_name}.json"

        # Idempotency check
        if output_json.exists():
            with open(output_json) as f:
                elements = json.load(f)
            page_nos = {e.get("page_no", 0) for e in elements}
            return BronzeResult(
                output_path=str(output_json),
                output_dir=str(output_dir),
                element_count=len(elements),
                page_count=len(page_nos),
                skipped=True,
            )

        # Create output directory
        output_dir.mkdir(exist_ok=True)

        # Get page count
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()

        # Extract elements
        elements = extract_elements(pdf_path, str(output_dir))

        # Save JSON
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(elements, f, indent=4, ensure_ascii=False)

        logger.info(f"Bronze: {path.name} → {len(elements)} elements, {page_count} pages")

        return BronzeResult(
            output_path=str(output_json),
            output_dir=str(output_dir),
            element_count=len(elements),
            page_count=page_count,
            skipped=False,
        )

    def process_folder(self, folder_path: str) -> ProcessingResult:
        """Process all PDF files in a folder (fail-fast disabled).

        Continues processing remaining files even if one fails.

        Args:
            folder_path: Path to folder containing PDF files.

        Returns:
            ProcessingResult with summary statistics.
        """
        start_time = time.time()
        folder = Path(folder_path)

        if not folder.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder_path}")

        pdf_files = sorted(folder.glob("*.pdf"))
        total = len(pdf_files)
        successful = 0
        failed = 0
        failures: list[ProcessingFailure] = []

        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"Processing {i}/{total}: {pdf_file.name}")
            try:
                self.process_file(str(pdf_file))
                successful += 1
            except Exception as e:
                failed += 1
                failures.append(
                    ProcessingFailure(filename=pdf_file.name, error=str(e))
                )
                logger.error(f"Failed to process {pdf_file.name}: {e}")

        elapsed = time.time() - start_time

        return ProcessingResult(
            total_files=total,
            successful=successful,
            failed=failed,
            failures=failures,
            processing_time_seconds=round(elapsed, 2),
            output_directory=str(folder),
            log_file="",
        )
