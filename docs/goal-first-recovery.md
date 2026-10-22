# Recovery with the desired outcome stated first

2026-10-22. [Italiano](it/fase-1-sinapsi/27-ripristino-obiettivo-esplicito.md).

## Controlled change

The new question starts with the desired outcome: IRIS-17 must actually irrigate,
the valve must open and water must flow. It then describes E42, the recovered
sensor signal and failure to resume, and asks for the complete procedure and
all necessary conditions up to actual opening.

The exact Italian question is in `tests/fixtures/goal_framing_questions.json`.
It supplies no chapter number, target ID, threshold, sample count or command
name. The separate rubric is used only after generation, never as model input.

Two fresh conversations use Qwen3.8 27B Q4_K_M, the original bible, the original
IRIS-17 seed, 70,000-token prompt budget, one VRAM slot and one RAM slot, as in
the preceding interviews. No follow-up correction, required-read policy or
changed node visibility is used. Public navigation inputs are recorded to
distinguish candidate visibility, legal local addresses and actual readings.
No prior interview, apology or self-explanation is supplied: each run starts
with empty conversation history.

```powershell
python -m luca_memory.autonomy_check --profile current --model qwen/qwen3.8-27b --questions tests/fixtures/goal_framing_questions.json --capture-inputs --vram-capacity 1 --ram-capacity 1 --repeat 2
```

The diagnostic runner now accepts held-out question files, model/slot overrides
and input capture; all overrides apply only to its in-memory configuration copy.
Existing defaults remain unchanged. Personal memory and the application config
are not touched. This is not a replacement of the old test: its question and
historical evidence remain intact.

## Observed result

Report: `D:/Test/Luca/autonomy-check-20261022-134703-161319.json`.
Both fresh runs answered with the complete procedure, reading nodes
`5 → 2 → 3 → 4`: recovery, modes, sensor/thresholds, E42 alarm. The first
opening was global; the other three were local choices made by the model.
All ten recorded navigation inputs have empty conversation history.

Both answers include four consecutive valid samples followed by CONFERMA,
remaining in OSSERVA until AVVIA, no active alarms, and three consecutive
readings strictly below 28% for opening. They also explain that a reading
at or above 28% resets the opening count and at or above 41% closes the valve.
This is coverage of the fictional manual, not a real-hardware test.

Total times were 183.286 and 218.459 seconds, five model calls each. CUDA
payload storage was real on device 1, with four uploads each and RAM/SSD
demotions under the one-slot limits. After the experiment, only the test
Qwen model was unloaded; Gemma remained loaded. GPU memory returned to
6,935/14/14 MiB, with zero utilization.

The old initial candidate order was `[4,2,5,6,1,3,7]`; the new one is
`[1,4,3,5,2,6,7]`. The candidate set is unchanged, but ranking is not.
More importantly, at modes node 2, the actual content and directory match
the previous runs: incoming 1/5, outgoing 3/4, legal local targets
`[1,3,4,5]`. The previously skipped sensor node was already available.
This time the model follows that existing local connection.

The outcome supports the narrower-task-interpretation hypothesis and shows
that current visibility suffices in these two runs. There is no evidence here
requiring a visibility change. It does not establish the private cause of the
old stopping decision or general reliability on ambiguous requests.

Verification: 259 Python tests (seven optional checks skipped), 19 JavaScript
tests and Ruff passed. Production navigation, bible and config are unchanged.

## Interpretation limits

Compare these runs with initial turns in
`D:/Test/Luca/memory-interview-20261022-092111-026346.json`, which repeatedly
stopped at recovery/modes without reading thresholds. These are historical
matched-configuration controls, not interleaved randomized trials.

Changing question wording naturally can change metadata-search ranking. Record
and compare entry order as well as the set of candidates and local directories;
do not claim that every visible input is identical. In particular, check whether
the model follows the previously available local address from modes to sensor,
rather than merely receiving the sensor node as a newly injected instruction.

A successful response would be consistent with the model's task-interpretation
explanation, not proof of its private cause or "honesty". It can demonstrate
that the existing visibility suffices for this task without proving that the
same interface will be sufficiently salient on larger graphs or other questions.
