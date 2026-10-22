"""Normal startup and reset must never replace personal knowledge."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from luca_memory.node import KnowledgeNode, load_node, save_node
from luca_memory.seed_v1 import ensure_knowledge_seed, knowledge_seed_from_file
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

    def test_structural_changes_without_version_change_are_rejected(self):
        for change in ("append", "remove", "reorder", "edge"):
            with self.subTest(change=change), tempfile.TemporaryDirectory(dir=self.root) as directory, MemoryStore(":memory:") as store:
                ensure_knowledge_seed(store, self.seed)
                document = json.loads(self.seed.read_text(encoding="utf-8"))
                if change == "append":
                    document["nodes"].append({"slug": "new_seed_node", "content": "new"})
                elif change == "remove":
                    slug = document["nodes"].pop()["slug"]
                    document["edges"] = [e for e in document["edges"] if slug not in e]
                elif change == "reorder":
                    document["nodes"][0], document["nodes"][1] = document["nodes"][1], document["nodes"][0]
                else:
                    document["edges"].pop()
                path = Path(directory) / "changed.json"
                path.write_text(json.dumps(document), encoding="utf-8")
                before = store.connection.total_changes
                with self.assertRaisesRegex(ValueError, "mapping or topology"):
                    ensure_knowledge_seed(store, path)
                self.assertEqual(store.connection.total_changes, before)

    def test_identical_seed_and_edge_order_have_stable_fingerprints(self):
        with tempfile.TemporaryDirectory(dir=self.root) as directory, MemoryStore(":memory:") as store:
            original = ensure_knowledge_seed(store, self.seed)
            self.assertEqual(len(original.fingerprint), 64)
            self.assertEqual(ensure_knowledge_seed(store, self.seed), original)
            document = json.loads(self.seed.read_text(encoding="utf-8"))
            document["edges"].reverse()
            path = Path(directory) / "reordered_edges.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(knowledge_seed_from_file(path).fingerprint, original.fingerprint)
            self.assertEqual(ensure_knowledge_seed(store, path), original)

    def test_legacy_seed_identity_check_is_read_only_and_allows_added_cells(self):
        with MemoryStore(":memory:") as store:
            metadata = ensure_knowledge_seed(store, self.seed)
            with store.transaction():
                store.connection.execute("UPDATE memory_events SET payload=? WHERE kind='seed_v1'", (json.dumps({"version": metadata.version}).encode(),))
                save_node(store, KnowledgeNode(999, "personal", "Personal", "new knowledge"))
            before = store.connection.total_changes
            self.assertEqual(ensure_knowledge_seed(store, self.seed).ids, metadata.ids)
            self.assertEqual(store.connection.total_changes, before)
            with store.transaction():
                save_node(store, KnowledgeNode(1, "wrong_identity", "Wrong", "keep me"))
            before = store.connection.total_changes
            with self.assertRaisesRegex(ValueError, "Legacy seed IDs"):
                ensure_knowledge_seed(store, self.seed)
            self.assertEqual(store.connection.total_changes, before)
            self.assertEqual(load_node(store, 1).content, "keep me")

    def test_invalid_seed_does_not_destroy_existing_memory(self):
        from luca_memory.seed_v1 import load_knowledge_seed
        with tempfile.TemporaryDirectory(dir=self.root) as directory, MemoryStore(":memory:") as store:
            ensure_knowledge_seed(store, self.seed)
            count = store.cell_count()
            document = json.loads(self.seed.read_text(encoding="utf-8"))
            document["nodes"].append(document["nodes"][0])
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_knowledge_seed(store, path)
            self.assertEqual(store.cell_count(), count)
