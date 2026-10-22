# Memory integration contract — Luca

2026-10-22. [Italiano](it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md).

This is the current integration guide for external producers and consumers.
Current automatic policy: [classification and deterministic routing](category-routing-planner.md).
Earlier design documents remain historical records. The application package
version is currently 0.1.0; this guide does not invent a separate versioned wire
protocol or promise backward compatibility that the project has not established.

## 1. Responsibility boundary

Luca stores, indexes, connects, opens and reorganizes knowledge. It does **not**
produce knowledge nodes, import PDFs, split books, distil content or build a
library. External software owns those operations and its semantic decisions.
The sample chat/dashboard is a test consumer, not memory logic. The bible is an
LLM interface configuration, not an ingestion format; it is outside this work.

The producer must deliver valid identifiers, meaningful titles, complete content,
explicit family memberships and intentional directed links. Luca guarantees the
structural operations described below, not factual truth, automatic provenance
verification, optimal taxonomy or the reasoning quality of a consuming LLM.

## 2. Node representation

Use `KnowledgeNode` from `luca_memory.node`, persisted with
`SynapticMemory.update_node`. It is a Python record, not a JSON file to write
directly into SQLite. Fields:

| Field | Producer contract / current meaning |
| --- | --- |
| `id` | Positive integer, stable within one database; obtain `store.next_cell_id()` and insert under the same store transaction/lock. It is a next-ID query, not a reservation service. |
| `slug` | Nonempty stable textual key; use a distinguishable namespace. Unlike seed slugs, general node slugs are not enforced unique. |
| `title` | Nonempty, informative name for entry lookup and directories. Titles need not be unique; identity is the integer ID. |
| `content` | Complete Unicode text; the persistent source of the node's knowledge. An empty body can represent an index, but is not a substitute for external content storage. |
| `keywords` | Tuple of searchable strings; optional. Slug, title and keywords create normalized aliases and metadata entry cues. |
| `summary` | Optional text; not automatic distillation and not a guarantee that the navigator uses it instead of content. |
| `sections` | Optional tuple of `KnowledgeSection(key, title, content)`; use nonempty unique section keys. Sections are not nodes, have no IDs or independent arcs. |
| `created_at` | Unix seconds; zero assigns current time on serialization. Preserve the existing record when editing. |
| `last_recalled_at`, `recall_count` | Runtime usage information, not producer-supplied truth or a semantic revision. |
| `content_complete`, `full_content_bytes` | Runtime cache-view metadata. A partial view (`content_complete=False`) cannot overwrite the persistent node. Not a content-splitting interface. |

These are integration requirements, not a claim that the dataclass constructor
validates every field. Some low-level paths accept empty titles or duplicate
keys; producers must not rely on that leniency. Partial-view persistence and
structural constraints are checked by the Core. Use `load_node` +
`dataclasses.replace` to edit a record without discarding optional fields.

There are no first-class source/page/date/confidence fields in this record.
Record source identity, revision, page/section and applicability in `content`
or its sections when needed. Luca stores them as text; it does not resolve
conflicting versions automatically. A link does not establish factual authority.

## 3. Directed arcs and canonical families

An arc is the ordered pair `(source_id, target_id)`, conceptually
`prefix:suffix`. It has no semantic label or weight to supply. Usage counters
are runtime metadata. Both endpoints must exist. The pair is unique; adding
it again does not create another arc. Reversing it is a different arc.
Self-links are supported; a root self-link counts once incoming and once
outgoing (degree two). It cannot be a grouping member.

An ordinary hub with neighbors is **not** automatically a content family.
Create A, A1, A2 independently, then call `attach_part(A, A1)` and
`attach_part(A, A2)`. The family is the explicit star A plus its parts:

- `root(A1) == A`; `parts(A)` lists its parts. Families cannot be nested;
  an attached part cannot itself have parts or belong to a second family.
