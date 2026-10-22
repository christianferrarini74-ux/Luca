# Sleep grouping comparison with Gemma 26B A4B

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

2026-10-22. [Italiano](it/fase-1-sinapsi/31-confronto-sonno-gemma26.md).

Follow-up implementation: [classification separated from routing arithmetic](category-routing-planner.md).
The observations below preserve the preceding numerical-proposal interface.

## Controlled protocol

Repeat the [target-stop experiment](maintenance-target-stop.md) using the exact
installed model `google/gemma-4-26b-a4b`, Gemma 4 26B A4B Q8_0 (26B-A4B in the
local catalog). The comparator is `google/gemma-4-e2b` Q4_K_M, catalog size 4.6B.
The model names do not identify two dense models differing only in parameter
count: architecture/active parameters, tokenizer and quantization also differ.
This is a local model comparison, not an isolated causal parameter-count study.

Four fresh temporary databases use the same 153-node fixture, 52 external arcs,
50/45 thresholds, canonical family, controls, original bible, real polling
worker and one-second diagnostic idle/poll timers. No conversation history,
semantic correction or second reviewer is added. Context budget stays 70,000
tokens, temperature 0, maintenance output 8,192 tokens, provider timeout 180 s.

```powershell
python -m luca_memory.sleep_check --model google/gemma-4-26b-a4b --repeat 4
```

Baseline: `D:/Test/Luca/sleep-check-20261022-152757-065979.json`.
Inspect all raw proposed groups, including those discarded by the Core. Check
theme membership, title compatibility and the requested eight-member group
bound separately from target-stop selection, structural correctness, reopening
and undo. A structural `passed` flag is not a semantic acceptance result.

The larger model is loaded only for this experiment (70,000 requested context,
70,144 loaded by the backend, one parallel slot). The pre-existing E2B model
remains loaded with its original settings. No production config, bible, runtime
code, dependency or personal memory is modified.

## Small-model reference

In the matched-code E2B baseline, both runs produced proposals large enough to
reach the target, but both violated the requested eight-member bound. The Core
selected one pure group per run, yielding 44/40 external arcs. One discarded
outgoing group in run 1 mixed Botanica with Astronomia under “Astronomia”.
Run 2's four raw groups were pure. Applied-plan purity alone would therefore
miss a real error in the proposal. Baseline worker durations were 15.005 and
16.612 seconds; these are local observations, not a standardized speed benchmark.

## Four-run result

Report: `D:/Test/Luca/sleep-check-20261022-153755-744261.json`.
All four captured directory/constraint payloads are identical to the E2B
reference, as are the complete system-instruction hashes and maintenance
settings. History is empty, input is 2,643 model tokens, and no input excerpting
is reported. This is not a missing-neighbor or context-capacity observation.

| Run | Raw proposal | Total reduction | Result | Worker duration |
| --- | --- | ---: | --- | ---: |
| 1 | Three groups of four: incoming Botanica, incoming Astronomia, outgoing Botanica | 9 | Applied, 52→43; restart and exact undo passed | 133.532 s |
| 2 | Two groups of four: incoming Botanica, outgoing Botanica | 6 | Rejected before apply: would reach 46, not <=45 | 125.832 s |
| 3 | Same two four-member groups | 6 | Rejected before apply | 124.242 s |
| 4 | Same two four-member groups | 6 | Rejected before apply | 128.556 s |

All **nine raw groups**, including proposals rejected before application, have
pure controlled theme membership and compatible Botanica/Astronomia labels.
Each contains four members and respects the requested eight-member bound.
There is no observed thematic mixing in this four-run sample. This is distinct
from complete maintenance success, achieved in only run 1. The 43 outcome is
the closest whole-group result: two groups reduce six and three reduce nine;
the proposal offers no exact-seven combination.

In runs 2–4 the proposer supplies too little aggregate reduction. The Core's
error is `The proposed grouping does not reach edge_target.` It rejects the
plan before the application transaction, rather than partially applying it or
pretending that 46 meets the target. These rejected runs do not have successful
restart/undo acceptance checks and are not counted as passed maintenance.
The diagnostic correctly exits with code 1 despite good theme separation.

The test does not capture private reasoning or prove *why* the model stopped;
it demonstrates an insufficient proposal, not a verified internal arithmetic
error. Calling the two groups “eight removed arcs” would be wrong: they replace
eight original arcs with two connectors, hence a net reduction of six.

## Interpretation and closure boundary

For this easy labelled fixture the larger model removes the previously observed
theme-mixing symptom and respects the requested group size. That supports a
model-dependent semantic-proposal problem rather than an observed corrupting
graph transformation. It does not prove that parameter count alone explains
the difference or that mixed groups cannot occur with this model.

**The end-to-end autonomous maintenance point is not closed by changing models.**
Three of four proposals still fail the existing numerical contract. A robust
future design could return validation feedback to the proposer for a bounded
correction before application, without weakening thresholds or changing group
membership in the Core. That is a possible next intervention, not implemented
or claimed to work in this comparison. No bible optimization was performed.

The applied operation preserves all structural, family-directory and reachability
checks and survives reopening/undo. Thus this experiment finds no new failing
memory-transformation invariant; it exposes a remaining proposal-completion
limitation. This is controlled evidence, not library-scale certification.

## Cleanup and verification

Only the newly loaded 26B model was unloaded after it became idle. E2B remains
loaded with its original 131,072 context and four parallel slots. GPU memory
returned to the initial 6,935/14/14 MiB, utilization zero. All four diagnostic
workers joined; temporary databases were removed. Reports remain available.

Portable suite: 280 Python tests, OK with seven optional hardware/service skips;
Ruff clean. This delivery adds documentation only: production code, config,
bible, dependency list and personal memory are unchanged.
