# Memory development roadmap — stages 1–5

Date: 2026-10-19. Scope: Luca only; integration with Cesare is deferred.

[Italiano](it/fase-1-sinapsi/08-roadmap-utilizzo-memoria.md)

1. Make the submarine conversation an executable contract, including references
   to yellow vehicles, lateral animal changes, family enumeration, accents,
   paraphrases, exclusions and unknown topics.
2. Add a recall planner with a deterministic baseline and optional bounded LLM
   proposals. The Core validates all target IDs and routes. A shared graph
   neighbor is not sufficient evidence of semantic relevance. Preserve pure edges.
3. Separate preload, opening, traversal and response exposure. Recent activity
   has a bounded lifetime; opening a hub must not reinforce every previously
   opened endpoint. Preserve SSD knowledge and existing tier capacity invariants.
4. Bound context and caches by size as well as node count. Keep stable document
   identity and support section access. Separate usage metadata from content so
   recalls do not rebuild the full text index. Bound the whole model request,
   including history, question, instructions and output reservation.
5. Keep explicit goal, constraints, decisions and resumable focus independently
   of local clusters. Task changes are explicit, bounded and visible in the API.

Acceptance: deterministic and mocked planner tests, invalid-plan rejection,
small-cache eviction and aging tests, large-content bounds, task continuation
across disconnected clusters, HTTP contracts and a live local-model smoke test.
Document empirical limits and keep experimental prompts separate from the free
conversation policy. No new acquisition pipeline or Cesare coupling is in scope.

## Stages 1–3 implemented

The reference dialogue now preserves object attributes, selects a lateral member
and opens the family for enumeration. A bounded hybrid planner accepts model
proposals only from graph-validated candidates and abstains on unresolved ties.
Negations are clause-scoped; accent normalization treats `Perché` and `Perche`
consistently. This is a baseline, not unrestricted semantic understanding.

Activity distinguishes preload, open, traverse, association, exposure and tier
demotion. Recent priority expires after a bounded activity window; only actual
traversals or links supporting the selected recall reinforce edges. Exposure
means content supplied for a successful response, not proof the model used it
correctly. SQLite `node_usage` stores usage separately from indexed content.

## Stage 4 implemented

`runtime.context_budget` configures the whole request envelope and memory/history
sub-budgets. UTF-8 bytes are used conservatively; this is not a provider tokenizer
or proof for arbitrary model templates. Configure a window no larger than the
server model's real window. Oversized questions are rejected, not silently cut.
VRAM/RAM additionally bound retained serialized payload bytes (`vram_bytes`,
`ram_bytes`); these are not process RSS or physical GPU allocation limits.
Oversized nodes have partial cache views, which cannot overwrite SSD knowledge.
Loading a full source to extract a section can still transiently allocate it.

Knowledge nodes support optional `summary` and `sections` (`key`, `title`,
`content`). The backend validates `/api/section` and keeps the document ID as
focus while exposing the chosen section. Context excerpts are explicitly marked
partial. The dashboard displays budgets and section controls; all logic remains
in Python. The source content and index are unchanged by usage updates.
