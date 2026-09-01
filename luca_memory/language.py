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
    subject: str | int
    predicate: str | int
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
        normalised = self._normalise(question)
        intent = self._intents.get(normalised) or self._object_question(normalised)
        if intent is None:
            return Answer("Non conosco ancora questa forma di domanda.", ())
        subject_id = self._id_for(intent.subject)
        predicate_id = self._id_for(intent.predicate)
        matches: list[tuple[int, int, str]] = []
        for edge in self.store.outgoing(subject_id):
            assertion_id = edge.target_id
            assertion = cell_payload(self.store, assertion_id)
            if assertion.get("kind") != "assertion" or assertion.get("predicate_id") != predicate_id:
                continue
            object_id = int(assertion["object_id"])
            object_label = str(cell_payload(self.store, object_id)["label"])
            matches.append((assertion_id, object_id, object_label))
        if not matches:
            return Answer("Non possiedo ancora una risposta verificata.", (subject_id, predicate_id))
        subject_label = str(cell_payload(self.store, subject_id)["label"])
        predicate_label = str(cell_payload(self.store, predicate_id)["label"])
        objects = self._italian_list([match[2] for match in matches])
        trace = [subject_id]
        for assertion_id, object_id, _ in matches:
            trace.extend((assertion_id, predicate_id, object_id))
        return Answer(intent.renderer.format(subject=subject_label, predicate=predicate_label, object=objects), tuple(trace))

    def _object_question(self, normalised: str) -> Intent | None:
        """Interpret ``Cosa <predicato> il <soggetto>?`` from known cell forms."""
        match = re.fullmatch(r"cosa (scalda|raffredda|bagna|produce) il (.+)", normalised)
        if match is None:
            return None
        predicate_form, subject_form = match.groups()
        subject = self._concept_for_form(subject_form)
        predicate = self._concept_for_form(predicate_form)
        if subject is None or predicate is None:
            return None
        return Intent(subject, predicate, "Il {subject} {predicate} {object}.")

    def _concept_for_form(self, form: str) -> int | None:
        cell = self.store.cell_by_alias(form)
        if cell is None or cell_payload(self.store, cell.id).get("kind") != "concept":
            return None
        return cell.id

    def _id_for(self, reference: str | int) -> int:
        return reference if isinstance(reference, int) else self.curriculum.id_for(reference)

    @staticmethod
    def _italian_list(values: list[str]) -> str:
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return f"{values[0]} e {values[1]}"
        return ", ".join(values[:-1]) + f" e {values[-1]}"

    @staticmethod
    def _normalise(text: str) -> str:
        lowered = text.lower().replace("è", "e")
        return re.sub(r"[^a-z0-9 ]+", "", lowered).strip()
