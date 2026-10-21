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
    def test_structured_generation_exhaustion_is_not_treated_as_valid_json(self):
        from luca_memory import LLMConfigurationError
        response = {"choices": [{"finish_reason": "length", "message": {
            "content": "", "reasoning_content": "Unfinished reasoning"}}]}
        adapter = LMStudioAdapter()
        with patch("luca_memory.llm.providers.urlopen", return_value=FakeResponse(response)):
            with self.assertRaisesRegex(LLMConfigurationError, "max_tokens"):
                adapter.connector.create_chat_model().complete([], response_format={"type": "json_schema"}, max_tokens=160)

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

    def test_generates_a_free_response_with_local_memory_context(self) -> None:
        response = {"choices": [{"message": {"content": "Maranello si trova in Emilia-Romagna."}}]}
        adapter = LMStudioAdapter()
        with patch("luca_memory.llm.providers.urlopen", return_value=FakeResponse(response)) as request:
            answer = adapter.respond("Sai dove si trova Maranello?", "- Maranello e una citta italiana.", [])

        self.assertEqual(answer, "Maranello si trova in Emilia-Romagna.")
        payload = json.loads(request.call_args.args[0].data)
        self.assertNotIn("response_format", payload)
        self.assertIn("Maranello e una citta italiana.", payload["messages"][0]["content"])

    def test_task_is_reserved_and_technical_focus_markers_are_not_sent(self) -> None:
        response = {"choices": [{"message": {"content": "Eseguo i test mantenendo il vincolo."}}]}
        adapter = LMStudioAdapter()
        with patch("luca_memory.llm.providers.urlopen", return_value=FakeResponse(response)) as request:
            adapter.respond_with_task("Continuiamo", "[FOCUS CORRENTE] Test del modulo", [], "Vincolo: non cambiare l'interfaccia")
        payload = json.loads(request.call_args.args[0].data)
        system = payload["messages"][0]["content"]
        self.assertIn("Vincolo: non cambiare l'interfaccia", system)
        self.assertNotIn("[FOCUS CORRENTE]", system)
        self.assertLessEqual(adapter.last_prompt_report["input_units"], adapter.last_prompt_report["input_limit"])

    def test_meta_only_response_is_not_returned_as_fallback(self):
        self.assertNotIn("focus corrente", LMStudioAdapter._sanitize_response("Il focus corrente è un dettaglio interno.").lower())
