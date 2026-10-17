"""API routes for semantic memory search.

Uses the TF-IDF ranking engine for deterministic, offline semantic search.
Returns memories ranked by cosine similarity to the query.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..core.auth import UserContext, require_role
from ..models.memory import MemoryPage
from ..services.ranking import TFIDFRanker
from ..services.store import MemoryStore
from .deps import get_ranker, get_store

router = APIRouter(prefix="/search", tags=["search"])

RequireAuth = require_role("analyst")


@router.get(
    "",
    response_model=MemoryPage,
    summary="Semantic search across memories using TF-IDF cosine similarity",
)
async def search_memories(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    agent_vendor: Optional[str] = Query(default=None, description="Filter by agent vendor"),
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    store: MemoryStore = Depends(get_store),
    ranker: TFIDFRanker = Depends(get_ranker),
    user: UserContext = Depends(RequireAuth),
) -> MemoryPage:
    """Semantic search: ranks all memories by TF-IDF cosine similarity to the
    query, then optionally filters by agent vendor or tag.

    Returns a paginated MemoryPage with items sorted by relevance score.
    """
    all_memories = store.all_for_ranking()

    if agent_vendor:
        all_memories = [m for m in all_memories if m.agent_vendor == agent_vendor]
    if tag:
        all_memories = [m for m in all_memories if tag in m.tags]

    ranker.index(all_memories)
    ranked = ranker.rank(q, limit=limit)

    # Build a lookup from id to memory for ordered results
    mem_by_id = {m.id: m for m in all_memories}
    items = [mem_by_id[mid] for mid, _ in ranked if mid in mem_by_id]

    # If ranking found nothing, fall back to substring search
    if not items and all_memories:
        page = store.search_by_title(q, page=1, per_page=limit)
        items = page.items
        return page

    return MemoryPage(
        items=items,
        total=len(items),
        page=1,
        per_page=limit,
        pages=1 if items else 0,
    )


@router.get(
    "/stats",
    summary="Return corpus statistics for the ranking engine",
)
async def ranking_stats(
    store: MemoryStore = Depends(get_store),
    ranker: TFIDFRanker = Depends(get_ranker),
    user: UserContext = Depends(RequireAuth),
) -> dict:
    """Return statistics about the indexed memory corpus.

    Useful for debugging the ranking engine and observing corpus size.
    """
    memories = store.all_for_ranking()
    ranker.index(memories)
    return {
        "document_count": ranker.document_count,
        "vocabulary_size": ranker.vocabulary_size,
        "is_indexed": ranker.is_indexed(),
    }