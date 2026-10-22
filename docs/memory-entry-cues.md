# Memory entry and dialogue continuity — 2026-10-21

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

[Italiano](it/fase-1-sinapsi/14-ingresso-memoria-e-dialogo.md)

## Evidence and corrections

The reported dialogue failed to retrieve “I Topi Intagliatori di Formaggio”,
although that node exists in the configured seed (ID 18). Read-only inspection
of the running API showed an `answer` action with no focus and `expose_memory`
false. This supports a missed-entry diagnosis, not missing stored knowledge.

Previously, global search depended entirely on the model requesting it. Also,
when the model declined exposure the prompt asserted that no relevant local
memory existed, even if no search had been performed. Finally, a recent long
answer could cause the whole question/answer pair to be excluded by `history_limit`.

Implemented changes:

- Before each navigation turn, consult the global index's metadata projection:
  indexed title, slug and keywords. Offer at most `global_candidates` ID/title
  entries. No node body is read or promoted, and no semantic target is chosen
  by the Core. The LLM can still search, open a candidate or answer generally.
- Use token-quoted OR search for these entry cues rather than an AND match of
  the entire conversational question. The existing explicit full-text/alias
  search remains available. This is lexical lookup, not synonym understanding.
- Keep metadata projection updates in the node transaction. Populate missing
  projections on migration without replacing content; remove deleted entries.
- Say memory was **not used**, not that it **does not exist**.
- Preserve the latest oversized conversational pair as explicitly marked byte
  excerpts within the existing budget. Stored history is unchanged; no semantic
  summary, history LLM or new persistent conversation memory is introduced.
- Give the navigation LLM the complete directory, but give the final answer call
  only selected knowledge. Routing JSON is not knowledge provenance. Exposure
  spans and diagnostics reflect the answer payload's actual byte positions.

The dashboard/API reports `entry_candidate_ids`, `explicit_search_performed`
and `history_excerpted`. These are diagnostic facts, not answer-truth scores.
The normal single entry point and dependencies are unchanged.

## Verification and unresolved behavior

**158 automated tests passed including four real CUDA checks.** Tests cover
metadata-only lookup without payload reads, rollback/rename/delete consistency,
no forced memory opening, bounded history excerpts and separate answer/navigation
contexts. Compilation and whitespace checks passed.

The isolated synthetic suite achieved **8/8** in
`D:/Test/Luca/phase11-live-20261021-180932.json`, including spontaneous recall that
failed previously. This is one fixture run, not a general reliability result.
Some successful turns still had redundant back-and-forth navigation within the
configured step limit; this remains an efficiency issue.

The seven-message reproduction of the user's dialogue correctly opened node 18
on entry and retained/recalled it after general questions. However, the final
strict report is **not green**:
`D:/Test/Luca/dialogue-live-20261021-181146.json`. Five of six scored lexical/scope
checks passed; one conceptual question is explicitly left for manual review.
The model still adds unsupported causal explanations and expressions such as
“description provided” / “it is said”. The runner separately records these style
warnings and exits unsuccessfully rather than claiming complete acceptance.
Its lexical checks are not certification of biological accuracy or faithfulness.

Reproduce with LM Studio available:

```powershell
python -X utf8 -m luca_memory.dialogue_check
python -X utf8 -m luca_memory.live_memory_check
```

Both runners use disposable databases under the configured data directory, not
the personal database. The running application was inspected but not restarted
or mutated through its API. To load the fixes, stop it with **Esci/Arresta Luca**
and start `python run_luca.py` again; schema/index migration occurs on startup.

Remaining work is model response faithfulness, avoidance of invented causes and
semantic/style consistency after general-knowledge digressions. This patch does
not claim to solve those through filtering or a larger model, and does not alter
the agreed family/directory architecture or add Cesare integration.
