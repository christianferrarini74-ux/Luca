import json
import unittest
from unittest.mock import patch

from luca_memory import LLMConfigurationError, LMStudioModelManager


class FakeResponse:
    status = 200

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class LMStudioModelManagerTests(unittest.TestCase):
    def test_does_not_reload_an_already_loaded_model(self) -> None:
        manager = LMStudioModelManager("http://127.0.0.1:1234")
        with patch(
            "luca_memory.llm.lmstudio.urlopen",
            return_value=FakeResponse(
                {"models": [{"key": "google/gemma", "loaded_instances": [{"id": "google/gemma"}]}]}
            ),
        ) as request:
            manager.ensure_loaded("google/gemma")

        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.args[0].full_url, "http://127.0.0.1:1234/api/v1/models")

    def test_loads_the_configured_model_when_it_is_installed_but_not_loaded(self) -> None:
        manager = LMStudioModelManager("http://127.0.0.1:1234")
        with patch(
            "luca_memory.llm.lmstudio.urlopen",
            side_effect=[
                FakeResponse({"models": [{"key": "google/gemma", "loaded_instances": []}]}),
                FakeResponse({"status": "loaded", "model_instance_id": "google/gemma"}),
            ],
        ) as request:
            manager.ensure_loaded("google/gemma")

        self.assertEqual(request.call_count, 2)
        load_request = request.call_args_list[1].args[0]
        self.assertEqual(load_request.full_url, "http://127.0.0.1:1234/api/v1/models/load")
        self.assertEqual(json.loads(load_request.data), {"model": "google/gemma"})

    def test_reports_available_models_when_the_configured_model_is_missing(self) -> None:
        manager = LMStudioModelManager("http://127.0.0.1:1234")
        with patch(
            "luca_memory.llm.lmstudio.urlopen",
            return_value=FakeResponse({"models": [{"key": "other/model", "loaded_instances": []}]}),
        ):
            with self.assertRaisesRegex(LLMConfigurationError, "other/model"):
                manager.ensure_loaded("google/gemma")


if __name__ == "__main__":
    unittest.main()
