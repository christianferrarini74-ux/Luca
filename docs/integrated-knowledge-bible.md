# Bible: acquired memory and general knowledge

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

Date: 2026-10-22. [Italiano](it/fase-1-sinapsi/17-bibbia-conoscenza-integrata.md).

## Changes

The `bible.md` rewrite treats read content as true contextual knowledge without
disabling the model's general knowledge. It preserves conditions and causal
direction, distinguishes content from ID/title addresses and asks the model
to read a relevant node before explaining it. It encourages direct factual
answers, transparent sources and reliability when asked, without invented
experiences or verification. Inference remains allowed, without automatically
turning it into read facts or reinterpreting memories as legends.

No changes to Core, configuration, model, generation, physical carousel or
personal database. No semantic filters or new dependencies. Rules remain in
the bible, not hardcoded semantic decisions. `docs/bible.en.md` is documentation,
not a second prompt. The user's previous bible was preserved at
`D:\Test\Luca\bible-before-revision-20261022.md`.

## Evidence

Full suite: **210 tests passed**, with native LM Studio tokenization and real
CUDA enabled. Live test with `google/gemma-4-e2b`:

```powershell
python -m luca_memory.reasoning_check --scenario integration
```

**8/8 checks** in a sequence alternating donkey diet, flight, natural rain,
unusual rain and a causal connection. Luca uses general knowledge after
reading, opens node 3 for flight and node 2 for unusual rain rather than
explaining its title alone. The test uses disposable synthetic storage and
closes resources. Answers, reads, traces, counts and the bible snapshot are in:

`D:\Test\Luca\reasoning-live-20261022-003635.json`

SHA-256 of text normalized by the bible reader:
`979c4b83dfd710be5853849b0872da3d1d251458df209512d594ee79cc7c0ecc`.

An additional in-memory test uses an invented technical manual: Luca reads
node 100, answers that R17 activates a mode after code BRINA-624, corrects
the hypothesis that R18 activates it (it deactivates it), then answers a
general diet question absent from the manual. Three successful exchanges;
evidence is in session output, not a separate report. The session was closed.

## Limits and usage

The eight checks test lexical evidence and actual reads, not complete semantics
or style. One answer still starts with “According to the available information”;
an explanation adds “less dense”, absent from the node. The final causal
connection matches the seed, not external reality verification of experimental
assertions.

Earlier drafts scored 5/8 and 7/8: a longer bible was not enough. The final
version mainly clarifies the read/answer decision. The previous `weather`
scenario, formerly 7/8 due to further exploration, was not rerun; that
limitation is not declared resolved.

The bible reloads on every request: this change needs no restart of an already
updated app. Start a **new conversation** to avoid carrying previous restrictive
answers forward. Tests did not modify personal memory. Naturalness and
faithfulness still need joint evaluation on longer dialogues and real documents.
