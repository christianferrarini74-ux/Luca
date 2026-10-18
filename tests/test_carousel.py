import unittest

from luca_memory.node import KnowledgeNode, save_node
from luca_memory.store import Edge, MemoryStore
from luca_memory.tiers import SynapticCarousel


class SynapticCarouselTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        # Create chain A(1) -> B(2) -> C(3) -> D(4) and E(5) -> C(3)
        with self.store.transaction():
            for idx, slug in ((1, "a"), (2, "b"), (3, "c"), (4, "d"), (5, "e")):
                save_node(self.store, KnowledgeNode(idx, slug, f"Node {slug.upper()}", f"Articulated thought {slug.upper()}"))
            self.store.add_edge(Edge(1, 2))  # A:B (suffix B)
            self.store.add_edge(Edge(2, 3))  # B:C (prefix B)
            self.store.add_edge(Edge(3, 4))  # C:D (2nd degree from B)
            self.store.add_edge(Edge(5, 3))  # E:C (converges on C)

    def tearDown(self) -> None:
        self.store.close()

    def test_recall_pulls_only_first_degree_and_step_to_opens_second_degree(self) -> None:
        carousel = SynapticCarousel(self.store, vram_capacity=8, ram_capacity=16)

        # Recall B(2): must bring B(2) + A(1) + C(3) into VRAM, but NOT D(4) or E(5)
        event = carousel.recall(2)
        self.assertEqual(event.center_id, 2)
        self.assertEqual(set(carousel.vram.node_ids()), {1, 2, 3})
        self.assertEqual(carousel.vram.node_ids()[0], 2)  # B is at the very head of VRAM
        self.assertNotIn(4, carousel.vram)
        self.assertEqual(set(carousel.vram_graph.edges()), {Edge(1, 2), Edge(2, 3)})

        # Now shift thought focus onto C(3) -> opens C's 1st degree (D(4) and E(5))
        carousel.step_to(3)
        self.assertIn(4, carousel.vram)
        self.assertIn(5, carousel.vram)
        self.assertIn(Edge(3, 4), carousel.vram_graph.edges())

    def test_overflow_cascades_from_vram_to_ram_to_ssd_and_recalls_back(self) -> None:
        # Small slots: VRAM=2, RAM=2
        carousel = SynapticCarousel(self.store, vram_capacity=2, ram_capacity=2)
        with self.store.transaction():
            for idx in range(10, 15):
                save_node(self.store, KnowledgeNode(idx, f"n{idx}", f"Node {idx}", f"Thought {idx}"))

        carousel.recall(10)
        carousel.recall(11)
        self.assertEqual(carousel.vram.node_ids(), (11, 10))
        self.assertEqual(carousel.ram.node_ids(), ())

        # Recall 12 -> 10 overflows from VRAM into RAM
        carousel.recall(12)
        self.assertEqual(carousel.vram.node_ids(), (12, 11))
        self.assertEqual(carousel.ram.node_ids(), (10,))

        # Recall 13 -> 11 overflows into RAM: RAM has (11, 10)
        carousel.recall(13)
        self.assertEqual(carousel.vram.node_ids(), (13, 12))
        self.assertEqual(carousel.ram.node_ids(), (11, 10))

        # Recall 14 -> 12 overflows into RAM, pushing 10 out of RAM back to SSD!
        event = carousel.recall(14)
        self.assertEqual(carousel.vram.node_ids(), (14, 13))
        self.assertEqual(carousel.ram.node_ids(), (12, 11))
        self.assertEqual(event.evicted_to_ssd, (10,))
        self.assertNotIn(10, carousel.vram)
        self.assertNotIn(10, carousel.ram)

        # Now recall 10 from deep SSD -> catapulted back to head of VRAM!
        carousel.recall(10)
        self.assertEqual(carousel.vram.node_ids()[0], 10)

    def test_synaptic_convergence_reflex_automatically_opens_shared_node(self) -> None:
        carousel = SynapticCarousel(self.store, vram_capacity=8, ram_capacity=16)
        # B(2) and E(5) both point to C(3) (2:3 and 5:3).
        # Recalling B(2) and E(5) together converges on C(3) (2 touches) -> C(3) opens automatically and pulls D(4)!
        carousel.recall_with_convergence([2, 5], convergence_threshold=2)
        self.assertIn(3, carousel.expanded_in_vram)
        self.assertIn(4, carousel.vram)

    def test_candidate_beyond_preload_limit_is_reached_across_turns(self) -> None:
        # vram_capacity=4 -> edge_fetch_limit = max(32, 16) = 32
        carousel = SynapticCarousel(self.store, vram_capacity=4, ram_capacity=8)
        with self.store.transaction():
            save_node(self.store, KnowledgeNode(100, "fam_a", "Family A", "Root family A"))
            save_node(self.store, KnowledgeNode(101, "fam_old", "Old Context Family", "Old context hub"))
            save_node(self.store, KnowledgeNode(200, "fam_b", "Family B", "Second family B"))
            # Node 888 is connected ONLY to old context hubs (100 and 101), NOT to the new anchor 200
            save_node(self.store, KnowledgeNode(888, "old_only", "Old Context Only", "Connected only to 100 and 101"))
            self.store.add_edge(Edge(100, 888))
            self.store.add_edge(Edge(101, 888))
            self.store.touch_edge(100, 888, 5000)
            self.store.touch_edge(101, 888, 5000)

            # Give both Family 100 and Family 200 50 hot filler children (> edge_fetch_limit=32)
            for offset in range(1, 51):
                cid_a = 1000 + offset
                cid_b = 2000 + offset
                save_node(self.store, KnowledgeNode(cid_a, f"a_{offset}", f"Child A {offset}", "Filler A"))
                save_node(self.store, KnowledgeNode(cid_b, f"b_{offset}", f"Child B {offset}", "Filler B"))
                self.store.add_edge(Edge(100, cid_a))
                self.store.add_edge(Edge(200, cid_b))
                self.store.touch_edge(100, cid_a, 1000)
                self.store.touch_edge(200, cid_b, 1000)

            # Target node #999 sits at rank 51 of BOTH families (use_count=0, outside preload limit 32 of both 100 and 200!)
            save_node(self.store, KnowledgeNode(999, "deep_target", "Deep SSD Target", "Shared member beyond preload"))
            self.store.add_edge(Edge(100, 999))
            self.store.add_edge(Edge(200, 999))

        # Turn 1: open old context hubs 100 and 101
        carousel.recall(101)
        event_100 = carousel.recall(100)
        self.assertNotIn(999, event_100.first_degree_ids)  # #999 was NOT preloaded by recall(100)!

        # Turn 2: ask about Family 200 -> must intersect 200 with context (100) on full SSD and open #999 (NOT #888!)
        carousel.recall_with_convergence([200])
        self.assertIsNotNone(carousel.last_convergence)
        self.assertEqual(carousel.last_convergence.selected_ids, (999,))
        self.assertEqual(carousel.vram.node_ids()[0], 999)
        self.assertIn(999, carousel.expanded_in_vram)
        self.assertNotIn(888, carousel.expanded_in_vram)
        # And #999's edges from 100 and 200 were reinforced to rank #1!
        self.assertEqual(self.store.prefix_family_ids(100, limit=1), (999,))
        self.assertEqual(self.store.prefix_family_ids(200, limit=1), (999,))

    def test_three_families_strict_vs_associative_and_relevance_over_recency(self) -> None:
        from luca_memory.context_builder import build_vram_context

        carousel = SynapticCarousel(self.store, vram_capacity=8, ram_capacity=16)
        with self.store.transaction():
            for fid in (10, 20, 30):
                save_node(self.store, KnowledgeNode(fid, f"f{fid}", f"Family {fid}", f"Family {fid}"))
            # Node 201 satisfies only 2 of 3 families (10 and 20), but has HUGE synaptic usage and recent recall
            save_node(self.store, KnowledgeNode(201, "partial_hot", "Partial 2/3 Hot", "Matches 10 and 20 only"))
            self.store.add_edge(Edge(10, 201))
            self.store.add_edge(Edge(20, 201))
            for _ in range(50):
                self.store.touch_edge(10, 201, 9_999_999)
                self.store.touch_edge(20, 201, 9_999_999)

            # Node 301 satisfies ALL 3 families (10, 20, 30), with zero prior usage
            save_node(self.store, KnowledgeNode(301, "exact_cold", "Exact 3/3 Cold", "Matches 10, 20, and 30"))
            self.store.add_edge(Edge(10, 301))
            self.store.add_edge(Edge(20, 301))
            self.store.add_edge(Edge(30, 301))

        # 1. Strict mode (Intersezione vincolante): ONLY 301 (3/3) is in ranked_ids and opened_ids; 201 (2/3) is in partial_matches
        carousel.recall_with_convergence([10, 20, 30], mode="strict")
        conv = carousel.last_convergence
        self.assertIsNotNone(conv)
        self.assertEqual(conv.ranked_ids, (301,))
        self.assertEqual(conv.opened_ids, (301,))
        self.assertEqual(tuple(m.node_id for m in conv.exact_matches), (301,))
        self.assertEqual(tuple(m.node_id for m in conv.partial_matches), (201,))
        self.assertEqual(carousel.vram.node_ids()[0], 301)
        self.assertIn(301, carousel.expanded_in_vram)
        self.assertNotIn(201, carousel.expanded_in_vram)

        # 2. Associative mode (default associative_max_open=1): 301 and 201 are ranked (301, 201), only 301 is opened, 201 stays in unopened_ids
        carousel_assoc_default = SynapticCarousel(self.store, vram_capacity=8, ram_capacity=16)
        carousel_assoc_default.recall_with_convergence([10, 20, 30], mode="associative")
        conv_assoc_1 = carousel_assoc_default.last_convergence
        self.assertIsNotNone(conv_assoc_1)
        self.assertEqual(conv_assoc_1.ranked_ids, (301, 201))
        self.assertEqual(conv_assoc_1.opened_ids, (301,))
        self.assertEqual(conv_assoc_1.unopened_ids, (201,))
        self.assertEqual(carousel_assoc_default.vram.node_ids()[0], 301)

        # 3. Associative mode with associative_max_open=2: opens from least relevant (201) to most relevant (301)
        # so the exact candidate 301 STILL remains the final focus head!
        carousel_assoc_multi = SynapticCarousel(self.store, vram_capacity=8, ram_capacity=16)
        carousel_assoc_multi.recall_with_convergence([10, 20, 30], mode="associative", associative_max_open=2)
        conv_assoc_2 = carousel_assoc_multi.last_convergence
        self.assertIsNotNone(conv_assoc_2)
        self.assertEqual(conv_assoc_2.ranked_ids, (301, 201))
        self.assertEqual(conv_assoc_2.opened_ids, (301, 201))
        self.assertEqual(carousel_assoc_multi.vram.node_ids()[0], 301)
        ctx = build_vram_context(carousel_assoc_multi)
        self.assertIn("[FOCUS CORRENTE] Exact 3/3 Cold", ctx)
        self.assertIn("[CONTESTO GIÀ APERTO] Partial 2/3 Hot", ctx)

    def test_multiple_results_with_small_vram_keep_capacities_and_open_closed_state_coherent(self) -> None:
        # 8 pertinent candidates (401..408) all matching families 10 and 20, with descending synaptic strength
        with self.store.transaction():
            save_node(self.store, KnowledgeNode(10, "f10", "Family 10", "Hub 10"))
            save_node(self.store, KnowledgeNode(20, "f20", "Family 20", "Hub 20"))
            for rank, cid in enumerate(range(401, 409)):
                ts = 10_000 - rank * 100
                save_node(self.store, KnowledgeNode(cid, f"cand_{cid}", f"Candidate {cid}", f"Content {cid}"))
                self.store.add_edge(Edge(10, cid))
                self.store.add_edge(Edge(20, cid))
                self.store.touch_edge(10, cid, ts)
                self.store.touch_edge(20, cid, ts)
                # Give each candidate an extra 1st-degree detail node (501..508)
                did = cid + 100
                save_node(self.store, KnowledgeNode(did, f"det_{did}", f"Detail {did}", f"Detail content {did}"))
                self.store.add_edge(Edge(cid, did))

        # Case A: Default behavior (max_open=1) on small VRAM (vram_capacity=3, ram_capacity=4)
        # Finds all 8 pertinent candidates in ranked_ids, opens ONLY the best (401), leaves 402..408 as unopened alternatives
        carousel_default = SynapticCarousel(self.store, vram_capacity=3, ram_capacity=4)
        carousel_default.recall_with_convergence([10, 20], mode="strict")
        conv = carousel_default.last_convergence
        self.assertIsNotNone(conv)
        self.assertEqual(conv.ranked_ids, tuple(range(401, 409)))
        self.assertEqual(conv.opened_ids, (401,))
        self.assertEqual(conv.unopened_ids, tuple(range(402, 409)))
        self.assertEqual(carousel_default.vram.node_ids()[0], 401)
        self.assertLessEqual(len(carousel_default.vram), 3)
        self.assertLessEqual(len(carousel_default.ram), 4)
        # Converging anchors 10 and 20 were reinforced before step_to(401), so they stay in VRAM alongside 401!
        self.assertEqual(set(carousel_default.vram.node_ids()), {401, 10, 20})
        self.assertEqual(carousel_default.expanded_in_vram, {401})
        self.assertTrue(carousel_default.expanded_in_vram.issubset(set(carousel_default.vram.node_ids())))
        self.assertIn(Edge(10, 401), carousel_default.vram_graph.edges())
        self.assertIn(Edge(20, 401), carousel_default.vram_graph.edges())

        # Case B: Opening multiple candidates (max_open=3: opens 403, then 402, then 401) in small VRAM (capacity=3, ram=4)
        carousel_multi = SynapticCarousel(self.store, vram_capacity=3, ram_capacity=4)
        carousel_multi.recall_with_convergence([10, 20], mode="strict", max_open=3)
        conv_m = carousel_multi.last_convergence
        self.assertIsNotNone(conv_m)
        self.assertEqual(conv_m.ranked_ids, tuple(range(401, 409)))
        self.assertEqual(conv_m.opened_ids, (401, 402, 403))
        self.assertEqual(conv_m.unopened_ids, tuple(range(404, 409)))
        # Because candidates are opened from least relevant (403) to most relevant (401), 401 is opened LAST and is at focus head!
        self.assertEqual(carousel_multi.vram.node_ids()[0], 401)
        self.assertLessEqual(len(carousel_multi.vram), 3)
        self.assertLessEqual(len(carousel_multi.ram), 4)
        vram_set = set(carousel_multi.vram.node_ids())
        ram_set = set(carousel_multi.ram.node_ids())
        self.assertTrue(vram_set.isdisjoint(ram_set))
        # Open/closed state invariant: only nodes currently in VRAM can be in expanded_in_vram; evicted candidates (402, 403) are closed in RAM
        self.assertTrue(carousel_multi.expanded_in_vram.issubset(vram_set))
        self.assertIn(401, carousel_multi.expanded_in_vram)
        self.assertNotIn(402, carousel_multi.expanded_in_vram)
        self.assertNotIn(403, carousel_multi.expanded_in_vram)
        self.assertIn(402, ram_set)
        self.assertIn(403, ram_set)
        # All edges in vram_graph connect nodes strictly inside VRAM
        for edge in carousel_multi.vram_graph.edges():
            self.assertIn(edge.source_id, vram_set)
            self.assertIn(edge.target_id, vram_set)

    def test_empty_strict_intersection_does_not_silently_relax_and_reports_partials(self) -> None:
        from luca_memory.context_builder import build_vram_context, convergence_signals

        carousel = SynapticCarousel(self.store, vram_capacity=8, ram_capacity=16)
        with self.store.transaction():
            for fid in (10, 20, 30):
                save_node(self.store, KnowledgeNode(fid, f"f{fid}", f"Family {fid}", f"Family {fid}"))
            # Node 201 matches (10, 20); Node 202 matches (20, 30). No node matches all three (10, 20, 30).
            save_node(self.store, KnowledgeNode(201, "p201", "Partial 10+20", "Only 10 and 20"))
            save_node(self.store, KnowledgeNode(202, "p202", "Partial 20+30", "Only 20 and 30"))
            self.store.add_edge(Edge(10, 201))
            self.store.add_edge(Edge(20, 201))
            self.store.add_edge(Edge(20, 202))
            self.store.add_edge(Edge(30, 202))

        carousel.recall_with_convergence([10, 20, 30], mode="strict")
        conv = carousel.last_convergence
        self.assertIsNotNone(conv)
        self.assertEqual(conv.exact_matches, ())
        self.assertEqual(conv.ranked_ids, ())
        self.assertEqual(conv.opened_ids, ())
        self.assertTrue(conv.has_only_partial_matches)
        self.assertEqual({m.node_id for m in conv.partial_matches}, {201, 202})
        self.assertEqual({m.node_id for m in conv.available_alternatives}, {201, 202})
        # Neither partial node was silently opened as exact
        self.assertNotIn(201, carousel.expanded_in_vram)
        self.assertNotIn(202, carousel.expanded_in_vram)
        # The LLM prompt uses plain Italian and never the technical labels (doc 05: small models echo them)
        ctx = build_vram_context(carousel)
        self.assertIn("Non conosco nessun fatto che riguardi insieme tutto quello che è stato chiesto.", ctx)
        self.assertIn("riguarda solo una parte della domanda: Partial 10+20", ctx)
        self.assertIn("riguarda solo una parte della domanda: Partial 20+30", ctx)
        self.assertNotIn("[INTERSEZIONE VINCOLANTE VUOTA]", ctx)
        self.assertNotIn("CORRISPONDENZA PARZIALE", ctx)
        self.assertNotIn("vincoli", ctx)
        self.assertNotIn("[FOCUS CORRENTE] Partial", ctx)
        # The labels are exposed only through the structured API signals
        signals = convergence_signals(carousel)
        self.assertIsNotNone(signals)
        self.assertEqual(signals["status_label"], "[INTERSEZIONE VINCOLANTE VUOTA]")
        self.assertEqual(
            {p["label"] for p in signals["partial_matches"]},
            {"[CORRISPONDENZA PARZIALE (2/3 vincoli)]"},
        )
        self.assertEqual(signals["opened_ids"], [])

    def test_materialized_degree_counters_update_on_add_and_remove_edge(self) -> None:
        # In setUp: 1->2, 2->3, 3->4, 5->3
        self.assertEqual(self.store.out_degree(2), 1)
        self.assertEqual(self.store.in_degree(2), 1)
        self.assertEqual(self.store.in_degree(3), 2)
        self.assertEqual(self.store.out_degree(3), 1)

        with self.store.transaction():
            # Duplicate add_edge must NOT increment degree counters
            self.store.add_edge(Edge(2, 3))
            self.assertEqual(self.store.out_degree(2), 1)
            self.assertEqual(self.store.in_degree(3), 2)

            # New edge 1->3 increments out_degree(1) and in_degree(3)
            self.store.add_edge(Edge(1, 3))
            self.assertEqual(self.store.out_degree(1), 2)
            self.assertEqual(self.store.in_degree(3), 3)

            # Removing edge 1->3 decrements out_degree(1) and in_degree(3)
            removed = self.store.remove_edge(1, 3)
            self.assertTrue(removed)
            self.assertEqual(self.store.out_degree(1), 1)
            self.assertEqual(self.store.in_degree(3), 2)
            self.assertFalse(self.store.remove_edge(1, 3))

    def _build_symmetric_families(self, size: int, *, hot_target: bool) -> None:
        with self.store.transaction():
            for fid in (10, 20, 30):
                save_node(self.store, KnowledgeNode(fid, f"f{fid}", f"Family {fid}", f"Hub {fid}"))
            conn = self.store.connection
            for i in range(size):
                for base, fid in ((10_000, 10), (20_000, 20), (30_000, 30)):
                    cid = base + i
                    conn.execute("INSERT INTO cells (id, content, created_at) VALUES (?, ?, 1)", (cid, b"{}"))
                    self.store.add_edge(Edge(fid, cid))
                    if not hot_target:
                        self.store.touch_edge(fid, cid, 1)
            save_node(self.store, KnowledgeNode(777, "target", "Target", "In all three families"))
            for fid in (10, 20, 30):
                self.store.add_edge(Edge(fid, 777))
                if hot_target:
                    self.store.touch_edge(fid, 777, 9_999)

    def test_hot_first_finds_exact_match_among_hottest_edges_without_exhaustive_scan(self) -> None:
        self._build_symmetric_families(600, hot_target=True)
        result = self.store.resolve_convergence([10, 20, 30], mode="strict", hot_k=64)
        self.assertEqual(result.strategy, "hot_first")
        self.assertEqual(result.ranked_ids, (777,))
        self.assertLessEqual(result.estimated_seed_edges, 64 * 2)
        from luca_memory.context_builder import convergence_signals
        hot_carousel = SynapticCarousel(self.store)
        hot_carousel.last_convergence = result
        self.assertFalse(convergence_signals(hot_carousel)["ranking_is_global"])
        self.assertEqual(convergence_signals(hot_carousel)["search_scope"], "hot_candidates")
        carousel = SynapticCarousel(self.store, search_policy="complete")
        carousel.recall_with_convergence([10, 20, 30])
        self.assertNotEqual(carousel.last_convergence.strategy, "hot_first")
        self.assertTrue(convergence_signals(carousel)["ranking_is_global"])
        self.assertEqual(carousel.last_convergence.opened_ids, (777,))

    def test_hot_first_falls_back_to_exhaustive_when_exact_match_is_cold(self) -> None:
        self._build_symmetric_families(600, hot_target=False)
        result = self.store.resolve_convergence([10, 20, 30], mode="strict", hot_k=64)
        self.assertEqual(result.strategy, "hot_first_fallback")
        self.assertEqual(result.ranked_ids, (777,))
        exhaustive = self.store.resolve_convergence([10, 20, 30], mode="strict", hot_k=0)
        self.assertEqual(exhaustive.strategy, "exhaustive")
        self.assertEqual(exhaustive.ranked_ids, (777,))

    def test_family_readers_are_bounded_by_default(self) -> None:
        with self.store.transaction():
            conn = self.store.connection
            for i in range(200):
                cid = 50_000 + i
                conn.execute("INSERT INTO cells (id, content, created_at) VALUES (?, ?, 1)", (cid, b"{}"))
                self.store.add_edge(Edge(1, cid))
                self.store.add_edge(Edge(cid, 4))
        limit = MemoryStore.DEFAULT_FAMILY_LIMIT
        self.assertEqual(len(self.store.prefix_family_ids(1)), limit)
        self.assertEqual(len(self.store.suffix_family_ids(4)), limit)
        self.assertEqual(len(self.store.prefix_family_ids(1, limit=None)), 201)
        memberships = self.store.node_family_memberships(1)
        self.assertLessEqual(len(memberships["suffix_families"]), limit)


if __name__ == "__main__":
    unittest.main()


