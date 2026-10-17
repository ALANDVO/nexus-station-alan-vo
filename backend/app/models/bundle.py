"""Pydantic models for handoff bundle export/import.

A Bundle is a structured snapshot of memories exported for handoff between
agent vendors. It includes metadata and a list of memory records.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .memory import MemoryBase


class BundleMemory(MemoryBase):
    """A memory record inside a bundle (no generated timestamps needed)."""


class BundleMeta(BaseModel):
    """Metadata about the handoff bundle."""

    schema_version: str = Field(default="1.0.0")
    source_agent_vendor: str = Field(..., min_length=1, max_length=100)
    destination_agent_vendor: str = Field(..., min_length=1, max_length=100)
    exported_at: datetime = Field(..., description="UTC export timestamp")
    exported_by: str = Field(default="nexus-station")
    memory_count: int = Field(..., ge=0)
    filters: dict[str, str | list[str]] = Field(default_factory=dict)


class Bundle(BaseModel):
    """A handoff bundle for agent-to-agent context transfer."""

    meta: BundleMeta
    memories: list[BundleMemory] = Field(default_factory=list)

    @field_validator("memories")
    @classmethod
    def validate_memories_length(cls, v: list[BundleMemory]) -> list[BundleMemory]:
        if len(v) > 1000:
            raise ValueError("bundle cannot contain more than 1000 memories")
        return v


class BundleImportRequest(BaseModel):
    """Request to import a bundle."""

    bundle_id: str = Field(..., min_length=1, description="Source bundle ID")
    conflict_resolution: str = Field(
        default="new",
        pattern="^(new|skip|replace)$",
        description="new: create copies; skip: skip existing; replace: overwrite",
    )


class BundleImportResult(BaseModel):
    """Result of a bundle import operation."""

    bundle_id: str
    imported_count: int = Field(..., ge=0)
    skipped_count: int = Field(..., ge=0)
    replaced_count: int = Field(..., ge=0)
    conflicts: list[str] = Field(default_factory=list)