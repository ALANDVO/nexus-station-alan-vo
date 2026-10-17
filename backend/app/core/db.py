"""Database initialization and persistence helpers.

Uses SQLite (persistent file) with parameterized SQL via sqlite3.
The schema is created idempotently on startup via init_db().
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import Settings


def _utc_now() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    tags        TEXT NOT NULL DEFAULT '[]',
    agent_vendor TEXT NOT NULL DEFAULT 'unknown',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action      TEXT NOT NULL,
    resource    TEXT NOT NULL,
    resource_id TEXT,
    detail      TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS imports (
    id          TEXT PRIMARY KEY,
    source_bundle TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    conflict    TEXT NOT NULL DEFAULT 'new'
);
"""


def get_db_path(database_url: str) -> str:
    """Extract the file path from a sqlite:/// URL."""
    if database_url.startswith("sqlite:///"):
        path = database_url[len("sqlite:///"):]
        if path.startswith("./"):
            from pathlib import Path
            return str(Path.cwd() / path[2:])
        return path
    raise ValueError(f"Unsupported database URL: {database_url}")


def init_db(settings: Settings) -> None:
    """Create database tables if they do not exist."""
    db_path = get_db_path(settings.database_url)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def get_connection(settings: Settings) -> sqlite3.Connection:
    """Return a SQLite connection with row factory."""
    db_path = get_db_path(settings.database_url)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def log_audit(
    conn: sqlite3.Connection,
    action: str,
    resource: str,
    resource_id: str | None = None,
    detail: str | None = None,
) -> int:
    """Write an audit log entry and return its row id."""
    conn.execute(
        """
        INSERT INTO audit_log (action, resource, resource_id, detail, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (action, resource, resource_id, detail, _utc_now()),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def generate_id() -> str:
    """Generate a UUID4 string for a new record."""
    return str(uuid.uuid4())


def _parse_tags_from_db(value: Any) -> list[str]:
    """Parse tags from database storage format."""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            return json.loads(value) if value else []
        except (json.JSONDecodeError, ValueError):
            return []
    if isinstance(value, list):
        return [str(t) for t in value]
    return []


def serialize_tags(tags: list[str]) -> str:
    """Serialize tags list to JSON string for database storage."""
    return json.dumps(tags)