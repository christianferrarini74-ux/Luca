"""Exercise actual adapter request assembly without contacting a live model."""

import json
import unittest
from unittest.mock import Mock

from luca_memory.adapters import LMStudioAdapter, LanguageAdapterUnavailable
from luca_memory.synaptic import Directory, DirectoryEntry
from luca_memory.synaptic_settings import SynapticSettings


class NavigationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.connector = Mock()
        self.model = self.connector.create_chat_model.return_value
        self.adapter = LMStudioAdapter(connector=self.connector)

    def test_navigation_keeps_full_directory_in_fixed_input(self):
        self.model.complete.return_value = '{"action":"open","source":"local","target_id":50}'
        directory = Directory(1, 123, (), tuple(DirectoryEntry(index, f"Title {index}") for index in range(2, 52)), ())
        result = self.adapter.navigate_memory("Next", {"directory": directory.payload(), "local_target_ids": list(range(2, 52))}, [])
        self.assertEqual(result["target_id"], 50)
        messages = self.model.complete.call_args.args[0]
        self.assertIn('"id": 51', messages[0]["content"])
        response_format = self.model.complete.call_args.kwargs["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        self.assertEqual(response_format["json_schema"]["schema"]["properties"]["action"]["enum"], ["search", "open", "answer"])
        self.assertEqual(response_format["json_schema"]["schema"]["properties"]["target_id"]["enum"], list(range(2, 52)))
        self.assertEqual(self.model.complete.call_args.kwargs["max_tokens"], 2048)

    def test_oversized_directory_is_rejected_before_any_model_request(self):
        with self.assertRaises(ValueError):
            self.adapter.navigate_memory("Next", {"directory": "X" * 10000}, [])
        self.model.complete.assert_not_called()

    def test_final_response_does_not_clip_routing_metadata(self):
        self.model.complete.return_value = "Risposta."
        memory = "Complete directory " + "X" * 4200
        self.assertEqual(self.adapter.respond_with_navigation("Next", memory, [], ""), "Risposta.")
        self.assertIn(memory, self.model.complete.call_args.args[0][0]["content"])

    def test_group_request_and_invalid_model_response(self):
        self.model.complete.return_value = json.dumps({"groups": [{"title": "Group", "direction": "outgoing", "members": [2, 3]}]})
        directory = Directory(1, 1, (), (DirectoryEntry(2, "Two"), DirectoryEntry(3, "Three")), ())
        groups = self.adapter.propose_groups(directory, SynapticSettings())
        self.assertEqual(groups[0]["members"], [2, 3])
        self.assertEqual(self.model.complete.call_args.kwargs["max_tokens"], 2048)
        group_format = self.model.complete.call_args.kwargs["response_format"]
        variant = group_format["json_schema"]["schema"]["properties"]["groups"]["items"]["anyOf"][0]
        self.assertEqual(variant["properties"]["direction"]["const"], "outgoing")
        self.assertEqual(variant["properties"]["members"]["items"]["enum"], [2, 3])
        self.model.complete.return_value = "Not JSON"
        with self.assertRaises(LanguageAdapterUnavailable):
            self.adapter.navigate_memory("Next", {}, [])

    def test_cold_entry_cannot_request_an_unlisted_id_in_the_schema(self):
        self.model.complete.return_value = '{"action":"search","query":"topic"}'
        self.adapter.navigate_memory("Next", {"reading_id": None, "global_candidates": [], "local_target_ids": []}, [])
        schema = self.model.complete.call_args.kwargs["response_format"]["json_schema"]["schema"]
        self.assertEqual(schema["properties"]["action"]["enum"], ["search", "answer"])
