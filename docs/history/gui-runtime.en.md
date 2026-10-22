> Archived on 2026-10-22; not current instructions. Snapshot before documentation review; relative links rebased where necessary. See the [current contract](../memory-integration-contract.md).

# Luca dashboard runtime

Current update: the bundled cockpit is served directly by Python, without Vite
or a Node child process. Orderly shutdown releases CUDA buffers and the database.
See [physical memory](../physical-memory.md); the frontend process description below
is retained as historical background, not current startup instructions.

The dashboard is a frontend, not part of Luca's cognitive runtime.

```text
browser GUI → local HTTP API → LucaSession / MemorySearch / LLM Connector
```

The Python API is started with:

```powershell
python run_luca.py
```

The optional Gemma path is selected by setting
`runtime.language_adapter: gemma` in `config.yaml`; the same entry point is used:

```powershell
python run_luca.py
```

The entry point starts the Vite frontend as a child process and opens the
configured browser URL automatically. Stopping the entry point stops both
runtime and frontend. Use the `Esci` button in the header for an orderly
shutdown; the API closes the session and database, then stops the frontend
child process.

## API boundary

- `GET /api/health` reports backend availability.
- `GET /api/state` returns a read-only runtime snapshot.
- `POST /api/chat` accepts `{ "text": "..." }` and returns the verified reply,
  trace, and updated snapshot.
- `POST /api/shutdown` requests an orderly shutdown of the complete runtime.

The frontend cannot access SQLite, traverse the graph, select an LLM, or write
memory. It sends user text and renders backend responses. This keeps the same
Core usable from the CLI, tests, or another frontend.
