"""Neutral models used by Luca's LLM connector."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMCapabilities:
    """Capabilities declared by a provider profile."""

    structured_output: bool = False
    streaming: bool = False


@dataclass(frozen=True, slots=True)
class LLMProfile:
    """A provider, model and its invocation settings."""

    name: str
    provider_name: str
    provider_kind: str
    model: str
    temperature: float = 0.0
    timeout_seconds: float = 30.0
    capabilities: LLMCapabilities = field(default_factory=LLMCapabilities)
    provider_config: dict[str, Any] = field(default_factory=dict)
    generation: dict[str, Any] = field(default_factory=dict)


class LLMConfigurationError(ValueError):
    """Raised when the active LLM configuration is incomplete or invalid."""
