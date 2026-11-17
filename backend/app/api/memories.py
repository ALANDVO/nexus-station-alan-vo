"""API routes for memory CRUD operations.

All endpoints require authentication. Standard roles:
  - analysts: read + create + update + delete
 بالإضافة إلى: generate LLM advisory explanations
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.auth import UserContext, require_role
from ..models.memory import Memory, MemoryCreate, MemoryPage, MemoryUpdate
from ..services.store import MemoryStore, MemoryNotFoundError
from ..services.llm_advisory import LLMAdvisoryService
from .deps import get_store, get_llm_advisory_service

router = APIRouter(prefix="/memories", tags=["memories"])
RequireAuth = require_role("analyst")


@router.post(
    "",
    response_model=Memory,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new memory entry",
)
async def create_memory(
    data: MemoryCreate,
    store: MemoryStore = Depends(get_store),
    user: UserContext = Depends(RequireAuth),
) -> Memory:
    """Create a new memory record in the store."""
    return store.create(data)


@router.get(
    "",
    response_model=MemoryPage,
    summary="List memories with pagination and filtering",
)
async def list_memories(
    page: int = Query(default=1, ge=1, le=10000),
    per_page: int = Query(default=20, ge=1, le=100),
    agent_vendor: Optional[str] = Query(default=None, description="Filter by agent vendor"),
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    store: MemoryStore = Depends(get_store),
    user: UserContext = Depends(RequireAuth),
) -> MemoryPage:
    """List memories, optionally filtered by agent vendor or tag."""
    return store.list(
        page=page, per_page=per_page,
        agent_vendor=agent_vendor, tag=tag,
    )


@router.get(
    "/{memory_id}",
    response_model=Memory,
    summary="Get a single memory by ID",
)
async def get_memory(
    memory_id: str,
    store: MemoryStore = Depends(get_store),
    user: UserContext = Depends(RequireAuth),
) -> Memory:
    """Retrieve a single memory by its UUID."""
    try:
        return store.get(memory_id)
    except MemoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}",
        )


@router.patch(
    "/{memory_id}",
    response_model=Memory,
    summary="Update a memory (partial)",
)
async def update_memory(
    memory_id: str,
    data: MemoryUpdate,
    store: MemoryStore = Depends(get_store),
    user: UserContext = Depends(RequireAuth),
) -> Memory:
    """Partially update an existing memory."""
    try:
        return store.update(memory_id, data)
    except MemoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}",
        )


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
    response_model=None,
)
async def delete_memory(
    memory_id: str,
    store: MemoryStore = Depends(get_store),
    user: UserContext = Depends(RequireAuth),
) -> None:
    """Delete a memory by ID."""
    try:
        store.delete(memory_id)
    except MemoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}",
        )


@router.get(
    "/{memory_id}/advisory",
    response_model=dict,
    summary="Generate an LLM advisory explanation for a memory",
)
async def get_memory_advisory(
    memory_id: str,
    store: MemoryStore = Depends(get_store),
    service: LLMAdvisoryService = Depends(get_llm_advisory_service),
    user: UserContext = Depends(RequireAuth),
) -> dict:
    """Return a concise advisory explanation for the memory, if LLM is configured."""
    try:
        mem = store.get(memory_id)
    except MemoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}",
        )
    prompt = (
        f"Provide a concise advisory explanation for the following memory context:\\n"
        f"Title: {mem.title}\\n"
        f"Content: {mem.content}\\n"
        f"Tags: {mem.tags}\\n"
        f"Agent vendor: {mem.agent_vendor}"
    )
    advisory = await service.generate_advisory(prompt)
    return {"advisory": advisory}
