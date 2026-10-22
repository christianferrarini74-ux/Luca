"""Executable external-producer example and documented family/navigation rules."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from luca_memory.node import KnowledgeNode, load_node
from luca_memory.store import MemoryStore
from luca_memory.synaptic import StaleRevision, SynapticMemory


class MemoryContractTests(unittest.TestCase):
    def test_producer_example_is_atomic_searchable_and_preserves_family_identity(self):
        spec = importlib.util.spec_from_file_location("memory_contract_example", Path(__file__).parents[1] / "examples/memory_contract.py")
        example = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(example)
        with (
            tempfile.TemporaryDirectory() as temporary,
            MemoryStore(Path(temporary) / "example.sqlite") as store,
        ):
            ids = example.populate_example(store)
            memory = SynapticMemory(store)
            self.assertEqual(store.cell_count(), 4)
            self.assertEqual(memory.root(ids["reference"]), ids["root"])
            self.assertEqual(memory.directory(ids["installation"]), memory.directory(ids["reference"]))
            self.assertIsNotNone(store.edge(ids["root"], ids["environment"]))
            self.assertIsNone(store.edge(ids["installation"], ids["environment"]))
            self.assertEqual(load_node(store, ids["reference"]).sections[0].key, "entry")
            self.assertIn(ids["reference"], {entry.id for entry in memory.global_lookup("Atlas")})
            count, revision = store.cell_count(), store.revision
            with self.assertRaises(ValueError):
                example.populate_example(store)
            self.assertEqual((store.cell_count(), store.revision), (count, revision))

    def test_global_revision_is_not_a_directory_revision_and_partial_views_cannot_be_saved(self):
        with MemoryStore(":memory:") as store:
            memory = SynapticMemory(store)
            for identity in range(1, 4):
                memory.update_node(KnowledgeNode(identity, f"node_{identity}", f"Title {identity}", "Body"))
            directory = memory.directory(1)
            self.assertNotEqual(directory.revision, store.revision)
            with self.assertRaises(StaleRevision):
                memory.connect(1, 2, expected_revision=directory.revision)
            with self.assertRaises(ValueError):
                memory.update_node(KnowledgeNode(1, "partial", "Partial", "Excerpt", content_complete=False))
            self.assertEqual(load_node(store, 1).content, "Body")
