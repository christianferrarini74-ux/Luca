"""Fast, bounded search paths over Luca's persistent memory."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .store import Cell, Edge, MemoryStore
from .thought import ThoughtBudget, ThoughtEngine, ThoughtRequest, ThoughtResult


@dataclass(frozen=True, slots=True)
class CellSearchResult:
    """A cell returned by exact or full-text search."""

    cell: Cell
    score: float = 0.0


@dataclass(frozen=True, slots=True)
class AssertionSearchResult:
    """An assertion cell and its referenced subject, predicate, and object."""

    assertion_id: int
    subject_id: int
    predicate_id: int
    object_id: int
    score: float = 0.0


class MemorySearch:
    """Expose indexed lookup without making callers know SQLite details."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def cell_by_id(self, cell_id: int) -> Cell | None:
        return self.store.cell(cell_id)

    def cell_by_alias(self, alias: str) -> Cell | None:
        return self.store.cell_by_alias(self._normalise(alias))

    def cells_by_text(self, query: str, *, kind: str | None = None, limit: int = 20) -> list[CellSearchResult]:
        """Search indexed cell text, optionally restricted to one cell kind."""

        if limit < 1:
            return []
        match_query = self._fts_query(query)
        if not match_query:
            return []
        parameters: list[object] = [match_query]
        kind_clause = ""
        if kind:
            kind_clause = " AND kind = ?"
            parameters.append(kind)
        parameters.append(limit)
        rows = self.store.connection.execute(
            """SELECT cell_id, bm25(cell_search) AS score
               FROM cell_search
               WHERE cell_search MATCH ?"""
            + kind_clause
            + " ORDER BY score, cell_id LIMIT ?",
            parameters,
        )
        return [CellSearchResult(self.store.cell(int(row["cell_id"])), float(row["score"])) for row in rows if self.store.cell(int(row["cell_id"]))]

    def cells_by_kind(self, kind: str, *, limit: int = 100) -> list[CellSearchResult]:
        """Return cells of one indexed kind without scanning the cells table."""

        if limit < 1:
            return []
        rows = self.store.connection.execute(
            """SELECT cell_id FROM cell_search
               WHERE cell_search MATCH ?
               ORDER BY cell_id LIMIT ?""",
            (f'kind:"{kind.replace(chr(34), chr(34) * 2)}"', limit),
        )
        return [CellSearchResult(cell) for row in rows if (cell := self.store.cell(int(row["cell_id"]))) is not None]

    def assertions(
        self,
        *,
        subject_id: int | None = None,
        predicate_id: int | None = None,
        object_id: int | None = None,
        text: str | None = None,
        limit: int = 100,
    ) -> list[AssertionSearchResult]:
        """Find assertion cells through indexed text and explicit references."""

        if text:
            candidates = self.cells_by_text(text, kind="assertion", limit=limit)
        elif subject_id is not None:
            candidates = []
            for edge in self.outgoing(subject_id):
                cell = self.store.cell(edge.target_id)
                if cell is not None and self._kind(cell) == "assertion":
                    candidates.append(CellSearchResult(cell))
        else:
            candidates = self.cells_by_kind("assertion", limit=limit)
        results: list[AssertionSearchResult] = []
        for candidate in candidates:
            payload = self._payload(candidate.cell)
            if not all(isinstance(payload.get(key), int) for key in ("subject_id", "predicate_id", "object_id")):
                continue
            if subject_id is not None and payload["subject_id"] != subject_id:
                continue
            if predicate_id is not None and payload["predicate_id"] != predicate_id:
                continue
            if object_id is not None and payload["object_id"] != object_id:
                continue
            results.append(
                AssertionSearchResult(
                    candidate.cell.id,
                    int(payload["subject_id"]),
                    int(payload["predicate_id"]),
                    int(payload["object_id"]),
                    candidate.score,
                )
            )
            if len(results) >= limit:
                break
        return results

    def exact_edge(self, source_id: int, target_id: int) -> Edge | None:
        return self.store.edge(source_id, target_id)

    def outgoing(self, source_id: int) -> list[Edge]:
        return self.store.outgoing(source_id)

    def incoming(self, target_id: int) -> list[Edge]:
        return self.store.incoming(target_id)

    def expand(self, seed_ids: tuple[int, ...], budget: ThoughtBudget | None = None) -> ThoughtResult:
        """Expand a local neighbourhood through both address directions."""

        return ThoughtEngine(self.store).run(ThoughtRequest(tuple(seed_ids), budget or ThoughtBudget()))

    @staticmethod
    def _fts_query(query: str) -> str:
        tokens = re.findall(r"[\wÀ-ÿ]+", query.lower())
        return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)

    @staticmethod
    def _normalise(value: str) -> str:
        return re.sub(r"\s+", " ", value.lower().replace("è", "e").strip())

    @staticmethod
    def _payload(cell: Cell) -> dict[str, object]:
        try:
            value = json.loads(cell.content)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def _kind(cls, cell: Cell) -> str:
        return str(cls._payload(cell).get("kind") or "unknown")
