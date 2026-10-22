"""Grouping addresses are unique by construction, without choosing semantics."""

import unittest

from luca_memory.grouping_schema import grouping_schema, groups_from_assignments
from luca_memory.synaptic import Directory, DirectoryEntry


class GroupingSchemaTests(unittest.TestCase):
    def setUp(self):
        self.directory = Directory(1, 1, (DirectoryEntry(4, "Four"),),
                                   (DirectoryEntry(2, "Two"), DirectoryEntry(3, "Three")), ())

    def test_schema_does_not_offer_unknown_ids_or_duplicate_membership_lists(self):
        directions = grouping_schema(self.directory)["properties"]["assignments"]["properties"]
        self.assertEqual(set(directions["outgoing"]["properties"]), {"2", "3"})
        self.assertFalse(directions["outgoing"]["additionalProperties"])
        self.assertEqual(set(directions["incoming"]["properties"]), {"4"})

    def test_model_labels_define_groups_without_core_semantic_choices(self):
        result = groups_from_assignments({"assignments": {"incoming": {"4": None},
            "outgoing": {"2": "Model label", "3": "Model label"}}}, self.directory)
        self.assertEqual(result, [{"title": "Model label", "direction": "outgoing", "members": [2, 3]}])

    def test_invalid_assignments_are_rejected(self):
        for values in ({"999": "Group"}, {"2": True}, {"2": " "}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                groups_from_assignments({"assignments": {"incoming": {}, "outgoing": values}}, self.directory)

    def test_opposite_directions_remain_distinct_even_with_the_same_label(self):
        result = groups_from_assignments({"assignments": {"incoming": {"4": "Shared"},
            "outgoing": {"2": "Shared", "3": "Shared"}}}, self.directory)
        self.assertEqual(len(result), 2)
        self.assertEqual([group["direction"] for group in result], ["incoming", "outgoing"])
