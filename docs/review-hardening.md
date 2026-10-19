# Review hardening — Phase 1.10

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
