"""Deterministic CPU reference for Luca's bounded local thought process.

This module is deliberately independent from a GPU runtime. A future GPU
backend must reproduce this work model before it may be used as an accelerator.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from .store import Edge, MemoryStore


@dataclass(frozen=True, slots=True)
class ThoughtBudget:
    """Explicit bounds that keep a thought from expanding without limit."""

    max_depth: int = 3
    ram_cells: int = 5_000
    ram_edges: int = 20_000
    vram_cells: int = 512
    propagation_decay: float = 0.75


@dataclass(frozen=True, slots=True)
class ThoughtRequest:
    seed_cells: tuple[int, ...]
    budget: ThoughtBudget = ThoughtBudget()


@dataclass(frozen=True, slots=True)
class Traversal:
    from_cell: int
    to_cell: int
    edge: Edge
    depth: int
    activation: float


@dataclass(frozen=True, slots=True)
class ThoughtResult:
    """A traceable proposal, not a persistent change to Luca's memory."""

    context_cells: tuple[int, ...]
    context_edges: tuple[Edge, ...]
    vram_focus: tuple[int, ...]
    traversals: tuple[Traversal, ...]


class ThoughtEngine:
    """Expand a local graph neighbourhood with bounded, deterministic search.

    The RAM context contains every retained cell and edge. ``vram_focus`` is
    the narrower, highest-activation subset that a GPU worker would receive.
    No state is written to cells, edges, or disk by this class.
    """

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def run(self, request: ThoughtRequest) -> ThoughtResult:
        budget = request.budget
        if not request.seed_cells:
            return ThoughtResult((), (), (), ())
        if min(budget.max_depth, budget.ram_cells, budget.ram_edges, budget.vram_cells) < 1:
            raise ValueError("Every thought budget must be positive.")
        if not 0 < budget.propagation_decay <= 1:
            raise ValueError("propagation_decay must be in (0, 1].")

        activations = {cell_id: 1.0 for cell_id in sorted(set(request.seed_cells))}
        queue = [(-1.0, 0, cell_id) for cell_id in activations]
        heapq.heapify(queue)
        retained_edges: dict[tuple[int, int], Edge] = {}
        traversals: list[Traversal] = []
        expanded: set[tuple[int, int]] = set()

        while queue and len(activations) < budget.ram_cells and len(retained_edges) < budget.ram_edges:
            negative_activation, depth, current = heapq.heappop(queue)
            activation = -negative_activation
            if (current, depth) in expanded or depth >= budget.max_depth:
                continue
            expanded.add((current, depth))

            neighbours = [
                *((edge, edge.target_id) for edge in self.store.outgoing(current)),
                *((edge, edge.source_id) for edge in self.store.incoming(current)),
            ]
            for edge, neighbour in neighbours:
                if len(retained_edges) >= budget.ram_edges:
                    break
                if neighbour not in activations and len(activations) >= budget.ram_cells:
                    continue
                retained_edges[(edge.source_id, edge.target_id)] = edge
                next_activation = activation * budget.propagation_decay
                if next_activation > activations.get(neighbour, 0.0):
                    activations[neighbour] = next_activation
                    heapq.heappush(queue, (-next_activation, depth + 1, neighbour))
                    traversals.append(Traversal(current, neighbour, edge, depth + 1, next_activation))

        ranked_cells = sorted(activations, key=lambda cell_id: (-activations[cell_id], cell_id))
        return ThoughtResult(
            context_cells=tuple(ranked_cells),
            context_edges=tuple(sorted(retained_edges.values(), key=lambda edge: (edge.source_id, edge.target_id))),
            vram_focus=tuple(ranked_cells[: budget.vram_cells]),
            traversals=tuple(traversals),
        )
