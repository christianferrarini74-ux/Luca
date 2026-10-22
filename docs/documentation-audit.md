# Documentation alignment audit

2026-10-22. [Italiano](it/fase-1-sinapsi/33-revisione-documentazione.md).

## Why this review was necessary

The old READMEs accumulated chronological release notes over the original demo
instructions. They simultaneously described the current LLM/CUDA runtime and
claimed no LLM, no third-party dependencies, an obsolete model and initial
assertion-learning workflows. Historical operating guides still described a
Vite child process, frontend port/configuration keys and “verified” chat replies.
The Italian index also presented old plans and Cesare integration as active goals.
Those are not accurate statements of the current product.

## Current source of truth

Luca is an external synaptic-memory system, not a competing language model.
The owning Core manages nodes/arcs/families, indexes, tier residency, atomic
mutations and reorganization. Producers create/partition content. Chat and
dashboard are test consumers. Content production, PDF import, distillation,
library construction and Cesare integration are outside the current scope.

Configuration and startup were checked against `config.yaml`, `config.py`,
`run_luca.py`, `api.py`, `adapters.py` and the connector implementation:
one Python server/entry point, bundled static frontend, PyYAML dependency,
Gemma E2B profile, 70,000-token budget, explicit CUDA/host selection and
external storage. Model-native token counting, structured routing/classification
and numerical Core planning are distinguished from model reasoning quality.
The connector's provider options are not certification of every provider for
the application adapter. No “verified reply” or automatic rules fallback claim.

## Whole-documentation review method

The starting Markdown inventory contained 94 tracked files (84 under `docs/`).
The review inventories document roles, checks local links across every document,
compares current operational claims with code/configuration, and separates
historical specifications/results from current guidance. It does not retroactively
revalidate every old experiment or claim a fresh execution of old hardware tests.

- Replaced both READMEs with current scope, architecture, prerequisites, entry
  point, verification commands and explicit limits.
- Revised configuration, dashboard and connector guides in both languages.
- Created complete English/Italian indexes: **96 documents**, classified as
  **15 current guides/references, 79 historical records/snapshots, two fixtures**.
- Added explicit historical-status notices to 70 original documents. Their
  original design/evidence bodies are retained, not rewritten to look current.
- Preserved nine prior versions: both READMEs, the Italian index and six
  operating guides. Relative links were rebased where relocation required it.
- Current operating guides are bilingual. Six early phase originals remain
  Italian-only historical records; the catalog explicitly identifies that limit.
- Fictional source manuals, runtime bible and experimental/legacy prompt data
  were not edited or silently promoted into the current contract.

This is a scope/status and operational-consistency audit, not a claim that all
historical architectures were implemented or all narrative hypotheses proved.
External web links are not fetched by the documentation tests. Local test reports
under `D:/Test/Luca` are artifacts of this machine, not committed reproducibility
inputs; the repository contains fixtures and commands to rerun the experiments.

## Regression checks and delivery

Five documentation tests verify repository Markdown destinations outside fenced
examples, full catalog coverage in both languages, model/database alignment with
YAML, explicit historical status and absence of old demo claims in current
READMEs. These tests are portable and do not need GitHub, CUDA or LM Studio.

The application, config, dependencies, bible and personal databases are unchanged.
Only documentation and documentation regression tests are updated. Existing
milestone test counts remain their dated evidence; the project READMEs record
the latest portable checkpoint rather than copying those old counts as current.

Delivery verification: 300 Python tests, OK (seven optional hardware/service
checks skipped); 19 JavaScript tests and Ruff passed. All checked local links
resolve and both catalogs cover all 96 documentation files. No new GPU/model
experiment was required or claimed by this documentation-only change.
