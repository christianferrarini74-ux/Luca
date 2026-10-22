# LLM Connector

[Italiano](it/llm-connector.md) · [Documentation index](README.md)

Current boundary guide, reviewed 2026-10-22. The older example is
[archived](history/llm-connector.en.md).

`luca_memory.llm.LLMConnector` resolves a configured role to a provider/model
profile and creates a chat client. Provider-neutral clients and the application
adapter are different layers: configuring a client does not certify a provider
for structured navigation, native token accounting or model management.

The supplied application uses `LMStudioAdapter`, selected by the historical
config name `runtime.language_adapter: gemma`. The configured model need not
be Gemma. This adapter currently requires the `openai_compatible` provider kind,
LM Studio-compatible model management and, with token budgets, its native
tokenizer. The connector's other provider implementations are not automatically
drop-in replacements for this full application path.

## Supplied profile

`llm.active_runtime` is `local`. Under `llm.runtimes.local`, provider
`lm_studio` has `base_url: http://127.0.0.1:1234/v1` and
`management_url: http://127.0.0.1:1234`. Role `orchestrator` selects that
provider, `google/gemma-4-e2b`, temperature 0, timeout 180 seconds and
`generation: {}`. Settings belong in `config.yaml`, not in consumer code.

The adapter discovers installed/resident models and requests loading the
configured installed model when necessary. It does not download models, start
the LM Studio app or claim support for a model merely because it is listed.

## Requests and ownership

Model instructions come from `runtime.bible`. Runtime facts, user text and
history are data. Navigation and maintenance classification use structured
output; a final conversational reply can be part of the navigation result.
This is not a pipeline where JSON is used only for fact acquisition.

The classifier labels the complete directional directory; the Core calculates
routing groups and owns all memory writes. See the
[classification contract](category-routing-planner.md) and
[integration API](memory-integration-contract.md).

Provider failures remain visible, without silently switching to a rules model.
Remote connector profiles require the relevant authentication/HTTPS rules;
do not put secrets in committed YAML. Different providers need explicit
adapter/capability validation before production use.
