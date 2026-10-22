"""Repeatable synthetic workload for the first Luca storage experiment."""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

from .store import Cell, Edge, MemoryStore
from .thought import ThoughtBudget, ThoughtEngine, ThoughtRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells", type=int, default=1_000_000)
    parser.add_argument("--edges", type=int, default=10_000_000)
    parser.add_argument("--database", type=Path, default=Path("luca-benchmark.sqlite"))
    parser.add_argument("--queries", type=int, default=1_000)
    parser.add_argument("--depth", type=int, default=3, help="Maximum local thought depth")
    return parser.parse_args()


def edge_for(number: int, cell_count: int) -> tuple[int, int]:
    """Return a stable, collision-free pair while edges <= cells squared."""
    source_zero_based = number % cell_count
    source = source_zero_based + 1
    target = (source_zero_based + number // cell_count) % cell_count + 1
    return source, target


def seconds_since(start: float) -> float:
    return time.perf_counter() - start


def main() -> None:
    args = parse_args()
    if args.cells < 1 or args.edges < 1 or args.edges > args.cells * args.cells:
        raise SystemExit("Require cells >= 1 and 1 <= edges <= cells squared.")
    if args.database.exists():
        raise SystemExit(f"Refusing to overwrite existing database: {args.database}")

    now = int(time.time())
    started = time.perf_counter()
    with MemoryStore(args.database) as store:
        with store.transaction():
            for cell_id in range(1, args.cells + 1):
                store.add_cell(Cell(cell_id, f"synthetic-cell-{cell_id}".encode(), now))
        cell_seconds = seconds_since(started)

        edge_started = time.perf_counter()
        with store.transaction():
            for number in range(args.edges):
                source, target = edge_for(number, args.cells)
                store.add_edge(Edge(source, target))
        edge_seconds = seconds_since(edge_started)

        probes = random.Random(0).sample(range(args.edges), min(args.queries, args.edges))
        exact_started = time.perf_counter()
        for number in probes:
            source, target = edge_for(number, args.cells)
            assert store.edge(source, target) is not None
        exact_seconds = seconds_since(exact_started)

        source, target = edge_for(probes[0], args.cells)
        outgoing_started = time.perf_counter()
        outgoing = store.outgoing(source)
        outgoing_seconds = seconds_since(outgoing_started)
        incoming_started = time.perf_counter()
        incoming = store.incoming(target)
        incoming_seconds = seconds_since(incoming_started)
        thought_started = time.perf_counter()
        thought = ThoughtEngine(store).run(
            ThoughtRequest((source,), ThoughtBudget(max_depth=args.depth, ram_cells=5_000, ram_edges=20_000, vram_cells=512))
        )
        thought_seconds = seconds_since(thought_started)

    size = args.database.stat().st_size
    print(f"cells: {args.cells:,} in {cell_seconds:.3f}s")
    print(f"edges: {args.edges:,} in {edge_seconds:.3f}s ({args.edges / edge_seconds:,.0f}/s)")
    print(f"exact lookups: {len(probes):,} in {exact_seconds:.3f}s ({exact_seconds / len(probes) * 1e6:.1f} us/lookup)")
    print(f"outgoing {source}: {len(outgoing):,} edges in {outgoing_seconds * 1e3:.3f} ms")
    print(f"incoming {target}: {len(incoming):,} edges in {incoming_seconds * 1e3:.3f} ms")
    print(f"local thought: {len(thought.context_cells):,} cells, {len(thought.context_edges):,} edges, {len(thought.vram_focus):,} VRAM candidates in {thought_seconds * 1e3:.3f} ms")
    print(f"database: {size / 1_000_000:.2f} MB at {args.database}")


if __name__ == "__main__":
    main()