- Reading A1 keeps `reading_id=A1`, but its external identity/focus is A.
  A, A1 and A2 expose the same complete external directory and list of parts.
- External arcs live on A, not in copied per-part edge lists. Connecting
  A1 to B through the Core becomes A→B; arrival at a family's part likewise
  canonicalizes the external endpoint to its root.
- Attaching an existing independent node moves its external routes onto A,
  deduplicating ordered pairs; it is a mutation, not just a display tag.
  Existing internal root/part connections are replaced by the canonical star.
- Parts are not counted in A's external degree, but their ID/title entries do
  consume directory/prompt space. There is no configured hard part-count cap.

Navigation grouping nodes G are different: A→G→B or B→G→A reduces A's
external degree. G has its own identity and directory, not A's family identity.
An active generated G cannot become a content fragment. A consuming LLM may
need one extra opening; the original direct arc must not be assumed to persist.

Valid: A1→B requested through `memory.connect` (stored as A→B).
Invalid: nesting A1 under A and then attaching children under A1; an unknown
endpoint; direct SQL external arcs on a part; saving a truncated cache view.
No public detach/delete-family migration is supplied; do not invent SQL fixes.

## 4. Indexes, reads and limits

The global entry index uses title/slug/keywords. Explicit `global_lookup` uses
aliases plus full-text search over stored text. Both return bounded ID/title
candidates, not semantic completeness guarantees or opened contents. Aliases
normalize case, accents and whitespace; collisions may return multiple nodes.

`directory(node_id)` returns `focus_id`, `revision`, `incoming`, `outgoing`,
`parts`; entries contain only `id` and `title`. It includes all first-degree
addresses regardless of whether their payloads are on SSD, RAM or VRAM. A title
or resident neighbor is not a content read. A second-degree index is not part
of the current contract. After a mutation, refresh directories and search results.

| Configuration (`config.yaml`) | Current distributed value | Effect |
| --- | ---: | --- |
| `runtime.synaptic.edge_upper` / `edge_target` | 50 / 45 | External incoming + outgoing degree. Automatic sleep only above upper; classified routing reaches target exactly when compatible capacity suffices. Explicit concrete groups retain nearest-whole-group selection. Temporary overflow is allowed. |
| `navigation_steps` / `global_candidates` | 8 / 20 | Maximum model actions per turn / bounded global results. Not maximum graph size. |
| `fast_index_bytes` | 65536 | Serialized complete directory allowance, measured in UTF-8 bytes. Never silently drops arcs. |
| `automatic_sleep` / `idle_seconds` | true / 60 | Automatic reorganization and idle threshold. |
| `sleep_poll_seconds` / `sleep_retry_seconds` | 5 / 300 | Poll interval / failed unchanged-directory retry backoff. |
| `maintenance_output_tokens` | 8192 | Maximum model generation for a grouping proposal. |
| `runtime.context_budget.unit` / `context_window` | tokens / 70000 | Model-native token accounting and configured context budget. |
| `memory_limit` / `per_node_limit` | 20000 / 16000 | Reading-workspace and per-reading text budgets; not persistent-node size limits. |
| `history_limit` / `task_limit` | 40000 / 2048 | Conversation and task budgets. |
| `output_reserve` / `framing_reserve` | 4096 / 512 | Output and framing reserves; operation-specific output can differ. |
| `runtime.vram_capacity` / `ram_capacity` | 5 / 12 | Payload slots. |
| `runtime.vram_bytes` / `ram_bytes` | 8000000 / 32000000 | Serialized tier byte capacities; different from prompt tokens. |

Synaptic settings validate positive integers, `edge_upper>=3` and
`2<=edge_target<edge_upper`. Other deployments can configure different values.
Core objects used without application config have their own constructor defaults;
do not assume the table is a hardcoded universal limit.

