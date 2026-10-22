# Luca test dashboard and runtime

[Italiano](it/gui-runtime.md) · [Documentation index](README.md)

Current guide, 2026-10-22. Previous startup instructions are
[archived](history/gui-runtime.en.md).

The application has one entry point, `python run_luca.py`. Python serves both
the local API and static `luca_memory/web/` cockpit at `http://127.0.0.1:8765/`.
It opens the browser when `frontend.enabled` is true. No Node/Vite runtime,
frontend child process, separate frontend port or extra shell is required.

The GUI is a test frontend. It submits requests and renders Core state; graph
navigation, persistence, revisions, model selection, budgets and sleep
maintenance are implemented by the backend. Map inspection is distinct from
explicit recall. A visible title, cached payload or colored node does not
prove that the LLM read or correctly used its contents.

## Local endpoints

- `GET /api/health`: backend availability.
- `GET /api/state`: runtime/tiers/focus/directory/maintenance snapshot.
- `POST /api/chat` with `{"text":"..."}`: model reply, trace and state. The Core
  validates routing and response structure, not the factual truth of the reply.
- `POST /api/recall` with `{"node_id":1}`: explicit recall of a known node.
- `/api/memory/*` and `/api/maintenance/*`: Core operations documented in the
  [integration contract](memory-integration-contract.md).
- `POST /api/shutdown`: orderly runtime shutdown, also requested by **Esci**.

Use the configured host/port rather than assuming defaults. The API is local,
not an authenticated remote/multi-user service. The frontend cannot mutate
SQLite itself: editing and confirmation requests are validated by the owning
Core. Display limits do not reduce the memory's complete first-degree directory.

## Lifecycle

Start LM Studio's server before the supplied LLM configuration. Stop with
**Esci** (or Ctrl+C in the entry-point shell). The owned sleep worker is stopped
and joined; session, database and tier allocations are released. An in-flight
provider request is not forcibly cancelled and can delay shutdown until its
timeout. A transaction already started finishes atomically.

Restart after Python/config/interface changes and reload the browser when
frontend assets change. Documentation and tests do not restart a user's app.
