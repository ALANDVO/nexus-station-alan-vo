"""API dependency providers.

Provides the database connection and service instances per request.
Also provides authenticated user role requirements.
"""
from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from fastapi import Depends

from ..core.config import Settings, get_settings
from ..core.db import get_connection
from ..core.auth import require_role
from ..services.handoff import HandoffService
from ..services.ranking import TFIDFRanker
from ..services.store import MemoryStore

if TYPE_CHECKING:
    from ..services.llm_advisory import LLMAdvisoryService


def get_db(
    settings: Settings = Depends(get_settings),
) -> sqlite3.Connection:
    """Per-request SQLite connection."""
    return get_connection(settings)


def get_store(
    conn: sqlite3.Connection = Depends(get_db),
) -> MemoryStore:
    """Per-request MemoryStore instance."""
    return MemoryStore(conn)


def get_ranker() -> TFIDFRanker:
    """Return a TF-IDF ranker (per-request scope)."""
    return TFIDFRanker()


def get_handoff_service(
    conn: sqlite3.Connection = Depends(get_db),
) -> HandoffService:
    """Per-request HandoffService instance."""
    return HandoffService(conn)


def get_llm_advisory_service(
    settings: Settings = Depends(get_settings),
) -> LLMAdvisoryService:
    """Per-request LLM advisory service instance."""
    from ..services.llm_advisory import LLMAdvisoryService
    return LLMAdvisoryService(settings)


# Pre-built role requirements for reuse across routers
RequireAnalyst = require_role("analyst")
RequireAdmin = require_role("admin")
