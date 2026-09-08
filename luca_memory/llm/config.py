"""Configuration resolution for Luca's provider-neutral LLM connector."""

from __future__ import annotations

from typing import Any

from .models import LLMCapabilities, LLMConfigurationError, LLMProfile


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _active_runtime(config: dict[str, Any]) -> dict[str, Any]:
    llm = _mapping(config.get("llm"))
    name = str(llm.get("active_runtime") or "").strip()
    runtime = _mapping(_mapping(llm.get("runtimes")).get(name))
    if not name or not runtime:
        raise LLMConfigurationError(
            "Configurazione LLM non valida: usare llm.active_runtime e llm.runtimes.<nome>."
        )
    return runtime


def resolve_llm_profile(config: dict[str, Any], assignment: str | None = None) -> LLMProfile:
    """Resolve a role directly to one provider and model."""

    runtime = _active_runtime(config)
    role = str(assignment or "orchestrator").strip() or "orchestrator"
    agents = _mapping(runtime.get("agents"))
    agent = _mapping(agents.get(role)) or _mapping(agents.get("orchestrator"))
    if not agent:
        raise LLMConfigurationError("Configurazione LLM incompleta: manca l'agente orchestrator.")

    provider_name = str(agent.get("provider") or "").strip()
    provider = _mapping(_mapping(runtime.get("providers")).get(provider_name))
    provider_kind = str(provider.get("kind") or "").strip().lower()
    model = str(agent.get("model") or "").strip()
    if not provider_name or not provider_kind or not model:
        raise LLMConfigurationError(f"Configurazione LLM incompleta per il ruolo '{role}'.")

    try:
        temperature = float(agent.get("temperature", 0.0))
        timeout = float(agent.get("timeout_seconds", provider.get("timeout_seconds", 30.0)))
    except (TypeError, ValueError) as error:
        raise LLMConfigurationError(f"Parametri numerici non validi per il ruolo '{role}'.") from error

    capabilities = _mapping(agent.get("capabilities"))
    return LLMProfile(
        name=role,
        provider_name=provider_name,
        provider_kind=provider_kind,
        model=model,
        temperature=temperature,
        timeout_seconds=timeout,
        capabilities=LLMCapabilities(
            structured_output=bool(capabilities.get("structured_output", False)),
            streaming=bool(capabilities.get("streaming", False)),
        ),
        provider_config=provider,
    )
