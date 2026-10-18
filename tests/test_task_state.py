"""Task goals and decisions survive detours, restarts and context trimming."""

from pathlib import Path
import tempfile
import unittest

from luca_memory.session import LucaSession
from luca_memory.budget import PromptBudget


SEED = Path(__file__).parents[1] / "seed/knowledge_base_v1.json"


class TaskStateTests(unittest.TestCase):
    def test_resume_after_disconnected_topic_preserves_goal_constraints_and_decisions(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "task.sqlite"
            session = LucaSession.open(database, SEED)
            try:
                session.handle("Obiettivo: studiare il volo degli asini")
                session.handle("Vincolo: distinguere cause e conseguenze")
                session.handle("Decisione: iniziare dalla montagna")
                session.handle("Gli asini volano?")
                self.assertEqual(session.task.state.focus_id, 3)
                session.handle("Cambiamo argomento: parliamo dei gatti nei sottomarini")
                self.assertEqual(session.current_subject_id, 7)
                self.assertTrue(session.task.state.suspended)
                self.assertEqual(session.task.state.focus_id, 3)
            finally:
                session.close()
            reopened = LucaSession.open(database, SEED)
            try:
                reopened.handle("Riprendi il compito")
                self.assertEqual(reopened.current_subject_id, 3)
                self.assertFalse(reopened.task.state.suspended)
                rendered = reopened.task.state.render()
                self.assertIn("studiare il volo", rendered)
                self.assertIn("distinguere cause", rendered)
                self.assertIn("iniziare dalla montagna", rendered)
                messages, report = PromptBudget().messages("Istruzioni", "X" * 100000, [], "Continuiamo", required_context=rendered)
                self.assertIn(rendered, messages[0]["content"])
                self.assertLessEqual(report["input_units"], report["input_limit"])
                reopened.reset()
                self.assertFalse(reopened.task.state.active)
            finally:
                reopened.close()

    def test_invalid_or_oversized_task_update_is_atomic(self):
        session = LucaSession.open(":memory:", SEED)
        try:
            session.task.update({"goal": "Scrivere il modulo"})
            before = session.task.snapshot()
            for update in ({"constraints": "invalid"}, {"goal": "X" * 10000}, {"unknown": True}, {"clear": "yes"}):
                with self.assertRaises(ValueError):
                    session.task.update(update)
                self.assertEqual(session.task.snapshot(), before)
        finally:
            session.close()

    def test_manual_document_section_does_not_clear_task(self):
        from luca_memory.node import KnowledgeNode, KnowledgeSection, save_node
        session = LucaSession.open(":memory:", SEED)
        try:
            with session.store.transaction():
                save_node(session.store, KnowledgeNode(100, "manual", "Manuale", "Sintesi",
                          sections=(KnowledgeSection("a", "Sezione A", "Dettagli"),)))
            session.recall_manual(100)
            session.task.update({"goal": "Studiare il manuale"}, 100)
            session.open_section(100, "a")
            self.assertEqual(session.task.state.section_key, "a")
            self.assertTrue(session.task.state.active)
            session.recall_manual(7)
            self.assertTrue(session.task.state.suspended)
            session.handle("Riprendi il compito")
            self.assertEqual(session.carousel.section_focus, (100, "a"))
            self.assertFalse(session.task.state.suspended)
        finally:
            session.close()
