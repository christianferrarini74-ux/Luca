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
