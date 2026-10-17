"""Nexus Station — FastAPI application factory.

Creates the FastAPI app with all API routes registered. The database is
initialized on startup. Use `create_app()` as the entry point for both
Docker and local development.

Example:
    uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import memories, search, handoff
from .core.config import Settings, get_settings
from .core.db import init_db


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override. Uses get_settings() if not provided.

    Returns:
        A configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    # Refuse to start in production mode without OIDC
    settings.require_oidc()

    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ) -> AsyncIterator[None]:
        # Initialize database on startup
        init_db(settings)
        yield

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        lifespan=lifespan,
    )

    # If custom settings were provided, override get_settings
    if settings is not get_settings():
        get_settings.cache_clear()
        app.dependency_overrides[get_settings] = lambda: settings

    # CORS: allow localhost origins for demo/development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(memories.router, prefix=settings.api_prefix)
    app.include_router(search.router, prefix=settings.api_prefix)
    app.include_router(handoff.router, prefix=settings.api_prefix)

    @app.get(f"{settings.api_prefix}/healthz", tags=["health"])
    async def health_check() -> dict:
        """Health check endpoint for container orchestration."""
        return {"status": "ok", "version": settings.version}

    return app


app = create_app()  # Module-level instance for uvicorn direct run