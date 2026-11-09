"""API routes for semantic memory search.

Uses the TF-IDF ranking engine for deterministic, offline semantic search.
Returns memories ranked by cosine similarity to the query.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..core.auth import UserContext, require_role
from ..models.memory import MemoryPage, MemoryWithScore, SearchResults
from ..services.ranking import TFIDFRanker
from ..services.store import MemoryStore
from .deps import get_ranker, get_store

router = APIRouter(prefix="/search", tags=["search"])

RequireAuth = require_role("analyst")


@router.get(
    "",
    response_model=SearchResults,
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
) -> SearchResults:
    """Semantic search: ranks all memories by TF-IDF cosine similarity to the
    query, then optionally filters by agent vendor or tag.

    Returns scored memories sorted by relevance score.
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
    scored_items: list[MemoryWithScore] = []
    for mid, score in ranked:
        if mid in mem_by_id:
            mem = mem_by_id[mid]
            scored_items.append(
                MemoryWithScore(
                    id=mem.id,
                    title=mem.title,
                    content=mem.content,
                    tags=mem.tags,
                    agent_vendor=mem.agent_vendor,
                    created_at=mem.created_at,
                    updated_at=mem.updated_at,
                    relevance_score=score,
                )
            )

    # If ranking found nothing, fall back to substring search
    if not scored_items and all_memories:
        page = store.search_by_title(q, page=1, per_page=limit)
        # Fallback results get a score of 0.0 since they're not ranked
        scored_items = [
            MemoryWithScore(
                id=mem.id,
                title=mem.title,
                content=mem.content,
                tags=mem.tags,
                agent_vendor=mem.agent_vendor,
                created_at=mem.created_at,
                updated_at=mem.updated_at,
                relevance_score=0.0,
            )
            for mem in page.items
        ]

    return SearchResults(
        items=scored_items,
        total=len(scored_items),
        query=q,
        limit=limit,
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
