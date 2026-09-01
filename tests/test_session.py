from pathlib import Path
import unittest

from luca_memory import LucaSession


class LucaSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(__file__).parent / "session-runtime.sqlite"
        self.database.unlink(missing_ok=True)
        self.seed = Path(__file__).parent.parent / "seed" / "italian_base_v0.json"

    def tearDown(self) -> None:
        self.database.unlink(missing_ok=True)

    def test_teach_contextual_recall_and_restart(self) -> None:
        session = LucaSession.open(self.database, self.seed)
        self.assertEqual(session.handle("Parlami del sole.").text, "So che sole scalda pelle.")
        taught = session.handle("Luca, ricorda che il sole produce luce.")
        self.assertEqual(taught.text, "Ho registrato la conoscenza.")
        self.assertEqual(session.handle("E cosa produce?").text, "Il sole produce luce.")
        session.close()

        restarted = LucaSession.open(self.database, self.seed)
        answer = restarted.handle("Cosa produce il sole?")
        restarted.close()
        self.assertEqual(answer.text, "Il sole produce luce.")
        self.assertEqual(len(answer.trace), 4)

    def test_compatible_facts_are_returned_together(self) -> None:
        session = LucaSession.open(self.database, self.seed)
        session.handle("Luca ricorda che il sole produce luce")
        session.handle("Luca ricorda che il sole produce calore")
        answer = session.handle("Cosa produce il sole?")
        session.close()
        self.assertEqual(answer.text, "Il sole produce luce e calore.")
        self.assertEqual(len(answer.trace), 7)

    def test_duplicate_lesson_is_not_silently_duplicated(self) -> None:
        session = LucaSession.open(self.database, self.seed)
        self.assertEqual(session.handle("Luca ricorda che il sole produce luce").text, "Ho registrato la conoscenza.")
        self.assertEqual(session.handle("Luca ricorda che il sole produce luce").text, "Ho già questa conoscenza.")
        session.close()


if __name__ == "__main__":
    unittest.main()
