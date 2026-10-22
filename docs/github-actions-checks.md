# Reproducible GitHub checks — 2026-10-22

[Italiano](it/fase-1-sinapsi/21-controlli-github-actions.md)

The previous remote run failed in Ruff, before tests ran. The Node.js 20
deprecation and `ubuntu-latest` migration messages were separate notices.
The workflow added directly on GitHub was merged with the unpublished local
history; neither line of development was discarded.

## Changes

- Ruff 0.17.1 is pinned in CI and required by the tool configuration, targeting
  Python 3.11. Safe automatic fixes and reviewed manual changes align the code
  and tests with the existing lint rules.
- Existing `ValueError` validation contracts and intentional broad catches at
  HTTP, background-worker and diagnostic boundaries are preserved through
  narrowly scoped, explained lint exemptions.
- Actions use checkout/setup-python/setup-node v6, with Node.js 24 for frontend
  tests. The runner matrix explicitly selects Ubuntu 24.04 and Windows 2025.
- CI installs the project with `pip install -e .`, including its declared PyYAML
  dependency. It runs the actual standard-library unittest suite rather than
  introducing pytest, followed by both JavaScript test files.
- No new application dependency, bible change or personal-memory migration is
  introduced. Ruff is a development tool; Node is used by these frontend tests.

## Local verification

Ruff passes. All 235 Python tests pass with real CUDA and native LM Studio
tokenization enabled, and all 19 JavaScript tests pass. A separate editable
installation also passes the suite: 235 Python tests discovered, with seven
hardware/service-dependent tests deliberately skipped, plus 19 JavaScript tests.
Cloud CI follows this latter contract and does not require a GPU or LM Studio.
These checks do not establish conversational quality or library-scale performance.
