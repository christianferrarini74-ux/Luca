# Luca

[English](README.md) | [Italiano](README.it.md)

Current sleep planner: [semantic categories, deterministic arc reduction](docs/category-routing-planner.md).
Both Gemma models classified the full fixture; the Core reached 52→45 in all four live runs.

Model comparison: [sleep with Gemma 26B A4B](docs/sleep-gemma26-comparison.md).
Four runs: no mixed-theme proposals, but three insufficient reductions rejected; model size alone does not complete autonomous maintenance.

Maintenance correction: [stop at the configured target](docs/maintenance-target-stop.md).
Apply only necessary whole groups; retain original routes for unselected groups.

Integration: [memory producer/consumer contract](docs/memory-integration-contract.md).
Nodes, arcs, families, budgets, atomic mutations, APIs and an executable producer example.

Sleep verification: [controlled real-worker and fault tests](docs/sleep-reorganization-verification.md).
Structure/restart/undo verified; a real mixed-theme proposal exposes the limit of semantic grouping.
Luca manages memory; external software produces and partitions content. Library creation is out of scope.

Goal-first experiment: [complete recovery without changing node visibility](docs/goal-first-recovery.md).
Two fresh Qwen runs read the missing thresholds and complete the procedure; limited evidence, not a general guarantee.

Follow-up investigation: [asking Luca why it stopped reading](docs/memory-stopping-interview.md).
Same-session self-assessment is checked against actual reading traces, not taken as causal proof.

Measured comparison: [Qwen 27B, required reads and multi-GPU carousel coexistence](docs/model-and-required-read.md).
24 live executions; larger-model gains and remaining limitations, with per-call costs.

Investigation: [autonomous reading and knowledge freshness](docs/memory-autonomy-investigation.md).
Experimental profiles remain isolated; autonomous completion is not yet reliable.

Controlled experiment: [IRIS-17 manual, isolated paired questions and reading traces](docs/controlled-document-experiment.md).

Real-library workspace: [empty initial memory, synthetic examples isolated](docs/real-library-start.md).
Exit and restart Luca to use the new database; the previous database is preserved.

CI maintenance: [reproducible GitHub checks](docs/github-actions-checks.md),
with lint and Python/JavaScript tests on explicit Ubuntu and Windows runners.

Code maintenance: [simplification and internal English comments](docs/code-maintenance-review.md).
235 Python tests with real CUDA/tokenizer and 19 JavaScript tests passed.
No behavior, dependency, configuration or bible changes. Restart Luca cleanly
and reload the page to load the revised implementation.

Graph fix: [centering after dragging and changing views](docs/memory-graph-centering.md).
10 JavaScript regression tests and 219 Python tests passed. Reload the page
to load the corrected frontend; no server restart needed.

New: [interactive memory graph](docs/memory-graph.md), global/focus views,
expandable families, real-tier colors and explicit recall separate from inspection.
No new dependencies. 219 Python tests with real CUDA/tokenizer and 5 JavaScript
tests passed. Restart Luca cleanly to load the new graph API.

Latest bible revision: [acquired memory plus general knowledge](docs/integrated-knowledge-bible.md).
210 automated tests passed with native tokenization and real CUDA; the new
integration dialogue passed 8/8 reading/lexical checks. Style and unsupported
extra details remain imperfect: see the report. Start a fresh conversation;
the bible itself reloads on each request, without restarting Luca.

Current reasoning contract: [one bible, no semantic output filters, multi-node readings](docs/reasoning-contract.md).
Instructions come only from `runtime.bible`; model reasoning is no longer forcibly
disabled. Generation options and operation budgets are explicit in YAML.
206 automated tests passed with native tokenization and real CUDA enabled.
Final synthetic live checks: 8/8. Weather-dialogue checks: 7/8; spontaneous
further exploration remains unreliable. See the report before claiming acceptance.

Current context: [70,000 model tokens, configurable in YAML](docs/token-context.md).
Native LM Studio token counting, token-bounded history without fixed turn caps,
and unchanged physical byte accounting. No additional dependencies. 182 tests passed
with native tokenizer and real CUDA enabled. Restart Luca with `python run_luca.py`.

Phase 1.11 implemented: [canonical families, complete indexes, LLM navigation and atomic maintenance](docs/phase-1-11-implementation.md).
The [confirmed design](docs/bounded-synaptic-memory-design.md) remains the conceptual reference.
Start with `python run_luca.py`; configuration selects `memory_planner: llm` and 50/45 external-edge limits.
Latest: [memory-entry and dialogue fixes](docs/memory-entry-cues.md). Automated suite: 158 tests passed including real CUDA; synthetic live checks: 8/8. The full dialogue still exposes unsupported explanations and provenance/style problems; acceptance is not complete. Earlier [live evidence](docs/phase-1-11-live-validation.md) is preserved.

Latest review: [seed safety, exact alias summaries and measured GPU transfers](docs/review-hardening.md).

