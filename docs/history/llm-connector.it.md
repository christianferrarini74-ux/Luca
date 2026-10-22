> Archivio del 2026-10-22, non guida attuale. Copia precedente alla revisione documentale; collegamenti relativi adattati dove necessario. Per lo stato vigente vedere [il contratto](../it/fase-1-sinapsi/28-contratto-utilizzo-memoria.md).

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
                        "model": "google/gemma-3-1b",
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

- Il connector crea i client. L'adapter LM Studio individua inoltre il modello
  configurato tramite `/api/v1/models` e chiede a LM Studio di caricarlo tramite
  `/api/v1/models/load` quando è installato ma non residente.
- Luca non scarica modelli e non avvia autonomamente l'applicazione LM Studio.
- Il provider restituisce testo; l'adapter linguistico valida il JSON.
- Il Core di Luca resta l'unico proprietario della memoria persistente.
- Aggiungere un provider non richiede modifiche a memoria, pensiero o sessione.
