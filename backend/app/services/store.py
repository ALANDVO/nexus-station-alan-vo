"""Memory persistence service.

Handles CRUD operations for Memory records using SQLite with parameterized
SQL. All mutations are transactional and logged to the audit_log.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

import sqlite3

from ..core.db import (
    _parse_tags_from_db,
    _utc_now,
    generate_id,
    log_audit,
    serialize_tags,
)
from ..models.memory import Memory, MemoryCreate, MemoryPage, MemoryUpdate


def _row_to_memory(row: sqlite3.Row) -> Memory:
    """Convert a database row to a Memory model."""
    return Memory(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        tags=_parse_tags_from_db(row["tags"]),
        agent_vendor=row["agent_vendor"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class MemoryStore:
    """Persistence layer for Memory records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, data: MemoryCreate) -> Memory:
        """Insert a new memory and return it. Transactional with audit log."""
        now = _utc_now()
        mem_id = generate_id()
        try:
            self._conn.execute(
                """
                INSERT INTO memories (id, title, content, tags, agent_vendor,
                                      created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mem_id,
                    data.title,
                    data.content,
                    serialize_tags(data.tags),
                    data.agent_vendor,
                    now,
                    now,
                ),
            )
            log_audit(self._conn, "memory.create", "memories", mem_id, data.title)
            return self.get(mem_id)
        except Exception:
            self._conn.rollback()
            raise

    def get(self, mem_id: str) -> Memory:
        """Retrieve a single memory by ID."""
        row = self._conn.execute(
            "SELECT * FROM memories WHERE id = ?", (mem_id,)
        ).fetchone()
        if row is None:
            raise MemoryNotFoundError(mem_id)
        return _row_to_memory(row)

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        agent_vendor: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> MemoryPage:
        """List memories with pagination and filtering."""
        offset = (page - 1) * per_page
        where_clauses: list[str] = []
        params: list[Any] = []

        if agent_vendor:
            where_clauses.append("agent_vendor = ?")
            params.append(agent_vendor)
        if tag:
            where_clauses.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM memories {where_sql}", params
            ).fetchone()[0]
        )

        rows = self._conn.execute(
            f"""
            SELECT * FROM memories
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

        items = [_row_to_memory(r) for r in rows]
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return MemoryPage(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    def search_by_title(self, query: str, page: int = 1, per_page: int = 20) -> MemoryPage:
        """Substring search on title and content. Returns ranked page."""
        offset = (page - 1) * per_page
        pattern = f"%{query}%"
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM memories WHERE title LIKE ? OR content LIKE ?",
                (pattern, pattern),
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            """
            SELECT * FROM memories
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (pattern, pattern, per_page, offset),
        ).fetchall()
        items = [_row_to_memory(r) for r in rows]
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return MemoryPage(
            items=items, total=total, page=page, per_page=per_page, pages=pages
        )

    def update(self, mem_id: str, data: MemoryUpdate) -> Memory:
        """Update fields of a memory. Only provided fields are changed."""
        update_data = data.model_dump(exclude_unset=True)
        if "tags" in update_data:
            update_data["tags"] = serialize_tags(update_data["tags"])

        if not update_data:
            raise ValueError("no fields to update")

        now = _utc_now()
        set_clauses = [f"{k} = ?" for k in update_data]
        params = list(update_data.values()) + [now, mem_id]

        try:
            result = self._conn.execute(
                f"""
                UPDATE memories
                SET {", ".join(set_clauses)}, updated_at = ?
                WHERE id = ?
                """,
                params,
            )
            if result.rowcount == 0:
                raise MemoryNotFoundError(mem_id)
            log_audit(self._conn, "memory.update", "memories", mem_id, str(update_data))
            return self.get(mem_id)
        except Exception:
            self._conn.rollback()
            raise

    def delete(self, mem_id: str) -> bool:
        """Delete a memory by ID. Returns True if deleted."""
        try:
            result = self._conn.execute(
                "DELETE FROM memories WHERE id = ?", (mem_id,)
            )
            if result.rowcount == 0:
                raise MemoryNotFoundError(mem_id)
            log_audit(self._conn, "memory.delete", "memories", mem_id)
            return True
        except Exception:
            self._conn.rollback()
            raise

    def all_for_ranking(self) -> list[Memory]:
        """Return all memories for the ranking engine to index."""
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY created_at ASC"
        ).fetchall()
        return [_row_to_memory(r) for r in rows]


class MemoryNotFoundError(Exception):
    """Raised when a memory ID does not exist."""

    def __init__(self, mem_id: str) -> None:
        self.mem_id = mem_id
        super().__init__(f"Memory not found: {mem_id}")