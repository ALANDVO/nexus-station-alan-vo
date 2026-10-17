"""Tests for authentication and authorization.

Tests:
  - Unauthenticated requests are rejected with 401
  - Invalid tokens are rejected with 401
  - Valid tokens are accepted
  - Wrong auth scheme is rejected
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthRejection:
    async def test_no_auth_header_rejected(self, client_no_auth: AsyncClient):
        """Requests without Authorization header should be rejected."""
        resp = await client_no_auth.get("/api/v1/memories")
        assert resp.status_code == 401

    async def test_invalid_token_rejected(self, client_no_auth: AsyncClient):
        """Requests with wrong API key should be rejected."""
        client_no_auth.headers["Authorization"] = "Bearer invalid-token-" + "x" * 16
        resp = await client_no_auth.get("/api/v1/memories")
        assert resp.status_code == 401

    async def test_wrong_scheme_rejected(self, client_no_auth: AsyncClient):
        """Non-Bearer auth schemes should be rejected."""
        client_no_auth.headers["Authorization"] = "Basic " + "not-a-key"
        resp = await client_no_auth.get("/api/v1/memories")
        assert resp.status_code == 401

    async def test_missing_token_value_rejected(self, client_no_auth: AsyncClient):
        """Bearer without token value should be rejected."""
        client_no_auth.headers["Authorization"] = "Bearer "
        resp = await client_no_auth.get("/api/v1/memories")
        assert resp.status_code == 401

    async def test_valid_token_accepted(self, client: AsyncClient):
        """Valid API key should succeed."""
        resp = await client.get("/api/v1/memories")
        assert resp.status_code == 200

    async def test_search_requires_auth(self, client_no_auth: AsyncClient):
        """Search endpoint also requires authentication."""
        resp = await client_no_auth.get("/api/v1/search?q=test")
        assert resp.status_code == 401

    async def test_handoff_export_requires_auth(self, client_no_auth: AsyncClient):
        """Handoff export requires authentication."""
        resp = await client_no_auth.post("/api/v1/handoff/export", json={})
        assert resp.status_code == 401

    async def test_handoff_import_requires_auth(self, client_no_auth: AsyncClient):
        """Handoff import requires authentication."""
        resp = await client_no_auth.post("/api/v1/handoff/import", json={
            "bundle": {"meta": {}, "memories": []},
        })
        assert resp.status_code == 401