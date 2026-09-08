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

The default configuration selects the local Gemma adapter:

```yaml
runtime:
  language_adapter: gemma
```

Start LM Studio and configure the selected OpenAI-compatible provider under
`llm.runtimes` before sending the first chat message. Set the value to `rules`
only for deterministic offline fallback tests.

CLI demonstrations may still use their own explicit flags; the real dashboard
runtime does not. This keeps startup choices in one inspectable file.

Runtime memory files are kept outside the source tree. The current configuration
uses `D:/Test/Luca` for the SQLite database and future persistent memory files;
the versioned seed remains under the repository's `seed/` directory.
