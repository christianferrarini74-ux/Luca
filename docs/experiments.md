# Luca: experimental protocol

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

## Method

Every component begins as a controlled experiment. We define the data, expected outcome, comparison baseline, resource budget, and failure condition before calling it a part of Luca.

## Experiment 1 — direct graph navigation

**Claim:** cells connected through addressed edges can be retrieved and expanded quickly at scale.

**Data:** synthetic cells and balanced directed edges.

**Operations:** exact lookup `(A,B)`, outgoing scan `A:*`, incoming scan `*:B`, and bounded local expansion from one or more seeds.

**Measures:** ingest rate, lookup latency, scan latency, local-thought latency, RAM context size, disk size, and correctness of returned paths.

**Pass condition:** the direct indexes return the complete expected neighbourhood and bounded expansion remains within its declared resource budget. Performance results are recorded; no fixed target is invented before observing the machine.

## Experiment 2 — associative address, CPU-only

**Claim:** an address learned from Luca's own graph and activation history can retrieve useful distant candidates better than direct navigation alone.

**Data:** synthetic families of graph patterns, with independently recorded ground truth. Include shared-cell families, structurally similar but unconnected families, noise, and deliberate counterexamples.

**Comparison:**

```text
A. direct graph only
B. direct graph + learned associative address
```

**Measures:** recall@k, precision@k, false-jump rate, index build/update time, disk/RAM use, and query latency.

**Failure condition:** B does not outperform A on declared distant-pattern tasks, or improves recall only by producing an unacceptable false-jump rate. We then revise the learning signal rather than hide the result behind a larger model.

## Experiment 3 — tier policy without a GPU dependency

**Claim:** a strict RAM/VRAM budget retains useful reasoning context while limiting transfers and memory use.

**Method:** run the CPU reference with independently varied RAM-context and simulated-VRAM-focus capacities.

**Measures:** retained relevant paths, expansion time, focus size, eviction rate, and result stability at each budget.

**Pass condition:** smaller focus degrades progressively rather than unpredictably, and the coordinator can explain which cells were excluded.

## Experiment 4 — one GPU

**Claim:** a GPU accelerates a defined operation without changing its meaning.

**Method:** choose one CPU-proven operation—activation propagation, candidate scoring, or associative ranking—and implement a GPU backend. Feed identical snapshots to CPU and GPU.

**Pass condition:** semantic parity with the CPU trace, measured speed improvement after transfer costs, and no persistent write from the worker.

## Experiment 5 — multiple GPUs

**Claim:** independent branches of a thought can run concurrently and be consolidated safely.

**Method:** partition declared independent branches across workers; merge their proposals through one CPU/RAM consolidator.

**Measures:** speedup, scheduling overhead, duplicate work, merge conflicts, reproducibility, and VRAM utilisation.

**Pass condition:** gains exceed coordination cost and the resulting consolidated trace is reproducible from the same inputs and budgets.

## Non-negotiable records

Every experiment must save or print enough information to reproduce its conclusion: data seed, configuration, budgets, software version, timings, resource use, expected result, actual result, and decision made from the evidence.
