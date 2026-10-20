# Phase 1.11 — Navigable, reorganizable synaptic memory

Date: 2026-10-20

[Italiano](it/fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md)

Status: design synthesis of the discussion with Christian, intended as the basis
for the next roadmap. This document does not describe implemented features and
does not, by itself, authorize changes to the personal graph.

## 1. Goal and boundaries

Luca should retain complete, connected and progressively growing knowledge while
making it usable by an LLM with finite resources and context. Growing the library
must not require placing the whole library in the prompt or necessarily replacing
its contents with summaries.

Luca is an autonomous system. Its architecture must not inherit constraints from
Cesare or another application. Any future integration is a separate assessment
and does not drive the decisions in this document.

The brain and its “sleep” are functional metaphors for a memory-maintenance phase,
not a demonstrated biological reproduction.

## 2. Starting with a book and its table of contents

The original PDF remains a persistent, identifiable source. The author's structure
is the first organizing resource, before arbitrary segmentation or automatically
generated associations.

A book-entry node contains title, subject, provenance and table of contents.
Each entry addresses a chapter or topic node; chapters may contain subindexes
addressing sections and subsections. Order, titles and page references belong
to node/index data. Edges remain directed addresses without semantic payloads.

The hierarchy does not confine memory to a closed tree: nodes can connect to
knowledge from other books and to alternative thematic entry points. A shared
word is not necessarily a shared concept; matching titles must not automatically
merge different knowledge.

Following an address to a known entry does not require scanning a whole book.
Interpreting a free-form question and finding the right entry is a separate,
fallible selection problem.

## 3. Three distinct planes

| Plane | Meaning | What it does not imply |
| --- | --- | --- |
| Persistent knowledge | Sources, complete contents, nodes and connections on disk/SSD. | Everything need not be resident or read. |
| Physical residency | Payloads actually stored in disk/RAM/VRAM tiers. | A VRAM-resident node is not automatically in the prompt. |
| LLM exposure | Contents and navigation alternatives examined in the current context. | The model does not automatically know unexamined information. |

The carousel governs residency and replacement. Navigation governs what to open.
Prompt construction governs how much to expose in one computation. These are
coordinated responsibilities, not interchangeable ones.

A book can remain almost entirely on SSD while its index and addresses make its
contents reachable. Loading a chapter still incurs actual reading and transfer
costs related to payload size.

## 4. Who chooses the path

The intended role of the LLM is to select the next node from the question, focus
and available alternatives. The Core validates addresses and operations, performs
recall and enforces resource policies; it must not substitute its own semantic
preference for the model's navigation decision.

For reorganization, the LLM may propose titles, boundaries and groups. The Core
checks structural integrity and application. Those checks alone do not prove
that a group is semantically useful; initial human review is also needed.

Navigation autonomy does not authorize arbitrary execution, access to unrelated
files or unvalidated direct modification of memory.

## 5. Complete adjacency and its scaling difficulty

A focused node B must make every active B:* and *:B edge available. The subset
that fits neighboring-node preload is insufficient. Carousel capacity must not
amputate the focus's directory of connections.

There is an information constraint: arbitrarily many addresses and descriptions
cannot all fit in a finite context. Pagination is one possible approach, but it
is not the primary direction chosen in this discussion. The proposal here is to
organize memory so each local choice stays small and understandable enough to
be exposed in full.

Complete reachability and exhaustive reading remain different: access to every
node does not guarantee that the model chooses the right path or examines all
the knowledge.

## 6. Soft connection limits

Christian's working example is a threshold of 100 incident connections, incoming
and outgoing combined. The 101st connection flags the node for local maintenance
that brings it back to, for example, no more than 90.

These are experimental parameters, not approved production constants. The gap
between intervention threshold and target avoids repeated reorganization after
every addition. The threshold is soft: acquisition may temporarily exceed it
while the node awaits a maintenance window.

A candidate definition consistent with current counters is in-degree plus
out-degree. A self-loop would therefore consume two incidences; this convention
must be explicitly confirmed rather than left implicit.

