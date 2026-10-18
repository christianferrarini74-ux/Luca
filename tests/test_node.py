import unittest

from luca_memory.node import KnowledgeNode, load_node, save_node
from luca_memory.search import MemorySearch
from luca_memory.store import MemoryStore


class KnowledgeNodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")

    def tearDown(self) -> None:
        self.store.close()

    def test_save_and_load_articulated_knowledge_node(self) -> None:
        node = KnowledgeNode(
            id=1,
            slug="giostra_sinaptica",
            title="Giostra Sinaptica dei Livelli",
            content="I ricordi richiamati salgono in testa alla VRAM con il loro grappolo di primo grado.",
            keywords=("vram", "giostra", "sinapsi"),
            created_at=100,
        )
        with self.store.transaction():
            save_node(self.store, node)

        loaded = load_node(self.store, 1)
        self.assertEqual(loaded, node)

        # Verify alias and full-text search
        search = MemorySearch(self.store)
        by_alias = search.cell_by_alias("vram")
        self.assertIsNotNone(by_alias)
        self.assertEqual(by_alias.id, 1)

        by_text = search.cells_by_text("grappolo primo grado", kind="knowledge")
        self.assertEqual([item.cell.id for item in by_text], [1])

    def test_with_recall_updates_usage_metadata(self) -> None:
        node = KnowledgeNode(id=1, slug="cesare", title="Progetto Cesare", content="Destinazione finale di Luca.")
        recalled = node.with_recall(timestamp=500)
        self.assertEqual(recalled.recall_count, 1)
        self.assertEqual(recalled.last_recalled_at, 500)


if __name__ == "__main__":
    unittest.main()
