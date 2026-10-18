"""Articulated knowledge nodes for Luca's Phase 1 synaptic memory."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time
import unicodedata

from .store import Cell, MemoryStore


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
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return Cell(id=self.id, content=encoded, created_at=created)

    def with_recall(self, timestamp: int | None = None) -> "KnowledgeNode":
        now = int(time.time()) if timestamp is None else timestamp
        return KnowledgeNode(
            id=self.id,
            slug=self.slug,
            title=self.title,
            content=self.content,
            keywords=self.keywords,
            created_at=self.created_at,
            last_recalled_at=now,
            recall_count=self.recall_count + 1,
        )

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

    cell = node.to_cell()
    store.upsert_cell(cell)
    if node.slug:
        store.add_alias(normalise_key(node.slug), node.id)
    if node.title:
        store.add_alias(normalise_key(node.title), node.id)
    for keyword in node.keywords:
        normalised = normalise_key(keyword)
        if normalised:
            store.add_alias(normalised, node.id)


def load_node(store: MemoryStore, cell_id: int) -> KnowledgeNode | None:
    """Load a cell from the store and decode it as a KnowledgeNode."""

    cell = store.cell(cell_id)
    return KnowledgeNode.from_cell(cell) if cell is not None else None
