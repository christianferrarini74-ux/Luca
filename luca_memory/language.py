"""Small, explicit Italian interface for the first curriculum experiment."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .curriculum import Curriculum, cell_payload
from .store import MemoryStore


@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    trace: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Intent:
    subject: str
    predicate: str
    renderer: str


class ItalianSeedInterface:
    """Recognise a deliberately narrow, inspectable question grammar.

    This is not an LLM or a general language parser. It maps a handful of
    reviewed forms into cell addresses and renders answers only after the
    corresponding assertion cell has been recovered from Luca's graph.
    """

    _intents = {
        "come ti chiami": Intent("luca", "nome", "Mi chiamo {object}."),
        "chi e il tuo creatore": Intent("luca", "creatore", "Il mio creatore è {object}."),
        "cos e il fuoco": Intent("fuoco", "is", "Il fuoco è {object}."),
        "sai cos e il fuoco": Intent("fuoco", "is", "Il fuoco è {object}."),
        "cosa produce il fuoco": Intent("fuoco", "produce", "Il fuoco produce {object}."),
        "cosa fa il fuoco": Intent("fuoco", "produce", "Il fuoco produce {object}."),
    }

    def __init__(self, store: MemoryStore, curriculum: Curriculum) -> None:
        self.store = store
        self.curriculum = curriculum

    def answer(self, question: str) -> Answer:
        intent = self._intents.get(self._normalise(question))
        if intent is None:
            return Answer("Non conosco ancora questa forma di domanda.", ())
        subject_id = self.curriculum.id_for(intent.subject)
        predicate_id = self.curriculum.id_for(intent.predicate)
        for edge in self.store.outgoing(subject_id):
            assertion_id = edge.target_id
            assertion = cell_payload(self.store, assertion_id)
            if assertion.get("kind") != "assertion" or assertion.get("predicate_id") != predicate_id:
                continue
            object_id = int(assertion["object_id"])
            object_label = str(cell_payload(self.store, object_id)["label"])
            return Answer(intent.renderer.format(object=object_label), (subject_id, assertion_id, predicate_id, object_id))
        return Answer("Non possiedo ancora una risposta verificata.", (subject_id, predicate_id))

    @staticmethod
    def _normalise(text: str) -> str:
        lowered = text.lower().replace("è", "e")
        return re.sub(r"[^a-z0-9 ]+", "", lowered).strip()
