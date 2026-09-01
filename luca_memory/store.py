"""The deliberately small, deterministic storage core for Luca."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
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

    def add_edge(self, edge: Edge) -> None:
        self.connection.execute(
            "INSERT INTO edges (source_id, target_id) VALUES (?, ?)",
            (edge.source_id, edge.target_id),
        )

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
            """
        )
