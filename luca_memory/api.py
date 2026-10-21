"""Local HTTP API that exposes Luca's runtime and synaptic carousel to a frontend dashboard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import threading
import time
import webbrowser
import secrets
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .adapters import LanguageAdapter, LMStudioAdapter, RuleAdapter
from .config import load_config
from .context_builder import convergence_signals
from .curriculum import cell_payload
from .memory import MemoryEditor
from .node import KnowledgeNode, load_node
from .search import MemorySearch
from .session import LucaSession, SessionReply
from .store import MemoryStore
from .maintenance import IdleMaintenance, MemoryMaintenance


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
        vram_cap = int(runtime_config.get("vram_capacity", 6))
        ram_cap = int(runtime_config.get("ram_capacity", 16))
        self.session = LucaSession.open(
            self.database,
            storage["seed"],
            adapter=adapter,
            vram_capacity=vram_cap,
            ram_capacity=ram_cap,
            search_policy=str(runtime_config.get("memory_search_policy", "fast")),
            planner_mode=str(runtime_config.get("memory_planner", "hybrid")),
            memory_settings=runtime_config,
        )
        self.search = MemorySearch(self.session.store)
        self.editor = MemoryEditor(self.session.store)
        self._lock = self.session.store.lock
        self.maintenance = MemoryMaintenance(self.session.carousel.synaptic, self.session.synaptic_settings)
        self.sleep = IdleMaintenance(self.maintenance, self.session.adapter)
        self._plans = {}
        self._closed = False
        self._last_trace: tuple[int, ...] = ()

    def close(self) -> None:
        self.sleep.close()
        with self._lock:
            if not self._closed:
                self._closed = True
                self.session.close()

    def chat(self, text: str) -> dict[str, Any]:
        self.sleep.touch()
        with self._lock:
            reply = self.session.handle(text)
            self._last_trace = reply.trace
            return {"reply": self._reply_payload(reply), "state": self.state()}

    def recall_node(self, node_id: int, *, alternative: bool = False) -> dict[str, Any]:
        """Explicitly shift thought focus onto `node_id` and return updated state."""

        self.sleep.touch()
        with self._lock:
            self.session.recall_manual(node_id, alternative=alternative)
            self._last_trace = self.session.carousel.vram.node_ids()
            return {"state": self.state()}

    def reset_session(self) -> dict[str, Any]:
        """Clear chat history and reset the VRAM/RAM carousel, then greet fresh."""

        self.sleep.touch()
        with self._lock:
            self.session.reset()
            self.maintenance.memory = self.session.carousel.synaptic
            self._last_trace = ()
            reply = self.session.handle("Ciao")
            self._last_trace = reply.trace
            return {"reply": self._reply_payload(reply), "state": self.state()}

    def open_section(self, node_id: int, key: str) -> dict[str, Any]:
        self.sleep.touch()
        with self._lock:
            self.session.open_section(node_id, key)
            self._last_trace = self.session.carousel.vram.node_ids()
            return {"state": self.state()}

    def update_task(self, values: dict[str, Any]) -> dict[str, Any]:
        self.sleep.touch()
        with self._lock:
            self.session.task.update(values, self.session.current_subject_id)
            return {"state": self.state()}

    def memory_operation(self, operation, payload):
        """All mutations stay in the Core; the dashboard only supplies requests."""
        self.sleep.touch()
        with self._lock:
            memory = self.session.carousel.synaptic
            if operation == "search":
                query = payload.get("query")
                if not isinstance(query, str) or not query.strip() or len(query) > 2000:
                    raise ValueError("A nonempty query of at most 2000 characters is required.")
                return {"revision": self.session.store.revision, "candidates": [
                    {"id": entry.id, "title": entry.title} for entry in memory.global_lookup(
                        query, self.session.synaptic_settings.global_candidates)]}
            if operation == "navigate":
                target, revision = payload.get("target_id"), payload.get("directory_revision")
                if type(target) is not int or type(revision) is not int or self.session.carousel.reading_id is None:
                    raise ValueError("A reading focus, integer target and directory revision are required.")
                memory.validate_step(self.session.carousel.reading_id, target, revision)
                return self.recall_node(target)
            expected = payload.get("expected_revision")
            if type(expected) is not int:
                raise ValueError("An integer expected_revision is required.")
            if operation == "node":
                node_id = payload.get("node_id")
                if type(node_id) is not int or node_id <= 0:
                    raise ValueError("A positive integer node_id is required.")
                old = load_node(self.session.store, node_id)
                if not isinstance(payload.get("title"), str) or not isinstance(payload.get("content"), str):
                    raise ValueError("Node title and content must be strings.")
                node = replace(old, title=payload["title"], content=payload["content"]) if old else KnowledgeNode(
                    node_id, f"node_{node_id}", payload["title"], payload["content"])
                memory.update_node(node, expected_revision=expected)
            elif operation == "edge":
                if type(payload.get("source")) is not int or type(payload.get("target")) is not int:
                    raise ValueError("Edge endpoints must be integers.")
                memory.connect(payload["source"], payload["target"], remove=payload.get("remove") is True,
                               expected_revision=expected)
            elif operation == "family":
                if type(payload.get("root")) is not int or type(payload.get("part")) is not int:
                    raise ValueError("Family IDs must be integers.")
                memory.attach_part(payload["root"], payload["part"], expected_revision=expected)
            else:
                raise ValueError("Unknown memory operation.")
            return {"state": self.state()}

    def maintenance_operation(self, operation, payload):
        self.sleep.touch()
        with self._lock:
            if operation == "preview":
                node_id = payload.get("node_id")
                if type(node_id) is not int:
                    raise ValueError("An integer node_id is required.")
                directory = self.maintenance.memory.directory(node_id)
                groups = payload.get("groups")
                if groups is None and directory.external_degree > self.session.synaptic_settings.edge_target:
                    if not hasattr(self.session.adapter, "propose_groups"):
                        raise ValueError("The configured adapter cannot propose groups; supply explicit groups.")
                    groups = self.session.adapter.propose_groups(directory, self.session.synaptic_settings)
                plan = self.maintenance.plan(node_id, groups or [])
                plan_id = secrets.token_hex(16)
                # Bound pending previews; clients must prepare a new one after replacement.
                self._plans = {plan_id: plan}
                return {"plan_id": plan_id, "plan": plan.payload()}
            if operation == "apply":
                plan = self._plans.get(payload.get("plan_id"))
                if plan is None:
                    raise ValueError("Unknown maintenance preview; prepare it again.")
                operation_id = self.maintenance.apply(plan, confirmed=payload.get("confirmed") is True)
                self._plans.clear()
                return {"operation_id": operation_id, "state": self.state()}
            if operation == "restore":
                operation_id = payload.get("operation_id")
                if type(operation_id) is not int:
                    raise ValueError("An integer operation_id is required.")
                self.maintenance.restore(operation_id, confirmed=payload.get("confirmed") is True)
                return {"state": self.state()}
            raise ValueError("Unknown maintenance operation.")

    def state(self) -> dict[str, Any]:
        """Return a bounded dashboard view of the authoritative Core state."""
        with self._lock:
            memory = self._build_memory_items()
            carousel = self.session.carousel
            carousel.synchronize()
            vram_nodes = [self._serialize_tier_node(node, in_vram=True) for node in carousel.vram.nodes()]
            ram_nodes = [self._serialize_tier_node(node, in_vram=False) for node in carousel.ram.nodes()]
            chains = [
                [
                    (load_node(self.session.store, nid).title if load_node(self.session.store, nid) else str(nid))
                    for nid in chain
                ]
                for chain in carousel.vram_graph.chains()
            ]
            families = self._serialize_vram_families()
            convergence = convergence_signals(carousel)

            database_size = self.database.stat().st_size if self.database.exists() else 0
            active_cells = list(carousel.vram.node_ids()) or sorted(set(self._last_trace))
            ram_count = len(carousel.ram) if self.session.is_v1 else len(active_cells)
            vram_count = len(carousel.vram) if self.session.is_v1 else min(len(active_cells), 512)
            total_cells = self.session.store.cell_count()

            return {
                "status": "ready",
                "synaptic": {
                    "revision": self.session.store.revision,
                    "focus_id": carousel.focus_id,
                    "reading_id": carousel.reading_id,
                    "family": {"root_id": carousel.synaptic.root(carousel.reading_id),
                               "part_ids": carousel.synaptic.parts(carousel.synaptic.root(carousel.reading_id))}
                        if carousel.reading_id is not None else None,
                    "directory": carousel.synaptic.directory(carousel.focus_id).payload()
                        if carousel.focus_id is not None and self.session.store.cell(carousel.focus_id) else None,
                    "planner": self.session.planner_mode,
                    "navigation": self.session.navigator.trace,
                    "entry_candidate_ids": self.session.navigator.entry_ids,
                    "explicit_search_performed": self.session.navigator.search_performed,
                    "edge_upper": self.session.synaptic_settings.edge_upper,
                    "edge_target": self.session.synaptic_settings.edge_target,
                    "automatic_sleep": self.session.synaptic_settings.automatic_sleep,
                    "sleep_error": self.sleep.last_error,
                    "last_operation": self.sleep.last_operation,
                    "operations": [dict(id=row[0], active=bool(row[1])) for row in self.session.store.connection.execute(
                        "SELECT id,active FROM maintenance_operations ORDER BY id DESC LIMIT 20")],
                },
                "physical_memory": carousel.physical_state(),
                "adapter": self.config["runtime"]["language_adapter"],
                "memory": memory,
                "convergence": convergence,
                "previous_convergence": convergence_signals(carousel, previous=True),
                "memory_search_policy": carousel.search_policy,
                "memory_policy": self.config["runtime"].get("memory_policy", "grounded"),
                "recall_plan": self.session.last_plan.payload() if self.session.last_plan else None,
                "memory_activity": carousel.activity.snapshot(),
                "context_budget": carousel.context_report,
                "model_request": getattr(self.session.adapter, "last_prompt_report", {}),
                "task": self.session.task.snapshot(),
                "tiers": {
                    "vram": {
                        "capacity": carousel.vram.capacity,
                        "payload_bytes": carousel.vram.used_bytes,
                        "max_bytes": carousel.vram.max_bytes,
                        "nodes": vram_nodes,
                        "chains": chains,
                        "families": families,
                    },
                    "ram": {
                        "capacity": carousel.ram.capacity,
                        "payload_bytes": carousel.ram.used_bytes,
                        "max_bytes": carousel.ram.max_bytes,
                        "nodes": ram_nodes,
                    },
                    "ssd": {
                        "total_cells": total_cells,
                    },
                },
                "storage": {
                    "ssd_bytes": database_size,
                    "ssd_label": f"{database_size / 1_000_000:.2f} MB",
                },
                "working_set": {
                    "ram_cells": ram_count,
                    "vram_cells": vram_count,
                    "ssd_cells": total_cells,
                    "trace": active_cells,
                },
            }

    def _serialize_vram_families(self) -> list[dict[str, Any]]:
        carousel = self.session.carousel
        store = self.session.store
        vram_ids = list(carousel.vram.node_ids())
        seen: set[tuple[str, int]] = set()
        result: list[dict[str, Any]] = []

        for node_id in vram_ids:
            node = load_node(store, node_id)
            if node is None:
                continue
            prefix_members = store.prefix_family_ids(node_id, limit=8)
            if len(prefix_members) >= 2 and ("prefix", node_id) not in seen:
                seen.add(("prefix", node_id))
                result.append(
                    {
                        "anchor_id": node_id,
                        "anchor_slug": node.slug,
                        "anchor_title": node.title,
                        "direction": "prefix",
                        "pattern": f"{node_id}:*",
                        "slug_pattern": f"{node.slug}:*",
                        "member_ids": list(prefix_members),
                        "member_titles": [
                            (load_node(store, mid).title if load_node(store, mid) else str(mid))
                            for mid in prefix_members
                        ],
                    }
                )
            suffix_members = store.suffix_family_ids(node_id, limit=8)
            if len(suffix_members) >= 2 and ("suffix", node_id) not in seen:
                seen.add(("suffix", node_id))
                result.append(
                    {
                        "anchor_id": node_id,
                        "anchor_slug": node.slug,
                        "anchor_title": node.title,
                        "direction": "suffix",
                        "pattern": f"*:{node_id}",
                        "slug_pattern": f"*:{node.slug}",
                        "member_ids": list(suffix_members),
                        "member_titles": [
                            (load_node(store, mid).title if load_node(store, mid) else str(mid))
                            for mid in suffix_members
                        ],
                    }
                )
        return result

    def _build_memory_items(self) -> list[dict[str, Any]]:
        memory: list[dict[str, Any]] = []
        knowledge_cells = self.search.cells_by_kind("knowledge", limit=100)
        if knowledge_cells:
            for result in knowledge_cells:
                node = KnowledgeNode.from_cell(result.cell)
                facts = []
                for edge in self.session.store.outgoing(node.id, limit=MemoryStore.DEFAULT_FAMILY_LIMIT):
                    target = load_node(self.session.store, edge.target_id)
                    if target is not None:
                        facts.append({"predicate": f"{node.slug}:*", "object": target.title})
                for edge in self.session.store.incoming(node.id, limit=MemoryStore.DEFAULT_FAMILY_LIMIT):
                    source = load_node(self.session.store, edge.source_id)
                    if source is not None:
                        facts.append({"predicate": f"*:{node.slug}", "object": source.title})
                memory.append({"id": node.id, "label": node.title, "slug": node.slug,
                               "content": node.content[:2000], "content_truncated": len(node.content) > 2000,
                               "summary": node.summary[:512],
                               "sections": [{"key": s.key, "title": s.title} for s in node.sections[:32]], "facts": facts})
            return memory

        for result in self.search.cells_by_kind("concept", limit=100):
            payload = cell_payload(self.session.store, result.cell.id)
            label = str(payload.get("label") or payload.get("forms", [result.cell.id])[0])
            facts = []
            for fact in self.editor.facts_about(result.cell.id):
                predicate = cell_payload(self.session.store, fact.predicate_id).get("label", "?")
                object_label = cell_payload(self.session.store, fact.object_id).get("label", "?")
                facts.append({"predicate": str(predicate), "object": str(object_label)})
            memory.append({"id": result.cell.id, "label": label, "facts": facts})
        return memory

    def _serialize_tier_node(self, node: KnowledgeNode, *, in_vram: bool) -> dict[str, Any]:
        carousel = self.session.carousel
        family_limit = MemoryStore.DEFAULT_FAMILY_LIMIT
        incoming = [
            edge.source_id
            for edge in (
                carousel.vram_graph.incoming_for(node.id) if in_vram else self.session.store.incoming(node.id, limit=family_limit)
            )
        ]
        outgoing = [
            edge.target_id
            for edge in (
                carousel.vram_graph.outgoing_for(node.id) if in_vram else self.session.store.outgoing(node.id, limit=family_limit)
            )
        ]
        return {
            "id": node.id,
            "slug": node.slug,
            "title": node.title,
            "content": node.content[:2000],
            "content_truncated": not node.content_complete or len(node.content) > 2000,
            "expanded": node.id in carousel.expanded_in_vram if in_vram else False,
            "recall_count": node.recall_count,
            "incoming_ids": incoming,
            "outgoing_ids": outgoing,
            "prefix_families": [f"{pid}:*" for pid in incoming],
            "suffix_families": [f"*:{sid}" for sid in outgoing],
        }

    @staticmethod
    def _reply_payload(reply: SessionReply) -> dict[str, Any]:
        return {"text": reply.text, "trace": list(reply.trace)}


_WEB_DIR = Path(__file__).resolve().parent / "web"
_STATIC_ROUTES: dict[str, tuple[str, str]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/cesare.css": ("cesare.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
}


class ApiHandler(BaseHTTPRequestHandler):
    runtime: LucaRuntime
    shutdown_server: Any

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        clean_path = self.path.split("?", 1)[0]
        if clean_path in _STATIC_ROUTES:
            filename, content_type = _STATIC_ROUTES[clean_path]
            file_path = _WEB_DIR / filename
            if file_path.exists():
                body = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        if clean_path == "/api/health":
            self._json({"status": "ok"})
            return
        if clean_path == "/api/state":
            self._json(self.runtime.state())
            return
        self._json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            self._json({"error": "Cross-origin mutations are not allowed."}, status=403)
            return
        if self.path.startswith("/api/maintenance/") or self.path.startswith("/api/memory/"):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000:
                    raise ValueError("Invalid request size.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("The request must be an object.")
                operation = self.path.rsplit("/", 1)[1]
                method = self.runtime.maintenance_operation if self.path.startswith("/api/maintenance/") else self.runtime.memory_operation
                self._json(method(operation, payload))
            except (ValueError, TypeError, KeyError) as error:
                self._json({"error": str(error)}, status=400)
            except Exception as error:
                self._json({"error": str(error)}, status=500)
            return
        if self.path == "/api/task":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
                self._json(self.runtime.update_task(payload))
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                self._json({"error": str(error)}, status=400)
            return
        if self.path == "/api/shutdown":
            self._json({"status": "shutting_down"}, status=202)
            threading.Thread(target=self.shutdown_server, daemon=True).start()
            return
        if self.path in {"/api/recall", "/api/alternative", "/api/section"}:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("The request body must be an object.")
                node_id = int(payload.get("node_id"))
                if self.path == "/api/section":
                    key = payload.get("key")
                    if not isinstance(key, str):
                        raise ValueError("A section key is required.")
                    self._json(self.runtime.open_section(node_id, key))
                else:
                    self._json(self.runtime.recall_node(node_id, alternative=self.path == "/api/alternative"))
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                self._json({"error": str(error)}, status=400)
            return
        if self.path == "/api/reset":
            self._json(self.runtime.reset_session())
            return
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
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


def create_server(config: dict[str, Any]) -> ThreadingHTTPServer:
    runtime = LucaRuntime(config)

    class BoundApiHandler(ApiHandler):
        pass

    BoundApiHandler.runtime = runtime
    api_config = config["runtime"]["api"]
    try:
        server = ThreadingHTTPServer((api_config["host"], api_config["port"]), BoundApiHandler)
    except BaseException:
        runtime.close()
        raise
    BoundApiHandler.shutdown_server = server.shutdown
    server.runtime = runtime  # type: ignore[attr-defined]
    runtime.sleep.start()
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    args = parser.parse_args()
    config = load_config(args.config)
    server = create_server(config)
    api_config = config["runtime"]["api"]
    cockpit_url = f"http://{api_config['host']}:{api_config['port']}/"
    if config.get("frontend", {}).get("enabled", True):
        threading.Thread(
            target=lambda: (time.sleep(0.25), webbrowser.open(cockpit_url)),
            daemon=True,
        ).start()
    print(f"Luca cockpit ready at {cockpit_url}")
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
