"""DocMeld main parser - orchestrates the full pipeline."""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from docmeld.bronze.processor import BronzeProcessor
from docmeld.silver.page_models import BronzeResult, GoldResult, ProcessingResult, SilverResult
from docmeld.silver.processor import SilverProcessor

logger = logging.getLogger("docmeld")


class DocMeldParser:
    """Main entry point for the DocMeld pipeline.

    Supports processing a single PDF file or a folder of PDFs
    through bronze, silver, and gold stages.
    """

    def __init__(self, path: str, output_dir: Optional[str] = None) -> None:
        self.path = path
        self.output_dir = output_dir
        self._is_folder = Path(path).is_dir()

    def process_bronze(self) -> BronzeResult | ProcessingResult:
        """Run bronze stage only."""
        processor = BronzeProcessor()
        if self._is_folder:
            return processor.process_folder(self.path)
        return processor.process_file(self.path)

    def process_silver(self, bronze_json_path: str) -> SilverResult:
        """Run silver stage on a bronze JSON file."""
        processor = SilverProcessor()
        return processor.process(bronze_json_path)

    def process_gold(self, silver_jsonl_path: str) -> GoldResult:
        """Run gold stage on a silver JSONL file."""
        from docmeld.gold.processor import GoldProcessor
        from docmeld.utils.env_loader import load_env

        env = load_env(require_api_key=True)
        processor = GoldProcessor(
            api_key=env["DEEPSEEK_API_KEY"],
            endpoint=env.get("DEEPSEEK_API_ENDPOINT"),
            temperature=1.0,
        )
        return processor.process(silver_jsonl_path)

    def process_all(self) -> ProcessingResult:
        """Run the full pipeline: bronze → silver → gold.

        For folder input, processes all PDFs through all stages.
        For single file, processes through all three stages.
        """
        start_time = time.time()
        bronze_processor = BronzeProcessor()
        silver_processor = SilverProcessor()

        if self._is_folder:
            folder_result = bronze_processor.process_folder(self.path)
            # Process silver and gold for each successful bronze output
            folder = Path(self.path)
            for subdir in sorted(folder.iterdir()):
                json_files = list(subdir.glob("*.json")) if subdir.is_dir() else []
                for json_file in json_files:
                    try:
                        silver_result = silver_processor.process(str(json_file))
                        try:
                            self.process_gold(silver_result.output_path)
                        except Exception as e:
                            logger.warning(f"Gold stage skipped for {json_file.name}: {e}")
                    except Exception as e:
                        logger.warning(f"Silver stage failed for {json_file.name}: {e}")

            elapsed = time.time() - start_time
            folder_result.processing_time_seconds = round(elapsed, 2)
            return folder_result
        else:
            bronze_result = bronze_processor.process_file(self.path)
            silver_result = silver_processor.process(bronze_result.output_path)

            gold_failed = False
            try:
                self.process_gold(silver_result.output_path)
            except Exception as e:
                logger.warning(f"Gold stage skipped: {e}")
                gold_failed = True

            elapsed = time.time() - start_time
            return ProcessingResult(
                total_files=1,
                successful=1,
                failed=0,
                failures=[],
                processing_time_seconds=round(elapsed, 2),
                output_directory=bronze_result.output_dir,
                log_file="",
            )
