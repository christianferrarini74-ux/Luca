"""Language adapters. The current rule adapter is the reference contract."""

from __future__ import annotations

from typing import Protocol
import re

from .protocol import LanguageIntent


class LanguageAdapter(Protocol):
    def interpret(self, text: str, current_subject: str | None = None) -> LanguageIntent: ...


class RuleAdapter:
    """Small deterministic adapter that a future micro LLM must be able to replace."""

    def interpret(self, text: str, current_subject: str | None = None) -> LanguageIntent:
        normalised = self._normalise(text)
        if normalised in {"ciao", "ciao luca", "buongiorno luca"}:
            return LanguageIntent("greet", text)
        lesson = self._parse_lesson(normalised)
        if lesson is not None:
            subject, predicate, object_ = lesson
            return LanguageIntent("remember", text, subject, predicate, (object_,))
        if normalised.startswith("parlami del ") or normalised.startswith("parlami di "):
            subject = normalised.removeprefix("parlami del ").removeprefix("parlami di ")
            return LanguageIntent("describe", text, subject=subject)
        if normalised in {"e cosa produce", "e cosa produce il"} and current_subject:
            return LanguageIntent("ask", text, subject=current_subject, predicate="produce", question=f"cosa produce il {current_subject}")
        if normalised:
            return LanguageIntent("ask", text, question=normalised)
        return LanguageIntent("unknown", text)

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
