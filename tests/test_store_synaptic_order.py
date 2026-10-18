import unittest

from luca_memory.store import Cell, Edge, MemoryStore


class SynapticEdgeOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        with self.store.transaction():
            for cell_id in range(1, 6):
                self.store.add_cell(Cell(cell_id, f"node-{cell_id}".encode(), 1))
            # Outgoing from 1: 1:2, 1:3, 1:4
            self.store.add_edge(Edge(1, 2))
            self.store.add_edge(Edge(1, 3))
            self.store.add_edge(Edge(1, 4))
            # Incoming to 5: 2:5, 3:5, 4:5
            self.store.add_edge(Edge(2, 5))
            self.store.add_edge(Edge(3, 5))
            self.store.add_edge(Edge(4, 5))

    def tearDown(self) -> None:
        self.store.close()

    def test_used_edges_move_to_front_while_unused_drift_back(self) -> None:
        # Initially ordered by ID because all have last_used_at=0
        self.assertEqual([e.target_id for e in self.store.outgoing(1)], [2, 3, 4])

        # Touch edge 1:4 at t=10, then 1:3 at t=20
        with self.store.transaction():
            self.store.touch_edge(1, 4, used_at=10)
            self.store.touch_edge(1, 3, used_at=20)

        # Now 1:3 is most recent, followed by 1:4, while unused 1:2 drifted to the end
        self.assertEqual([e.target_id for e in self.store.outgoing(1)], [3, 4, 2])

    def test_incoming_suffix_edges_also_follow_synaptic_recency(self) -> None:
        self.assertEqual([e.source_id for e in self.store.incoming(5)], [2, 3, 4])

        with self.store.transaction():
            self.store.touch_edge(4, 5, used_at=100)

        self.assertEqual([e.source_id for e in self.store.incoming(5)], [4, 2, 3])


if __name__ == "__main__":
    unittest.main()
