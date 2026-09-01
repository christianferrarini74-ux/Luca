from pathlib import Path
import unittest

from luca_memory import ItalianSeedInterface, MemoryStore, load_curriculum


class CurriculumTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"
        self.curriculum = load_curriculum(self.store, seed)
        self.interface = ItalianSeedInterface(self.store, self.curriculum)

    def tearDown(self) -> None:
        self.store.close()

    def test_seed_answers_identity_and_world_questions_from_graph(self) -> None:
        answer = self.interface.answer("Chi è il tuo creatore?")
        self.assertEqual(answer.text, "Il mio creatore è Christian.")
        self.assertEqual(len(answer.trace), 4)
        self.assertEqual(self.interface.answer("Cosa produce il fuoco?").text, "Il fuoco produce calore.")

    def test_unknown_question_is_not_invented(self) -> None:
        answer = self.interface.answer("Qual è il colore del fuoco?")
        self.assertEqual(answer.text, "Non conosco ancora questa forma di domanda.")
        self.assertEqual(answer.trace, ())


if __name__ == "__main__":
    unittest.main()
