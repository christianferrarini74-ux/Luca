"""Verify actual traversal, bounded recent activity and index-free usage updates."""

import unittest
from luca_memory.node import KnowledgeNode, save_node, load_node
from luca_memory.store import MemoryStore, Edge
from luca_memory.tiers import SynapticCarousel


class MemoryActivityTests(unittest.TestCase):
    def test_old_ssd_endpoint_is_not_reinforced_by_opening_a_hub(self):
        with MemoryStore(":memory:") as store:
            with store.transaction():
                for nid in range(1, 8):
                    save_node(store, KnowledgeNode(nid, str(nid), str(nid), "Knowledge"))
                store.add_edge(Edge(1, 2))
            carousel = SynapticCarousel(store, vram_capacity=1, ram_capacity=1, recent_window=2)
            for nid in (2, 3, 4, 5):
                carousel.recall(nid)
            self.assertNotIn(2, carousel.opened_in_session)
            carousel.recall(1)
            usage = store.connection.execute("SELECT use_count FROM edges WHERE source_id=1 AND target_id=2").fetchone()[0]
            self.assertEqual(usage, 0)
            self.assertNotIn(2, carousel.vram)
            carousel.step_to(2)
            self.assertEqual(store.connection.execute("SELECT use_count FROM edges WHERE source_id=1 AND target_id=2").fetchone()[0], 1)
            kinds = {event.kind for event in carousel.activity.events}
            self.assertTrue({"open", "traverse", "demote_ram", "demote_ssd"} <= kinds)

    def test_recall_usage_is_persistent_without_reindexing_content(self):
        with MemoryStore(":memory:") as store:
            with store.transaction():
                save_node(store, KnowledgeNode(1, "doc", "Document", "A long chapter"))
            statements = []
            store.connection.set_trace_callback(statements.append)
            carousel = SynapticCarousel(store)
            carousel.recall(1)
            carousel.mark_exposed([1])
            self.assertEqual(load_node(store, 1).recall_count, 1)
            self.assertFalse(any("DELETE FROM cell_search" in sql for sql in statements))
            self.assertFalse(any("INSERT INTO cell_search (" in sql for sql in statements))
            self.assertEqual(store.connection.execute("SELECT exposure_count FROM node_usage WHERE node_id=1").fetchone()[0], 1)
