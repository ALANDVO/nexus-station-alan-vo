"""Tests for memory persistence (store service)."""
from __future__ import annotations

import pytest
import sqlite3

from app.core.db import SCHEMA_SQL, generate_id
from app.models.memory import MemoryCreate, MemoryUpdate
from app.services.store import MemoryStore, MemoryNotFoundError


def _fresh_store() -> tuple[sqlite3.Connection, MemoryStore]:
    """Create a fresh in-memory store for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn, MemoryStore(conn)


class TestStoreCreate:
    def test_create_returns_memory(self):
        conn, store = _fresh_store()
        data = MemoryCreate(
            title="Test memory",
            content="Some content",
            tags=["tag1"],
            agent_vendor="claude-code",
        )
        mem = store.create(data)
        assert mem.id is not None
        assert mem.title == "Test memory"
        assert mem.content == "Some content"
        assert mem.tags == ["tag1"]
        assert mem.agent_vendor == "claude-code"
        conn.close()

    def test_create_assigns_timestamps(self):
        conn, store = _fresh_store()
        mem = store.create(MemoryCreate(
            title="T", content="C", agent_vendor="codex"
        ))
        assert mem.created_at is not None
        assert mem.updated_at is not None
        conn.close()

    def test_create_empty_title_rejected(self):
        conn, store = _fresh_store()
        with pytest.raises(Exception):
            store.create(MemoryCreate(title="", content="C", agent_vendor="x"))
        conn.close()

    def test_create_empty_content_rejected(self):
        conn, store = _fresh_store()
        with pytest.raises(Exception):
            store.create(MemoryCreate(title="T", content="", agent_vendor="x"))
        conn.close()


class TestStoreGet:
    def test_get_returns_existing(self):
        conn, store = _fresh_store()
        mem = store.create(MemoryCreate(
            title="G", content="content here", agent_vendor="codex"
        ))
        fetched = store.get(mem.id)
        assert fetched.id == mem.id
        assert fetched.title == "G"
        conn.close()

    def test_get_nonexistent_raises(self):
        conn, store = _fresh_store()
        with pytest.raises(MemoryNotFoundError):
            store.get("nonexistent-id")
        conn.close()


class TestStoreList:
    def test_list_pagination(self):
        conn, store = _fresh_store()
        for i in range(5):
            store.create(MemoryCreate(title=f"m{i}", content="c", agent_vendor="v"))

        page = store.list(page=1, per_page=2)
        assert len(page.items) == 2
        assert page.total == 5
        assert page.pages == 3
        conn.close()

    def test_list_with_vendor_filter(self):
        conn, store = _fresh_store()
        store.create(MemoryCreate(title="a", content="c", agent_vendor="claude-code"))
        store.create(MemoryCreate(title="b", content="c", agent_vendor="codex"))
        page = store.list(agent_vendor="claude-code")
        assert len(page.items) == 1
        assert page.items[0].agent_vendor == "claude-code"
        conn.close()

    def test_list_with_tag_filter(self):
        conn, store = _fresh_store()
        store.create(MemoryCreate(title="a", content="c", tags=["important"], agent_vendor="v"))
        store.create(MemoryCreate(title="b", content="c", tags=["other"], agent_vendor="v"))
        page = store.list(tag="important")
        assert len(page.items) == 1
        assert "important" in page.items[0].tags
        conn.close()

    def test_list_empty(self):
        conn, store = _fresh_store()
        page = store.list()
        assert page.total == 0
        assert page.items == []
        conn.close()


class TestStoreUpdate:
    def test_update_partial(self):
        conn, store = _fresh_store()
        mem = store.create(MemoryCreate(title="T", content="C", agent_vendor="v"))
        updated = store.update(mem.id, MemoryUpdate(title="Updated"))
        assert updated.title == "Updated"
        assert updated.content == "C"  # unchanged
        conn.close()

    def test_update_nonexistent_raises(self):
        conn, store = _fresh_store()
        with pytest.raises(MemoryNotFoundError):
            store.update("nope", MemoryUpdate(title="X"))
        conn.close()

    def test_update_no_fields_raises(self):
        conn, store = _fresh_store()
        mem = store.create(MemoryCreate(title="T", content="C", agent_vendor="v"))
        with pytest.raises(ValueError):
            store.update(mem.id, MemoryUpdate())
        conn.close()


class TestStoreDelete:
    def test_delete_existing(self):
        conn, store = _fresh_store()
        mem = store.create(MemoryCreate(title="T", content="C", agent_vendor="v"))
        assert store.delete(mem.id) is True
        with pytest.raises(MemoryNotFoundError):
            store.get(mem.id)
        conn.close()

    def test_delete_nonexistent_raises(self):
        conn, store = _fresh_store()
        with pytest.raises(MemoryNotFoundError):
            store.delete("nope")
        conn.close()


class TestAuditLog:
    def test_create_writes_audit_entry(self):
        conn, store = _fresh_store()
        store.create(MemoryCreate(title="T", content="C", agent_vendor="v"))
        count = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'memory.create'"
        ).fetchone()[0]
        assert count == 1
        conn.close()

    def test_delete_writes_audit_entry(self):
        conn, store = _fresh_store()
        mem = store.create(MemoryCreate(title="T", content="C", agent_vendor="v"))
        store.delete(mem.id)
        count = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'memory.delete'"
        ).fetchone()[0]
        assert count == 1
        conn.close()


class TestTransactionRollback:
    def test_update_failure_rolls_back(self):
        """If an update fails mid-operation, no partial changes persist."""
        conn, store = _fresh_store()
        mem = store.create(MemoryCreate(title="T", content="C", agent_vendor="v"))
        original = store.get(mem.id)
        with pytest.raises(ValueError):
            store.update(mem.id, MemoryUpdate())
        # Data should be unchanged
        after = store.get(mem.id)
        assert after.title == original.title
        conn.close()