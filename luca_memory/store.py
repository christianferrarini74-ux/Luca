"""The deliberately small, deterministic storage core for Luca."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Iterator


@dataclass(frozen=True, slots=True)
class Cell:
    id: int
    content: bytes
    created_at: int


@dataclass(frozen=True, slots=True)
class Edge:
    """A pure, directed address between two cells."""

    source_id: int
    target_id: int


class MemoryStore:
    """Persistent graph with exact, outgoing, and incoming edge access paths.

    The ordered pair ``(source_id, target_id)`` is the edge's physical address.
    Edges intentionally contain no semantic type or mutable cognitive state:
    Luca works on cells; edges only make those cells addressable.
    """

    def __init__(self, database: str | Path) -> None:
        self.path = Path(database)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self._create_schema()
        self._rebuild_cell_search_index()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        try:
            self.connection.execute("BEGIN")
            yield
        except BaseException:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()

    def add_cell(self, cell: Cell) -> None:
        self.connection.execute(
            "INSERT INTO cells (id, content, created_at) VALUES (?, ?, ?)",
            (cell.id, cell.content, cell.created_at),
        )
        self._index_cell_for_search(cell)

    def next_cell_id(self) -> int:
        row = self.connection.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM cells").fetchone()
        return int(row["next_id"])

    def has_cells(self) -> bool:
        return self.connection.execute("SELECT EXISTS(SELECT 1 FROM cells)").fetchone()[0] == 1

    def all_cells(self) -> list[Cell]:
        rows = self.connection.execute("SELECT id, content, created_at FROM cells ORDER BY id")
        return [Cell(row["id"], row["content"], row["created_at"]) for row in rows]

    def add_alias(self, alias: str, cell_id: int) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO cell_aliases (alias, cell_id) VALUES (?, ?)",
            (alias, cell_id),
        )

    def cell_by_alias(self, alias: str) -> Cell | None:
        row = self.connection.execute(
            """SELECT cells.* FROM cell_aliases
               JOIN cells ON cells.id = cell_aliases.cell_id
               WHERE cell_aliases.alias = ?""",
            (alias,),
        ).fetchone()
        return Cell(row["id"], row["content"], row["created_at"]) if row else None

    def record_event(self, kind: str, payload: bytes, occurred_at: int) -> int:
        cursor = self.connection.execute(
            "INSERT INTO memory_events (kind, payload, occurred_at) VALUES (?, ?, ?)",
            (kind, payload, occurred_at),
        )
        return int(cursor.lastrowid)

    def add_edge(self, edge: Edge) -> None:
        self.connection.execute(
            "INSERT INTO edges (source_id, target_id) VALUES (?, ?)",
            (edge.source_id, edge.target_id),
        )

    def cell(self, cell_id: int) -> Cell | None:
        row = self.connection.execute(
            "SELECT * FROM cells WHERE id = ?", (cell_id,)
        ).fetchone()
        return Cell(row["id"], row["content"], row["created_at"]) if row else None

    def edge(self, source_id: int, target_id: int) -> Edge | None:
        row = self.connection.execute(
            "SELECT * FROM edges WHERE source_id = ? AND target_id = ?",
            (source_id, target_id),
        ).fetchone()
        return self._edge_from_row(row) if row else None

    def outgoing(self, source_id: int) -> list[Edge]:
        rows = self.connection.execute(
            "SELECT * FROM edges WHERE source_id = ? ORDER BY target_id", (source_id,)
        )
        return [self._edge_from_row(row) for row in rows]

    def incoming(self, target_id: int) -> list[Edge]:
        rows = self.connection.execute(
            "SELECT * FROM edges WHERE target_id = ? ORDER BY source_id", (target_id,)
        )
        return [self._edge_from_row(row) for row in rows]

    @staticmethod
    def _edge_from_row(row: sqlite3.Row) -> Edge:
        return Edge(source_id=row["source_id"], target_id=row["target_id"])

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS cells (
                id          INTEGER PRIMARY KEY CHECK (id > 0),
                content     BLOB NOT NULL,
                created_at  INTEGER NOT NULL
            ) STRICT;

            CREATE TABLE IF NOT EXISTS edges (
                source_id  INTEGER NOT NULL REFERENCES cells(id),
                target_id  INTEGER NOT NULL REFERENCES cells(id),
                PRIMARY KEY (source_id, target_id)
            ) WITHOUT ROWID, STRICT;

            CREATE INDEX IF NOT EXISTS edges_by_target
                ON edges (target_id, source_id);

            CREATE VIRTUAL TABLE IF NOT EXISTS cell_search USING fts5(
                cell_id UNINDEXED,
                kind,
                text
            );

            CREATE TABLE IF NOT EXISTS cell_aliases (
                alias    TEXT PRIMARY KEY,
                cell_id  INTEGER NOT NULL REFERENCES cells(id)
            ) STRICT;

            CREATE TABLE IF NOT EXISTS memory_events (
                id           INTEGER PRIMARY KEY,
                kind         TEXT NOT NULL,
                payload      BLOB NOT NULL,
                occurred_at  INTEGER NOT NULL
            ) STRICT;
            """
        )

    def _rebuild_cell_search_index(self) -> None:
        cell_count = int(self.connection.execute("SELECT COUNT(*) FROM cells").fetchone()[0])
        indexed_count = int(self.connection.execute("SELECT COUNT(*) FROM cell_search").fetchone()[0])
        if cell_count == indexed_count:
            return
        self.connection.execute("DELETE FROM cell_search")
        for cell in self.all_cells():
            self._index_cell_for_search(cell)
        self.connection.commit()

    def _index_cell_for_search(self, cell: Cell) -> None:
        try:
            payload = json.loads(cell.content)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            payload = {"kind": "raw", "text": cell.content.decode("utf-8", errors="replace")}
        if not isinstance(payload, dict):
            payload = {"kind": "raw", "text": str(payload)}

        kind = str(payload.get("kind") or "unknown")
        terms: list[str] = [str(payload.get("label") or ""), str(payload.get("text") or "")]
        forms = payload.get("forms")
        if isinstance(forms, list):
            terms.extend(str(form) for form in forms)
        for key in ("provenance", "source"):
            if payload.get(key):
                terms.append(str(payload[key]))
        for key in ("subject_id", "predicate_id", "object_id"):
            referenced_id = payload.get(key)
            if isinstance(referenced_id, int):
                referenced = self.cell(referenced_id)
                if referenced is not None:
                    try:
                        referenced_payload = json.loads(referenced.content)
                    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
                        referenced_payload = {}
                    if isinstance(referenced_payload, dict):
                        terms.append(str(referenced_payload.get("label") or ""))
        terms.append(cell.content.decode("utf-8", errors="replace"))
        searchable_text = " ".join(term for term in terms if term)
        self.connection.execute("DELETE FROM cell_search WHERE rowid = ?", (cell.id,))
        self.connection.execute(
            "INSERT INTO cell_search (rowid, cell_id, kind, text) VALUES (?, ?, ?, ?)",
            (cell.id, cell.id, kind, searchable_text),
        )
