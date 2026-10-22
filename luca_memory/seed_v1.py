"""Loader for Phase 1 articulated knowledge seeds (knowledge_base_v1.json)."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from .node import KnowledgeNode, KnowledgeSection, save_node
from .store import Edge, MemoryStore


@dataclass(frozen=True, slots=True)
class KnowledgeSeed:
    version: str
    language: str
    ids: dict[str, int]
    fingerprint: str = ""

    def id_for(self, slug: str) -> int:
        return self.ids[slug]


def is_v1_seed(path: str | Path) -> bool:
    """Return True when the JSON seed file uses Phase 1 `nodes` + `edges` format."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return isinstance(document, dict) and "nodes" in document


def _seed_metadata(document: dict) -> KnowledgeSeed:
    """Identify the seed's ID mapping and topology, not mutable personal content."""
    if not isinstance(document, dict) or not isinstance(document.get("nodes"), list) or not isinstance(document.get("edges", []), list):
        # Preserve the existing ValueError contract used by validation callers.
        raise ValueError("A knowledge seed must contain node and edge lists.")  # noqa: TRY004
    raw_nodes = document.get("nodes", [])
    if any(not isinstance(item, dict) or "slug" not in item for item in raw_nodes):
        raise ValueError("Every seed node must contain a slug.")
    ids = {str(item["slug"]): index for index, item in enumerate(raw_nodes, start=1)}
    if len(ids) != len(raw_nodes) or any(not slug.strip() for slug in ids):
        raise ValueError("Seed node slugs must be non-empty and unique.")
    edges = set()
    for edge in document.get("edges", []):
        if not isinstance(edge, (list, tuple)) or len(edge) != 2 or any(str(slug) not in ids for slug in edge):
            raise ValueError("Each seed edge must name two existing node slugs.")
        edges.add((ids[str(edge[0])], ids[str(edge[1])]))
    canonical = json.dumps({"ids": sorted(ids.items()), "edges": sorted(edges)}, separators=(",", ":"), ensure_ascii=False)
    return KnowledgeSeed(str(document.get("version", "1.0.0")), str(document.get("language", "it")), ids,
                         hashlib.sha256(canonical.encode("utf-8")).hexdigest())


def load_knowledge_seed(store: MemoryStore, path: str | Path) -> KnowledgeSeed:
    """Load or refresh an articulated Phase 1 knowledge graph into `store`."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    metadata = _seed_metadata(document)
    version = metadata.version
    raw_nodes = document.get("nodes", [])
    raw_edges = document.get("edges", [])
    ids = metadata.ids
    now = int(time.time())

    with store.transaction():
        store.connection.execute("DELETE FROM edges")
        store.connection.execute("DELETE FROM family_parts")
        store.connection.execute("DELETE FROM maintenance_operations")
        store.connection.execute("DELETE FROM cell_aliases")
        store.connection.execute("DELETE FROM cell_search")
        store.connection.execute("DELETE FROM entry_search")
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
                summary=str(item.get("summary") or ""),
                sections=tuple(KnowledgeSection(str(s["key"]), str(s.get("title") or s["key"]), str(s.get("content") or ""))
                               for s in item.get("sections", []) if isinstance(s, dict) and s.get("key")),
            )
            save_node(store, node)

        for source_slug, target_slug in raw_edges:
            source_id = ids[str(source_slug)]
            target_id = ids[str(target_slug)]
            store.add_edge(Edge(source_id, target_id))

        store.record_event("seed_v1", json.dumps({"version": version, "fingerprint": metadata.fingerprint}).encode("utf-8"), now)

    return KnowledgeSeed(
        version=version,
        language=str(document.get("language", "it")),
        ids=ids,
        fingerprint=metadata.fingerprint,
    )


def ensure_knowledge_seed(store: MemoryStore, path: str | Path) -> KnowledgeSeed:
    """Initialize an empty store; never replace an existing knowledge library."""

    expected = knowledge_seed_from_file(path)
    if not store.has_cells():
        return load_knowledge_seed(store, path)
    row = store.connection.execute(
        "SELECT payload FROM memory_events WHERE kind = 'seed_v1' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is not None:
        try:
            loaded_version = json.loads(row["payload"]).get("version")
            if loaded_version == expected.version:
                event = json.loads(row["payload"])
                if "fingerprint" in event:
                    if event["fingerprint"] != expected.fingerprint:
                        raise ValueError("Seed ID mapping or topology changed without a version change. Increment the seed version and migrate explicitly, or use a new database. Existing memory was not modified.")
                else:
                    # Legacy events have no baseline topology hash; verify identities without writing one.
                    for slug, node_id in expected.ids.items():
                        cell = store.cell(node_id)
                        if cell is None or KnowledgeNode.from_cell(cell).slug != slug:
                            raise ValueError("Legacy seed IDs do not match the configured seed. Use an explicit migration or a new database; existing memory was not modified.")
                return expected
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            pass
    raise ValueError("Existing memory does not match the configured seed version. Use a separate experimental database or an explicit migration; existing knowledge was not replaced.")


def knowledge_seed_from_file(path: str | Path) -> KnowledgeSeed:
    """Read the slug-to-ID map of a Phase 1 knowledge seed without writing to a store."""

    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return _seed_metadata(document)
