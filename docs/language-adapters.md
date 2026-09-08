# Language adapters and free conversation

Luca Core must not depend on a particular language model. Rule-based interpretation remains a deterministic fallback, while the LLM can now converse freely and receive retrieved memory as context.

```text
user text → memory retrieval → LLM conversation → natural response
     └──────────────────────→ intent extraction → Core validation → memory
```

## The stable contract

An adapter may interpret natural language into a `LanguageIntent` for the memory path:

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

The conversational path is intentionally different. `LMStudioAdapter.respond()` receives a bounded memory context and dialogue history, then returns a natural response without a JSON intent schema. The Core still owns retrieval, persistence, and trace generation.

## LM Studio integration

`LMStudioAdapter` uses a model served by LM Studio for two separate operations:

1. generate a free natural response using retrieved memory and conversation history;
2. extract durable user-provided knowledge into a structured proposal.

The LLM does not own long-term knowledge, write SQLite, select internal cell identifiers, or run graph traversal. The Core validates and consolidates every memory proposal. If the model is removed, changed, or unavailable, `RuleAdapter` remains a functional fallback and the existing Luca database remains valid.

## Initial safety policy

- An ambiguous lesson produces a proposal that can require confirmation; it is not silently stored.
- A low-confidence extraction is reported as uncertain rather than becoming memory.
- Every stored assertion retains origin and event trace.
- Evaluation tests must exercise the same intent contract for the rules adapter and each candidate micro LLM.

The present code implements the input contract and tests replacement with a small stand-in adapter. Connecting LM Studio is deliberately the next integration step, once a model and its local endpoint are chosen.
