# Phase 1.11 — Execution and acceptance

[Italiano](it/fase-1-sinapsi/12-implementazione-memoria-navigabile.md)

Scope: implement the confirmed [specification](bounded-synaptic-memory-design.md),
not book ingestion, content distillation or Cesare integration. Existing personal
databases are not used by automated tests or rewritten by development scripts.

1. Durable foundations: explicit star-family membership, canonical identity,
   transactional mutations, revision tracking, current aliases and global search.
   Verify rollback, rename, restart and ordinary-node compatibility.
2. Complete first-degree fast directory independent of payload residence. Verify
   incoming/outgoing coverage, family continuity and stale-cache invalidation,
   including failed GPU allocation. No silent truncation of routing metadata.
3. LLM navigation: bounded search/open/answer protocol; the Core checks IDs,
   revisions and routes, never substitutes a semantic choice. Legacy rule mode
   remains available as an explicit test/reference configuration.
4. Maintenance: configurable upper/target limits, confirmed manual plans and idle
   automatic execution, directional grouping, audited reversible transformations.
   Verify original routes, stale plans, rollback and local degree reduction.
5. Integration: API/cockpit visibility, deterministic end-to-end tests, portable
   suite and opt-in real CUDA checks. Record evidence and remaining limitations
   here and in both READMEs; commit verified milestones.

Implementation status and test results are recorded below as work progresses.

Foundation checkpoint: canonical families, complete metadata directories, additive
revision/catalog migration, atomic node mutations and revision-aware host/device
slots implemented. Portable suite: 116 tests, 3 hardware checks skipped. The old
test equating first-degree membership with preloaded contents now checks the two
separately. No personal database was opened.
