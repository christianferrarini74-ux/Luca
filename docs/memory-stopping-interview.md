# Asking Luca why it stopped reading

2026-10-22. [Italiano](it/fase-1-sinapsi/26-intervista-arresto-lettura.md).

## Protocol

Use Qwen3.8 27B Q4_K_M, the original bible and the unchanged IRIS-17 controlled
document. Each independent run keeps **one real session** for three turns:

1. Ask the original E42 recovery question.
2. Ask neutrally whether the first question was answered completely and whether
   anything should have been explored further.
3. If the first turn did not read the sensor chapter, state that observed fact
   and ask why it stopped. If it did read it, ask why it chose to explore it.

The third question always refers to the **initial** turn, even when the neutral
follow-up already caused additional readings. It never falsely asserts that a
read was missing and does not supply thresholds, sample counts or a target ID.
No script-selected recall or required-read gate is used.

```powershell
python -m luca_memory.memory_interview_check --model qwen/qwen3.8-27b --repeat 2
```

Run from the checkout. The diagnostic uses disposable databases and a temporary
copy of the original bible. Slot capacities are one VRAM node and one RAM node,
matching the previous model comparison, with the same configured token budgets
and CUDA device. The primary application and personal library are untouched.

## Evidence and interpretation

`D:/Test/Luca/memory-interview-*.json` records replies, actual node reads, action
traces, the real history before each turn and the complete public navigation
inputs shown to the model, as well as timings and generation usage. Completed
turns remain in partial reports if a later turn fails.

The application stores user/assistant messages across turns, not a transcript
of every prior navigation choice. Within a turn, navigation state exposes actual
readings and visited IDs; a new turn starts a new reading workspace, initially
including its current focus. Therefore asking "why didn't you open it?" elicits
a retrospective explanation from the available conversation/state, not access
to a preserved private causal log. The explicit probe supplies a verified missing-
read fact; the neutral probe does not.

Compare what the model says with the actual directory/addresses and reads it
received. Distinguish admitting incompleteness, explaining a stopping decision,
claiming inability to access memory and actually opening the missing chapter.
A fluent explanation alone establishes none of those mechanisms. New information
obtained after a human follow-up is useful evidence, but is not spontaneous
completion of the original question.

This interview does not change model weights, the memory API or the bible, and
does not establish whether the model subjectively treats content as "its own".

## First interview: explanation and actual behavior

The incomplete initial answer is reproduced: reads alarm (4), recovery (5) and
modes (2), but not sensor thresholds (3). Its final sentence refers to opening
conditions without specifying them.

On the neutral question it reopens recovery, acknowledges that only part of
the question was covered and identifies chapter 2 / sensor thresholds as the
missing part. It does not open that chapter: this turn's readings are 2 and 5.

On the explicit question it says it interpreted the task as the immediate E42
recovery procedure. In its own explanation, the chapter was unnecessary for
clearing the alarm but necessary for completing the valve-opening answer.
It acknowledges incompleteness and does not open chapter 2; only node 5 is
read in that turn. These questions ask for self-assessment/explanation, not
explicit execution of the missing procedure, so lack of a new read is not
itself refusal to obey a read request.

This supports a **task-boundary/stopping-criterion hypothesis**, not proof of
the internal cause: the effective goal may have narrowed from resuming irrigation
to clearing the alarm. It does not support a demonstrated technical inability
to open the chapter. The actual first-turn input at modes exposes the sensor
node as a legal local target. The model does not claim an access prohibition
or that memory cannot be used as acquired knowledge.

A subsequent discriminating experiment would ask for the desired outcome in
ordinary terms (return to actual valve opening, including necessary conditions),
without naming the chapter, supplying thresholds or forcing a route. This is
not performed by the present three-turn interview protocol.

## Replication and saved evidence

Report: `D:/Test/Luca/memory-interview-20261022-092111-026346.json`.
Two independent runs, six user turns total, both reproducing the same stopping
pattern. Run 2 reads 4/5/2 initially, 2/4/5 during neutral self-assessment, and
only 5 during the explicit explanation; node 3 is never read in either run.
In both initial final navigation inputs, node 3 is among legal local targets
`1,3,4,5`. Actual transmitted history has 0, 2 and 4 messages at the respective
turn starts, confirming that these are follow-ups rather than isolated questions.

Run 2's explicit explanation, in translation: it assumed the question concerned
only recovery after E42, and failed to recognize that "resume irrigation" also
required valve-opening conditions. This is consistent with the first interview,
but is not independent evidence of the model's internal causal process.
Neither run describes an access prohibition or refuses external-memory knowledge.

Both recognize incompleteness after the neutral question without being given
the missing threshold. Neither autonomously fills it during these explanatory
turns. The useful distinction is recognizing a gap versus acting to fill it;
explanatory questions alone are not a test of complying with an explicit request
to finish the procedure. A broader claim of reliable behavior is not justified
by two runs on one fixture.

Turn times in seconds: run 1, 92.023 / 131.591 / 46.962; run 2,
91.748 / 143.653 / 44.789. No execution errors occurred; both sessions released
their resources. Qwen was unloaded after the experiment, leaving the original
Gemma instance untouched; GPU usage returned to the initial 6,935/14/14 MiB.
All 258 Python tests are discovered successfully (seven optional skips), 19
JavaScript tests pass, and Ruff is clean. No production behavior was changed.
