from pathlib import Path
import unittest

from luca_memory.api import LucaRuntime
from luca_memory.session import LucaSession


class Phase1KnowledgeSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(__file__).parent / "v1-runtime.sqlite"
        self.database.unlink(missing_ok=True)
        self.seed = Path(__file__).parent.parent / "seed" / "knowledge_base_v1.json"

    def tearDown(self) -> None:
        self.database.unlink(missing_ok=True)

    def test_fables_first_degree_and_second_degree_step_and_overflow(self) -> None:
        session = LucaSession.open(self.database, self.seed, vram_capacity=4, ram_capacity=6)
        try:
            # 1. Ask about flying donkeys (#3 asini_volanti)
            # Should pull #3 (center) + #2 (pioggia_zucchero) + #4 (nidi_campanili) into VRAM,
            # while #5 (formaggio_blu_campane, 2nd degree) MUST remain closed outside VRAM!
            reply = session.handle("Gli asini volano?")
            self.assertIn("Gli Asini Volano", reply.text)
            self.assertIn(3, session.carousel.vram)
            self.assertIn(2, session.carousel.vram)
            self.assertIn(4, session.carousel.vram)
            self.assertNotIn(5, session.carousel.vram)

            # 2. Shift thought to the 1st-degree node (#4 nidi_campanili)
            # Now #5 (formaggio_blu_campane) MUST be catapulted into VRAM!
            session.handle("Cosa succede nei nidi sui campanili?")
            self.assertIn(5, session.carousel.vram)

            # 3. Trigger the other two fable chains to push older nodes from VRAM into RAM
            session.handle("Parlami dei gatti nei sottomarini")
            session.handle("Cosa fanno gli alberi di caffè?")
            self.assertEqual(len(session.carousel.vram), 4)
            self.assertGreater(len(session.carousel.ram), 0)
        finally:
            session.close()

    def test_api_exposes_tiers_and_recall_endpoint_shifts_focus(self) -> None:
        runtime = LucaRuntime(
            {
                "storage": {"database": str(self.database), "seed": str(self.seed)},
                "runtime": {
                    "language_adapter": "rules",
                    "adapter_role": "orchestrator",
                    "vram_capacity": 4,
                    "ram_capacity": 8,
                },
            }
        )
        try:
            # Recall node 3 (asini_volanti) -> pulls its 1st-degree cluster (2 and 4) into VRAM
            result = runtime.recall_node(3)
            vram_nodes = result["state"]["tiers"]["vram"]["nodes"]
            self.assertEqual(vram_nodes[0]["id"], 3)
            self.assertTrue(vram_nodes[0]["expanded"])
            self.assertGreater(len(result["state"]["tiers"]["vram"]["chains"]), 0)
        finally:
            runtime.close()

    def test_meta_sentences_do_not_corrupt_vram_and_runtime_data_is_separate(self) -> None:
        from luca_memory.adapters import LMStudioAdapter

        session = LucaSession.open(self.database, self.seed, vram_capacity=5, ram_capacity=8)
        try:
            session.handle("Cambiamo argomento, parliamo di mare")
            vram_before = session.carousel.vram.node_ids()
            self.assertIn(6, vram_before)

            # Meta-sentence without domain aliases must NOT alter VRAM
            session.handle("dai smetti di sognare, torna con i piedi per terra non interpretare parti, voglio un rapporto serio")
            self.assertEqual(session.carousel.vram.node_ids(), vram_before)

            # First talk about donkeys/nests (nodes 3, 4, 5, 2)
            session.handle("Parlami dei nidi di paglia")
            self.assertIn(4, session.carousel.vram.node_ids())
            self.assertIn(5, session.carousel.vram.node_ids())

            # Then switch to submarines (nodes 7, 8, 6); 4 and 5 stay in tail of VRAM
            # but MUST NOT appear in build_vram_context! ("sottomarini" -> #7; "sommergibili" now -> #14 flotta)
            reply_sub = session.handle("Parliamo dei sottomarini")
            self.assertEqual(reply_sub.trace[:3], (7, 8, 6))
            context_sub = session._memory_context("sommergibili")
            self.assertIn("I Gatti Guidano Sottomarini Gialli di Cartone", context_sub)
            self.assertNotIn("Nidi di Paglia Dorata", context_sub)
            self.assertNotIn("Formaggio Blu", context_sub)

            import json
            from luca_memory.bible import read_bible
            adapter = LMStudioAdapter()
            messages, _ = adapter._request("respond", "Domanda", {"memory": context_sub})
            self.assertEqual(messages[0]["content"], read_bible())
            self.assertEqual(json.loads(messages[-1]["content"])["memory"], context_sub)
        finally:
            session.close()

    def test_multi_edge_family_intersection_and_submarine_fleet_disambiguation(self) -> None:
        session = LucaSession.open(self.database, self.seed, vram_capacity=5, ram_capacity=8)
        try:
            # 1. Without submarine context in VRAM, asking about monkeys opens the terrestrial monkey family (#17)
            reply_monkeys = session.handle("Parlami delle scimmie")
            self.assertEqual(session.carousel.vram.node_ids()[0], 17)
            self.assertIn("Le Scimmie", reply_monkeys.text)
            self.assertNotIn(21, session.carousel.expanded_in_vram)

            # 2. Reset and enter submarine context (#7 gatti_sottomarini, which pulls prefix #14 flotta_sommergibili into VRAM)
            session.reset()
            session.handle("Conosci i sommergibili?")
            self.assertIn(7, session.carousel.vram)
            self.assertIn(14, session.carousel.vram)

            # 3. Follow-ups across the animal families converge via shared prefix #14 + animal family onto each animal's submarine
            expected_submarines = [
                ("E i cani?", 19, "Sommergibili Rossi di Biscotto"),
                ("E i pappagalli?", 20, "Sommergibili Verdi di Vetro Soffiato"),
                ("E le scimmie?", 21, "Sommergibili Blu a Pedali di Legno"),
                ("E i topi?", 22, "Sommergibili Arancioni di Crosta di Parmigiano"),
            ]
            for question, expected_node_id, expected_phrase in expected_submarines:
                reply = session.handle(question)
                self.assertEqual(session.carousel.vram.node_ids()[0], expected_node_id)
                self.assertIn(expected_node_id, session.carousel.expanded_in_vram)
                self.assertIn(expected_phrase, reply.text)

            # 4. Selective synaptic reinforcement: #22 (sommergibile_topi, last used) has moved to the front of #14's prefix family!
            self.assertEqual(session.store.prefix_family_ids(14)[0], 22)

            # 5. Explicit family memberships derived directly from prefix:suffix edges:
            #    - Prefix family 14:* (flotta_sommergibili:*) has all 5 animal submarines {7, 19, 20, 21, 22}
            #    - Suffix family *:8 (*:biblioteche_corallo) has all 5 animal submarines {7, 19, 20, 21, 22}
            #    - Node #19 (sommergibile_cani) belongs to prefix families (14, 15) and suffix family (8)
            self.assertEqual(set(session.store.prefix_family_ids(14)), {7, 19, 20, 21, 22})
            self.assertEqual(set(session.store.suffix_family_ids(8)), {7, 19, 20, 21, 22})
            memberships_19 = session.store.node_family_memberships(19)
            self.assertEqual(set(memberships_19["prefix_families"]), {14, 15})
            self.assertEqual(set(memberships_19["suffix_families"]), {8})

            # 6. Suffix-family intersection (*:8 ∩ 15:* -> #19):
            #    Starting from the shared suffix #8 (biblioteche_corallo), asking "E i cani?" (#15) also converges onto #19!
            session.reset()
            session.handle("Parlami delle biblioteche di corallo")
            self.assertEqual(session.carousel.vram.node_ids()[0], 8)
            reply_dogs_from_suffix = session.handle("E i cani?")
            self.assertEqual(session.carousel.vram.node_ids()[0], 19)
            self.assertIn("Sommergibili Rossi di Biscotto", reply_dogs_from_suffix.text)
        finally:
            session.close()

    def test_query_diagnostics_expire_but_working_memory_and_alternatives_survive(self) -> None:
        session = LucaSession.open(self.database, self.seed, vram_capacity=5, ram_capacity=8)
        try:
            session.handle("I sommergibili dei cani e dei pinguini")
            previous = session.carousel.last_convergence
            self.assertTrue(previous.has_only_partial_matches)
            before = session.carousel.vram.node_ids()
            session.handle("Quanto fa due più due?")
            self.assertIsNone(session.carousel.last_convergence)
            self.assertIs(session.carousel.previous_convergence, previous)
            self.assertEqual(session.carousel.vram.node_ids(), before)
            self.assertNotIn("Non conosco nessun fatto che riguardi insieme", session._memory_context("due più due"))
            session.carousel.open_alternative(19)
            self.assertEqual(session.carousel.vram.node_ids()[0], 19)
            self.assertIsNone(session.carousel.last_convergence)
            self.assertNotIn(19, {m.node_id for m in session.carousel.previous_convergence.available_alternatives})
            with self.assertRaises(ValueError):
                session.carousel.open_alternative(999999)
        finally:
            session.close()

    def test_dogs_submarines_in_one_sentence_is_an_exact_strict_intersection(self) -> None:
        session = LucaSession.open(self.database, self.seed, vram_capacity=5, ram_capacity=8)
        try:
            reply = session.handle("I sommergibili dei cani")
            conv = session.carousel.last_convergence
            self.assertIsNotNone(conv)
            self.assertEqual(conv.required_anchors, (14, 15))
            self.assertEqual(tuple(m.node_id for m in conv.exact_matches), (19,))
            self.assertEqual(conv.opened_ids, (19,))
            self.assertEqual(session.carousel.vram.node_ids()[0], 19)
            self.assertIn("Sommergibili Rossi di Biscotto", reply.text)

            # Three required anchors without a common member: no silent relaxation, plain-Italian partial reply
            session.reset()
            reply_partial = session.handle("I sommergibili dei cani e dei pinguini")
            conv_p = session.carousel.last_convergence
            self.assertEqual(conv_p.required_anchors, (14, 15, 13))
            self.assertEqual(conv_p.exact_matches, ())
            self.assertEqual(conv_p.opened_ids, ())
            self.assertIn(19, {m.node_id for m in conv_p.partial_matches})
            self.assertIn("Non conosco nulla che riguardi insieme", reply_partial.text)
            self.assertIn("Sommergibili Rossi di Biscotto", reply_partial.text)
            self.assertNotIn("vincoli", reply_partial.text)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()


