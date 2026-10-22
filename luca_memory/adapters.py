"""Language adapters with one external instruction source and explicit runtime data."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Any, ClassVar, Protocol

from .bible import DEFAULT_BIBLE, read_bible
from .budget import PromptBudget
from .grouping_schema import grouping_schema, groups_from_assignments
from .llm import LLMConfigurationError, LLMConnector, LMStudioModelManager
from .navigation_schema import navigation_schema
from .protocol import LanguageIntent
from .synaptic_settings import SynapticSettings


class LanguageAdapter(Protocol):
    def interpret(self, text: str, current_subject: str | None = None) -> LanguageIntent: ...


class ConversationAdapter(LanguageAdapter, Protocol):
    """Language adapter that can generate a natural response with memory context."""

    def respond(
        self,
        text: str,
        memory_context: str,
        history: list[dict[str, str]],
    ) -> str: ...


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
        if normalised.startswith(("parlami del ", "parlami di ")):
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
    DEFAULT_MODEL = "google/gemma-3-1b"
    _KINDS: ClassVar[set[str]] = {"greet", "ask", "describe", "remember", "unknown"}

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
        self.prompt_budget = PromptBudget()
        self.last_prompt_report: dict[str, Any] = {}
        self.memory_policy = "grounded"
        self.bible_path = DEFAULT_BIBLE
        self.user_identity = None
        self.synaptic_settings = SynapticSettings()

    @classmethod
    def from_config(cls, config: dict[str, Any], assignment: str = "orchestrator") -> LMStudioAdapter:
        """Build the adapter from the active LLM runtime in config.yaml."""

        # Resolve one provider/model profile before acquiring a model or tokenizer.
        connector = LLMConnector(config)
        profile = connector.profile_for(assignment)
        if profile.provider_kind != "openai_compatible":
            raise LLMConfigurationError(
                "The selected Luca language adapter requires an openai_compatible provider."
            )
        base_url = str(profile.provider_config.get("base_url") or "").strip()
        if not base_url:
            raise LLMConfigurationError("The selected LLM provider does not define base_url.")
        adapter = cls(
            base_url=base_url,
            model=profile.model,
            timeout_seconds=profile.timeout_seconds,
            connector=connector,
            assignment=assignment,
        )
        adapter.bible_path = config.get("runtime", {}).get("bible", DEFAULT_BIBLE)
        adapter.user_identity = config.get("runtime", {}).get("user_identity")
        read_bible(adapter.bible_path)
        adapter.prompt_budget = PromptBudget.from_config(config.get("runtime", {}))
        manager = LMStudioModelManager.from_provider_config(profile.provider_config, profile.timeout_seconds)
        manager.ensure_loaded(adapter.model, context_length=adapter.prompt_budget.context_window if adapter.prompt_budget.unit == "tokens" else None)
        if adapter.prompt_budget.unit == "tokens":
            from .llm.tokenization import LMStudioTokenCounter
            counter = LMStudioTokenCounter(manager, adapter.model)
            counter.count("Luca")  # Validate tokenization at startup, not halfway through a turn.
            adapter.prompt_budget = replace(adapter.prompt_budget, counter=counter)
        adapter.memory_policy = str(config.get("runtime", {}).get("memory_policy", "grounded"))
        adapter.synaptic_settings = SynapticSettings.from_config(config.get("runtime", {}))
        return adapter

    def _request(self, operation, question, data, history=(), *, output_tokens=None):
        """Keep all instructions in the bible and all runtime facts in user data."""
        # Reload the sole instruction source; operation-specific reserves do not mutate defaults.
        budget = replace(self.prompt_budget, output_reserve=output_tokens) if output_tokens else self.prompt_budget
        payload = {"operation": operation, "question": question, "user_identity": self.user_identity, **data}
        messages, report = budget.messages(read_bible(self.bible_path), "", list(history),
                                           json.dumps(payload, ensure_ascii=False))
        report.update(instruction_source=str(self.bible_path), operation=operation)
        return messages, report

    def interpret(self, text, current_subject=None):
        """Validate proposed legacy lessons before the session can consolidate them."""
        messages, _ = self._request("interpret", text,
            {"current_subject": current_subject},
            output_tokens=self.synaptic_settings.interpretation_output_tokens)
        try:
            raw = self.connector.create_chat_model(self.assignment).complete(messages,
                response_format=self._response_format(),
                max_tokens=self.synaptic_settings.interpretation_output_tokens)
            return self._intent_from_json(json.loads(raw), text)
        except (LLMConfigurationError, TypeError, json.JSONDecodeError) as error:
            raise LanguageAdapterUnavailable("LM Studio returned an invalid language intent.") from error

    def propose_recall(self, text, focus, candidates, operation):
        """Offer a candidate ID; the planner still validates membership and relevance."""
        messages, _ = self._request("recall", text,
            {"focus": focus, "relation": operation, "candidates": candidates},
            output_tokens=self.synaptic_settings.recall_output_tokens)
        try:
            raw = self.connector.create_chat_model(self.assignment).complete(messages,
                response_format=self._json_schema("recall", {
                    "type": "object", "properties": {"target_id": {"type": ["integer", "null"]}},
                    "required": ["target_id"], "additionalProperties": False}),
                max_tokens=self.synaptic_settings.recall_output_tokens)
            value = json.loads(raw)
            return value if isinstance(value, dict) else {}
        except (LLMConfigurationError, ValueError, TypeError):
            return {}

    def respond_with_task(self, text, memory_context, history, task_context):
        return self.respond(text, memory_context, history, task_context=task_context)

    def navigate_memory(self, text, state, history):
        """Exchange structured routing data without adding hidden semantic instructions."""
        messages, report = self._request("navigate", text, {"state": state, "memory_scope": self.memory_policy}, history,
            output_tokens=self.synaptic_settings.navigation_output_tokens)
        memory = json.dumps(state.get("read_nodes", []), ensure_ascii=False)
        self.last_prompt_report = {**report, "memory_units": self.prompt_budget.count(memory),
                                  "memory_bytes": len(memory.encode("utf-8"))}
        try:
            model = self.connector.create_chat_model(self.assignment)
            raw = model.complete(messages, response_format=self._json_schema("memory_navigation", navigation_schema(state)),
                max_tokens=self.synaptic_settings.navigation_output_tokens)
            self._record_usage(model)
            value = json.loads(raw)
            return value if isinstance(value, dict) else {}
        except (LLMConfigurationError, ValueError, TypeError) as error:
            raise LanguageAdapterUnavailable(f"Memory navigation failed: {error}") from error

    def respond_with_navigation(self, text, memory_context, history, task_context):
        return self._respond(text, memory_context, history, task_context, bounded=True)

    def propose_groups(self, directory, settings):
        """Propose grouping assignments only; the Core owns validation and atomic writes."""
        if not any(len(getattr(directory, direction)) >= 2 for direction in ("incoming", "outgoing")):
            return []
        messages, _ = self._request("group", "", {"directory": directory.payload(),
            "constraints": {"edge_upper": settings.edge_upper, "edge_target": settings.edge_target,
                "degree_before": directory.external_degree, "min_members": 2,
                "max_members": min(settings.edge_upper - 1, max(2, directory.external_degree - settings.edge_target + 1)),
                "unique_members_per_direction": True,
                "required_reduction": max(0, directory.external_degree - settings.edge_target)}},
            output_tokens=settings.maintenance_output_tokens)
        try:
            raw = self.connector.create_chat_model(self.assignment).complete(messages,
                response_format=self._json_schema("memory_groups", grouping_schema(directory)),
                max_tokens=settings.maintenance_output_tokens)
            value = json.loads(raw)
            return groups_from_assignments(value, directory) if isinstance(value, dict) else None
        except (LLMConfigurationError, ValueError, TypeError) as error:
            raise LanguageAdapterUnavailable("Invalid LLM maintenance proposal; memory was not changed.") from error

    @staticmethod
    def _json_schema(name, schema):
        return {"type": "json_schema", "json_schema": {"name": name, "schema": schema}}

    def respond(self, text, memory_context, history, *, task_context=""):
        return self._respond(text, memory_context, history, task_context, bounded=False)

    def _respond(self, text, memory_context, history, task_context, *, bounded):
        """Share free response generation while preserving complete navigational readings."""
        budget = self.prompt_budget
        if budget.count(task_context) > budget.task_limit:
            raise ValueError("Task exceeds the configured task budget.")
        original = memory_context
        # Navigation already bounded its readings and reserved complete directories.
        if not bounded:
            memory_context = budget.truncate(memory_context, budget.memory_limit)
        messages, report = self._request("respond", text, {
            "memory": memory_context, "task": task_context, "memory_scope": self.memory_policy}, history)
        self.last_prompt_report = {**report, "memory_units": budget.count(memory_context),
            "memory_bytes": len(memory_context.encode("utf-8")), "memory_truncated": memory_context != original}
        try:
            model = self.connector.create_chat_model(self.assignment)
            response = model.complete(messages, max_tokens=budget.output_reserve)
            self._record_usage(model)
            return response
        except LLMConfigurationError as error:
            raise LanguageAdapterUnavailable("The model did not return a conversational response.") from error

    def _record_usage(self, model):
        """Compare provider usage with local counting without changing the generated answer."""
        usage = getattr(model, "last_usage", {})
        if isinstance(usage, dict):
            self.last_prompt_report.update({"server_" + key: value for key, value in usage.items()})
            if self.prompt_budget.unit == "tokens" and "prompt_tokens" in usage:
                self.last_prompt_report["template_token_delta"] = usage["prompt_tokens"] - self.last_prompt_report["input_tokens"]

    @classmethod
    def _intent_from_json(cls, value: object, original_text: str) -> LanguageIntent:
        """Reject malformed lessons rather than allowing partial writes into memory."""
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
    def _response_format() -> dict[str, object]:
        """Describe the legacy intent wire format, not extra model instructions."""
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
