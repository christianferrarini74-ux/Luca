"""Regression coverage for result copies, alternatives and transaction ownership."""

import unittest
from dataclasses import fields

from luca_memory.store import Cell, ConvergenceMatch, ConvergenceResult, MemoryStore


class ConvergenceResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.exact = ConvergenceMatch(10, 2, 2, 1, 1, 100, 5)
        self.partial = ConvergenceMatch(20, 1, 2, 1, 1, 90, 3)

    def test_recall_copy_preserves_selection_and_accepts_a_generator(self) -> None:
        original = ConvergenceResult(
            mode="associative",
            required_anchors=(1, 2),
            context_anchors=(3,),
            exact_matches=(self.exact,),
            partial_matches=(self.partial,),
            opened_ids=(99,),
            estimated_seed_edges=42,
            selection_ms=1.25,
            query_ms=2.5,
            elapsed_ms=3.75,
            recall_ms=4.0,
            strategy="hot_first_fallback",
        )

        copied = original.with_recall_outcome((nid for nid in ("20", "10", "20")), 8.5)

        self.assertIsNot(copied, original)
        self.assertEqual(copied.opened_ids, (20, 10, 20))
        self.assertEqual(copied.recall_ms, 8.5)
        self.assertEqual(original.opened_ids, (99,))
        self.assertEqual(original.recall_ms, 4.0)
        for field in fields(original):
            if field.name not in {"opened_ids", "recall_ms"}:
                with self.subTest(field=field.name):
                    self.assertEqual(getattr(copied, field.name), getattr(original, field.name))

    def test_alternatives_respect_mode_ranking_and_strict_partial_fallback(self) -> None:
        cases = (
            ("strict", (self.exact,), (self.partial,), (), (10,), (10,), (10,)),
            ("strict", (self.exact,), (self.partial,), (10,), (), (10,), ()),
            ("strict", (), (self.partial,), (), (20,), (), ()),
            ("strict", (), (self.partial,), (20,), (), (), ()),
            ("associative", (self.exact,), (self.partial,), (), (10, 20), (10, 20), (10, 20)),
            ("associative", (self.exact,), (self.partial,), (10,), (20,), (10, 20), (20,)),
            ("associative", (), (self.partial,), (), (20,), (20,), (20,)),
            ("strict", (), (), (99,), (), (), ()),
        )
        for index, (mode, exact, partial, opened, alternatives, ranked, unopened) in enumerate(cases):
            with self.subTest(case=index):
                result = ConvergenceResult(
                    mode=mode,
                    required_anchors=(1, 2),
                    context_anchors=(3,),
                    exact_matches=exact,
                    partial_matches=partial,
                    opened_ids=opened,
                )
                self.assertEqual(tuple(m.node_id for m in result.available_alternatives), alternatives)
                self.assertEqual(result.ranked_ids, ranked)
                self.assertEqual(result.selected_ids, ranked)
                self.assertEqual(result.unopened_ids, unopened)


class TransactionOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        self.addCleanup(self.store.close)

    def test_failed_nested_scope_leaves_outer_writes_committable(self) -> None:
        with self.store.transaction():
            self.store.add_cell(Cell(1, b"outer", 1))
            with self.assertRaisesRegex(RuntimeError, "inner failure"), self.store.transaction():
                self.store.add_cell(Cell(2, b"inner", 1))
                raise RuntimeError("inner failure")
            self.assertTrue(self.store.connection.in_transaction)
            self.assertIsNone(self.store.cell(2))
            self.store.add_cell(Cell(3, b"continued", 1))

        self.assertFalse(self.store.connection.in_transaction)
        self.assertEqual([cell.id for cell in self.store.all_cells()], [1, 3])
        indexed_ids = [row[0] for row in self.store.connection.execute(
            "SELECT cell_id FROM cell_search ORDER BY cell_id"
        )]
        self.assertEqual(indexed_ids, [1, 3])

    def test_successful_savepoint_does_not_commit_a_direct_write_transaction(self) -> None:
        self.store.add_cell(Cell(1, b"implicit transaction", 1))
        with self.store.transaction():
            self.store.add_cell(Cell(2, b"savepoint", 1))

        self.assertTrue(self.store.connection.in_transaction)
        self.store.connection.rollback()
        self.assertEqual(self.store.all_cells(), [])
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM cell_search").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
