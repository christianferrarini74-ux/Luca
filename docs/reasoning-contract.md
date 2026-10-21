# One bible, free reasoning and multi-node readings

[Italiano](it/fase-1-sinapsi/16-ragionamento-libero.md)

2026-10-21. Supersedes the earlier prompt policies and output sanitization,
without rewriting historical experiment reports.

## Instruction ownership

`runtime.bible: bible.md` is the sole system instruction source for navigation,
conversation, legacy interpretation/recall and memory maintenance. Missing or
empty files fail explicitly; neither policy files nor packaged copies are
silently substituted. The file is read for every model call, so an edit takes
effect without restarting the model. Configuration changes still require a
Luca restart. [English translation](bible.en.md) is documentation only.

All runtime information is a JSON user-message envelope with `operation`,
`question` and relevant data (`state`, `memory`, `task`, `constraints`,
`user_identity`). No behavioral prose is appended to the system message.
Schemas remain executable protocol definitions, not hidden personality prompts.
Feedback records technical errors/status instead of instructions about answers.

The old experimental/grounded prompt files remain historical artifacts but are
not loaded. The legacy `memory_policy` field now describes memory scope in data;
it does not select another bible. `runtime.user_identity` replaces the embedded
assumption that the user is Christian.

The bible permits inference, explanation, creative hypotheses and general
knowledge alongside acquired memories. It distinguishes observations from
inference when relevant and permits correcting previous answers. It contains
no vocabulary specific to cheese, donkeys or other regression fixtures.

## No semantic output censorship

Removed sentence/line deletion based on phrases such as “local memory”, “direct
links”, self-introductions or stage directions. Returned answer text is not
rewritten to hide how the model expressed itself. Empty or malformed provider
results still produce errors, not fabricated answers. Existing regression tests
that required censorship now verify an unchanged response and instruction/data
separation; unrelated topology and isolation assertions are retained.

## Reasoning and generation options

The connector no longer injects `reasoning_effort: none` or
`chat_template_kwargs.enable_thinking: false`. With `generation: {}` the
provider's default applies; this does not certify that any particular model
actually used internal reasoning. Provider-specific options can be supplied
under the configured agent:

```yaml
generation:
  reasoning_effort: high
  chat_template_kwargs:
    enable_thinking: true
```

Only use options supported by that provider/model. `generation` cannot override
addresses, messages, schema, streaming, temperature or the controlled output
budget. Temperature remains explicitly configured at `0.0`; improving memory
use is not equated with increasing randomness.

The 70,000-token total window remains. Navigation and maintenance reserve 8,192
output tokens each in the project config; conversation reserves 4,096. Legacy
interpretation and recall reserves are separately configured at 1,024, replacing
the embedded 160/80 caps. The silent 2,000-character truncation of recall
questions is removed. `synaptic.search_query_characters` explicitly controls
generated search-query/API limits; it does not truncate the user's question.
Output reserves include whatever generation work the provider accounts there;
model behavior and latency must be measured, not assumed.

## Read, compare, answer

The navigator maintains a per-turn `ReadingWorkspace` of actually read content
and each node's complete directory. Moving the focus no longer discards all
previous readings from that turn. The workspace is bounded by `memory_limit`;
older readings are evicted when necessary and listed in `omitted_ids`. Contents
may be excerpted under `per_node_limit`, but directories are never silently cut.
This workspace is ephemeral prompt material in CPU memory, not a fourth durable
storage tier or a new always-resident copy of the library. Physical carousel
payloads and transfers remain unchanged.

Every subsequent navigation decision sees the available readings. An `answer`
action can directly contain the final `response`, generated with those same
readings and directories. No separate renderer loses that work. If an adapter
only returns an action (legacy/test compatibility), the conversation call gets
the complete bounded reading workspace and the same bible.

Each action has its own schema branch: opening requires the correct source
and an ID from that source; answering requires a memory-use decision and answer
text. This fixes a live-discovered protocol ambiguity where missing `source`
caused repeated rejected opens. Global candidates remain available after a
local step so the model can compare other global results without an unnecessary
new search. The Core still does not select semantic targets or force all
candidates into the answer.

