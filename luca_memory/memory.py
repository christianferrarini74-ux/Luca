"""Controlled writes to Luca's durable cell-and-address memory."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time

from .curriculum import cell_payload
from .protocol import MemoryProposal
from .store import Cell, Edge, MemoryStore


@dataclass(frozen=True, slots=True)
class RememberedAssertion:
    assertion_id: int
    subject_id: int
    predicate_id: int
    object_id: int
    created: bool


class MemoryEditor:
    """Create concepts and assertions while preserving an append-only history."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def remember(self, subject: str, predicate: str, object_: str, source: str = "user") -> RememberedAssertion:
        with self.store.transaction():
            subject_id = self._ensure_concept(subject)
            predicate_id = self._ensure_concept(predicate)
            object_id = self._ensure_concept(object_)
            existing = self._find_assertion(subject_id, predicate_id, object_id)
            now = int(time.time())
            if existing is not None:
                self.store.record_event("reaffirm", self._event_payload(existing, source), now)
                return RememberedAssertion(existing, subject_id, predicate_id, object_id, False)

            assertion_id = self.store.next_cell_id()
            payload = {
                "kind": "assertion",
                "subject_id": subject_id,
                "predicate_id": predicate_id,
                "object_id": object_id,
                "provenance": source,
                "created_at": now,
            }
            self.store.add_cell(Cell(assertion_id, json.dumps(payload, ensure_ascii=False, sort_keys=True).encode(), now))
            for source_id, target_id in sorted({(subject_id, assertion_id), (assertion_id, predicate_id), (assertion_id, object_id)}):
                self.store.add_edge(Edge(source_id, target_id))
            self.store.record_event("remember", self._event_payload(assertion_id, source), now)
        return RememberedAssertion(assertion_id, subject_id, predicate_id, object_id, True)

    def consolidate(self, proposal: MemoryProposal) -> tuple[RememberedAssertion, ...]:
        """Apply an adapter proposal only through the Core's write path."""
        intent = proposal.intent
        if intent.kind != "remember" or not intent.subject or not intent.predicate:
            raise ValueError("Unsupported memory proposal.")
        return tuple(self.remember(intent.subject, intent.predicate, object_, proposal.source) for object_ in intent.objects)

    def facts_about(self, subject_id: int) -> list[RememberedAssertion]:
        facts = []
        for edge in self.store.outgoing(subject_id):
            payload = cell_payload(self.store, edge.target_id)
            if payload.get("kind") == "assertion" and payload.get("subject_id") == subject_id:
                facts.append(
                    RememberedAssertion(
                        edge.target_id,
                        subject_id,
                        int(payload["predicate_id"]),
                        int(payload["object_id"]),
                        False,
                    )
                )
        return facts

    def _ensure_concept(self, label: str) -> int:
        alias = self._normalise(label)
        existing = self.store.cell_by_alias(alias)
        if existing is not None:
            return existing.id
        now = int(time.time())
        cell_id = self.store.next_cell_id()
        payload = {"kind": "concept", "label": alias, "forms": [alias], "created_at": now}
        self.store.add_cell(Cell(cell_id, json.dumps(payload, ensure_ascii=False, sort_keys=True).encode(), now))
        self.store.add_alias(alias, cell_id)
        self.store.record_event("concept", json.dumps({"cell_id": cell_id, "label": alias}).encode(), now)
        return cell_id

    def _find_assertion(self, subject_id: int, predicate_id: int, object_id: int) -> int | None:
        for fact in self.facts_about(subject_id):
            if fact.predicate_id == predicate_id and fact.object_id == object_id:
                return fact.assertion_id
        return None

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().replace("è", "e").strip())

    @staticmethod
    def _event_payload(assertion_id: int, source: str) -> bytes:
        return json.dumps({"assertion_id": assertion_id, "source": source}).encode()
