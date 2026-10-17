"""Integration tests crossing the real HTTP boundary.

Tests the full request/response cycle: FastAPI -> dependency injection ->
store -> database -> serialization back to JSON.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.memory import MemoryCreate
from app.services.store import MemoryStore


@pytest.mark.asyncio
class TestMemoriesAPI:
    async def test_create_and_get_memory(self, client: AsyncClient, db_conn, sample_memory_data):
        """End-to-end: create a memory via HTTP, retrieve it, verify fields."""
        resp = await client.post("/api/v1/memories", json=sample_memory_data)
        assert resp.status_code == 201
        created = resp.json()
        assert created["title"] == sample_memory_data["title"]
        assert created["agent_vendor"] == sample_memory_data["agent_vendor"]

        resp2 = await client.get(f"/api/v1/memories/{created['id']}")
        assert resp2.status_code == 200
        fetched = resp2.json()
        assert fetched["id"] == created["id"]
        assert fetched["content"] == sample_memory_data["content"]

    async def test_list_memories_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/memories")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    async def test_list_memories_with_pagination(self, client: AsyncClient, sample_memory_data):
        # Create 3 memories
        for i in range(3):
            data = {**sample_memory_data, "title": f"memory-{i}"}
            resp = await client.post("/api/v1/memories", json=data)
            assert resp.status_code == 201

        resp = await client.get("/api/v1/memories?per_page=2&page=1")
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["total"] == 3

    async def test_create_memory_validation_error(self, client: AsyncClient):
        """Malformed input should return 422."""
        resp = await client.post("/api/v1/memories", json={
            "title": "",  # empty title
            "content": "valid content",
            "agent_vendor": "test",
        })
        assert resp.status_code == 422

    async def test_get_nonexistent_memory(self, client: AsyncClient):
        resp = await client.get("/api/v1/memories/nonexistent-id")
        assert resp.status_code == 404

    async def test_patch_memory(self, client: AsyncClient, sample_memory_data):
        resp = await client.post("/api/v1/memories", json=sample_memory_data)
        mem_id = resp.json()["id"]

        resp2 = await client.patch(f"/api/v1/memories/{mem_id}", json={"title": "Updated"})
        assert resp2.status_code == 200
        assert resp2.json()["title"] == "Updated"

    async def test_delete_memory(self, client: AsyncClient, sample_memory_data):
        resp = await client.post("/api/v1/memories", json=sample_memory_data)
        mem_id = resp.json()["id"]

        resp2 = await client.delete(f"/api/v1/memories/{mem_id}")
        assert resp2.status_code == 204

        resp3 = await client.get(f"/api/v1/memories/{mem_id}")
        assert resp3.status_code == 404

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/v1/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
class TestSearchAPI:
    async def test_search_returns_ranked_results(self, client: AsyncClient):
        """Semantic search across stored memories."""
        # Create memories with distinct content
        await client.post("/api/v1/memories", json={
            "title": "Auth fix", "content": "OAuth callback state validation",
            "tags": ["auth"], "agent_vendor": "claude-code",
        })
        await client.post("/api/v1/memories", json={
            "title": "DB migration", "content": "sessions table migration TTL",
            "tags": ["db"], "agent_vendor": "codex",
        })

        resp = await client.get("/api/v1/search?q=oauth+callback")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] > 0
        # The auth memory should rank first
        assert "oauth" in body["items"][0]["content"].lower()

    async def test_search_empty_query_rejected(self, client: AsyncClient):
        resp = await client.get("/api/v1/search?q=")
        assert resp.status_code == 422

    async def test_search_stats(self, client: AsyncClient):
        resp = await client.get("/api/v1/search/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["document_count"] >= 0
        assert "vocabulary_size" in body


@pytest.mark.asyncio
class TestHandoffAPI:
    async def test_export_and_import_roundtrip(self, client: AsyncClient, sample_memory_data):
        """Export a memory, then import it into a fresh store."""
        # Create a memory
        resp = await client.post("/api/v1/memories", json=sample_memory_data)
        mem_id = resp.json()["id"]

        # Export
        export_resp = await client.post("/api/v1/handoff/export", json={
            "source_agent_vendor": "claude-code",
            "destination_agent_vendor": "codex",
            "memory_ids": [mem_id],
        })
        assert export_resp.status_code == 200
        bundle = export_resp.json()
        assert bundle["meta"]["source_agent_vendor"] == "claude-code"
        assert bundle["meta"]["memory_count"] == 1
        assert len(bundle["memories"]) == 1

        # Delete original
        await client.delete(f"/api/v1/memories/{mem_id}")

        # Import the bundle back
        import_resp = await client.post("/api/v1/handoff/import", json={
            "bundle": bundle,
            "bundle_id": "test-bundle-1",
        })
        assert import_resp.status_code == 200
        result = import_resp.json()
        assert result["imported_count"] == 1
        assert result["bundle_id"] == "test-bundle-1"

        # Verify the memory was restored
        search_resp = await client.get("/api/v1/memories")
        assert search_resp.json()["total"] == 1