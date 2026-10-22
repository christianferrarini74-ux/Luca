"""Semantic coverage and deterministic routing budgets are distinct contracts."""

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from luca_memory.api import LucaRuntime
from luca_memory.classification import classification_from_assignments
from luca_memory.grouping_schema import grouping_schema
from luca_memory.maintenance import MemoryMaintenance
from luca_memory.maintenance_selection import route_categories
from luca_memory.node import load_node
from luca_memory.sleep_fixture import graph_snapshot, populate, verify_regrouping
from luca_memory.store import MemoryStore
from luca_memory.synaptic import (
    Directory,
    DirectoryEntry,
    StaleRevision,
    SynapticMemory,
)
from luca_memory.synaptic_settings import SynapticSettings


def classify_fixture(memory, fixture):
    assignments = {direction: {str(identity): category for identity, category in members.items()}
                   for direction, members in fixture["assignments"].items()}
    return classification_from_assignments({"assignments": assignments}, memory.directory(fixture["root"]))


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = Directory(1, 7, (DirectoryEntry(2, "Incoming"),),
                                   (DirectoryEntry(2, "Outgoing"), DirectoryEntry(3, "Other")), ())
        self.value = {"assignments": {"incoming": {"2": "Topic"}, "outgoing": {"2": "Topic", "3": None}}}

    def test_required_schema_and_parser_cover_every_directional_address(self):
        schema = grouping_schema(self.directory)["properties"]["assignments"]["properties"]
        self.assertEqual(schema["incoming"]["required"], ["2"])
        self.assertEqual(schema["outgoing"]["required"], ["2", "3"])
        result = classification_from_assignments(self.value, self.directory)
        self.assertEqual(result.categories(self.directory), (("incoming", "Topic", (2,)), ("outgoing", "Topic", (2,))))
        self.assertEqual(result.payload()["assignments"], self.value["assignments"])

    def test_omission_is_not_silently_treated_as_uncertainty(self):
        del self.value["assignments"]["outgoing"]["3"]
        with self.assertRaisesRegex(ValueError, "Every external"):
            classification_from_assignments(self.value, self.directory)

    def test_unknown_ids_invalid_labels_and_legacy_groups_are_rejected(self):
        for label in (False, " ", "x" * 257):
            self.value["assignments"]["incoming"]["2"] = label
            with self.subTest(label=label), self.assertRaises(ValueError):
                classification_from_assignments(self.value, self.directory)
        with self.assertRaises(ValueError):
            classification_from_assignments({"groups": []}, self.directory)

    def test_stale_and_forged_classifications_are_checked_again(self):
        result = classification_from_assignments(self.value, self.directory)
        with self.assertRaises(StaleRevision):
            result.categories(replace(self.directory, revision=8))
        for incoming in (((2, "Topic"), (2, "Topic")), ((99, "Topic"),), ((True, "Topic"),),
                         (("2", "Topic"),), ((2,),)):
            with self.subTest(incoming=incoming), self.assertRaises(ValueError):
                replace(result, incoming=incoming).categories(self.directory)

    def test_self_focus_and_internal_parts_are_not_classification_addresses(self):
        directory = Directory(1, 7, (DirectoryEntry(1, "Self"),), (), (DirectoryEntry(9, "Part"),))
        result = classification_from_assignments({"assignments": {"incoming": {}, "outgoing": {}}}, directory)
        self.assertEqual(result.categories(directory), ())


