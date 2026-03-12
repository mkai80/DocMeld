"""Unit tests for environment loader."""
import os
import pytest
from pathlib import Path


class TestLoadEnv:
    def test_loads_api_key_from_env_file(self, tmp_path: Path) -> None:
        from docmeld.utils.env_loader import load_env

        env_file = tmp_path / ".env.local"
        env_file.write_text("DEEPSEEK_API_KEY=test_key_123\n")

        result = load_env(env_path=str(env_file))
        assert result["DEEPSEEK_API_KEY"] == "test_key_123"

    def test_missing_api_key_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from docmeld.utils.env_loader import load_env

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        env_file = tmp_path / ".env.local"
        env_file.write_text("OTHER_VAR=value\n")

        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            load_env(env_path=str(env_file), require_api_key=True)

    def test_optional_endpoint(self, tmp_path: Path) -> None:
        from docmeld.utils.env_loader import load_env

        env_file = tmp_path / ".env.local"
        env_file.write_text(
            "DEEPSEEK_API_KEY=key123\nDEEPSEEK_API_ENDPOINT=https://custom.api.com\n"
        )

        result = load_env(env_path=str(env_file))
        assert result["DEEPSEEK_API_KEY"] == "key123"
        assert result["DEEPSEEK_API_ENDPOINT"] == "https://custom.api.com"

    def test_missing_env_file_no_error_when_not_required(self, tmp_path: Path) -> None:
        from docmeld.utils.env_loader import load_env

        result = load_env(env_path=str(tmp_path / "nonexistent"), require_api_key=False)
        assert isinstance(result, dict)