Grouping twelve direct connections behind one intermediary reduces degree 101
to 90 in the simple example. The new parent-to-group connection counts against
the parent's budget; the group's parent connection counts against its own.
Explicit reverse or cross-connections consume additional capacity. Counting
only new outgoing branches would be incorrect.

## 7. Grouping without falsifying relationships

Grouping inserts navigation nodes with meaningful titles and short descriptions.
Direct connections become paths through a group: knowledge remains reachable,
but distances can increase. “Thermodynamics” may help navigation; “Group 7” alone
does not.

This resolves a crucial ambiguity: retaining every old edge as an active direct
connection cannot simultaneously reduce the focus's degree. Previous connections
must be redirected, with provenance and a separate mapping retained for audit,
historical references and rollback.

Navigation nodes must be distinguishable from knowledge-asserting nodes. A path
through a group is not a new direct relationship between every pair of members.
Grouping incoming and outgoing connections must preserve direction and original
route membership without introducing unsupported semantic combinations or
shortcuts.

Intermediaries also obey thresholds. Maintenance must neither move the hub down
one level nor create excessively deep chains. Local breadth, depth and clarity
of choices must be evaluated together, not just the final edge count.

## 8. Limiting node information as well

A node with few edges may still contain a huge chapter. Content needs a separate
threshold and a lower target that leaves room for growth, just as edges do.

Size can be measured as serialized payload bytes and against the exposure budget;
neither metric alone measures semantic complexity. Values and a combined policy
have not been chosen. Physical limits remain hard: soft organizational thresholds
cannot authorize allocations beyond available VRAM. An unallocatable payload
must remain persistent pending segmentation or an explicit decision, never be
reported as loaded when it is not.

When content is excessive, the node keeps its logical identity and becomes an
entry with a subindex; complete portions move into child nodes. The original and
its version remain on disk. The active parent payload need not retain a duplicate
of the entire chapter.

Splits should follow intelligible units and preserve definitions, conditions,
examples and necessary references. Character counts may trigger maintenance but
cannot establish the correct semantic boundary by themselves.

## 9. Distill the map, not the knowledge away

The proposed distillation is organizational: identify subtopics and produce titles,
short descriptions and subindexes that help navigation. It is not a summary left
behind in place of the source.

Original content is distributed completely among child nodes. Every portion
retains source, order and position in the reference text. Persistent references
do not replace actual physical content on loading: the required node payload
must really be materialized.

Extracted text should have verifiable complete coverage and, where possible,
ordered reconstruction. Necessary overlaps must be explicit and must not hide
gaps. Correct PDF extraction, particularly for scans, tables, images and equations,
is a preceding, separate verification. Perfectly retaining a bad extraction
does not preserve the full meaning of a book.

Generated descriptions and source text remain distinguishable. The map can be
improved without rewriting what the author actually stated.

## 10. Contents and connections share a context budget

Limits cannot stop at “100 edges” and a payload-size threshold. One computation
must accommodate instructions, question, task state, useful history, exposed
contents, the focus's complete directory and output reserve.

Titles and descriptions have costs: one hundred long descriptors may exceed
context even for a short node. Exposure therefore needs an overall feasibility
check. The edge limit is a structural ceiling, not a target to reach everywhere.

Temporary graph overflow does not authorize silent prompt truncation. If a focus
cannot be fully exposed under the selected contract, it must first be reorganized
or its opening explicitly deferred. The exact operational policy remains a
roadmap decision. Unbounded overflow, immediate selection and full visibility
cannot all be guaranteed in a finite prompt.

The two transformations interact: splitting text creates new edges; grouping
edges creates new indexes and descriptive content. Reorganization must therefore
validate connections, content and context together, not run two independent
procedures that repeatedly push each other over their thresholds.

## 11. “Sleep”: local maintenance, not a global rebuild

Maintenance collects over-threshold nodes and prepares small, targeted changes.
It may run on command, in an agreed phase or during actual inactivity. Automatic
scheduling is not yet an approved implementation decision.

The logical cycle is detection; deduplicated queueing; proposed grouping or split;
validation of contents and routes; publication; and rechecking affected nodes.

