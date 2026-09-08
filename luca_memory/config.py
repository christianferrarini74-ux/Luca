"""Load and validate Luca's single YAML runtime configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


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
    storage.setdefault("database", "luca.sqlite")
    storage.setdefault("seed", "seed/italian_base_v0.json")
    storage["database"] = str(_resolve_path(storage["database"], config_path.parent))
    storage["seed"] = str(_resolve_path(storage["seed"], config_path.parent))

    runtime = _mapping(config.setdefault("runtime", {}))
    config["runtime"] = runtime
    runtime.setdefault("language_adapter", "rules")
    runtime.setdefault("adapter_role", "orchestrator")
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
    return config


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resolve_path(value: Any, base: Path) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else base / path
