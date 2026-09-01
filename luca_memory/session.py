"""A small persistent conversational shell over Luca's native memory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .curriculum import cell_payload, curriculum_from_file, load_curriculum
from .language import ItalianSeedInterface
from .memory import MemoryEditor
from .store import MemoryStore


@dataclass(frozen=True, slots=True)
class SessionReply:
    text: str
    trace: tuple[int, ...] = ()


class LucaSession:
    """Maintains only a small ephemeral dialogue state; knowledge stays on disk."""

    def __init__(self, store: MemoryStore, seed_path: str | Path) -> None:
        self.store = store
        self.curriculum = curriculum_from_file(seed_path)
        self.language = ItalianSeedInterface(store, self.curriculum)
        self.editor = MemoryEditor(store)
        self.current_subject_id: int | None = None

    @classmethod
    def open(cls, database: str | Path, seed_path: str | Path) -> "LucaSession":
        store = MemoryStore(database)
        if not store.has_cells():
            load_curriculum(store, seed_path)
        return cls(store, seed_path)

    def close(self) -> None:
        self.store.close()

    def handle(self, text: str) -> SessionReply:
        normalised = self._normalise(text)
        if normalised in {"ciao", "ciao luca", "buongiorno luca"}:
            return SessionReply("Ciao Christian. Sono Luca.")

        lesson = self._parse_lesson(normalised)
        if lesson is not None:
            subject, predicate, object_ = lesson
            remembered = self.editor.remember(subject, predicate, object_)
            self.current_subject_id = remembered.subject_id
            detail = "Ho già questa conoscenza." if not remembered.created else "Ho registrato la conoscenza."
            return SessionReply(detail, (remembered.subject_id, remembered.assertion_id, remembered.predicate_id, remembered.object_id))

        if normalised.startswith("parlami del ") or normalised.startswith("parlami di "):
            subject_form = normalised.removeprefix("parlami del ").removeprefix("parlami di ")
            subject = self.store.cell_by_alias(subject_form)
            if subject is None:
                return SessionReply("Non possiedo ancora conoscenze su questo argomento.")
            self.current_subject_id = subject.id
            facts = self.editor.facts_about(subject.id)
            if not facts:
                return SessionReply("Non possiedo ancora una risposta verificata.", (subject.id,))
            phrases = []
            trace = [subject.id]
            for fact in facts:
                predicate = str(cell_payload(self.store, fact.predicate_id)["label"])
                object_label = str(cell_payload(self.store, fact.object_id)["label"])
                phrases.append(f"{predicate} {object_label}")
                trace.extend((fact.assertion_id, fact.predicate_id, fact.object_id))
            label = str(cell_payload(self.store, subject.id)["label"])
            return SessionReply(f"So che {label} " + " e ".join(phrases) + ".", tuple(trace))

        if normalised in {"e cosa produce", "e cosa produce il"} and self.current_subject_id is not None:
            subject = str(cell_payload(self.store, self.current_subject_id)["label"])
            return self._answer(f"cosa produce il {subject}")

        return self._answer(normalised)

    def _answer(self, question: str) -> SessionReply:
        answer = self.language.answer(question)
        if answer.trace:
            self.current_subject_id = answer.trace[0]
        return SessionReply(answer.text, answer.trace)

    @staticmethod
    def _parse_lesson(text: str) -> tuple[str, str, str] | None:
        match = re.fullmatch(
            r"(?:luca )?ricorda che (?:il |la |l )?(.+?) (scalda|produce|raffredda|bagna) (?:il |la |l |gli |le )?(.+)",
            text,
        )
        return match.groups() if match else None

    @staticmethod
    def _normalise(text: str) -> str:
        lowered = text.lower().replace("è", "e")
        return re.sub(r"[^a-z0-9 ]+", "", lowered).strip()
