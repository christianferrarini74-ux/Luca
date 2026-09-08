# Luca configuration

Luca has one runtime configuration file: `config.yaml` at the repository root.
The configured entry point is:

```powershell
python run_luca.py
```

The file controls storage paths, the API bind address, the frontend directory
and URL, the language adapter, and the LLM runtime selected by the connector.
The runtime loads it once and constructs the rest of the system from that
configuration.

Change:

```yaml
runtime:
  language_adapter: rules
```

to `gemma` only after starting LM Studio and configuring the selected
OpenAI-compatible provider under `llm.runtimes`.

CLI demonstrations may still use their own explicit flags; the real dashboard
runtime does not. This keeps startup choices in one inspectable file.
