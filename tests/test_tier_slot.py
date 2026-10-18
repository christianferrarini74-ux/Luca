import unittest

from luca_memory.node import KnowledgeNode
from luca_memory.store import Edge
from luca_memory.tiers import GraphView, TierSlot


class TierSlotAndGraphViewTests(unittest.TestCase):
    def test_slot_promotes_to_head_and_evicts_least_recently_recalled(self) -> None:
        slot = TierSlot("VRAM", capacity=3)
        n1 = KnowledgeNode(1, "n1", "Node 1", "Content 1")
        n2 = KnowledgeNode(2, "n2", "Node 2", "Content 2")
        n3 = KnowledgeNode(3, "n3", "Node 3", "Content 3")
        n4 = KnowledgeNode(4, "n4", "Node 4", "Content 4")

        self.assertEqual(slot.promote(n1), [])
        self.assertEqual(slot.promote(n2), [])
        self.assertEqual(slot.promote(n3), [])
        # Current head-to-tail order: 3, 2, 1
        self.assertEqual(slot.node_ids(), (3, 2, 1))

        # Recall n1 -> jumps to head: 1, 3, 2 (now n2 is the oldest!)
        self.assertEqual(slot.promote(n1), [])
        self.assertEqual(slot.node_ids(), (1, 3, 2))

        # Promote n4 -> evicts n2 from the tail
        evicted = slot.promote(n4)
        self.assertEqual([item.id for item in evicted], [2])
        self.assertEqual(slot.node_ids(), (4, 1, 3))

    def test_graph_view_self_assembles_prefix_suffix_domino_chains(self) -> None:
        view = GraphView()
        # Add edges in scrambled order: B:C, C:D, A:B
        view.add_edges([Edge(2, 3), Edge(3, 4), Edge(1, 2)])
        self.assertEqual(view.chains(), [(1, 2, 3, 4)])

    def test_graph_view_extracts_prefix_and_suffix_families_directly_from_edges(self) -> None:
        view = GraphView()
        # Prefix family 14:* -> (7, 19, 20) and Suffix family *:8 <- (7, 19)
        view.add_edges([Edge(14, 7), Edge(14, 19), Edge(14, 20), Edge(7, 8), Edge(19, 8)])
        prefix_fam = view.prefix_family(14)
        self.assertEqual(prefix_fam.pattern, "14:*")
        self.assertEqual(prefix_fam.member_ids, (7, 19, 20))
        suffix_fam = view.suffix_family(8)
        self.assertEqual(suffix_fam.pattern, "*:8")
        self.assertEqual(suffix_fam.member_ids, (7, 19))
        families = {(f.direction, f.anchor_id): f.member_ids for f in view.families(min_members=2)}
        self.assertEqual(families[("prefix", 14)], (7, 19, 20))
        self.assertEqual(families[("suffix", 8)], (7, 19))


if __name__ == "__main__":
    unittest.main()

