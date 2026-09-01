# Replaceable language adapters

Luca Core must not depend on a particular language model. The first implementation uses deterministic Italian rules; a local micro LLM is an optional replacement for that one component, not a new cognitive core.

```text
user text
   |
   v
LanguageAdapter  ->  LanguageIntent  ->  Luca Core / MemoryEditor
                                                   |
                                                   v
                                             EvidenceBundle
```

## The stable contract

An adapter may interpret natural language into a `LanguageIntent`:

- `greet`, `ask`, `describe`, `remember`, or `unknown`;
- a normalized subject, predicate, and one or more objects for a `remember` intent;
- a confidence value and an ambiguity note when appropriate.

For example, an adapter can turn “Luca, ricorda che il sole produce luce e calore” into:

```text
kind: remember
subject: sole
predicate: produce
objects: [luce, calore]
```

Only `MemoryEditor.consolidate()` can turn that proposal into durable cells, assertion cells, edges, and append-only events. The adapter cannot write SQLite directly, choose internal cell identifiers, or alter an existing fact.

Core answers are grounded in an `EvidenceBundle`: the rendered text, the graph trace, and the assertion identifiers used. A future adapter may make that text more conversational, but must preserve the answer's meaning and must never introduce a fact absent from the bundle.

## Consequences for the LM Studio integration

The future `MicroLLMAdapter` will call a model served by LM Studio only to:

1. classify the utterance into the stable intent schema;
2. extract the proposed lesson in simple normalized terms;
3. optionally render a Core-provided answer in Italian.

It will not own long-term knowledge, decide persistence, run the graph traversal, or synthesize unsupported information. If the model is removed, changed, or unavailable, `RuleAdapter` remains a functional fallback and the existing Luca database remains valid.

## Initial safety policy

- An ambiguous lesson produces a proposal that can require confirmation; it is not silently stored.
- A low-confidence extraction is reported as uncertain rather than becoming memory.
- Every stored assertion retains origin and event trace.
- Evaluation tests must exercise the same intent contract for the rules adapter and each candidate micro LLM.

The present code implements the input contract and tests replacement with a small stand-in adapter. Connecting LM Studio is deliberately the next integration step, once a model and its local endpoint are chosen.
