from pathlib import Path
import unittest

from luca_memory import LanguageIntent, LucaSession


class TeachingAdapter:
    """Minimal stand-in for a future local micro-LLM adapter."""

    def interpret(self, text: str, current_subject: str | None = None) -> LanguageIntent:
        if text == "memorizza il fatto":
            return LanguageIntent(
                "remember",
                text,
                subject="sole",
                predicate="produce",
                objects=("luce", "calore"),
                confidence=0.98,
            )
        return LanguageIntent("ask", text, question="cosa produce il sole")


class ConversationalTeachingAdapter(TeachingAdapter):
    def respond(self, text: str, memory_context: str, history: list[dict[str, str]]) -> str:
        return f"Risposta libera: {text}. Contesto: {memory_context}"


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

    def test_a_language_adapter_can_be_replaced_without_changing_memory(self) -> None:
        session = LucaSession.open(self.database, self.seed, adapter=TeachingAdapter())
        learned = session.handle("memorizza il fatto")
        answer = session.handle("domanda libera")
        session.close()

        self.assertEqual(learned.text, "Ho registrato la conoscenza.")
        self.assertEqual(answer.text, "Il sole produce luce e calore.")

    def test_conversational_adapter_receives_retrieved_memory_context(self) -> None:
        session = LucaSession.open(self.database, self.seed, adapter=ConversationalTeachingAdapter())
        answer = session.handle("Parlami del sole.")
        session.close()

        self.assertIn("Risposta libera", answer.text)
        self.assertIn("sole scalda pelle", answer.text)


if __name__ == "__main__":
    unittest.main()