class CategoryRoutingTests(unittest.TestCase):
    def test_thirteen_compatible_nodes_need_only_eight_to_reduce_seven(self):
        groups = route_categories((("incoming", "Botany", tuple(range(1, 14))),), 7, 49)
        self.assertEqual(groups, (("Botany", "incoming", tuple(range(1, 9))),))

    def test_directions_and_labels_are_never_merged_to_make_the_budget(self):
        categories = (("incoming", "Botany", (1, 2, 3, 4)), ("outgoing", "Botany", (5, 6, 7, 8)))
        with self.assertRaisesRegex(ValueError, "insufficient compatible"):
            route_categories(categories, 7, 49)
        groups = route_categories(categories, 5, 49)
        self.assertEqual([len(group[2]) for group in groups], [4, 3])
        self.assertEqual([group[1] for group in groups], ["incoming", "outgoing"])

    def test_large_category_is_packed_into_bounded_nonoverlapping_groups(self):
        groups = route_categories((("outgoing", "Topic", tuple(range(200))),), 155, 49)
        self.assertEqual([len(group[2]) for group in groups], [49, 49, 49, 12])
        self.assertEqual(sum(len(group[2]) - 1 for group in groups), 155)
        members = [identity for group in groups for identity in group[2]]
        self.assertEqual(len(members), len(set(members)))

    def test_singletons_and_insufficient_one_level_capacity_do_not_force_a_merge(self):
        with self.assertRaises(ValueError):
            route_categories((("outgoing", "One", (1,)), ("outgoing", "Other", (2,))), 1, 49)
        with self.assertRaises(ValueError):
            route_categories((("outgoing", "Topic", tuple(range(2500))),), 2455, 49)

    def test_invalid_planner_limits_are_rejected(self):
        for reduction, limit in ((0, 49), (-1, 49), (7, 1), (True, 49)):
            with self.subTest(reduction=reduction, limit=limit), self.assertRaises(ValueError):
                route_categories((), reduction, limit)

    def test_seeded_random_plans_have_exact_reduction_and_minimal_new_nodes(self):
        generator = random.Random(504532)
        for _ in range(200):
            limit = generator.randint(2, 6)
            counts = [generator.randint(1, 12) for _ in range(generator.randint(1, 5))]
            categories, offset = [], 0
            # An independent DP tries all reductions possible in each semantic category.
            costs = {0: 0}
            for index, count in enumerate(counts):
                categories.append(("outgoing", f"Topic {index}", tuple(range(offset, offset + count))))
                offset += count
                options = {0: 0}
                for reduction in range(1, count):
                    nodes = (reduction + limit - 2) // (limit - 1)
                    if reduction + nodes <= count:
                        options[reduction] = nodes
                updated = {}
                for total, cost in costs.items():
                    for reduction, nodes in options.items():
                        value = total + reduction
                        updated[value] = min(updated.get(value, 10**9), cost + nodes)
                costs = updated
            if max(costs) == 0:
                continue
            required = generator.randint(1, max(costs))
            groups = route_categories(categories, required, limit)
            self.assertEqual(sum(len(group[2]) - 1 for group in groups), required)
            self.assertEqual(len(groups), costs[required])
            self.assertTrue(all(2 <= len(group[2]) <= limit for group in groups))

    def test_core_plan_reaches_exact_target_and_undo_preserves_full_graph(self):
        with MemoryStore(":memory:") as store:
            memory = SynapticMemory(store)
            settings = SynapticSettings()
            fixture = populate(memory, settings)
            classification = classify_fixture(memory, fixture)
            maintenance = MemoryMaintenance(memory, settings)
            plan = maintenance.plan(fixture["root"], classification)
            self.assertEqual((plan.degree_before, plan.degree_after, len(plan.groups)), (52, 45, 1))
            self.assertEqual(len(plan.groups[0].members), 8)
            operation = maintenance.apply(plan, automatic=True)
            self.assertTrue(all(verify_regrouping(memory, settings, fixture, operation)["checks"].values()))
            maintenance.restore(operation, confirmed=True)
            self.assertEqual(graph_snapshot(memory), fixture["before"])

    def test_all_null_or_insufficient_classification_leaves_memory_unchanged(self):
        with MemoryStore(":memory:") as store:
            memory = SynapticMemory(store)
            settings = SynapticSettings()
            fixture = populate(memory, settings)
            classification = classify_fixture(memory, fixture)
            empty = replace(classification, incoming=tuple((identity, None) for identity, _ in classification.incoming),
                            outgoing=tuple((identity, None) for identity, _ in classification.outgoing))
            with self.assertRaises(ValueError):
                MemoryMaintenance(memory, settings).plan(fixture["root"], empty)
            self.assertEqual(graph_snapshot(memory), fixture["before"])

    def test_content_or_title_change_invalidates_classification_before_planning(self):
        with MemoryStore(":memory:") as store:
            memory = SynapticMemory(store)
            settings = SynapticSettings()
            fixture = populate(memory, settings)
            classification = classify_fixture(memory, fixture)
            memory.update_node(replace(load_node(store, 5), title="Revised topic"))
            with self.assertRaises(StaleRevision):
                MemoryMaintenance(memory, settings).plan(fixture["root"], classification)

    def test_dashboard_preview_confirmation_and_restore_accept_classification_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = LucaRuntime({"storage": {"database": str(Path(directory) / "api.sqlite"),
                "seed": str(Path(__file__).parents[1] / "seed/library_empty_v1.json")},
                "runtime": {"language_adapter": "rules", "memory_backend": "host", "synaptic": {"automatic_sleep": False}}})
            try:
                memory = runtime.session.carousel.synaptic
                fixture = populate(memory, runtime.session.synaptic_settings)
                runtime.session.adapter = SimpleNamespace(propose_groups=lambda current, settings: classify_fixture(memory, fixture))
                preview = runtime.maintenance_operation("preview", {"node_id": fixture["root"]})
                self.assertEqual(preview["plan"]["degree_after"], 45)
                self.assertEqual(len(preview["plan"]["groups"]), 1)
                result = runtime.maintenance_operation("apply", {"plan_id": preview["plan_id"], "confirmed": True})
                runtime.maintenance_operation("restore", {"operation_id": result["operation_id"], "confirmed": True})
                self.assertEqual(graph_snapshot(memory), fixture["before"])
            finally:
                runtime.close()
