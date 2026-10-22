"""Behavioral contracts around the simplified turn and reading serializers."""

import json
from pathlib import Path
import unittest

from luca_memory.adapters import RuleAdapter
from luca_memory.budget import PromptBudget
from luca_memory.reading_workspace import ReadingWorkspace
from luca_memory.session import LucaSession


class WorkspaceSerializationTests(unittest.TestCase):
    def test_unicode_byte_spans_match_the_original_json_serialization(self):
        workspace = ReadingWorkspace(PromptBudget(context_window=100000, memory_limit=80000))
        for node_id in range(1, 13):
            workspace.remember({"reading_id": node_id, "title": "Caffè 🌧️", "content": "Più dettagli: acqua e città.",
                                "directory": {"incoming": [], "outgoing": []}, "partial_content": node_id == 2})
        workspace.omitted_ids = [99]
        class Carousel:
            focus_id = 12
            reading_id = 12
        carousel = Carousel()
        rendered = workspace.render(carousel, "answered")
        expected = json.dumps({"navigation_status": "answered", "read_nodes": workspace.payload(),
                               "omitted_ids": [99]}, ensure_ascii=False)
        self.assertEqual(rendered, expected)
        encoded = rendered.encode("utf-8")
        for span, reading in zip(carousel.context_report["node_spans"], workspace.payload()):
            self.assertEqual(json.loads(encoded[span["start"]:span["end"]]), reading)
        self.assertEqual(carousel.context_report["truncated_ids"], [2])
        self.assertEqual(carousel.context_report["span_unit"], "utf8_bytes")


class TurnDispatchTests(unittest.TestCase):
    def open_session(self, adapter, **options):
        seed = Path(__file__).parents[1] / "seed/knowledge_base_v1.json"
        session = LucaSession.open(":memory:", seed, adapter, **options)
        self.addCleanup(session.close)
        return session

    def test_model_answer_is_generated_once_and_history_keeps_complete_roles(self):
        class Adapter(RuleAdapter):
            def __init__(self):
                self.calls = []
            def respond(self, text, context, history):
                raise AssertionError("Task-aware response should have priority")
            def respond_with_task(self, text, context, history, task):
                self.calls.append((text, list(history), task))
                return "Risposta senza filtri."
        adapter = Adapter()
        session = self.open_session(adapter)
        reply = session.handle("Ciao")
        self.assertEqual(reply.text, "Risposta senza filtri.")
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(session.history, [{"role": "user", "content": "Ciao"},
                                           {"role": "assistant", "content": reply.text}])

    def test_navigation_final_answer_does_not_trigger_a_second_generation(self):
        class Adapter(RuleAdapter):
            def __init__(self):
                self.calls = 0
            def navigate_memory(self, text, state, history):
                self.calls += 1
                return {"action": "answer", "use_memory": False, "response": "Risposta già pronta."}
            def respond(self, *args):
                raise AssertionError("Navigation already answered")
        adapter = Adapter()
        session = self.open_session(adapter, planner_mode="llm")
        reply = session.handle("Ciao")
        self.assertEqual(reply.text, "Risposta già pronta.")
        self.assertEqual(adapter.calls, 1)

    def test_rule_only_adapter_stays_on_the_deterministic_path(self):
        session = self.open_session(RuleAdapter())
        self.assertEqual(session.handle("Ciao").text, "Ciao Christian. Sono Luca.")
        self.assertEqual(session.history, [])
