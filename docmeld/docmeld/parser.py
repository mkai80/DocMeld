"""DocMeld main parser - orchestrates the full pipeline."""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from docmeld.bronze.processor import BronzeProcessor
from docmeld.silver.page_models import BronzeResult, CategorizeResult, GoldResult, ProcessingResult, SilverResult
from docmeld.silver.processor import SilverProcessor

logger = logging.getLogger("docmeld")


class DocMeldParser:
    """Main entry point for the DocMeld pipeline.

    Supports processing a single PDF file or a folder of PDFs
    through bronze, silver, and gold stages.
    """

    def __init__(self, path: str, output_dir: Optional[str] = None, backend: str = "pymupdf") -> None:
        self.path = path
        self.output_dir = output_dir
        self.backend = backend
        self._is_folder = Path(path).is_dir()

    def process_bronze(self) -> BronzeResult | ProcessingResult:
        """Run bronze stage only."""
        processor = BronzeProcessor()
        if self._is_folder:
            return processor.process_folder(self.path, backend=self.backend)
        return processor.process_file(self.path, backend=self.backend)

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
            folder_result = bronze_processor.process_folder(self.path, backend=self.backend)
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
            bronze_result = bronze_processor.process_file(self.path, backend=self.backend)
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

    def process_categorize(self, reorganize: bool = False) -> CategorizeResult:
        """Run full pipeline + categorization on a folder of PDFs.

        Processes all PDFs through bronze→silver→gold, aggregates gold
        metadata, clusters papers into categories via DeepSeek, and
        writes categories.json. Optionally reorganizes files.

        Args:
            reorganize: If True, move files into category subdirectories.

        Returns:
            CategorizeResult with index path and statistics.
        """
        if not self._is_folder:
            raise ValueError("process_categorize() requires a folder path, not a single file")

        folder = Path(self.path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {self.path}")

        pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
        if not pdf_files:
            logger.warning(f"No PDFs found in {self.path}")
            return CategorizeResult(
                index_path="",
                total_papers=0,
                total_categories=0,
                papers_failed=0,
                reorganized=False,
            )

        # Step 1: Run full pipeline (bronze → silver → gold)
        logger.info(f"Processing {len(pdf_files)} PDFs through full pipeline...")
        self.process_all()

        # Step 2: Aggregate gold metadata
        from docmeld.categorize.aggregator import aggregate_paper_metadata

        papers = aggregate_paper_metadata(self.path)
        if not papers:
            logger.warning("No gold metadata found to categorize")
            return CategorizeResult(
                index_path="",
                total_papers=0,
                total_categories=0,
                papers_failed=0,
                reorganized=False,
            )

        # Step 3: Categorize via DeepSeek
        from docmeld.categorize.categorizer import categorize_papers
        from docmeld.gold.deepseek_client import DeepSeekClient
        from docmeld.utils.env_loader import load_env

        env = load_env(require_api_key=True)
        client = DeepSeekClient(
            api_key=env["DEEPSEEK_API_KEY"],
            endpoint=env.get("DEEPSEEK_API_ENDPOINT"),
        )

        categories = categorize_papers(papers, client)

        # Step 4: Write categories.json
        from docmeld.categorize.index_writer import write_category_index

        index_path = write_category_index(self.path, papers, categories)

        # Step 5: Optionally reorganize
        if reorganize:
            from docmeld.categorize.reorganizer import reorganize_by_category

            reorganize_by_category(self.path)

        return CategorizeResult(
            index_path=index_path,
            total_papers=len(papers),
            total_categories=len(categories),
            papers_failed=0,
            reorganized=reorganize,
        )

    def process_prd(self) -> "PrdResult":
        """Generate a PRD from a single PDF research paper.

        Processes the PDF through bronze→silver, then sends aggregated
        content to DeepSeek to generate a structured PRD markdown file.

        Returns:
            PrdResult with output path and section count.
        """
        if self._is_folder:
            raise ValueError("process_prd() requires a single PDF file, not a folder")

        from docmeld.prd.generator import generate_prd
        from docmeld.prd.models import PrdResult

        # Step 1: Bronze
        bronze_result = self.process_bronze()
        if not hasattr(bronze_result, "output_path"):
            raise RuntimeError("Bronze processing failed")

        # Step 2: Silver
        silver_result = self.process_silver(bronze_result.output_path)

        # Step 3: Generate PRD
        from docmeld.gold.deepseek_client import DeepSeekClient
        from docmeld.utils.env_loader import load_env

        env = load_env(require_api_key=True)
        client = DeepSeekClient(
            api_key=env["DEEPSEEK_API_KEY"],
            endpoint=env.get("DEEPSEEK_API_ENDPOINT"),
        )

        return generate_prd(
            silver_jsonl_path=silver_result.output_path,
            client=client,
            source_pdf=Path(self.path).name,
        )
