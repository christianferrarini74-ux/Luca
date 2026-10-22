"""Exercise real maintenance on controlled graphs, independent of model eloquence."""

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from luca_memory.maintenance import IdleMaintenance, MemoryMaintenance
from luca_memory.node import load_node
from luca_memory.sleep_check import run_worker
from luca_memory.sleep_fixture import (
    graph_snapshot,
    oracle_groups,
    populate,
    verify_regrouping,
)
from luca_memory.store import MemoryStore
from luca_memory.synaptic import StaleRevision, SynapticMemory
from luca_memory.synaptic_settings import SynapticSettings
from luca_memory.tiers import SynapticCarousel


class SleepSimulationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "sleep.sqlite"
        self.store = MemoryStore(self.path)
        self.memory = SynapticMemory(self.store)
        self.settings = SynapticSettings(edge_upper=6, edge_target=4, idle_seconds=1, sleep_poll_seconds=1)
        self.fixture = populate(self.memory, self.settings)
        self.maintenance = MemoryMaintenance(self.memory, self.settings)
        self.groups = oracle_groups(self.fixture)

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def reopen(self):
        self.store.close()
        self.store = MemoryStore(self.path)
        self.memory = SynapticMemory(self.store)
        self.maintenance = MemoryMaintenance(self.memory, self.settings)

    def apply(self):
        return self.maintenance.apply(self.maintenance.plan(self.fixture["root"], self.groups), confirmed=True)

    def assert_untouched(self):
        self.assertEqual(graph_snapshot(self.memory), self.fixture["before"])
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM maintenance_operations").fetchone()[0], 0)

    def test_default_thresholds_and_all_original_paths_survive_regroup_restart_restore(self):
        # Exercise the distributed 50/45 thresholds too, not just the small unit fixture.
        with MemoryStore(Path(self.temporary.name) / "default.sqlite") as store:
            memory = SynapticMemory(store)
            settings = SynapticSettings()
            fixture = populate(memory, settings)
            maintenance = MemoryMaintenance(memory, settings)
            self.assertEqual(maintenance.candidates(), (fixture["root"],))
            operation = maintenance.apply(maintenance.plan(fixture["root"], oracle_groups(fixture)), automatic=True)
            result = verify_regrouping(memory, settings, fixture, operation)
            self.assertTrue(all(result["checks"].values()), result)
            self.assertTrue(result["thematically_pure"])
            self.assertEqual((result["degree_before"], result["degree_after"]), (52, 4))
        with MemoryStore(Path(self.temporary.name) / "default.sqlite") as store:
            memory = SynapticMemory(store)
            self.assertTrue(all(verify_regrouping(memory, settings, fixture, operation)["checks"].values()))
            MemoryMaintenance(memory, settings).restore(operation, confirmed=True)
            self.assertEqual(graph_snapshot(memory), fixture["before"])

    def test_real_polling_worker_uses_inactivity_and_stops_without_orphan_threads(self):
        groups = self.groups
        class Adapter:
            finished = threading.Event()
            calls = 0
            def propose_groups(adapter, directory, settings):
                adapter.calls += 1
                adapter.finished.set()
                return groups
        adapter = Adapter()
        result = run_worker(self.memory, self.settings, adapter, timeout=5)
        self.assertTrue(result["worker_stopped"])
        self.assertGreaterEqual(result["seconds"], self.settings.idle_seconds)
        self.assertEqual(adapter.calls, 1)
        self.assertIsNotNone(result["operation_id"])
        self.assertTrue(all(verify_regrouping(self.memory, self.settings, self.fixture, result["operation_id"])["checks"].values()))

    def test_structurally_valid_mixed_theme_group_is_reported_not_mistaken_for_semantic_success(self):
        mixed = [{"title": "Astronomia", "direction": "outgoing",
                  "members": list(self.fixture["assignments"]["outgoing"])}, self.groups[0]]
        operation = self.maintenance.apply(self.maintenance.plan(self.fixture["root"], mixed), confirmed=True)
        result = verify_regrouping(self.memory, self.settings, self.fixture, operation)
        self.assertTrue(all(result["checks"].values()), result)
        self.assertFalse(result["thematically_pure"])
        self.assertTrue(any(len(group["source_categories"]) > 1 for group in result["groups"]))

    def test_resident_family_part_refreshes_directory_and_navigates_through_generated_group(self):
        with closing(SynapticCarousel(self.store, vram_capacity=1, ram_capacity=1)) as carousel:
            part = self.fixture["parts"][0]
            carousel.step_to(part)
            old = carousel.synaptic.directory(part)
            self.apply()
            current = carousel.synaptic.directory(part)
            self.assertNotEqual(current.revision, old.revision)
            self.assertEqual(current.focus_id, self.fixture["root"])
            group = next(entry.id for entry in current.outgoing if entry.id > len(self.fixture["before"]["cells"]))
            carousel.synaptic.validate_step(part, group, current.revision)
            carousel.step_to(group)
            self.assertEqual(carousel.focus_id, group)
            directory = carousel.synaptic.directory(group)
            member = directory.outgoing[0].id
            carousel.synaptic.validate_step(group, member, directory.revision)
            carousel.step_to(member)
            self.assertEqual(carousel.reading_id, member)

    def test_activity_cancels_inflight_proposal_before_queued_mutation(self):
        entered, release, mutated = threading.Event(), threading.Event(), threading.Event()
        errors = []
        groups = self.groups
        class Adapter:
            def propose_groups(adapter, directory, settings):
                entered.set()
                if not release.wait(3):
                    raise TimeoutError("Test release timed out")
                return groups
        worker = IdleMaintenance(self.maintenance, Adapter())
        worker.last_activity = 0
        root = self.fixture["root"]
        def mutation():
            try:
                self.memory.update_node(replace(load_node(self.store, root), content="Queued update"))
                mutated.set()
            except Exception as error:  # noqa: BLE001 - Surface thread failures in the test.
                errors.append(error)
        sleeping = threading.Thread(target=lambda: worker.run_once(now=10))
        sleeping.start()
        writing = None
        try:
            self.assertTrue(entered.wait(2))
            worker.touch()  # Same ordering used by runtime requests: signal before acquiring the lock.
            writing = threading.Thread(target=mutation)
            writing.start()
            self.assertFalse(mutated.wait(0.05))
        finally:
            release.set()
            sleeping.join(4)
            if writing:
                writing.join(4)
            worker.close()
        self.assertFalse(sleeping.is_alive())
        self.assertFalse(writing.is_alive())
        self.assertEqual(errors, [])
        self.assertIsNone(worker.last_operation)
        self.assertTrue(mutated.is_set())
        self.assertEqual(self.memory.directory(root).external_degree, 8)
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM maintenance_operations").fetchone()[0], 0)

    def test_shutdown_during_owned_worker_proposal_cancels_and_joins(self):
        entered, release = threading.Event(), threading.Event()
        groups = self.groups
        class Adapter:
            def propose_groups(adapter, directory, settings):
                entered.set()
                if not release.wait(3):
                    raise TimeoutError("Test release timed out")
                return groups
        worker = IdleMaintenance(self.maintenance, Adapter())
        worker.start()
        closing = None
        try:
            self.assertTrue(entered.wait(3))
            closing = threading.Thread(target=worker.close)
            closing.start()
            self.assertTrue(worker._stop.wait(2))
            self.assertTrue(closing.is_alive())
        finally:
            release.set()
            worker.close()
            if closing:
                closing.join(3)
        self.assertFalse(worker._thread.is_alive())
        self.assertIsNone(worker.last_operation)
        self.assert_untouched()

    def test_invalid_proposal_backoff_then_retry_without_partial_writes(self):
        valid = self.groups
        class Adapter:
            calls = 0
            def propose_groups(adapter, directory, settings):
                adapter.calls += 1
                return [] if adapter.calls == 1 else valid
        adapter = Adapter()
        worker = IdleMaintenance(self.maintenance, adapter)
        worker.last_activity = 0
        self.assertIsNone(worker.run_once(now=10))
        self.assertIn("edge_target", worker.last_error)
        self.assert_untouched()
        self.assertIsNone(worker.run_once(now=11))
        self.assertEqual(adapter.calls, 1)
        self.assertIsNotNone(worker.run_once(now=10 + self.settings.sleep_retry_seconds))
        self.assertIsNone(worker.last_error)
        self.assertEqual(adapter.calls, 2)

    def test_disabled_sleep_never_calls_adapter(self):
        class Adapter:
            def propose_groups(adapter, directory, settings):
                raise AssertionError("Disabled sleep called the model")
        maintenance = MemoryMaintenance(self.memory, replace(self.settings, automatic_sleep=False))
        worker = IdleMaintenance(maintenance, Adapter())
        worker.last_activity = 0
        self.assertIsNone(worker.run_once(now=10))
        self.assert_untouched()

    def test_stale_neighbor_title_invalidates_plan_and_modified_group_blocks_restore(self):
        plan = self.maintenance.plan(self.fixture["root"], self.groups)
        member = self.groups[0]["members"][0]
        self.memory.update_node(replace(load_node(self.store, member), title="Revised topic"))
        with self.assertRaises(StaleRevision):
            self.maintenance.apply(plan, confirmed=True)
        operation = self.apply()
        row = self.store.connection.execute("SELECT payload FROM maintenance_operations WHERE id=?", (operation,)).fetchone()
        group = json.loads(row[0])["created_ids"][0]
        self.memory.update_node(replace(load_node(self.store, group), content="Edited index"))
        snapshot = graph_snapshot(self.memory)
        with self.assertRaises(StaleRevision):
            self.maintenance.restore(operation, confirmed=True)
        self.assertEqual(graph_snapshot(self.memory), snapshot)

    def test_failure_at_commit_boundary_rolls_back_indexes_ids_and_revision(self):
        revision, next_id = self.store.revision, self.store.next_cell_id()
        with (
            patch.object(self.memory, "_event", side_effect=RuntimeError("Injected precommit failure")),
            self.assertRaises(RuntimeError),
        ):
            self.apply()
        self.assert_untouched()
        self.assertEqual(self.store.revision, revision)
        self.assertEqual(self.store.next_cell_id(), next_id)
        self.reopen()
        self.assert_untouched()

    def test_abrupt_process_exit_before_commit_recovers_complete_original_graph(self):
        revision = self.store.revision
        self.store.close()
        # Exit without finally/connection.close after all writes, before the enclosing COMMIT.
        code = """
import json, os, sys
from unittest.mock import patch
from luca_memory.store import MemoryStore
from luca_memory.synaptic import SynapticMemory
from luca_memory.maintenance import MemoryMaintenance
from luca_memory.synaptic_settings import SynapticSettings
with MemoryStore(sys.argv[1]) as store:
    memory = SynapticMemory(store)
    maintenance = MemoryMaintenance(memory, SynapticSettings(edge_upper=6, edge_target=4))
    plan = maintenance.plan(1, json.loads(sys.argv[2]))
    with patch.object(memory, '_event', side_effect=lambda *args: os._exit(73)):
        maintenance.apply(plan, confirmed=True)
"""
        try:
            result = subprocess.run([sys.executable, "-c", code, str(self.path), json.dumps(self.groups)],
                                    capture_output=True, text=True, timeout=15, check=False)
        finally:
            self.store = MemoryStore(self.path)
            self.memory = SynapticMemory(self.store)
            self.maintenance = MemoryMaintenance(self.memory, self.settings)
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assert_untouched()
        self.assertEqual(self.store.revision, revision)
        self.assertEqual(self.store.connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertIsNotNone(self.apply())

    def test_repeated_sleep_restore_cycles_do_not_reuse_committed_group_ids(self):
        previous = set()
        for _ in range(3):
            operation = self.apply()
            payload = self.store.connection.execute("SELECT payload FROM maintenance_operations WHERE id=?", (operation,)).fetchone()[0]
            created = set(json.loads(payload)["created_ids"])
            self.assertFalse(created & previous)
            previous.update(created)
            self.maintenance.restore(operation, confirmed=True)
            self.assertEqual(graph_snapshot(self.memory), self.fixture["before"])
