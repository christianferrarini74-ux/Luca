"""Stable boundary between language adapters and Luca Core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


IntentKind = Literal["greet", "ask", "describe", "remember", "unknown"]


@dataclass(frozen=True, slots=True)
class LanguageIntent:
    """A model-independent interpretation of a user utterance."""

    kind: IntentKind
    original_text: str
    subject: str | None = None
    predicate: str | None = None
    objects: tuple[str, ...] = ()
    question: str | None = None
    confidence: float = 1.0
    ambiguity: str | None = None

    def proposal(self, source: str = "user") -> "MemoryProposal":
        if self.kind != "remember" or not self.subject or not self.predicate or not self.objects:
            raise ValueError("Only a complete remember intent can become a memory proposal.")
        return MemoryProposal(self, source)


@dataclass(frozen=True, slots=True)
class MemoryProposal:
    """A proposed durable change. Only Luca Core may consolidate it."""

    intent: LanguageIntent
    source: str
    requires_confirmation: bool = False


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    """Core-produced evidence that an adapter may render but not alter."""

    text: str
    trace: tuple[int, ...] = ()
    assertion_ids: tuple[int, ...] = ()
