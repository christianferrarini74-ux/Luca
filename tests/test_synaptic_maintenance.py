"""Directional regrouping, confirmation, stale plans and lossless route restoration."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from luca_memory.maintenance import IdleMaintenance, MemoryMaintenance
from luca_memory.node import KnowledgeNode, load_node
from luca_memory.store import MemoryStore
from luca_memory.synaptic import StaleRevision, SynapticMemory
from luca_memory.synaptic_settings import SynapticSettings


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = MemoryStore(Path(self.temp.name) / "memory.sqlite")
        self.memory = SynapticMemory(self.store)
        self.settings = SynapticSettings(edge_upper=6, edge_target=4)
        self.maintenance = MemoryMaintenance(self.memory, self.settings)
        for index in range(1, 11):
            self.memory.update_node(KnowledgeNode(index, f"n{index}", f"Node {index}", f"Payload {index}"))
        for index in (2, 3, 4, 5):
            self.memory.connect(1, index)
        for index in (6, 7, 8):
            self.memory.connect(index, 1)
        self.groups = [{"title": "Outgoing group", "direction": "outgoing", "members": [2, 3, 4]},
                       {"title": "Incoming group", "direction": "incoming", "members": [6, 7]}]

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_confirmed_regrouping_preserves_direction_and_restores_routes(self):
        plan = self.maintenance.plan(1, self.groups)
        with self.assertRaises(ValueError):
            self.maintenance.apply(plan)
        operation = self.maintenance.apply(plan, confirmed=True)
        directory = self.memory.directory(1)
        self.assertEqual(directory.external_degree, 4)
        record = self.store.connection.execute("SELECT payload FROM maintenance_operations WHERE id=?", (operation,)).fetchone()[0]
        import json
        record = json.loads(record)
        outgoing, incoming = record["created_ids"]
        self.assertEqual(self.memory.parts(1), ())
        self.assertEqual(self.memory.root(outgoing), outgoing)
        self.assertEqual({e.id for e in self.memory.directory(outgoing).outgoing}, {2, 3, 4})
        self.assertEqual({e.id for e in self.memory.directory(incoming).incoming}, {6, 7})
        self.assertIsNone(self.store.edge(1, 2))
        self.assertIsNotNone(self.store.edge(1, outgoing))
        self.assertIsNotNone(self.store.edge(outgoing, 2))
        with self.store.transaction():
            self.store.touch_edge(outgoing, 2, 123)
        self.maintenance.restore(operation, confirmed=True)
        self.assertEqual(self.memory.directory(1).external_degree, 7)
        self.assertIsNotNone(self.store.edge(1, 2))
        self.assertIsNotNone(self.store.edge(6, 1))
        self.assertIsNone(self.store.cell(outgoing))
        self.assertGreater(self.store.next_cell_id(), max(record["created_ids"]))
        self.assertEqual(self.store.connection.execute("SELECT use_count FROM edges WHERE source_id=1 AND target_id=2").fetchone()[0], 1)

    def test_automatic_candidates_exclude_internal_family_edges(self):
        self.memory.attach_part(1, 9)
        self.memory.attach_part(1, 10)
        self.assertEqual(self.maintenance.candidates(), (1,))
        self.memory.connect(1, 5, remove=True)
        self.assertEqual(self.maintenance.candidates(), ())

    def test_manual_above_target_below_upper_and_noop_at_target(self):
        self.memory.connect(1, 5, remove=True)
        self.assertEqual(self.memory.directory(1).external_degree, 6)
        plan = self.maintenance.plan(1, self.groups)
        self.assertIsNone(self.maintenance.apply(plan, automatic=True))
        self.maintenance.apply(plan, confirmed=True)
        self.assertLessEqual(self.memory.directory(1).external_degree, 4)
        self.assertIsNone(self.maintenance.apply(self.maintenance.plan(1, []), confirmed=True))

    def test_stale_plan_and_modified_group_restore_are_rejected(self):
        plan = self.maintenance.plan(1, self.groups)
        self.memory.connect(1, 9)
        with self.assertRaises(StaleRevision):
            self.maintenance.apply(plan, confirmed=True)
        operation = self.maintenance.apply(self.maintenance.plan(1, self.groups + [
            {"title": "More", "direction": "outgoing", "members": [5, 9]}]), confirmed=True)
        group_id = self.memory.directory(1).outgoing[0].id
        self.memory.update_node(replace(load_node(self.store, group_id), content="Changed"))
        with self.assertRaises(StaleRevision):
            self.maintenance.restore(operation, confirmed=True)

    def test_failed_batch_rolls_back_every_node_edge_index_and_revision(self):
        before = self.store.revision
        with (
            patch.object(self.memory, "_event", side_effect=RuntimeError("Injected failure")),
            self.assertRaises(RuntimeError),
        ):
            self.maintenance.apply(self.maintenance.plan(1, self.groups), confirmed=True)
        self.assertEqual(self.store.revision, before)
        self.assertEqual(self.store.cell_count(), 10)
        self.assertEqual(self.memory.directory(1).external_degree, 7)
        self.assertIsNotNone(self.store.edge(1, 2))
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM maintenance_operations").fetchone()[0], 0)

    def test_invalid_groupings_are_not_applied(self):
        for groups in ([{"title": "Bad", "direction": "outgoing", "members": [2, 999]}],
                       [{"title": "Bad", "direction": "outgoing", "members": [2, 2]}],
                       [{"title": "Bad", "direction": "outgoing", "members": [2, 3]}],
                       [{"title": "Bad", "direction": "mixed", "members": [2, 6]}]):
            with self.assertRaises(ValueError):
                self.maintenance.plan(1, groups)
        self.assertEqual(self.memory.directory(1).external_degree, 7)

    def test_idle_sleep_only_runs_after_inactivity_and_over_upper_limit(self):
        class Adapter:
            calls = 0
            def propose_groups(adapter, directory, settings):
                adapter.calls += 1
                return self.groups
        adapter = Adapter()
        sleep = IdleMaintenance(self.maintenance, adapter)
        sleep.last_activity = 100
        self.assertIsNone(sleep.run_once(now=101))
        self.assertEqual(adapter.calls, 0)
        self.assertIsNotNone(sleep.run_once(now=200))
        self.assertEqual(self.memory.directory(1).external_degree, 4)
        sleep.run_once(now=201)
        self.assertEqual(adapter.calls, 1)

    def test_new_user_activity_cancels_idle_plan_before_commit(self):
        class Adapter:
            def propose_groups(adapter, directory, settings):
                sleep.touch()
                return self.groups
        sleep = IdleMaintenance(self.maintenance, Adapter())
        sleep.last_activity = 100
        self.assertIsNone(sleep.run_once(now=200))
        self.assertEqual(self.memory.directory(1).external_degree, 7)

    def test_failed_idle_proposal_is_visible_and_not_retried_in_a_loop(self):
        class Adapter:
            calls = 0
            def propose_groups(adapter, directory, settings):
                adapter.calls += 1
                return []
        adapter = Adapter()
        sleep = IdleMaintenance(self.maintenance, adapter)
        sleep.last_activity = 100
        sleep.run_once(now=200)
        sleep.run_once(now=201)
        self.assertEqual(adapter.calls, 1)
        self.assertIn("edge_target", sleep.last_error)
        self.assertEqual(self.memory.directory(1).external_degree, 7)

    def test_owned_sleep_worker_stops_cleanly(self):
        class Adapter:
            def propose_groups(adapter, directory, settings):
                return self.groups
        sleep = IdleMaintenance(self.maintenance, Adapter())
        sleep.start()
        self.assertTrue(sleep._thread.is_alive())
        sleep.close()
        self.assertFalse(sleep._thread.is_alive())

    def test_grouping_node_cannot_become_a_fragment_or_lose_added_aliases_on_restore(self):
        operation = self.maintenance.apply(self.maintenance.plan(1, self.groups), confirmed=True)
        group_id = next(entry.id for entry in self.memory.directory(1).outgoing if entry.id > 10)
        with self.assertRaises(ValueError):
            self.memory.attach_part(9, group_id)
        with self.store.transaction():
            self.store.add_alias("important new reference", group_id)
        with self.assertRaises(StaleRevision):
            self.maintenance.restore(operation, confirmed=True)
        self.assertEqual(self.store.cell_by_alias("important new reference").id, group_id)
