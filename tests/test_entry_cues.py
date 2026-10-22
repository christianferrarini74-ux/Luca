"""Index hints are metadata only; the model remains responsible for opening nodes."""

import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from luca_memory.budget import PromptBudget, units
from luca_memory.navigation import MemoryNavigator
from luca_memory.node import KnowledgeNode, load_node
from luca_memory.seed_v1 import load_knowledge_seed
from luca_memory.store import MemoryStore
from luca_memory.synaptic import SynapticMemory
from luca_memory.tiers import SynapticCarousel


class EntryCueTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        self.memory = SynapticMemory(self.store)

    def tearDown(self):
        self.store.close()

    def test_natural_question_finds_seed_title_without_loading_node_payloads(self):
        seed = load_knowledge_seed(self.store, Path(__file__).parents[1] / "seed/knowledge_base_v1.json")
        with patch.object(self.store, "cell", side_effect=AssertionError("No payload reads in entry metadata lookup")):
            candidates = self.memory.entry_candidates("Hai mai sentito parlare dei topi intagliatori di formaggio?")
        self.assertEqual(candidates[0].id, seed.id_for("famiglia_topi"))

    def test_body_only_matches_do_not_pollute_entry_cues(self):
        self.memory.update_node(KnowledgeNode(1, "a", "Mammiferi", "The content mentions uniquequartz."))
        self.assertEqual(self.memory.entry_candidates("uniquequartz"), ())

    def test_rename_and_failed_update_keep_entry_index_atomic(self):
        self.memory.update_node(KnowledgeNode(1, "a", "Old quartz heading", "Body"))
        node = load_node(self.store, 1)
        with (
            patch.object(self.memory, "_event", side_effect=RuntimeError("Injected failure")),
            self.assertRaises(RuntimeError),
        ):
            self.memory.update_node(replace(node, title="New zircon heading"))
        self.assertEqual(self.memory.entry_candidates("zircon"), ())
        self.assertEqual(self.memory.entry_candidates("quartz")[0].id, 1)
        self.memory.update_node(replace(node, title="New zircon heading"))
        self.assertEqual(self.memory.entry_candidates("quartz"), ())
        self.assertEqual(self.memory.entry_candidates("zircon")[0].id, 1)

    def test_cues_offer_ids_but_do_not_force_memory_or_auto_open(self):
        self.memory.update_node(KnowledgeNode(1, "aurora", "Aurora index", "Private payload"))
        carousel = SynapticCarousel(self.store, vram_capacity=1)
        self.addCleanup(carousel.close)
        class Adapter:
            def navigate_memory(adapter, text, state, history):
                adapter.state = state
                return {"action": "answer", "use_memory": False}
        adapter = Adapter()
        navigator = MemoryNavigator(carousel)
        navigator.run("Aurora", adapter, [])
        self.assertEqual(adapter.state["global_candidates"], [{"id": 1, "title": "Aurora index"}])
        self.assertNotIn("Private payload", str(adapter.state))
        self.assertIsNone(carousel.reading_id)
        self.assertFalse(navigator.expose_memory)

    def test_long_reply_keeps_latest_question_with_explicit_history_excerpt(self):
        budget = PromptBudget(history_limit=512)
        history = [{"role": "user", "content": "Parliamo dei topi intagliatori di formaggio"},
                   {"role": "assistant", "content": "Descrizione molto lunga. " * 1000}]
        messages, report = budget.messages("Instructions", "", history, "E perché lo fanno?")
        self.assertEqual(messages[1], history[0])
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertIn("estratto cronologia", messages[2]["content"])
        self.assertTrue(report["history_excerpted"])
        self.assertLessEqual(sum(units(item["content"]) + 16 for item in messages[1:-1]), 512)
        self.assertEqual(history[1]["content"], "Descrizione molto lunga. " * 1000)

    def test_deleting_a_node_removes_metadata_candidates(self):
        self.memory.update_node(KnowledgeNode(1, "a", "Quartz", "Body"))
        with self.store.transaction():
            self.store.connection.execute("DELETE FROM cell_aliases WHERE cell_id=1")
            self.store.connection.execute("DELETE FROM cells WHERE id=1")
        self.assertEqual(self.memory.entry_candidates("Quartz"), ())

    def test_answer_has_knowledge_only_but_navigation_still_has_the_directory(self):
        from luca_memory.navigation import answer_context
        self.memory.update_node(KnowledgeNode(1, "a", "Opened", "Selected knowledge"))
        self.memory.update_node(KnowledgeNode(2, "b", "Neighbor title", "Not opened"))
        self.memory.connect(1, 2)
        carousel = SynapticCarousel(self.store, vram_capacity=1)
        self.addCleanup(carousel.close)
        carousel.recall(1)
        text = answer_context(carousel)
        self.assertIn("Selected knowledge", text)
        self.assertNotIn("Neighbor title", text)
        self.assertNotIn("focus_id", text)
        self.assertEqual(carousel.synaptic.directory(1).outgoing[0].id, 2)
        span = carousel.context_report["node_spans"][0]
        self.assertEqual(span["end"], units(text))
