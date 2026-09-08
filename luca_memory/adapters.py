"""Language adapters. The current rule adapter is the reference contract."""

from __future__ import annotations

import json
from typing import Any, Protocol
import re

from .llm import LLMConfigurationError, LLMConnector
from .protocol import LanguageIntent


class LanguageAdapter(Protocol):
    def interpret(self, text: str, current_subject: str | None = None) -> LanguageIntent: ...


class LanguageAdapterUnavailable(RuntimeError):
    """The optional local language service cannot currently be reached."""


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


class LMStudioAdapter:
    """Local, optional interpreter served by LM Studio's OpenAI-compatible API."""

    DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1"
    DEFAULT_MODEL = "gemma-3-1B-it-QAT-GGUF"
    _KINDS = {"greet", "ask", "describe", "remember", "unknown"}

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout_seconds: float = 30.0,
        *,
        connector: LLMConnector | None = None,
        assignment: str = "orchestrator",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.connector = connector or LLMConnector(
            {
                "llm": {
                    "active_runtime": "local",
                    "runtimes": {
                        "local": {
                            "providers": {
                                "lm_studio": {
                                    "kind": "openai_compatible",
                                    "base_url": self.base_url,
                                }
                            },
                            "agents": {
                                "orchestrator": {
                                    "provider": "lm_studio",
                                    "model": self.model,
                                    "timeout_seconds": self.timeout_seconds,
                                }
                            },
                        }
                    },
                }
            }
        )
        self.assignment = assignment

    @classmethod
    def from_config(cls, config: dict[str, Any], assignment: str = "orchestrator") -> "LMStudioAdapter":
        """Build the adapter from the active LLM runtime in config.yaml."""

        connector = LLMConnector(config)
        profile = connector.profile_for(assignment)
        if profile.provider_kind != "openai_compatible":
            raise LLMConfigurationError(
                "The selected Luca language adapter requires an openai_compatible provider."
            )
        base_url = str(profile.provider_config.get("base_url") or "").strip()
        if not base_url:
            raise LLMConfigurationError("The selected LLM provider does not define base_url.")
        return cls(
            base_url=base_url,
            model=profile.model,
            timeout_seconds=profile.timeout_seconds,
            connector=connector,
            assignment=assignment,
        )

    def interpret(self, text: str, current_subject: str | None = None) -> LanguageIntent:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._system_instruction(current_subject)},
                {"role": "user", "content": text},
            ],
            "temperature": 0,
            "max_tokens": 160,
            "stream": False,
            "response_format": self._response_format(),
        }
        try:
            content = self.connector.create_chat_model(self.assignment).complete(
                payload["messages"],
                response_format=payload["response_format"],
                max_tokens=payload["max_tokens"],
            )
            decoded = json.loads(content)
        except (LLMConfigurationError, TypeError, json.JSONDecodeError) as error:
            raise LanguageAdapterUnavailable("LM Studio returned an invalid language intent.") from error
        return self._intent_from_json(decoded, text)

    @classmethod
    def _intent_from_json(cls, value: object, original_text: str) -> LanguageIntent:
        if not isinstance(value, dict):
            raise LanguageAdapterUnavailable("LM Studio did not return a JSON object.")
        kind = value.get("kind")
        if kind not in cls._KINDS:
            raise LanguageAdapterUnavailable("LM Studio returned an unsupported intent kind.")
        subject = cls._label(value.get("subject"))
        predicate = cls._label(value.get("predicate"))
        objects_value = value.get("objects", [])
        if not isinstance(objects_value, list):
            raise LanguageAdapterUnavailable("LM Studio returned invalid intent objects.")
        objects = tuple(label for item in objects_value if (label := cls._label(item)))
        question = cls._text(value.get("question"))
        confidence = value.get("confidence", 0.0)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            confidence = 0.0
        ambiguity = cls._text(value.get("ambiguity"))
        if kind == "remember" and (not subject or not predicate or not objects):
            raise LanguageAdapterUnavailable("LM Studio proposed an incomplete lesson; nothing was stored.")
        return LanguageIntent(kind, original_text, subject, predicate, objects, question, float(confidence), ambiguity)

    @staticmethod
    def _label(value: object) -> str | None:
        text = LMStudioAdapter._text(value)
        if text is None or not re.fullmatch(r"[a-zàèéìòóù0-9 ]{1,80}", text.lower()):
            return None
        return text.lower()

    @staticmethod
    def _text(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _system_instruction(current_subject: str | None) -> str:
        context = current_subject or "nessuno"
        return (
            "Sei l'interprete linguistico locale di Luca, non la sua memoria. "
            "Rispondi esclusivamente con JSON conforme allo schema. Non aggiungere fatti. "
            "Estrai una lezione solo se l'utente dice chiaramente 'Luca, ricorda ...'. "
            "Normalizza soggetto, predicato e oggetti in italiano minuscolo, senza articoli. "
            f"Il soggetto conversazionale corrente e: {context}."
        )

    @staticmethod
    def _response_format() -> dict[str, object]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "luca_language_intent",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["greet", "ask", "describe", "remember", "unknown"]},
                        "subject": {"type": ["string", "null"]},
                        "predicate": {"type": ["string", "null"]},
                        "objects": {"type": "array", "items": {"type": "string"}},
                        "question": {"type": ["string", "null"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "ambiguity": {"type": ["string", "null"]},
                    },
                    "required": ["kind", "subject", "predicate", "objects", "question", "confidence", "ambiguity"],
                    "additionalProperties": False,
                },
            },
        }
