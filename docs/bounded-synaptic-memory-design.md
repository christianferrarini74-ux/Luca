# Phase 1.11 — Navigable, reorganizable synaptic memory

Date: 2026-10-20

[Italiano](it/fase-1-sinapsi/11-memoria-sinaptica-riorganizzabile.md)

Status: design synthesis of the discussion with Christian, intended as the basis
for the next roadmap. This document does not describe implemented features and
does not, by itself, authorize changes to the personal graph.

Addendum dated 2026-10-20: measure information in words, or exact tokens when
counting is straightforward; retain the original node's complete directory
while reading any of its fragments (§8 and §10).

Christian's subsequent clarification: the next phase concerns only synaptic
navigation and edge management, assuming already suitable node contents.
Content distillation/splitting (§8–9) is a separate, deferred system. The upper
edge limit is 50 and the lower target 45, both configuration parameters; visible
directory entries contain only ID and title. Section 14 records the updated decisions.

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

For edge reorganization, the LLM may propose titles and groups. The Core
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

Christian selected an initial limit of 50 incident connections, incoming plus
outgoing, and a maintenance target of 45. Both belong in the configuration file,
not hard-coded constants. This replaces the earlier 100/90 hypothesis. The gap
between intervention and target avoids reorganization after every addition.
The threshold is soft: acquisition may temporarily exceed it
while the node awaits a maintenance window.

Automatic maintenance affects only nodes above 50, while the LLM is not in use.
Manual maintenance requires confirmation and operates on selected nodes down to
the lower target even if the upper limit has not been exceeded; nodes already
within target need no compression. Automatic jobs must recheck eligibility at
execution time.

Exact configuration key names are implementation details. Validation will require
positive integers and a target below the upper limit. Inert keys are not added
now to config.yaml while the runtime does not implement this feature yet.

A candidate definition consistent with current counters is in-degree plus
out-degree. A self-loop would therefore consume two incidences; this convention
must be explicitly confirmed rather than left implicit.

Grouping seven direct connections behind one intermediary reduces degree 51
to 45 in the simple example. The new parent-to-group connection counts against
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

Background for a separate phase, not work included in the next navigation
roadmap. That phase assumes nodes already have suitable contents.

A node with few edges may still contain a huge chapter. Content needs a separate
threshold and a lower target that leaves room for growth, just as edges do.

The operational content measure is word count. A simple, reproducible initial
definition counts nonempty whitespace-separated sequences without a linguistic
parser. Prefer tokens if the model's exact tokenizer is already available with
negligible integration and counting cost. Do not add a framework or remote calls
solely to count them.

Words are a practical segmentation trigger, not an exact prompt-size guarantee.
Language, code, equations and tokenization prevent a universally fixed conversion.
Thresholds must be calibrated to the model and content type; final context checks
remain separate. Neither words nor tokens alone measure semantic complexity.

Bytes remain the physical allocation/transfer measure, not the primary measure
of information size. Word/token thresholds have not been chosen. A soft
organizational threshold cannot authorize allocations beyond available VRAM:
an unallocatable payload remains persistent pending segmentation or an explicit
decision, never reported as loaded when it is not.

When content is excessive, the node keeps its logical identity and becomes an
entry with a subindex; complete portions move into child nodes. The original and
its version remain on disk. The active parent payload need not retain a duplicate
of the entire chapter.

Splits should follow intelligible units and preserve definitions, conditions,
examples and necessary references. Word/token counts can trigger maintenance but
cannot establish the correct semantic boundary by themselves.

### Synaptic continuity across a split

If A is split into A1, A2, A3, A4 and A5, opening any part must retain access to
all of A's active incoming and outgoing edges, plus the part's own connections.
Navigation between parts remains available and the current part is identified.
A parent-return link alone is insufficient: the LLM must not leave the detail
to recover the original map. A becomes the knowledge anchor; Ai is the reading focus.

The requirement is complete availability in every fragment, not necessarily
physical edge duplication. The implementation proposal to evaluate is a shared
directory referenced by the split family, combined with local connections. Each
part materializes its complete view on opening, without loading other parts'
contents for that purpose.

Origin and direction stay explicit: an inherited A:B navigation route is not
presented as a new A1:B assertion. The Core must validate choices against the
reading context's effective directory, not just edges physically owned by Ai.
Identical edges appear once while retaining their identity; an entry targeting
the already open part is recognizable as such.

Inheritance follows an explicit split relationship, not arbitrary graph links.
If A1 is split again, its new parts must retain anchor A, family continuity and
all connections of the split levels. Shared-directory updates must
refresh part views coherently without divergent copies. Concrete representation
and versioning remain roadmap decisions.

## 9. Distill the map, not the knowledge away

Content generation/distillation is deferred and distinct from edge grouping
during “sleep” in the current phase.

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

Limits cannot stop at “50 edges” and a word/token threshold. One computation
must accommodate instructions, question, task state, useful history, exposed
contents, the focus's complete directory and output reserve.

The chosen directory format is ID and title, without extra generated descriptions.
Titles still have a cost. Exposure therefore needs an overall feasibility
check. The edge limit is a structural ceiling, not a target to reach everywhere.

For a fragment, the effective directory includes inherited family edges, local
edges and part navigation, without duplicating the same edge. Storing a directory
once saves storage, not the context needed to expose it. Ai's physical degree
alone cannot certify budget compliance: the combined view must also be checked,
including multilevel splits. Count content words and descriptor words separately,
then validate the complete prompt. Arbitrarily hiding inherited connections is
not a valid remedy for exceeding the budget.

