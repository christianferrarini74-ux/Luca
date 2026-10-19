"""Normal startup and reset must never replace personal knowledge."""

import json
import os
from pathlib import Path
import tempfile
import unittest

from luca_memory.node import KnowledgeNode, save_node, load_node
from luca_memory.seed_v1 import ensure_knowledge_seed
from luca_memory.session import LucaSession
from luca_memory.store import MemoryStore


class SeedPreservationTests(unittest.TestCase):
    seed = Path(__file__).parents[1] / "seed/knowledge_base_v1.json"

    def setUp(self):
        self.root = Path(os.getenv("LUCA_TEST_DIRECTORY", "D:/Test/Luca"))
        self.root.mkdir(parents=True, exist_ok=True)

    def test_added_node_survives_reset_and_restart(self):
        with tempfile.TemporaryDirectory(prefix="seed-preservation-", dir=self.root) as directory:
            database = Path(directory) / "synthetic.sqlite"
            session = LucaSession.open(database, self.seed)
            try:
                with session.store.transaction():
                    save_node(session.store, KnowledgeNode(999, "personal", "Personal", "Do not replace", created_at=1))
                session.reset()
                self.assertEqual(load_node(session.store, 999).content, "Do not replace")
            finally:
                session.close()
            reopened = LucaSession.open(database, self.seed)
            try:
                self.assertEqual(load_node(reopened.store, 999).content, "Do not replace")
            finally:
                reopened.close()

    def test_changed_seed_is_rejected_without_replacing_existing_data(self):
        with tempfile.TemporaryDirectory(prefix="seed-preservation-", dir=self.root) as directory:
            seed = Path(directory) / "changed.json"
            document = json.loads(self.seed.read_text(encoding="utf-8"))
            document["version"] += "-changed"
            seed.write_text(json.dumps(document), encoding="utf-8")
            with MemoryStore(":memory:") as store:
                ensure_knowledge_seed(store, self.seed)
                count = store.cell_count()
                before = store.cell(3).content
                with self.assertRaises(ValueError):
                    ensure_knowledge_seed(store, seed)
                self.assertEqual(store.cell_count(), count)
                self.assertEqual(store.cell(3).content, before)