Work and resource consumption must be bounded, interruptible and resumable,
without repeated oscillation. If data changes after planning, the proposal must
be revalidated. Maintenance starvation must not cause hidden unbounded growth:
pressure diagnostics and an explicit admission policy are needed.

Publication must expose one coherent graph version. A SQLite transaction does
not make GPU allocations atomic: in-flight readers, resident payloads, caches
and task references require coordinated versioning/invalidation. Errors and
interruptions must leave the previous organization recoverable, not half of
an applied transformation.

The organizer itself has finite context: it must not require reading everything
in one prompt to solve the very size problem under consideration. It can first
use source indexes and boundaries, then inspect successive portions with explicit
references. If no reliable split is found, it must leave a pending proposal or
request review rather than force a boundary solely to meet a numeric threshold.

## 12. Acceptance invariants

- No silent loss of content, sources or connections.
- All active focus alternatives are available, not merely a top-K.
- Reorganization changes paths without asserting new facts between group members.
- Existing identities/references remain resolvable or explicitly migrated.
- New nodes also meet budgets; depth does not grow without control.
- VRAM residency is real and distinct from LLM exposure.
- No partial reorganization is exposed to an ongoing conversation.
- The cockpit displays decisions, state and maintenance; it contains no Core logic.
- Frameworks are not adopted for convenience alone; dependencies require justification.

## 13. Existing implementation versus proposed work

Current code has SQLite persistence, directed addresses, a physical CUDA carousel,
payload/context budgets, diagnostics, a recall planner and seed checks. The prior
milestone records 105 passing tests including real CUDA; this report is not a
fresh execution of those tests.

It does not implement this design yet. Recall still limits edge retrieval to
`max(32, vram_capacity * 4)` per direction and neighboring-node preload to active
tier capacity. Planning remains hybrid, often using rules rather than autonomous
LLM navigation across the complete alternatives.

Missing components include index-led book ingestion, a complete-directory
contract, reorganization thresholds, managed navigation nodes, conservative
content splitting, a maintenance queue and versioned transformation publication.
Using a real PDF also requires selecting and validating extraction without
automatically installing dependencies.

## 14. Decisions before an executable roadmap

1. Initial edge/content thresholds, margins and counting convention.
2. Directory descriptor format and budget, beyond plain IDs.
3. Representation of navigation nodes and preserved original-route mappings.
4. Handling a focus temporarily over its exposure budget.
5. The operational contract for LLM inspection, opening, backtracking and stopping.
6. Grouping/splitting criteria and initial human review.
7. Maintenance triggers, bounds, approval and version management.
8. A first book/chapter chosen jointly, with verifiable questions and references.

These are design decisions, not an already authorized development sequence. The
next roadmap should turn them into experiments and measurable criteria: coverage,
route correctness, LLM selection, context consumption, depth, latency, maintenance
cost and recovery after failure.

## 15. Conclusion

The design addresses scaling through structural reorganization, not a promise
of infinite context: complete persistent knowledge, bounded information units
and local choices, LLM-led navigation and maintenance that redistributes excess
without losing the source.

The book supplies an initial organization. Cross-source connections extend it.
The carousel brings useful knowledge nearby. “Sleep” keeps the network navigable.
Distillation builds signposts rather than replacing knowledge.

This is a coherent architectural hypothesis to test, not proof that every
reorganization improves recall. The decisive test is preserving contents and
correct paths as the library grows and questions change.

## References from the preceding research

- [PageIndex tree navigation](https://docs.pageindex.ai/tutorials/tree-search/llm): useful document structure; its basic example exposes the tree in the prompt.
- [MemGPT](https://shishirpatil.github.io/publications/memgpt-2023.pdf): external memory versus context, pagination and limits of actual exploration.
- [GraphWalk](https://arxiv.org/html/2604.01610v1): tool-based exploration, not proof of huge-hub handling when all neighbors are returned.
- [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview): partial reads and external result management as adjacent mechanisms.

These are partial references, not adopted dependencies or evidence of equivalence
with Luca.
