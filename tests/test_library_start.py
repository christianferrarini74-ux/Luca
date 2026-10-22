"""Keep the real-library workspace separate from synthetic regression seeds."""

import tempfile
import unittest
from pathlib import Path

from luca_memory.config import load_config
from luca_memory.navigation import MemoryNavigator
from luca_memory.node import KnowledgeNode, load_node, save_node
from luca_memory.seed_v1 import ensure_knowledge_seed
from luca_memory.session import LucaSession
from luca_memory.store import MemoryStore
from luca_memory.tiers import SynapticCarousel

ROOT = Path(__file__).parents[1]
SEED = ROOT / "seed/library_empty_v1.json"


class GeneralKnowledgeAdapter:
    def navigate_memory(self, text, state, history):
        self.state = state
        return {"action": "answer", "use_memory": False,
                "response": "General knowledge remains available."}


class LibraryStartTests(unittest.TestCase):
    def test_default_workspace_is_not_the_experimental_database(self):
        config = load_config(ROOT / "config.yaml")
        self.assertEqual(Path(config["storage"]["database"]).name, "luca_library.sqlite")
        self.assertEqual(Path(config["storage"]["seed"]), SEED)
        self.assertEqual(config["runtime"]["memory_policy"], "grounded")

    def test_empty_library_can_navigate_without_inventing_memories(self):
        with MemoryStore(":memory:") as store:
            seed = ensure_knowledge_seed(store, SEED)
            self.assertEqual(seed.ids, {})
            self.assertEqual(store.cell_count(), 0)
            carousel = SynapticCarousel(store)
            try:
                navigator = MemoryNavigator(carousel)
                adapter = GeneralKnowledgeAdapter()
                navigator.run("Explain rainfall", adapter, [])
                self.assertEqual(navigator.response, "General knowledge remains available.")
                self.assertEqual(navigator.entry_ids, ())
                self.assertIsNone(carousel.focus_id)
                self.assertEqual(store.cell_count(), 0)
            finally:
                carousel.close()

    def test_new_knowledge_survives_restart_with_empty_initial_seed(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "library.sqlite"
            session = LucaSession.open(database, SEED)
            try:
                with session.store.transaction():
                    save_node(session.store, KnowledgeNode(1, "manual", "Manual", "Reviewed chapter"))
                session.reset()
            finally:
                session.close()
            reopened = LucaSession.open(database, SEED)
            try:
                self.assertEqual(reopened.store.cell_count(), 1)
                self.assertEqual(load_node(reopened.store, 1).content, "Reviewed chapter")
            finally:
                reopened.close()

    def test_clean_seed_cannot_replace_an_experimental_store(self):
        with MemoryStore(":memory:") as store:
            ensure_knowledge_seed(store, ROOT / "seed/knowledge_base_v1.json")
            count = store.cell_count()
            content = store.cell(3).content
            with self.assertRaises(ValueError):
                ensure_knowledge_seed(store, SEED)
            self.assertEqual(store.cell_count(), count)
            self.assertEqual(store.cell(3).content, content)