Temporary graph overflow does not authorize silent prompt truncation. If a focus
cannot be fully exposed under the selected contract, that condition must be
reported. Immediate reorganization, deferred opening and automatic conversation
compression have not been selected. For now measure the total context rather
than turning this issue into a blocker for navigation. Unbounded overflow,
immediate selection and full visibility
cannot all be guaranteed in a finite prompt.

In the overall system, future text splitting may create new edges, while edge
grouping creates new indexes. This phase assumes contents are already suitable:
check connections and exposure cost without introducing text segmentation now.

## 11. “Sleep”: local maintenance, not a global rebuild

Current-phase maintenance groups edges into families and creates the associated
navigation nodes; it does not distill or split node contents. Two modes are
specified: manual invocation with confirmation on selected nodes, and automatic
execution while the LLM is not in use only for nodes exceeding the configured
upper limit. Both aim for the configured lower target.

The logical cycle is detection; deduplicated queueing; proposed edge grouping;
validation of families and routes; publication; and rechecking affected nodes.

Work and resource consumption must be bounded, interruptible and resumable,
without repeated oscillation. If data changes after planning, the proposal must
be revalidated. Maintenance starvation must not cause hidden unbounded growth:
pressure diagnostics and an explicit admission policy are needed.

Publication must expose one coherent graph version. A SQLite transaction does
not make GPU allocations atomic: in-flight readers, resident payloads, caches
and task references require coordinated versioning/invalidation. Errors and
interruptions must leave the previous organization recoverable, not half of
an applied transformation.

The organizer itself has finite context. This phase organizes connections through
IDs and titles without distilling book contents. If no reliable families are
identified, leave a proposal pending or request review rather than delete edges
or invent groups solely to meet a numeric threshold.

## 12. Acceptance invariants

- No silent loss of content, sources or connections.
- All active focus alternatives are available, not merely a top-K.
- Reorganization changes paths without asserting new facts between group members.
- Existing identities/references remain resolvable or explicitly migrated.
- Every fragment retains the split node's complete directory while serving as the reading focus.
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

Current prompt accounting uses conservative UTF-8 bytes, not the word counts or
exact model tokenizer specified by this addendum.

It does not implement this design yet. Recall still limits edge retrieval to
`max(32, vram_capacity * 4)` per direction and neighboring-node preload to active
tier capacity. Planning remains hybrid, often using rules rather than autonomous
LLM navigation across the complete alternatives.

Immediate missing components are a complete-directory contract, LLM-led navigation,
configurable thresholds, managed navigation nodes, a maintenance queue and
coherent transformation publication. Book ingestion, PDF extraction and content
distillation/splitting remain separate developments, not prerequisites for this phase.

## 14. Updated decisions for the navigation roadmap

1. **Agreed:** initial maximum 50 edges, incoming and outgoing combined; compression
   target 45. Parameters belong in configuration, not code constants. Content-size
   thresholds concern the separate distillation system and must not delay this phase.
2. **Agreed:** expose only ID and title of connected nodes, without mandatory
   additional descriptions.
3. **Agreed:** children inherit the parent's shared directory without independent
   copies. Christian specifies that only the edge representing the child changes.
   Clarify only that edge's precise meaning: the candidate interpretation is the
   current-part reference within the family, not a change to the whole directory.
   Internal representation remains an implementation detail.
4. **Evaluate, not a blocker:** the concern was the total conversational context,
   not one node alone. With suitable contents and a bounded directory, measure
   actual behavior. Do not introduce conversation compression or a new opening-
   suspension policy now.
5. **Principle already agreed, operational explanation:** the LLM reads the node
   and directory and requests an ID; the Core validates it and moves focus. The
   LLM may continue, revisit a node or answer. This is not content distillation or
   a transfer of semantic choice to the Core. Request formats and loop/error
   safeguards are implementation details, not new conceptual choices to impose
   on the user.
6. **Narrow scope:** assume nodes already contain suitable information. Content
   generation, distillation and text splitting belong to a separate system not
   being designed now. Edge-family grouping through secondary nodes during
   “sleep” remains in scope.
7. **Agreed:** manual invocation with confirmation and node selection down to the
   lower target; automatic invocation while the LLM is not in use only for nodes
   above the upper limit. Idle detection and coherent updates are technical
   responsibilities to specify in the roadmap.
8. **Deferred:** the book, chapter and real-library evaluation will be chosen
   jointly later; they are not prerequisites for completing navigation design.

These decisions do not start implementation yet. The next roadmap concerns
navigation, directory continuity and edge management only. With already suitable
nodes, it will measure alternative completeness, route correctness, LLM choices,
context, latency and grouping/rollback correctness.

## 15. Conclusion

The design addresses scaling through structural reorganization, not a promise
of infinite context: complete persistent knowledge, bounded information units
and local choices, LLM-led navigation and maintenance that redistributes excess
without losing the source.

The book supplies an initial organization. Cross-source connections extend it.
The carousel brings useful knowledge nearby. “Sleep” keeps the network navigable.
Distillation builds signposts rather than replacing knowledge.

Granularity can increase without losing orientation: reading A3 means reading
part of A while retaining the map of A's connections.

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
