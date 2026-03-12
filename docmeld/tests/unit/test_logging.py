"""Unit tests for timestamped logging utility."""
import os
import re
import logging
import pytest
from pathlib import Path


class TestSetupLogging:
    def test_creates_log_file_in_cwd(self, tmp_path: Path) -> None:
        from docmeld.utils.logging import setup_logging

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            logger = setup_logging()
            log_files = list(tmp_path.glob("docmeld_*.log"))
            assert len(log_files) == 1
            logger.handlers.clear()
        finally:
            os.chdir(original_cwd)

    def test_log_filename_format(self, tmp_path: Path) -> None:
        from docmeld.utils.logging import setup_logging

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            logger = setup_logging()
            log_files = list(tmp_path.glob("docmeld_*.log"))
            name = log_files[0].name
            pattern = r"^docmeld_\d{8}_\d{6}\.log$"
            assert re.match(pattern, name), f"Log filename {name} doesn't match expected pattern"
            logger.handlers.clear()
        finally:
            os.chdir(original_cwd)

    def test_log_levels(self, tmp_path: Path) -> None:
        from docmeld.utils.logging import setup_logging

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            logger = setup_logging()
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")

            log_files = list(tmp_path.glob("docmeld_*.log"))
            content = log_files[0].read_text()
            assert "info message" in content
            assert "warning message" in content
            assert "error message" in content
            logger.handlers.clear()
        finally:
            os.chdir(original_cwd)

    def test_returns_logger_instance(self, tmp_path: Path) -> None:
        from docmeld.utils.logging import setup_logging

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            logger = setup_logging()
            assert isinstance(logger, logging.Logger)
            logger.handlers.clear()
        finally:
            os.chdir(original_cwd)
