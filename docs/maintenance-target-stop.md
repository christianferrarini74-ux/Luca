# Regroup only until the configured target

2026-10-22. [Italiano](it/fase-1-sinapsi/30-arresto-riorganizzazione-obiettivo.md).

Successor: [classification and deterministic routing](category-routing-planner.md).
The whole-group selector below remains the explicit concrete-plan path, not
the current LLM classification pipeline.

## Corrected behavior

The intended 50/45 policy has two thresholds: start automatic maintenance only
above 50 external arcs, then stop at 45 or the closest reachable value below
45 if the last whole group cannot be divided. It does not mean “apply every
valid group as long as the final degree is <=45”. The preceding
[sleep experiment](sleep-reorganization-verification.md) exposed that excessive
regrouping, independently of the semantic-quality problem.

The Core now validates all proposed groups before mutation and selects a subset
of whole groups minimizing excess reduction beyond `degree_before-edge_target`.
Ties prefer fewer groups and then their original order. No model-supplied group
has members arbitrarily removed or redistributed. Unselected groups are not
created and their original arcs stay direct. If the combined valid proposals
cannot reach target, the operation fails without writes. At/below target it
remains a no-op. Manual maintenance uses the same target-stop rule; automatic
eligibility remains strictly above `edge_upper`. All limits come from settings.

The selection helper uses subset-reduction states below the required reduction;
crossings are terminal, so no extra group is added after the target is reached.
It is a structural choice, not semantic grouping or content distillation.
Preview shows the selected plan, apply revalidates it, and the transactional undo
record contains only applied groups. Existing committed undo records remain usable.

## Examples and acceptance

- Degree 52, target 45: choose a proposed eight-member group (reduction seven)
  over an earlier thirteen-member group (reduction twelve): stop exactly at 45.
- Degree 52, four thirteen-member groups only: select **one**, yielding 40,
  not all four yielding 4. No smaller reduction is offered in that proposal.
- Reductions 6, 4, 3 with gap 7: choose 4+3 rather than a greedy 6+3.
- Existing 50/45-degree control nodes are never automatic candidates.

The adapter also asks for `max_members=min(edge_upper-1, max(2,gap+1))`.
For 52→45 this is eight. This request alone is not a guarantee: the model
can violate it. Core structural group validation still allows up to
`edge_upper-1` members; the closest whole-group fallback handles such proposals
without inventing semantic subgroups. Therefore this change limits unnecessary
regrouping but does not guarantee exactly 45 for every model response.

## Real Gemma repetition

Same model, original bible, original 153-node synthetic fixture and real idle
worker; temporary DBs only. Report:
`D:/Test/Luca/sleep-check-20261022-152757-065979.json`.

| Run | Model proposal | Applied plan | Worker duration |
| --- | --- | --- | ---: |
| 1 | Two groups, reductions 8 and 11 | One nine-member incoming Botanica group: **52→44** | 15.005 s |
| 2 | Four groups, each reduction 12 | One thirteen-member incoming Botanica group: **52→40** | 16.612 s |

All structural, family-directory, reachability, restart and exact-undo checks
passed. Both selected groups had pure controlled membership. This does not
prove title accuracy or general semantic reliability; discarded groups are not
certified. In run 1 a discarded outgoing “Astronomia” group mixed topics. Raw
proposals remain in the report so selection cannot hide that evidence.

Gemma ignored the requested eight-member limit in both runs. The applied plans
therefore undershoot by one/five arcs, respectively: not a claim of exact 45.
Enforcing smaller LLM proposals or independently reviewing semantics would be
separate work. No bible, runtime config, dependency or personal memory was changed.

## Verification

New tests cover exact-target preference in a real graph, minimal indivisible
undershoot, tie-breaking, insufficient proposals, the adapter's configured gap
and 100 seeded comparisons against exhaustive subset enumeration. Existing
integrity, process-crash, family navigation and undo tests remain active.

Delivery: 280 Python tests, OK (seven optional hardware/service skips),
19 JavaScript tests passed, Ruff and `git diff --check` clean. A forged plan
containing unnecessary groups is also rejected on apply without any writes.
