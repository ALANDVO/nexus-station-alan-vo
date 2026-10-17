"""API routes for agent-to-agent handoff bundles.

Export memories as structured bundles for transfer between agent vendors,
and import bundles with deduplication and conflict resolution.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from ..core.auth import UserContext, require_role
from ..models.bundle import Bundle, BundleImportRequest, BundleImportResult
from ..services.handoff import HandoffService
from .deps import get_handoff_service

router = APIRouter(prefix="/handoff", tags=["handoff"])

RequireAuth = require_role("analyst")


class BundleValidationError(Exception):
    """Raised when a bundle fails validation during import."""


@router.post(
    "/export",
    response_model=Bundle,
    status_code=200,
    summary="Export memories as a handoff bundle",
)
async def export_bundle(
    request: dict = Body(
        default=...,
        description=(
            '{"source_agent_vendor":"claude-code",'
            '"destination_agent_vendor":"codex",'
            '"memory_ids":["id1","id2"],"filters":{"tag":"important"}}'
        ),
    ),
    service: HandoffService = Depends(get_handoff_service),
    user: UserContext = Depends(RequireAuth),
) -> Bundle:
    """Export selected or filtered memories as a structured bundle."""
    source = request.get("source_agent_vendor", "nexus-station")
    dest = request.get("destination_agent_vendor", "unknown")
    ids = request.get("memory_ids")
    filters = request.get("filters")

    return service.export_bundle(
        source_vendor=source,
        destination_vendor=dest,
        memory_ids=ids,
        filters=filters,
    )


@router.post(
    "/import",
    response_model=BundleImportResult,
    status_code=200,
    summary="Import memories from a handoff bundle",
)
async def import_bundle(
    bundle: Bundle = Body(..., description="The handoff bundle JSON to import"),
    conflict_resolution: str = Body(
        default="new",
        description="Conflict resolution: new, skip, or replace",
    ),
    bundle_id: str = Body(
        default="manual-import",
        description="Identifier for this import operation",
    ),
    service: HandoffService = Depends(get_handoff_service),
    user: UserContext = Depends(RequireAuth),
) -> BundleImportResult:
    """Import memories from a handoff bundle.

    Conflict resolution:
      - "new" (default): always create copies
      - "skip": skip memories whose content already exists
      - "replace": overwrite existing memories with same content
    """
    req = BundleImportRequest(
        bundle_id=bundle_id,
        conflict_resolution=conflict_resolution,
    )

    try:
        return service.import_bundle(req, bundle)
    except BundleValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {e}",
        )