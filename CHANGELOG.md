# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Fixed (this checkpoint)
- Frontend test quality: eliminated React `act()` warnings by wrapping renders in `act()` and migrating from `fireEvent` to `@testing-library/user-event` in all 3 test files.
- All 9 frontend tests pass cleanly; frontend builds successfully.
- Verified end-to-end backend/frontend integration: create, search, list, handoff export/import.

## [1.0.0] — 2025-01-01

### Added
- FastAPI backend with SQLite persistence for agent session memories.
- Memory CRUD API: create, list (with pagination/filtering), read, update, delete.
- `/api/v1/healthz` health check endpoint.
- TF-IDF semantic ranking engine for deterministic offline memory search.
- Semantic search API: `GET /api/v1/search?q=...` with TF-IDF cosine similarity.
- Agent handoff bundle export/import service with conflict resolution (new/skip/replace).
- Handoff API: `POST /api/v1/handoff/export` and `POST /api/v1/handoff/import`.
- Audit log recording all memory and handoff mutations.
- Local-only demo authentication (shared-secret API key).
- React + TypeScript + Vite frontend with memory dashboard, semantic search, and handoff pages.
- Typed API client derived from backend routes.
- Dockerfiles for backend and frontend with nonroot users.
- Docker compose with API, frontend, and Keycloak services.
- CI workflow: backend pytest + frontend npm build/test + Dockerfile builds.
- README with install/run/test instructions, architecture diagram, and AI/ML evaluation section.