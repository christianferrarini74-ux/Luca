"""Phase 1.11 contracts use isolated temporary databases, never personal memory."""

import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from luca_memory.node import KnowledgeNode, load_node
from luca_memory.store import Edge, MemoryStore
from luca_memory.synaptic import StaleRevision, SynapticMemory
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
        with (
            patch.object(self.memory, "_event", side_effect=RuntimeError("Injected journal failure")),
            self.assertRaises(RuntimeError),
        ):
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

    def test_reader_cannot_observe_half_updated_node(self):
        entered, release, read = threading.Event(), threading.Event(), threading.Event()
        original = self.store._index_cell_for_search
        result, errors = [], []
        def paused_index(cell):
            entered.set()
            if not release.wait(3):
                raise RuntimeError("Writer test timed out")
            original(cell)
        def writer():
            try:
                self.memory.update_node(KnowledgeNode(1, "updated", "Updated", "New body"))
            except Exception as error:  # noqa: BLE001 - Collect worker failures for assertion in this concurrency test.
                errors.append(error)
        def reader():
            result.append(load_node(self.store, 1))
            read.set()
        with patch.object(self.store, "_index_cell_for_search", side_effect=paused_index):
            writing = threading.Thread(target=writer)
            writing.start()
            self.assertTrue(entered.wait(2))
            reading = threading.Thread(target=reader)
            reading.start()
            try:
                self.assertFalse(read.wait(0.05))
            finally:
                release.set()
                writing.join(3)
                reading.join(3)
        self.assertFalse(writing.is_alive())
        self.assertFalse(reading.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result[0].title, "Updated")

    def test_gpu_failure_after_committed_update_cannot_resurrect_old_payload(self):
        from test_device_memory import FakeDevice

        from luca_memory.tiers.coherent_slot import CoherentSlot
        from luca_memory.tiers.cuda import DeviceMemoryError
        from luca_memory.tiers.device_slot import DeviceSlot
        carousel = SynapticCarousel(self.store, vram_capacity=1)
        self.addCleanup(carousel.close)
        carousel.vram.close()
        device = FakeDevice()
        carousel.vram = CoherentSlot(DeviceSlot(1, 10000, memory=device), self.store)
        carousel.recall(1)
        self.memory.update_node(replace(load_node(self.store, 1), content="Committed new version"))
        device.fail_after = device.next_id
        with self.assertRaises(DeviceMemoryError):
            carousel.recall(1)
        self.assertIsNone(carousel.vram.get(1))
        self.assertEqual(device.buffers, {})
        self.assertEqual(load_node(self.store, 1).content, "Committed new version")
        device.fail_after = None
        carousel.recall(1)
        self.assertEqual(carousel.vram.get(1).content, "Committed new version")

    def test_legacy_migration_preserves_content_and_routes_and_replaces_old_generated_alias(self):
        import sqlite3
        path = Path(self.temp.name) / "legacy.sqlite"
        node = KnowledgeNode(1, "legacy", "Legacy heading", "Original knowledge", created_at=123)
        connection = sqlite3.connect(path)
        connection.executescript("""CREATE TABLE cells(id INTEGER PRIMARY KEY, content BLOB, created_at INTEGER);
            CREATE TABLE edges(source_id INTEGER, target_id INTEGER, PRIMARY KEY(source_id,target_id));
            CREATE TABLE cell_aliases(alias TEXT PRIMARY KEY,cell_id INTEGER);""")
        connection.execute("INSERT INTO cells VALUES(?,?,?)", (1, node.to_cell().content, 123))
        connection.execute("INSERT INTO cell_aliases VALUES('legacy heading',1)")
        connection.execute("INSERT INTO cell_aliases VALUES('explicit historical alias',1)")
        connection.execute("INSERT INTO edges VALUES(1,1)")
        connection.commit()
        connection.close()
        with MemoryStore(path) as migrated:
            memory = SynapticMemory(migrated)
            self.assertEqual(migrated.cell(1).content, node.to_cell().content)
            self.assertIsNotNone(migrated.edge(1, 1))
            self.assertEqual(memory.parts(1), ())
            memory.update_node(replace(node, title="New heading"))
            self.assertIsNone(migrated.cell_by_alias("legacy heading"))
            self.assertEqual(migrated.cell_by_alias("explicit historical alias").id, 1)

    def test_attaching_a_part_preserves_its_self_loop_as_a_root_route(self):
        self.memory.connect(2, 2)
        self.memory.attach_part(1, 2)
        self.assertIsNotNone(self.store.edge(1, 1))
        self.assertEqual(self.memory.directory(1).external_degree, 2)


if __name__ == "__main__":
    unittest.main()
