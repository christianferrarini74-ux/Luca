"""Load the single, explicit source of model-facing instructions."""

from pathlib import Path

from .llm.models import LLMConfigurationError

DEFAULT_BIBLE = Path(__file__).resolve().parent.parent / "bible.md"


def read_bible(path=DEFAULT_BIBLE):
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError as error:
        raise LLMConfigurationError(f"Cannot read Luca's configured bible: {path}") from error
    if not text:
        raise LLMConfigurationError("Luca's configured bible is empty.")
    return text
