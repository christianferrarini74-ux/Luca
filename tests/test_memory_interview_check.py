"""Verify interview continuity and factual probes without consulting a model."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from luca_memory.memory_interview_check import explicit_question, interview


class MemoryInterviewTests(unittest.TestCase):
    def test_explicit_probe_does_not_claim_a_read_was_missing_when_it_happened(self):
        self.assertIn("hai letto anche", explicit_question([3]))
        self.assertNotIn("non hai aperto", explicit_question([3]))

    def test_explicit_probe_does_not_supply_the_missing_threshold(self):
        question = explicit_question([4, 5, 2])
        self.assertIn("non hai aperto", question)
        self.assertNotIn("28", question)
        self.assertNotIn("41", question)

    def make_session(self, adapter):
        session = MagicMock()
        session.history = []
        session.carousel.physical_state.return_value = {}
        readings = iter(([4, 5, 2], [3], [3]))

        def handle(question):
            session.navigator.workspace.nodes = dict.fromkeys(next(readings))
            adapter.observations.append({"action": "answer"})
            adapter.navigation_inputs.append({"question": question})
            adapter.request_observations.append({"input_tokens": 1})
            session.history.extend(({"role": "user", "content": question},
                                    {"role": "assistant", "content": "Reply"}))
            return SimpleNamespace(text="Reply")

        session.handle.side_effect = handle
        return session

    def test_followups_keep_history_and_explicit_probe_refers_to_initial_turn(self):
        adapter = SimpleNamespace(observations=[], navigation_inputs=[], request_observations=[])
        session = self.make_session(adapter)
        with patch("builtins.print"):
            result = interview(session, adapter)
        self.assertEqual([len(turn["history_before"]) for turn in result["turns"]], [0, 2, 4])
        self.assertEqual(len(session.history), 6)
        self.assertFalse(result["initial_sensor_read"])
        self.assertTrue(result["turns"][1]["sensor_read_this_turn"])
        self.assertIn("non hai aperto", result["turns"][2]["question"])

    def test_completed_turn_is_preserved_if_a_followup_fails(self):
        adapter = SimpleNamespace(observations=[], navigation_inputs=[], request_observations=[])
        session = self.make_session(adapter)
        first_handle = session.handle.side_effect

        def handle(question):
            if session.history:
                raise RuntimeError("Synthetic followup failure")
            return first_handle(question)

        session.handle.side_effect = handle
        turns = []
        with patch("builtins.print"), self.assertRaises(RuntimeError):
            interview(session, adapter, turns=turns)
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["stage"], "initial")
