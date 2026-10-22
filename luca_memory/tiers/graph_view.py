"""Self-assembling domino graph view and prefix/suffix families over `prefix:suffix` edges."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from ..store import Edge


@dataclass(frozen=True, slots=True)
class SynapticFamily:
    """Explicit family of nodes derived directly from shared prefix (`P:*`) or suffix (`*:S`) edges."""

    anchor_id: int
    direction: Literal["prefix", "suffix"]
    member_ids: tuple[int, ...]
    edges: tuple[Edge, ...]

    @property
    def pattern(self) -> str:
        return f"{self.anchor_id}:*" if self.direction == "prefix" else f"*:{self.anchor_id}"


class GraphView:
    """Maintain `prefix:suffix` edges for a tier and assemble domino chains and prefix/suffix families."""

    def __init__(self) -> None:
        self._edges: dict[tuple[int, int], Edge] = {}

    def add_edge(self, edge: Edge) -> None:
        self._edges[(edge.source_id, edge.target_id)] = edge

    def add_edges(self, edges: Iterable[Edge]) -> None:
        for edge in edges:
            self.add_edge(edge)

    def edges(self) -> tuple[Edge, ...]:
        return tuple(self._edges.values())

    def incoming_for(self, node_id: int) -> tuple[Edge, ...]:
        """Return all active edges with suffix `:node_id` (`*:B`)."""

        return tuple(edge for edge in self._edges.values() if edge.target_id == node_id)

    def outgoing_for(self, node_id: int) -> tuple[Edge, ...]:
        """Return all active edges with prefix `node_id:` (`B:*`)."""

        return tuple(edge for edge in self._edges.values() if edge.source_id == node_id)

    def prefix_family(self, prefix_id: int) -> SynapticFamily:
        """Return the family `prefix_id:*` of all nodes sharing `prefix_id` as their incoming prefix."""

        edges = self.outgoing_for(prefix_id)
        members = tuple(dict.fromkeys(edge.target_id for edge in edges))
        return SynapticFamily(
            anchor_id=prefix_id,
            direction="prefix",
            member_ids=members,
            edges=edges,
        )

    def suffix_family(self, suffix_id: int) -> SynapticFamily:
        """Return the family `*:suffix_id` of all nodes sharing `suffix_id` as their outgoing suffix."""

        edges = self.incoming_for(suffix_id)
        members = tuple(dict.fromkeys(edge.source_id for edge in edges))
        return SynapticFamily(
            anchor_id=suffix_id,
            direction="suffix",
            member_ids=members,
            edges=edges,
        )

    def families(self, min_members: int = 2) -> list[SynapticFamily]:
        """Extract all active prefix families (`P:*`) and suffix families (`*:S`) with at least `min_members`."""

        prefix_anchors: list[int] = []
        suffix_anchors: list[int] = []
        for edge in self._edges.values():
            if edge.source_id not in prefix_anchors:
                prefix_anchors.append(edge.source_id)
            if edge.target_id not in suffix_anchors:
                suffix_anchors.append(edge.target_id)

        result: list[SynapticFamily] = []
        for prefix_id in prefix_anchors:
            fam = self.prefix_family(prefix_id)
            if len(fam.member_ids) >= min_members:
                result.append(fam)
        for suffix_id in suffix_anchors:
            fam = self.suffix_family(suffix_id)
            if len(fam.member_ids) >= min_members:
                result.append(fam)
        return result

    def prune_to_nodes(self, active_node_ids: set[int]) -> list[Edge]:
        """Retain only edges whose prefix and suffix are both in `active_node_ids`; return removed edges."""

        kept: dict[tuple[int, int], Edge] = {}
        removed: list[Edge] = []
        for key, edge in self._edges.items():
            if edge.source_id in active_node_ids and edge.target_id in active_node_ids:
                kept[key] = edge
            else:
                removed.append(edge)
        self._edges = kept
        return removed

    def chains(self, max_length: int = 8) -> list[tuple[int, ...]]:
        """Assemble ordered domino chains `A -> B -> C` where suffix of `A:B` matches prefix of `B:C`."""

        if not self._edges:
            return []
        outgoing: dict[int, list[int]] = {}
        incoming_count: dict[int, int] = {}
        nodes: set[int] = set()
        for edge in self._edges.values():
            outgoing.setdefault(edge.source_id, []).append(edge.target_id)
            incoming_count[edge.target_id] = incoming_count.get(edge.target_id, 0) + 1
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)

        heads = [node for node in nodes if incoming_count.get(node, 0) == 0]
        if not heads:
            heads = sorted(nodes)

        assembled: list[tuple[int, ...]] = []

        def _walk(path: list[int]) -> None:
            current = path[-1]
            next_targets = [target for target in outgoing.get(current, []) if target not in path]
            if not next_targets or len(path) >= max_length:
                if len(path) >= 2:
                    assembled.append(tuple(path))
                return
            for target in next_targets:
                _walk([*path, target])

        for head in heads:
            _walk([head])
        return assembled

