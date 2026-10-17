"""Pydantic models for memory records.

A Memory represents a piece of agent session context saved for later retrieval
and handoff between different agent vendors.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _parse_tags(value: Any) -> list[str]:
    """Parse tags from a list or JSON string."""
    if value is None:
        return []
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise ValueError("tags must be a list of strings")
    return [str(t) for t in value]


class MemoryBase(BaseModel):
    """Shared fields for memory create/update operations."""

    title: str = Field(..., min_length=1, max_length=200, description="Short title")
    content: str = Field(..., min_length=1, description="Full memory content")
    tags: list[str] = Field(
        default_factory=list,
        description="Labels: agent vendor, project, session type",
    )
    agent_vendor: str = Field(
        default="unknown",
        max_length=100,
        description="Agent vendor that created this memory",
    )

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[str]:
        return _parse_tags(v)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("agent_vendor")
    @classmethod
    def validate_agent_vendor(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("agent_vendor must not be empty")
        return v


class MemoryCreate(MemoryBase):
    """Fields required to create a new memory."""


class MemoryUpdate(BaseModel):
    """Fields for updating a memory (all optional)."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = Field(default=None)
    agent_vendor: str | None = Field(default=None, max_length=100)

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[str] | None:
        if v is None:
            return None
        return _parse_tags(v)


class Memory(MemoryBase):
    """A complete memory record as stored and returned by the API."""

    id: str = Field(..., description="UUID identifier")
    created_at: datetime = Field(..., description="UTC creation timestamp")
    updated_at: datetime = Field(..., description="UTC last update timestamp")

    model_config = {"from_attributes": True}


class MemoryPage(BaseModel):
    """Paginated list of memories."""

    items: list[Memory] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    pages: int = Field(..., ge=0)