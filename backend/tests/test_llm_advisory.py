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
