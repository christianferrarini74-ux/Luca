# Luca dashboard runtime

The dashboard is a frontend, not part of Luca's cognitive runtime.

```text
browser GUI → local HTTP API → LucaSession / MemorySearch / LLM Connector
```

The Python API is started with:

```powershell
python -m luca_memory.api --database .\luca.sqlite --adapter rules
```

The optional Gemma path uses:

```powershell
python -m luca_memory.api --database .\luca.sqlite --adapter gemma
```

The Vite frontend runs separately from `gui/`:

```powershell
npm run dev
```

## API boundary

- `GET /api/health` reports backend availability.
- `GET /api/state` returns a read-only runtime snapshot.
- `POST /api/chat` accepts `{ "text": "..." }` and returns the verified reply,
  trace, and updated snapshot.

The frontend cannot access SQLite, traverse the graph, select an LLM, or write
memory. It sends user text and renders backend responses. This keeps the same
Core usable from the CLI, tests, or another frontend.
