"""Behavioral contract derived from the user's submarine conversation."""

from pathlib import Path
import unittest

from luca_memory.session import LucaSession


SEED = Path(__file__).parents[1] / "seed/knowledge_base_v1.json"


class RecallPlanningTests(unittest.TestCase):
    def setUp(self):
        self.session = LucaSession.open(":memory:", SEED, vram_capacity=5, ram_capacity=12)

    def tearDown(self):
        self.session.close()

    def test_conversation_keeps_vehicle_attributes_then_moves_laterally_and_to_family(self):
        cases = [
            ("hai mai sentito parlare di gatti che guidano sommergibili?", 7),
            ("Ci sono altri animali che conducono questi sottomarini gialli?", 7),
            ("e i cani?", 19),
            ("quindi ci sono altri aniamli che guidano altri sottomarini?", 14),
        ]
        for question, focus in cases:
            with self.subTest(question=question):
                self.session.handle(question)
                self.assertEqual(self.session.current_subject_id, focus)
        self.assertNotIn(8, self.session.carousel.expanded_in_vram)

    def test_accented_cause_and_destination_are_distinct(self):
        for question in ("Perché?", "Perche?", "Come mai?"):
            self.session.reset()
            self.session.handle("Gli asini volano?")
            self.session.handle(question)
            self.assertEqual(self.session.current_subject_id, 2)
        self.session.reset()
        self.session.handle("Parlami dei gatti nei sottomarini")
        self.session.handle("Dove attraccano?")
        self.assertEqual(self.session.current_subject_id, 8)

    def test_excluded_subject_does_not_drive_intersection(self):
        self.session.handle("Non voglio parlare dei cani, parlami dei sommergibili")
        self.assertEqual(self.session.current_subject_id, 14)
        self.assertNotIn(19, self.session.carousel.expanded_in_vram)

    def test_unknown_topic_keeps_cache_but_does_not_expose_old_focus(self):
        self.session.handle("Parlami dei sottomarini")
        before = self.session.carousel.vram.node_ids()
        self.session.handle("Cambiamo argomento: spiegami la fotosintesi")
        self.assertEqual(self.session.carousel.vram.node_ids(), before)
        self.assertNotIn("Sottomarini", self.session._memory_context("fotosintesi"))
