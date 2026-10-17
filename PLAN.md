# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

react-frontend

## Roadmap

### backend-skeleton — FastAPI backend skeleton with SQLite persistence and memory model

Status: done

Acceptance:
- FastAPI app factory exports create_app()
- SQLite database initialized with memory table and audit_log table
- Memory model with title, content, tags, agent_vendor, UTC timestamps
- POST /memories creates a memory record
- GET /memories lists memories with pagination
- GET /memories/{id} returns a single memory

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/db.py`, `backend/app/core/auth.py`, `backend/app/models/memory.py`, `backend/app/models/bundle.py`, `backend/app/services/store.py`, `backend/app/api/memories.py`, `backend/app/api/deps.py`

Tests: `backend/tests/test_store.py`, `backend/tests/test_api.py`

### tfidf-ranking-engine — Deterministic TF-IDF semantic ranking engine for memory search

Status: done

Acceptance:
- Tokenization: lowercase, strip punctuation, split on alphanumeric
- TF-IDF vector computation across all memories
- Cosine similarity ranking for search queries
- GET /memories/search returns ranked results
- Works offline without any LLM key

Implementation: `backend/app/services/ranking.py`, `backend/app/api/search.py`

Tests: `backend/tests/test_ranking.py`

### agent-handoff-bundles — Agent vendor handoff bundles: export/import structured memory bundles

Status: done

Acceptance:
- POST /handoff/export generates a JSON bundle with selected memories
- POST /handoff/import accepts and deduplicates an imported bundle
- Bundle includes metadata: agent vendor, export timestamp, memory schema version
- Import handles duplicate detection and conflict resolution

Implementation: `backend/app/services/handoff.py`, `backend/app/api/handoff.py`

Tests: `backend/tests/test_handoff.py`, `backend/tests/test_api.py::TestHandoffAPI`

### local-auth — Local-only demo auth with migration path to OIDC/Keycloak

Status: done

Acceptance:
- AUTH_MODE=local uses shared-secret API key from env
- AUTH_MODE=production refuses to start without OIDC
- Auth dependency enforces authenticated access on data endpoints
- Tests cover unauthenticated rejection

Implementation: `backend/app/core/auth.py`

Tests: `backend/tests/test_auth.py`

### react-frontend — React/TSX frontend with memory dashboard, search, and handoff workflows

Status: in_progress

Acceptance:
- Vite + React + TypeScript + package-lock.json
- Typed API client derived from backend routes
- Memory dashboard with loading/error/empty states
- Create/import/search/detail/export workflows
- 3+ frontend tests with Vitest

Implementation: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/hooks/useMemories.ts`, `frontend/src/components/MemoryDashboard.tsx`, `frontend/src/components/MemoryForm.tsx`, `frontend/src/components/MemoryList.tsx`, `frontend/src/components/SearchBar.tsx`, `frontend/src/components/SearchDashboard.tsx`, `frontend/src/components/HandoffPage.tsx`

Tests: `frontend/src/__tests__/App.test.tsx`, `frontend/src/__tests__/MemoryForm.test.tsx`, `frontend/src/__tests__/SearchBar.test.tsx`

### docker-ci — Dockerfiles, compose.yaml with Keycloak, CI workflow

Status: done

Acceptance:
- backend/Dockerfile and frontend/Dockerfile with nonroot users
- compose.yaml with Keycloak and persistent volumes
- .github/workflows/ci.yml runs pytest, npm build/test

Implementation: `backend/Dockerfile`, `frontend/Dockerfile`, `compose.yaml`, `.github/workflows/ci.yml`

### llm-advisory — Opt-in LLM advisory explanations with mocked adapters

Status: planned

Acceptance:
- LLM_API_KEY, LLM_PROVIDER, LLM_MODEL, LLM_BASE_URL support
- OpenAI-compatible, Anthropic, Gemini adapters via httpx
- Advisory labels in UI, never fabricate responses
- CI mocks external LLM calls

