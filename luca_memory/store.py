"""The deliberately small, deterministic storage core for Luca."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import time
import threading
from typing import Iterable, Iterator, Literal


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


@dataclass(frozen=True, slots=True)
class ConvergenceMatch:
    """A candidate node evaluated by synaptic family convergence on SSD."""

    node_id: int
    matched_required: int
    required_total: int
    matched_context: int
    context_total: int
    max_last_used_at: int
    sum_use_count: int

    @property
    def is_exact(self) -> bool:
        """True when all required anchors are satisfied (and >=1 context anchor for single-anchor questions)."""
        if self.required_total <= 0:
            return False
        if self.required_total >= 2:
            return self.matched_required == self.required_total
        return self.matched_required == 1 and self.matched_context >= 1


@dataclass(frozen=True, slots=True)
class ConvergenceResult:
    """Outcome of a binding (`strict`) or `associative` family convergence query on SSD."""

    mode: Literal["strict", "associative"]
    required_anchors: tuple[int, ...]
    context_anchors: tuple[int, ...]
    exact_matches: tuple[ConvergenceMatch, ...]
    partial_matches: tuple[ConvergenceMatch, ...]
    opened_ids: tuple[int, ...] = ()
    estimated_seed_edges: int = 0
    selection_ms: float = 0.0
    query_ms: float = 0.0
    elapsed_ms: float = 0.0
    recall_ms: float = 0.0
    strategy: str = "none"

    @property
    def ranked_matches(self) -> tuple[ConvergenceMatch, ...]:
        """Full relevance-ordered candidate ranking eligible under `mode`."""
        if self.mode == "strict":
            return self.exact_matches
        return (*self.exact_matches, *self.partial_matches)

    @property
    def ranked_ids(self) -> tuple[int, ...]:
        """Candidate IDs in the full ranking eligible under `mode` (distinct from `opened_ids`)."""
        return tuple(match.node_id for match in self.ranked_matches)

    @property
    def selected_ids(self) -> tuple[int, ...]:
        """Alias for `ranked_ids` kept for compatibility with direct store queries."""
        return self.ranked_ids

    @property
    def unopened_ids(self) -> tuple[int, ...]:
        """Ranked candidate IDs that remain available as alternatives without having been opened in VRAM."""
        opened_set = set(self.opened_ids)
        return tuple(nid for nid in self.ranked_ids if nid not in opened_set)

    @property
    def available_alternatives(self) -> tuple[ConvergenceMatch, ...]:
        """Remaining ranked candidates (or partial matches when strict intersection is empty) available for the next step."""
        if self.ranked_matches:
            opened_set = set(self.opened_ids)
            return tuple(m for m in self.ranked_matches if m.node_id not in opened_set)
        opened_set = set(self.opened_ids)
        return tuple(m for m in self.partial_matches if m.node_id not in opened_set)

    @property
    def has_only_partial_matches(self) -> bool:
        """True when strict intersection is empty but partial matches (e.g. 2 of 3 families) exist."""
        return len(self.exact_matches) == 0 and len(self.partial_matches) > 0

    @property
    def rows_examined(self) -> int:
        """Backward-compatible alias for `estimated_seed_edges`."""
        return self.estimated_seed_edges

    def with_recall_outcome(self, opened_ids: Iterable[int], recall_ms: float) -> "ConvergenceResult":
        """Return a copy annotated with the candidate IDs actually opened in VRAM and total recall time."""
        return ConvergenceResult(
            mode=self.mode,
            required_anchors=self.required_anchors,
            context_anchors=self.context_anchors,
            exact_matches=self.exact_matches,
            partial_matches=self.partial_matches,
            opened_ids=tuple(int(nid) for nid in opened_ids),
            estimated_seed_edges=self.estimated_seed_edges,
            selection_ms=self.selection_ms,
            query_ms=self.query_ms,
            elapsed_ms=self.elapsed_ms,
            recall_ms=recall_ms,
            strategy=self.strategy,
        )




class MemoryStore:
    """Persistent graph with exact, outgoing, and incoming edge access paths.

    The ordered pair ``(source_id, target_id)`` is the edge's physical address.
    Edges intentionally contain no semantic type or mutable cognitive state:
    Luca works on cells; edges only make those cells addressable.
    """

    def __init__(self, database: str | Path) -> None:
        self.path = Path(database)
        self.lock = threading.RLock()
        self._savepoint = 0
        # The API serves requests from worker threads; the runtime serializes access.
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")
        try:
            self._create_schema()
            self._ensure_edge_usage_columns()
            self._ensure_cell_usage_summary()
            from .synaptic_schema import ensure_synaptic_schema
            ensure_synaptic_schema(self)
            self._rebuild_cell_search_index()
        except BaseException:
            self.connection.close()
            raise

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self.lock:
            nested = self.connection.in_transaction
            self._savepoint += 1
            name = f"luca_{self._savepoint}"
            self.connection.execute(f"SAVEPOINT {name}" if nested else "BEGIN IMMEDIATE")
            try:
                yield
                self.connection.execute(f"RELEASE {name}" if nested else "COMMIT")
            except BaseException:
                if nested:
                    self.connection.execute(f"ROLLBACK TO {name}")
                    self.connection.execute(f"RELEASE {name}")
                else:
                    self.connection.rollback()
                raise

    @property
    def revision(self) -> int:
        with self.lock:
            return int(self.connection.execute("SELECT revision FROM graph_revision").fetchone()[0])

    def node_revision(self, node_id: int) -> tuple[int, int]:
        with self.lock:
            row = self.connection.execute("SELECT content_revision, directory_revision FROM node_versions WHERE node_id=?", (node_id,)).fetchone()
            return tuple(row) if row else (-1, -1)

    def add_cell(self, cell: Cell) -> None:
        self.connection.execute(
            "INSERT INTO cells (id, content, created_at) VALUES (?, ?, ?)",
            (cell.id, cell.content, cell.created_at),
        )
        self._index_cell_for_search(cell)

    def upsert_cell(self, cell: Cell) -> None:
        self.connection.execute(
            """INSERT INTO cells (id, content, created_at) VALUES (?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET content = excluded.content""",
            (cell.id, cell.content, cell.created_at),
        )
        self._index_cell_for_search(cell)

    def next_cell_id(self) -> int:
        row = self.connection.execute("SELECT last_id + 1 AS next_id FROM node_id_sequence").fetchone()
        return int(row["next_id"])

    def has_cells(self) -> bool:
        return self.connection.execute("SELECT EXISTS(SELECT 1 FROM cells)").fetchone()[0] == 1

    def cell_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM cells").fetchone()[0])

    def all_cells(self) -> list[Cell]:
        rows = self.connection.execute("SELECT id, content, created_at FROM cells ORDER BY id")
        return [Cell(row["id"], row["content"], row["created_at"]) for row in rows]

    def add_alias(self, alias: str, cell_id: int) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO cell_aliases (alias, cell_id) VALUES (?, ?)",
            (alias, cell_id),
        )

    def cells_by_alias(self, alias: str, limit: int = 8) -> list[Cell]:
        rows = self.connection.execute(
            """SELECT cells.*
               FROM cell_aliases
               JOIN cells ON cells.id = cell_aliases.cell_id
               LEFT JOIN cell_degrees AS d ON d.cell_id = cells.id
               WHERE cell_aliases.alias = ?
               ORDER BY COALESCE(d.last_used_at, 0) DESC,
                        COALESCE(d.use_count, 0) DESC,
                        cells.id ASC
               LIMIT ?""",
            (alias, limit),
        )
        return [Cell(row["id"], row["content"], row["created_at"]) for row in rows]

    def cell_by_alias(self, alias: str) -> Cell | None:
        matches = self.cells_by_alias(alias, limit=1)
        return matches[0] if matches else None

    def record_event(self, kind: str, payload: bytes, occurred_at: int) -> int:
        cursor = self.connection.execute(
            "INSERT INTO memory_events (kind, payload, occurred_at) VALUES (?, ?, ?)",
            (kind, payload, occurred_at),
        )
        return int(cursor.lastrowid)

    def add_edge(self, edge: Edge) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO edges (source_id, target_id, last_used_at, use_count) VALUES (?, ?, 0, 0)",
            (edge.source_id, edge.target_id),
        )

    def remove_edge(self, source_id: int, target_id: int) -> bool:
        """Remove a directed edge `(source_id, target_id)` and decrement materialized degree counters."""

        cursor = self.connection.execute(
            "DELETE FROM edges WHERE source_id = ? AND target_id = ?",
            (source_id, target_id),
        )
        return cursor.rowcount > 0

    def touch_edge(self, source_id: int, target_id: int, used_at: int) -> None:
        """Reinforce a synaptic edge when traversed, moving it to the front of recall order."""

        self.connection.execute(
            """UPDATE edges
               SET last_used_at = ?, use_count = use_count + 1
               WHERE source_id = ? AND target_id = ?""",
            (used_at, source_id, target_id),
        )

    def record_node_usage(self, node_id: int, used_at: int, *, exposed: bool = False, initial_count: int = 0) -> None:
        """Update usage without rewriting knowledge content or its search index."""
        self.connection.execute(
            """INSERT INTO node_usage (node_id, recall_count, exposure_count, last_recalled_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(node_id) DO UPDATE SET
                 recall_count = recall_count + ?,
                 exposure_count = exposure_count + excluded.exposure_count,
                 last_recalled_at = MAX(last_recalled_at, excluded.last_recalled_at)""",
            (node_id, initial_count + (0 if exposed else 1), 1 if exposed else 0, used_at, 0 if exposed else 1),
        )

    def node_usage(self, node_id: int) -> tuple[int, int] | None:
        row = self.connection.execute(
            "SELECT recall_count, last_recalled_at FROM node_usage WHERE node_id = ?", (node_id,)
        ).fetchone()
        return (int(row[0]), int(row[1])) if row else None

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

    def outgoing(self, source_id: int, limit: int | None = None) -> list[Edge]:
        if limit is not None:
            rows = self.connection.execute(
                """SELECT * FROM edges
                   WHERE source_id = ?
                   ORDER BY last_used_at DESC, use_count DESC, target_id ASC
                   LIMIT ?""",
                (source_id, limit),
            )
        else:
            rows = self.connection.execute(
                """SELECT * FROM edges
                   WHERE source_id = ?
                   ORDER BY last_used_at DESC, use_count DESC, target_id ASC""",
                (source_id,),
            )
        return [self._edge_from_row(row) for row in rows]

    def incoming(self, target_id: int, limit: int | None = None) -> list[Edge]:
        if limit is not None:
            rows = self.connection.execute(
                """SELECT * FROM edges
                   WHERE target_id = ?
                   ORDER BY last_used_at DESC, use_count DESC, source_id ASC
                   LIMIT ?""",
                (target_id, limit),
            )
        else:
            rows = self.connection.execute(
                """SELECT * FROM edges
                   WHERE target_id = ?
                   ORDER BY last_used_at DESC, use_count DESC, source_id ASC""",
                (target_id,),
            )
        return [self._edge_from_row(row) for row in rows]

    DEFAULT_FAMILY_LIMIT = 64

    def prefix_family_ids(self, prefix_id: int, limit: int | None = DEFAULT_FAMILY_LIMIT) -> tuple[int, ...]:
        """Return the hottest member IDs of the prefix family `prefix_id:*` (bounded by `limit`; `None` = all)."""

        return tuple(edge.target_id for edge in self.outgoing(prefix_id, limit=limit))

    def suffix_family_ids(self, suffix_id: int, limit: int | None = DEFAULT_FAMILY_LIMIT) -> tuple[int, ...]:
        """Return the hottest member IDs of the suffix family `*:suffix_id` (bounded by `limit`; `None` = all)."""

        return tuple(edge.source_id for edge in self.incoming(suffix_id, limit=limit))

    def node_family_memberships(
        self, node_id: int, limit: int | None = DEFAULT_FAMILY_LIMIT
    ) -> dict[str, tuple[int, ...]]:
        """Return the hottest prefix families (`P:*`) and suffix families (`*:S`) of `node_id` (bounded by `limit`)."""

        return {
            "prefix_families": tuple(edge.source_id for edge in self.incoming(node_id, limit=limit)),
            "suffix_families": tuple(edge.target_id for edge in self.outgoing(node_id, limit=limit)),
        }

    def out_degree(self, cell_id: int) -> int:
        """Return the outgoing degree of `cell_id` in O(1) from the materialized `cell_degrees` table."""

        row = self.connection.execute(
            "SELECT out_degree FROM cell_degrees WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()
        return int(row["out_degree"]) if row is not None else 0

    def in_degree(self, cell_id: int) -> int:
        """Return the incoming degree of `cell_id` in O(1) from the materialized `cell_degrees` table."""

        row = self.connection.execute(
            "SELECT in_degree FROM cell_degrees WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()
        return int(row["in_degree"]) if row is not None else 0

    def _anchor_degree(self, anchor_id: int) -> int:
        row = self.connection.execute(
            "SELECT out_degree + in_degree AS deg FROM cell_degrees WHERE cell_id = ?",
            (anchor_id,),
        ).fetchone()
        return int(row["deg"]) if row is not None else 0

    def _anchor_degrees(self, anchor_ids: Iterable[int]) -> dict[int, int]:
        ids = list(dict.fromkeys(int(a) for a in anchor_ids))
        if not ids:
            return {}
        placeholders = ", ".join("?" for _ in ids)
        rows = self.connection.execute(
            f"SELECT cell_id, out_degree + in_degree AS deg FROM cell_degrees WHERE cell_id IN ({placeholders})",
            tuple(ids),
        )
        result = {aid: 0 for aid in ids}
        for row in rows:
            result[int(row["cell_id"])] = int(row["deg"])
        return result

    def resolve_convergence(
        self,
        required_anchors: Iterable[int],
        *,
        context_anchors: Iterable[int] = (),
        excluded_ids: Iterable[int] = (),
        mode: Literal["strict", "associative"] = "strict",
        min_degree: int = 2,
        limit: int = 8,
        hot_k: int = 256,
        hot_min_exact: int = 1,
    ) -> ConvergenceResult:
        """Evaluate family intersections directly on SSD, separating required question anchors from conversation context.

        Uses O(1) materialized degree counters (`cell_degrees`) for seed selection + `PRIMARY KEY (source_id, target_id)`
        B-Tree probes so that large context families or the largest required family are probed by point lookup.

        When all required families are large (symmetric regime), a "hot first" pass is tried first: the candidate
        domain is limited to the `hot_k` hottest edges (per direction) of the smallest required family, read in
        order from `idx_edges_*_synaptic`. If it yields at least `hot_min_exact` exact matches the result is returned
        (`strategy="hot_first"`); otherwise the exhaustive query runs (`strategy="hot_first_fallback"`).
        Hot-first results are always truly exact, but colder exact matches outside the hot domain are not ranked.
        """

        t0 = time.perf_counter()
        req_list = list(dict.fromkeys(int(a) for a in required_anchors))
        req_set = set(req_list)
        ctx_list = [int(a) for a in dict.fromkeys(context_anchors) if int(a) not in req_set]
        all_anchors = [*req_list, *ctx_list]
        if not req_list or len(all_anchors) < min_degree:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ConvergenceResult(
                mode=mode,
                required_anchors=tuple(req_list),
                context_anchors=tuple(ctx_list),
                exact_matches=(),
                partial_matches=(),
                estimated_seed_edges=0,
                selection_ms=elapsed,
                query_ms=0.0,
                elapsed_ms=elapsed,
            )

        deg_map = self._anchor_degrees(all_anchors)
        sorted_req = sorted(req_list, key=lambda aid: deg_map[aid])
        if len(sorted_req) == 1:
            seed_anchors = sorted_req
        elif not ctx_list and min_degree >= 2:
            # Pigeonhole principle: any candidate matching >=2 of k required anchors must belong to the k-1 smallest anchors.
            seed_anchors = sorted_req[:-1]
        else:
            seed_anchors = sorted_req

        seed_deg = sum(deg_map[aid] for aid in seed_anchors)
        total_deg = sum(deg_map[aid] for aid in all_anchors)
        use_pk_probe = (ctx_list and seed_deg <= 256) or (seed_deg * len(all_anchors) * 2 < total_deg)

        excluded_list = list(dict.fromkeys([*req_list, *(int(x) for x in excluded_ids)]))
        values_sql = ", ".join("(?, 1)" for _ in req_list)
        if ctx_list:
            values_sql += ", " + ", ".join("(?, 0)" for _ in ctx_list)
        excluded_sql = ", ".join("?" for _ in excluded_list)
        row_limit = max(limit * 2, 16)
        t_select_done = time.perf_counter()
        selection_ms = (t_select_done - t0) * 1000.0
        req_total = len(req_list)
        ctx_total = len(ctx_list)
        hot_edges_read = 0
        strategy = "pk_probe" if use_pk_probe else "exhaustive"

        smallest_req = sorted_req[0]
        if not use_pk_probe and hot_k > 0 and deg_map[smallest_req] > hot_k:
            # "Hot first": candidate domain = top-K hottest edges (both directions) of the smallest required family,
            # read in index order from idx_edges_outgoing_synaptic / idx_edges_incoming_synaptic, then PK-probed.
            hot_query = f"""
                WITH hot_out AS (
                    SELECT target_id AS candidate_id FROM edges
                    WHERE source_id = ?
                    ORDER BY last_used_at DESC, use_count DESC, target_id ASC
                    LIMIT ?
                ),
                hot_in AS (
                    SELECT source_id AS candidate_id FROM edges
                    WHERE target_id = ?
                    ORDER BY last_used_at DESC, use_count DESC, source_id ASC
                    LIMIT ?
                ),
                candidate_domain AS (
                    SELECT candidate_id FROM (
                        SELECT candidate_id FROM hot_out
                        UNION
                        SELECT candidate_id FROM hot_in
                    )
                    WHERE candidate_id NOT IN ({excluded_sql})
                ),
                anchor_set(anchor_id, is_required) AS (
                    VALUES {values_sql}
                ),
                matched_edges AS (
                    SELECT cd.candidate_id AS candidate_id, a.anchor_id AS anchor_id, a.is_required AS is_required,
                           e.last_used_at AS last_used_at, e.use_count AS use_count
                    FROM candidate_domain cd
                    CROSS JOIN anchor_set a
                    CROSS JOIN edges e ON e.source_id = a.anchor_id AND e.target_id = cd.candidate_id
                    UNION ALL
                    SELECT cd.candidate_id AS candidate_id, a.anchor_id AS anchor_id, a.is_required AS is_required,
                           e.last_used_at AS last_used_at, e.use_count AS use_count
                    FROM candidate_domain cd
                    CROSS JOIN anchor_set a
                    CROSS JOIN edges e ON e.target_id = a.anchor_id AND e.source_id = cd.candidate_id
                )
                SELECT candidate_id,
                       COUNT(DISTINCT CASE WHEN is_required = 1 THEN anchor_id END) AS matched_required,
                       COUNT(DISTINCT CASE WHEN is_required = 0 THEN anchor_id END) AS matched_context,
                       COUNT(DISTINCT anchor_id) AS matched_total,
                       MAX(last_used_at) AS max_last_used_at,
                       SUM(use_count) AS sum_use_count
                FROM matched_edges
                GROUP BY candidate_id
                HAVING matched_required >= 1
                   AND matched_total >= ?
                ORDER BY matched_required DESC,
                         matched_context DESC,
                         max_last_used_at DESC,
                         sum_use_count DESC,
                         candidate_id ASC
                LIMIT ?
            """
            hot_params = (smallest_req, hot_k, smallest_req, hot_k, *excluded_list, *all_anchors, min_degree, row_limit)
            hot_rows = self.connection.execute(hot_query, hot_params).fetchall()
            hot_edges_read = min(self.out_degree(smallest_req), hot_k) + min(self.in_degree(smallest_req), hot_k)
            hot_exact, hot_partial = self._classify_rows(hot_rows, req_total, ctx_total, limit)
            if len(hot_exact) >= max(1, hot_min_exact):
                t_end = time.perf_counter()
                return ConvergenceResult(
                    mode=mode,
                    required_anchors=tuple(req_list),
                    context_anchors=tuple(ctx_list),
                    exact_matches=hot_exact,
                    partial_matches=hot_partial,
                    estimated_seed_edges=hot_edges_read,
                    selection_ms=selection_ms,
                    query_ms=(t_end - t_select_done) * 1000.0,
                    elapsed_ms=(t_end - t0) * 1000.0,
                    strategy="hot_first",
                )
            strategy = "hot_first_fallback"

        if use_pk_probe:
            # Asymmetric regime: seed candidates from the small family/families and probe large families by PRIMARY KEY
            seed_values_sql = ", ".join("(?)" for _ in seed_anchors)
            query = f"""
                WITH seed_set(anchor_id) AS (
                    VALUES {seed_values_sql}
                ),
                candidate_domain AS (
                    SELECT e.target_id AS candidate_id
                    FROM seed_set s
                    CROSS JOIN edges e ON e.source_id = s.anchor_id
                    WHERE e.target_id NOT IN ({excluded_sql})
                    UNION
                    SELECT e.source_id AS candidate_id
                    FROM seed_set s
                    CROSS JOIN edges e ON e.target_id = s.anchor_id
                    WHERE e.source_id NOT IN ({excluded_sql})
                ),
                anchor_set(anchor_id, is_required) AS (
                    VALUES {values_sql}
                ),
                matched_edges AS (
                    SELECT cd.candidate_id AS candidate_id,
                           a.anchor_id AS anchor_id,
                           a.is_required AS is_required,
                           e.last_used_at AS last_used_at,
                           e.use_count AS use_count
                    FROM candidate_domain cd
                    CROSS JOIN anchor_set a
                    CROSS JOIN edges e ON e.source_id = a.anchor_id AND e.target_id = cd.candidate_id
                    UNION ALL
                    SELECT cd.candidate_id AS candidate_id,
                           a.anchor_id AS anchor_id,
                           a.is_required AS is_required,
                           e.last_used_at AS last_used_at,
                           e.use_count AS use_count
                    FROM candidate_domain cd
                    CROSS JOIN anchor_set a
                    CROSS JOIN edges e ON e.target_id = a.anchor_id AND e.source_id = cd.candidate_id
                )
                SELECT candidate_id,
                       COUNT(DISTINCT CASE WHEN is_required = 1 THEN anchor_id END) AS matched_required,
                       COUNT(DISTINCT CASE WHEN is_required = 0 THEN anchor_id END) AS matched_context,
                       COUNT(DISTINCT anchor_id) AS matched_total,
                       MAX(last_used_at) AS max_last_used_at,
                       SUM(use_count) AS sum_use_count
                FROM matched_edges
                GROUP BY candidate_id
                HAVING matched_required >= 1
                   AND matched_total >= ?
                ORDER BY matched_required DESC,
                         matched_context DESC,
                         max_last_used_at DESC,
                         sum_use_count DESC,
                         candidate_id ASC
                LIMIT ?
            """
            params: tuple[int, ...] = (*seed_anchors, *excluded_list, *excluded_list, *all_anchors, min_degree, row_limit)
            estimated_seed_edges = seed_deg
        else:
            # Symmetric regime: single-pass index scan over incident edges + group-by
            query = f"""
                WITH anchor_set(anchor_id, is_required) AS (
                    VALUES {values_sql}
                ),
                incident_edges AS (
                    SELECT e.target_id AS candidate_id,
                           e.source_id AS anchor_id,
                           a.is_required AS is_required,
                           e.last_used_at AS last_used_at,
                           e.use_count AS use_count
                    FROM anchor_set a
                    CROSS JOIN edges e ON e.source_id = a.anchor_id
                    UNION ALL
                    SELECT e.source_id AS candidate_id,
                           e.target_id AS anchor_id,
                           a.is_required AS is_required,
                           e.last_used_at AS last_used_at,
                           e.use_count AS use_count
                    FROM anchor_set a
                    CROSS JOIN edges e ON e.target_id = a.anchor_id
                )
                SELECT candidate_id,
                       COUNT(DISTINCT CASE WHEN is_required = 1 THEN anchor_id END) AS matched_required,
                       COUNT(DISTINCT CASE WHEN is_required = 0 THEN anchor_id END) AS matched_context,
                       COUNT(DISTINCT anchor_id) AS matched_total,
                       MAX(last_used_at) AS max_last_used_at,
                       SUM(use_count) AS sum_use_count
                FROM incident_edges
                WHERE candidate_id NOT IN ({excluded_sql})
                GROUP BY candidate_id
                HAVING matched_required >= 1
                   AND matched_total >= ?
                ORDER BY matched_required DESC,
                         matched_context DESC,
                         max_last_used_at DESC,
                         sum_use_count DESC,
                         candidate_id ASC
                LIMIT ?
            """
            params = (*all_anchors, *excluded_list, min_degree, row_limit)
            estimated_seed_edges = total_deg

        rows = self.connection.execute(query, params).fetchall()
        exact, partial = self._classify_rows(rows, req_total, ctx_total, limit)

        t_end = time.perf_counter()
        query_ms = (t_end - t_select_done) * 1000.0
        elapsed_ms = (t_end - t0) * 1000.0
        return ConvergenceResult(
            mode=mode,
            required_anchors=tuple(req_list),
            context_anchors=tuple(ctx_list),
            exact_matches=exact,
            partial_matches=partial,
            estimated_seed_edges=estimated_seed_edges + hot_edges_read,
            selection_ms=selection_ms,
            query_ms=query_ms,
            elapsed_ms=elapsed_ms,
            strategy=strategy,
        )

    @staticmethod
    def _classify_rows(
        rows: Iterable[sqlite3.Row], req_total: int, ctx_total: int, limit: int
    ) -> tuple[tuple[ConvergenceMatch, ...], tuple[ConvergenceMatch, ...]]:
        exact: list[ConvergenceMatch] = []
        partial: list[ConvergenceMatch] = []
        for row in rows:
            match = ConvergenceMatch(
                node_id=int(row["candidate_id"]),
                matched_required=int(row["matched_required"]),
                required_total=req_total,
                matched_context=int(row["matched_context"]),
                context_total=ctx_total,
                max_last_used_at=int(row["max_last_used_at"]),
                sum_use_count=int(row["sum_use_count"]),
            )
            if match.is_exact:
                if len(exact) < limit:
                    exact.append(match)
            elif len(partial) < limit:
                partial.append(match)
        return tuple(exact), tuple(partial)

    def shared_neighbors(
        self,
        anchor_ids: list[int] | tuple[int, ...] | set[int],
        *,
        mode: Literal["strict", "associative"] = "associative",
        min_degree: int = 2,
        limit: int = 8,
    ) -> list[int]:
        """Intersect prefix (`P:*`) and suffix (`*:S`) families of `anchor_ids` to find shared member nodes."""

        res = self.resolve_convergence(
            anchor_ids,
            mode=mode,
            min_degree=min_degree,
            limit=limit,
        )
        return list(res.ranked_ids)

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
                source_id     INTEGER NOT NULL REFERENCES cells(id),
                target_id     INTEGER NOT NULL REFERENCES cells(id),
                last_used_at  INTEGER NOT NULL DEFAULT 0,
                use_count     INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (source_id, target_id)
            ) WITHOUT ROWID, STRICT;

            CREATE INDEX IF NOT EXISTS edges_by_target
                ON edges (target_id, source_id);

            CREATE TABLE IF NOT EXISTS cell_degrees (
                cell_id     INTEGER PRIMARY KEY REFERENCES cells(id) ON DELETE CASCADE,
                out_degree  INTEGER NOT NULL DEFAULT 0,
                in_degree   INTEGER NOT NULL DEFAULT 0
            ) WITHOUT ROWID, STRICT;

            CREATE TRIGGER IF NOT EXISTS trg_edges_ai_degrees
            AFTER INSERT ON edges
            BEGIN
                INSERT INTO cell_degrees (cell_id, out_degree, in_degree)
                VALUES (NEW.source_id, 1, 0)
                ON CONFLICT(cell_id) DO UPDATE SET out_degree = out_degree + 1;

                INSERT INTO cell_degrees (cell_id, out_degree, in_degree)
                VALUES (NEW.target_id, 0, 1)
                ON CONFLICT(cell_id) DO UPDATE SET in_degree = in_degree + 1;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_edges_ad_degrees
            AFTER DELETE ON edges
            BEGIN
                UPDATE cell_degrees SET out_degree = MAX(0, out_degree - 1) WHERE cell_id = OLD.source_id;
                UPDATE cell_degrees SET in_degree = MAX(0, in_degree - 1) WHERE cell_id = OLD.target_id;
            END;

            CREATE VIRTUAL TABLE IF NOT EXISTS cell_search USING fts5(
                cell_id UNINDEXED,
                kind,
                text
            );

            CREATE TABLE IF NOT EXISTS cell_aliases (
                alias    TEXT NOT NULL,
                cell_id  INTEGER NOT NULL REFERENCES cells(id),
                PRIMARY KEY (alias, cell_id)
            ) WITHOUT ROWID, STRICT;

            CREATE INDEX IF NOT EXISTS idx_cell_aliases_alias
                ON cell_aliases (alias);

            CREATE TABLE IF NOT EXISTS memory_events (
                id           INTEGER PRIMARY KEY,
                kind         TEXT NOT NULL,
                payload      BLOB NOT NULL,
                occurred_at  INTEGER NOT NULL
            ) STRICT;

            CREATE TABLE IF NOT EXISTS node_usage (
                node_id INTEGER PRIMARY KEY REFERENCES cells(id) ON DELETE CASCADE,
                recall_count INTEGER NOT NULL DEFAULT 0,
                exposure_count INTEGER NOT NULL DEFAULT 0,
                last_recalled_at INTEGER NOT NULL DEFAULT 0
            ) STRICT;

            CREATE TABLE IF NOT EXISTS task_state (
                name TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            ) STRICT;
            """
        )

    def _ensure_edge_usage_columns(self) -> None:
        columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(edges)")}
        if "last_used_at" not in columns:
            self.connection.execute("ALTER TABLE edges ADD COLUMN last_used_at INTEGER NOT NULL DEFAULT 0")
        if "use_count" not in columns:
            self.connection.execute("ALTER TABLE edges ADD COLUMN use_count INTEGER NOT NULL DEFAULT 0")
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_outgoing_synaptic ON edges (source_id, last_used_at DESC, use_count DESC, target_id ASC)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_incoming_synaptic ON edges (target_id, last_used_at DESC, use_count DESC, source_id ASC)"
        )
        has_degrees = self.connection.execute("SELECT EXISTS(SELECT 1 FROM cell_degrees)").fetchone()[0] == 1
        has_edges = self.connection.execute("SELECT EXISTS(SELECT 1 FROM edges)").fetchone()[0] == 1
        if has_edges and not has_degrees:
            self.connection.executescript(
                """
                INSERT INTO cell_degrees (cell_id, out_degree, in_degree)
                SELECT source_id, COUNT(*), 0 FROM edges GROUP BY source_id
                ON CONFLICT(cell_id) DO UPDATE SET out_degree = excluded.out_degree;

                INSERT INTO cell_degrees (cell_id, out_degree, in_degree)
                SELECT target_id, 0, COUNT(*) FROM edges GROUP BY target_id
                ON CONFLICT(cell_id) DO UPDATE SET in_degree = excluded.in_degree;
                """
            )
        alias_pk_cols = [
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(cell_aliases)")
            if int(row["pk"]) > 0
        ]
        if alias_pk_cols == ["alias"]:
            self.connection.executescript(
                """
                CREATE TABLE cell_aliases_new (
                    alias    TEXT NOT NULL,
                    cell_id  INTEGER NOT NULL REFERENCES cells(id),
                    PRIMARY KEY (alias, cell_id)
                ) WITHOUT ROWID, STRICT;
                INSERT OR IGNORE INTO cell_aliases_new (alias, cell_id)
                    SELECT alias, cell_id FROM cell_aliases;
                DROP TABLE cell_aliases;
                ALTER TABLE cell_aliases_new RENAME TO cell_aliases;
                CREATE INDEX IF NOT EXISTS idx_cell_aliases_alias ON cell_aliases (alias);
                """
            )
        self.connection.commit()

    def _ensure_cell_usage_summary(self) -> None:
        """Migrate once, then maintain exact alias-ranking aggregates transactionally."""
        # Each endpoint uses its ordered index: decreasing/deleting a maximum never scans a hub.
        latest = """COALESCE((SELECT MAX(stamp) FROM (
            SELECT (SELECT last_used_at FROM edges WHERE source_id = cell_degrees.cell_id
                    ORDER BY last_used_at DESC, use_count DESC, target_id ASC LIMIT 1) AS stamp
            UNION ALL
            SELECT (SELECT last_used_at FROM edges WHERE target_id = cell_degrees.cell_id
                    ORDER BY last_used_at DESC, use_count DESC, source_id ASC LIMIT 1)
        )), 0)"""
        with self.transaction():
            columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(cell_degrees)")}
            migrate = "last_used_at" not in columns or "use_count" not in columns
            for column in ("last_used_at", "use_count"):
                if column not in columns:
                    self.connection.execute(f"ALTER TABLE cell_degrees ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0")
            if migrate:
                self.connection.execute(f"""UPDATE cell_degrees SET last_used_at = {latest},
                    use_count = COALESCE((SELECT SUM(use_count) FROM edges WHERE source_id = cell_degrees.cell_id), 0)
                              + COALESCE((SELECT SUM(use_count) FROM edges WHERE target_id = cell_degrees.cell_id
                                          AND source_id != target_id), 0)""")
            self.connection.execute(f"""CREATE TRIGGER IF NOT EXISTS trg_edges_ai_usage
                AFTER INSERT ON edges BEGIN
                    INSERT INTO cell_degrees(cell_id, last_used_at, use_count)
                    VALUES(NEW.source_id, NEW.last_used_at, NEW.use_count)
                    ON CONFLICT(cell_id) DO UPDATE SET
                        last_used_at = {latest}, use_count = cell_degrees.use_count + NEW.use_count;
                    INSERT INTO cell_degrees(cell_id, last_used_at, use_count)
                    SELECT NEW.target_id, NEW.last_used_at, NEW.use_count WHERE NEW.target_id != NEW.source_id
                    ON CONFLICT(cell_id) DO UPDATE SET
                        last_used_at = {latest}, use_count = cell_degrees.use_count + NEW.use_count;
                END""")
            self.connection.execute(f"""CREATE TRIGGER IF NOT EXISTS trg_edges_au_usage
                AFTER UPDATE OF last_used_at, use_count ON edges BEGIN
                    UPDATE cell_degrees SET last_used_at = {latest},
                        use_count = MAX(0, use_count + NEW.use_count - OLD.use_count)
                    WHERE cell_id IN (NEW.source_id, NEW.target_id);
                END""")
            self.connection.execute(f"""CREATE TRIGGER IF NOT EXISTS trg_edges_ad_usage
                AFTER DELETE ON edges BEGIN
                    UPDATE cell_degrees SET last_used_at = {latest},
                        use_count = MAX(0, use_count - OLD.use_count)
                    WHERE cell_id IN (OLD.source_id, OLD.target_id);
                END""")
            self.connection.execute("""CREATE TRIGGER IF NOT EXISTS trg_edges_immutable_address
                BEFORE UPDATE OF source_id, target_id ON edges
                WHEN NEW.source_id != OLD.source_id OR NEW.target_id != OLD.target_id
                BEGIN SELECT RAISE(ABORT, 'Edge addresses are immutable; remove and insert the edge instead.'); END""")

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
        from .node import KnowledgeNode
        title = KnowledgeNode.from_cell(cell).title
        self.connection.execute("INSERT INTO node_catalog VALUES (?, ?) ON CONFLICT(node_id) DO UPDATE SET title=excluded.title", (cell.id, title))
        try:
            payload = json.loads(cell.content)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            payload = {"kind": "raw", "text": cell.content.decode("utf-8", errors="replace")}
        if not isinstance(payload, dict):
            payload = {"kind": "raw", "text": str(payload)}

        kind = str(payload.get("kind") or "unknown")
        terms: list[str] = [
            str(payload.get("label") or ""),
            str(payload.get("title") or ""),
            str(payload.get("slug") or ""),
            str(payload.get("content") or ""),
            str(payload.get("text") or ""),
        ]
        for list_key in ("forms", "keywords"):
            items = payload.get(list_key)
            if isinstance(items, list):
                terms.extend(str(item) for item in items)
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
