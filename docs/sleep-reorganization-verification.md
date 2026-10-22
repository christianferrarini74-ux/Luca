# Verification of sleep reorganization

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

2026-10-22. [Italiano](it/fase-1-sinapsi/29-verifica-riorganizzazione-sonno.md).
Companion to the [memory integration contract](memory-integration-contract.md).

Historical checkpoint: the [subsequent target-stop correction](maintenance-target-stop.md)
supersedes the unbounded application of all valid groups recorded here. These
original observations, including the mixed-theme result, remain unchanged.

## Scope and method

Simulate knowledge and graph topology, not the maintenance implementation.
`sleep_fixture.py` builds disposable graphs via `SynapticMemory`; `sleep_check.py`
starts the **real** `IdleMaintenance.start()` polling thread with the configured
LM Studio adapter. No application server, personal DB, PDF importer, content
distiller or library is used. Production `maintenance.py`, config and bible
are unchanged. No new dependency was added.

The fixture has 153 original nodes: an index/family root, three content parts,
52 external topic neighbors, and two independent controls with 50 and 45
outgoing arcs and their own neighbors. Only the 52-degree root is eligible
for automatic maintenance. Its family links do not count toward that degree.
The external neighbors alternate Botanica/Astronomia in both directions;
titles deliberately expose the category. This is an easy controlled taxonomy,
not a realistic ambiguous library. Model inputs contain only the production
directory and constraints; evaluation categories are not injected as instructions.

Thresholds remain 50/45. The diagnostic shortens idle/poll timers to one second
in a configuration copy, then waits for actual elapsed inactivity. It does not
call `apply` in place of the worker or fabricate an idle timestamp. Restoring
the graph is a subsequent explicitly confirmed diagnostic operation. The harness
waits for worker application/error before stopping and joining the thread;
proposal completion alone would not establish commit completion.

```powershell
python -m unittest discover -s tests -p test_sleep_simulation.py -v
python -m luca_memory.sleep_check --repeat 2
```

Reports go into `D:/Test/Luca/sleep-check-*.json`; SQLite fixtures are temporary
and removed after the experiment. An optional `--model` overrides only the
diagnostic copy. The script uses LM Studio's existing model-load behavior and
does not unload user models. Its `passed` field/exit code concern structural
checks, **not** taxonomy acceptance; inspect `thematically_pure` and group titles.
The purity flag checks membership against controlled labels, not whether a
generated title accurately names a category. Human review is still required.

## Structural acceptance

For every committed operation the oracle checks:

1. Degree at most 45; generated group degrees at most 50.
2. Every original node's serialized content unchanged.
3. Every original directed route retained directly or through one generated
   intermediary, and the exact directed reachability relation among **all**
   original nodes unchanged (not just the root's neighborhood).
4. Family membership unchanged and the same complete directory visible from
   all three parts.
5. The 50/45-degree controls untouched.
6. Generated groups present in catalog/entry index; original entry metadata unchanged.
7. The same invariants after reopening SQLite.
8. Explicit undo after reopening reproduces the original content, routes, usage,
   family, catalog, aliases and search-index snapshot exactly. Audit/revision
   counters and the committed-ID high-water mark intentionally do not rewind.
9. Owned worker joined; no diagnostic thread left behind.

## Real-model evidence

Model: already-loaded `google/gemma-4-e2b` Q4_K_M. No model change, prompt change
or forced semantic route. Bible SHA-256:
`a7326f92b597976edc837233fd5da81f6cd03d70db625e9a29901ac074b2f7c4`.

Final recorded pair:
`D:/Test/Luca/sleep-check-20261022-143525-384407.json`.

| Run | External degree | Groups | Worker duration | Structural checks | Controlled theme purity |
| --- | --- | --- | ---: | --- | --- |
| 1 | 52 → 4 | 4 | 15.345 s | All passed, including restart/undo | Pure memberships; Botanica/Astronomia separated by direction |
| 2 | 52 → 18 | 2 | 16.702 s | All passed, including restart/undo | **Failed**: all 26 outgoing neighbors assigned to “Astronomia”, mixing both categories |

Run 2 also grouped ten incoming Botanica nodes, leaving other incoming nodes
direct. The Core correctly accepts this structurally valid reduction; it does
not know that the outgoing title is semantically misleading. A regression test
reproduces a valid mixed-theme proposal and confirms the distinction.

Preliminary evidence is preserved at
`D:/Test/Luca/sleep-check-20261022-142643-660994.json`: both runs were structurally
correct and formed four pure groups (16.196/15.329 s). The harness was then
tightened to wait explicitly for commit/error before requesting shutdown, and
the pair above was repeated. Do not replace the mixed result with the better
preliminary runs or treat these few observations as a statistical reliability rate.

The current target means **<=45**, not “stop exactly at 45” or “make the minimum
possible change”. Both 4 and 18 meet the implemented contract. There is no
minimal-regrouping optimizer; this is an explicit characteristic, not a measured
benefit. No CUDA payload movement or large-node throughput is claimed by this
metadata-reorganization experiment.

## Fault and concurrency verification

Twelve new deterministic sleep tests cover the 50/45 fixture, actual polling,
activity cancellation before a queued mutation, owned-worker shutdown during a
pending proposal, disabled sleep, invalid proposals/backoff/retry, stale plans
after a neighbor-title change, guarded refusal of undo after group edits,
precommit exception rollback and repeated cycles without committed-ID reuse.
An already-resident family part also refreshes its separate cached directory
after regrouping and traverses a generated group to the original payload with
one-slot host tiers. This is structural navigation, not an LLM answer-quality test.

One test starts a separate Python process on the disposable SQLite file and
terminates with `os._exit(73)` after all regrouping writes but **before commit**.
On reopen, the original graph/index snapshot and revision are intact,
`PRAGMA integrity_check` returns `ok`, no operation was committed, and maintenance
can run successfully afterward. This tests abrupt process termination, not power
loss or storage-device failure. Waiting for provider cancellation still obeys
the real runtime's timeout semantics; no forced HTTP cancellation is invented.

Two additional contract tests execute the external-producer example, verify
canonical family routes, and reject confusion between global/directory revisions
or attempts to save a partial view. Full-suite results are recorded in the
delivery checkpoint below.

## Conclusion

The existing sleep mechanism works structurally in these controlled executions:
it triggers, reduces degree, preserves knowledge/navigation, survives reopening
and permits exact guarded restoration. No production-algorithm fix was needed.
**Semantic grouping quality is not guaranteed**, even with easy titles; one
real proposal demonstrates that limitation. Automatic application currently
validates structure, not an independent semantic assessment. Manual preview and
confirmation are available when that distinction matters. Improving grouping
quality or adding an optional review policy would be separate design work, not
an undisclosed bible modification made to pass this test.

## Delivery checkpoint

`python -m unittest discover -s tests -q`: 273 tests, OK, seven optional
hardware/service checks skipped. `node --test tests/test_graph_frontend.js
tests/test_cockpit_frontend.js`: 19 passed. Ruff and `git diff --check` passed.
The 14 added tests comprise 12 sleep tests and two contract tests. Real-model
calls above are separate from the portable suite and do not waive its skips.
Gemma remained loaded and idle afterward; no user model was unloaded. No
production memory database was opened by these diagnostics.
