# Phase 1.11 — Real LM Studio validation

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

Date: 2026-10-21

[Italiano](it/fase-1-sinapsi/13-verifica-live-lmstudio.md)

## Result: 7/8, not full acceptance

The final synthetic run used `google/gemma-4-e2b` (Q4_K_M), real CUDA on device 1,
one resident node slot and two RAM slots. No personal database was opened.

| Check | Final result |
| --- | --- |
| Global search, entry selection and stopping to answer | Pass |
| Fragment reading with canonical parent identity | Pass |
| External navigation through the parent's shared directory | Pass |
| Spontaneous recall from a natural question | **Fail** |
| Updating a resident fragment and answering with its new code | Pass |
| General knowledge without forced memory exposure | Pass |
| LLM grouping and Core route restoration | Structural pass |
| Automatic idle code path with real LLM and restoration | Structural pass |

The failure trace shows the model choosing `answer` without opening the closing
fragment and inventing `VENTO-113`. The real code was available in that fragment.
The Core executed the chosen action; `use_memory: true` does not certify truth.

The freshness check explicitly focuses fragment 3 **before** modifying it, to
isolate cache coherence from the preceding semantic-navigation failure. The model
then uses the new `VELA-903`, not the old `RAME-731`, despite conflicting history.
This is not scored as autonomous entry selection.

Grouping reduces 51 external edges to 26, below target 45; restoration recovers
all 51 original directed routes. Idle time is accelerated for that check, not a
60-second interactive wait. Structural success is **not semantic validation**:
some generated groups named “Astronomia” contain fixture nodes titled “Geologia”.
Their names can mislead navigation even though addresses remain intact.

## Fixes and limits

- This server rejects `json_object`; structured calls now use `json_schema`.
- Legal action/ID schemas and explicit opening feedback prevent repeated no-op
  reopening. Returning to a different previously visited node is still allowed;
  total work remains bounded by `navigation_steps`.
- The old 160-token cap could expire during reasoning before any JSON answer.
  New `runtime.synaptic.navigation_output_tokens` and `maintenance_output_tokens`
  both default to 2048. Their reserves also reduce input allowance; complete
  directories are never silently clipped. Exhaustion and empty answers fail
  explicitly. Reasoning text is never executed as an action.
- Node/directory data is structured JSON rather than an escaped nested JSON string.

An intermediate configuration achieved 8/8, but repetitions failed spontaneous
recall. The final result deliberately reports the remaining failure, not the
best attempt. Larger output budgets fix truncation, not semantic reliability.
No model comparison or real-library accuracy claim is made.

## Reproduce

With LM Studio running:

```powershell
python -X utf8 -m luca_memory.live_memory_check
```

The runner loads `seed/phase11_validation.json` into a disposable database under
the configured storage directory, **not** the personal database. It writes a
timestamped JSON report, releases its CUDA allocations and leaves the existing
LM Studio model loaded. `--host-memory` selects host reference slots. Exit code 1
means a failed check, including the currently unresolved spontaneous recall.

Final report on this machine: `D:/Test/Luca/phase11-live-20261021-140838.json`.
Failed/intermediate reports are retained alongside it. The report records choices,
answers, group directions, source taxonomy and resource cleanup.

After the fixes, **151 automated tests passed**, including four real CUDA tests:
`LUCA_TEST_CUDA=1 python -m unittest discover -s tests`. Python compilation and
`git diff --check` passed. No new package dependency. No browser visual QA claimed.

Next acceptance work: reliable model-led recall and group-title quality. PDF
ingestion, distillation and Cesare integration remain outside this phase.
