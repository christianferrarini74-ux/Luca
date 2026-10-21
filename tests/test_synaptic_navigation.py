"""Model choices, complete directories and family focus through the real session."""

from pathlib import Path
import json
import tempfile
import unittest

from luca_memory.navigation import MemoryNavigator, focus_context
from luca_memory.node import KnowledgeNode
from luca_memory.session import LucaSession
from luca_memory.store import MemoryStore
from luca_memory.synaptic import SynapticMemory
from luca_memory.tiers import SynapticCarousel


class ScriptedAdapter:
    def __init__(self, actions):
        self.actions = iter(actions)
        self.states = []

    def navigate_memory(self, text, state, history):
        self.states.append(state)
        return next(self.actions)

    def respond(self, text, memory_context, history):
        self.context = memory_context
        return "Risposta libera."


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = MemoryStore(Path(self.temp.name) / "memory.sqlite")
        self.memory = SynapticMemory(self.store)
        for index, title in ((1, "Python"), (2, "Part one"), (3, "Libraries"), (4, "Unrelated")):
            self.memory.update_node(KnowledgeNode(index, f"n{index}", title, f"Full content of {title}"))
        self.memory.attach_part(1, 2)
        self.memory.connect(1, 3)
        self.carousel = SynapticCarousel(self.store, vram_capacity=1)
        self.nav = MemoryNavigator(self.carousel)

    def tearDown(self):
        self.carousel.close()
        self.store.close()
        self.temp.cleanup()

    def test_global_entry_family_part_and_external_route_are_model_choices(self):
        adapter = ScriptedAdapter([
            {"action": "search", "query": "Python"},
            {"action": "open", "source": "global", "target_id": 1},
            {"action": "open", "source": "local", "target_id": 2},
            {"action": "open", "source": "local", "target_id": 3},
            {"action": "answer", "use_memory": True}])
        self.nav.run("Read the library", adapter, [])
        self.assertEqual(self.carousel.focus_id, 3)
        self.assertEqual([step["target_id"] for step in self.nav.trace if "target_id" in step], [1, 2, 3])
        self.assertEqual(adapter.states[3]["focus"], 1)
        self.assertIn('"Libraries"', json.dumps(adapter.states[3]["context"]))
        self.assertNotIn("Full content of Libraries", json.dumps(adapter.states[3]["context"]))
        self.assertTrue(self.nav.expose_memory)

    def test_invented_id_bool_non_neighbor_and_cycles_are_rejected(self):
        self.carousel.recall(1)
        adapter = ScriptedAdapter([
            {"action": "open", "target_id": 999},
            {"action": "open", "target_id": True},
            {"action": "open", "target_id": 4},
            {"action": "open", "target_id": 3},
            {"action": "open", "target_id": 3},
            {"action": "answer", "use_memory": True}])
        self.nav.run("Test", adapter, [])
        self.assertEqual(self.carousel.reading_id, 3)
        self.assertEqual("target_already_open", adapter.states[5]["feedback"]["error"])
        self.assertEqual(sum("target_id" in step for step in self.nav.trace), 1)

    def test_general_knowledge_does_not_force_a_local_memory(self):
        self.carousel.recall(1)
        self.nav.run("Something else", ScriptedAdapter([{"action": "answer", "use_memory": False}]), [])
        self.assertFalse(self.nav.expose_memory)

    def test_complete_directory_is_not_silently_truncated(self):
        self.memory.update_node(KnowledgeNode(3, "n3", "X" * 6000, "Payload"))
        self.carousel.recall(1)
        with self.assertRaisesRegex(ValueError, "No routes were truncated"):
            focus_context(self.carousel)

    def test_navigation_work_is_bounded(self):
        nav = MemoryNavigator(self.carousel, max_steps=2)
        nav.run("Test", ScriptedAdapter([{}, {}]), [])
        self.assertEqual(nav.trace[-1]["action"], "step_limit")

    def test_returning_to_a_previously_read_node_is_allowed(self):
        self.carousel.recall(1)
        adapter = ScriptedAdapter([
            {"action": "open", "source": "local", "target_id": 3},
            {"action": "open", "source": "local", "target_id": 1},
            {"action": "open", "source": "local", "target_id": 3},
            {"action": "answer", "use_memory": True}])
        self.nav.run("Compare both nodes", adapter, [])
        self.assertEqual([step["target_id"] for step in self.nav.trace if "target_id" in step], [3, 1, 3])
        self.assertEqual(self.nav.trace[-1]["action"], "answer")

    def test_actual_session_uses_llm_protocol_not_legacy_semantic_rules(self):
        seed = Path(__file__).resolve().parents[1] / "seed/knowledge_base_v1.json"
        adapter = ScriptedAdapter([
            {"action": "search", "query": "Python"},
            {"action": "open", "source": "global", "target_id": 1},
            {"action": "answer", "use_memory": True}])
        session = LucaSession(self.store, seed, adapter, planner_mode="llm")
        self.addCleanup(session.carousel.close)
        reply = session.handle("Argomento scelto dal modello")
        self.assertEqual(reply.text, "Risposta libera.")
        self.assertIn("Full content of Python", adapter.context)
        self.assertEqual(session.last_plan.operation, "llm_navigation")

    def test_reading_a_family_part_preserves_conversation_continuity(self):
        seed = Path(__file__).resolve().parents[1] / "seed/knowledge_base_v1.json"
        adapter = ScriptedAdapter([
            {"action": "open", "source": "local", "target_id": 2},
            {"action": "answer", "use_memory": True}])
        session = LucaSession(self.store, seed, adapter, planner_mode="llm", vram_capacity=1)
        self.addCleanup(session.carousel.close)
        session.recall_manual(1)
        session.history = [{"role": "user", "content": "Prima domanda"},
                           {"role": "assistant", "content": "Prima risposta"}]
        session.handle("Leggi la parte uno")
        self.assertEqual(session.current_subject_id, 1)
        self.assertEqual(session.carousel.reading_id, 2)
        self.assertEqual(len(session.history), 4)
