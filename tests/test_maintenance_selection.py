"""Check target-stop selection independently against exhaustive whole-group choices."""

import itertools
import random
import unittest

from luca_memory.maintenance import EdgeGroup
from luca_memory.maintenance_selection import select_groups


def groups_for(reductions):
    return tuple(EdgeGroup(f"Group {index}", "outgoing", tuple(range(reduction + 1)))
                 for index, reduction in enumerate(reductions))


class MaintenanceSelectionTests(unittest.TestCase):
    def test_exact_target_can_use_a_later_combination_without_clipping_members(self):
        groups = groups_for((6, 4, 3, 12))
        self.assertEqual(select_groups(groups, 7), (groups[1], groups[2]))

    def test_indivisible_fallback_minimizes_overshoot(self):
        groups = groups_for((12, 8, 10))
        self.assertEqual(select_groups(groups, 7), (groups[1],))

    def test_ties_prefer_fewer_groups_then_stable_proposal_order(self):
        groups = groups_for((3, 4, 7, 7))
        self.assertEqual(select_groups(groups, 7), (groups[2],))

    def test_insufficient_proposals_are_rejected(self):
        with self.assertRaises(ValueError):
            select_groups(groups_for((2, 3)), 7)

    def test_random_small_inputs_match_exhaustive_minimum(self):
        generator = random.Random(5045)
        for _ in range(100):
            groups = groups_for([generator.randint(1, 12) for _ in range(generator.randint(1, 8))])
            required = generator.randint(1, sum(len(group.members) - 1 for group in groups))
            options = []
            for count in range(1, len(groups) + 1):
                for indices in itertools.combinations(range(len(groups)), count):
                    total = sum(len(groups[index].members) - 1 for index in indices)
                    if total >= required:
                        options.append((total, count, indices))
            expected = min(options)
            self.assertEqual(select_groups(groups, required), tuple(groups[index] for index in expected[2]))
