# Architecture

## Overview

Nexus Station stores agent session memories and enables semantic search
across them for handoff between different agent vendors (Claude Code, Codex,
OpenCode, etc.).

## Components

### Backend (FastAPI + SQLite)

- **app/main.py**: Application factory, creates the FastAPI app with all routes.
- **app/core/config.py**: Environment-based configuration (settings, auth mode).
- **app/core/db.py**: SQLite initialization, connection management, audit logging.
- **app/core/auth.py**: Authentication and authorization dependencies.
- **app/models/**: Pydantic models for Memory, Bundle, and pagination.
- **app/services/store.py**: Memory persistence (CRUD with SQLite).
- **app/services/ranking.py**: TF-IDF ranking engine (deterministic, offline).
- **app/services/handoff.py**: Bundle export/import with conflict resolution.
- **app/api/**: API route handlers (memories, search, handoff).

### Frontend (React + TypeScript + Vite)

- **src/main.tsx**: React entry point with BrowserRouter.
- **src/App.tsx**: Main app with navigation and routing.
- **src/api/client.ts**: Typed API client matching backend routes.
- **src/hooks/useMemories.ts**: Data-fetching hooks for memories and search.
- **src/components/**: UI components (dashboard, form, list, search, handoff).

## Data Flow

1. Agent creates a memory via API → stored in SQLite with audit log.
2. Agent searches memories via `/search?q=...` → TF-IDF engine ranks results.
3. Agent exports a handoff bundle → JSON with selected memories.
4. Another agent imports the bundle → memories restored with deduplication.

## TF-IDF Ranking Engine

The ranking engine (`services/ranking.py`) builds an in-memory TF-IDF index:

1. Tokenize: lowercase, strip punctuation, split on alphanumeric boundaries.
2. Term frequency: TF(t,d) = count(t,d) / total_tokens(d).
3. Inverse document frequency: IDF(t) = ln((1+N) / (1+df(t))) + 1 (sklearn-style).
4. Cosine similarity: dot product of L2-normalized TF-IDF vectors.

This is fully deterministic — no randomness, no LLM, no training.

## Database Schema

```sql
-- Memories: agent session context
CREATE TABLE memories (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    content      TEXT NOT NULL,
    tags         TEXT NOT NULL DEFAULT '[]',  -- JSON array
    agent_vendor TEXT NOT NULL DEFAULT 'unknown',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

-- Audit log: all mutations
CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action      TEXT NOT NULL,
    resource    TEXT NOT NULL,
    resource_id TEXT,
    detail      TEXT,
    created_at  TEXT NOT NULL
);

-- Imports: handoff bundle import tracking
CREATE TABLE imports (
    id            TEXT PRIMARY KEY,
    source_bundle TEXT NOT NULL,
    imported_at   TEXT NOT NULL,
    conflict      TEXT NOT NULL DEFAULT 'new'
);
```