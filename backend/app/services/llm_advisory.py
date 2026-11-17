"""LLM advisory service with optional external adapters.

Exports a simple LLM advisory explanation for a memory record.
The adapter used is determined by environment variables and
supports OpenAI-compatible endpoints, Anthropic, and Gemini.
When no key is set, returns an empty advisory (no external call).
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import Depends
import httpx

from ..core.config import Settings, get_settings
from ..models.memory import Memory


class LLMAdapter:
    """Abstract adapter for LLM-based advisory generation."""
    async def generate_advisory(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatibleAdapter(LLMAdapter):
    """Adapter for OpenAI-compatible endpoints (including Azure, etc.)."""
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate_advisory(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 150,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic's Claude models."""
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate_advisory(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.model,
                    "max_tokens": 150,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]


class GeminiAdapter(LLMAdapter):
    """Adapter for Google Gemini models."""
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate_advisory(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 150, "temperature": 0},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]


class LLMAdvisoryService:
    """Service that coordinates the LLM adapter for advisory explanations."""
    def __init__(self, settings: Settings):
        self.settings = settings
        self.adapter: Optional[LLMAdapter] = self._build_adapter()

    def _build_adapter(self) -> Optional[LLMAdapter]:
        if not self.settings.llm_api_key:
            return None
        provider = self.settings.llm_provider
        if provider == "openai-compatible":
            base_url = self.settings.llm_base_url or "https://api.openai.com/v1"
            return OpenAICompatibleAdapter(
                self.settings.llm_api_key,
                base_url,
                self.settings.llm_model,
            )
        if provider == "anthropic":
            return AnthropicAdapter(self.settings.llm_api_key, self.settings.llm_model)
        if provider == "gemini":
            return GeminiAdapter(self.settings.llm_api_key, self.settings.llm_model)
        # fallback to a generic HTTP POST to base_url if provider is custom
        # (implementation omitted for brevity)
        return None

    async def generate_advisory(self, prompt: str) -> str:
        if self.adapter is None:
            return ""  # No key configured; return empty advisory
        return await self.adapter.generate_advisory(prompt)


def get_llm_advisory_service(
    settings: Settings = Depends(get_settings),
) -> LLMAdvisoryService:
    """FastAPI dependency to provide an LLM advisory service instance."""
    return LLMAdvisoryService(settings)
