# LUCA: project vision

## Purpose

LUCA is an experiment in a different kind of artificial intelligence: a persistent cognitive architecture that learns by changing its explicit memory, rather than primarily by changing a large, opaque set of model weights.

LUCA is not intended to compete with frontier LLMs at broad language generation or pre-trained world knowledge. It is intended to demonstrate a complementary capability:

> A system can receive a limited base of knowledge, be instructed in simple language, retain what it learns, correct it, and use it later through a traceable memory structure.

The working expansion of the name is **Logical, Updatable, Cell-based, Addressable intelligence**. It remains a working description, not a claim that has already been proven.

## Core thesis

In an LLM with retrieval augmentation, external information is normally recovered and supplied to a model as context for a response. The model's underlying structure does not necessarily change.

In LUCA, important new information becomes part of the system itself:

```text
simple instruction
    → cells, assertions, and addressed paths
    → persistent internal memory changes
    → future thoughts start from the changed structure
```

Cells hold content, state, evidence, and history. Edges are semantic-free, directed addresses. The graph is not an attachment to the cognitive system; it is its native memory.

## Memory is the model

LUCA is designed from the storage hierarchy outward:

```text
SSD   complete persistent brain
RAM   active context and topological neighbourhood
VRAM  narrow working set for a particular thought
```

The brain is never assumed to fit in RAM or VRAM. A thought activates and moves through a bounded region of a much larger persistent memory. GPU computation is an accelerator for selected working sets, never the owner of the brain.

This design must be present in the algorithms, data layout, budgets, cache policy, and consolidation process from the beginning. It is not an optimisation to bolt onto a monolithic model later.

## Role of LLMs, RAG, and external tools

LUCA may use language models, retrieval systems, libraries, search, calculators, sensors, or other modules as support. They are useful for language, discovery, and evidence gathering.

They do not replace LUCA's memory. The durable path is explicit:

```text
external information or user instruction
    → proposed lesson / evidence
    → validation and provenance
    → LUCA's internal memory
```

The instruction "LUCA, remember …" is a request to create durable, versioned internal knowledge. A retrieval result remains external evidence until it passes through this path.

## What the first demonstrator must prove

The first demonstrator is deliberately small. It should hold a light conversation in a bounded domain, not imitate a general-purpose chatbot.

It must show all of the following:

1. A person can teach LUCA a new fact in simple language.
2. LUCA converts it into inspectable cells, assertions, and addresses.
3. LUCA retrieves it in later turns and after restart.
4. LUCA maintains topic context across a short conversation.
5. LUCA states when it does not know or cannot verify an answer.
6. LUCA can receive a correction without silently deleting history.
7. Every answer and memory change has an inspectable trace and provenance.

This is the proof of concept. It will be evaluated on controlled, partly invented micro-worlds so that pre-trained LLM knowledge cannot masquerade as LUCA's learning.

## What success does not mean

Success does not mean that LUCA has matched an LLM's language fluency, encyclopaedic knowledge, or general reasoning ability. It means that the architecture has proved a different and useful form of growth:

```text
limited starting knowledge
+ incremental instruction
+ immediate persistence
+ correction and provenance
+ traceable retrieval and local reasoning
= a growing cognitive memory
```

## Long-term direction

If the core is validated, a larger LUCA can live in a data centre:

```text
shared NVMe/NAS storage   complete versioned memory
compute nodes             RAM-resident active regions
multi-GPU servers         parallel thought branches
consolidation service     safe merge into one evolving history
```

The system could serve personal, organisational, domain-specific, and explicitly shared memories without merging private knowledge by default. LLMs could provide the conversational and tool-using interface; LUCA would provide continuity, explicit learning, and durable cognitive state.

## Scientific discipline

Every claim must be testable. We will publish or retain: curriculum versions, sources, inputs, expected outcomes, execution traces, resource budgets, benchmark results, failures, and revisions. When a hypothesis fails, we change the design rather than hide the result behind a larger opaque model.
