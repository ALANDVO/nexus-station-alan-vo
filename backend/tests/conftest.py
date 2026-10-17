"""Shared pytest fixtures for backend tests."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import sqlite3
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.core.db import SCHEMA_SQL, init_db, get_connection
from app.main import create_app


def _fresh_db_path() -> str:
    """Return a path for a fresh temporary SQLite database."""
    return tempfile.mktemp(suffix=".db")


def _init_schema(db_path: str) -> None:
    """Initialize the database schema at the given path."""
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """Provide test settings with a temp SQLite database and local auth."""
    db_path = str(tmp_path / "test.db")
    settings = Settings()
    settings.database_url = f"sqlite:///{db_path}"
    # Clear cached singleton so get_settings() returns our test settings
    get_settings.cache_clear()
    init_db(settings)
    yield settings


@pytest.fixture
def db_path(test_settings: Settings) -> str:
    """Extract the database file path from settings."""
    return test_settings.database_url.replace("sqlite:///", "")


@pytest.fixture
def db_conn(db_path: str) -> sqlite3.Connection:
    """Provide a direct SQLite connection for test assertions."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def app(test_settings: Settings):
    """Create a FastAPI test app with test settings."""
    # get_settings is cached; clear and patch
    get_settings.cache_clear()

    def _override_settings():
        return test_settings

    application = create_app(test_settings)
    application.dependency_overrides[get_settings] = _override_settings
    yield application
    application.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
def client(app, test_settings: Settings):
    """Provide an authenticated httpx AsyncClient for the test app."""
    transport = ASGITransport(app=app)
    test_client = AsyncClient(transport=transport, base_url="http://test")
    test_client.headers["Authorization"] = f"Bearer {test_settings.local_api_key}"
    yield test_client
    import asyncio
    try:
        asyncio.get_running_loop()
        asyncio.ensure_future(test_client.aclose())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(test_client.aclose())
        loop.close()


@pytest.fixture
def client_no_auth(app):
    """Provide an httpx client without auth headers."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def auth_headers(test_settings: Settings) -> dict:
    """Standard auth headers for tests."""
    return {"Authorization": f"Bearer {test_settings.local_api_key}"}


@pytest.fixture
def sample_memory_data() -> dict:
    """Sample memory data for tests."""
    return {
        "title": "Fix auth bug in login flow",
        "content": "The login flow was failing because the OAuth callback "
                   "was not validating the state parameter correctly. Fixed by "
                   "adding state validation in the callback handler. Issue #1280.",
        "tags": ["auth", "bugfix", "claude-code"],
        "agent_vendor": "claude-code",
    }


@pytest.fixture
def another_memory_data() -> dict:
    """Another sample memory for ranking tests."""
    return {
        "title": "Database migration for session table",
        "content": "Added a new sessions table to track user session state "
                   "across agent restarts. Includes TTL-based cleanup and "
                   "session metadata. Issue #1261.",
        "tags": ["database", "migration", "codex"],
        "agent_vendor": "codex",
    }