There is no automatic word-count splitting or persistent-node token cap.
An external producer decides content partitioning, measured against its target
consumer's tokenizer/budgets. Long bodies can be excerpted with a partial marker;
the source remains complete on SSD. Complete directories take priority: if they
do not fit, Luca raises an explicit budget error instead of hiding routes.
CUDA tiers retain complete serialized payloads, not arbitrarily compacted nodes;
a payload too large for an individual tier cannot be assumed to load. Host-mode
views may be compacted. No SSD-size-independence or unlimited-context claim.

## 5. Writes, atomicity and ownership

Use one owning runtime/store connection. Its reentrant lock serializes readers,
writes and maintenance. SQLite transactions/savepoints atomically commit node
content, catalog, aliases, full-text/entry indexes, revisions and mutation events.
Use `with store.transaction():` for a multi-node/edge/family batch. A producer
cannot obtain a multi-request transaction by sending separate HTTP operations.

`expected_revision` on Core mutations is the **global** `store.revision`, not
the focus's directory revision. A stale value raises `StaleRevision`: refresh
and reconsider; never silently force the old operation. Core callers can omit
the check only when they intentionally own serialization. HTTP requires it.
`validate_step(reading_id,target,directory_revision)` instead checks the local
directory revision. Usage reinforcement does not count as a structural edit.

Committed IDs are not recycled, even after undoing generated groups. A rolled
back allocation was never committed and may be reused. Replacing a title also
refreshes relevant directories/indexes; stale tier copies are invalidated before
use. A GPU allocation failure does not undo an already committed content change
and must not resurrect the old view. Raw SQL writes, external writers modifying
the live file, multiple independent writing runtimes and cross-process ID
reservation are not supported integration interfaces.

## 6. Executable producer example

[examples/memory_contract.py](../examples/memory_contract.py) creates an index,
two content parts and an external reference in one transaction, then demonstrates
a metadata-preserving edit. It refuses a nonempty store. Run from the repository
with an installed/editable package and a **new** output file:

```powershell
python -m examples.memory_contract --database D:/Test/Luca/contract-example.sqlite
```

The example establishes the empty-library seed identity. Startup with the same
seed can therefore preserve the added nodes. `ensure_knowledge_seed` checks an
existing seed identity; it is not an incremental content importer. Never call
`load_knowledge_seed` to append a document: that explicit loader **replaces**
graph contents. Seed JSON is a bootstrap/fixture format, not the reusable
incremental producer contract, and does not encode explicit family membership.

## 7. Existing local HTTP facade

Default base URL `http://127.0.0.1:8765`; this is the test application's local
facade, not a remote authenticated multi-user service. `GET /api/state` exposes
`synaptic.revision` and the current focus/directory. All endpoints below are POST
with a JSON object; mutations return `state`, except where specified.

| Path | Request / result |
| --- | --- |
| `/api/memory/search` | `{ "query": "Atlas" }` → `{ "revision": ..., "candidates": [{"id":...,"title":...}] }` |
| `/api/recall` | `{ "node_id": 1 }` → open an explicit known entry, returning state. |
| `/api/memory/navigate` | `{ "target_id": 2, "directory_revision": 123 }`; needs a current reading focus and a current legal local address. |
| `/api/memory/node` | `{ "node_id": 1, "title": "Atlas", "content": "...", "expected_revision": 123 }`; create/edit title and content. |
| `/api/memory/edge` | `{ "source": 1, "target": 4, "expected_revision": 123 }`; add. Set `"remove":true` to remove. |
| `/api/memory/family` | `{ "root": 1, "part": 2, "expected_revision": 123 }`; both nodes must already exist. |
| `/api/maintenance/preview` | `{ "node_id": 1 }` asks the configured adapter, or supply `"groups":[{"title":"Topic","direction":"outgoing","members":[2,3]}]`; returns `plan_id`, `plan`. |
| `/api/maintenance/apply` | `{ "plan_id": "...", "confirmed": true }` → `operation_id`, `state`. |
| `/api/maintenance/restore` | `{ "operation_id": 1, "confirmed": true }` → state after guarded undo. |

