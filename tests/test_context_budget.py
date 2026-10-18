"""Bound model requests and cache payloads without destroying source documents."""

import unittest
from pathlib import Path
from luca_memory.budget import PromptBudget, units
from luca_memory.context_builder import build_vram_context
from luca_memory.node import KnowledgeNode, KnowledgeSection, save_node, load_node
from luca_memory.store import MemoryStore
from luca_memory.tiers import SynapticCarousel
from luca_memory.session import LucaSession


class ContextBudgetTests(unittest.TestCase):
    def test_large_node_is_bounded_in_cache_and_prompt_but_kept_on_ssd(self):
        with MemoryStore(":memory:") as store:
            source = KnowledgeNode(1, "book", "A book", "Conoscenza " * 40000,
                                   sections=(KnowledgeSection("tests", "Test", "Contenuto della sezione test"),))
            with store.transaction():
                save_node(store, source)
            carousel = SynapticCarousel(store, vram_bytes=2048, ram_bytes=4096)
            carousel.recall(1)
            self.assertLessEqual(carousel.vram.used_bytes, 2048)
            self.assertFalse(carousel.vram.get(1).content_complete)
            self.assertEqual(load_node(store, 1).content, source.content)
            context = build_vram_context(carousel)
            self.assertLessEqual(units(context), carousel.prompt_budget.memory_limit)
            self.assertIn("estratto parziale", context)
            with self.assertRaises(ValueError):
                save_node(store, carousel.vram.get(1))

    def test_entire_request_reserves_output_and_framing_and_keeps_question(self):
        budget = PromptBudget()
        history = [{"role": role, "content": "test " * 1000} for role in ("user", "assistant") for _ in range(2)]
        messages, report = budget.messages("Istruzioni stabili", "Memoria " * 100000, history, "Domanda esatta")
        self.assertEqual(messages[-1]["content"], "Domanda esatta")
        self.assertLessEqual(report["input_units"] + budget.output_reserve + budget.framing_reserve, budget.context_window)
        self.assertTrue(report["memory_truncated"])
        with self.assertRaises(ValueError):
            budget.messages("Istruzioni", "", [], "X" * budget.context_window)

    def test_section_access_validates_key_and_keeps_document_identity(self):
        seed = Path(__file__).parents[1] / "seed/knowledge_base_v1.json"
        session = LucaSession.open(":memory:", seed)
        try:
            with session.store.transaction():
                save_node(session.store, KnowledgeNode(100, "manual", "Manuale", "Panoramica",
                          sections=(KnowledgeSection("testing", "Verifiche", "Eseguire i test del modulo."),)))
            session.open_section(100, "testing")
            self.assertEqual(session.current_subject_id, 100)
            self.assertIn("Eseguire i test", session._memory_context("sezione"))
            self.assertEqual(session.carousel.section_focus, (100, "testing"))
            session.carousel.section_focus = None
            session.handle("Apri la sezione Verifiche")
            self.assertEqual(session.last_plan.operation, "section")
            self.assertEqual(session.carousel.section_focus, (100, "testing"))
            with self.assertRaises(ValueError):
                session.open_section(100, "missing")
        finally:
            session.close()

    def test_summary_is_used_without_claiming_to_expose_the_whole_document(self):
        with MemoryStore(":memory:") as store:
            with store.transaction():
                save_node(store, KnowledgeNode(1, "doc", "Document", "Long body " * 10000, summary="Sintesi verificata"))
            carousel = SynapticCarousel(store, vram_bytes=2048)
            carousel.recall(1)
            context = build_vram_context(carousel)
            self.assertIn("Sintesi verificata", context)
            self.assertNotIn("Long body", context)
