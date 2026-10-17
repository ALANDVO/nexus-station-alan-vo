# API Reference

All endpoints are under `/api/v1/`. All data endpoints require authentication.

## Authentication

The API uses Bearer token authentication. In local demo mode:

```
Authorization: Bearer <LOCAL_API_KEY>
```

In production mode, OIDC authorization-code flow is used via Keycloak (future milestone).

## Endpoints

### Health Check

`GET /api/v1/healthz`

Returns `{"status": "ok", "version": "<version>"}`.

### Memories

`POST /api/v1/memories` — Create a memory.

Request body:
```json
{
  "title": "string",
  "content": "string",
  "tags": ["string"],
  "agent_vendor": "string"
}
```

`GET /api/v1/memories` — List memories.

Query params: `page` (int, default 1), `per_page` (int, default 20),
`agent_vendor` (string, filter), `tag` (string, filter).

`GET /api/v1/memories/{id}` — Get a single memory.

`PATCH /api/v1/memories/{id}` — Update a memory (partial).

`DELETE /api/v1/memories/{id}` — Delete a memory (returns 204).

### Search

`GET /api/v1/search?q=<query>&limit=<int>&agent_vendor=<str>&tag=<str>`

Semantic search using TF-IDF cosine similarity. Returns ranked `MemoryPage`.

`GET /api/v1/search/stats`

Corpus statistics: `document_count`, `vocabulary_size`, `is_indexed`.

### Handoff

`POST /api/v1/handoff/export` — Export memories as a bundle.

Request body:
```json
{
  "source_agent_vendor": "string",
  "destination_agent_vendor": "string",
  "memory_ids": ["uuid"],
  "filters": {"tag": "string"}
}
```

`POST /api/v1/handoff/import` — Import a bundle.

Body params: `bundle` (Bundle object), `bundle_id` (string),
`conflict_resolution` ("new" | "skip" | "replace").

Returns `BundleImportResult` with counts.

## Response Envelopes

### Memory

```json
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "tags": ["string"],
  "agent_vendor": "string",
  "created_at": "2025-01-01T00:00:00+00:00",
  "updated_at": "2025-01-01T00:00:00+00:00"
}
```

### MemoryPage

```json
{
  "items": [Memory],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### Bundle

```json
{
  "meta": {
    "schema_version": "1.0.0",
    "source_agent_vendor": "string",
    "destination_agent_vendor": "string",
    "exported_at": "2025-01-01T00:00:00+00:00",
    "exported_by": "nexus-station",
    "memory_count": 3,
    "filters": {}
  },
  "memories": [MemoryCreate]
}
```