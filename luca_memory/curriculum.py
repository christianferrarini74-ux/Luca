"""Auditable curriculum loading for Luca's initial knowledge."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time

from .store import Cell, Edge, MemoryStore


@dataclass(frozen=True, slots=True)
class Curriculum:
    version: str
    language: str
    ids: dict[str, int]

    def id_for(self, slug: str) -> int:
        return self.ids[slug]


def load_curriculum(store: MemoryStore, path: str | Path) -> Curriculum:
    """Load a reviewed curriculum into an empty store.

    The file contains every cell and address explicitly. Assertions are cells;
    their subject, predicate and object are cell addresses stored in the
    assertion cell itself. Edges remain semantic-free navigation paths.
    """
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    cells = document["cells"]
    ids = {item["slug"]: number for number, item in enumerate(cells, start=1)}
    created_at = int(time.time())

    with store.transaction():
        for item in cells:
            payload = dict(item)
            payload.pop("slug")
            if payload.get("kind") == "assertion":
                payload["subject_id"] = ids[payload.pop("subject")]
                payload["predicate_id"] = ids[payload.pop("predicate")]
                payload["object_id"] = ids[payload.pop("object")]
            store.add_cell(Cell(ids[item["slug"]], json.dumps(payload, ensure_ascii=False, sort_keys=True).encode(), created_at))
            if item.get("kind") == "concept":
                store.add_alias(item["slug"], ids[item["slug"]])
                for form in item.get("forms", []):
                    store.add_alias(form, ids[item["slug"]])

        for item in cells:
            if item.get("kind") != "assertion":
                continue
            assertion_id = ids[item["slug"]]
            subject_id = ids[item["subject"]]
            predicate_id = ids[item["predicate"]]
            object_id = ids[item["object"]]
            addresses = {
                (subject_id, assertion_id),
                (assertion_id, predicate_id),
                (assertion_id, object_id),
            }
            for source_id, target_id in sorted(addresses):
                store.add_edge(Edge(source_id, target_id))

    return Curriculum(document["version"], document["language"], ids)


def curriculum_from_file(path: str | Path) -> Curriculum:
    """Read the stable ID map of a curriculum without writing to a store."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = {item["slug"]: number for number, item in enumerate(document["cells"], start=1)}
    return Curriculum(document["version"], document["language"], ids)


def cell_payload(store: MemoryStore, cell_id: int) -> dict[str, object]:
    cell = store.cell(cell_id)
    if cell is None:
        raise KeyError(f"Unknown cell: {cell_id}")
    return json.loads(cell.content)
