# Luca

Luca is an experimental project exploring an explicit, persistent memory rather than a pre-trained language model.

The first experiment is deliberately narrow: validate the storage core for **cells** and directed **edges**.  The questions are practical:

- Can an edge be found directly from `(source_id, target_id)`?
- Can every outgoing edge `A:*` be read efficiently?
- Can every incoming edge `*:B` be read efficiently?
- What are the write, lookup, scan, and on-disk costs at increasing scale?

This repository currently contains only that foundation. It does not contain an agent, a user interface, an LLM, or an associative/vector index.

## Model

- A **cell** is an atomic, persisted item of memory, addressed by a compact positive integer.
- An **edge** is a directed relation between two cells. Its physical address is the ordered pair `(source_id, target_id)`.
- The primary storage index serves exact lookup and outgoing traversal. A secondary index on `target_id` serves incoming traversal.

The design intentionally leaves relation-space search for a later experiment. It must not be introduced before the deterministic graph core has been measured.

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

## Status

This is an intentionally replaceable baseline implemented with SQLite. It validates the data model and access patterns before we commit to a custom page format, a cache policy, or an associative relation index.
