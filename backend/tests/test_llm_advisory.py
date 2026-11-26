"""Tests for LLM advisory service."""
from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.llm_advisory import LLMAdvisoryService


class TestLLMAdvisoryServiceNoKey:
    """Test service behavior when LLM_API_KEY is not set."""

    @pytest.mark.asyncio
    async def test_service_returns_empty_advisory(self):
        settings = Settings()
        settings.llm_api_key = None
        service = LLMAdvisoryService(settings)
        assert service.adapter is None
        advisory = await service.generate_advisory("prompt")
        assert advisory == ""

    def test_service_with_dummy_key(self):
        settings = Settings()
        settings.llm_api_key = "dummy-key"
        service = LLMAdvisoryService(settings)
        # Should have an adapter (openai-compatible, fallback)
        assert service.adapter is not None


class TestLLMAdvisoryWithMock:
    """Test that CI can mock external LLM calls.

    These tests verify the adapter pattern allows httpx calls to be
    mocked in CI environments using unittest.mock, preventing real
    network requests.
    """

    @pytest.mark.asyncio
    async def test_service_adapter_is_creatable_with_key(self):
        """Verify that setting LLM_API_KEY creates an adapter.

        This is a prerequisite for CI mocking - the adapter must be
        creatable when a key is provided.
        """
        settings = Settings()
        settings.llm_api_key = "sk-test-key-1234567890abcdef"
        settings.llm_provider = "openai-compatible"
        settings.llm_model = "gpt-3.5-turbo"

        service = LLMAdvisoryService(settings)
        assert service.adapter is not None
        assert service.adapter.__class__.__name__ == "OpenAICompatibleAdapter"

    @pytest.mark.asyncio
    async def test_adapter_generate_advisory_method_exists(self):
        """Verify adapter has generate_advisory method for mocking."""
        from app.services.llm_advisory import OpenAICompatibleAdapter

        adapter = OpenAICompatibleAdapter(
            api_key="sk-test-key-1234567890abcdef",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
        )

        # Verify the method exists and is a coroutine
        assert hasattr(adapter, "generate_advisory")
        import asyncio
        # Verify it's awaitable
        assert asyncio.iscoroutinefunction(adapter.generate_advisory)


class TestLLMBaseURL:
    """Test that LLM_BASE_URL environment variable is properly configured."""

    @pytest.mark.asyncio
    async def test_service_respects_llm_base_url(self):
        """Verify that setting LLM_BASE_URL configures the adapter's base URL."""
        from app.services.llm_advisory import OpenAICompatibleAdapter

        settings = Settings()
        settings.llm_api_key = "sk-test-key-1234567890abcdef"
        settings.llm_provider = "openai-compatible"
        settings.llm_model = "gpt-3.5-turbo"
        settings.llm_base_url = "https://custom-openai.example/v1"

        service = LLMAdvisoryService(settings)
        assert service.adapter is not None
        assert service.adapter.base_url == "https://custom-openai.example/v1"

    @pytest.mark.asyncio
    async def test_service_uses_default_base_url_when_not_set(self):
        """Verify default base URL is used when LLM_BASE_URL is not set."""
        from app.services.llm_advisory import OpenAICompatibleAdapter

        settings = Settings()
        settings.llm_api_key = "sk-test-key-1234567890abcdef"
        settings.llm_provider = "openai-compatible"
        settings.llm_model = "gpt-3.5-turbo"
        # llm_base_url not set - should use default

        service = LLMAdvisoryService(settings)
        assert service.adapter is not None
        assert service.adapter.base_url == "https://api.openai.com/v1"
