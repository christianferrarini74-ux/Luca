import unittest

from luca_memory import (
    Cell,
    Edge,
    MemoryStore,
    ThoughtBudget,
    ThoughtEngine,
    ThoughtRequest,
)


class ThoughtEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        with self.store.transaction():
            for cell_id in range(1, 6):
                self.store.add_cell(Cell(cell_id, str(cell_id).encode(), 1))
            for edge in (Edge(1, 2), Edge(3, 1), Edge(2, 4), Edge(5, 4)):
                self.store.add_edge(edge)

    def tearDown(self) -> None:
        self.store.close()

    def test_thought_expands_both_prefix_and_suffix_neighbourhoods(self) -> None:
        result = ThoughtEngine(self.store).run(
            ThoughtRequest((1,), ThoughtBudget(max_depth=3, ram_cells=10, ram_edges=10, vram_cells=2))
        )

        self.assertEqual(result.context_cells, (1, 2, 3, 4, 5))
        self.assertEqual(result.vram_focus, (1, 2))
        self.assertEqual(result.context_edges, (Edge(1, 2), Edge(2, 4), Edge(3, 1), Edge(5, 4)))

    def test_thought_never_exceeds_its_context_budget(self) -> None:
        result = ThoughtEngine(self.store).run(
            ThoughtRequest((1,), ThoughtBudget(max_depth=3, ram_cells=3, ram_edges=2, vram_cells=2))
        )

        self.assertLessEqual(len(result.context_cells), 3)
        self.assertLessEqual(len(result.context_edges), 2)


if __name__ == "__main__":
    unittest.main()
