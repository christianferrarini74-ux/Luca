# Review hardening — Phase 1.10

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

Date: 2026-10-19

[Italiano](it/fase-1-sinapsi/10-verifica-claude.md)

Scope: verify Claude's review on local hardware, preserve personal knowledge,
and remove measured bottlenecks without adding dependencies or integrating Cesare.
All fixtures are synthetic and temporary under the configured test directory.

## Seed identities and topology

Seed metadata now includes a SHA-256 structural fingerprint of the canonical
slug-to-ID map and directed edge set. Node order matters because it defines IDs;
edge-list order and duplicate identical edges do not change graph identity.
The fingerprint identifies topology, not mutable knowledge text or personal additions.

New seed events store both version and fingerprint. Opening a database checks
both and rejects incompatible seed structure without refreshing or rewriting it.
A matching version alone no longer accepts reordered, added or removed seed nodes.
Personal nodes added beyond the seed remain allowed, irrespective of total count.
Duplicate/empty slugs and unknown edge endpoints are rejected before an explicit
experimental seed refresh can delete anything.

Legacy events without a fingerprint are checked against the stored slug at each
expected ID, without updating the event. This deliberately does not invent a
historical topology fingerprint: the original topology cannot be proven from a
library that may have legitimately gained or lost edges. A legacy identity match
is therefore weaker than a fingerprinted seed match.

Tests cover unchanged seeds, edge-list ordering, same-version append/removal/
reordering/topology changes, read-only legacy acceptance/rejection, personal
growth and invalid seed preservation. Version changes still require an explicit
migration or a separate experimental database; changing the version is not a
command to replace existing knowledge.

## Exact materialized alias ranking

`cells_by_alias` now joins per-cell usage in `cell_degrees` rather than aggregating
all incident edges for each lookup. One transactional migration adds columns,
backfills them, then creates the usage triggers. Incoming/outgoing ordering
indexes are created only after legacy edge-usage columns exist.

Unlike the proposed historical maximum, recency remains the exact maximum over
currently existing incident edges. Deleting the newest edge or lowering its
timestamp can therefore change the winner exactly as before. Each update uses
two ordered index-head lookups per affected cell, not a hub-sized scan. Insert,
update and delete all maintain usage, independent of degree-trigger order.
Self-loops contribute once to usage, matching the old `OR` join, although they
still contribute one incoming and one outgoing degree. Endpoint IDs are immutable
edge addresses; change an address by removing and inserting an edge.

Tests compare materialized values and ranking against the original aggregation
after 100 deterministic random operations, plus ties, isolated aliases, nonzero
inserts, self-loops, rollback, newest-edge deletion, timestamp decreases, old
schemas with/without usage columns and repeated reopen without double counting.

## Local alias benchmark

`python -m luca_memory.review_benchmark --mode aliases --repeats 15`

Fixture: a temporary SQLite database on D:, 500,000 synthetic cells, a 100,000-edge
hub, and an isolated cell sharing its alias. Two warmups precede 15 timed lookups.
The reference executes the old aggregation; current also constructs Cell objects.

| Lookup | Median | p95 |
| --- | ---: | ---: |
| Original aggregation | 43.491 ms | 44.294 ms |
| Materialized summary | 0.0166 ms | 0.0205 ms |

For 100 timed touches inside an open transaction, SQL median was 0.00520 ms with
usage maintenance and 0.00175 ms without it: about 0.00345 ms extra here. The
benchmark disables triggers only inside its disposable fixture and rolls back
after measurement. These are warm SQL timings, not commit/fsync or startup
migration timings, and not a universal performance guarantee.

## GPU transfers: measured, then minimized

The initial benchmark established a non-negligible cost, so the implementation
was changed. DeviceSlot reuses an allocation only when serialized length and
SHA-256 match its verified payload. Reused entries are excluded from the free
path. Changed recall metadata changes the payload and still requires an upload.
New or changed allocations retain upload/readback verification; reads still
verify integrity. Tests cover unchanged pointer reuse, metadata changes and
failure of a neighboring upload without freeing the reused pointer.

Rather than adding a turn-scoped host cache with invalidation rules, connected
component traversal now uses IDs and graph metadata only: zero payload reads.
Context assembly downloads only opened nodes to be exposed. The deterministic
response path reads the focus only, not every node. This removes redundant work
at its source without retaining a second host payload cache. Dashboard snapshots
still read nodes and their actual transfer cost remains visible in diagnostics.

`python -m luca_memory.review_benchmark --mode turns --repeats 15`

Five synthetic nodes, identical five-question dialogues, two warmup dialogues,
5-slot capacity, 16 MB active and 32 MB warm payload budgets, GPU ordinal 1.
The larger budget lets all five complete 1.65 MB nodes fit identically in both
backends; it is a benchmark override, not a change to `config.yaml`. Before
optimization, 5 measured dialogues yielded 25 turns per case; after optimization,
15 yielded 75. SHA-256 of exposed contexts and recall traces match between
HOST/CUDA. The adapter is deterministic and makes no LLM calls. Timings include
Core planning, storage, serialization and prompt preparation, but exclude seed
import, initial CUDA context creation, model inference, HTTP and dashboard work.

| Node bytes | Backend | Before median / p95 | After median / p95 |
| --- | --- | ---: | ---: |
| 64,000 | HOST | 2.837 / 3.335 ms | 2.531 / 2.961 ms |
| 64,000 | CUDA | 6.145 / 6.559 ms | 2.372 / 2.801 ms |
| 1,650,000 | HOST | 81.471 / 83.225 ms | 71.512 / 74.164 ms |
| 1,650,000 | CUDA | 152.414 / 154.221 ms | 54.086 / 55.440 ms |

In the fixture CUDA copies fall from 3 uploads/26 downloads per turn to 1/6.
For 1.65 MB nodes, downloads fall from about 42.9 MB to 9.9 MB per turn.
The HOST reference still has different serialization/compaction accounting work;
these results do not establish general CUDA superiority or real-library quality.
They justify removing this specific redundancy while preserving the physical
carousel. These are local small-sample measurements, not performance assertions
in CI. The complete benchmark is available with `--mode all`.

## Validation and boundaries

105 tests pass with real CUDA enabled, including migration and allocation-reuse
regressions. Ordinary test runs skip the three opt-in hardware tests. No packages
were installed. No personal runtime database was opened. Real-library evaluation
remains joint work with Christian; Cesare remains excluded.

A separate live check with the configured LM Studio model and a temporary seed
database preserved focus 7 → 7 → 19 → 14 across the four submarine questions,
returned non-empty relevant replies, and released all owned CUDA buffers. It
does not turn the synthetic timing benchmark into an inference benchmark.
