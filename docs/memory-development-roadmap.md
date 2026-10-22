# Memory development roadmap — stages 1–5

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

Date: 2026-10-19. Scope: Luca only; integration with Cesare is deferred.

Subsequent milestone: [physical memory](physical-memory.md) replaces the
logical-only cache backend and protects existing knowledge during startup/reset.
The implementation notes below record the preceding stages 1–5.

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

## Stage 5 implemented

Task state is explicit and bounded: goal, up to eight constraints and decisions,
current task checkpoint, selected section, suspension flag and an eight-focus
trail. SQLite persists it independently of the knowledge graph. An unrelated
cluster can suspend the task without erasing its goal or replacing the saved
checkpoint. “Riprendi il compito” restores that checkpoint and section.
New Session intentionally clears task state; ordinary topic changes do not.

Use the dashboard form, `POST /api/task`, or chat commands `Obiettivo: ...`,
`Vincolo: ...`, `Decisione: ...`, and `Nuovo compito: ...`. Updates exceeding
`task_limit` are rejected atomically instead of silently dropping constraints.
Task text has reserved priority in model requests before expendable memory and
history. No unconfirmed model-generated decisions are saved automatically.
Conversational history is bounded to sixteen messages.

`runtime.memory_planner` accepts `rules` or `hybrid`. The hybrid baseline uses
bounded candidate previews and optionally asks the LLM to choose an ambiguous
neighbor; Core rejects unknown IDs and invalid graph jumps. It does not yet
implement arbitrary natural-language query planning or unrestricted typo repair.
`recent_window` counts activity steps/turn transitions, not wall-clock seconds.

`runtime.memory_policy: experimental` preserves the counterfactual seed's domain
for the current fable tests. Use `grounded` for ordinary knowledge: local details
remain useful while the LLM can use general knowledge. This separates experiment
control from the long-term conversation policy; neither modifies model weights.

The dashboard remains a frontend. Plans, budgets, sections, activity and task
state are computed by Python. Stage 6 and all Cesare integration remain deferred.

## Validation on 2026-10-19

77 automated tests passed, including the original core suite and new dialogue,
invalid planner proposal, exclusions, accent/typo variants, usage aging, legacy
counter preservation, no-reindex recall, large document/cache budgets, section
access, task restart/resume, atomic task update and HTTP error/shutdown tests.
JavaScript syntax and dashboard data-rendering checks passed (escaped section
titles/keys, task status and budget display). No full visual browser audit was
performed.

Live LM Studio checks used temporary databases under `D:/Test/Luca`, removed
after orderly shutdown, without opening the personal runtime database. The
reference four-turn dialogue reached focus IDs `7, 7, 19, 14`. Responses preserved
the yellow cardboard vehicles and red biscuit vehicles with a bone periscope,
then named the remaining fleet species. Final requests used 1255–2476 conservative
input units against a 7424-unit input budget. A separate live run checked general
arithmetic outside local memory and task resumption after a disconnected topic.
These smoke tests do not establish general LLM answer reliability.

Prompt policies remain project-overridable (`bible.md` and
`prompts/memory-experiment.it.md`); bundled fallbacks ship with the package.
Technical focus labels stay in Core diagnostics and are removed from model-facing
prose. Empty sanitized responses no longer fall back to leaking technical text.

Known boundaries: planner language rules are bounded Italian heuristics with an
optional model tie-breaker, not a universal semantic reasoner. Task updates require
explicit commands or API input; inferred decisions are not persisted. The seed
loader is still experimental dataset refresh, not a library migration system.
Large source reads can allocate transient memory even when retained caches are
bounded. No physical GPU cache, document acquisition pipeline, or Cesare adapter
was introduced.
