import unittest

from luca_memory import Cell, Edge, MemoryStore


class MemoryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        with self.store.transaction():
            for cell_id in range(1, 5):
                self.store.add_cell(Cell(cell_id, f"cell-{cell_id}".encode(), 1))

    def tearDown(self) -> None:
        self.store.close()

    def test_exact_outgoing_and_incoming_access(self) -> None:
        with self.store.transaction():
            self.store.add_edge(Edge(1, 2))
            self.store.add_edge(Edge(1, 3))
            self.store.add_edge(Edge(4, 2))

        self.assertEqual(self.store.edge(1, 2), Edge(1, 2))
        self.assertIsNone(self.store.edge(2, 1))
        self.assertEqual([edge.target_id for edge in self.store.outgoing(1)], [2, 3])
        self.assertEqual([edge.source_id for edge in self.store.incoming(2)], [1, 4])

    def test_rejects_edge_with_unknown_cell(self) -> None:
        with self.assertRaisesRegex(Exception, "FOREIGN KEY"):
            self.store.add_edge(Edge(1, 99))


if __name__ == "__main__":
    unittest.main()
