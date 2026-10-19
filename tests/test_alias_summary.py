"""Materialized alias usage must match the original incident-edge aggregation."""

import os
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest

from luca_memory.store import Cell, Edge, MemoryStore


class AliasSummaryTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        with self.store.transaction():
            for i in range(1, 8):
                self.store.add_cell(Cell(i, f"node{i}".encode(), 1))
            for i in (1, 2, 7):
                self.store.add_alias("shared", i)

    def tearDown(self):
        self.store.close()

    def assert_summaries(self):
        for i in range(1, 8):
            expected = self.store.connection.execute("SELECT COALESCE(MAX(last_used_at),0), COALESCE(SUM(use_count),0) FROM edges WHERE source_id=? OR target_id=?", (i, i)).fetchone()
            row = self.store.connection.execute("SELECT last_used_at,use_count FROM cell_degrees WHERE cell_id=?", (i,)).fetchone()
            self.assertEqual(tuple(row) if row else (0, 0), tuple(expected), i)
        old_order = [row[0] for row in self.store.connection.execute("""SELECT c.id FROM cell_aliases a JOIN cells c ON c.id=a.cell_id
            LEFT JOIN edges e ON e.source_id=c.id OR e.target_id=c.id WHERE a.alias='shared' GROUP BY c.id
            ORDER BY COALESCE(MAX(e.last_used_at),0) DESC, COALESCE(SUM(e.use_count),0) DESC,c.id""")]
        self.assertEqual([c.id for c in self.store.cells_by_alias("shared")], old_order)

    def test_recency_frequency_id_and_isolated_alias(self):
        self.assertEqual([c.id for c in self.store.cells_by_alias("shared")], [1, 2, 7])
        with self.store.transaction():
            self.store.add_edge(Edge(1, 3))
            self.store.add_edge(Edge(2, 4))
            self.store.touch_edge(2, 4, 10)
        self.assertEqual(self.store.cell_by_alias("shared").id, 2)
        with self.store.transaction():
            self.store.touch_edge(1, 3, 10)
        self.assertEqual(self.store.cell_by_alias("shared").id, 1)
        with self.store.transaction():
            self.store.touch_edge(2, 4, 10)
        self.assertEqual(self.store.cell_by_alias("shared").id, 2)
        self.assert_summaries()

    def test_delete_and_timestamp_decrease_preserve_exact_current_order(self):
        with self.store.transaction():
            for edge in (Edge(1, 3), Edge(1, 4), Edge(2, 5)):
                self.store.add_edge(edge)
            self.store.touch_edge(1, 3, 100)
            self.store.touch_edge(1, 4, 20)
            self.store.touch_edge(2, 5, 50)
        self.assertEqual(self.store.cell_by_alias("shared").id, 1)
        with self.store.transaction():
            self.store.remove_edge(1, 3)
        self.assertEqual(self.store.cell_by_alias("shared").id, 2)
        with self.store.transaction():
            self.store.touch_edge(2, 5, 5)
        self.assertEqual(self.store.cell_by_alias("shared").id, 1)
        self.assert_summaries()

    def test_self_loop_nonzero_insert_delete_and_rollback(self):
        with self.store.transaction():
            self.store.connection.execute("INSERT INTO edges VALUES(1,1,10,4)")
        self.assert_summaries()
        self.assertEqual(self.store.out_degree(1), 1)
        self.assertEqual(self.store.in_degree(1), 1)
        with self.assertRaisesRegex(RuntimeError, "rollback"):
            with self.store.transaction():
                self.store.touch_edge(1, 1, 20)
                raise RuntimeError("rollback")
        self.assert_summaries()
        with self.store.transaction():
            self.store.remove_edge(1, 1)
        self.assert_summaries()
        self.assertEqual(tuple(self.store.connection.execute("SELECT last_used_at,use_count FROM cell_degrees WHERE cell_id=1").fetchone()), (0, 0))

    def test_random_operations_match_reference(self):
        generator = random.Random(42)
        for _ in range(100):
            source, target = generator.randint(1, 7), generator.randint(1, 7)
            with self.store.transaction():
                if generator.random() < .25:
                    self.store.remove_edge(source, target)
                else:
                    self.store.add_edge(Edge(source, target))
                    self.store.touch_edge(source, target, generator.randint(0, 100))
            self.assert_summaries()

    def test_edge_addresses_cannot_change_in_place(self):
        with self.store.transaction():
            self.store.add_edge(Edge(1, 2))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
            with self.store.transaction():
                self.store.connection.execute("UPDATE edges SET target_id=3 WHERE source_id=1")
        self.assert_summaries()

    def test_old_schemas_migrate_and_reopen_without_double_counting(self):
        root = Path(os.getenv("LUCA_TEST_DIRECTORY", "D:/Test/Luca"))
        root.mkdir(parents=True, exist_ok=True)
        for old_usage in (False, True):
            with self.subTest(old_usage=old_usage), tempfile.TemporaryDirectory(prefix="alias-migration-", dir=root) as directory:
                path = Path(directory) / "old.sqlite"
                connection = sqlite3.connect(path)
                connection.executescript("""CREATE TABLE cells(id INTEGER PRIMARY KEY, content BLOB NOT NULL, created_at INTEGER NOT NULL);
                    INSERT INTO cells VALUES(1,X'61',1),(2,X'62',1),(3,X'63',1);
                    CREATE TABLE cell_aliases(alias TEXT PRIMARY KEY,cell_id INTEGER NOT NULL);
                    INSERT INTO cell_aliases VALUES('shared',1);
                    CREATE TABLE cell_degrees(cell_id INTEGER PRIMARY KEY,out_degree INTEGER NOT NULL DEFAULT 0,in_degree INTEGER NOT NULL DEFAULT 0);""")
                usage = ",last_used_at INTEGER NOT NULL DEFAULT 0,use_count INTEGER NOT NULL DEFAULT 0" if old_usage else ""
                connection.execute(f"CREATE TABLE edges(source_id INTEGER NOT NULL,target_id INTEGER NOT NULL{usage},PRIMARY KEY(source_id,target_id))")
                connection.execute("INSERT INTO edges VALUES(1,1,11,3)" if old_usage else "INSERT INTO edges VALUES(1,1)")
                connection.execute("INSERT INTO edges VALUES(1,2,10,2)" if old_usage else "INSERT INTO edges VALUES(1,2)")
                connection.commit()
                connection.close()
                for _ in range(2):
                    with MemoryStore(path) as store:
                        row = store.connection.execute("SELECT out_degree,in_degree,last_used_at,use_count FROM cell_degrees WHERE cell_id=1").fetchone()
                        self.assertEqual(tuple(row), (2, 1, 11, 5) if old_usage else (2, 1, 0, 0))
                        self.assertEqual(store.cell_by_alias("shared").id, 1)
                        with store.transaction():
                            store.add_alias("shared", 3)
                        self.assertEqual(len(store.cells_by_alias("shared")), 2)
