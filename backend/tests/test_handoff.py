"""Tests for the handoff bundle export/import service."""
from __future__ import annotations

import json

import pytest
import sqlite3

from app.core.db import SCHEMA_SQL
from app.models.bundle import BundleImportRequest
from app.models.memory import MemoryCreate
from app.services.handoff import HandoffService
from app.services.store import MemoryStore


def _fresh_services() -> tuple[sqlite3.Connection, MemoryStore, HandoffService]:
    """Create fresh in-memory services for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    store = MemoryStore(conn)
    handoff = HandoffService(conn)
    return conn, store, handoff


class TestExport:
    def test_export_by_ids(self):
        conn, store, handoff = _fresh_services()
        m1 = store.create(MemoryCreate(title="m1", content="c1", agent_vendor="claude"))
        m2 = store.create(MemoryCreate(title="m2", content="c2", agent_vendor="codex"))

        bundle = handoff.export_bundle(
            source_vendor="claude", destination_vendor="codex",
            memory_ids=[m1.id],
        )
        assert bundle.meta.source_agent_vendor == "claude"
        assert bundle.meta.destination_agent_vendor == "codex"
        assert bundle.meta.memory_count == 1
        assert len(bundle.memories) == 1
        assert bundle.memories[0].title == "m1"
        conn.close()

    def test_export_all_with_filters(self):
        conn, store, handoff = _fresh_services()
        store.create(MemoryCreate(
            title="m1", content="c1", tags=["important"], agent_vendor="claude"
        ))
        store.create(MemoryCreate(
            title="m2", content="c2", tags=["other"], agent_vendor="codex"
        ))

        bundle = handoff.export_bundle(
            source_vendor="claude", destination_vendor="codex",
            filters={"agent_vendor": "claude"},
        )
        assert bundle.meta.memory_count == 1
        assert bundle.memories[0].agent_vendor == "claude"
        conn.close()

    def test_export_writes_audit(self):
        conn, store, handoff = _fresh_services()
        store.create(MemoryCreate(title="m1", content="c1", agent_vendor="v"))
        handoff.export_bundle("v1", "v2")
        count = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'handoff.export'"
        ).fetchone()[0]
        assert count == 1
        conn.close()


class TestImport:
    def test_import_creates_new_memories(self):
        conn, store, handoff = _fresh_services()
        from app.models.bundle import Bundle, BundleMeta, BundleMemory
        from datetime import datetime, timezone

        bundle = Bundle(
            meta=BundleMeta(
                source_agent_vendor="claude", destination_agent_vendor="codex",
                exported_at=datetime.now(timezone.utc), memory_count=1,
            ),
            memories=[
                BundleMemory(
                    title="imported mem", content="great content",
                    tags=["test"], agent_vendor="claude",
                )
            ],
        )
        req = BundleImportRequest(bundle_id="bundle-1", conflict_resolution="new")
        result = handoff.import_bundle(req, bundle)
        assert result.imported_count == 1
        assert result.skipped_count == 0
        assert result.bundle_id == "bundle-1"
        conn.close()

    def test_import_skip_conflict(self):
        conn, store, handoff = _fresh_services()
        from app.models.bundle import Bundle, BundleMeta, BundleMemory
        from datetime import datetime, timezone

        # Create an existing memory
        existing = store.create(MemoryCreate(
            title="orig", content="shared content", agent_vendor="v"
        ))

        bundle = Bundle(
            meta=BundleMeta(
                source_agent_vendor="v", destination_agent_vendor="v2",
                exported_at=datetime.now(timezone.utc), memory_count=1,
            ),
            memories=[
                BundleMemory(
                    title="orig", content="shared content",
                    tags=["x"], agent_vendor="v",
                )
            ],
        )
        req = BundleImportRequest(bundle_id="b2", conflict_resolution="skip")
        result = handoff.import_bundle(req, bundle)
        assert result.imported_count == 0
        assert result.skipped_count == 1
        conn.close()

    def test_import_replace_conflict(self):
        conn, store, handoff = _fresh_services()
        from app.models.bundle import Bundle, BundleMeta, BundleMemory
        from datetime import datetime, timezone

        existing = store.create(MemoryCreate(
            title="orig title", content="shared content", agent_vendor="v"
        ))

        bundle = Bundle(
            meta=BundleMeta(
                source_agent_vendor="v", destination_agent_vendor="v2",
                exported_at=datetime.now(timezone.utc), memory_count=1,
            ),
            memories=[
                BundleMemory(
                    title="updated title", content="shared content",
                    tags=["y"], agent_vendor="v2",
                )
            ],
        )
        req = BundleImportRequest(bundle_id="b3", conflict_resolution="replace")
        result = handoff.import_bundle(req, bundle)
        assert result.imported_count == 0
        assert result.replaced_count == 1

        # Verify the content was updated
        fetched = store.get(existing.id)
        assert fetched.title == "updated title"
        assert fetched.agent_vendor == "v2"
        conn.close()

    def test_import_records_import_row(self):
        conn, store, handoff = _fresh_services()
        from app.models.bundle import Bundle, BundleMeta, BundleMemory
        from datetime import datetime, timezone

        bundle = Bundle(
            meta=BundleMeta(
                source_agent_vendor="v", destination_agent_vendor="v2",
                exported_at=datetime.now(timezone.utc), memory_count=0,
            ),
            memories=[],
        )
        req = BundleImportRequest(bundle_id="b4")
        handoff.import_bundle(req, bundle)
        count = conn.execute(
            "SELECT COUNT(*) FROM imports WHERE source_bundle = 'b4'"
        ).fetchone()[0]
        assert count == 1
        conn.close()