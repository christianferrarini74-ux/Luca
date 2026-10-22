# Code simplification and internal comments

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

2026-10-22. [Italiano](it/fase-1-sinapsi/20-revisione-codice-e-commenti.md).
Baseline: commit `291189f`.

## Scope

Remove duplication/repeated work and explain the internals of larger modules.
This is not an architecture or behavior rewrite. Bible, configuration,
dependencies, persistent formats, SQL ranking, public interfaces and memory
behavior remain unchanged. Historical paths still covered by tests are retained.

## Changes

- `api.py`: one prefix/suffix serialization loop, one load instead of two per
  title lookup, one JSON body reader. Route-specific validation, limits and
  errors remain distinct.
- `store.py`: `dataclasses.replace` preserves result fields when recording recall;
  one alternatives filter. Convergence strategies, SQL and migrations retained.
- `session.py`: `handle` shrinks from **132 to 48 physical lines**, separating
  turn orchestration from model and deterministic response paths. Private
  helpers remain under the turn lock. Already-produced navigation answers do
  not trigger a second generation; adapter priority and history are preserved.
- `navigation.py`: construction and subsequent turns share initialization.
- `reading_workspace.py`: incremental UTF-8 offsets replace repeated prefix
  construction/counting. Serialization and byte spans remain identical, including
  accents/emoji; offsets are not confused with model tokens.
- `tiers/carousel.py`: ordered dictionary deduplication avoids repeated list
  membership scans; redundant expanded-set updates removed; directional
  reinforcement unified. Recall order, transactions and physical tiers retained.
- `web/app.js`: shared JSON POST setup and navigation-group updates; page IDs
  derive from existing metadata. Transcript effects, errors and confirmations
  remain action-specific.
- `web/graph.js`: title search uses one pass rather than a scan per visible node;
  fitting no longer rebuilds the SVG twice, and redundant viewBox updates are
  removed. DOMPoint recovery remains intact.

These are local complexity improvements, not measured LLM acceleration or a
large-library performance benchmark.

## Internal explanations

English comments/docstrings now sit beside the relevant code, not only at file
headers. They explain reentrant locks, nested transactions/savepoints, migration
order, indexes/self-loops, canonical families and revisions, serialization,
actual reads versus preloading, bytes versus tokens, task continuity,
proposal/confirmation/restore, idle cancellation, cockpit lifecycle and geometry.

`adapters.py`, `budget.py`, `maintenance.py`, `planning.py` and
`synaptic_schema.py` also receive targeted explanations. In particular,
rules/hybrid legacy heuristics are distinct from LLM-led navigation. No semantic
instructions were added to code or prompts. Comments explain responsibilities,
invariants and reasons, not obvious assignments. Superficially similar but
different contracts, such as token and byte packing, were not forced into
generic helpers.

## Size and validation

Across nine functionally reorganized files (`api`, `store`, `session`,
`adapters`, `navigation`, `reading_workspace`, `tiers/carousel`, `web/app`,
`web/graph`), nonempty operational lines decrease from **3424 to 3388**,
excluding whole-line comments and Python docstrings. Instructions are not
artificially minified. Physical lines increase from **3864 to 3940**, because
explanations and responsibility boundaries were added. This is not presented
as a drastic size reduction. New tests/docs are excluded from these counts.

Before: **219 Python and 10 JavaScript tests**. After: **235 Python and 19
JavaScript tests**, all passing. Python ran with real CUDA/native tokenization
enabled and no skips.

```powershell
$env:LUCA_TEST_CUDA='1'
$env:LUCA_TEST_LMSTUDIO='1'
.venv/Scripts/python.exe -m unittest discover -s tests
node --test tests/test_graph_frontend.js tests/test_cockpit_frontend.js
```

New regressions cover HTTP/payload contracts, family titles/limits, transaction
ownership/result copies, generation priority/no duplicate answer, Unicode spans,
collapsed-child search, busy/error/confirmation handling, startup and polling.
The four new public session/workspace tests also pass with the previous source
loaded; the eight cockpit VM tests were also checked against the original code.

Cockpit JavaScript tests use a simulated DOM: no new manual browser/layout
certification is claimed for this revision. No free-model conversation was
used to claim a semantic improvement. Tests do not use personal memory or
restart the user's application.

To load Python changes, stop Luca cleanly and run `python run_luca.py`, then
reload the page. No dependency reinstall is needed.
