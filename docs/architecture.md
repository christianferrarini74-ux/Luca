# Luca: logical architecture

## Governing rule

Luca works on cells. An edge is never a hidden claim, label, or unit of truth; it is only a stable directed address between two cells.

```text
CELL  = persistent content and cognitive state
EDGE  = source_id : target_id
```

Cells may represent a concept (`fuoco`), a relation-concept (`scalda`), an experience, a question, a hypothesis, evidence, or a conclusion. The route `fuoco → scalda → ferro` can therefore be activated, inspected, reinforced, disputed, or reused without adding semantics to its edges.

## Direct memory

Each edge exists in two physical orderings:

```text
forward index  [source_id, target_id]  answers A:*
reverse index  [target_id, source_id]  answers *:B
```

This is Luca's guaranteed local navigation. It discovers correlated material through shared cells and repeated routes, without an associative/vector search.

## Memory scopes

```text
SSD
  Complete persistent brain: cells, edges, durable indexes, append-only changes.

RAM
  Current context: requested cells, their topological neighbourhood, cached regions,
  coordinator state, and pending changes.

VRAM
  The narrow working set for one active thought: selected cell identifiers,
  edges, compact numeric state, and activation values.
```

SSD is authoritative. RAM is a mutable operational cache. VRAM contains disposable snapshots; a GPU cannot commit a change to the brain.

## Thought lifecycle

1. A trigger selects seed cells and an explicit objective.
2. RAM loads the seeds and the nearby `A:*` / `*:B` neighbourhood.
3. The coordinator expands a bounded frontier and scores candidates.
4. A smaller focus is promoted to VRAM for parallel evaluation when a GPU exists.
5. Results return as proposals with a trace, not direct memory writes.
6. A single consolidator validates, merges, and persists accepted changes.

Each thought has fixed budgets: depth, RAM cells, RAM edges, VRAM cells, and time. Budgets are both an engineering limit and a cognitive discipline.

## Compute roles

The CPU implementation is the reference semantics. A GPU backend may accelerate propagation, candidate scoring, and associative search only after parity tests against the CPU reference.

With multiple GPUs, the coordinator may split independent branches of one thought. Each branch receives a read-only snapshot and its own budget. Workers return ranked candidates, evidence, and traces; the consolidator remains the sole writer. Direct GPU-to-GPU transfer may be an optimisation, never an architectural dependency.

## Associative jumps: a later layer

The future associative index is not a database of text embeddings. It indexes compact, learned addresses that point back to cells. Those addresses may be shaped by graph topology, co-activation history, and roles in repeated paths. It may propose distant candidates; Luca must verify them by loading the actual graph neighbourhood.

Two completely disconnected regions with no shared cell, co-activation, observed regularity, or external bridge contain no signal from which to infer similarity. This is a boundary condition to test, not a gap to hide.