Physical memory milestone: [SSD/RAM/GPU carousel](docs/physical-memory.md).
Complete nodes now use real CUDA device allocations, with no new Python packages.
The configured GPU is ordinal 1; select an available device in `config.yaml`.
See the [dependency audit](docs/dependency-audit.md) and run the synthetic check
with `python -m luca_memory.hardware_check`. Real-library tests remain joint work.

Previous milestone: [memory development stages 1–5](docs/memory-development-roadmap.md).

Current Phase 1 runtime: [synaptic memory, search policies and dashboard](docs/synaptic-memory-runtime.md).
Start with `python run_luca.py`; the current cockpit is served by Python on port 8765.
The original experiments below are retained as historical background.

Luca is an experimental project developing explicit, persistent memory for a language model.
The LLM contributes reasoning and general knowledge; Luca manages navigable memory.
Every major claim must earn its place through a small, reproducible experiment.

## The working model

- **Cells** contain Luca's knowledge and state: concepts, experiences, hypotheses, evidence, and conclusions.
- **Edges** contain no semantic payload. They are directed addresses between cells, identified by `(source_id, target_id)`.
- The direct graph is Luca's certain navigation: `A:*` finds routes out of a cell and `*:B` finds routes into it.
- A later associative index may suggest distant candidates, but only the explicit graph may verify a proposed connection.

```text
SSD   complete persistent brain
RAM   active context + topological neighbourhood
VRAM  the smallest, highest-priority working set for one thought
```

The CPU coordinates work and consolidation. GPU workers are optional accelerators: the CPU reference implementation remains the semantic baseline, and GPUs never write directly to persistent memory.

Read [the architecture](docs/architecture.md) and [the experimental protocol](docs/experiments.md) before extending the system.
The first controlled Italian seed is described in [the curriculum specification](docs/curriculum.md).
The project's purpose and evidence-based milestones are set out in [the vision](docs/vision.md) and [the roadmap](docs/roadmap.md).
The replaceable boundary between language and durable memory is defined in [the language-adapter protocol](docs/language-adapters.md).
The indexed retrieval layer is described in [memory search](docs/memory-search.md).

## Current experiment

The current code validates deterministic graph access and provides a CPU reference for a bounded local thought: activate seed cells, expand through incoming and outgoing addresses, score the discovered context, and retain a smaller VRAM-sized focus. It contains no LLM, embedding model, GPU dependency, or associative index yet.

## Run a small benchmark

Python 3.11+ is sufficient; no third-party dependency is required.

```powershell
python -m luca_memory.benchmark --cells 10000 --edges 100000 --database .\luca-benchmark.sqlite
```

The default workload is the planned 1 million cells and 10 million edges. Start with a small run when checking the environment.

```powershell
python -m luca_memory.benchmark
```

## Verify the core

```powershell
python -m unittest discover -s tests -v
```

## Try the initial Italian seed

```powershell
python -m luca_memory.demo "Come ti chiami?"
```

## Run the persistent conversation demonstrator

```powershell
python -m luca_memory.chat --database .\luca.sqlite
```

The default runtime uses the local Gemma conversation adapter. Start the LM
Studio local server; Luca discovers the configured model and asks LM Studio to
load it when it is installed but not currently resident. The default model key
is `google/gemma-3-1b`.

```powershell
python run_luca.py
```

The endpoint and model are configured under `llm.runtimes` in `config.yaml`.
The LLM responds freely with retrieved memory context; structured output is
used only when Luca extracts a durable memory proposal. Set
`runtime.language_adapter: rules` only for deterministic offline tests.

Try this short dialogue:

```text
Parlami del sole.
Luca, ricorda che il sole produce luce.
E cosa produce?
```

Close the program with the GUI `Esci` button, run it again with the same database, then ask:

```text
Cosa produce il sole?
```

The learned assertion is stored in the database with a trace and an append-only event entry.

## Run the complete Luca runtime

The single project entry point reads `config.yaml`, starts the Python runtime,
starts the frontend, and opens the dashboard in the browser. The GUI remains a
frontend only: it renders state returned by Luca and does not contain memory or
language logic.

Start the complete runtime from the repository root:

```powershell
python run_luca.py
```

Start LM Studio before using the default Gemma conversation adapter. Luca then
selects and loads the configured model automatically:

```powershell
python run_luca.py
```

The dashboard calls `http://127.0.0.1:8765/api` for chat and runtime
snapshots. The backend remains the only component allowed to access Luca's
memory and LLM connector.

## Status

Luca exposes canonical families, complete first-degree directories, atomic
mutations, physical tier storage and guarded sleep reorganization. The chat and
dashboard are test consumers. The integration contract and controlled sleep
evidence above define the current delivery; semantic grouping is not guaranteed.
Content production, document import, automatic splitting, library creation and
Cesare integration are outside the current scope. Bible work is closed unless
an interface-context problem prevents memory use.
