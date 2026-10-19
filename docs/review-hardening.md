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
