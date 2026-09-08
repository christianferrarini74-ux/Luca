import json
import unittest
from unittest.mock import patch

from luca_memory import LMStudioAdapter


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class LMStudioAdapterTests(unittest.TestCase):
    def test_uses_local_endpoint_and_validates_a_lesson(self) -> None:
        response = {
            "choices": [{"message": {"content": json.dumps({
                "kind": "remember",
                "subject": "sole",
                "predicate": "produce",
                "objects": ["luce", "calore"],
                "question": None,
                "confidence": 0.97,
                "ambiguity": None,
            })}}]
        }
        adapter = LMStudioAdapter()
        with patch("luca_memory.llm.providers.urlopen", return_value=FakeResponse(response)) as request:
            intent = adapter.interpret("Luca, ricorda che il sole produce luce e calore.")

        self.assertEqual(intent.kind, "remember")
        self.assertEqual(intent.objects, ("luce", "calore"))
        self.assertEqual(request.call_args.args[0].full_url, "http://127.0.0.1:1234/v1/chat/completions")
