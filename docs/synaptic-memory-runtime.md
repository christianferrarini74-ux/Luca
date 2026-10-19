# Synaptic memory runtime — Phase 1.07

Date: 2026-10-19

Superseding milestone: [physical SSD/RAM/GPU carousel](physical-memory.md).
The logical-cache and seed-refresh limitations below describe Phase 1.07,
not the current CUDA backend and non-destructive startup policy.

[Italiano](it/fase-1-sinapsi/07-completamento-runtime.md)

This document records the completion of the Phase 1 runtime. Earlier phase
documents remain historical records. The current milestone concerns the use
of articulated knowledge, not conversational acquisition.

## Recall and convergence

Directed addresses support chains, prefix families (`P:*`) and suffix families
(`*:S`). Query anchors are separated from conversational anchors. Convergence
searches SSD independently of the bounded first-degree preload. Strict mode
requires every query anchor; associative mode also admits partial matches.
Relevance is ranked before recency and frequency.

Only the best candidate is opened automatically by default. Multiple openings
run from lowest to highest rank so that the best remains the final focus.
The ranking, opened candidates, and available alternatives are separate results.
VRAM and RAM are bounded logical Python caches; physical GPU allocation is not
implemented. SSD retains the persistent graph.

## Fast and complete search

Set `runtime.memory_search_policy` in `config.yaml`:

- `fast` (default): bounded hot-first search can return as soon as it finds an
  exact candidate. If none is found, an exhaustive search follows.
- `complete`: disables the hot-first shortcut and evaluates the full candidate
  domain of the requested families. Returned results still have a size limit.

An exact candidate satisfies the required links. It does not imply a globally
best result when only hot candidates were searched. API `search_scope` and
`ranking_is_global` distinguish these cases; neither claims semantic certainty.
Family matching currently treats incident edges in either direction as links;
language entry points use explicit aliases and at most three query anchors.

Materialized degree counters are maintained by SQLite triggers. Indexed degree
lookups avoid scanning a family's edges solely to count them. Selection, query
and full carousel recall have separate timings. `estimated_seed_edges` estimates
candidate seeding work, not SQLite page reads or total physical I/O. `recall_ms`
includes selection and query time; these numbers must not be added together.

## Turn lifecycle and explicit alternatives

At each chat turn, the query result is archived and removed from the current
prompt. VRAM, RAM, opened nodes and graph state are preserved. An empty strict
intersection therefore cannot leave an old warning in unrelated later prompts.
The latest prior result remains visible as historical diagnostics.

The dashboard's “Richiamo della memoria e alternative” panel shows scope,
strategy, opened candidates, timings and remaining alternatives. Clicking an
alternative requests a backend operation; the GUI contains no selection logic.
Partial alternatives are marked as partial and require an explicit click.

`POST /api/alternative` accepts `{"node_id": 19}` only when the node is a
registered remaining alternative. The backend opens it, synchronizes dialogue
focus and removes it from the available list. `POST /api/recall` remains the
general manual recall operation. Both clear current query notices.

`GET /api/state` exposes current `convergence` and historical
`previous_convergence`. A new session clears both, preserving the search policy.

## Validation and remaining scope

Run `python -m unittest discover -s tests -v`. Coverage includes cold candidates
beyond preload, relevance versus recency, multiple openings with small caches,
strict empty intersections, query lifecycle, counters and hot-first fallback.
The cold fixture explicitly warms filler edges, avoiding accidental ordering by
node ID. HTTP checks cover alternatives, static assets and orderly shutdown.

Validation on 2026-10-19: 58 automated tests passed. JavaScript syntax and
dashboard rendering checks passed, including escaped titles and disabled
alternative actions during requests. A live HTTP conversation with the
configured LM Studio model (`google/gemma-4-e2b`) returned non-empty replies
and moved focus from the fleet to the dogs' submarine (node 19). The test
used a temporary database under `D:/Test/Luca`, removed after shutdown;
the personal runtime database was not opened or refreshed. This is a smoke
test, not a broad evaluation of answer quality or a visual browser audit.

The Phase 1 seed loader still provides experimental dataset refresh, not a
production migration policy for a growing personal library. Token budgets,
large-document segmentation, semantic query planning and integration with
Cesare are subsequent milestones. No brain equivalence or unbounded hardware
capacity is claimed by this implementation.
