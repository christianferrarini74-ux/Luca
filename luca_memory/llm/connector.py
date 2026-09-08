"""Single entry point between Luca and configurable LLM providers."""

from __future__ import annotations

from typing import Any

from .config import resolve_llm_profile
from .models import LLMProfile
from .providers import ChatModel, create_provider


class LLMConnector:
    """Resolve a role and create its provider client without leaking provider details."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def profile_for(self, assignment: str | None = None) -> LLMProfile:
        return resolve_llm_profile(self.config, assignment)

    def create_chat_model(self, assignment: str | None = None) -> ChatModel:
        profile = self.profile_for(assignment)
        return create_provider(profile.provider_kind).create_chat_model(profile)
