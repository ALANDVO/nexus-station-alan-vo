"""Agent handoff bundle service.

Exports memories as structured JSON bundles for handoff between agent
vendors, and imports them with deduplication and conflict resolution.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import sqlite3

from ..core.db import _utc_now, generate_id, log_audit
from ..models.bundle import Bundle, BundleImportRequest, BundleImportResult, BundleMeta
from ..models.memory import Memory, MemoryCreate
from .store import MemoryStore, _parse_tags_from_db

def _rows_to_memories(rows: list[sqlite3.Row]) -> list[Memory]:
    """Convert database rows to Memory models."""
    return [
        Memory(
            id=r["id"],
            title=r["title"],
            content=r["content"],
            tags=_parse_tags_from_db(r["tags"]),
            agent_vendor=r["agent_vendor"],
            created_at=datetime.fromisoformat(r["created_at"]),
            updated_at=datetime.fromisoformat(r["updated_at"]),
        )
        for r in rows
    ]


class HandoffService:
    """Handles bundle export and import for inter-agent handoff."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._store = MemoryStore(conn)

    def export_bundle(
        self,
        source_vendor: str,
        destination_vendor: str,
        memory_ids: list[str] | None = None,
        filters: dict[str, str | list[str]] | None = None,
    ) -> Bundle:
        """Create a bundle from selected or filtered memories.

        If memory_ids is provided, export exactly those memories.
        Otherwise, export all memories (optionally filtered by tags/vendor).
        """
        if memory_ids:
            placeholders = ",".join("?" for _ in memory_ids)
            rows = self._conn.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders}) ORDER BY created_at DESC",
                memory_ids,
            ).fetchall()
        else:
            query = "SELECT * FROM memories"
            params: list = []
            if filters:
                where: list[str] = []
                for key, val in filters.items():
                    if key == "agent_vendor":
                        where.append("agent_vendor = ?")
                        params.append(str(val))
                    elif key == "tag":
                        where.append("tags LIKE ?")
                        params.append(f'%"{val}"%')
                if where:
                    query += " WHERE " + " AND ".join(where)
            query += " ORDER BY created_at DESC"
            rows = self._conn.execute(query, params).fetchall()

        memories = _rows_to_memories(rows) if rows else []
        bundle = Bundle(
            meta=BundleMeta(
                source_agent_vendor=source_vendor,
                destination_agent_vendor=destination_vendor,
                exported_at=datetime.now(timezone.utc),
                memory_count=len(memories),
                filters=filters or {},
            ),
            memories=[
                {
                    "title": m.title,
                    "content": m.content,
                    "tags": m.tags,
                    "agent_vendor": m.agent_vendor,
                }
                for m in memories
            ],
        )
        log_audit(
            self._conn,
            "handoff.export",
            "bundles",
            None,
            f"exported {len(memories)} memories, vendor={source_vendor}",
        )
        return bundle

    def import_bundle(
        self,
        req: BundleImportRequest,
        bundle: Bundle,
    ) -> BundleImportResult:
        """Import memories from a bundle with conflict resolution.

        Conflict resolution modes:
          - "new": always create copies (default)
          - "skip": skip memories whose content hash already exists
          - "replace": overwrite existing memories with same content hash
        """
        imported = 0
        skipped = 0
        replaced = 0
        conflicts: list[str] = []

        try:
            for mem_in in bundle.memories:
                existing = self._conn.execute(
                    "SELECT id FROM memories WHERE content = ?",
                    (mem_in.content,),
                ).fetchone()

                if existing and req.conflict_resolution == "skip":
                    skipped += 1
                    continue
                elif existing and req.conflict_resolution == "replace":
                    existing_id = existing["id"]
                    self._conn.execute(
                        """
                        UPDATE memories SET title = ?, content = ?, tags = ?,
                            agent_vendor = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            mem_in.title,
                            mem_in.content,
                            json.dumps(mem_in.tags),
                            mem_in.agent_vendor,
                            _utc_now(),
                            existing_id,
                        ),
                    )
                    replaced += 1
                else:
                    create_data = MemoryCreate(
                        title=mem_in.title,
                        content=mem_in.content,
                        tags=mem_in.tags,
                        agent_vendor=mem_in.agent_vendor,
                    )
                    mem = self._store.create(create_data)
                    imported += 1
                    conflicts.append(mem.id)

            self._conn.execute(
                """
                INSERT INTO imports (id, source_bundle, imported_at, conflict)
                VALUES (?, ?, ?, ?)
                """,
                (generate_id(), req.bundle_id, _utc_now(), req.conflict_resolution),
            )
            log_audit(
                self._conn,
                "handoff.import",
                "bundles",
                req.bundle_id,
                f"imported={imported} skipped={skipped} replaced={replaced}",
            )
            self._conn.commit()

            return BundleImportResult(
                bundle_id=req.bundle_id,
                imported_count=imported,
                skipped_count=skipped,
                replaced_count=replaced,
                conflicts=conflicts[:20],
            )
        except Exception:
            self._conn.rollback()
            raise