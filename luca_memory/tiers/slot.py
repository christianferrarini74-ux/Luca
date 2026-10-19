"""Bounded LRU memory slot for VRAM and RAM tiers."""

from __future__ import annotations

from collections import OrderedDict
from typing import Iterable

from ..node import KnowledgeNode
from ..budget import payload_size, cache_view


class TierSlot:
    """Fixed-capacity slot where recalled nodes jump to the head and unused nodes slide to the tail."""

    def __init__(self, name: str, capacity: int, max_bytes: int | None = None, *, compact: bool = True) -> None:
        if capacity < 1:
            raise ValueError(f"TierSlot '{name}' capacity must be >= 1.")
        self.name = name
        self.capacity = capacity
        if max_bytes is not None and max_bytes < 2048:
            raise ValueError("Cache payload budget must be at least 2048 bytes.")
        self.max_bytes = max_bytes
        self.compact = compact
        self._nodes: OrderedDict[int, KnowledgeNode] = OrderedDict()

    def __len__(self) -> int:
        return len(self._nodes)

    @property
    def used_bytes(self) -> int:
        return sum(payload_size(node) for node in self._nodes.values())

    def __contains__(self, node_id: int) -> bool:
        return node_id in self._nodes

    def get(self, node_id: int) -> KnowledgeNode | None:
        return self._nodes.get(node_id)

    def node_ids(self) -> tuple[int, ...]:
        """Return node IDs ordered from most recently recalled (head) to oldest (tail)."""

        return tuple(self._nodes.keys())

    def nodes(self) -> tuple[KnowledgeNode, ...]:
        """Return nodes ordered from most recently recalled (head) to oldest (tail)."""

        return tuple(self._nodes.values())

    def promote(self, node: KnowledgeNode) -> list[KnowledgeNode]:
        """Place `node` at the head of the slot and return any oldest nodes evicted from the tail."""

        if self.max_bytes and not self.compact and payload_size(node) > self.max_bytes:
            self._nodes.pop(node.id, None)
            return [node]
        node = cache_view(node, self.max_bytes) if self.max_bytes and self.compact else node
        self._nodes[node.id] = node
        self._nodes.move_to_end(node.id, last=False)
        evicted: list[KnowledgeNode] = []
        while len(self._nodes) > self.capacity or (self.max_bytes is not None and self.used_bytes > self.max_bytes):
            _, oldest = self._nodes.popitem(last=True)
            evicted.append(oldest)
        return evicted

    def promote_many(self, nodes: Iterable[KnowledgeNode]) -> list[KnowledgeNode]:
        """Promote a sequence of nodes so the first item in `nodes` ends up at the very head."""

        ordered = list(nodes)
        evicted: list[KnowledgeNode] = []
        for node in reversed(ordered):
            evicted.extend(self.promote(node))
        # Filter out any node that was re-promoted inside the same batch
        active_ids = set(self._nodes.keys())
        return [item for item in evicted if item.id not in active_ids]

    def remove(self, node_id: int) -> KnowledgeNode | None:
        """Remove and return a node if present (e.g., when promoted to a higher tier)."""

        return self._nodes.pop(node_id, None)

    def close(self) -> None:
        self._nodes.clear()
