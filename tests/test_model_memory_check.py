"""Check experimental read gates and accounting without loading models or CUDA."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from luca_memory.controlled_document_check import ROOT
from luca_memory.live_memory_check import ObservedAdapter
from luca_memory.model_memory_check import (
    MeasuredAdapter,
    RequiredReadAdapter,
    experiment_config,
)
from luca_memory.navigation_schema import navigation_schema
from luca_memory.seed_v1 import ensure_knowledge_seed
from luca_memory.store import MemoryStore
from luca_memory.synaptic import SynapticMemory


class ModelMemoryCheckTests(unittest.TestCase):
    def test_generic_word_can_match_specific_revision_candidates(self):
        with MemoryStore(":memory:") as store:
            ensure_knowledge_seed(store, ROOT / "seed/iris17_freshness_v1.json")
            self.assertTrue(SynapticMemory(store).entry_candidates("Che cosa significa revisione di un documento?", 20))

    def test_gate_keeps_all_legal_addresses_but_removes_answer_and_search(self):
        adapter = object.__new__(RequiredReadAdapter)
        adapter.require_first_read = True
        original = navigation_schema({"global_candidates": [{"id": 8}, {"id": 17}]})
        result = adapter._json_schema("memory_navigation", original)["json_schema"]["schema"]
        self.assertEqual(len(result["anyOf"]), 1)
        self.assertEqual(result["anyOf"][0]["properties"]["target_id"]["enum"], [8, 17])
        self.assertEqual(len(original["anyOf"]), 3)

    def test_no_candidates_and_actual_readings_leave_answers_available(self):
        adapter = object.__new__(RequiredReadAdapter)
        adapter.observations = []

        def observe(instance, text, state, history):
            instance.observations.append({})
            return {"action": "answer"}

        with patch.object(ObservedAdapter, "navigate_memory", observe):
            adapter.navigate_memory("General question", {}, [])
            self.assertFalse(adapter.require_first_read)
            adapter.navigate_memory("Read", {"global_candidates": [{"id": 3}]}, [])
            self.assertTrue(adapter.require_first_read)
            adapter.navigate_memory("Answer", {"global_candidates": [{"id": 3}], "read_nodes": [{"reading_id": 3}]}, [])
            self.assertFalse(adapter.require_first_read)

    def test_usage_is_accumulated_instead_of_reporting_only_the_last_call(self):
        adapter = object.__new__(MeasuredAdapter)
        adapter.prompt_budget = SimpleNamespace(unit="bytes")
        adapter.last_prompt_report = {"operation": "navigate"}
        model = SimpleNamespace(last_usage={"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19})
        adapter._record_usage(model)
        adapter._record_usage(model)
        self.assertEqual(len(adapter.request_observations), 2)
        self.assertEqual(sum(item["server_total_tokens"] for item in adapter.request_observations), 38)

    def test_model_and_slot_overrides_do_not_change_main_configuration(self):
        original = {"runtime": {"bible": "bible.md", "vram_capacity": 5},
                    "llm": {"active_runtime": "local", "runtimes": {"local": {
                        "agents": {"orchestrator": {"model": "small"}}}}}}
        selected = experiment_config(original, "large", "snapshot.md")
        self.assertEqual(original["runtime"]["vram_capacity"], 5)
        self.assertEqual(original["llm"]["runtimes"]["local"]["agents"]["orchestrator"]["model"], "small")
        self.assertEqual(selected["runtime"]["vram_capacity"], 1)
        self.assertEqual(selected["runtime"]["ram_capacity"], 1)
