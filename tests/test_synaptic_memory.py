"""Phase 1.11 contracts use isolated temporary databases, never personal memory."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from luca_memory.node import KnowledgeNode, load_node, save_node
from luca_memory.store import Edge, MemoryStore
from luca_memory.synaptic import SynapticMemory, StaleRevision
from luca_memory.tiers import SynapticCarousel


class SynapticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "memory.sqlite"
        self.store = MemoryStore(self.path)
        self.memory = SynapticMemory(self.store)
        for index in range(1, 8):
            self.memory.update_node(KnowledgeNode(index, f"n{index}", f"Node {index}", f"Content {index}"))

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_shared_family_identity_and_canonical_external_routes(self):
        self.memory.connect(1, 4)
        self.memory.connect(5, 2)
        self.memory.attach_part(1, 2)
        self.memory.attach_part(1, 3)
        directory = self.memory.directory(2)
        self.assertIs(directory, self.memory.directory(3))
        self.assertEqual(directory.focus_id, 1)
        self.assertEqual([e.id for e in directory.incoming], [5])
        self.assertEqual([e.id for e in directory.outgoing], [4])
        self.assertEqual(directory.external_degree, 2)
        self.assertEqual([e.id for e in directory.parts], [2, 3])
        self.assertEqual(self.memory.validate_step(2, 4, directory.revision), (1, 4))
        self.memory.connect(3, 6)
        self.assertIsNotNone(self.store.edge(1, 6))
        self.assertIsNone(self.store.edge(3, 6))

    def test_neighbor_is_not_implicitly_a_fragment(self):
        self.memory.connect(1, 2)
        self.memory.connect(1, 3)
        self.assertEqual(self.memory.root(2), 2)
        self.assertEqual(self.memory.parts(1), ())

    def test_family_rejects_cycles_nesting_and_low_level_external_edges(self):
        self.memory.attach_part(1, 2)
        for root, part in ((1, 1), (2, 3), (3, 1)):
            with self.assertRaises(ValueError):
                self.memory.attach_part(root, part)
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError), self.store.transaction():
            self.store.add_edge(Edge(2, 4))

    def test_current_aliases_search_and_neighbor_titles_change_together(self):
        self.memory.connect(1, 2)
        old = self.memory.directory(1)
        self.memory.update_node(replace(load_node(self.store, 2), title="New heading", content="Rareword"))
        self.assertIsNone(self.store.cell_by_alias("node 2"))
        self.assertEqual(self.store.cell_by_alias("new heading").id, 2)
        self.assertEqual(self.memory.global_lookup("Rareword")[0].id, 2)
        self.assertEqual(self.memory.directory(1).outgoing[0].title, "New heading")
        with self.assertRaises(StaleRevision):
            self.memory.validate_step(1, 2, old.revision)

    def test_failed_node_update_rolls_back_payload_aliases_catalog_and_revision(self):
        before = self.store.revision
        node = load_node(self.store, 1)
        with patch.object(self.memory, "_event", side_effect=RuntimeError("Injected journal failure")):
            with self.assertRaises(RuntimeError):
                self.memory.update_node(replace(node, title="Wrong", content="Wrong"))
        self.assertEqual(load_node(self.store, 1), node)
        self.assertEqual(self.store.revision, before)
        self.assertIsNone(self.store.cell_by_alias("wrong"))
        self.assertEqual(self.memory.global_lookup("Node 1")[0].title, "Node 1")

    def test_stale_mutation_and_unrelated_directory_cache(self):
        directory = self.memory.directory(1)
        revision = self.store.revision
        self.memory.connect(5, 6)
        self.assertIs(self.memory.directory(1), directory)
        with self.assertRaises(StaleRevision):
            self.memory.connect(1, 2, expected_revision=revision)
        self.assertIsNone(self.store.edge(1, 2))

    def test_usage_does_not_change_structural_revision(self):
        self.memory.connect(1, 2)
        revision = self.store.revision
        with self.store.transaction():
            self.store.touch_edge(1, 2, 123)
            self.store.record_node_usage(1, 123)
        self.assertEqual(self.store.revision, revision)

    def test_directory_complete_with_one_payload_slot(self):
        for index in range(8, 89):
            self.memory.update_node(KnowledgeNode(index, f"n{index}", str(index), "Filler"))
            self.memory.connect(1, index)
        carousel = SynapticCarousel(self.store, vram_capacity=1)
        self.addCleanup(carousel.close)
        event = carousel.recall(1)
        self.assertEqual(len(event.first_degree_ids), 81)
        self.assertEqual(len(carousel.synaptic.directory(1).outgoing), 81)
        self.assertEqual(carousel.vram.node_ids(), (1,))

    def test_resident_payload_is_invalidated_after_update(self):
        carousel = SynapticCarousel(self.store, vram_capacity=1)
        self.addCleanup(carousel.close)
        carousel.recall(1)
        self.memory.update_node(replace(load_node(self.store, 1), content="Updated payload"))
        self.assertIsNone(carousel.vram.get(1))
        carousel.recall(1)
        self.assertEqual(carousel.vram.get(1).content, "Updated payload")

    def test_directory_and_family_survive_restart(self):
        self.memory.attach_part(1, 2)
        self.memory.connect(2, 4)
        self.store.close()
        self.store = MemoryStore(self.path)
        self.memory = SynapticMemory(self.store)
        self.assertEqual(self.memory.directory(2).focus_id, 1)
        self.assertEqual([e.id for e in self.memory.directory(2).outgoing], [4])

    def test_family_reading_keeps_synaptic_focus_and_shared_routes(self):
        self.memory.attach_part(1, 2)
        self.memory.connect(1, 4)
        carousel = SynapticCarousel(self.store, vram_capacity=2)
        self.addCleanup(carousel.close)
        carousel.step_to(2)
        self.assertEqual((carousel.focus_id, carousel.reading_id), (1, 2))
        carousel.step_to(4)
        self.assertEqual(self.store.prefix_family_ids(1, limit=1), (4,))


if __name__ == "__main__":
    unittest.main()
