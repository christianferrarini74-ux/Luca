# Controlled-document experiment: IRIS-17

2026-10-22. [Italiano](it/fase-1-sinapsi/23-esperimento-documento-controllato.md).

## Material and isolation

The [manual](iris17-manual.en.md) describes a fictional, internally consistent
irrigation controller, not a real product. Its Italian operational version is
represented verbatim by seven nodes in `seed/iris17_controlled_v1.json`: one
entry/index and six chapters. Index edges reach all chapters; additional real
edges connect startup, thresholds, alarm, recovery and maintenance. These are
ordinary connected nodes, not artificial family parts.

The answer key lives separately in `tests/fixtures/iris17_questions.json`.
It is never passed to the model. Tests check source/seed fidelity and topology.
This is a hand-prepared controlled fixture, not a PDF importer or an automatic
chapter splitter. The regular empty library and personal databases are untouched.

## Paired experiment

Run from the checkout using the same configured model, bible and token budgets:

```powershell
python -m luca_memory.controlled_document_check --case all
# Shorter single pair:
python -m luca_memory.controlled_document_check --case chain
```

Each question has two independent, fresh sessions with temporary databases:
first an empty baseline, then the document. Each arm creates a fresh adapter,
with no conversation or focus carried over. Questions name the device but do
not name node IDs or force traversal. No rule requires reading the manual.
Runtime settings, model ID, bible snapshot, fixture hashes, actual readings,
navigation choices, physical-memory snapshots, times and final replies are
saved under `D:/Test/Luca/iris17-check-*.json`. Reports also include the private
rubric for human review, after generation. Exit status indicates execution
errors, not semantic acceptance.

## Seven probes

- Direct retrieval: sampling frequency.
- Paraphrase: dry soil but no water; conditions for opening.
- Linked application: E42, recovered signal, return to irrigation.
- Boundary: 27%, 28%, 27% with valve closed.
- False premise: power cycling clears E42.
- Missing fact: supply voltage.
- Maintenance procedure and interval.

Score correct facts, preserved conditions, unjustified additions and recognition
of missing information separately. Compare baseline/document answers and actual
reads. Lexical matches and expected-node coverage are diagnostic signals only:
negation can fool them, and one chapter may repeat a fact from another.
Reading all expected nodes is not itself a correctness requirement or proof of
local traversal: inspect the trace for global entries versus actual edge steps.

Fixed baseline-first order and deterministic fixture facts limit the experiment.
A single run is not statistical evidence, and these small nodes do not establish
storage pressure, eviction quality or performance on large books. No new model
instructions, semantic filters or runtime dependencies are introduced.

## First live run — not accepted as complete

All fourteen executions completed with `google/gemma-4-e2b`, native token
counting and real CUDA on GPU 1. Evidence:
`D:/Test/Luca/iris17-check-20261022-080943-175245.json`.
Document SHA-256: `99f7abad79d4a14ab5153b8cbc3929b9ee44638a7366fa118cf4db589bc43d16`.
The bible and graph runtime were not changed to improve the results.

Human inspection finds correct sampling frequency, threshold-boundary reasoning
and maintenance. The paraphrase answer omits the opening thresholds; it reads
modes and then unrelated maintenance. The recovery answer reads chapter 4 but
omits the four valid samples and CONFERMA, and never reads the opening conditions.
The false-premise answer rejects power cycling but does not read the recovery
procedure. The missing-voltage answer invents no number, but reads only the index
and wrongly treats the device being fictional as the reason for missing voltage.

Every opened node in this run was a global entry: **no local edge traversal was
observed**. Resident/preloaded neighbors are not equivalent to chapters actually
read by the model. The empty maintenance baseline repeated searches to the
eight-step limit; no execution error occurred, but this is inefficient behavior.
Thus memory-dependent retrieval/use is demonstrated on this fixture, not reliable
multi-chapter exploration. Do not report the lexical indicators as a pass rate.

Automated verification: 244 Python tests discovered, seven optional hardware/
service tests skipped; 19 JavaScript tests pass and Ruff is clean. The live run
above separately exercised native tokenization and physical CUDA storage.
