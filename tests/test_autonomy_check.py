"""Validate experiment isolation and fixture links without external services."""

import json
import unittest
from unittest.mock import patch

from luca_memory.autonomy_check import CASES, GUIDANCE, AuditedAdapter, profile_config
from luca_memory.controlled_document_check import ROOT
from luca_memory.live_memory_check import ObservedAdapter
from luca_memory.seed_v1 import ensure_knowledge_seed
from luca_memory.store import MemoryStore


class AutonomyCheckTests(unittest.TestCase):
    def test_profile_does_not_mutate_application_configuration(self):
        original = {"runtime": {"bible": "bible.md", "synaptic": {"navigation_steps": 8}}}
        candidate = profile_config(original, "candidate.md")
        candidate["runtime"]["synaptic"]["navigation_steps"] = 1
        self.assertEqual(original["runtime"]["bible"], "bible.md")
        self.assertEqual(original["runtime"]["synaptic"]["navigation_steps"], 8)

    def test_expected_nodes_exist_and_history_is_explicit(self):
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(len({case["id"] for case in cases}), 6)
        for case in cases:
            with MemoryStore(":memory:") as store:
                seed = ensure_knowledge_seed(store, ROOT / "seed" / case["seed"])
                self.assertTrue(set(case["required_slugs"]).issubset(seed.ids))
        stale = next(case for case in cases if case["id"] == "stale_history")
        self.assertEqual(stale["history"][-1]["role"], "assistant")

    def test_experimental_guidance_contains_no_fixture_answers(self):
        text = GUIDANCE.read_text(encoding="utf-8")
        for answer in ("1502", "1902", "2502", "3502", "IRIS", "CONFERMA"):
            self.assertNotIn(answer, text)

    def test_address_labels_do_not_change_facts_or_graph(self):
        original = json.loads((ROOT / "seed/iris17_controlled_v1.json").read_text(encoding="utf-8"))
        addressed = json.loads((ROOT / "seed/iris17_addressed_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(original["edges"], addressed["edges"])
        self.assertEqual(len(original["nodes"]), len(addressed["nodes"]))
        for before, after in zip(original["nodes"], addressed["nodes"], strict=True):
            self.assertEqual({key: value for key, value in before.items() if key != "title"},
                             {key: value for key, value in after.items() if key != "title"})

    def test_audit_allows_the_model_to_choose_a_read_and_only_runs_once(self):
        adapter = object.__new__(AuditedAdapter)
        adapter.observations = []
        proposals = iter(({"action": "answer", "response": "Draft"},
                          {"action": "open", "source": "local", "target_id": 7},
                          {"action": "answer", "response": "Complete"}))
        states = []

        def observe(instance, text, state, history):
            states.append(state)
            choice = next(proposals)
            instance.observations.append({"choice": choice})
            return choice

        state = {"focus": 1}
        with patch.object(ObservedAdapter, "navigate_memory", observe):
            self.assertEqual(adapter.navigate_memory("Question", state, [])["action"], "open")
            self.assertEqual(adapter.navigate_memory("Question", state, [])["response"], "Complete")
        self.assertNotIn("draft_response", state)
        self.assertEqual(states[1]["draft_response"], "Draft")
        self.assertEqual(len(states), 3)
