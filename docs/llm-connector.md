# LLM Connector

Luca uses `luca_memory.llm.LLMConnector` as the single boundary between the
Core and language engines. The Core does not know provider URLs, API keys, or
wire protocols.

## Configuration

Configuration follows the same separation used by the Cesare project:

```python
config = {
    "llm": {
        "active_runtime": "local",
        "runtimes": {
            "local": {
                "providers": {
                    "lm_studio": {
                        "kind": "openai_compatible",
                        "base_url": "http://127.0.0.1:1234/v1",
                    },
                    "ollama": {
                        "kind": "ollama",
                        "base_url": "http://127.0.0.1:11434",
                    },
                },
                "agents": {
                    "orchestrator": {
                        "provider": "lm_studio",
                        "model": "gemma-3-1B-it-QAT-GGUF",
                        "temperature": 0.0,
                        "timeout_seconds": 30,
                    }
                },
            }
        },
    }
}
```

Remote OpenAI-compatible providers require an HTTPS endpoint and an explicit
key through `api_key` or `api_key_env`. The supported kinds are `openai`,
`xai`, `mistral`, `deepseek`, `qwen`, `moonshot`, and `zhipu`.

## Boundaries

- The connector creates clients but does not start processes or models.
- A provider returns text; the language adapter validates the JSON.
- Luca Core remains the sole owner of persistent memory.
- Adding a provider does not require changes to memory, thought, or session code.
