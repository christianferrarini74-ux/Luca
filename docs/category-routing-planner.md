# Semantic classification, deterministic arc reduction

2026-10-22. [Italiano](it/fase-1-sinapsi/32-classificazione-e-pianificazione-archi.md).
Supersedes the automatic proposal interface in the
[whole-group planner](maintenance-target-stop.md) and the
[Gemma comparison](sleep-gemma26-comparison.md). Those records remain historical.

## Separation of responsibilities

The LLM labels every external address by topic, separately for incoming and
outgoing directions. It no longer chooses group sizes, computes reductions or
decides which arcs to move. The request carries the complete directory and a
classification contract, without the previous degree/target arithmetic.
The schema requires every address; an explicit null represents uncertainty.
The parser rejects omissions, unknown IDs and malformed/empty/overlong labels.
Root self-addresses and internal family parts are not classified.

`ClassifiedDirectory` is an immutable focus/revision-bound result. The Core
revalidates its completeness, uniqueness, labels and current directory revision
before deriving any plan. Classification categories may contain one or many
members; they are **not** indivisible routing nodes. Inferred semantics remain
the classifier's responsibility: completeness does not prove correct labels.

The technical `group` paragraph of `bible.md` and its English translation was
necessarily updated: its old instruction required the model to compute the
final degree, contradicting the new interface. Only that paragraph changed;
conversation, knowledge integration and reasoning guidance are unchanged.
No extra system prompt or hidden instruction was added in Python.

## Deterministic algorithm

Let `D` be current external degree, `T=edge_target`, `U=edge_upper`, and
`m=U-1`. Automatic eligibility stays `D>U`; if eligible the required reduction
is `R=D-T`. A routing node with `k` members removes `k-1` direct parent arcs,
and its own degree is `k+1<=U`. This reduces local fan-out, **not** global edge
count: each generated routing node adds one net graph edge.

1. Group labels within each direction only; sort member IDs for reproducibility.
2. Partition each category into disjoint candidate chunks of at most `m` members.
   Singleton chunks cannot reduce degree and remain direct.
3. Sort chunks by decreasing capacity (`len(chunk)-1`), with stable ties.
4. Select full chunks while needed. In the last selected chunk use only
   `remaining_reduction+1` members. Leave every unused member's arc direct.
5. Stop at reduction exactly `R`; output ordinary `EdgeGroup` records for the
   existing revision-checked, atomic application and guarded undo machinery.

The Core changes neither a member's category nor its direction. Example:
thirteen Botanica addresses and a reduction of seven yield **one eight-member
Botanica routing node**, leaving five Botanica addresses direct. Category
membership is not content-family membership; no source node is split or distilled.
The selected groups minimize the number of new routing nodes for the disjoint
category chunks: the largest capacities first reach any given reduction with
the fewest chunks, and the final partial chunk removes overshoot.
Complexity is `O(N+C log C)` after category validation/sorting, where `N` is
the number of classified addresses and `C` the number of candidate chunks;
member sorting adds its own `O(N log N)` worst-case bound. No new library is used.

For a category of size `n`, maximum single-level reduction is
`n-ceil(n/m)`. If aggregate compatible capacity is below `R`, the Core raises
an explicit error without writes. It never merges unrelated categories or
treats null as permission to guess. Two categories of four still cannot remove
seven arcs. A very large hub can require a future multi-level plan (e.g. 2,500
same-category neighbors, `m=49`, cannot reach degree 45 in one level). This
delivery does not invent recursive batches outside the existing operation format.

## Core and application contract

```python
directory = memory.directory(root_id)
classification = classification_from_assignments(
    {"assignments": {"incoming": incoming_labels, "outgoing": outgoing_labels}},
    directory,
)
plan = maintenance.plan(root_id, classification)
operation_id = maintenance.apply(plan, confirmed=True)
```

Import the parser from `luca_memory.classification`. Label-map keys are decimal
ID strings, values category titles or null/None. Both maps cover all addresses
in their direction, excluding self; a bidirectional neighbor appears in both.
Only the owning runtime/store may write. Plans remain versioned previews; no
classification directly mutates memory. A stale classification must be refreshed.

The local dashboard's preview path uses the new adapter result automatically,
then displays the concrete plan before confirmation. Apply/restore endpoints
and persisted undo format are unchanged. Custom adapters and explicit HTTP
`groups` lists may still supply **concrete whole groups**: that compatibility
path retains nearest-target subset selection without clipping those explicit
groups. Do not confuse a manual concrete plan with an LLM semantic category.

## Verification

Fifteen new tests cover complete schema/parser coverage, nulls, unknown/duplicate
IDs, malformed public records, stale revisions, direction/category separation,
bounded large-category packing, insufficient capacity, exact target, full graph
undo and the dashboard preview/apply/restore path. Two hundred seeded cases
compare exact reduction and routing-node count against an independent exhaustive
per-category dynamic program. Existing whole-group, sleep cancellation, crash
and persistence tests remain active.

Real-worker runs use the unchanged 153-node diagnostic graph and 50/45 settings,
not personal memory. Each model ran two fresh databases:

| Model | Worker durations | Classification | Applied plan |
| --- | --- | --- | --- |
| Gemma 4 E2B Q4_K_M | 21.014 / 19.343 s | All 52 IDs, four pure categories of 13, no nulls | One eight-member incoming Botanica group, **52→45**, both runs |
| Gemma 4 26B A4B Q8_0 | 29.012 / 34.298 s | All 52 IDs, four pure categories of 13, no nulls | Same plan, **52→45**, both runs |

Reports:
`D:/Test/Luca/sleep-check-20261022-160543-520995.json` and
`D:/Test/Luca/sleep-check-20261022-160749-341104.json`.
All raw categories, not only selected groups, were inspected against the
controlled titles. All four runs preserve original contents, directed routes,
family directories, control nodes and indexes, and pass reopening plus exact
guarded restoration. Worker threads joined and temporary databases were removed.
Only the newly loaded 26B model was unloaded; E2B remained loaded, GPU memory
returned to 6,935/14/14 MiB, utilization zero.

Compared with the preceding experiment, the classifier contract, schema and
technical bible paragraph intentionally changed. These results support this
pipeline on the controlled fixture, not a model-size causal claim or universal
semantic correctness. Small-model timings overlapped the larger model's loading;
the durations are observations, not a clean benchmark. Semantic validation on
ambiguous labels remains distinct from deterministic numeric correctness.

Delivery checkpoint: 295 Python tests, OK (seven optional hardware/service
checks skipped), 19 JavaScript tests passed, Ruff and `git diff --check` clean.
Current bible SHA-256:
`87fa4075ab02797df4edbe65d3e49851fef9d91bae4cb98f83b1059e3f86c1ab`.
No runtime config, SQLite schema, dependency or personal database changed.
Restart a running application with its normal Esci/start sequence to load the
new Python interface together with its updated technical instruction paragraph.
