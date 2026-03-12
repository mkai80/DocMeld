"""Unit tests for DeepSeek client."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest


class TestDeepSeekClient:
    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from docmeld.gold.deepseek_client import DeepSeekClient

        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            DeepSeekClient(api_key="")

    def test_creates_with_valid_key(self) -> None:
        from docmeld.gold.deepseek_client import DeepSeekClient

        client = DeepSeekClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.temperature == 1.0

    def test_custom_temperature(self) -> None:
        from docmeld.gold.deepseek_client import DeepSeekClient

        client = DeepSeekClient(api_key="key", temperature=0.5)
        assert client.temperature == 0.5

    def test_extract_metadata_returns_description_and_keywords(self) -> None:
        from docmeld.gold.deepseek_client import DeepSeekClient

        client = DeepSeekClient(api_key="test_key")

        mock_response = MagicMock()
        mock_response.content = '{"description": "Test page about revenue", "keywords": ["revenue", "growth"]}'

        with patch.object(client, "_call_api", return_value={"description": "Test page about revenue", "keywords": ["revenue", "growth"]}):
            result = client.extract_metadata("Some page content about revenue growth")
            assert "description" in result
            assert "keywords" in result
            assert isinstance(result["keywords"], list)

    def test_retry_on_failure(self) -> None:
        from docmeld.gold.deepseek_client import call_with_retry

        call_count = 0

        def failing_then_success() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("API unavailable")
            return "success"

        result = call_with_retry(failing_then_success, max_retries=3, base_delay=0.01)
        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self) -> None:
        from docmeld.gold.deepseek_client import call_with_retry

        def always_fails() -> str:
            raise ConnectionError("API unavailable")

        with pytest.raises(ConnectionError):
            call_with_retry(always_fails, max_retries=3, base_delay=0.01)
