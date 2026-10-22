"""Exercise actual adapter request assembly without contacting a live model."""

import json
import unittest
from unittest.mock import Mock

from luca_memory.adapters import LanguageAdapterUnavailable, LMStudioAdapter
from luca_memory.budget import PromptBudget
from luca_memory.synaptic import Directory, DirectoryEntry
from luca_memory.synaptic_settings import SynapticSettings


class NavigationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.connector = Mock()
        self.model = self.connector.create_chat_model.return_value
        self.adapter = LMStudioAdapter(connector=self.connector)
        self.adapter.prompt_budget = PromptBudget(context_window=16000)

    def test_navigation_keeps_full_directory_in_fixed_input(self):
        self.model.complete.return_value = '{"action":"open","source":"local","target_id":50}'
        directory = Directory(1, 123, (), tuple(DirectoryEntry(index, f"Title {index}") for index in range(2, 52)), ())
        result = self.adapter.navigate_memory("Next", {"directory": directory.payload(), "local_target_ids": list(range(2, 52))}, [])
        self.assertEqual(result["target_id"], 50)
        messages = self.model.complete.call_args.args[0]
        self.assertEqual(json.loads(messages[-1]["content"])["state"]["directory"]["outgoing"][-1]["id"], 51)
        response_format = self.model.complete.call_args.kwargs["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        variants = response_format["json_schema"]["schema"]["anyOf"]
        self.assertEqual([v["properties"]["action"]["const"] for v in variants], ["search", "open", "answer"])
        self.assertEqual(variants[1]["properties"]["target_id"]["enum"], list(range(2, 52)))
        self.assertIn("source", variants[1]["required"])
        self.assertEqual(self.model.complete.call_args.kwargs["max_tokens"], 2048)

    def test_oversized_directory_is_rejected_before_any_model_request(self):
        with self.assertRaises(ValueError):
            self.adapter.navigate_memory("Next", {"directory": "X" * (2 * self.adapter.prompt_budget.context_window)}, [])
        self.model.complete.assert_not_called()

    def test_final_response_does_not_clip_routing_metadata(self):
        self.adapter.prompt_budget = PromptBudget(context_window=16000)
        self.model.complete.return_value = "Risposta."
        memory = "Complete directory " + "X" * 4200
        self.assertEqual(self.adapter.respond_with_navigation("Next", memory, [], ""), "Risposta.")
        self.assertEqual(memory, json.loads(self.model.complete.call_args.args[0][-1]["content"])["memory"])

    def test_group_request_and_invalid_model_response(self):
        self.model.complete.return_value = json.dumps({"groups": [{"title": "Group", "direction": "outgoing", "members": [2, 3]}]})
        directory = Directory(1, 1, (), (DirectoryEntry(2, "Two"), DirectoryEntry(3, "Three")), ())
        groups = self.adapter.propose_groups(directory, SynapticSettings())
        self.assertEqual(groups[0]["members"], [2, 3])
        self.assertEqual(self.model.complete.call_args.kwargs["max_tokens"], 2048)
        group_format = self.model.complete.call_args.kwargs["response_format"]
        directions = group_format["json_schema"]["schema"]["properties"]["assignments"]["properties"]
        self.assertEqual(set(directions["outgoing"]["properties"]), {"2", "3"})
        self.assertFalse(directions["outgoing"]["additionalProperties"])
        self.model.complete.return_value = "Not JSON"
        with self.assertRaises(LanguageAdapterUnavailable):
            self.adapter.navigate_memory("Next", {}, [])

    def test_cold_entry_cannot_request_an_unlisted_id_in_the_schema(self):
        self.model.complete.return_value = '{"action":"search","query":"topic"}'
        self.adapter.navigate_memory("Next", {"reading_id": None, "global_candidates": [], "local_target_ids": []}, [])
        schema = self.model.complete.call_args.kwargs["response_format"]["json_schema"]["schema"]
        self.assertEqual([v["properties"]["action"]["const"] for v in schema["anyOf"]], ["search", "answer"])

    def test_group_request_sizes_proposals_to_the_configured_target_gap(self):
        self.model.complete.return_value = '{"assignments":{"incoming":{},"outgoing":{}}}'
        directory = Directory(1, 1, (), tuple(DirectoryEntry(index, f"Node {index}") for index in range(2, 54)), ())
        self.adapter.propose_groups(directory, SynapticSettings())
        constraints = json.loads(self.model.complete.call_args.args[0][-1]["content"])["constraints"]
        self.assertEqual(constraints["required_reduction"], 7)
        self.assertEqual(constraints["max_members"], 8)
