# Phase 1.11 — Execution and acceptance

[Italiano](it/fase-1-sinapsi/12-implementazione-memoria-navigabile.md)

Follow-up: [real LM Studio validation](phase-1-11-live-validation.md) records
subsequent fixes and the remaining recall/group-title limitations. The checkpoints
below retain the implementation-time evidence.

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

## Implemented runtime

The five execution blocks are implemented. This does not claim that grouping
quality or natural-model navigation has been validated on a real library.

- `SynapticMemory`: canonical family membership, one shared external directory,
  current generated aliases, global FTS/exact lookup and atomic mutations.
- `MemoryNavigator`: model-led search/open/answer, complete directional ID/title
  directories, explicit entry selection, route validation and bounded steps.
- Revision-aware slots discard obsolete host/device payloads before access. A
  failed GPU reload cannot undo committed knowledge or expose its previous copy.
- `MemoryMaintenance`: revision-checked plans, manual confirmation, incoming and
  outgoing groups kept separate, original-route journal and guarded restoration.
  G nodes have their own identity and cannot be attached as content fragments.
- `IdleMaintenance`: an owned, stoppable worker, serialized with chat/model use.
  Only external degree > upper is eligible. New input during proposal generation
  cancels its application. An atomic mutation already started finishes before
  chat proceeds. In-flight model HTTP generation is not forcibly interrupted;
  shutdown/user input may wait for the configured provider timeout.
- The Python cockpit shows both indexes, canonical/reading focus, maintenance
  preview/confirmation and operation restoration. Its refresh does not trigger
  model calls or count as user activity. Existing prefix/suffix neighborhood
  diagnostics remain historical views, not inferred content-family membership.

## Configuration and use

Start only `python run_luca.py`. Start the LM Studio server first; Luca still
loads the configured installed model through its existing connector. Runtime
memory stays under `D:/Test/Luca`; no additional package was introduced.

`runtime.memory_planner: llm` selects the new navigation protocol. `rules` and
`hybrid` retain the previous reference planner; a rule-only adapter cannot run
the `llm` planner. All new operating parameters are in `runtime.synaptic`:

| Key | Shipped value | Meaning |
| --- | ---: | --- |
| `edge_upper` / `edge_target` | 50 / 45 | External family degree, incoming + outgoing |
| `navigation_steps` | 8 | Maximum search/open/answer calls per turn |
| `global_candidates` | 20 | Explicitly bounded global search results; refine the query |
| `fast_index_bytes` | 65536 | Serialized directory budget in host RAM |
| `automatic_sleep` | true | Enable idle regrouping of over-upper identities |
| `idle_seconds` / `sleep_poll_seconds` | 60 / 5 | Inactivity threshold / worker polling |
| `sleep_retry_seconds` | 300 | Backoff for an unchanged failed proposal |

The first degree is never clipped to fit payload slots or a prompt. Exceeding
the configured directory/context budget fails explicitly and requires raising
the budget or reorganizing the node. Only selected content may be excerpted;
whole source text stays durable. Word-based splitting and optional second-degree
indexing remain deferred. Prompt accounting still uses conservative UTF-8 bytes.

In the cockpit, open “Rubrica sinaptica” for global lookup and local navigation.
For manual maintenance, select a node, prepare the preview and confirm its exact
plan. At/below target this is a no-op. Automatic maintenance only acts above upper,
never merely because a node exceeds target. Invalid model proposals change nothing.
At the next application startup, additive schema/catalog migration runs; it does
not reseed personal knowledge or infer families from existing star-like edges.

## Core/API boundaries

There is one owning runtime/store connection; all in-process Core mutations and
consumer operations share its reentrant lock. Persistent content, catalog/search,
aliases, revisions and mutation events commit together in SQLite. Revision values
are monotonic mutation markers, not counts of user operations. Usage reinforcement
does not invalidate content. Direct SQL writes and multiple independent runtime
writers are not supported mutation interfaces.

| POST endpoint | Contract |
| --- | --- |
| `/api/memory/search` | `query` → bounded ID/title global candidates |
| `/api/memory/navigate` | `target_id`, `directory_revision` → validated local step |
| `/api/memory/node` | `node_id`, `title`, `content`, `expected_revision` → atomic upsert |
| `/api/memory/edge` | `source`, `target`, optional `remove`, `expected_revision` |
| `/api/memory/family` | `root`, `part`, `expected_revision` → explicit star membership |
| `/api/maintenance/preview` | `node_id`, optional explicit `groups` → plan and temporary `plan_id` |
| `/api/maintenance/apply` | `plan_id`, `confirmed: true` → atomic regrouping |
| `/api/maintenance/restore` | `operation_id`, `confirmed: true` → guarded restoration |

Create nodes with fresh IDs (`store.next_cell_id()` in the Core). Automatically
allocated IDs are not reused after restoration. Stale mutations/routes/plans are
rejected. Preparing a preview replaces the previous pending preview; committed
operations remain persisted across restart (the cockpit shows the latest 20).
Restoration removes only the original, unmodified grouping nodes and refuses if
their contents, aliases, family membership or incident routes changed. It retains
reinforcement accrued on replacement routes. Cross-origin mutations are rejected.

## Verification and limits

Portable suite: 148 tests, including four opt-in CUDA tests skipped by default.
The final hardware run and any additional checks are recorded in the delivery
checkpoint below. JavaScript syntax is checked with `node --check`; Node remains
a development check, not an application runtime dependency.

Tests cover migration without source replacement, atomic rollback, concurrent
readers, cache reload failure, complete metadata beyond preload capacity, family
continuity, model request assembly, invalid/cyclic navigation, directional grouping,
stale plans, confirmation, idle cancellation/backoff, restore guards and real HTTP.
No personal database was opened. LM Studio at `127.0.0.1:1234` was not listening:
new model decisions were tested using scripted adapters and mocked connector
responses, not presented as a successful live Gemma conversation. That acceptance
test remains to run with LM Studio available; real-library evaluation remains joint
work. PDF ingestion, content distillation and Cesare integration are not included.

### Delivery checkpoint — 2026-10-21

`LUCA_TEST_CUDA=1 python -m unittest discover -s tests`: **148 tests passed**, no
skips, including four real NVIDIA CUDA tests on the configured separate GPU.
`python -m compileall -q luca_memory`, `node --check luca_memory/web/app.js` and
`git diff --check` also passed. No live LLM conversation or visual browser QA is
claimed by these checks. The application entry point and dependency set are unchanged.
