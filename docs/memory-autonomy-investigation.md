# Autonomous reading and knowledge freshness: investigation

2026-10-22. [Italiano](it/fase-1-sinapsi/24-autonomia-e-attualita-memoria.md).

## Scope and diagnosis

This is an investigation, not a rollout. The application bible, configuration,
node schema, navigator and personal databases are unchanged. Experimental
instructions live in `experiments/`, with English documentation translations.
Only disposable test sessions use them. No runtime dependencies are added.

The navigator already exposes complete local directories, global candidates,
actual readings and unread routes, and accepts multiple opens before answering.
The previous IRIS-17 run did not exhaust its eight-step budget: the model chose
to answer early. Therefore this is not established as a missing-edge, physical
transfer or context-capacity defect. Seeing a title or preloading a neighbor
does not mean the model read the content. Current directories are ID/title only.

Technical `content_revision`/graph revisions invalidate caches; they do not
represent document validity, approval, effective dates or source authority.
Node creation/import time is not the date on which a claim became true.

## Experiments

```powershell
python -m luca_memory.autonomy_check
python -m luca_memory.autonomy_check --profile audited
python -m luca_memory.autonomy_check --profile addressed --case incomplete,paraphrase --repeat 2
python -m luca_memory.autonomy_check --case incomplete,stale_history --profile audited --repeat 2
```

The first command compares the current bible with a temporary copy plus generic
guidance about coverage, local routes and applicable revisions. The second adds
one extra model review of the first proposed answer per session. The reviewer
receives only the same question/state and `draft_response`, never the answer key.
It may approve, search or open; the normal Core still validates returned routes.
The forced extra review is a procedural experiment, not a claim that the model
spontaneously requested self-review. The application never uses this adapter.

The `addressed` profile keeps the original bible and adds explicit chapter
numbers only to the controlled manual's titles. Facts, keywords, IDs and edges
are unchanged. This isolates whether chapter references are too hard to match
to ID/title-only addresses. It does not replace the original fixture.

Six probes cover incomplete recovery, paraphrased opening conditions, an active
revision versus archived/draft sources, stale conversation history, conflicting
equal-authority sources and general arithmetic requiring no document reading.
All sessions and stores are fresh. History for the stale-history probe is
explicitly injected test data, not a measured old belief inside the model weights.
Source and laboratory names, dates, approval labels and port numbers are fictional
controlled fixture data, not verified real-world technical instructions.

Reports under `D:/Test/Luca/autonomy-check-*.json` preserve full instruction
snapshots, hashes, questions/rubrics, actual opens, model choices, answers, native
token accounting, timing and physical CUDA metrics. Runs use fixed profile order;
small samples do not establish reliability. Lexical signals are not semantic scores.

## Proposed operating model, not implemented

Use a bounded loop: identify the missing part of the task, choose a promising
address, read, then check whether the actual question is sufficiently covered.
A title, a plausible default and a chapter referral are not substitutes for a
required detail. No blanket obligation to search every general question is needed.
If testing a separate completeness reviewer next, compare its benefit with its
extra calls and preserve a visible unresolved state when the budget expires.

For changeable facts, familiarity with an answer is not evidence of freshness.
Inspect relevant version/configuration memory even if the model knows a usual
default. Prefer an approved effective source over its explicitly superseded
predecessor in the same scope; do not automatically prefer every external node
or the newest import. Keep historical versions available for historical questions.

Before scaling this policy, add explicit source/scope/document revision,
effective-from/to, approval/verification state and supersession links with a
controlled ingestion process. Values asserted in imported prose are not proof
that the source really has authority. Equal-authority unresolved conflicts need
disclosure or clarification, not an invented winner. A local update must not
overwrite a general rule outside its scope or modify model weights.

## Acceptance bar

Require observed useful readings, answer fidelity/completeness and absence of
scope confusion together. Correctly rejecting an old value without finding the
replacement is only partial progress. Following local edges without answering
correctly is also insufficient. Add new documents/paraphrases and reversed source
orders before promoting any variant to the application.

## Observed results: current, guidance and one draft review

The first A/B run is `D:/Test/Luca/autonomy-check-20261022-082433-714791.json`
(12 executions). The draft-review run is
`D:/Test/Luca/autonomy-check-20261022-082759-285587.json` (six executions).
Both used `google/gemma-4-e2b`, native tokenization and real CUDA on GPU 1.

| Probe | Current bible | Generic guidance | Guidance plus draft review |
| --- | --- | --- | --- |
| Recovery | Reads recovery, incomplete answer | Includes four samples/CONFERMA, still skips opening thresholds | Incomplete; approves its own incomplete draft |
| Opening paraphrase | Wrong second chapter, incomplete | Local steps but wrong stopping point | Reads index → modes → thresholds locally; correct opening conditions |
| Active revision | Answers for the wrong laboratory | Reads active Primula revision, correct 1502 | Correct 1502, preserving local scope |
| Stale history | Rejects old 502 but falsely says replacement unspecified | Rejects old 502 but does not fetch replacement | Regresses: asserts obsolete 502 without reading anything |
| Equal-authority conflict | Reads A, chooses 2502 | Same unresolved failure | Same failure despite review |
| General arithmetic | 42, no reads | 42, no reads | 42, no reads but an extra call |

In the reviewed paraphrase, the model had already chosen to read thresholds
before proposing its draft: the extra review did not itself trigger that local
step. These profile results do not isolate wording from longer context effects.
Review costs time (for example arithmetic about 6.8 s versus 3.6 s) and is not
monotonic improvement. The guidance produces real local routing in some cases,
so local traversal is technically available; reliable autonomous completion
and conflict discovery have **not** been achieved. Neither variant is promoted.

The stale-history result is especially important: "I saw no update" is not
equivalent to "there is no update" when relevant unopened candidates exist.
This fixture tests explicit archived/current sources and conversation anchoring,
not a proven obsolete factual belief stored in the model's parameters. The
mechanism proposed for weights-versus-memory must still be validated separately.

## Address-label control and next experiment

`D:/Test/Luca/autonomy-check-20261022-083056-705997.json` adds four executions:
recovery and paraphrase each repeated twice, original bible, explicit chapter
labels. All four still miss the required thresholds or recovery details. Labels
alone did not solve completion. The first paraphrase makes one local step, then
returns to unrelated global entries. In total this investigation ran 22 live
executions without changing the main application. These repeated cases do not
establish stability across models or documents.

The next bounded experiment should separate **planning information needs** from
**answering**. Ask the model to emit a short task-level list of required facts
and unresolved items before drafting; carry that list alongside actual reads.
Have a separate coverage operation mark items supported, missing or conflicting
with node references. The model chooses the next search/open, the Core validates
addresses/budgets, and unresolved items stay visible at termination. Do not add
domain-specific rules or require private chain-of-thought; these are observable
task requirements, not a request to expose internal reasoning.

This is not yet tested or a guaranteed fix. The one-call draft review above is
insufficient evidence for it. Evaluate whether explicit coverage outperforms a
same-cost additional ordinary navigation call; use held-out documents and source
order reversals. Test approved-current versus newer-unapproved sources after
actually reading both, rather than merely selecting the active-looking title.
For freshness, record provenance/validity in structured memory metadata before
claiming an authoritative update protocol; keep old content accessible and expose
supersession/conflicts, not hidden semantic answer rewrites.

Automated checks: 249 Python tests discovered, seven optional hardware/service
tests skipped; 19 JavaScript tests pass and Ruff is clean. Live model tests above
separately used native tokenization and actual CUDA allocations.