When an address is available both globally and in the current fast directory,
the schema offers its local route once rather than duplicating the address.
This preserves synaptic routing without deciding which knowledge to select.
Usage telemetry also records exposure of actual workspace readings that have
already left VRAM; it does not promote their physical payloads to fake residency.

Grouping uses directional ID-to-label assignments rather than independently
generated membership lists. Every supplied address can have only one label per
direction; the Core converts equal labels into groups without choosing their
meaning. Unknown addresses are rejected and degree/size constraints are still
validated before any write. This addresses duplicate-membership proposals
observed in the first live run without adding behavioral text to the code.

The step budget, valid IDs, revisions, complete directories, token limits and
atomic maintenance remain integrity/resource controls. Reaching the step budget
is exposed as `step_limit`, not successful completion. The UI shows actual read
IDs separately from VRAM residency. Reset clears readings and pending answers.

## Verification

Controlled tests cover all call types using exactly the bible as system content,
unchanged output, custom/missing/empty bibles, configurable generation options,
action-specific schemas, multi-node reads with one physical payload slot,
workspace eviction and existing memory integrity checks.

Reproducible live checks use isolated databases and release their CUDA resources:

```powershell
$env:LUCA_TEST_CUDA = '1'
$env:LUCA_TEST_LMSTUDIO = '1'
python -m unittest discover -s tests
python -m luca_memory.reasoning_check
python -m luca_memory.live_memory_check
```

The targeted real-model check opened node 2 and correctly recalled the mountain
rain phenomenon and its explicit connection to flying donkeys. Both responses
were direct navigation answers. This is evidence for that case, not a claim
that hallucinations or all navigation defects are solved. Full-run outcomes
are recorded below. The user's running application and personal
database are not restarted or modified by these checks.

### Results and remaining limits

206 tests passed with both `LUCA_TEST_CUDA=1` and `LUCA_TEST_LMSTUDIO=1`.
The weather dialogue replay is recorded in
`D:/Test/Luca/reasoning-live-20261021-191230.json`: **7/8 assessed turns passed**;
greeting and personal-preference turns were recorded for review, not scored.
It retrieved the remembered mountain phenomenon, preserved its causal link
to flying donkeys, and read nodes 2 and 4 together for the nest question.
The final “is there more?” turn did not explore node 5. A focused retry with
the subsequent general exploration guidance still stopped early. This is an
open model-planning limitation, not declared fixed by freer reasoning.

The initial wider run (`phase11-live-20261021-191125.json`) returned 4/8:
a timeout, a global route where a local route was expected, and duplicate
group proposals. After protocol corrections, the isolated grouping check
produced 17 Astronomy incoming members, 17 Botany outgoing members and 17
Geology outgoing members, reducing degree **51 → 3**, restoring **51**, and
successfully repeating grouping during idle maintenance.

The next full run (`phase11-live-20261021-192755.json`) returned 7/8: the
remaining checker failure required the cursor to stay on the root after
reading the index, despite the index remaining available in the workspace
while the cursor moved to a family part. The checker now requires actual root
reading, canonical family identity and correct section names, not an artificial
root-only cursor position. Dedicated tests reject an unread root or unrelated
cursor.

Final serial full run: `D:/Test/Luca/phase11-live-20261021-193004.json`, **8/8**.
Global entry, family parts, local external route, natural recall, resident
updates, general knowledge, manual grouping/restore and idle grouping all
passed; resources were released. This final run answered the index question
while still on the root, so it also satisfied the original cursor expectation.
It does not override the separate failed exploration turn in the weather replay.

Early concurrent generation checks showed large delays and one 180-second
timeout; later serial navigation calls were approximately 3–6 seconds. These
are observations, not a controlled performance benchmark. Default reasoning
can cost time and output tokens; leaving it unconstrained by hidden flags does
not guarantee speed or factual accuracy.

Close the currently running application with **Esci**, then run
`python run_luca.py` to activate the new adapter and configuration. Do not
start another application instance over the existing one. The LM Studio model
can remain loaded. No new Python dependencies were installed.
