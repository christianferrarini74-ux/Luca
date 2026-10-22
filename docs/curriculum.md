# Luca: initial curriculum

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

## Purpose

Luca does not start with completely empty memory. It receives a limited, verifiable linguistic and conceptual seed that is separate from the reasoning engine.

An external AI may prepare teaching material, but it will not enter Luca's answer loop. Its output is importable only when expressed in this readable format and reviewed.

## Principles

- Every taught item is a cell with explicit content, type, and provenance.
- A fact is an `assertion` cell containing addresses to its subject, predicate, and object.
- Edges remain semantic-free addresses: subject → assertion and assertion → components.
- Evaluation questions are separate from lessons.
- Every answer must report the trace of cells that made it possible.

## Format

The JSON file contains a `version`, a `language`, and an ordered list of cells. Slugs are human-readable addresses used only in the curriculum; on load they become compact numeric IDs.

```json
{"slug": "fuoco", "kind": "concept", "label": "fuoco"}
{"slug": "calore", "kind": "concept", "label": "calore"}
{"slug": "fuoco_produce_calore", "kind": "assertion", "subject": "fuoco", "predicate": "produce", "object": "calore"}
```

The loader creates these edges:

```text
fuoco → fuoco_produce_calore
fuoco_produce_calore → produce
fuoco_produce_calore → calore
```

This makes the assertion a cell Luca can work with, while edges serve navigation only.

## First language boundary

`ItalianSeedInterface` is intentionally a small rule grammar. It recognises a few Italian identity and physical-world questions and turns them into graph-retrieval targets. It is not a language model and must not be presented as general language understanding.

To run the initial seed:

```powershell
python -m luca_memory.demo "Come ti chiami?"
python -m luca_memory.demo "Chi è il tuo creatore?"
python -m luca_memory.demo "Cosa produce il fuoco?"
```

Evaluation cases, stored separately from lessons, run as follows:

```powershell
python -m luca_memory.evaluate
```

The first set includes three analogous experiences converging on `scalda`
(`fuoco`, `sole`, `forno`) and two contrastive experiences (`raffredda`,
`bagna`). This already makes it possible to measure topological navigation
before introducing an associative index.

## Next expansion

The next curriculum should add analogous experiences, counterexamples, evaluation questions that differ from the lessons, and provenance for every assertion. Only then can we evaluate distant associative retrieval without confusing it with simple repetition.

## Persistent instruction in the demonstrator

`python -m luca_memory.chat --database .\luca.sqlite` starts a persistent
session. For now it accepts an intentionally small instruction language:

```text
Luca, ricorda che il sole produce luce.
Luca, ricorda che il ghiaccio raffredda bevanda.
```

Each instruction creates or reuses concept cells, creates an assertion with
`user` provenance, adds the addresses, and records an append-only event.
The knowledge remains available after restart. The grammar is an explicit
boundary of the first demonstrator, not a claim of free-form language support.
