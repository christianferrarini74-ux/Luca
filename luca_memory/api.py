"""Local HTTP API that exposes Luca's runtime to a frontend dashboard."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .adapters import LanguageAdapter, LMStudioAdapter, RuleAdapter
from .curriculum import cell_payload
from .memory import MemoryEditor
from .search import MemorySearch
from .session import LucaSession, SessionReply


@dataclass(frozen=True, slots=True)
class ApiConfig:
    database: Path
    seed: Path
    adapter_name: str
    host: str
    port: int


class LucaRuntime:
    """Own Luca's session; the frontend receives snapshots, never the store."""

    def __init__(self, config: ApiConfig) -> None:
        adapter: LanguageAdapter = (
            LMStudioAdapter() if config.adapter_name == "gemma" else RuleAdapter()
        )
        self.config = config
        self.session = LucaSession.open(config.database, config.seed, adapter=adapter)
        self.search = MemorySearch(self.session.store)
        self.editor = MemoryEditor(self.session.store)
        self._lock = threading.RLock()
        self._last_trace: tuple[int, ...] = ()

    def close(self) -> None:
        with self._lock:
            self.session.close()

    def chat(self, text: str) -> dict[str, Any]:
        with self._lock:
            reply = self.session.handle(text)
            self._last_trace = reply.trace
            return {"reply": self._reply_payload(reply), "state": self.state()}

    def state(self) -> dict[str, Any]:
        with self._lock:
            memory = []
            for result in self.search.cells_by_kind("concept", limit=100):
                payload = cell_payload(self.session.store, result.cell.id)
                label = str(payload.get("label") or payload.get("forms", [result.cell.id])[0])
                facts = []
                for fact in self.editor.facts_about(result.cell.id):
                    predicate = cell_payload(self.session.store, fact.predicate_id).get("label", "?")
                    object_label = cell_payload(self.session.store, fact.object_id).get("label", "?")
                    facts.append({"predicate": str(predicate), "object": str(object_label)})
                memory.append({"id": result.cell.id, "label": label, "facts": facts})

            database_size = self.config.database.stat().st_size if self.config.database.exists() else 0
            active_cells = sorted(set(self._last_trace))
            return {
                "status": "ready",
                "adapter": self.config.adapter_name,
                "memory": memory,
                "storage": {
                    "ssd_bytes": database_size,
                    "ssd_label": f"{database_size / 1_000_000:.2f} MB",
                },
                "working_set": {
                    "ram_cells": len(active_cells),
                    "vram_cells": min(len(active_cells), 512),
                    "trace": active_cells,
                },
            }

    @staticmethod
    def _reply_payload(reply: SessionReply) -> dict[str, Any]:
        return {"text": reply.text, "trace": list(reply.trace)}


class ApiHandler(BaseHTTPRequestHandler):
    runtime: LucaRuntime

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            self._json({"status": "ok"})
            return
        if self.path == "/api/state":
            self._json(self.runtime.state())
            return
        self._json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/chat":
            self._json({"error": "Not found"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            text = payload.get("text") if isinstance(payload, dict) else None
            if not isinstance(text, str) or not text.strip():
                raise ValueError("text must be a non-empty string")
            self._json(self.runtime.chat(text.strip()))
        except (ValueError, json.JSONDecodeError) as error:
            self._json({"error": str(error)}, status=400)
        except Exception as error:  # pragma: no cover - defensive HTTP boundary
            self._json({"error": str(error)}, status=500)

    def log_message(self, format: str, *args: object) -> None:
        return None

    def _json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _headers(self) -> None:
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


def create_server(config: ApiConfig) -> ThreadingHTTPServer:
    runtime = LucaRuntime(config)

    class BoundApiHandler(ApiHandler):
        pass

    BoundApiHandler.runtime = runtime
    server = ThreadingHTTPServer((config.host, config.port), BoundApiHandler)
    server.runtime = runtime  # type: ignore[attr-defined]
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("luca.sqlite"))
    parser.add_argument("--seed", type=Path, default=Path(__file__).parent.parent / "seed" / "italian_base_v0.json")
    parser.add_argument("--adapter", choices=("rules", "gemma"), default="rules")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    config = ApiConfig(args.database, args.seed, args.adapter, args.host, args.port)
    server = create_server(config)
    print(f"Luca API ready at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        server.runtime.close()  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
