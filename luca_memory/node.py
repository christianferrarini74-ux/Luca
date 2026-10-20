"""Articulated knowledge nodes for Luca's Phase 1 synaptic memory."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re
import time
import unicodedata

from .store import Cell, MemoryStore


@dataclass(frozen=True, slots=True)
class KnowledgeSection:
    key: str
    title: str
    content: str


@dataclass(frozen=True, slots=True)
class KnowledgeNode:
    """A self-contained block of articulated knowledge stored in a Cell."""

    id: int
    slug: str
    title: str
    content: str
    keywords: tuple[str, ...] = ()
    created_at: int = 0
    last_recalled_at: int = 0
    recall_count: int = 0
    summary: str = ""
    sections: tuple[KnowledgeSection, ...] = ()
    content_complete: bool = True
    full_content_bytes: int = 0

    def to_cell(self) -> Cell:
        created = self.created_at or int(time.time())
        payload = {
            "kind": "knowledge",
            "slug": self.slug,
            "title": self.title,
            "content": self.content,
            "keywords": list(self.keywords),
            "created_at": created,
            "last_recalled_at": self.last_recalled_at,
            "recall_count": self.recall_count,
            "summary": self.summary,
            "sections": [{"key": section.key, "title": section.title, "content": section.content} for section in self.sections],
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return Cell(id=self.id, content=encoded, created_at=created)

    def with_recall(self, timestamp: int | None = None) -> "KnowledgeNode":
        now = int(time.time()) if timestamp is None else timestamp
        return replace(self, last_recalled_at=now, recall_count=self.recall_count + 1)

    @classmethod
    def from_cell(cls, cell: Cell) -> "KnowledgeNode":
        try:
            payload = json.loads(cell.content)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            text = cell.content.decode("utf-8", errors="replace")
            return cls(id=cell.id, slug=f"cell_{cell.id}", title=f"Cell {cell.id}", content=text, created_at=cell.created_at)

        if not isinstance(payload, dict):
            return cls(id=cell.id, slug=f"cell_{cell.id}", title=f"Cell {cell.id}", content=str(payload), created_at=cell.created_at)

        if payload.get("kind") == "knowledge":
            raw_keywords = payload.get("keywords", [])
            keywords = tuple(str(k) for k in raw_keywords) if isinstance(raw_keywords, list) else ()
            return cls(
                id=cell.id,
                slug=str(payload.get("slug") or f"cell_{cell.id}"),
                title=str(payload.get("title") or payload.get("slug") or f"Cell {cell.id}"),
                content=str(payload.get("content") or ""),
                keywords=keywords,
                created_at=int(payload.get("created_at") or cell.created_at),
                last_recalled_at=int(payload.get("last_recalled_at") or 0),
                recall_count=int(payload.get("recall_count") or 0),
                summary=str(payload.get("summary") or ""),
                sections=tuple(KnowledgeSection(str(s["key"]), str(s.get("title") or s["key"]), str(s.get("content") or ""))
                               for s in payload.get("sections", []) if isinstance(s, dict) and s.get("key")),
            )

        # Fallback for Phase 0 legacy cells
        label = str(payload.get("label") or payload.get("text") or f"cell_{cell.id}")
        forms = payload.get("forms", [])
        keywords = tuple(str(f) for f in forms) if isinstance(forms, list) else ()
        return cls(
            id=cell.id,
            slug=normalise_key(label) or f"cell_{cell.id}",
            title=label,
            content=label,
            keywords=keywords,
            created_at=cell.created_at,
        )


def normalise_key(value: str) -> str:
    lowered = "".join(ch for ch in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(ch)).strip()
    return re.sub(r"\s+", " ", lowered)


def save_node(store: MemoryStore, node: KnowledgeNode) -> None:
    """Insert or update a KnowledgeNode and register its slug and keyword aliases."""

    if not node.content_complete:
        raise ValueError("A partial cache view cannot overwrite durable knowledge.")
    with store.transaction():
        store.upsert_cell(node.to_cell())
        store.connection.execute("""DELETE FROM cell_aliases WHERE cell_id=? AND alias IN
            (SELECT alias FROM managed_aliases WHERE node_id=?)""", (node.id, node.id))
        store.connection.execute("DELETE FROM managed_aliases WHERE node_id=?", (node.id,))
        for alias in {normalise_key(value) for value in (node.slug, node.title, *node.keywords)} - {""}:
            store.add_alias(alias, node.id)
            store.connection.execute("INSERT INTO managed_aliases VALUES (?, ?)", (node.id, alias))


def load_node(store: MemoryStore, cell_id: int) -> KnowledgeNode | None:
    """Load a cell from the store and decode it as a KnowledgeNode."""

    with store.lock:
        cell = store.cell(cell_id)
        if cell is None:
            return None
        node = KnowledgeNode.from_cell(cell)
        usage = store.node_usage(cell_id)
        return replace(node, recall_count=usage[0], last_recalled_at=usage[1]) if usage else node
