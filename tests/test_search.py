import json
import unittest
from pathlib import Path

from luca_memory import Cell, MemorySearch, MemoryStore, ThoughtBudget, load_curriculum


class MemorySearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        self.seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"
        load_curriculum(self.store, self.seed)
        self.search = MemorySearch(self.store)

    def tearDown(self) -> None:
        self.store.close()

    def test_full_text_search_finds_concepts_and_assertions(self) -> None:
        concepts = self.search.cells_by_text("sole", kind="concept")
        assertions = self.search.cells_by_text("sole luce", kind="assertion")

        self.assertEqual([result.cell.id for result in concepts], [12])
        self.assertEqual(len(assertions), 0)

        with self.store.transaction():
            self.store.add_cell(Cell(31, json.dumps({"kind": "concept", "label": "luce"}).encode(), 1))
        self.assertEqual(self.search.cells_by_text("luce", kind="concept")[0].cell.id, 31)

    def test_assertion_search_matches_explicit_references(self) -> None:
        sole = self.search.cell_by_alias("sole")
        scalda = self.search.cell_by_alias("scalda")
        pelle = self.search.cell_by_alias("pelle")

        results = self.search.assertions(
            subject_id=sole.id if sole else None,
            predicate_id=scalda.id if scalda else None,
            object_id=pelle.id if pelle else None,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].assertion_id, 27)

    def test_search_exposes_both_edge_directions_and_bounded_expansion(self) -> None:
        sole = self.search.cell_by_alias("sole")
        self.assertIsNotNone(sole)
        outgoing = self.search.outgoing(sole.id)
        incoming = self.search.incoming(sole.id)
        result = self.search.expand((sole.id,), ThoughtBudget(max_depth=2, ram_cells=8, ram_edges=10, vram_cells=3))

        self.assertTrue(any(edge.source_id == sole.id for edge in outgoing))
        self.assertEqual(incoming, [])
        self.assertLessEqual(len(result.context_cells), 8)
        self.assertLessEqual(len(result.context_edges), 10)

    def test_search_index_is_rebuilt_when_reopening_a_database(self) -> None:
        path = Path(__file__).parent / "search-runtime.sqlite"
        path.unlink(missing_ok=True)
        first = MemoryStore(path)
        load_curriculum(first, self.seed)
        first.close()

        reopened = MemoryStore(path)
        self.assertEqual(MemorySearch(reopened).cell_by_alias("fuoco").id, 5)
        self.assertEqual(MemorySearch(reopened).cells_by_text("fuoco", kind="concept")[0].cell.id, 5)
        reopened.close()
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
