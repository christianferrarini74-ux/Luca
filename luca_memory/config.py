"""Load and validate Luca's single YAML runtime configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from .budget import PromptBudget
from .synaptic_settings import SynapticSettings


class ConfigurationError(ValueError):
    """Raised when config.yaml is missing or does not describe a usable runtime."""


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Load config.yaml and resolve its project-relative paths."""

    config_path = Path(path).resolve()
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}
    if not isinstance(config, dict):
        raise ConfigurationError("The root of config.yaml must be a mapping.")

    storage = _mapping(config.setdefault("storage", {}))
    config["storage"] = storage
    storage_directory = storage.get("directory")
    if storage_directory is not None:
        storage_directory = _resolve_path(storage_directory, config_path.parent)
        storage["directory"] = str(storage_directory)

    storage.setdefault("database", "luca.sqlite")
    storage.setdefault("seed", "seed/italian_base_v0.json")
    database_base = storage_directory or config_path.parent
    storage["database"] = str(_resolve_path(storage["database"], database_base))
    storage["seed"] = str(_resolve_path(storage["seed"], config_path.parent))

    runtime = _mapping(config.setdefault("runtime", {}))
    config["runtime"] = runtime
    runtime.setdefault("language_adapter", "rules")
    runtime.setdefault("adapter_role", "orchestrator")
    runtime.setdefault("memory_search_policy", "fast")
    runtime.setdefault("memory_planner", "hybrid")
    runtime.setdefault("memory_policy", "grounded")
    runtime.setdefault("memory_backend", "host")
    runtime.setdefault("gpu_device", 0)
    if runtime["memory_backend"] not in {"host", "cuda"}:
        raise ConfigurationError("runtime.memory_backend must be 'host' or 'cuda'.")
    if isinstance(runtime["gpu_device"], bool) or not isinstance(runtime["gpu_device"], int) or runtime["gpu_device"] < 0:
        raise ConfigurationError("runtime.gpu_device must be a non-negative integer.")
    if runtime["memory_policy"] not in {"grounded", "experimental"}:
        raise ConfigurationError("runtime.memory_policy must be 'grounded' or 'experimental'.")
    try:
        PromptBudget.from_config(runtime)
        SynapticSettings.from_config(runtime)
        for key, minimum, default in (("vram_bytes", 2048, 8_000_000), ("ram_bytes", 2048, 32_000_000), ("recent_window", 1, 8)):
            runtime[key] = int(runtime.get(key, default))
            if runtime[key] < minimum:
                raise ValueError(f"{key} must be at least {minimum}.")
    except (ValueError, TypeError) as error:
        raise ConfigurationError(str(error)) from error
    if runtime["memory_planner"] not in {"rules", "hybrid", "llm"}:
        raise ConfigurationError("runtime.memory_planner must be 'rules', 'hybrid' or 'llm'.")
    if runtime["memory_search_policy"] not in {"fast", "complete"}:
        raise ConfigurationError("runtime.memory_search_policy must be 'fast' or 'complete'.")
    if runtime["language_adapter"] not in {"rules", "gemma"}:
        raise ConfigurationError("runtime.language_adapter must be 'rules' or 'gemma'.")

    api = _mapping(runtime.setdefault("api", {}))
    runtime["api"] = api
    api.setdefault("host", "127.0.0.1")
    api.setdefault("port", 8765)
    try:
        api["port"] = int(api["port"])
    except (TypeError, ValueError) as error:
        raise ConfigurationError("runtime.api.port must be an integer.") from error

    frontend = _mapping(config.setdefault("frontend", {}))
    config["frontend"] = frontend
    frontend.setdefault("enabled", True)
    # The cockpit is bundled and served by the same Python HTTP server.
    for obsolete in ("directory", "url", "api_url"):
        frontend.pop(obsolete, None)
    return config


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resolve_path(value: Any, base: Path) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else base / path
