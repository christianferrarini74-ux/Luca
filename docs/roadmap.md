# LUCA: validation roadmap

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

This roadmap is ordered by evidence. A later stage is not considered justified merely because an earlier component has been coded.

## 1. Conversational memory demonstrator

Build a persistent, small-domain dialogue in which LUCA can answer simple questions, receive a new fact, preserve it across restart, keep a short topic context, refuse unknown claims, and record a correction with provenance.

**Evidence:** repeatable multi-turn transcripts and tests with a separate evaluation set.

## 2. Native Memory Fabric

Replace the baseline database-only assumption with a locality-aware memory fabric: SSD-resident regions, RAM cache budgets, explicit load/evict decisions, append-only durable updates, and a simulated VRAM focus.

**Evidence:** bounded thought execution on a memory larger than the active RAM context, with recorded cache and I/O behaviour.

## 3. Associative address experiment

Test whether addresses learned from topology, co-activation, and repeated path roles retrieve useful distant candidates beyond direct `A:*` and `*:B` traversal.

**Evidence:** improvement over direct-graph-only retrieval on predeclared synthetic and invented-domain tasks, with false-jump rate reported.

## 4. Single-GPU parity and acceleration

Move one CPU-proven operation to a GPU while preserving its trace and result. The GPU receives a bounded snapshot; it cannot write durable memory.

**Evidence:** CPU/GPU parity plus speed benefit after transfer cost.

## 5. Multi-GPU thought branches

Schedule independent branches across GPUs with individual VRAM budgets and one consolidator.

**Evidence:** reproducible merges and a speedup that exceeds coordination cost.

## 6. Distributed memory fabric

Separate global persistent memory from compute nodes. Nodes load versioned regions, calculate locally, return proposals, and commit through a controlled consolidation path.

**Evidence:** multiple processes use the same durable memory without silent conflicts or loss of provenance.

## Presentation threshold

LUCA is ready to present as a functioning concept when it can demonstrate, end-to-end and reproducibly:

```text
teach → persist → restart → retrieve → contextualise → correct → explain
```

The presentation must state its limits openly. The purpose is to invite serious technical evaluation and instruction partnerships, not to claim parity with frontier LLMs.
