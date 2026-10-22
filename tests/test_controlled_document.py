"""Check fixture fidelity, topology and isolation without querying a language model."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from luca_memory.controlled_document_check import (
    DOCUMENT,
    QUESTIONS,
    ROOT,
    indicators,
    run_case,
)
from luca_memory.seed_v1 import ensure_knowledge_seed, knowledge_seed_from_file
from luca_memory.store import MemoryStore
from luca_memory.synaptic import SynapticMemory


class ControlledDocumentTests(unittest.TestCase):
    def test_manual_matches_every_seed_chapter(self):
        manual = (ROOT / "docs/it/esperimenti/iris17-manuale.md").read_text(encoding="utf-8")
        document = json.loads(DOCUMENT.read_text(encoding="utf-8"))
        self.assertEqual(len(document["nodes"]), 7)
        for node in document["nodes"]:
            self.assertIn(node["title"], manual)
            self.assertIn(node["content"], manual)
        self.assertNotIn("rubric", document)

    def test_index_and_recovery_routes_are_real_edges(self):
        with MemoryStore(":memory:") as store:
            seed = ensure_knowledge_seed(store, DOCUMENT)
            memory = SynapticMemory(store)
            self.assertEqual(store.cell_count(), 7)
            self.assertEqual(len(store.outgoing(seed.ids["iris_index"])), 6)
            for source, target in (("iris_alarm", "iris_recovery"), ("iris_recovery", "iris_modes"),
                                   ("iris_recovery", "iris_sensor")):
                directory = memory.directory(seed.ids[source])
                memory.validate_step(seed.ids[source], seed.ids[target], directory.revision)

    def test_questions_only_reference_document_nodes(self):
        ids = knowledge_seed_from_file(DOCUMENT).ids
        cases = json.loads(QUESTIONS.read_text(encoding="utf-8"))
        self.assertEqual(len({case["id"] for case in cases}), 7)
        for case in cases:
            self.assertTrue(set(case["required_slugs"]).issubset(ids))
            self.assertTrue(case["terms"])

    def test_lexical_success_is_not_reading_or_semantic_success(self):
        case = {"terms": [["30"]], "required_slugs": ["sensor"]}
        result = indicators(case, "not 30", [], {"sensor": 3})
        self.assertTrue(result["lexical_match"])
        self.assertFalse(result["required_nodes_read"])
        self.assertTrue(result["review_required"])

    def test_answer_key_never_enters_the_session_and_resources_close(self):
        session = MagicMock()
        session.handle.return_value.text = "Response"
        session.navigator.workspace.nodes = {}
        session.navigator.trace = []
        session.carousel.physical_state.return_value = {}
        adapter = SimpleNamespace(model="test-model", last_prompt_report={})
        case = {"question": "Ordinary question", "rubric": "SECRET ANSWER KEY"}
        with patch("luca_memory.controlled_document_check.ObservedAdapter.from_config", return_value=adapter), \
                patch("luca_memory.controlled_document_check.LucaSession.open", return_value=session):
            result = run_case({"runtime": {}}, case, DOCUMENT, ":memory:")
        session.handle.assert_called_once_with("Ordinary question")
        session.close.assert_called_once()
        self.assertEqual(result["reply"], "Response")
