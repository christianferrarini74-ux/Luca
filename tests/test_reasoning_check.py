"""The integration replay must test actual reads, not merely recognized titles."""

import unittest

from luca_memory.reasoning_check import INTEGRATION_CASES, assess


class IntegrationReplayTests(unittest.TestCase):
    def test_scenario_includes_general_knowledge_before_and_after_memory(self):
        names = [name for name, _, _ in INTEGRATION_CASES]
        self.assertEqual(len(names), 8)
        self.assertEqual(len(set(names)), len(names))
        self.assertLess(names.index("diet_before"), names.index("flying"))
        self.assertGreater(names.index("diet_after"), names.index("flying"))

    def test_general_knowledge_does_not_require_a_read_node(self):
        self.assertTrue(assess("diet", "Sono erbivori e mangiano erba.", []))
        self.assertFalse(assess("diet", "Le informazioni non specificano cosa mangiano.", [3]))

    def test_title_recognition_without_reading_cannot_pass_memory_check(self):
        text = "Pioggia di zucchero filato in montagna"
        self.assertFalse(assess("rain", text, [3]))
        self.assertTrue(assess("rain", text, [2]))

    def test_connection_requires_reading_the_node_with_the_explanation(self):
        text = "La pioggia di zucchero filato cambia la gravità e gli asini volano."
        self.assertFalse(assess("connection", text, [3]))
        self.assertTrue(assess("connection", text, [2, 3]))
