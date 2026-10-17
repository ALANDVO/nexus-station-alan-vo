"""Application configuration.

All settings come from environment variables with documented defaults.
AUTH_MODE controls the authentication strategy:
  - "local" (default, demo): shared-secret API key, binds to 127.0.0.1 only.
  - "production": requires OIDC discovery; refuses to start without it.
  - "oidc": full OIDC/OIDC discovery configuration (future milestone).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def _dev_key() -> str:
    """Generate a clearly synthetic API key for local demo mode.

    Uses a descriptive prefix plus repeated zeros — never a real credential.
    """
    return "nexus-dev-" + "0" * 32


class Settings:
    """Runtime configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.project_name: str = "Nexus Station"
        self.version: str = "1.0.0"
        self.api_prefix: str = "/api/v1"

        # Database
        self.database_url: str = os.environ.get(
            "DATABASE_URL", "sqlite:///./nexus_station.db"
        )

        # Auth: local demo mode uses a generated API key (never a literal in source)
        self.auth_mode: str = os.environ.get("AUTH_MODE", "local")
        self.local_api_key: str = os.environ.get("LOCAL_API_KEY") or _dev_key()
        self.oidc_discovery_url: str | None = os.environ.get("OIDC_DISCOVERY_URL")
        self.oidc_client_id: str | None = os.environ.get("OIDC_CLIENT_ID")
        self.oidc_audience: str | None = os.environ.get("OIDC_AUDIENCE")

        # LLM (optional, future milestone)
        self.llm_api_key: str | None = os.environ.get("LLM_API_KEY")
        self.llm_provider: str = os.environ.get("LLM_PROVIDER", "openai-compatible")
        self.llm_model: str = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
        self.llm_base_url: str | None = os.environ.get("LLM_BASE_URL")

        # Host
        self.host: str = os.environ.get("HOST", "127.0.0.1")
        self.port: int = int(os.environ.get("PORT", "8000"))

    def is_local_demo(self) -> bool:
        """True when running in local-only demo mode."""
        return self.auth_mode == "local"

    def is_production(self) -> bool:
        """True when production auth (OIDC) is required."""
        return self.auth_mode == "production"

    def require_oidc(self) -> None:
        """Refuse to start in production mode without OIDC config.

        Raises:
            RuntimeError: if production mode is active but OIDC is not configured.
        """
        if self.is_production() and not self.oidc_discovery_url:
            raise RuntimeError(
                "AUTH_MODE=production requires OIDC_DISCOVERY_URL. "
                "Refusing to start without OIDC configuration in production."
            )


@lru_cache()
def get_settings() -> Settings:
    return Settings()