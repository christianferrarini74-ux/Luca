# Separating the real library from synthetic experiments

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

2026-10-22. [Italiano](it/fase-1-sinapsi/22-avvio-biblioteca-reale.md).

The default configuration now uses `seed/library_empty_v1.json` and the new
`D:/Test/Luca/luca_library.sqlite` database. The initial graph has zero nodes
and zero edges. No factual collection is invented to replace the old examples.
`memory_policy` is `grounded`; the bible, model reasoning, budgets and physical
carousel are unchanged. This setting is metadata, not a new output filter.

The previous `D:/Test/Luca/luca_v1.sqlite` database is left untouched, including
any additions made during experiments. The synthetic seed remains in the
repository for regression and live checks with separate temporary storage.
Old reports remain historical evidence, not active knowledge.

An already-running process continues to use its old database and chat history.
Exit with Luca's **Esci** button, then start `python run_luca.py` and use a new
conversation. The new database is created at that startup, not by a migration
of the running process. Do not copy the old database over the new one.

Regression coverage verifies empty navigation with a scripted adapter,
persistence of subsequently added knowledge across reset/restart, and rejection
of attempts to initialize an experimental store with the new seed. These are
structural tests, not a new live-model evaluation.

Next, choose the first real source together, establish its title/index/chapter
nodes and source/page references, then validate answers against that source.
PDF ingestion and automatic structuring are not implemented by this change.
