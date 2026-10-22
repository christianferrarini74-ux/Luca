"""Keep the goal-first probe free of solution facts and validate its fixture."""

import json
import unittest

from luca_memory.controlled_document_check import ROOT
from luca_memory.seed_v1 import knowledge_seed_from_file


class GoalFramingTests(unittest.TestCase):
    def test_goal_precedes_fault_without_supplying_the_solution(self):
        case = json.loads((ROOT / "tests/fixtures/goal_framing_questions.json").read_text(encoding="utf-8"))[0]
        question = case["question"]
        self.assertLess(question.index("valvola deve aprirsi"), question.index("E42"))
        for clue in ("capitolo", "28", "41", "CONFERMA", "AVVIA", "quattro", "tre letture"):
            self.assertNotIn(clue, question)
        ids = knowledge_seed_from_file(ROOT / "seed" / case["seed"]).ids
        self.assertTrue(set(case["required_slugs"]).issubset(ids))
