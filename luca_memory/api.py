"""Local HTTP API that exposes Luca's runtime to a frontend dashboard."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from urllib.request import urlopen
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .adapters import LanguageAdapter, LMStudioAdapter, RuleAdapter
from .config import load_config
from .curriculum import cell_payload
from .memory import MemoryEditor
from .search import MemorySearch
from .session import LucaSession, SessionReply


class LucaRuntime:
    """Own Luca's session; the frontend receives snapshots, never the store."""

    def __init__(self, config: dict[str, Any]) -> None:
        storage = config["storage"]
        self.data_directory = Path(storage["database"]).parent
        self.data_directory.mkdir(parents=True, exist_ok=True)
        runtime_config = config["runtime"]
        adapter_name = str(runtime_config["language_adapter"])
        assignment = str(runtime_config.get("adapter_role", "orchestrator"))
        adapter: LanguageAdapter = (
            LMStudioAdapter.from_config(config, assignment=assignment)
            if adapter_name == "gemma"
            else RuleAdapter()
        )
        self.config = config
        self.database = Path(storage["database"])
        self.session = LucaSession.open(self.database, storage["seed"], adapter=adapter)
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

            database_size = self.database.stat().st_size if self.database.exists() else 0
            active_cells = sorted(set(self._last_trace))
            return {
                "status": "ready",
                "adapter": self.config["runtime"]["language_adapter"],
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


def create_server(config: dict[str, Any]) -> ThreadingHTTPServer:
    runtime = LucaRuntime(config)

    class BoundApiHandler(ApiHandler):
        pass

    BoundApiHandler.runtime = runtime
    api_config = config["runtime"]["api"]
    server = ThreadingHTTPServer((api_config["host"], api_config["port"]), BoundApiHandler)
    server.runtime = runtime  # type: ignore[attr-defined]
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    args = parser.parse_args()
    config = load_config(args.config)
    server = create_server(config)
    api_config = config["runtime"]["api"]
    frontend_process = _start_frontend(config)
    browser_thread = threading.Thread(
        target=_open_frontend_when_ready,
        args=(frontend_process, config["frontend"]["url"]),
        daemon=True,
    )
    browser_thread.start()
    print(f"Luca runtime ready at http://{api_config['host']}:{api_config['port']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        server.runtime.close()  # type: ignore[attr-defined]
        _stop_frontend(frontend_process)


def _start_frontend(config: dict[str, Any]) -> subprocess.Popen[bytes] | None:
    """Start the configured frontend as a child of the single Luca process."""

    frontend = config["frontend"]
    if not frontend.get("enabled", True):
        return None
    directory = Path(frontend["directory"])
    if not directory.exists():
        raise RuntimeError(f"Frontend directory not found: {directory}")
    _remove_stale_frontend_lock(directory, str(frontend["url"]))
    executable = "npm.cmd" if os.name == "nt" else "npm"
    return subprocess.Popen(
        [executable, "run", "dev", "--", "--host", "localhost"],
        cwd=directory,
    )


def _remove_stale_frontend_lock(directory: Path, url: str) -> None:
    """Remove Vinext's lock only when its advertised server is unreachable."""

    lock_path = directory / ".vinext" / "dev" / "lock.json"
    if not lock_path.exists():
        return
    try:
        with urlopen(url, timeout=1.0) as response:
            if 200 <= response.status < 500:
                return
    except OSError:
        pass
    lock_path.unlink(missing_ok=True)


def _open_frontend_when_ready(process: subprocess.Popen[bytes] | None, url: str) -> None:
    """Open the browser only after the frontend responds successfully."""

    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            print("Luca frontend stopped before becoming ready.")
            return
        try:
            with urlopen(url, timeout=1.0) as response:
                if 200 <= response.status < 500:
                    webbrowser.open(url)
                    return
        except OSError:
            pass
        time.sleep(0.25)
    print(f"Luca frontend did not become ready at {url} within 60 seconds.")


def _stop_frontend(process: subprocess.Popen[bytes] | None) -> None:
    """Stop the frontend child without affecting unrelated processes."""

    if process is None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


if __name__ == "__main__":
    main()
