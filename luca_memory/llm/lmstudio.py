"""LM Studio model discovery and lifecycle management."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import LLMConfigurationError


class LMStudioModelManager:
    """Ensure that the model selected by Luca is loaded in LM Studio."""

    def __init__(self, management_url: str, timeout_seconds: float = 30.0, api_key: str = "") -> None:
        self.management_url = management_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key

    @classmethod
    def from_provider_config(cls, provider_config: dict[str, Any], timeout_seconds: float) -> "LMStudioModelManager":
        base_url = str(provider_config.get("base_url") or "").strip().rstrip("/")
        if not base_url:
            raise LLMConfigurationError("LM Studio non definisce base_url.")
        management_url = str(provider_config.get("management_url") or "").strip().rstrip("/")
        if not management_url:
            management_url = base_url[:-3] if base_url.endswith("/v1") else base_url
        api_key = str(provider_config.get("api_key") or "").strip()
        api_key_env = str(provider_config.get("api_key_env") or "").strip()
        if not api_key and api_key_env:
            api_key = os.getenv(api_key_env, "")
        return cls(management_url, timeout_seconds, api_key)

    def ensure_loaded(self, model_key: str, *, context_length: int | None = None, _allow_load: bool = True) -> None:
        """Load the configured model when it is installed but not resident."""

        try:
            available = self._request("GET", "/api/v1/models")
        except LLMConfigurationError as error:
            raise LLMConfigurationError(
                "LM Studio non è raggiungibile. Avvia il server locale prima di avviare Luca."
            ) from error
        models = available.get("models") or available.get("data") or []
        if not isinstance(models, list):
            raise LLMConfigurationError("LM Studio ha restituito un elenco modelli non valido.")
        selected = next(
            (item for item in models if isinstance(item, dict) and str(item.get("key") or item.get("id")) == model_key),
            None,
        )
        if selected is None:
            choices = ", ".join(
                str(item.get("key") or item.get("id"))
                for item in models
                if isinstance(item, dict) and (item.get("key") or item.get("id"))
            )
            raise LLMConfigurationError(
                f"Il modello LM Studio '{model_key}' non è installato. Modelli disponibili: {choices or 'nessuno'}."
            )
        loaded_instances = selected.get("loaded_instances") or []
        if context_length and int(selected.get("max_context_length") or 0) < context_length:
            raise LLMConfigurationError(f"Il modello '{model_key}' non supporta il contesto richiesto di {context_length} token.")
        if isinstance(loaded_instances, list) and loaded_instances:
            if context_length and not any(int(item.get("config", {}).get("context_length") or 0) >= context_length for item in loaded_instances):
                raise LLMConfigurationError(f"Ricarica '{model_key}' in LM Studio con almeno {context_length} token di contesto. Luca non scarica automaticamente modelli già in uso.")
            return
        if not _allow_load:
            raise LLMConfigurationError(f"LM Studio non ha confermato il caricamento di '{model_key}' con {context_length} token.")
        payload = {"model": model_key}
        if context_length:
            payload["context_length"] = context_length
        response = self._request("POST", "/api/v1/models/load", payload)
        if response.get("status") not in {None, "loaded"}:
            raise LLMConfigurationError(f"LM Studio non ha caricato il modello '{model_key}'.")
        if context_length:
            self.ensure_loaded(model_key, context_length=context_length, _allow_load=False)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            f"{self.management_url}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                decoded = json.loads(response.read().decode("utf-8"))
            if not isinstance(decoded, dict):
                raise LLMConfigurationError("LM Studio ha restituito una risposta non valida.")
            return decoded
        except (HTTPError, URLError, OSError, json.JSONDecodeError, TypeError) as error:
            raise LLMConfigurationError("LM Studio non ha completato la richiesta di gestione del modello.") from error
