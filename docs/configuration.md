# Luca configuration

[Italiano](it/configuration.md) · [Documentation index](README.md)

Current operational guide, reviewed against `config.yaml` and
`luca_memory/config.py` on 2026-10-22. The previous guide is
[archived](history/configuration.en.md).

## One entry point, one configuration

From the repository root run `python run_luca.py`. It loads `config.yaml`
once; an explicit alternate file can be selected with `--config`. Restart after
Python/YAML changes. `runtime.bible` is reread on model requests, but a changed
interface must be deployed with the matching Python code.

The supplied file is machine-specific, not a portable hardware prescription:

| Setting | Supplied value / meaning |
| --- | --- |
| `storage.directory` | `D:/Test/Luca`, outside the source tree |
| `storage.database` | `luca_library.sqlite`, resolved against the storage directory |
| `storage.seed` | `seed/library_empty_v1.json`, resolved against the config directory |
| `runtime.bible` | `bible.md`, resolved against the config directory |
| `language_adapter` / `memory_planner` | `gemma` / `llm`, the LM Studio structured navigation path |
| `memory_backend` / `gpu_device` | `cuda` / 1; real device storage on zero-based ordinal 1 |
| `vram_capacity` / `ram_capacity` | 5 / 12 payload slots |
| `vram_bytes` / `ram_bytes` | 8,000,000 / 32,000,000 serialized bytes |
| `context_budget.unit` / `context_window` | `tokens` / 70,000; native model counting |
| `synaptic.edge_upper` / `edge_target` | 50 / 45 external incoming + outgoing arcs |
| `synaptic.automatic_sleep` / `idle_seconds` | true / 60 |
| `runtime.api.host` / `port` | `127.0.0.1` / 8765 |
| `frontend.enabled` | true; automatically opens the bundled cockpit |
| `frontend.graph.node_limit` / `edge_limit` | 500 / 2,000 display limits, not memory limits |

Paired keys share the first key's parent path; other abbreviated keys belong
under `runtime`. Use `runtime.memory_backend: host` without suitable CUDA
hardware; host mode does not test physical VRAM. Do not assume GPU 1 exists.
Change the storage path on other operating systems or machines.

The active LLM role is `runtime.adapter_role: orchestrator`. It resolves through
`llm.active_runtime` and `llm.runtimes.<name>.agents.<role>`. The supplied profile
uses `google/gemma-4-e2b` at `http://127.0.0.1:1234/v1`, management URL
`http://127.0.0.1:1234`, temperature 0, timeout 180 seconds and no forced
generation overrides. Start LM Studio's server and install the model first.

`rules` is an explicit deterministic test adapter, not an automatic LLM outage
fallback. If using it, select a compatible `rules` or `hybrid` planner; the
`llm` planner needs an adapter supporting structured navigation.

See the [memory contract](memory-integration-contract.md) for all token,
directory and maintenance budgets. Tokens bound prompts; bytes bound physical
tiers. Neither is an automatic content-distillation or splitting service.

## Persistence and frontend

Do not call the replacement seed loader to append knowledge. Empty initialization
and existing-seed validation preserve existing nodes; mismatched identities
require an explicit migration or a separate DB. [Producer example](../examples/memory_contract.py).

The Python server serves the frontend itself. Old `frontend.directory`,
`frontend.url` and `frontend.api_url` keys are obsolete and discarded by the
loader. There is no Vite child process or separately configured frontend port.