Numbers above are placeholders: obtain current IDs/revisions, do not paste them
as preconditions. This facade does not expose full `KnowledgeNode` fields, an
ID-allocation endpoint, batch transactions or family detach. New HTTP nodes get
`slug=node_<id>`; updates preserve other existing fields. Do not expect arbitrary
extra JSON fields to import metadata. Use the Core inside the owning runtime for
the complete producer interface and coordinated ID allocation.

Invalid requests and stale revisions return HTTP 400 (`{"error":"..."}`),
not HTTP 409; unexpected backend failures return 500. Cross-origin mutation
requests are rejected (403). The memory/maintenance request-body cap is
2,000,000 bytes, not a node-content token limit. A new preview replaces the
previous pending plan; confirmed operations remain in the database after restart.

## 8. Sleep and failure semantics

Manual maintenance requires preview and explicit confirmation, and may operate
above target even below/equal upper. Automatic sleep only selects independent
canonical identities whose external degree is **greater than** upper. Internal
family links do not trigger it. At/below target manual maintenance is a no-op.

The LLM receives the complete directory (IDs/titles), not node bodies or arc
arithmetic. Producers must give informative titles. It returns a complete
`ClassifiedDirectory`: every external directional ID has a category title of
1..256 characters or explicit null (uncertain). Omission is invalid. Self and
internal parts are excluded. Categories may have any size and are not routing
nodes. The Core revalidates coverage, labels, IDs and directory revision.

The Core builds disjoint routing groups of 2..`edge_upper-1` members within
one category and direction, leaving unused/null/singleton addresses direct.
Reduction is `sum(member_count-1)`. The last group may use only part of its
category to reach `edge_target` exactly. Insufficient compatible single-level
capacity fails without writes, never by merging unrelated topics. No content
is split. Preview and undo show only the concrete applied groups.

External Core consumers can call `classification_from_assignments(value,
directory)` from `luca_memory.classification`, then pass the result to
`MemoryMaintenance.plan`. See the executable-shaped example and capacity limits
in [the planner specification](category-routing-planner.md). The default local
preview uses this path automatically. Explicit HTTP `groups` and custom adapters
returning concrete lists remain a separate compatibility path: whole-group
subset selection with minimum overshoot, no splitting of those manual groups.
Structural validity and complete classification do not prove semantic quality.

One worker tick attempts at most one candidate. It records errors and backs off
failed proposals by node-directory revision. No invalid proposal changes the
graph. The owning store lock serializes model calls and writes; renewed activity
is signaled **before** waiting for that lock and cancels a pending automatic
proposal before application. Shutdown similarly cancels a returned pending
proposal and joins the worker. In-flight HTTP generation is not forcibly
interrupted: waiting may last up to provider timeout. An atomic transaction
already started finishes before the queued request.

Apply stores original routes and undo data in the same transaction. Undo requires
confirmation and refuses to discard edits to generated groups, aliases, family
membership or incident routes. It preserves accumulated route usage. Undo is not
a general-purpose rollback for arbitrary later knowledge edits. Back up SQLite
correctly (including WAL consistency or with the runtime stopped), not by copying
only a live `.sqlite` file. Process-crash recovery is tested; power-loss behavior
is not certified (`synchronous=NORMAL` is the current store setting).

## 9. Acceptance and scope

Run `python -m unittest discover -s tests -v`. `test_memory_contract.py` executes
the producer example and checks family identity, canonical arcs, revisions and
partial-view rejection. `test_sleep_simulation.py` checks the reorganization
contract on isolated fixtures, including abrupt precommit process termination.
The opt-in real-model experiment is `python -m luca_memory.sleep_check --repeat 2`.
See [sleep verification](sleep-reorganization-verification.md) for evidence and
limits. These tests do not turn PDF conversion, library creation, LLM training,
bible optimization or Cesare integration into Luca responsibilities.
