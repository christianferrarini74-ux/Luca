"""Loader for Phase 1 articulated knowledge seeds (knowledge_base_v1.json)."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time

from .node import KnowledgeNode, save_node
from .store import Edge, MemoryStore


@dataclass(frozen=True, slots=True)
class KnowledgeSeed:
    version: str
    language: str
    ids: dict[str, int]

    def id_for(self, slug: str) -> int:
        return self.ids[slug]


def is_v1_seed(path: str | Path) -> bool:
    """Return True when the JSON seed file uses Phase 1 `nodes` + `edges` format."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return isinstance(document, dict) and "nodes" in document


def load_knowledge_seed(store: MemoryStore, path: str | Path) -> KnowledgeSeed:
    """Load or refresh an articulated Phase 1 knowledge graph into `store`."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    version = str(document.get("version", "1.0.0"))
    raw_nodes = document.get("nodes", [])
    raw_edges = document.get("edges", [])
    ids = {str(item["slug"]): index for index, item in enumerate(raw_nodes, start=1)}
    now = int(time.time())

    with store.transaction():
        store.connection.execute("DELETE FROM edges")
        store.connection.execute("DELETE FROM cell_aliases")
        store.connection.execute("DELETE FROM cell_search")
        store.connection.execute("DELETE FROM cells")
        for item in raw_nodes:
            slug = str(item["slug"])
            node = KnowledgeNode(
                id=ids[slug],
                slug=slug,
                title=str(item.get("title") or slug),
                content=str(item.get("content") or ""),
                keywords=tuple(str(k) for k in item.get("keywords", [])),
                created_at=now,
            )
            save_node(store, node)

        for source_slug, target_slug in raw_edges:
            source_id = ids[str(source_slug)]
            target_id = ids[str(target_slug)]
            store.add_edge(Edge(source_id, target_id))

        store.record_event("seed_v1", json.dumps({"version": version}).encode("utf-8"), now)

    return KnowledgeSeed(
        version=version,
        language=str(document.get("language", "it")),
        ids=ids,
    )


def ensure_knowledge_seed(store: MemoryStore, path: str | Path) -> KnowledgeSeed:
    """Load the v1 seed if the store is empty or if the seed file version changed."""

    expected = knowledge_seed_from_file(path)
    if not store.has_cells():
        return load_knowledge_seed(store, path)
    row = store.connection.execute(
        "SELECT payload FROM memory_events WHERE kind = 'seed_v1' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is not None:
        try:
            loaded_version = json.loads(row["payload"]).get("version")
            if loaded_version == expected.version and store.cell_count() == len(expected.ids):
                return expected
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            pass
    return load_knowledge_seed(store, path)


def knowledge_seed_from_file(path: str | Path) -> KnowledgeSeed:
    """Read the slug-to-ID map of a Phase 1 knowledge seed without writing to a store."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = {str(item["slug"]): index for index, item in enumerate(document.get("nodes", []), start=1)}
    return KnowledgeSeed(
        version=str(document.get("version", "1.0.0")),
        language=str(document.get("language", "it")),
        ids=ids,
    )
