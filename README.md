# Luca

[English](README.md) | [Italiano](README.it.md)

Confirmed and closed conceptual specification, not yet implemented: [navigable and reorganizable memory](docs/bounded-synaptic-memory-design.md), ready for the roadmap.

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

Luca is an experimental project exploring an explicit, persistent memory rather than a pre-trained language model. Every major claim must earn its place through a small, reproducible experiment.

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

The current milestone has a free LLM conversation path, bounded retrieval from
cell-and-edge memory, controlled memory proposals, and a deterministic fallback.
The next work extends consolidation and associative retrieval without moving
memory ownership into the GUI or the model.
