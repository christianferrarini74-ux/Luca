# LLM Connector

Luca usa `luca_memory.llm.LLMConnector` come confine unico tra Core e motori linguistici. Il Core non conosce URL, API key o protocolli dei provider.

## Configurazione

La configurazione separa runtime attivo, provider e ruolo che sceglie il modello:

```python
config = {
    "llm": {
        "active_runtime": "local",
        "runtimes": {
            "local": {
                "providers": {
                    "lm_studio": {"kind": "openai_compatible", "base_url": "http://127.0.0.1:1234/v1"},
                    "ollama": {"kind": "ollama", "base_url": "http://127.0.0.1:11434"},
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

I provider remoti OpenAI-compatible richiedono HTTPS e una chiave esplicita tramite `api_key` oppure `api_key_env`. Sono supportati `openai`, `xai`, `mistral`, `deepseek`, `qwen`, `moonshot` e `zhipu`.

## Confini

- Il connector crea client, ma non avvia processi o modelli.
- Il provider restituisce testo; l'adapter linguistico valida il JSON.
- Il Core di Luca resta l'unico proprietario della memoria persistente.
- Aggiungere un provider non richiede modifiche a memoria, pensiero o sessione.
