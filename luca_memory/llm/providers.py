"""Small standard-library clients for LLM HTTP protocols."""

from __future__ import annotations

import json
import os
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import LLMConfigurationError, LLMProfile


class ChatModel(Protocol):
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
        **options: Any,
    ) -> str: ...


class _HTTPChatModel:
    def __init__(self, profile: LLMProfile, endpoint: str, api_key: str = "") -> None:
        self.profile = profile
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
        **options: Any,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.profile.model,
            "messages": messages,
            "temperature": self.profile.temperature,
            "stream": False,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        payload.update(options)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            f"{self.endpoint}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.profile.timeout_seconds) as response:  # noqa: S310
                decoded = json.loads(response.read().decode("utf-8"))
            return decoded["choices"][0]["message"]["content"]
        except (HTTPError, URLError, OSError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise LLMConfigurationError(
                f"Il provider '{self.profile.provider_name}' non ha restituito una risposta valida."
            ) from error


class OpenAICompatibleProvider:
    kind = "openai_compatible"

    def create_chat_model(self, profile: LLMProfile) -> ChatModel:
        base_url = str(profile.provider_config.get("base_url") or "").strip().rstrip("/")
        if not base_url:
            raise LLMConfigurationError(f"Il provider '{profile.provider_name}' non definisce base_url.")
        api_key = str(profile.provider_config.get("api_key") or "").strip()
        env_name = str(profile.provider_config.get("api_key_env") or DEFAULT_API_KEY_ENVS.get(self.kind, "")).strip()
        return _HTTPChatModel(profile, base_url, api_key or (os.getenv(env_name, "") if env_name else ""))


class RemoteOpenAICompatibleProvider(OpenAICompatibleProvider):
    def __init__(self, kind: str) -> None:
        self.kind = kind

    def create_chat_model(self, profile: LLMProfile) -> ChatModel:
        base_url = str(profile.provider_config.get("base_url") or "").strip()
        if not base_url.startswith("https://"):
            raise LLMConfigurationError(f"Il provider remoto '{profile.provider_name}' richiede HTTPS.")
        api_key = str(profile.provider_config.get("api_key") or "").strip()
        env_name = str(
            profile.provider_config.get("api_key_env") or DEFAULT_API_KEY_ENVS.get(self.kind, "")
        ).strip()
        api_key = api_key or (os.getenv(env_name, "") if env_name else "")
        if not api_key:
            raise LLMConfigurationError(f"Il provider '{profile.provider_name}' richiede una API key.")
        return _HTTPChatModel(profile, base_url, api_key)


class OllamaProvider:
    """Ollama's native chat endpoint, kept separate from OpenAI-compatible APIs."""

    kind = "ollama"

    def create_chat_model(self, profile: LLMProfile) -> ChatModel:
        base_url = str(profile.provider_config.get("base_url") or "").strip().rstrip("/")
        if not base_url:
            raise LLMConfigurationError(f"Il provider Ollama '{profile.provider_name}' non definisce base_url.")
        return _OllamaChatModel(profile, base_url)


class _OllamaChatModel:
    def __init__(self, profile: LLMProfile, base_url: str) -> None:
        self.profile = profile
        self.endpoint = base_url

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
        **options: Any,
    ) -> str:
        payload: dict[str, Any] = {"model": self.profile.model, "messages": messages, "stream": False}
        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"
        payload.update(options)
        request = Request(
            f"{self.endpoint}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.profile.timeout_seconds) as response:  # noqa: S310
                decoded = json.loads(response.read().decode("utf-8"))
            return decoded["message"]["content"]
        except (HTTPError, URLError, OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise LLMConfigurationError(f"Ollama non ha restituito una risposta valida.") from error


REMOTE_PROVIDER_KINDS = {"xai", "mistral", "deepseek", "qwen", "moonshot", "zhipu"}
DEFAULT_API_KEY_ENVS = {
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "zhipu": "ZHIPUAI_API_KEY",
}


def create_provider(kind: str) -> OpenAICompatibleProvider | OllamaProvider | RemoteOpenAICompatibleProvider:
    normalized = str(kind or "").strip().lower()
    if normalized == "ollama":
        return OllamaProvider()
    if normalized == "openai_compatible":
        return OpenAICompatibleProvider()
    if normalized in REMOTE_PROVIDER_KINDS or normalized == "openai":
        return RemoteOpenAICompatibleProvider(normalized)
    raise LLMConfigurationError(f"Provider LLM non supportato: '{kind}'.")
