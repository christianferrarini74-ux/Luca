# Luca

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

Try this short dialogue:

```text
Parlami del sole.
Luca, ricorda che il sole produce luce.
E cosa produce?
```

Close the program with `esci`, run it again with the same database, then ask:

```text
Cosa produce il sole?
```

The learned assertion is stored in the database with a trace and an append-only event entry.

## Status

This is an intentionally replaceable SQLite baseline. It validates data access and thought budgets before we commit to a custom page format, a cache policy, GPU runtime, or associative index.
