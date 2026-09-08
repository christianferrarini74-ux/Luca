"""A small persistent conversational shell over Luca's native memory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .curriculum import cell_payload, curriculum_from_file, load_curriculum
from .adapters import LanguageAdapter, RuleAdapter
from .language import ItalianSeedInterface
from .memory import MemoryEditor
from .search import MemorySearch
from .store import MemoryStore
from .protocol import EvidenceBundle, LanguageIntent


@dataclass(frozen=True, slots=True)
class SessionReply:
    text: str
    trace: tuple[int, ...] = ()


class LucaSession:
    """Maintains only a small ephemeral dialogue state; knowledge stays on disk."""

    def __init__(self, store: MemoryStore, seed_path: str | Path, adapter: LanguageAdapter | None = None) -> None:
        self.store = store
        self.curriculum = curriculum_from_file(seed_path)
        self.language = ItalianSeedInterface(store, self.curriculum)
        self.editor = MemoryEditor(store)
        self.search = MemorySearch(store)
        self.adapter = adapter or RuleAdapter()
        self.current_subject_id: int | None = None
        self.history: list[dict[str, str]] = []

    @classmethod
    def open(cls, database: str | Path, seed_path: str | Path, adapter: LanguageAdapter | None = None) -> "LucaSession":
        store = MemoryStore(database)
        if not store.has_cells():
            load_curriculum(store, seed_path)
        return cls(store, seed_path, adapter)

    def close(self) -> None:
        self.store.close()

    def handle(self, text: str) -> SessionReply:
        current_subject = self._current_subject_label()
        intent = self.adapter.interpret(text, current_subject)
        if hasattr(self.adapter, "respond"):
            trace = self._consolidate_intent(intent)
            response = self.adapter.respond(text, self._memory_context(text, intent), self.history)
            self.history.extend(({"role": "user", "content": text}, {"role": "assistant", "content": response}))
            return SessionReply(response, trace)
        if intent.kind == "greet":
            return SessionReply("Ciao Christian. Sono Luca.")
        if intent.kind == "remember":
            remembered = self.editor.consolidate(intent.proposal())
            first = remembered[0]
            self.current_subject_id = first.subject_id
            detail = "Ho già questa conoscenza." if all(not item.created for item in remembered) else "Ho registrato la conoscenza."
            trace = tuple(value for item in remembered for value in (item.subject_id, item.assertion_id, item.predicate_id, item.object_id))
            return SessionReply(detail, trace)

        if intent.kind == "describe" and intent.subject:
            subject = self.store.cell_by_alias(intent.subject)
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

        return self._answer(intent.question or text)

    def _consolidate_intent(self, intent: object) -> tuple[int, ...]:
        if not isinstance(intent, LanguageIntent) or intent.kind != "remember":
            return ()
        remembered = self.editor.consolidate(intent.proposal())
        self.current_subject_id = remembered[0].subject_id
        return tuple(value for item in remembered for value in (item.subject_id, item.assertion_id, item.predicate_id, item.object_id))

    def _memory_context(self, text: str, intent: LanguageIntent | None = None) -> str:
        lines: list[str] = []
        seen: set[int] = set()
        sources = [text]
        if intent:
            sources.extend(value for value in (intent.subject, intent.question) if value)
        stopwords = {"a", "al", "alla", "che", "cosa", "del", "di", "e", "il", "la", "lo", "parlami", "produce"}
        queries = [
            token
            for source in sources
            for token in re.findall(r"[a-zàèéìòóù0-9]+", source.lower())
            if len(token) > 2 and token not in stopwords
        ]
        queries = list(dict.fromkeys(queries))
        for query in queries:
            for result in self.search.cells_by_text(query, kind="concept", limit=8):
                if result.cell.id in seen:
                    continue
                seen.add(result.cell.id)
                label = str(cell_payload(self.store, result.cell.id).get("label") or result.cell.id)
                facts = self.editor.facts_about(result.cell.id)
                if not facts:
                    lines.append(f"- concept: {label}")
                    continue
                for fact in facts:
                    predicate = str(cell_payload(self.store, fact.predicate_id).get("label") or "?")
                    object_label = str(cell_payload(self.store, fact.object_id).get("label") or "?")
                    lines.append(f"- {label} {predicate} {object_label} (assertion {fact.assertion_id})")
        return "\n".join(lines) if lines else "(nessun ricordo locale direttamente collegato alla richiesta)"

    def _answer(self, question: str) -> SessionReply:
        answer = self.language.answer(question)
        if answer.trace:
            self.current_subject_id = answer.trace[0]
        bundle = EvidenceBundle(answer.text, answer.trace, answer.trace[1::3] if answer.trace else ())
        return SessionReply(bundle.text, bundle.trace)

    def _current_subject_label(self) -> str | None:
        if self.current_subject_id is None:
            return None
        return str(cell_payload(self.store, self.current_subject_id)["label"])
